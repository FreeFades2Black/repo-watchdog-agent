"""
Unit Test Suite for Repo Watchdog Agent
Validates GitHub REST API tool, agent synthesis, and markdown digest generation.
"""

from unittest.mock import MagicMock, patch

from agent_watchdog import (
    build_deterministic_digest,
    inspect_repository_trail,
    main,
    summon_the_watchman,
)


def test_inspect_repository_trail_success(monkeypatch):
    """Test repository trail scanner parses commits and merged pull requests."""
    fake_commits = [
        {
            "sha": "a1b2c3d4e5f6",
            "commit": {
                "author": {"name": "Roland Deschain"},
                "message": "feat(core): harden sentinel boundary\nExtra details"
            }
        },
        {
            "sha": "f9e8d7c6b5a4",
            "commit": {
                "author": {"name": "Eddie Dean"},
                "message": "fix(api): handle token rotation gracefully"
            }
        }
    ]

    fake_prs = [
        {
            "number": 101,
            "title": "Add multi-agent consensus policy",
            "merged_at": "2099-01-01T12:00:00Z",
            "user": {"login": "gunslinger"}
        }
    ]

    def mock_get(url, headers=None, timeout=10):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        if "commits" in url:
            mock_resp.json.return_value = fake_commits
        elif "pulls" in url:
            mock_resp.json.return_value = fake_prs
        return mock_resp

    monkeypatch.setattr("requests.get", mock_get)

    report = inspect_repository_trail("microsoft/agent-framework")

    assert "=== Trail Report for: microsoft/agent-framework ===" in report
    assert "Recent Commits Count: 2" in report
    assert "- [a1b2c3d] Roland Deschain: feat(core): harden sentinel boundary" in report
    assert "- [f9e8d7c] Eddie Dean: fix(api): handle token rotation gracefully" in report
    assert "Merged Pull Requests: 1" in report
    assert "PR #101: Add multi-agent consensus policy (by gunslinger)" in report


def test_inspect_repository_trail_api_error(monkeypatch):
    """Test repository scanner gracefully logs non-200 responses."""
    def mock_get(url, headers=None, timeout=10):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        return mock_resp

    monkeypatch.setattr("requests.get", mock_get)

    report = inspect_repository_trail("nonexistent/repo")
    assert "Failed to read commits. Status: 404" in report
    assert "Failed to read PRs. Status: 404" in report


def test_summon_the_watchman():
    """Verify sentinel agent instantiation and instructions."""
    agent = summon_the_watchman()
    assert agent is not None
    assert hasattr(agent, "run")
    assert len(agent.tools) == 1
    assert agent.tools[0].__name__ == "inspect_repository_trail"


def test_build_deterministic_digest():
    """Verify markdown structure, breaking changes section, and sentinel risk posture."""
    mock_reports = {
        "microsoft/agent-framework": (
            "=== Trail Report for: microsoft/agent-framework ===\n"
            "Recent Commits Count: 1\n"
            "- [1234567] Dev: chore(ci): update workflow\n"
            "Merged Pull Requests: 1\n"
            "- PR #42: Feat: add tool decorator (by dev)"
        )
    }

    digest = build_deterministic_digest(mock_reports, ["microsoft/agent-framework"])
    assert "## 🚨 1. High Impact / Breaking Changes" in digest
    assert "## ✨ 2. New Features & Framework Changes" in digest
    assert "- PR #42: Feat: add tool decorator (by dev)" in digest
    assert "## 🔧 3. Routine Chores, Maintenance & Documentation" in digest
    assert "- [1234567] Dev: chore(ci): update workflow" in digest
    assert "## 🧭 4. Sentinel Risk & Action Posture" in digest
    assert "🟢 `HEALTHY`" in digest


def test_main_cli_execution(tmp_path, monkeypatch):
    """Verify main entrypoint handles CLI flags and writes output file."""
    monkeypatch.setattr(
        "sys.argv",
        ["agent_watchdog.py", "--dry-run", "--output-dir", str(tmp_path), "--repos", "microsoft/agent-framework"]
    )

    with patch("agent_watchdog.inspect_repository_trail") as mock_inspect:
        mock_inspect.return_value = "=== Trail Report ===\n- [abc1234] Test User: chore: test commit"
        main()

    files = list(tmp_path.glob("digest-*.md"))
    assert len(files) == 1
    content = files[0].read_text(encoding="utf-8")
    assert "Daily Repository Intelligence Digest" in content
    assert "Test User: chore: test commit" in content
