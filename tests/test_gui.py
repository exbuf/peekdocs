"""Tests for the GUI module — headless-safe, no display required."""

import os
import pytest
from peekdocs.gui import _build_command_from_values, _parse_summary_text, _parse_matched_files, _parse_inverse_files


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


def test_build_command_rank(tmp_path):
    on = _build_command_from_values(
        search_text="budget", folder=str(tmp_path),
        and_mode=False, recursive=False, fuzzy=False,
        wildcard=False, ocr=False, regex=False,
        exclude="", file_types="", proximity="",
        context_before="", context_after="", index_search=True, rank=True,
    )
    assert "--rank" in on
    off = _build_command_from_values(
        search_text="budget", folder=str(tmp_path),
        and_mode=False, recursive=False, fuzzy=False,
        wildcard=False, ocr=False, regex=False,
        exclude="", file_types="", proximity="",
        context_before="", context_after="", index_search=True, rank=False,
    )
    assert "--rank" not in off


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
        "  peekdocs_standard_results.txt (2.50 KB), peekdocs_standard_results.docx (15.30 KB)\n"
        "Elapsed time: 1.45 seconds, Cores used: 4 of 8\n"
    )
    result = _parse_summary_text(stdout)
    assert "12" in result
    assert "5" in result
    assert "1.23 MB" in result
    assert "1.45" in result


def test_parse_summary_with_errors():
    stdout = (
        "Files searched: 97 (4.23 MB)\n"
        "Found \033[1;94m5\033[0m match(es).\n"
        "Results ==> /tmp/docs\n"
        "  peekdocs_standard_results.txt (2.50 KB), peekdocs_standard_results.docx (15.30 KB)\n"
        "Elapsed time: 2.34 seconds, Cores used: 4 of 8\n"
        "Errors logged to peekdocs_errors.log (3 error(s))\n"
    )
    result = _parse_summary_text(stdout)
    assert "5 match(es)" in result
    assert "97 file(s) searched" in result
    assert "3 file(s) could not be read" in result


def test_parse_summary_empty():
    assert _parse_summary_text("") == ""
    assert _parse_summary_text(None) == ""


def test_parse_matched_files(tmp_path):
    results = tmp_path / "peekdocs_standard_results.txt"
    results.write_text(
        'Program name: peekdocs\n'
        '\n'
        'Document: report.pdf (2 matches), Line: 5, Match:\n'
        f'({tmp_path})\n'
        '"some matched text"\n'
        '\n'
        'Document: notes.txt (1 match), Line: 12, Match:\n'
        f'({tmp_path})\n'
        '"another match"\n'
        '\n'
        'Document: report.pdf (2 matches), Line: 20, Match:\n'
        f'({tmp_path})\n'
        '"duplicate file should not repeat"\n'
    )
    files = _parse_matched_files(str(tmp_path))
    assert len(files) == 2
    assert files[0][1] == "report.pdf"
    assert files[0][2] == 2  # report.pdf appears twice
    assert files[1][1] == "notes.txt"
    assert files[1][2] == 1  # notes.txt appears once


def test_parse_matched_files_empty(tmp_path):
    assert _parse_matched_files(str(tmp_path)) == []


def test_build_command_index_search_default(tmp_path):
    """By default (index_search=False), --no-index is appended."""
    cmd = _build_command_from_values(
        search_text="budget",
        folder=str(tmp_path),
        and_mode=False, recursive=False, fuzzy=False,
        wildcard=False, ocr=False, regex=False,
        exclude="", file_types="", proximity="",
        context_before="", context_after="",
    )
    assert cmd is not None
    assert "--no-index" in cmd


def test_build_command_index_search_enabled(tmp_path):
    """With index_search=True, --no-index is NOT in the command."""
    cmd = _build_command_from_values(
        search_text="budget",
        folder=str(tmp_path),
        and_mode=False, recursive=False, fuzzy=False,
        wildcard=False, ocr=False, regex=False,
        exclude="", file_types="", proximity="",
        context_before="", context_after="",
        index_search=True,
    )
    assert cmd is not None
    assert "--no-index" not in cmd


