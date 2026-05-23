"""Global suite-name → folder index, stored at ~/.peekdocs_suites_index.json.

Lets the CLI find a suite by name from any working directory, so users do not
have to remember which folder a suite was created in. The index is kept up to
date by ``collection.add_suite`` / ``remove_suite`` / ``rename_suite``.

If the index is missing or empty, ``find_suite`` and ``list_suites_global``
trigger a one-time bootstrap that reads folders the user has previously
searched (from ``~/.peekdocs_history.json`` and the ``folder`` /
``regex_search_folder`` keys in ``~/.peekdocsrc``) and registers any suites
found there.
"""

import json
import os
import tempfile

INDEX_FILENAME = ".peekdocs_suites_index.json"
INDEX_VERSION = 1


def index_path():
    return os.path.join(os.path.expanduser("~"), INDEX_FILENAME)


def _empty_index():
    return {"version": INDEX_VERSION, "entries": []}


def load_index():
    path = index_path()
    if not os.path.exists(path):
        return _empty_index()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("version", INDEX_VERSION)
        data.setdefault("entries", [])
        return data
    except (json.JSONDecodeError, OSError):
        return _empty_index()


def save_index(data):
    path = index_path()
    dir_ = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(prefix=".peekdocs_suites_index.", dir=dir_)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _norm(folder):
    return os.path.abspath(folder) if folder else ""


def register_suite(folder, name):
    """Add or update an entry for (name, folder)."""
    folder = _norm(folder)
    if not folder or not name:
        return
    data = load_index()
    for e in data["entries"]:
        if e.get("name") == name and _norm(e.get("folder", "")) == folder:
            return
    data["entries"].append({"name": name, "folder": folder})
    save_index(data)


def unregister_suite(folder, name):
    """Remove the entry for (name, folder), if present."""
    folder = _norm(folder)
    if not folder or not name:
        return
    data = load_index()
    before = len(data["entries"])
    data["entries"] = [
        e for e in data["entries"]
        if not (e.get("name") == name and _norm(e.get("folder", "")) == folder)
    ]
    if len(data["entries"]) != before:
        save_index(data)


def _verify_entry(entry):
    """Return True iff the folder still has a collection containing this suite."""
    from peekdocs.collection import load_collection
    folder = entry.get("folder", "")
    name = entry.get("name", "")
    if not folder or not name or not os.path.isdir(folder):
        return False
    try:
        return name in load_collection(folder).get("suites", {})
    except OSError:
        return False


# Directories the bootstrap walk should skip — too big, irrelevant, or
# common dev junk that won't contain user document folders.
_SCAN_SKIP_DIRS = {
    "node_modules", "venv", ".venv", "__pycache__", "Library",
    ".cache", ".npm", ".gradle", ".m2", "Trash", ".Trash",
    "site-packages", "dist", "build",
}

# Roots to walk when looking for collection files. Constrained so the
# first-run scan is fast.
_SCAN_ROOTS = ("Documents", "Desktop")
_SCAN_MAX_DEPTH = 6
COLLECTION_FILENAME = ".peekdocs_collection.json"


def _walk_for_collections(root, max_depth=_SCAN_MAX_DEPTH):
    """Yield folder paths under *root* (up to *max_depth* deep) that hold a
    ``.peekdocs_collection.json``.  Hidden and known-junk dirs are skipped.
    """
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        return
    base_depth = root.count(os.sep)
    for dirpath, dirnames, filenames in os.walk(root):
        depth = dirpath.count(os.sep) - base_depth
        if depth >= max_depth:
            dirnames[:] = []
            continue
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".") and d not in _SCAN_SKIP_DIRS
        ]
        if COLLECTION_FILENAME in filenames:
            yield dirpath


