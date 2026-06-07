"""
Smoke tests for the built PyInstaller CLI binary.

These tests run the actual binary via subprocess (not the in-process
``from peekdocs.cli import main`` path used by the rest of the test suite).
Their job is to exercise the shell-binary boundary on Windows — argument
parsing, shell wildcard handling, console encoding, Unicode filenames,
backslash escapes in regex — that the standard test harness skips.

Activation:
    Set the PEEKDOCS_BINARY environment variable to the path of the built
    CLI executable. When unset, the entire module skips cleanly so a
    regular ``pytest tests/`` run is unaffected.

Platform:
    Currently Windows-only. The workflow at
    .github/workflows/build-release.yml runs these on windows-latest after
    the PyInstaller build, before the artifact upload — so a binary that
    fails smoke tests never publishes to a release.

    To extend to Linux/macOS later: drop the ``sys.platform`` skip below.
    The binary path semantics work the same on all three OSes; macOS will
    additionally need ``xattr -dr com.apple.quarantine`` applied to the
    binary before invocation.
"""
import os
import subprocess
import sys
import time

import pytest

BINARY = os.environ.get("PEEKDOCS_BINARY")

pytestmark = [
    pytest.mark.skipif(not BINARY, reason="PEEKDOCS_BINARY not set"),
    pytest.mark.skipif(sys.platform != "win32", reason="Windows-only initially"),
]


def run(args, cwd=None, timeout=60):
    """Invoke the CLI binary with the given arguments.

    Uses ``errors="replace"`` because peekdocs writes Unicode punctuation
    (em-dashes, smart quotes) to stdout, and on Windows the console
    defaults to cp1252 — strict UTF-8 decoding crashes in subprocess's
    reader thread and turns ``stdout`` into ``None``. Replacing invalid
    bytes with ``?`` keeps stdout decodable while preserving all the
    ASCII tokens the assertions actually check.
    """
    return subprocess.run(
        [BINARY] + list(args),
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


@pytest.fixture
def text_files(tmp_path):
    """Three plain-text files whose contents match the wildcard ``budg*``."""
    (tmp_path / "a.txt").write_text("budget")
    (tmp_path / "b.txt").write_text("budgets")
    (tmp_path / "c.txt").write_text("budgeting")
    return tmp_path


# ── Sanity ─────────────────────────────────────────────────────────────

def test_version():
    r = run(["--version"], timeout=15)
    assert r.returncode == 0, f"stdout={r.stdout!r} stderr={r.stderr!r}"
    assert "peekdocs" in r.stdout.lower()


def test_check():
    r = run(["--check"], timeout=30)
    assert r.returncode == 0, f"stdout={r.stdout!r} stderr={r.stderr!r}"


# ── Backslash regex (shell-quoting boundary) ──────────────────────────

def test_backslash_regex_survives_shell(tmp_path):
    """``\\b`` and ``\\d`` must survive shell parsing as regex metachars."""
    (tmp_path / "order.txt").write_text("REF-12345")
    (tmp_path / "noise.txt").write_text("nothing to find here")

    r = run(["-x", r"\bREF-\d{4,}\b", "."], cwd=tmp_path)

    assert r.returncode == 0, f"stdout={r.stdout!r} stderr={r.stderr!r}"
    assert "1 file(s)" in r.stdout, (
        f"expected one match for REF-12345; got: {r.stdout!r}"
    )


# ── Shell wildcard handling ───────────────────────────────────────────

def test_wildcard_passes_literal(text_files):
    """cmd.exe and PowerShell pass ``budg*`` literally; peekdocs expands it."""
    r = run(["-w", "budg*", "."], cwd=text_files)
    assert r.returncode == 0, f"stdout={r.stdout!r} stderr={r.stderr!r}"
    # budget / budgets / budgeting across three files
    assert "3 file(s)" in r.stdout, (
        f"expected three wildcard matches; got: {r.stdout!r}"
    )


# ── ``-t`` extension case sensitivity ──────────────────────────────────

def test_extension_case_parity(tmp_path):
    """``-t pdf`` and ``-t PDF`` must produce identical results."""
    (tmp_path / "test.pdf").write_text("budget")

    lower = run(["-t", "pdf", "budget", "."], cwd=tmp_path)
    upper = run(["-t", "PDF", "budget", "."], cwd=tmp_path)

    assert lower.returncode == upper.returncode, (
        f"return codes differ: lower={lower.returncode} upper={upper.returncode}"
    )
    # Both forms should find (or both should miss) the .pdf file
    assert ("1 file(s)" in lower.stdout) == ("1 file(s)" in upper.stdout), (
        f"\nlowercase stdout: {lower.stdout!r}\n"
        f"uppercase stdout: {upper.stdout!r}"
    )


# ── Unicode filename round-trip ────────────────────────────────────────

def test_unicode_filename_in_report(tmp_path):
    """A CJK filename must round-trip through the UTF-8 report file intact."""
    (tmp_path / "北京报告.txt").write_text("budget", encoding="utf-8")

    r = run(["budget", "."], cwd=tmp_path)
    assert r.returncode == 0, f"stdout={r.stdout!r} stderr={r.stderr!r}"

    report = tmp_path / "peekdocs_standard_results.txt"
    assert report.exists(), "expected report file was not written"

    content = report.read_text(encoding="utf-8")
    assert "北京报告" in content, (
        f"CJK filename missing from report. First 500 chars: {content[:500]!r}"
    )


# ── PyInstaller startup tax ────────────────────────────────────────────

def test_startup_under_six_seconds():
    """Documented Windows startup tax is 2-4s; assert a generous upper bound."""
    t0 = time.perf_counter()
    r = run(["--version"], timeout=15)
    elapsed = time.perf_counter() - t0
    assert r.returncode == 0
    assert elapsed < 6.0, (
        f"startup took {elapsed:.2f}s; documented expectation is 2-4s, "
        f"hard ceiling 6s"
    )
