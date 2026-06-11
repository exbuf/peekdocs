"""Tests for peekdocs.watcher.

The watcher is a long-running mode, so we don't test the observer loop end-to-
end here — that would need real file-system event timing and is the kind of
test that goes flaky on CI. Instead we test:

  - safety_checks against the matrix of (root | not root, system path | not,
    other user home | not, folder exists | not).
  - _enabled_patterns against the legacy `"on"` / `"off"` string enabled flag
    plus the modern bool.
  - scan_file against a real on-disk file, verifying the right NDJSON records
    land in the configured emit sink.

The CLI dispatch path is exercised by hand and by the existing pytest battery's
golden-import check; no need to spin up a subprocess just to verify argparse-
style flag consumption.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from peekdocs.watcher import (
    WatcherConfig,
    _enabled_patterns,
    _is_other_user_home,
    _is_system_path,
    safety_checks,
    scan_file,
)


# ── _enabled_patterns ────────────────────────────────────────────────


def test_enabled_patterns_bool_true():
    patterns = [{"enabled": True, "name": "n", "regex": "x"}]
    assert _enabled_patterns(patterns) == patterns


def test_enabled_patterns_bool_false():
    patterns = [{"enabled": False, "name": "n", "regex": "x"}]
    assert _enabled_patterns(patterns) == []


def test_enabled_patterns_string_on():
    patterns = [{"enabled": "on", "name": "n", "regex": "x"}]
    assert _enabled_patterns(patterns) == patterns


def test_enabled_patterns_string_off():
    patterns = [{"enabled": "off", "name": "n", "regex": "x"}]
    assert _enabled_patterns(patterns) == []


def test_enabled_patterns_empty_regex_dropped():
    patterns = [{"enabled": True, "name": "n", "regex": "   "}]
    assert _enabled_patterns(patterns) == []


def test_enabled_patterns_missing_regex_dropped():
    patterns = [{"enabled": True, "name": "n"}]
    assert _enabled_patterns(patterns) == []


def test_enabled_patterns_mixed():
    patterns = [
        {"enabled": True, "name": "a", "regex": "x"},
        {"enabled": "off", "name": "b", "regex": "y"},
        {"enabled": "on", "name": "c", "regex": "z"},
        {"enabled": False, "name": "d", "regex": "w"},
    ]
    kept = _enabled_patterns(patterns)
    assert [p["name"] for p in kept] == ["a", "c"]


# ── _is_system_path ────────────────────────────────────────────────


def test_is_system_path_unix_etc():
    # Only meaningful on non-Windows; the function returns False on
    # Windows for Unix-shaped paths.
    if os.name == "nt":
        pytest.skip("Unix path heuristic on Windows host")
    assert _is_system_path("/etc")
    assert _is_system_path("/etc/passwd")
    assert _is_system_path("/var/log")


def test_is_system_path_user_home_string_clean():
    # Pytest monkeypatches $HOME to a tempdir under /private/var/folders
    # on macOS, so testing against the live home would land inside the
    # system-path heuristic. Test against a fabricated user-home string
    # instead — the heuristic is path-based, not filesystem-state-based,
    # so this exercises the same code path without depending on env vars.
    if os.name == "nt":
        pytest.skip("Unix path heuristic on Windows host")
    assert not _is_system_path("/Users/somebody")
    assert not _is_system_path("/home/somebody")


def test_is_system_path_documents_folder_clean():
    if os.name == "nt":
        pytest.skip("Unix path heuristic on Windows host")
    assert not _is_system_path("/Users/somebody/Documents/work")
    assert not _is_system_path("/opt/myapp/data")


# ── _is_other_user_home ────────────────────────────────────────────────


def test_is_other_user_home_own_home():
    if os.name == "nt":
        pytest.skip("Unix-only heuristic")
    assert not _is_other_user_home(os.path.expanduser("~"))


def test_is_other_user_home_other_user():
    if os.name == "nt":
        pytest.skip("Unix-only heuristic")
    # A path inside /Users or /home that isn't the current user's home
    # should trigger. Use a synthetic path that almost certainly doesn't
    # exist; the function works on string prefixes, not filesystem state.
    if os.path.expanduser("~").startswith("/Users/"):
        assert _is_other_user_home("/Users/definitely-not-this-real-user")
    elif os.path.expanduser("~").startswith("/home/"):
        assert _is_other_user_home("/home/definitely-not-this-real-user")
    else:
        pytest.skip("home not under /Users or /home")


# ── safety_checks ────────────────────────────────────────────────


def test_safety_checks_folder_does_not_exist():
    cfg = WatcherConfig(
        folder="/this/path/definitely/does/not/exist",
        patterns=[{"enabled": True, "name": "x", "regex": "y"}],
    )
    proceed, errors, _ = safety_checks(cfg)
    assert proceed is False
    assert any("does not exist" in e or "not a directory" in e for e in errors)


def test_safety_checks_happy_path():
    with tempfile.TemporaryDirectory() as td:
        cfg = WatcherConfig(
            folder=td,
            patterns=[{"enabled": True, "name": "x", "regex": "y"}],
        )
        proceed, errors, _ = safety_checks(cfg)
        assert proceed is True
        assert errors == []


def test_safety_checks_system_path_warns_but_proceeds():
    # /tmp is in our system-path list. We want a warning, not an error,
    # because legitimate watchers do point at /tmp sometimes.
    if os.name == "nt":
        pytest.skip("Unix-only system-path warning")
    if not os.path.isdir("/tmp"):
        pytest.skip("/tmp not present on this host")
    cfg = WatcherConfig(
        folder="/tmp",
        patterns=[{"enabled": True, "name": "x", "regex": "y"}],
    )
    proceed, errors, warnings = safety_checks(cfg)
    assert proceed is True
    assert errors == []
    assert any("system path" in w for w in warnings)


def test_safety_checks_system_path_suppressed_when_allowed():
    if os.name == "nt":
        pytest.skip("Unix-only system-path warning")
    if not os.path.isdir("/tmp"):
        pytest.skip("/tmp not present on this host")
    cfg = WatcherConfig(
        folder="/tmp",
        patterns=[{"enabled": True, "name": "x", "regex": "y"}],
        allow_system_paths=True,
    )
    _, _, warnings = safety_checks(cfg)
    assert not any("system path" in w for w in warnings)


# ── scan_file ────────────────────────────────────────────────


def test_scan_file_emits_matches_to_sink(tmp_path: Path):
    # Write a tiny text file with a known pattern and verify scan_file
    # emits a single record with the right shape.
    target = tmp_path / "sample.txt"
    target.write_text(
        "the quick brown fox\n"
        "an ssn 123-45-6789 is on this line\n"
        "and a phone 555-555-5555 on this one\n",
        encoding="utf-8",
    )
    sink: list = []
    cfg = WatcherConfig(
        folder=str(tmp_path),
        patterns=[
            {"enabled": True, "name": "SSN",
             "regex": r"\b\d{3}-\d{2}-\d{4}\b"},
        ],
        collection_name="TestCollection",
        _emit_sink=sink,
    )
    scan_file(cfg, str(target))
    assert len(sink) == 1
    rec = sink[0]
    assert rec["pattern_name"] == "SSN"
    assert rec["collection"] == "TestCollection"
    assert rec["file"] == str(target)
    assert rec["line"] == 2
    assert "123-45-6789" in rec["matched_text"]


def test_scan_file_skips_missing_file(tmp_path: Path):
    sink: list = []
    cfg = WatcherConfig(
        folder=str(tmp_path),
        patterns=[{"enabled": True, "name": "x", "regex": "y"}],
        _emit_sink=sink,
    )
    # Should silently no-op rather than raise.
    scan_file(cfg, str(tmp_path / "does-not-exist.txt"))
    assert sink == []


def test_scan_file_multiple_patterns(tmp_path: Path):
    target = tmp_path / "log.txt"
    target.write_text(
        "TODO: replace this hardcoded url\n"
        "see http://example.com/inner for details\n",
        encoding="utf-8",
    )
    sink: list = []
    cfg = WatcherConfig(
        folder=str(tmp_path),
        patterns=[
            {"enabled": True, "name": "TODO", "regex": r"\bTODO\b"},
            {"enabled": True, "name": "URL", "regex": r"https?://\S+"},
            {"enabled": False, "name": "Disabled",
             "regex": r"some-disabled-pattern"},
        ],
        collection_name="Mixed",
        _emit_sink=sink,
    )
    scan_file(cfg, str(target))
    names = sorted(r["pattern_name"] for r in sink)
    assert names == ["TODO", "URL"]
