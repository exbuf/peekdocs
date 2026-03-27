"""Saved search collections and search suites — per-folder JSON persistence."""

import json
import os

COLLECTION_FILENAME = ".docsearch_collection.json"
COLLECTION_VERSION = 1

# Keys stored for each saved search (matches _build_command_from_values params).
SEARCH_PARAM_KEYS = [
    "search_text", "and_mode", "recursive", "fuzzy", "wildcard",
    "ocr", "regex", "exclude", "file_types", "proximity",
    "context_before", "context_after", "cores", "specific_files",
    "index_search", "inverse", "expression", "whole_word",
]


def _empty_collection():
    return {"version": COLLECTION_VERSION, "saved_searches": {}, "test_suites": {}}


def collection_path(folder):
    """Return the full path to the collection file for *folder*."""
    return os.path.join(folder, COLLECTION_FILENAME)


def load_collection(folder):
    """Load and return the collection dict.  Returns empty structure if missing or corrupt."""
    path = collection_path(folder)
    if not os.path.exists(path):
        return _empty_collection()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure required keys exist
        data.setdefault("version", COLLECTION_VERSION)
        data.setdefault("saved_searches", {})
        data.setdefault("test_suites", {})
        return data
    except (json.JSONDecodeError, OSError):
        return _empty_collection()


def save_collection(folder, data):
    """Write the collection dict to the folder's collection file."""
    path = collection_path(folder)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_saved_search(folder, name, params):
    """Add or overwrite a named saved search in the collection."""
    data = load_collection(folder)
    data["saved_searches"][name] = params
    save_collection(folder, data)


def remove_saved_search(folder, name):
    """Remove a saved search and scrub it from any suites that reference it."""
    data = load_collection(folder)
    data["saved_searches"].pop(name, None)
    for suite in data["test_suites"].values():
        suite["searches"] = [s for s in suite["searches"] if s != name]
    save_collection(folder, data)


def add_test_suite(folder, suite_name, description, search_names):
    """Create or overwrite a named search suite."""
    data = load_collection(folder)
    data["test_suites"][suite_name] = {
        "description": description,
        "searches": list(search_names),
    }
    save_collection(folder, data)


def remove_test_suite(folder, suite_name):
    """Remove a search suite (saved searches are not affected)."""
    data = load_collection(folder)
    data["test_suites"].pop(suite_name, None)
    save_collection(folder, data)


def get_search_params(folder, name):
    """Return the parameter dict for a named saved search, or None."""
    data = load_collection(folder)
    return data["saved_searches"].get(name)


def get_suite(folder, suite_name):
    """Return the suite dict for a named suite, or None."""
    data = load_collection(folder)
    return data["test_suites"].get(suite_name)
