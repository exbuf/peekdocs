"""Tests for peekdocs.gui._error_guard — the gui_guard context manager."""
from __future__ import annotations

import os

import pytest

from peekdocs.gui._error_guard import gui_guard, gui_race_guard


def test_gui_guard_swallows_exception(tmp_path, monkeypatch):
    """A raised exception inside gui_guard does not propagate."""
    monkeypatch.chdir(tmp_path)
    # No assertion needed — the with-block would re-raise if the
    # guard didn't swallow. Pytest's "no exception" is the assertion.
    with gui_guard("test operation"):
        raise RuntimeError("boom")


def test_gui_guard_logs_to_error_log(tmp_path, monkeypatch):
    """gui_guard writes a diagnostic line to peekdocs_errors.log in cwd."""
    monkeypatch.chdir(tmp_path)
    with gui_guard("save config"):
        raise ValueError("disk full")

    log_path = tmp_path / "peekdocs_errors.log"
    assert log_path.exists()
    content = log_path.read_text()
    assert "gui_guard swallowed: save config" in content
    assert "ValueError" in content
    assert "disk full" in content


def test_gui_guard_no_log_when_no_exception(tmp_path, monkeypatch):
    """No exception → no log line. The guard is a no-op on the happy path."""
    monkeypatch.chdir(tmp_path)
    with gui_guard("happy path"):
        pass

    log_path = tmp_path / "peekdocs_errors.log"
    # Log file may not even exist; if it does, it should not mention
    # this operation.
    if log_path.exists():
        assert "happy path" not in log_path.read_text()


def test_gui_guard_survives_log_write_failure(tmp_path, monkeypatch):
    """If the log-write itself fails, the guard still swallows the
    original exception. Diagnostic telemetry must not cascade into
    primary error handling."""
    monkeypatch.chdir(tmp_path)
    # Make cwd non-writable so the log write fails
    os.chmod(tmp_path, 0o500)
    try:
        # Should not raise — the log-write failure is itself swallowed
        with gui_guard("op"):
            raise RuntimeError("original")
    finally:
        os.chmod(tmp_path, 0o700)  # restore for pytest cleanup


def test_gui_race_guard_swallows_exception():
    """gui_race_guard swallows without logging."""
    with gui_race_guard():
        raise RuntimeError("tk race")


def test_gui_race_guard_does_not_log(tmp_path, monkeypatch):
    """gui_race_guard writes nothing to peekdocs_errors.log."""
    monkeypatch.chdir(tmp_path)
    with gui_race_guard():
        raise RuntimeError("tk race that must stay silent")

    log_path = tmp_path / "peekdocs_errors.log"
    assert not log_path.exists() or "tk race" not in log_path.read_text()


def test_multiple_guards_stack(tmp_path, monkeypatch):
    """Nested guards behave — outer one doesn't catch what inner one
    already swallowed."""
    monkeypatch.chdir(tmp_path)

    outer_reached_finally = False
    try:
        with gui_guard("outer"):
            with gui_guard("inner"):
                raise ValueError("inner boom")
            # If inner guard did its job, we get here.
            outer_reached_finally = True
    except Exception:
        pytest.fail("Inner guard should have swallowed")

    assert outer_reached_finally
    content = (tmp_path / "peekdocs_errors.log").read_text()
    assert "inner" in content
    assert "outer" not in content
