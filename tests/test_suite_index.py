"""Tests for the global suite-name → folder index."""

import json
import os
import pytest

from peekdocs.collection import add_suite, remove_suite, rename_suite, add_saved_search
from peekdocs.suite_index import (
    index_path, load_index, save_index, register_suite, unregister_suite,
    find_suite, list_suites_global, rescan,
)


@pytest.fixture(autouse=True)
def isolate_home(tmp_path, monkeypatch):
    home = tmp_path / "_home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home


def _docfolder(tmp_path, name="docs"):
    p = tmp_path / name
    p.mkdir(exist_ok=True)
    return str(p)


def test_load_returns_empty_when_missing():
    data = load_index()
    assert data == {"version": 1, "entries": []}


def test_register_and_find(tmp_path):
    folder = _docfolder(tmp_path)
    add_saved_search(folder, "find budget", {"search_text": "budget"})
    add_suite(folder, "Example 1", ["find budget"])

    matches = find_suite("Example 1")
    assert matches == [os.path.abspath(folder)]


def test_register_is_idempotent(tmp_path):
    folder = _docfolder(tmp_path)
    register_suite(folder, "S")
    register_suite(folder, "S")
    data = load_index()
    matching = [e for e in data["entries"] if e["name"] == "S"]
    assert len(matching) == 1


def test_unregister_on_remove_suite(tmp_path):
    folder = _docfolder(tmp_path)
    add_saved_search(folder, "x", {"search_text": "x"})
    add_suite(folder, "S", ["x"])
    assert find_suite("S") == [os.path.abspath(folder)]

    remove_suite(folder, "S")
    assert find_suite("S") == []


def test_rename_updates_index(tmp_path):
    folder = _docfolder(tmp_path)
    add_saved_search(folder, "x", {"search_text": "x"})
    add_suite(folder, "Old", ["x"])
    assert rename_suite(folder, "Old", "New") is True

    assert find_suite("Old") == []
    assert find_suite("New") == [os.path.abspath(folder)]


def test_find_returns_empty_when_unknown():
    assert find_suite("nope") == []


def test_find_returns_multiple_when_same_name_in_two_folders(tmp_path):
    a = _docfolder(tmp_path, "a")
    b = _docfolder(tmp_path, "b")
    add_saved_search(a, "x", {"search_text": "x"})
    add_saved_search(b, "x", {"search_text": "x"})
    add_suite(a, "Shared", ["x"])
    add_suite(b, "Shared", ["x"])

    matches = find_suite("Shared")
    assert set(matches) == {os.path.abspath(a), os.path.abspath(b)}