def test_build_command_inverse(tmp_path):
    """With inverse=True, --inverse appears in the command."""
    cmd = _build_command_from_values(
        search_text="budget",
        folder=str(tmp_path),
        and_mode=False, recursive=False, fuzzy=False,
        wildcard=False, ocr=False, regex=False,
        exclude="", file_types="", proximity="",
        context_before="", context_after="",
        inverse=True,
    )
    assert cmd is not None
    assert "--inverse" in cmd


def test_build_command_inverse_default(tmp_path):
    """By default, --inverse does NOT appear in the command."""
    cmd = _build_command_from_values(
        search_text="budget",
        folder=str(tmp_path),
        and_mode=False, recursive=False, fuzzy=False,
        wildcard=False, ocr=False, regex=False,
        exclude="", file_types="", proximity="",
        context_before="", context_after="",
    )
    assert cmd is not None
    assert "--inverse" not in cmd


def test_parse_summary_inverse():
    """_parse_summary_text handles inverse search output."""
    stdout = (
        "Files searched: 10 (1.50 MB)\n"
        "Found 3 file(s) WITHOUT matches (out of 10 searched).\n"
        "Elapsed time: 0.42 seconds, Cores used: 4 of 8\n"
    )
    result = _parse_summary_text(stdout)
    assert "10 file(s) searched" in result
    assert "3 file(s) WITHOUT matches" in result


def test_build_command_expression(tmp_path):
    """Expression text must be placed immediately after -e flag."""
    cmd = _build_command_from_values(
        search_text="(budget OR revenue) AND NOT draft",
        folder=str(tmp_path),
        and_mode=False, recursive=True, fuzzy=False,
        wildcard=False, ocr=False, regex=False,
        exclude="", file_types="", proximity="",
        context_before="2", context_after="2",
        expression=True,
    )
    assert cmd is not None
    idx = cmd.index("-e")
    assert cmd[idx + 1] == "(budget OR revenue) AND NOT draft"
    assert "-a" not in cmd
    assert "-r" in cmd
    assert "-B" in cmd


def test_build_command_whole_word(tmp_path):
    """Whole word flag (-W) should be included in the command."""
    cmd = _build_command_from_values(
        search_text="bob",
        folder=str(tmp_path),
        and_mode=False, recursive=False, fuzzy=False,
        wildcard=False, ocr=False, regex=False,
        exclude="", file_types="", proximity="",
        context_before="", context_after="",
        whole_word=True,
    )
    assert cmd is not None
    assert "-W" in cmd


# ── End-to-end binding tests: GUI checkbox → StringVar → CLI flag ──
#
# These tests guard against the GUI redesign quietly breaking the
# binding chain when widgets were reparented or relocated. The risk:
# a checkbox moves to a different container but still LOOKS the same,
# yet its variable= parameter accidentally points at a stale StringVar
# (or no StringVar at all), so toggling the box no longer reaches the
# search-execution code path.
#
# Instantiating the full GUI requires a display. Tests skip gracefully
# when the headless environment can't open a Toplevel.


def _instantiate_app_or_skip():
    """Instantiate PeekDocsApp, or call pytest.skip if no display."""
    try:
        from peekdocs.gui._app import PeekDocsApp
        app = PeekDocsApp()
        app.update_idletasks()
        return app
    except Exception as e:
        pytest.skip(f"GUI instantiation failed (likely no display): {e}")


