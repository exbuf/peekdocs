#!/usr/bin/env python3
"""Manual API test script — run on each OS after installation.

Usage:
    1. Create a test_folder/ with files containing "ComplianceTest2026",
       "$15,000", and "Authorized Signature" (see testing plan for details)
    2. Run: python tests/test_api_manual.py /path/to/test_folder

Each test prints PASS or FAIL. Review any failures before shipping.
"""

import os
import sys
import traceback

passed = 0
failed = 0
errors = []


def test(name, fn):
    """Run a test function and report results."""
    global passed, failed
    try:
        fn()
        print(f"  PASS  {name}")
        passed += 1
    except Exception as e:
        print(f"  FAIL  {name} — {e}")
        errors.append((name, traceback.format_exc()))
        failed += 1


def main():
    if len(sys.argv) < 2:
        print("Usage: python tests/test_api_manual.py /path/to/test_folder")
        print("\nThe test folder should contain files with these terms:")
        print('  "ComplianceTest2026", "$15,000", "Authorized Signature"')
        sys.exit(1)

    test_dir = os.path.abspath(sys.argv[1])
    if not os.path.isdir(test_dir):
        print(f"Error: {test_dir} is not a directory")
        sys.exit(1)

    print(f"\nTesting docsearch API against: {test_dir}")
    print(f"{'=' * 60}\n")

    from docsearch import search

    # ── Basic search ──────────────────────────────────────────

    print("Basic Search:")

    def test_basic_search():
        result = search(["ComplianceTest2026"], directory=test_dir)
        assert len(result.matches) > 0, f"Expected matches, got {len(result.matches)}"
        assert len(result.files_searched) > 0, "No files searched"
        assert result.elapsed > 0, "Elapsed time is 0"

    test("Basic keyword search", test_basic_search)

    def test_return_fields():
        result = search(["ComplianceTest2026"], directory=test_dir)
        assert hasattr(result, 'matches'), "Missing 'matches' field"
        assert hasattr(result, 'files_searched'), "Missing 'files_searched' field"
        assert hasattr(result, 'skipped_files'), "Missing 'skipped_files' field"
        assert hasattr(result, 'elapsed'), "Missing 'elapsed' field"
        assert hasattr(result, 'used_index'), "Missing 'used_index' field"

    test("Return value has all fields", test_return_fields)

    def test_match_fields():
        result = search(["ComplianceTest2026"], directory=test_dir)
        assert len(result.matches) > 0, "No matches to inspect"
        m = result.matches[0]
        assert m.file_dir, "file_dir is empty"
        assert m.filename, "filename is empty"
        assert m.line_num > 0, f"line_num is {m.line_num}"
        assert m.text, "text is empty"

    test("SearchMatch fields populated", test_match_fields)

    def test_match_unpacking():
        result = search(["ComplianceTest2026"], directory=test_dir)
        m = result.matches[0]
        fd, fn, ln, tx = m
        assert fd and fn and ln and tx

    test("SearchMatch tuple unpacking", test_match_unpacking)

    # ── Search modes ──────────────────────────────────────────

    print("\nSearch Modes:")

    def test_and_mode():
        result = search(["ComplianceTest2026", "Signature"], directory=test_dir, match_all=True)
        assert len(result.matches) > 0, "AND mode found no matches"

    test("AND mode", test_and_mode)

    def test_regex():
        result = search([r"\$[\d,]+"], directory=test_dir, use_regex=True)
        assert len(result.matches) > 0, "Regex found no dollar amounts"

    test("Regex search", test_regex)

    def test_fuzzy():
        result = search(["ComplianceTset"], directory=test_dir, use_fuzzy=True)
        assert len(result.matches) > 0, "Fuzzy search found no matches for misspelled term"

    test("Fuzzy search", test_fuzzy)

    def test_wildcard():
        result = search(["Compliance*"], directory=test_dir, use_wildcard=True)
        assert len(result.matches) > 0, "Wildcard search found no matches"

    test("Wildcard search", test_wildcard)

    def test_whole_word():
        result = search(["ComplianceTest2026"], directory=test_dir, use_whole_word=True)
        assert len(result.matches) > 0, "Whole-word search found no matches"

    test("Whole-word search", test_whole_word)

    def test_expression():
        result = search([], directory=test_dir, expression="ComplianceTest2026 AND Signature")
        assert len(result.matches) > 0, "Boolean expression found no matches"

    test("Boolean expression", test_expression)

    def test_expression_or():
        result = search([], directory=test_dir, expression="ComplianceTest2026 OR nonexistentterm99999")
        assert len(result.matches) > 0, "OR expression found no matches"

    test("Boolean expression (OR)", test_expression_or)

    def test_expression_not():
        result = search([], directory=test_dir, expression="ComplianceTest2026 AND NOT nonexistentterm99999")
        assert len(result.matches) > 0, "NOT expression found no matches"

    test("Boolean expression (NOT)", test_expression_not)

    # ── Filters ───────────────────────────────────────────────

    print("\nFilters:")

    def test_file_types():
        result = search(["ComplianceTest2026"], directory=test_dir, file_types=[".txt"])
        for m in result.matches:
            assert m.filename.endswith(".txt"), f"Unexpected file type: {m.filename}"

    test("File type filter", test_file_types)

    def test_exclude():
        result_without = search(["ComplianceTest2026"], directory=test_dir)
        result_with = search(["ComplianceTest2026"], directory=test_dir, exclude_terms=["Signature"])
        assert len(result_with.matches) <= len(result_without.matches), "Exclude didn't reduce matches"

    test("Exclude terms", test_exclude)

    def test_recursive():
        result = search(["ComplianceTest2026"], directory=test_dir, recursive=True)
        assert len(result.files_searched) > 0, "Recursive search found no files"

    test("Recursive search", test_recursive)

    def test_range_filter():
        result = search(["ComplianceTest2026"], directory=test_dir, range_filters=["amount:10000..20000"])
        # May or may not find matches depending on test data, but shouldn't crash
        assert result is not None

    test("Range filter (no crash)", test_range_filter)

    def test_proximity():
        result = search(["Authorized", "Signature"], directory=test_dir, proximity=3)
        assert len(result.matches) > 0, "Proximity search found no matches"

    test("Proximity search", test_proximity)

    def test_context():
        result = search(["ComplianceTest2026"], directory=test_dir, context_before=2, context_after=2)
        assert result is not None

    test("Context lines (no crash)", test_context)

    # ── Progress callback ─────────────────────────────────────

    print("\nProgress:")

    def test_progress_callback():
        progress_calls = []
        def on_progress(done, total, filename):
            progress_calls.append((done, total, filename))
        result = search(["ComplianceTest2026"], directory=test_dir, progress=on_progress)
        assert len(progress_calls) > 0, "Progress callback never called"

    test("Progress callback fires", test_progress_callback)

    # ── Index ─────────────────────────────────────────────────

    print("\nIndex:")

    def test_index_search():
        from docsearch.indexer import index_exists, build_index
        if not index_exists(test_dir):
            print("         (building index for test...)")
            build_index(test_dir, recursive=True)
        result = search(["ComplianceTest2026"], directory=test_dir, use_index=True)
        assert result.used_index, "Index was not used"
        assert len(result.matches) > 0, "Index search found no matches"

    test("Search with index", test_index_search)

    def test_index_matches_direct():
        direct = search(["ComplianceTest2026"], directory=test_dir, use_index=False)
        indexed = search(["ComplianceTest2026"], directory=test_dir, use_index=True)
        assert len(indexed.matches) == len(direct.matches), \
            f"Index ({len(indexed.matches)}) != direct ({len(direct.matches)})"

    test("Index results match direct results", test_index_matches_direct)

    # ── Error handling ────────────────────────────────────────

    print("\nError Handling:")

    def test_invalid_regex():
        try:
            search([r"[invalid"], directory=test_dir, use_regex=True)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    test("Invalid regex raises ValueError", test_invalid_regex)

    def test_regex_plus_fuzzy():
        try:
            search(["test"], directory=test_dir, use_regex=True, use_fuzzy=True)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    test("Regex + fuzzy raises ValueError", test_regex_plus_fuzzy)

    def test_wildcard_plus_regex():
        try:
            search(["test*"], directory=test_dir, use_wildcard=True, use_regex=True)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    test("Wildcard + regex raises ValueError", test_wildcard_plus_regex)

    def test_wildcard_plus_fuzzy():
        try:
            search(["test*"], directory=test_dir, use_wildcard=True, use_fuzzy=True)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    test("Wildcard + fuzzy raises ValueError", test_wildcard_plus_fuzzy)

    def test_no_search_terms():
        try:
            search([], directory=test_dir)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    test("Empty search terms raises ValueError", test_no_search_terms)

    def test_proximity_one_term():
        try:
            search(["single"], directory=test_dir, proximity=5)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    test("Proximity with 1 term raises ValueError", test_proximity_one_term)

    # ── Summary ───────────────────────────────────────────────

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed} tests")
    if errors:
        print(f"\nFailed tests:")
        for name, tb in errors:
            print(f"\n  {name}:")
            for line in tb.strip().split("\n"):
                print(f"    {line}")
    print()

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
