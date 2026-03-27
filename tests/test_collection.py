"""Tests for saved search collections and search suites."""

import json
import os
import pytest
from docsearch.collection import (
    COLLECTION_FILENAME,
    load_collection,
    save_collection,
    add_saved_search,
    remove_saved_search,
    add_test_suite,
    remove_test_suite,
    get_search_params,
    get_suite,
    collection_path,
)


def _sample_params(**overrides):
    base = {
        "search_text": "budget",
        "and_mode": False,
        "recursive": False,
        "fuzzy": False,
        "wildcard": False,
        "ocr": False,
        "regex": False,
        "exclude": "",
        "file_types": "",
        "proximity": "",
        "context_before": "",
        "context_after": "",
        "cores": "",
        "specific_files": "",
        "index_search": False,
        "inverse": False,
    }
    base.update(overrides)
    return base


def test_load_empty_collection(tmp_path):
    data = load_collection(str(tmp_path))
    assert data["saved_searches"] == {}
    assert data["test_suites"] == {}
    assert data["version"] == 1


def test_save_and_load_roundtrip(tmp_path):
    data = {
        "version": 1,
        "saved_searches": {"s1": _sample_params(search_text="hello")},
        "test_suites": {},
    }
    save_collection(str(tmp_path), data)
    loaded = load_collection(str(tmp_path))
    assert loaded["saved_searches"]["s1"]["search_text"] == "hello"


def test_add_saved_search(tmp_path):
    add_saved_search(str(tmp_path), "my_search", _sample_params(search_text="revenue"))
    data = load_collection(str(tmp_path))
    assert "my_search" in data["saved_searches"]
    assert data["saved_searches"]["my_search"]["search_text"] == "revenue"


def test_add_saved_search_overwrite(tmp_path):
    add_saved_search(str(tmp_path), "s1", _sample_params(search_text="old"))
    add_saved_search(str(tmp_path), "s1", _sample_params(search_text="new"))
    data = load_collection(str(tmp_path))
    assert data["saved_searches"]["s1"]["search_text"] == "new"


def test_remove_saved_search(tmp_path):
    add_saved_search(str(tmp_path), "s1", _sample_params())
    remove_saved_search(str(tmp_path), "s1")
    data = load_collection(str(tmp_path))
    assert "s1" not in data["saved_searches"]


def test_remove_saved_search_cascades_to_suites(tmp_path):
    add_saved_search(str(tmp_path), "s1", _sample_params())
    add_saved_search(str(tmp_path), "s2", _sample_params())
    add_test_suite(str(tmp_path), "suite1", "desc", ["s1", "s2"])
    remove_saved_search(str(tmp_path), "s1")
    data = load_collection(str(tmp_path))
    assert "s1" not in data["saved_searches"]
    assert data["test_suites"]["suite1"]["searches"] == ["s2"]


def test_remove_nonexistent_search(tmp_path):
    remove_saved_search(str(tmp_path), "nope")
    data = load_collection(str(tmp_path))
    assert data["saved_searches"] == {}


def test_add_test_suite(tmp_path):
    add_saved_search(str(tmp_path), "s1", _sample_params())
    add_test_suite(str(tmp_path), "suite1", "my desc", ["s1"])
    data = load_collection(str(tmp_path))
    assert "suite1" in data["test_suites"]
    assert data["test_suites"]["suite1"]["searches"] == ["s1"]
    assert data["test_suites"]["suite1"]["description"] == "my desc"


def test_remove_test_suite(tmp_path):
    add_saved_search(str(tmp_path), "s1", _sample_params())
    add_test_suite(str(tmp_path), "suite1", "", ["s1"])
    remove_test_suite(str(tmp_path), "suite1")
    data = load_collection(str(tmp_path))
    assert "suite1" not in data["test_suites"]
    assert "s1" in data["saved_searches"]


def test_remove_nonexistent_suite(tmp_path):
    remove_test_suite(str(tmp_path), "nope")
    data = load_collection(str(tmp_path))
    assert data["test_suites"] == {}


