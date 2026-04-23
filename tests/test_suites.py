"""Tests for search suite functionality."""

import json
import os
import pytest
from peekdocs.collection import (
    add_suite, remove_suite, get_suite, list_suites,
    rename_suite, update_suite_searches,
    add_saved_search, load_collection, collection_path,
)


@pytest.fixture
def suite_folder(tmp_path):
    """Create a temp folder with some saved searches."""
    folder = str(tmp_path)
    add_saved_search(folder, "find budget", {"search_text": "budget", "and_mode": False, "recursive": True})
    add_saved_search(folder, "find SSN", {"search_text": r"\d{3}-\d{2}-\d{4}", "regex": True, "recursive": True})
    add_saved_search(folder, "find TODO", {"search_text": "TODO", "whole_word": True})
    return folder


def test_add_suite(suite_folder):
    add_suite(suite_folder, "My Suite", ["find budget", "find SSN"])
    result = get_suite(suite_folder, "My Suite")
    assert result == ["find budget", "find SSN"]


def test_add_empty_suite(suite_folder):
    add_suite(suite_folder, "Empty Suite")
    result = get_suite(suite_folder, "Empty Suite")
    assert result == []


def test_remove_suite(suite_folder):
    add_suite(suite_folder, "To Delete", ["find budget"])
    remove_suite(suite_folder, "To Delete")
    assert get_suite(suite_folder, "To Delete") is None


def test_remove_nonexistent_suite(suite_folder):
    # Should not raise
    remove_suite(suite_folder, "does not exist")


def test_get_suite_nonexistent(suite_folder):
    assert get_suite(suite_folder, "nope") is None


def test_list_suites(suite_folder):
    add_suite(suite_folder, "Suite A", ["find budget"])
    add_suite(suite_folder, "Suite B", ["find SSN", "find TODO"])
    result = list_suites(suite_folder)
    assert "Suite A" in result
    assert "Suite B" in result
    assert result["Suite A"] == ["find budget"]
    assert result["Suite B"] == ["find SSN", "find TODO"]


def test_list_suites_empty(suite_folder):
    assert list_suites(suite_folder) == {}


def test_rename_suite(suite_folder):
    add_suite(suite_folder, "Old Name", ["find budget"])
    assert rename_suite(suite_folder, "Old Name", "New Name") is True
    assert get_suite(suite_folder, "Old Name") is None
    assert get_suite(suite_folder, "New Name") == ["find budget"]


def test_rename_suite_conflict(suite_folder):
    add_suite(suite_folder, "Suite A", ["find budget"])
    add_suite(suite_folder, "Suite B", ["find SSN"])
    assert rename_suite(suite_folder, "Suite A", "Suite B") is False
    # Both should still exist unchanged
    assert get_suite(suite_folder, "Suite A") == ["find budget"]
    assert get_suite(suite_folder, "Suite B") == ["find SSN"]


def test_rename_nonexistent_suite(suite_folder):
    assert rename_suite(suite_folder, "nope", "new") is False


def test_update_suite_searches(suite_folder):
    add_suite(suite_folder, "My Suite", ["find budget"])
    update_suite_searches(suite_folder, "My Suite", ["find TODO", "find SSN", "find budget"])
    assert get_suite(suite_folder, "My Suite") == ["find TODO", "find SSN", "find budget"]


def test_update_suite_reorder(suite_folder):
    add_suite(suite_folder, "Ordered", ["find budget", "find SSN", "find TODO"])
    # Move "find TODO" to the top
    update_suite_searches(suite_folder, "Ordered", ["find TODO", "find budget", "find SSN"])
    assert get_suite(suite_folder, "Ordered") == ["find TODO", "find budget", "find SSN"]


def test_update_nonexistent_suite(suite_folder):
    # Should not raise or create the suite
    update_suite_searches(suite_folder, "nope", ["find budget"])
    assert get_suite(suite_folder, "nope") is None


def test_suites_coexist_with_saved_searches(suite_folder):
    add_suite(suite_folder, "My Suite", ["find budget"])
    data = load_collection(suite_folder)
    assert "saved_searches" in data
    assert "suites" in data
    assert len(data["saved_searches"]) == 3
    assert len(data["suites"]) == 1


def test_suite_persists_to_disk(suite_folder):
    add_suite(suite_folder, "Persistent", ["find budget", "find TODO"])
    # Read the raw JSON file
    with open(collection_path(suite_folder), "r") as f:
        raw = json.load(f)
    assert "suites" in raw
    assert raw["suites"]["Persistent"] == ["find budget", "find TODO"]
