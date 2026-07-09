#!/usr/bin/env python3
"""Verify that internal links in the project's Markdown resolve.

Checks every tracked ``*.md`` file for inline Markdown links (``[text](target)``)
and reports any whose:

  * target file does not exist (resolved relative to the linking file), or
  * ``#anchor`` does not match a heading in the target ``.md`` file.

Anchors are matched against GitHub's heading-slug algorithm (lowercase, strip
punctuation, spaces → hyphens, de-duplicate with ``-1``/``-2``) plus any
explicit HTML ``id=``/``name=`` anchors in the target. Fenced code blocks are
skipped when both extracting headings and scanning for links.

Scope / limitations (kept deliberately narrow to avoid false positives):
  * Only tracked files (``git ls-files '*.md'``) — vendored/venv docs excluded.
  * Only inline Markdown links; raw HTML ``<a href>`` / ``<img src>`` are not
    checked. External links (http/https/mailto/tel/ftp) are skipped.

Exit status: 0 = all internal links resolve, 1 = broken links found,
2 = could not enumerate files.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
HTML_ANCHOR = re.compile(r'(?:id|name)\s*=\s*"([^"]+)"')
# Inline links [text](target ...) — ignore image alt collisions via the (?<!\]) guard.
LINK = re.compile(r"(?<!\])\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
EXTERNAL = re.compile(r"^(https?:|mailto:|tel:|ftp:|#!|data:)")


def read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def slug(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)                     # drop inline HTML
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)     # [txt](url) -> txt
    text = text.replace("`", "")
    s = re.sub(r"[^\w\- ]", "", text.strip().lower())
    return s.replace(" ", "-")


def anchors_for(path: str) -> set[str]:
    """Heading slugs (code fences skipped) plus explicit HTML id/name anchors."""
    slugs: set[str] = set()
    counts: dict[str, int] = {}
    in_fence = False
    text = read(path)
    for line in text.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING.match(line)
        if not m:
            continue
        s = slug(m.group(2))
        n = counts.get(s, 0)
        counts[s] = n + 1
        slugs.add(s if n == 0 else f"{s}-{n}")
    for m in HTML_ANCHOR.finditer(text):
        slugs.add(m.group(1).lower())
    return slugs


def tracked_markdown() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z", "*.md"],
        check=True, capture_output=True, text=True,
    ).stdout
    return [p for p in out.split("\0") if p]


def main() -> int:
    try:
        files = tracked_markdown()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"error: could not list tracked markdown files: {exc}", file=sys.stderr)
        return 2

    anchor_cache: dict[str, set[str]] = {}

    def anchors(path: str) -> set[str]:
        if path not in anchor_cache:
            anchor_cache[path] = anchors_for(path) if os.path.isfile(path) else set()
        return anchor_cache[path]

    broken: list[tuple[str, str, str]] = []
    checked = 0

    for f in files:
        base = os.path.dirname(f)
        in_fence = False
        for line in read(f).splitlines():
            if FENCE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for target in LINK.findall(line):
                if EXTERNAL.match(target):
                    continue
                checked += 1
                if target.startswith("#"):
                    filepart, anchor = f, target[1:]
                else:
                    fp, _, anchor = target.partition("#")
                    filepart = os.path.normpath(os.path.join(base, fp))
                if not (os.path.isfile(filepart) or os.path.isdir(filepart)):
                    broken.append((f, target, "FILE MISSING"))
                    continue
                if anchor and filepart.endswith(".md") and anchor.lower() not in anchors(filepart):
                    broken.append((f, target, "ANCHOR MISSING"))

    print(f"Checked {checked} internal links across {len(files)} markdown files.")
    if broken:
        print(f"\n{len(broken)} broken internal link(s):\n")
        for src, tgt, why in broken:
            print(f"  [{why}] {src} -> {tgt}")
        return 1
    print("All internal documentation links resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