def _candidate_bootstrap_folders():
    """Folders to scan during bootstrap.

    Pulls from the search history file, the saved ``folder`` /
    ``regex_search_folder`` keys in ``~/.peekdocsrc``, the current working
    directory, and a constrained walk of ``~/Documents`` and ``~/Desktop``.
    Returns a sorted list of unique, existing directories.
    """
    folders = set()
    cwd = os.getcwd()
    if os.path.isdir(cwd):
        folders.add(cwd)

    home = os.path.expanduser("~")

    rc = os.path.join(home, ".peekdocsrc")
    if os.path.exists(rc):
        try:
            with open(rc, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "=" not in line or line.startswith("#"):
                        continue
                    key, _, val = line.partition("=")
                    key = key.strip()
                    val = val.strip()
                    if key in ("folder", "regex_search_folder") and val and os.path.isdir(val):
                        folders.add(val)
        except OSError:
            pass

    hist = os.path.join(home, ".peekdocs_history.json")
    if os.path.exists(hist):
        try:
            with open(hist, "r", encoding="utf-8") as f:
                items = json.load(f)
            if isinstance(items, list):
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    folder = item.get("folder")
                    if folder and os.path.isdir(folder):
                        folders.add(folder)
        except (json.JSONDecodeError, OSError):
            pass

    for sub in _SCAN_ROOTS:
        root = os.path.join(home, sub)
        for found in _walk_for_collections(root):
            folders.add(found)

    return sorted(folders)


def rescan():
    """Discard the index and re-discover suites from scratch.

    Useful when users have moved folders or created suites outside the
    GUI's awareness.  Returns the freshly built index dict.
    """
    path = index_path()
    if os.path.exists(path):
        try:
            os.unlink(path)
        except OSError:
            pass
    return _bootstrap_if_empty()


def _bootstrap_if_empty():
    """Populate the index from candidate folders, but only if it is empty."""
    data = load_index()
    if data["entries"]:
        return data
    from peekdocs.collection import load_collection
    entries = []
    seen = set()
    for folder in _candidate_bootstrap_folders():
        try:
            suites = load_collection(folder).get("suites", {})
        except OSError:
            continue
        norm = _norm(folder)
        for sname in suites:
            key = (sname, norm)
            if key in seen:
                continue
            seen.add(key)
            entries.append({"name": sname, "folder": norm})
    if entries:
        data["entries"] = entries
        save_index(data)
    return data


def find_suite(name):
    """Return a list of folders that currently contain a suite named *name*.

    Stale entries (folder gone, or suite removed outside the index) are pruned.
    """
    data = _bootstrap_if_empty()
    matches = []
    stale = []
    for e in data["entries"]:
        if e.get("name") != name:
            continue
        if _verify_entry(e):
            matches.append(_norm(e.get("folder", "")))
        else:
            stale.append(e)
    if stale:
        data["entries"] = [e for e in data["entries"] if e not in stale]
        save_index(data)
    out, seen = [], set()
    for folder in matches:
        if folder not in seen:
            seen.add(folder)
            out.append(folder)
    return out


def list_suites_global():
    """Return ``[{name, folder, search_count}, ...]`` sorted by name then folder.

    Stale entries are pruned as a side effect.
    """
    from peekdocs.collection import load_collection
    data = _bootstrap_if_empty()
    valid = []
    stale = []
    seen = set()
    for e in data["entries"]:
        name = e.get("name")
        folder = _norm(e.get("folder", ""))
        key = (name, folder)
        if not name or not folder or key in seen:
            stale.append(e)
            continue
        seen.add(key)
        try:
            suites = load_collection(folder).get("suites", {})
        except OSError:
            stale.append(e)
            continue
        if name not in suites:
            stale.append(e)
            continue
        valid.append({"name": name, "folder": folder, "search_count": len(suites[name])})
    if stale:
        data["entries"] = [e for e in data["entries"] if e not in stale]
        save_index(data)
    valid.sort(key=lambda x: (x["name"].lower(), x["folder"].lower()))
    return valid
