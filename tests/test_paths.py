"""Tests for peekdocs.paths — resource_path and find_tesseract."""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from peekdocs import paths


@pytest.fixture(autouse=True)
def _clear_tesseract_cache():
    """Reset find_tesseract's lru_cache between tests so each case starts
    from a clean slate. Without this, the first test's result would be
    memoized and every other test would see the same answer."""
    paths.find_tesseract.cache_clear()
    yield
    paths.find_tesseract.cache_clear()


def test_find_tesseract_returns_which_result_when_on_path():
    """When shutil.which finds tesseract, return it — don't consult fallbacks."""
    with patch("peekdocs.paths.shutil.which", return_value="/some/where/tesseract"):
        assert paths.find_tesseract() == "/some/where/tesseract"


def test_find_tesseract_falls_back_to_homebrew_arm64_on_macos():
    """Regression test for the reported bug: macOS GUI launches get a
    stripped PATH that omits /opt/homebrew/bin, so shutil.which returns
    None even when Tesseract is installed via Homebrew. The helper must
    check the Apple Silicon Homebrew path as a fallback."""
    homebrew_arm = "/opt/homebrew/bin/tesseract"

    def _isfile(p):
        return p == homebrew_arm

    def _access(p, mode):
        return p == homebrew_arm

    with patch("peekdocs.paths.shutil.which", return_value=None), \
         patch("peekdocs.paths.platform.system", return_value="Darwin"), \
         patch("peekdocs.paths.os.path.isfile", side_effect=_isfile), \
         patch("peekdocs.paths.os.access", side_effect=_access):
        assert paths.find_tesseract() == homebrew_arm


def test_find_tesseract_falls_back_to_homebrew_intel_on_macos():
    """Intel-Mac Homebrew installs at /usr/local/bin instead."""
    homebrew_intel = "/usr/local/bin/tesseract"

    def _isfile(p):
        return p == homebrew_intel

    def _access(p, mode):
        return p == homebrew_intel

    with patch("peekdocs.paths.shutil.which", return_value=None), \
         patch("peekdocs.paths.platform.system", return_value="Darwin"), \
         patch("peekdocs.paths.os.path.isfile", side_effect=_isfile), \
         patch("peekdocs.paths.os.access", side_effect=_access):
        assert paths.find_tesseract() == homebrew_intel


def test_find_tesseract_returns_none_when_missing_everywhere():
    """No PATH hit, no fallback hit — signal genuine absence."""
    with patch("peekdocs.paths.shutil.which", return_value=None), \
         patch("peekdocs.paths.platform.system", return_value="Darwin"), \
         patch("peekdocs.paths.os.path.isfile", return_value=False):
        assert paths.find_tesseract() is None


def test_find_tesseract_skips_non_executable_matches():
    """A file that exists but isn't executable (e.g., a stray text file
    someone named ``tesseract``) must not be reported as a valid install."""
    homebrew_arm = "/opt/homebrew/bin/tesseract"
    with patch("peekdocs.paths.shutil.which", return_value=None), \
         patch("peekdocs.paths.platform.system", return_value="Darwin"), \
         patch("peekdocs.paths.os.path.isfile", return_value=True), \
         patch("peekdocs.paths.os.access", return_value=False):
        assert paths.find_tesseract() is None


def test_find_tesseract_checks_windows_program_files():
    """Windows-installed Tesseract usually lives under Program Files,
    which won't be on PATH for GUI-launched processes either."""
    win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    def _isfile(p):
        return p == win_path

    def _access(p, mode):
        return p == win_path

    with patch("peekdocs.paths.shutil.which", return_value=None), \
         patch("peekdocs.paths.platform.system", return_value="Windows"), \
         patch("peekdocs.paths.os.path.isfile", side_effect=_isfile), \
         patch("peekdocs.paths.os.access", side_effect=_access):
        assert paths.find_tesseract() == win_path


def test_resource_path_returns_absolute_path():
    """Sanity check that resource_path still returns an absolute path
    even when the resource itself doesn't exist. Callers own the exists
    check."""
    result = paths.resource_path("no-such-file.txt")
    assert os.path.isabs(result)


# ── format_bytes ───────────────────────────────────────────────


def test_format_bytes_base_tier_uses_bytes_word():
    """Below 1000 bytes → literal 'bytes' with no decimals. Reports show
    this format for tiny files."""
    assert paths.format_bytes(0) == "0 bytes"
    assert paths.format_bytes(1) == "1 bytes"
    assert paths.format_bytes(999) == "999 bytes"


def test_format_bytes_kb_tier():
    """1 KB (1000 bytes) up to 1 MB — 'KB' with two decimals."""
    assert paths.format_bytes(1_000) == "1.00 KB"
    assert paths.format_bytes(1_500) == "1.50 KB"
    assert paths.format_bytes(999_999) == "1000.00 KB"


def test_format_bytes_mb_tier():
    """1 MB up to 1 GB — 'MB' with two decimals."""
    assert paths.format_bytes(1_000_000) == "1.00 MB"
    assert paths.format_bytes(2_100_000) == "2.10 MB"
    assert paths.format_bytes(999_999_999) == "1000.00 MB"


def test_format_bytes_gb_tier():
    """1 GB and above — 'GB' with two decimals. The tier that reporter's
    old fmt_size lacked; large disk-usage displays used to overflow into
    thousand-MB territory."""
    assert paths.format_bytes(1_000_000_000) == "1.00 GB"
    assert paths.format_bytes(3_500_000_000) == "3.50 GB"


def test_reporter_fmt_size_delegates_to_format_bytes():
    """Back-compat: reporter.fmt_size is a thin re-export. Anyone
    importing it from peekdocs.reporter (cli.py + external consumers)
    keeps working after the consolidation."""
    from peekdocs.reporter import fmt_size

    assert fmt_size(0) == paths.format_bytes(0)
    assert fmt_size(1_500) == paths.format_bytes(1_500)
    assert fmt_size(3_500_000_000) == paths.format_bytes(3_500_000_000)
