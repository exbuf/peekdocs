"""Tests for saved search collections."""

import json
import os
import pytest
from docsearch.collection import (
    COLLECTION_FILENAME,
    load_collection,
    save_collection,
    add_saved_search,
    remove_saved_search,
    get_search_params,
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
    assert data["version"] == 1


def test_save_and_load_roundtrip(tmp_path):
    data = {
        "version": 1,
        "saved_searches": {"s1": _sample_params(search_text="hello")},
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


def test_remove_nonexistent_search(tmp_path):
    remove_saved_search(str(tmp_path), "nope")
    data = load_collection(str(tmp_path))
    assert data["saved_searches"] == {}


def test_get_search_params(tmp_path):
    add_saved_search(str(tmp_path), "s1", _sample_params(search_text="hello"))
    assert get_search_params(str(tmp_path), "s1")["search_text"] == "hello"
    assert get_search_params(str(tmp_path), "nonexistent") is None


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


def test_missing_keys_filled(tmp_path):
    path = os.path.join(str(tmp_path), COLLECTION_FILENAME)
    with open(path, "w") as f:
        json.dump({"version": 1}, f)
    data = load_collection(str(tmp_path))
    assert data["saved_searches"] == {}


def test_legacy_test_suites_key_is_dropped(tmp_path):
    """Collection files from the old compliance feature are accepted but the
    test_suites key is silently dropped."""
    path = os.path.join(str(tmp_path), COLLECTION_FILENAME)
    with open(path, "w") as f:
        json.dump({
            "version": 1,
            "saved_searches": {"s1": _sample_params(search_text="hello")},
            "test_suites": {"oldsuite": {"description": "old", "searches": ["s1"]}},
        }, f)
    data = load_collection(str(tmp_path))
    assert data["saved_searches"]["s1"]["search_text"] == "hello"
    assert "test_suites" not in data