def test_advanced_panel_vars_drive_cli_flags(tmp_path):
    """Every Advanced Search Options checkbox is bound to the StringVar
    that _build_command_from_values reads, and toggling the var to "on"
    produces the expected CLI flag in the constructed command."""
    app = _instantiate_app_or_skip()
    try:
        # (checkbox attribute name, StringVar attribute name,
        #  _build_command_from_values keyword arg, expected CLI flag)
        cases = [
            ("_adv_cb_and",         "and_mode_var",     "and_mode",     "-a"),
            ("_adv_cb_rec",         "recursive_var",    "recursive",    "-r"),
            ("_adv_cb_fuz",         "fuzzy_var",        "fuzzy",        "-z"),
            ("_adv_cb_wild",        "wildcard_var",     "wildcard",     "-w"),
            ("_adv_cb_ocr",         "ocr_var",          "ocr",          "-O"),
            ("_adv_cb_regex",       "regex_var",        "regex",        "-x"),
            ("_adv_cb_whole_word",  "whole_word_var",   "whole_word",   "-W"),
            ("_adv_cb_inverse",     "inverse_var",      "inverse",      "--inverse"),
        ]

        # 1. Every checkbox's `variable=` is bound to the expected
        #    StringVar. CTkCheckBox stores it as `self._variable`.
        for cb_name, var_name, _, _ in cases:
            cb = getattr(app, cb_name, None)
            var = getattr(app, var_name, None)
            assert cb is not None, f"missing checkbox {cb_name}"
            assert var is not None, f"missing var {var_name}"
            assert cb._variable is var, (
                f"{cb_name} is bound to {cb._variable!r}, expected {var_name}"
            )

        # 2. Setting every var to "on" produces every expected CLI flag.
        for _, var_name, _, _ in cases:
            getattr(app, var_name).set("on")

        flags_on = {kw: getattr(app, var).get() == "on"
                    for _, var, kw, _ in cases}
        cmd_on = _build_command_from_values(
            search_text="hello",
            folder=str(tmp_path),
            exclude="", file_types="", proximity="",
            context_before="", context_after="",
            **flags_on,
        )
        assert cmd_on is not None
        for _, _, _, flag in cases:
            assert flag in cmd_on, (
                f"expected {flag} in CLI command when corresponding var is 'on'; "
                f"got {cmd_on!r}"
            )

        # 3. Setting every var back to "off" removes every flag.
        for _, var_name, _, _ in cases:
            getattr(app, var_name).set("off")

        flags_off = {kw: getattr(app, var).get() == "on"
                     for _, var, kw, _ in cases}
        cmd_off = _build_command_from_values(
            search_text="hello",
            folder=str(tmp_path),
            exclude="", file_types="", proximity="",
            context_before="", context_after="",
            **flags_off,
        )
        assert cmd_off is not None
        for _, _, _, flag in cases:
            assert flag not in cmd_off, (
                f"unexpected {flag} in CLI command when corresponding var is 'off'"
            )
    finally:
        try:
            app.destroy()
        except Exception:
            pass


def test_use_index_var_toggles_no_index_flag(tmp_path):
    """The Use Index checkbox in Advanced Search Options binds to
    index_search_var; when on, --no-index is dropped from the CLI
    command. Regression guard for moving cb_index_search out of the
    main options row into the Advanced panel."""
    app = _instantiate_app_or_skip()
    try:
        cb = app.cb_index_search
        var = app.index_search_var
        assert cb._variable is var, "cb_index_search not bound to index_search_var"

        # Off: --no-index present
        var.set("off")
        cmd_off = _build_command_from_values(
            search_text="hello",
            folder=str(tmp_path),
            and_mode=False, recursive=False, fuzzy=False,
            wildcard=False, ocr=False, regex=False,
            exclude="", file_types="", proximity="",
            context_before="", context_after="",
            index_search=var.get() == "on",
        )
        assert "--no-index" in cmd_off

        # On: --no-index absent
        var.set("on")
        cmd_on = _build_command_from_values(
            search_text="hello",
            folder=str(tmp_path),
            and_mode=False, recursive=False, fuzzy=False,
            wildcard=False, ocr=False, regex=False,
            exclude="", file_types="", proximity="",
            context_before="", context_after="",
            index_search=var.get() == "on",
        )
        assert "--no-index" not in cmd_on
    finally:
        try:
            app.destroy()
        except Exception:
            pass


