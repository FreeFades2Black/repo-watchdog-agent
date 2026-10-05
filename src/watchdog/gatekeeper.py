"""
OCaml Gatekeeper Ingress Integration for Repo Watchdog Agent.
Streams scraped release events and CVE telemetry through ocaml-event-engine
before updating intel_cache.db or triggering LLM analysis.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class GatekeeperEngine:
    """Manages continuous interactive streaming with ocaml-event-engine."""

    def __init__(self, binary_cmd: list[str] | None = None, initial_seen: set | None = None):
        self._seen_ids = set(initial_seen or [])
        self.cmd = binary_cmd or self._detect_engine_cmd()
        self._proc: subprocess.Popen | None = None
        if self.cmd:
            self._start_process()

    def _detect_engine_cmd(self) -> list[str] | None:
        local_bins = [
            os.path.join(os.getcwd(), "bin", "ocaml-event-engine"),
            os.path.join(os.getcwd(), "bin", "ocaml-event-engine.exe"),
            os.path.expanduser("~/.local/bin/ocaml-event-engine"),
        ]
        for b in local_bins:
            if os.path.isfile(b) and os.access(b, os.X_OK):
                return [b]

        which_bin = shutil.which("ocaml-event-engine")
        if which_bin:
            return [which_bin]

        docker_bin = shutil.which("docker")
        if docker_bin:
            try:
                check = subprocess.run(
                    [docker_bin, "version"],
                    capture_output=True,
                    timeout=2,
                    text=True,
                )
                if check.returncode == 0:
                    return [
                        docker_bin,
                        "run",
                        "-i",
                        "--rm",
                        "ghcr.io/freefades2black/ocaml-event-engine:latest",
                    ]
            except Exception:
                pass

        return None

    def _start_process(self):
        try:
            self._proc = subprocess.Popen(
                self.cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except (OSError, FileNotFoundError) as e:
            logger.warning(
                f"Could not spawn gatekeeper command {self.cmd}: {e}. "
                "Operating in specification fallback mode."
            )
            self._proc = None

    def evaluate(self, event_id: str, timestamp: int, payload: str) -> tuple[str, str, str | None]:
        """
        Sends an event to ocaml-event-engine and returns (status, id, error).
        Status is one of: 'processed', 'duplicate', 'invalid'.
        """
        if self._proc is None or self._proc.poll() is not None:
            return self._spec_fallback(event_id, timestamp, payload)

        req_json = json.dumps({"id": event_id, "timestamp": timestamp, "payload": payload})
        try:
            assert self._proc.stdin is not None
            assert self._proc.stdout is not None
            self._proc.stdin.write(req_json + "\n")
            self._proc.stdin.flush()

            resp_line = self._proc.stdout.readline()
            if not resp_line:
                return self._spec_fallback(event_id, timestamp, payload)

            resp = json.loads(resp_line.strip())
            status = resp.get("status", "invalid")
            resp_id = resp.get("id", event_id)
            error = resp.get("error")
            return status, resp_id, error
        except (BrokenPipeError, OSError, json.JSONDecodeError) as e:
            logger.error(f"Gatekeeper process communication error: {e}")
            return self._spec_fallback(event_id, timestamp, payload)

    def _spec_fallback(self, event_id: str, timestamp: int, payload: str) -> tuple[str, str, str | None]:
        trimmed_id = event_id.strip() if event_id else ""
        trimmed_payload = payload.strip() if payload else ""

        if not trimmed_id:
            return "invalid", event_id, "Event ID cannot be blank"
        if not trimmed_payload:
            return "invalid", event_id, "Payload cannot be empty"
        if trimmed_id in self._seen_ids:
            return "duplicate", event_id, None

        self._seen_ids.add(trimmed_id)
        return "processed", event_id, None

    def close(self):
        if self._proc and self._proc.poll() is None:
            try:
                if self._proc.stdin:
                    self._proc.stdin.close()
                self._proc.terminate()
                self._proc.wait(timeout=2)
            except Exception:
                pass


class IntelCache:
    """SQLite-backed intelligence cache."""

    def __init__(self, db_path: str = "intel_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS intel_events (
                    id TEXT PRIMARY KEY,
                    timestamp INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    inserted_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def insert_event(self, event_id: str, timestamp: int, payload: str) -> bool:
        """Inserts an event into SQLite. Returns True if inserted, False on conflict."""
        now = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO intel_events (id, timestamp, payload, inserted_at) VALUES (?, ?, ?, ?)",
                    (event_id, timestamp, payload, now),
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def count_events(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM intel_events")
            return cursor.fetchone()[0]

    def has_event(self, event_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM intel_events WHERE id = ?", (event_id,))
            return cursor.fetchone() is not None

    def get_all_event_ids(self) -> set:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id FROM intel_events")
            return {row[0] for row in cursor.fetchall()}


def route_through_gatekeeper(
    events: list[dict[str, Any]],
    cache: IntelCache | None = None,
    engine: GatekeeperEngine | None = None,
    dead_letter_path: str = "dead_letter.jsonl",
) -> list[dict[str, Any]]:
    """
    Filters events through ocaml-event-engine gatekeeper:
    - Drops duplicate events with zero database writes.
    - Writes invalid events to dead_letter.jsonl with zero database writes.
    - Inserts processed events into intel_cache.db and forwards them downstream.
    """
    db = cache or IntelCache()
    gatekeeper = engine or GatekeeperEngine(initial_seen=db.get_all_event_ids())
    forwarded: list[dict[str, Any]] = []

    for evt in events:
        eid = str(evt.get("id", ""))
        ts = int(evt.get("timestamp", 0))
        payload = str(evt.get("payload", ""))

        status, res_id, error = gatekeeper.evaluate(eid, ts, payload)

        if status == "processed":
            logger.info(f"[Gatekeeper] Processed event: {res_id}")
            db.insert_event(eid, ts, payload)
            forwarded.append(evt)
        elif status == "duplicate":
            logger.debug(f"[Gatekeeper] Discarding duplicate event: {res_id}")
            # Explicit invariant: zero SQLite writes on duplicate
        elif status == "invalid":
            logger.warning(f"[Gatekeeper] Routing invalid event to dead-letter: {res_id} ({error})")
            with open(dead_letter_path, "a", encoding="utf-8") as dlf:
                dlf.write(
                    json.dumps(
                        {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "event": evt,
                            "error": error or "Unknown validation error",
                        }
                    )
                    + "\n"
                )

    return forwarded
