"""Compare two peekdocs JSON outputs and report what changed.

Powers ``peekdocs --diff peekdocs_snapshot_old.json peekdocs_snapshot_new.json``. Both inputs can be any
peekdocs JSON shape — standard search ``--stdout`` / ``-o json``, inverse
search, or regex-collection — and either may or may not have been produced
with ``--hash``. The diff is computed at the file level: a file is keyed by
``(folder, filename)`` so renames look like a remove + new pair.

The five buckets:
  * ``new``       — files matching now that weren't matching before
  * ``removed``   — files that were matching but no longer match
  * ``changed``   — same file, different match count
  * ``modified``  — same path AND same match count, but sha256 differs.
                    Requires --hash on both inputs; otherwise silently empty.
  * unchanged     — summarized as a count only, not enumerated

If ``matches_per_file`` is absent (e.g. a regex-collection JSON without
--hash), it is reconstructed from the flat ``matches`` array so the diff
still works.
"""

import json


def load_json(path):
    """Load a peekdocs JSON file. Returns (data, None) on success or (None, error_message)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return (json.load(f), None)
    except FileNotFoundError:
        return (None, f"file not found: {path}")
    except json.JSONDecodeError as exc:
        return (None, f"invalid JSON in {path}: {exc}")
    except OSError as exc:
        return (None, f"could not read {path}: {exc}")


def _files_from(data):
    """Normalize any peekdocs JSON shape into a {(folder, filename): entry} dict.

    Prefers ``matches_per_file`` (which carries the authoritative per-file
    match count and any sha256). Falls back to ``inverse_files``, then to
    reconstructing per-file counts from the flat ``matches`` array.
    """
    out = {}

    mpf = data.get("matches_per_file") if isinstance(data, dict) else None
    if mpf:
        for entry in mpf:
            key = (entry.get("folder", ""), entry.get("filename", ""))
            out[key] = {
                "filename": entry.get("filename"),
                "folder": entry.get("folder"),
                "matches": entry.get("matches", 0),
                "sha256": entry.get("sha256"),
            }
        return out

    inv = data.get("inverse_files") if isinstance(data, dict) else None
    if inv:
        for entry in inv:
            key = (entry.get("folder", ""), entry.get("filename", ""))
            out[key] = {
                "filename": entry.get("filename"),
                "folder": entry.get("folder"),
                "matches": 0,  # inverse is binary: presence is the signal
                "sha256": entry.get("sha256"),
            }
        return out

    # Fall back: reconstruct from the flat matches array (regex-collection
    # without --hash). One entry per (folder, filename), match count by tally.
    matches = data.get("matches", []) if isinstance(data, dict) else []
    for m in matches:
        key = (m.get("folder", ""), m.get("filename", ""))
        if key not in out:
            out[key] = {
                "filename": m.get("filename"),
                "folder": m.get("folder"),
                "matches": 0,
                "sha256": None,
            }
        out[key]["matches"] += 1
    return out


def compute_diff(old, new):
    """Compare two peekdocs JSON payloads. Returns a dict ready for human or JSON output."""
    old_files = _files_from(old)
    new_files = _files_from(new)
    old_keys = set(old_files)
    new_keys = set(new_files)

    new_only = [new_files[k] for k in sorted(new_keys - old_keys)]
    removed = [old_files[k] for k in sorted(old_keys - new_keys)]

    changed = []
    modified = []
    unchanged = 0

    for k in sorted(old_keys & new_keys):
        o = old_files[k]
        n = new_files[k]
        if o.get("matches") != n.get("matches"):
            changed.append({
                "filename": n["filename"],
                "folder": n["folder"],
                "old_matches": o.get("matches", 0),
                "new_matches": n.get("matches", 0),
                "delta": n.get("matches", 0) - o.get("matches", 0),
                "old_sha256": o.get("sha256"),
                "new_sha256": n.get("sha256"),
            })
        elif o.get("sha256") and n.get("sha256") and o["sha256"] != n["sha256"]:
            modified.append({
                "filename": n["filename"],
                "folder": n["folder"],
                "matches": n.get("matches"),
                "old_sha256": o["sha256"],
                "new_sha256": n["sha256"],
            })
        else:
            unchanged += 1

    old_total = sum((f.get("matches") or 0) for f in old_files.values())
    new_total = sum((f.get("matches") or 0) for f in new_files.values())

    return {
        "new": new_only,
        "removed": removed,
        "changed": changed,
        "modified": modified,
        "unchanged_count": unchanged,
        "old_file_count": len(old_files),
        "new_file_count": len(new_files),
        "old_match_total": old_total,
        "new_match_total": new_total,
    }


def is_actionable(diff):
    """True if the diff contains anything an IT user would want alerted on.

    "Actionable" = new matching files, OR files that gained matches, OR
    files whose content changed (sha256 differs). Removed files are not
    actionable by themselves — deleting a file is the normal way to stop
    something from showing up in a scan.
    """
    if diff["new"]:
        return True
    if diff["modified"]:
        return True
    for c in diff["changed"]:
        if c["delta"] > 0:
            return True
    return False


def format_human(diff, old_path, new_path):
    """Return a multi-line human-readable report of *diff*."""
    lines = []
    lines.append(f"Diff: {old_path} → {new_path}")
    lines.append("")
    lines.append(
        f"  Old: {diff['old_file_count']} matching file(s), {diff['old_match_total']} total match(es)"
    )
    lines.append(
        f"  New: {diff['new_file_count']} matching file(s), {diff['new_match_total']} total match(es)"
    )
    lines.append("")

    if diff["new"]:
        lines.append(f"NEW: {len(diff['new'])} file(s) now matching:")
        for entry in diff["new"]:
            lines.append(f"  + {entry['filename']}  ({entry['matches']} match(es))  {entry['folder']}")
        lines.append("")

    if diff["removed"]:
        lines.append(f"REMOVED: {len(diff['removed'])} file(s) no longer matching:")
        for entry in diff["removed"]:
            lines.append(f"  - {entry['filename']}  (was {entry['matches']} match(es))  {entry['folder']}")
        lines.append("")

    if diff["changed"]:
        lines.append(f"CHANGED: {len(diff['changed'])} file(s) with different match counts:")
        for c in diff["changed"]:
            sign = "+" if c["delta"] > 0 else ""
            lines.append(
                f"  ~ {c['filename']}  {c['old_matches']} → {c['new_matches']}  ({sign}{c['delta']})  {c['folder']}"
            )
        lines.append("")

    if diff["modified"]:
        lines.append(f"MODIFIED: {len(diff['modified'])} file(s) with same match count but changed content (sha256 differs):")
        for m in diff["modified"]:
            lines.append(f"  ! {m['filename']}  ({m['matches']} match(es), content changed)  {m['folder']}")
        lines.append("")

    lines.append(f"UNCHANGED: {diff['unchanged_count']} file(s)")
    net = diff["new_match_total"] - diff["old_match_total"]
    sign = "+" if net > 0 else ""
    lines.append(f"Net match delta: {sign}{net} ({diff['old_match_total']} → {diff['new_match_total']})")
    return "\n".join(lines) + "\n"