def test_stale_entry_pruned_when_collection_no_longer_has_suite(tmp_path):
    folder = _docfolder(tmp_path)
    add_saved_search(folder, "x", {"search_text": "x"})
    add_suite(folder, "S", ["x"])
    # Tamper: clear suites in the collection file directly, simulating an out-of-band edit.
    coll_path = os.path.join(folder, ".peekdocs_collection.json")
    with open(coll_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["suites"] = {}
    with open(coll_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    assert find_suite("S") == []
    # And the index file no longer references it.
    assert all(e["name"] != "S" for e in load_index()["entries"])


def test_stale_entry_pruned_when_folder_deleted(tmp_path):
    folder = _docfolder(tmp_path, "gone")
    add_saved_search(folder, "x", {"search_text": "x"})
    add_suite(folder, "S", ["x"])
    # Remove the folder entirely.
    import shutil
    shutil.rmtree(folder)

    assert find_suite("S") == []


def test_list_suites_global(tmp_path):
    a = _docfolder(tmp_path, "a")
    b = _docfolder(tmp_path, "b")
    add_saved_search(a, "x", {"search_text": "x"})
    add_saved_search(a, "y", {"search_text": "y"})
    add_saved_search(b, "z", {"search_text": "z"})
    add_suite(a, "AAA", ["x", "y"])
    add_suite(b, "BBB", ["z"])

    entries = list_suites_global()
    names = [(e["name"], e["search_count"]) for e in entries]
    assert ("AAA", 2) in names
    assert ("BBB", 1) in names


def test_bootstrap_from_history_file(tmp_path, isolate_home):
    folder = _docfolder(tmp_path)
    add_saved_search(folder, "x", {"search_text": "x"})
    add_suite(folder, "Boot", ["x"])

    # Now wipe the index so we can confirm bootstrap repopulates it from history.
    idx = index_path()
    if os.path.exists(idx):
        os.unlink(idx)
    hist = os.path.join(str(isolate_home), ".peekdocs_history.json")
    with open(hist, "w", encoding="utf-8") as f:
        json.dump([{"folder": folder, "search_text": "x"}], f)

    assert find_suite("Boot") == [os.path.abspath(folder)]


def test_bootstrap_walks_documents_directory(tmp_path, isolate_home):
    """A suite under ~/Documents/Whatever should be discovered by the walk."""
    documents = isolate_home / "Documents" / "MyDocs" / "Personal"
    documents.mkdir(parents=True)
    folder = str(documents)
    add_saved_search(folder, "x", {"search_text": "x"})
    add_suite(folder, "Walked", ["x"])

    # Wipe the index so bootstrap has to repopulate via the walk.
    idx = index_path()
    if os.path.exists(idx):
        os.unlink(idx)

    assert find_suite("Walked") == [os.path.abspath(folder)]


def test_rescan_rediscovers_after_external_change(tmp_path, isolate_home):
    """A suite created outside add_suite should appear after rescan()."""
    documents = isolate_home / "Documents" / "Stuff"
    documents.mkdir(parents=True)
    folder = str(documents)

    # Create a collection file directly (simulating an out-of-band edit or
    # a folder copied in from another machine).
    from peekdocs.collection import save_collection
    save_collection(folder, {
        "version": 1,
        "saved_searches": {"x": {"search_text": "x"}},
        "suites": {"External": ["x"]},
    })

    # The index doesn't know about it (we bypassed add_suite).
    # Populate the index with a different suite so it's non-empty.
    other = isolate_home / "Documents" / "Other"
    other.mkdir()
    add_saved_search(str(other), "y", {"search_text": "y"})
    add_suite(str(other), "Other", ["y"])
    assert find_suite("External") == []  # not discoverable yet

    rescan()
    assert find_suite("External") == [os.path.abspath(folder)]
    assert find_suite("Other") == [os.path.abspath(str(other))]


def test_walk_skips_hidden_and_junk_dirs(tmp_path, isolate_home):
    """Bootstrap walk should skip node_modules, .git, etc."""
    junk = isolate_home / "Documents" / "node_modules" / "pkg"
    junk.mkdir(parents=True)
    add_saved_search(str(junk), "x", {"search_text": "x"})
    # Save directly so the index doesn't get pre-populated.
    from peekdocs.collection import load_collection, save_collection
    c = load_collection(str(junk))
    c["suites"]["JunkSuite"] = ["x"]
    save_collection(str(junk), c)

    idx = index_path()
    if os.path.exists(idx):
        os.unlink(idx)

    assert find_suite("JunkSuite") == []


def test_bootstrap_does_not_run_when_index_has_entries(tmp_path, isolate_home):
    folder = _docfolder(tmp_path, "other")
    add_saved_search(folder, "x", {"search_text": "x"})
    add_suite(folder, "Other", ["x"])

    # Index now has 'Other'. Add a history entry pointing at a different folder
    # with a different suite — bootstrap should NOT run because the index is non-empty.
    second = _docfolder(tmp_path, "second")
    add_saved_search(second, "y", {"search_text": "y"})
    # Save directly via collection.save_collection to avoid registering in index.
    from peekdocs.collection import load_collection, save_collection
    c = load_collection(second)
    c["suites"]["Hidden"] = ["y"]
    save_collection(second, c)
    # Manually clear Hidden from index (it wasn't auto-registered since we bypassed add_suite).
    hist = os.path.join(str(isolate_home), ".peekdocs_history.json")
    with open(hist, "w", encoding="utf-8") as f:
        json.dump([{"folder": second, "search_text": "y"}], f)

    # Should NOT discover Hidden, because bootstrap only fires on an empty index.
    assert find_suite("Hidden") == []
    # But 'Other' is still findable.
    assert find_suite("Other") == [os.path.abspath(folder)]
