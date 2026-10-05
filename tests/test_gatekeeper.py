"""
Tests for OCaml Gatekeeper Ingress Integration.
Validates zero SQLite writes on duplicate inputs, dead-letter routing for invalid records,
and downstream forwarding for processed events.
"""

import json
import os

import pytest

from src.watchdog.gatekeeper import IntelCache, route_through_gatekeeper


@pytest.fixture
def temp_cache(tmp_path):
    db_file = tmp_path / "test_intel_cache.db"
    return IntelCache(str(db_file))


@pytest.fixture
def temp_dead_letter(tmp_path):
    return str(tmp_path / "dead_letter.jsonl")


def test_duplicates_produce_zero_sqlite_writes(temp_cache, temp_dead_letter):
    """
    CRITICAL INVARIANT TEST:
    Asserts that duplicate event arrivals produce ZERO additional SQLite writes.
    """
    events = [
        {"id": "CVE-2026-0001", "timestamp": 1728100000, "payload": "Critical RCE in agent sandbox"},
        {"id": "CVE-2026-0001", "timestamp": 1728100005, "payload": "Critical RCE duplicate notification"},
        {"id": "CVE-2026-0002", "timestamp": 1728100010, "payload": "Buffer overflow in protocol parser"},
    ]

    # First run
    forwarded = route_through_gatekeeper(
        events,
        cache=temp_cache,
        dead_letter_path=temp_dead_letter,
    )

    # Only 2 distinct events should be forwarded downstream
    assert len(forwarded) == 2
    assert [e["id"] for e in forwarded] == ["CVE-2026-0001", "CVE-2026-0002"]

    # Invariant: SQLite must contain strictly 2 records, zero writes from the duplicate
    assert temp_cache.count_events() == 2

    # Second arrival of the same batch must produce ZERO additional writes
    repeat_forwarded = route_through_gatekeeper(
        events,
        cache=temp_cache,
        dead_letter_path=temp_dead_letter,
    )
    assert len(repeat_forwarded) == 0
    assert temp_cache.count_events() == 2


def test_invalid_records_routed_to_dead_letter(temp_cache, temp_dead_letter):
    """
    Asserts that invalid records (blank ID, empty payload) produce zero SQLite writes
    and are captured in dead_letter.jsonl.
    """
    invalid_events = [
        {"id": "", "timestamp": 1728100020, "payload": "Missing event ID"},
        {"id": "CVE-2026-0003", "timestamp": 1728100025, "payload": "   "},
    ]

    forwarded = route_through_gatekeeper(
        invalid_events,
        cache=temp_cache,
        dead_letter_path=temp_dead_letter,
    )

    assert len(forwarded) == 0
    assert temp_cache.count_events() == 0

    assert os.path.exists(temp_dead_letter)
    with open(temp_dead_letter, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]

    assert len(lines) == 2
    assert "error" in lines[0]
    assert "error" in lines[1]
