"""Example regex patterns seeded into the user's regex collections on first GUI launch.

Conscious design choices behind what's in (and out of) this list:

- **One collection, capability-only categorization.** A single "Examples"
  collection that sits alongside whatever the user builds. No "Software
  development" / "Healthcare" / "Legal" sub-collections — peekdocs's
  THEORY_OF_OPERATION principle 7 forbids audience-coded shipping, and
  sub-collections by audience are the slippery slope. One flat
  "Examples" list dodges that question entirely.

- **Truly universal patterns only.** Email is email anywhere; UUIDs are
  deterministic; semantic versions are RFC-grade. Region-coded patterns
  (US phone numbers, US ZIP codes, fiscal quarters) are excluded —
  users in those regions can write them in 30 seconds; users outside
  those regions find them noise.

- **Pattern names describe what they match, not how to use them.**
  "Email address" not "Customer emails." "JIRA-style ticket ID" not
  "Ticket reference." This sidesteps semantic over-promising — a regex
  matches a string shape, not a meaning, and the user is the one
  evaluating whether a match means what they think it does.

- **Seeded once, owned by the user thereafter.** Loaded into
  ``~/.peekdocs_regex_collections.json`` on first GUI launch when the
  file doesn't yet exist, then never touched again by peekdocs.
  Modifications, deletions, additions all survive upgrades. There's no
  "patch to refresh examples to v1.0.24's improvements" — the user owns
  their copy from the moment it's seeded.
"""

# Each entry mirrors the schema used by the GUI's save/restore code in
# peekdocs/gui/_mixin_tools.py: a list of {enabled, name, regex} dicts.
# "enabled": "on" makes the pattern active on collection-run by default;
# the user can toggle individual rows once they've opened the collection.
EXAMPLES_COLLECTION = [
    {"enabled": "on", "name": "Email address",
     "regex": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"},
    {"enabled": "on", "name": "URL (http/https)",
     "regex": r"\bhttps?://[^\s<>\"']+"},
    {"enabled": "on", "name": "IPv4 address",
     "regex": r"\b(?:\d{1,3}\.){3}\d{1,3}\b"},
    {"enabled": "on", "name": "IPv6 address",
     "regex": r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"},
    {"enabled": "on", "name": "ISO date (YYYY-MM-DD)",
     "regex": r"\b\d{4}-\d{2}-\d{2}\b"},
    {"enabled": "on", "name": "ISO time (HH:MM or HH:MM:SS)",
     "regex": r"\b\d{2}:\d{2}(?::\d{2})?\b"},
    {"enabled": "on", "name": "UUID (canonical 8-4-4-4-12)",
     "regex": r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"},
    {"enabled": "on", "name": "Semantic version (1.2.3 or v1.2.3)",
     "regex": r"\bv?\d+\.\d+\.\d+(?:-[\w.]+)?\b"},
    {"enabled": "on", "name": "Hex color code (#RGB or #RRGGBB)",
     "regex": r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?\b"},
    {"enabled": "on", "name": "Markdown link",
     "regex": r"\[[^\]]+\]\([^)]+\)"},
    {"enabled": "on", "name": "TODO marker",
     "regex": r"\bTODO\b"},
    {"enabled": "on", "name": "FIXME marker",
     "regex": r"\bFIXME\b"},
    {"enabled": "on", "name": "JIRA-style ticket ID (PREFIX-NNN)",
     "regex": r"\b[A-Z]{2,}-\d+\b"},
    {"enabled": "on", "name": "ISBN-13",
     "regex": r"\b97[89]-?(?:\d-?){9}\d\b"},
    {"enabled": "on", "name": "DOI (Crossref pattern)",
     "regex": r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b"},
    {"enabled": "on", "name": "USD amount (with optional commas / cents)",
     "regex": r"\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?"},
    {"enabled": "on", "name": "Environment variable reference",
     "regex": r"\$\{?[A-Z_][A-Z0-9_]*\}?"},
]


def seed_examples_if_missing(collections_path):
    """Write an Examples collection to *collections_path* iff the file doesn't exist.

    No-op if the file already exists, regardless of whether it contains an
    Examples entry — meaning a user who deleted Examples doesn't get it
    re-created on next launch. The check is purely "has the file ever
    been written before?", which keeps the contract simple: peekdocs
    seeds once at the moment the user first interacts with regex collections,
    and never modifies their data after that.

    Returns ``True`` if seeding happened, ``False`` otherwise (file already
    existed, or write failed). Callers don't need to act on the return —
    it's there for telemetry / debugging only.
    """
    import json
    import os
    if os.path.exists(collections_path):
        return False
    try:
        with open(collections_path, "w", encoding="utf-8") as f:
            json.dump({"Examples": EXAMPLES_COLLECTION}, f, indent=2, ensure_ascii=False)
        return True
    except OSError:
        return False