def test_get_search_params(tmp_path):
    add_saved_search(str(tmp_path), "s1", _sample_params(search_text="hello"))
    assert get_search_params(str(tmp_path), "s1")["search_text"] == "hello"
    assert get_search_params(str(tmp_path), "nonexistent") is None


def test_get_suite(tmp_path):
    add_saved_search(str(tmp_path), "s1", _sample_params())
    add_test_suite(str(tmp_path), "suite1", "desc", ["s1"])
    suite = get_suite(str(tmp_path), "suite1")
    assert suite["searches"] == ["s1"]
    assert get_suite(str(tmp_path), "nonexistent") is None


def test_collection_file_location(tmp_path):
    add_saved_search(str(tmp_path), "s1", _sample_params())
    assert os.path.exists(os.path.join(str(tmp_path), COLLECTION_FILENAME))


def test_collection_path(tmp_path):
    expected = os.path.join(str(tmp_path), COLLECTION_FILENAME)
    assert collection_path(str(tmp_path)) == expected


def test_invalid_json_graceful(tmp_path):
    path = os.path.join(str(tmp_path), COLLECTION_FILENAME)
    with open(path, "w") as f:
        f.write("not valid json {{{")
    data = load_collection(str(tmp_path))
    assert data["saved_searches"] == {}
    assert data["test_suites"] == {}


def test_missing_keys_filled(tmp_path):
    path = os.path.join(str(tmp_path), COLLECTION_FILENAME)
    with open(path, "w") as f:
        json.dump({"version": 1}, f)
    data = load_collection(str(tmp_path))
    assert data["saved_searches"] == {}
    assert data["test_suites"] == {}


# ── Suite Report Tests ─────────────────────────────────────

from docsearch.reporter import write_suite_report_txt, write_suite_report_json


def _make_results(pass_list):
    """Create result dicts from a list of (name, passed, count) tuples."""
    results = []
    for name, passed, count in pass_list:
        results.append({
            "name": name,
            "search_text": f"term_{name}",
            "inverse": False,
            "return_code": 0 if passed else 1,
            "passed": passed,
            "match_count": count,
            "summary": "",
        })
    return results


def test_suite_report_txt_all_pass(tmp_path):
    results = _make_results([("s1", True, 5), ("s2", True, 3)])
    path = os.path.join(str(tmp_path), "report.txt")
    write_suite_report_txt(path, "my_suite", str(tmp_path), results, 1000.0, 1010.0)
    content = open(path).read()
    assert "PASSED" in content
    assert "[PASS] s1" in content
    assert "[PASS] s2" in content
    assert "2 of 2 tests passed" in content


def test_suite_report_txt_has_fail(tmp_path):
    results = _make_results([("s1", True, 5), ("s2", False, 0)])
    path = os.path.join(str(tmp_path), "report.txt")
    write_suite_report_txt(path, "my_suite", str(tmp_path), results, 1000.0, 1012.0)
    content = open(path).read()
    assert "FAILED" in content
    assert "[PASS] s1" in content
    assert "[FAIL] s2" in content
    assert "1 of 2 tests passed" in content


def test_suite_report_json_structure(tmp_path):
    results = _make_results([("s1", True, 5), ("s2", False, 0)])
    path = os.path.join(str(tmp_path), "report.json")
    write_suite_report_json(path, "my_suite", str(tmp_path), results, 1000.0, 1012.0)
    data = json.load(open(path))
    assert data["suite_name"] == "my_suite"
    assert data["total_tests"] == 2
    assert data["passed"] == 1
    assert data["failed"] == 1
    assert data["overall"] == "FAILED"
    assert len(data["tests"]) == 2
    assert data["tests"][0]["name"] == "s1"
    assert data["tests"][0]["passed"] is True
    assert data["tests"][1]["passed"] is False


def test_suite_report_json_all_pass(tmp_path):
    results = _make_results([("s1", True, 10)])
    path = os.path.join(str(tmp_path), "report.json")
    write_suite_report_json(path, "audit", str(tmp_path), results, 1000.0, 1005.0)
    data = json.load(open(path))
    assert data["overall"] == "PASSED"
    assert data["duration_seconds"] == 5.0