def test_output_format_vars_drive_cli_flags(tmp_path):
    """The CSV / JSON / PDF / HTML output checkboxes inside Advanced
    Search Options bind to their StringVars and drive the corresponding
    CLI -o flag pieces. Regression guard for removing the Step 3
    duplicate checkboxes — these vars now have a single source of truth
    in the Advanced panel."""
    app = _instantiate_app_or_skip()
    try:
        # output_*_var → _build_command_from_values kwarg
        cases = [
            ("output_csv_var",  "output_csv",  "csv"),
            ("output_json_var", "output_json", "json"),
            ("output_pdf_var",  "output_pdf",  "pdf"),
            ("output_html_var", "output_html", "html"),
        ]
        for var_name, _, _ in cases:
            assert getattr(app, var_name, None) is not None, (
                f"missing {var_name} — Advanced output checkboxes should still bind here"
            )
            getattr(app, var_name).set("on")

        kwargs = {kw: getattr(app, var).get() == "on" for var, kw, _ in cases}
        cmd = _build_command_from_values(
            search_text="hello",
            folder=str(tmp_path),
            and_mode=False, recursive=False, fuzzy=False,
            wildcard=False, ocr=False, regex=False,
            exclude="", file_types="", proximity="",
            context_before="", context_after="",
            **kwargs,
        )
        assert cmd is not None
        # Each format appears as part of the -o argument value.
        assert "-o" in cmd
        o_idx = cmd.index("-o")
        o_arg = cmd[o_idx + 1]
        for _, _, fmt in cases:
            assert fmt in o_arg, f"expected '{fmt}' in -o argument, got {o_arg!r}"
    finally:
        try:
            app.destroy()
        except Exception:
            pass


def test_recent_searches_round_trip_full_config(tmp_path):
    """Recent Searches snapshot/apply round-trip preserves the full
    config (terms + folder + every advanced field). Regression guard
    for the post-redesign behaviour where Recent stores dicts, not
    just terms strings. Also verifies legacy plain-string entries
    round-trip as terms-only restores."""
    app = _instantiate_app_or_skip()
    try:
        # Set distinctive values
        app.folder_entry.delete(0, "end")
        app.folder_entry.insert(0, str(tmp_path))
        app.search_entry.delete(0, "end")
        app.search_entry.insert(0, "alpha beta")
        app.and_mode_var.set("on")
        app.recursive_var.set("off")
        app.regex_var.set("on")
        app.output_csv_var.set("on")
        app.exclude_entry.delete(0, "end")
        app.exclude_entry.insert(0, "draft,obsolete")

        snap = app._snapshot_search_config()
        # Snapshot captured the values
        assert snap["terms"] == "alpha beta"
        assert snap["folder"] == str(tmp_path)
        assert snap["and_mode"] == "on"
        assert snap["recursive"] == "off"
        assert snap["regex"] == "on"
        assert snap["output_csv"] == "on"
        assert snap["exclude"] == "draft,obsolete"

        # Mutate everything
        app.search_entry.delete(0, "end")
        app.search_entry.insert(0, "gamma")
        app.and_mode_var.set("off")
        app.recursive_var.set("on")
        app.regex_var.set("off")
        app.output_csv_var.set("off")
        app.exclude_entry.delete(0, "end")

        # Restore from snapshot — everything comes back
        app._apply_search_config(snap)
        assert app.search_entry.get() == "alpha beta"
        assert app.folder_entry.get() == str(tmp_path)
        assert app.and_mode_var.get() == "on"
        assert app.recursive_var.get() == "off"
        assert app.regex_var.get() == "on"
        assert app.output_csv_var.get() == "on"
        assert app.exclude_entry.get() == "draft,obsolete"

        # Legacy plain-string entry: terms only, no other vars touched
        app.and_mode_var.set("off")
        app._apply_search_config("just_a_legacy_string")
        assert app.search_entry.get() == "just_a_legacy_string"
        assert app.and_mode_var.get() == "off"

        # Helper handles both formats
        assert app._recent_entry_terms({"terms": "abc"}) == "abc"
        assert app._recent_entry_terms("legacy") == "legacy"
    finally:
        try:
            app.destroy()
        except Exception:
            pass
