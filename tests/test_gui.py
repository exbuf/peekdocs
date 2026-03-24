"""Tests for the GUI module — headless-safe, no display required."""

import os
import pytest
from docsearch.gui import _build_command_from_values, _parse_summary_text


def test_build_command_basic(tmp_path):
    cmd = _build_command_from_values(
        search_text="budget revenue",
        folder=str(tmp_path),
        and_mode=False, recursive=False, fuzzy=False,
        wildcard=False, ocr=False, regex=False,
        exclude="", file_types="", proximity="",
        context_before="", context_after="",
    )
    assert cmd is not None
    assert "-q" in cmd
    assert cmd[-2:] == ["budget", "revenue"]
    assert "-a" not in cmd
    assert "-r" not in cmd


def test_build_command_all_flags(tmp_path):
    cmd = _build_command_from_values(
        search_text="hello world",
        folder=str(tmp_path),
        and_mode=True, recursive=True, fuzzy=True,
        wildcard=False, ocr=True, regex=False,
        exclude="draft,old", file_types="pdf,docx",
        proximity="5", context_before="3", context_after="2",
    )
    assert cmd is not None
    assert "-a" in cmd
    assert "-r" in cmd
    assert "-z" in cmd
    assert "-O" in cmd
    idx_n = cmd.index("-n")
    assert cmd[idx_n + 1] == "draft,old"
    idx_t = cmd.index("-t")
    assert cmd[idx_t + 1] == "pdf,docx"
    idx_p = cmd.index("-p")
    assert cmd[idx_p + 1] == "5"
    idx_B = cmd.index("-B")
    assert cmd[idx_B + 1] == "3"
    idx_A = cmd.index("-A")
    assert cmd[idx_A + 1] == "2"
    assert cmd[-2:] == ["hello", "world"]


def test_build_command_empty_search(tmp_path):
    result = _build_command_from_values(
        search_text="",
        folder=str(tmp_path),
        and_mode=False, recursive=False, fuzzy=False,
        wildcard=False, ocr=False, regex=False,
        exclude="", file_types="", proximity="",
        context_before="", context_after="",
    )
    assert result is None


def test_build_command_invalid_folder():
    result = _build_command_from_values(
        search_text="budget",
        folder="/nonexistent/path/abc123",
        and_mode=False, recursive=False, fuzzy=False,
        wildcard=False, ocr=False, regex=False,
        exclude="", file_types="", proximity="",
        context_before="", context_after="",
    )
    assert result is None


def test_build_command_invalid_proximity(tmp_path):
    result = _build_command_from_values(
        search_text="budget",
        folder=str(tmp_path),
        and_mode=False, recursive=False, fuzzy=False,
        wildcard=False, ocr=False, regex=False,
        exclude="", file_types="", proximity="abc",
        context_before="", context_after="",
    )
    assert result is None


def test_build_command_quoted_phrase(tmp_path):
    cmd = _build_command_from_values(
        search_text='"annual report" budget',
        folder=str(tmp_path),
        and_mode=False, recursive=False, fuzzy=False,
        wildcard=False, ocr=False, regex=False,
        exclude="", file_types="", proximity="",
        context_before="", context_after="",
    )
    assert cmd is not None
    assert cmd[-2:] == ["annual report", "budget"]


def test_build_command_flags_in_search(tmp_path):
    result = _build_command_from_values(
        search_text="-a budget revenue",
        folder=str(tmp_path),
        and_mode=False, recursive=False, fuzzy=False,
        wildcard=False, ocr=False, regex=False,
        exclude="", file_types="", proximity="",
        context_before="", context_after="",
    )
    assert result == "FLAGS_IN_SEARCH"


def test_build_command_flags_in_search_various(tmp_path):
    for flag in ["-r", "-z", "-w", "-O", "-x", "-n", "-t", "-p"]:
        result = _build_command_from_values(
            search_text=f"{flag} budget",
            folder=str(tmp_path),
            and_mode=False, recursive=False, fuzzy=False,
            wildcard=False, ocr=False, regex=False,
            exclude="", file_types="", proximity="",
            context_before="", context_after="",
        )
        assert result == "FLAGS_IN_SEARCH", f"Expected FLAGS_IN_SEARCH for {flag}"


def test_build_command_cores(tmp_path):
    cmd = _build_command_from_values(
        search_text="budget",
        folder=str(tmp_path),
        and_mode=False, recursive=False, fuzzy=False,
        wildcard=False, ocr=False, regex=False,
        exclude="", file_types="", proximity="",
        context_before="", context_after="",
        cores="4",
    )
    assert cmd is not None
    idx = cmd.index("-c")
    assert cmd[idx + 1] == "4"


def test_build_command_invalid_cores(tmp_path):
    result = _build_command_from_values(
        search_text="budget",
        folder=str(tmp_path),
        and_mode=False, recursive=False, fuzzy=False,
        wildcard=False, ocr=False, regex=False,
        exclude="", file_types="", proximity="",
        context_before="", context_after="",
        cores="abc",
    )
    assert result is None


def test_build_command_specific_files(tmp_path):
    cmd = _build_command_from_values(
        search_text="budget",
        folder=str(tmp_path),
        and_mode=False, recursive=False, fuzzy=False,
        wildcard=False, ocr=False, regex=False,
        exclude="", file_types="", proximity="",
        context_before="", context_after="",
        specific_files="report.pdf,notes.txt",
    )
    assert cmd is not None
    idx = cmd.index("-f")
    assert cmd[idx + 1] == "report.pdf,notes.txt"


def test_build_command_append_name(tmp_path):
    cmd = _build_command_from_values(
        search_text="budget",
        folder=str(tmp_path),
        and_mode=False, recursive=False, fuzzy=False,
        wildcard=False, ocr=False, regex=False,
        exclude="", file_types="", proximity="",
        context_before="", context_after="",
        append_name="combined_report",
    )
    assert cmd is not None
    idx = cmd.index("-sa")
    assert cmd[idx + 1] == "combined_report"


def test_parse_summary_with_ansi():
    stdout = (
        "\r  [########] 5/5 done\n"
        "Files searched: 5 (1.23 MB)\n"
        "Found \033[1;94m12\033[0m match(es).\n"
        "Results ==> /tmp/docs\n"
        "  docsearch_results.txt (2.50 KB), docsearch_results.docx (15.30 KB)\n"
        "Elapsed time: 1.45 seconds, Cores used: 4 of 8\n"
    )
    result = _parse_summary_text(stdout)
    assert "12" in result
    assert "5" in result
    assert "1.45" in result


def test_parse_summary_empty():
    assert _parse_summary_text("") == ""
    assert _parse_summary_text(None) == ""
