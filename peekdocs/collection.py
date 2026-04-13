"""Saved search collections — per-folder JSON persistence."""

import json
import os

COLLECTION_FILENAME = ".peekdocs_collection.json"
COLLECTION_VERSION = 1

# Keys stored for each saved search (matches _build_command_from_values params).
SEARCH_PARAM_KEYS = [
    "search_text", "and_mode", "recursive", "fuzzy", "wildcard",
    "ocr", "regex", "exclude", "file_types", "proximity",
    "context_before", "context_after", "cores", "specific_files",
    "index_search", "inverse", "expression", "whole_word", "max_matches",
    "range_filters",
]


def _empty_collection():
    return {"version": COLLECTION_VERSION, "saved_searches": {}}


def collection_path(folder):
    """Return the full path to the collection file for *folder*."""
    return os.path.join(folder, COLLECTION_FILENAME)


def load_collection(folder):
    """Load and return the collection dict.  Returns empty structure if missing or corrupt.

    Collection files created by older versions may contain a ``test_suites``
    key from the removed compliance/suites feature. That key is silently
    dropped on load so the file is treated as if it only ever had
    ``saved_searches``.
    """
    path = collection_path(folder)
    if not os.path.exists(path):
        return _empty_collection()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure required keys exist
        data.setdefault("version", COLLECTION_VERSION)
        data.setdefault("saved_searches", {})
        # Drop legacy test_suites key from old compliance feature
        data.pop("test_suites", None)
        # Migrate: rename "query" key to "search_text" in saved searches
        for params in data["saved_searches"].values():
            if "query" in params and "search_text" not in params:
                params["search_text"] = params.pop("query")
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
    """Remove a saved search from the collection."""
    data = load_collection(folder)
    data["saved_searches"].pop(name, None)
    save_collection(folder, data)


def get_search_params(folder, name):
    """Return the parameter dict for a named saved search, or None."""
    data = load_collection(folder)
    return data["saved_searches"].get(name)
