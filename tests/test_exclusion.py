"""Tests for the peekdocs-prefix exclusion rule.

The naming convention reserves the `peekdocs_` (visible) and
`.peekdocs` (hidden) prefixes for peekdocs-generated files. The
scanner's `discover_files` must skip every such file so peekdocs's
Search workflows (Standard / Suites / Regex) never find their own
outputs as user content.
"""

from peekdocs.scanner import is_peekdocs_internal_file, discover_files


def test_helper_recognizes_visible_prefix():
    assert is_peekdocs_internal_file("peekdocs_standard_results.txt")
    assert is_peekdocs_internal_file("peekdocs_report_archive.docx")
    assert is_peekdocs_internal_file("peekdocs_file_age_distribution.txt")
    assert is_peekdocs_internal_file("peekdocs_SHA256SUMS.txt")
    assert is_peekdocs_internal_file("peekdocs_regex_collection_code_patterns.json")


def test_helper_recognizes_hidden_prefix():
    assert is_peekdocs_internal_file(".peekdocsrc")
    assert is_peekdocs_internal_file(".peekdocs_collection.json")
    assert is_peekdocs_internal_file(".peekdocs.db")
    assert is_peekdocs_internal_file(".peekdocs_history.json")


def test_helper_rejects_unrelated_filenames():
    assert not is_peekdocs_internal_file("auth.py")
    assert not is_peekdocs_internal_file("notes_about_peekdocs.md")
    assert not is_peekdocs_internal_file("Peekdocs_capitalized.txt")  # case-sensitive
    assert not is_peekdocs_internal_file("budget_2026.docx")


def test_discover_files_skips_peekdocs_prefixed(tmp_path):
    """End-to-end: discover_files honors the prefix rule."""
    skip = [
        "peekdocs_standard_results.txt",
        "peekdocs_regex_results.docx",
        "peekdocs_suite_results.html",
        "peekdocs_report_archive.txt",
        "peekdocs_accumulated_batch.txt",
        "peekdocs_errors.log",
        "peekdocs_file_age_distribution.txt",
        "peekdocs_collection_summary.txt",
        "peekdocs_SHA256SUMS.txt",
        "peekdocs_global_test_results.txt",
        "peekdocs_regex_collection_code_patterns.json",
        "peekdocs_suite_collection_quarterly_audit.json",
        ".peekdocsrc",
        ".peekdocs_collection.json",
    ]
    keep = ["budget.txt", "notes.md", "report.docx"]
    for fn in skip + keep:
        (tmp_path / fn).write_text("test content\n")

    found = {p for p in discover_files(str(tmp_path), recursive=False, use_ocr=False)}
    found_names = {p.split("/")[-1] for p in found}

    for fn in skip:
        assert fn not in found_names, f"{fn} should be skipped"
    for fn in keep:
        assert fn in found_names, f"{fn} should be discovered"
