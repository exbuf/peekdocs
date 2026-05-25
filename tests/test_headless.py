"""Verify the CLI is import-clean and runnable on a headless server.

A headless server (no DISPLAY, no Tk libraries installed) is a real
deployment target — cron jobs, containers, locked-down VMs, fleet
scanners. peekdocs ships a GUI, but the GUI is optional; the CLI must
work even when neither ``tkinter`` nor ``customtkinter`` is importable.

These tests install an import-blocker that raises ImportError for any
Tk-related module, then exercise the main CLI paths through
``peekdocs.cli.main``. If any CLI code path reaches Tk at import time
or call time, the test catches it.
"""

import importlib.abc
import io
import os
import sys

import pytest


TK_MODULES = {
    "customtkinter",
    "tkinter",
    "_tkinter",
    "tkinter.font",
    "tkinter.ttk",
    "tkinter.filedialog",
    "tkinter.messagebox",
    "tkinter.simpledialog",
    "tkinter.scrolledtext",
    "tkinter.colorchooser",
}


class _HeadlessBlocker(importlib.abc.MetaPathFinder):
    """Block Tk-related imports at the spec resolution stage."""

    def find_spec(self, fullname, path, target=None):
        if fullname in TK_MODULES or fullname.startswith("customtkinter."):
            raise ImportError(f"headless test: '{fullname}' is not available")
        return None


@pytest.fixture
def headless(monkeypatch):
    """Make every Tk import raise ImportError for the duration of the test.

    Clears any cached Tk modules from ``sys.modules`` and installs a
    meta-path finder so future imports also fail.
    """
    for mod in list(sys.modules):
        if mod in TK_MODULES or mod.startswith("customtkinter") or mod.startswith("tkinter"):
            monkeypatch.delitem(sys.modules, mod, raising=False)
    blocker = _HeadlessBlocker()
    monkeypatch.setattr(sys, "meta_path", [blocker, *sys.meta_path])
    yield
    # Cleanup is implicit via monkeypatch.


def test_cli_imports_without_tk(headless):
    """peekdocs.cli must import cleanly with all Tk modules blocked."""
    # Force a fresh import so we go through the blocker.
    sys.modules.pop("peekdocs.cli", None)
    import peekdocs.cli  # noqa: F401

    # And no Tk module should have been pulled in transitively.
    assert "tkinter" not in sys.modules
    assert "customtkinter" not in sys.modules


def test_help_runs_headless(headless, capsys):
    """--help is the canonical "is it installed" probe and must work headless."""
    sys.modules.pop("peekdocs.cli", None)
    from peekdocs.cli import main

    rc = main(["--help"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "peekdocs" in out.lower()


def test_check_runs_headless_and_reports_missing_gui(headless, capsys):
    """--check must complete and explicitly call out the missing GUI dep."""
    sys.modules.pop("peekdocs.cli", None)
    from peekdocs.cli import main

    rc = main(["--check"])
    assert rc == 0
    out = capsys.readouterr().out
    # The GUI line should be present and indicate customtkinter is unavailable.
    assert "customtkinter" in out
    assert "not installed" in out or "missing" in out.lower()


def test_stdout_search_runs_headless(headless, tmp_path, monkeypatch, capsys):
    """A real --stdout search produces valid JSON on a headless system."""
    sys.modules.pop("peekdocs.cli", None)
    from peekdocs.cli import main

    # Tiny corpus so the test stays fast.
    (tmp_path / "a.txt").write_text("password = secret123\n")
    (tmp_path / "b.txt").write_text("no match here\n")
    monkeypatch.chdir(tmp_path)

    rc = main(["password", "--stdout"])
    assert rc == 0
    out = capsys.readouterr().out
    # --stdout must emit a JSON object — find the opening brace.
    brace = out.find("{")
    assert brace >= 0, f"no JSON object in --stdout output: {out!r}"
    import json
    payload = json.loads(out[brace:])
    assert payload["matches_found"] >= 1
    assert "generator" in payload
