# peekdocs Library API Reference

Use peekdocs — a privacy-first local document search and analysis tool — programmatically from Python code. For CLI and GUI usage, see the [User Guide](USER_GUIDE.md) or [README](../README.md).

**Prerequisites.** Python 3.10+ with peekdocs installed via pipx or pip — see [Installation](../README.md#installation). Run `peekdocs --check` to verify your install is healthy before scripting against the API.

## API at a Glance

Every search workflow available in the CLI and GUI is also available in the Python API:

| Workflow | API Function | CLI Flag | GUI |
|---|---|---|---|
| Single search | `search()` | `peekdocs "term"` | Search bar |
| Named search suite | `run_suite("name")` | `--suite "name"` | Tools → Search Suites |
| Named regex collection | `run_regex_collection("name")` | `--regex-collection "name"` | Regex Search → Restore |
| List suites | `list_suites(directory)` | — | Tools → Search Suites |
| List regex collections | `list_regex_collections()` | `--regex-collection --list` | Regex Search → Restore |

### Quick examples

```python
from peekdocs import search, run_suite, run_regex_collection
from peekdocs import list_suites, list_regex_collections

def main():
    # Single search
    result = search(["budget"], directory="/path/to/docs", recursive=True)
    print(f"{len(result.matches)} matches")

    # Run a named search suite
    suite = run_suite("Weekly Code Scan", directory="/path/to/docs")
    for sr in suite.search_results:
        print(f"  {sr.search_name}: {len(sr.matches)} matches")

    # Run a named regex collection
    collection = run_regex_collection("Code Patterns", directory="/path/to/docs", recursive=True)
    for pr in collection.pattern_results:
        print(f"  {pr.name}: {len(pr.matches)} matches")

    # List what's available
    print("Suites:", list_suites("/path/to/docs"))
    print("Regex collections:", list_regex_collections())

if __name__ == "__main__":
    main()
```

See the sections below for full parameter details, return values, and error handling.

## Table of Contents

- [API at a Glance](#api-at-a-glance)
  - [Quick examples](#quick-examples)
- [Complete Working Example](#complete-working-example)
- [Basic Usage](#basic-usage)
- [With Options](#with-options)
- [Parameters](#parameters)
- [Return Value](#return-value)
- [Search Suites](#search-suites)
- [Regex Collections](#regex-collections)
- [Notes](#notes)
- [Error Handling](#error-handling)
- [Next Steps](#next-steps)

## Complete Working Example

This example is available as [`samples/api_example.py`](../samples/api_example.py) and can be run directly:

```python
"""Example: Using the peekdocs Python API to search documents programmatically."""

from peekdocs import search


def main():
    # Basic search — find "budget" in the current directory
    result = search(["budget"], directory=".")

    print(f"Files searched: {len(result.files_searched)}")
    print(f"Matches found: {len(result.matches)}")
    print(f"Elapsed: {result.elapsed:.2f}s")
    print()

    # Print each match
    for match in result.matches[:10]:  # first 10 matches
        print(f"  {match.filename}, line {match.line_num}: {match.text[:80]}")

    print()

    # Advanced search — AND mode, recursive, only PDFs and Word docs
    result = search(
        ["invoice", "payment"],
        directory=".",
        match_all=True,         # AND mode — both terms must appear on the same line
        recursive=True,         # search subfolders
        file_types=[".pdf", ".docx"],  # only PDFs and Word docs
    )

    print(f"AND search: {len(result.matches)} match(es) in {len(result.files_searched)} file(s)")

    # Regex search — find invoice numbers like INV-12345
    result = search(
        [r"INV-\d{4,}"],
        directory=".",
        use_regex=True,
        recursive=True,
    )

    print(f"Invoice pattern: {len(result.matches)} match(es) found")

    # Access match details
    for match in result.matches:
        print(f"  File: {match.filename}")
        print(f"  Line: {match.line_num}")
        print(f"  Text: {match.text}")
        print()


# Required for multiprocessing on macOS and Windows
if __name__ == "__main__":
    main()
```

## Basic Usage

The simplest way to use the API is to call `search()` with a list of terms and a directory:

```python
from peekdocs import search

def main():
    result = search(["budget", "revenue"], directory="/path/to/docs")

    print(f"Found {len(result.matches)} matches in {len(result.files_searched)} files")
    for match in result.matches:
        print(f"  {match.filename}:{match.line_num}: {match.text}")

# Required for multiprocessing on macOS and Windows
if __name__ == "__main__":
    main()
```

> **Note:** The `if __name__ == "__main__":` guard is required because peekdocs uses multiprocessing to search files in parallel. Without it, macOS and Windows will crash with a `RuntimeError`. See [`samples/api_example.py`](../samples/api_example.py) for a complete working example.

## With Options

`search()` accepts many keyword arguments for fine-grained control. The example below shows several common patterns:

```python
from peekdocs import search

def main():
    # Wildcard search in specific file types, with subdirectories
    result = search(
        ["budg*"],
        directory="/path/to/docs",
        use_wildcard=True,
        recursive=True,
        file_types=[".pdf", ".docx"],
    )

    # Regex search with AND mode
    result = search(
        [r"\d{3}-\d{3}-\d{4}", "invoice"],
        directory="/path/to/docs",
        use_regex=True,
        match_all=True,
    )

    # Boolean expression search
    result = search(
        [],
        directory="/path/to/docs",
        expression="(budget OR revenue) AND (cost OR profit)",
    )

    # Expression with wildcard mode
    result = search(
        [],
        directory="/path/to/docs",
        expression="budg* AND rev*",
        use_wildcard=True,
    )

    # Range query — filter by value ranges
    result = search(
        ["invoice"],
        directory="/path/to/docs",
        range_filters=["amount:1000..5000", "date:2024-01-01..2024-12-31"],
    )

    # Range-only search (no text terms)
    result = search(
        [],
        directory="/path/to/docs",
        range_filters=["amount:1000..5000"],
    )

    # Range specs inside boolean expressions
    result = search(
        [],
        directory="/path/to/docs",
        expression="budget AND amount:1000..5000",
    )

    # Filename range — filter files by date in filename
    result = search(
        ["budget"],
        directory="/path/to/docs",
        range_filters=["fn:date:2024-01-01..2024-12-31"],
    )

    # Search emails for structured reference IDs (e.g., ORD-12345, REF-9876)
    result = search(
        [r"\b[A-Z]{2,3}-\d{4,}\b"],
        directory="/path/to/exported-emails",
        use_regex=True,
        file_types=[".eml", ".msg", ".pst"],
    )

    # Search inside ZIP archives
    result = search(
        ["confidential"],
        directory="/path/to/docs",
        file_types=[".zip", ".7z"],
    )

    # Search legacy and modern Office files together
    result = search(
        ["budget"],
        directory="/path/to/docs",
        file_types=[".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"],
    )

    # Progress tracking
    def on_progress(done, total, filename):
        print(f"  [{done}/{total}] {filename}")

    result = search(["error"], directory="/var/log", progress=on_progress)

# Required for multiprocessing on macOS and Windows
if __name__ == "__main__":
    main()
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search_terms` | `list[str]` | *(required)* | Terms to search for (pass `[]` when using `expression` or `range_filters`) |
| `directory` | `str` | Current directory | Directory to search in |
| `match_all` | `bool` | `False` | Require ALL terms (AND mode) |
| `expression` | `str` | `None` | Boolean expression with AND, OR, NOT, parentheses, and range specs (e.g. `"(budget OR revenue) AND NOT draft"`, `"budget AND amount:1000..5000"`) |
| `recursive` | `bool` | `False` | Search subdirectories |
| `use_regex` | `bool` | `False` | Treat terms as regex patterns |
| `use_fuzzy` | `bool` | `False` | Approximate matching |
| `use_wildcard` | `bool` | `False` | Wildcard patterns (`*` and `?`) |
| `use_whole_word` | `bool` | `False` | Whole-word matching — matches complete words only |
| `use_ocr` | `bool` | `False` | OCR for scanned PDFs and images |
| `exclude_terms` | `list[str]` | `None` | Exclude lines matching these terms |
| `file_types` | `list[str]` | `None` | Limit to these extensions (e.g. `[".pdf", ".docx"]`) |
| `file_names` | `list[str]` | `None` | Search only these specific files |
| `context_before` | `int` | `0` | Lines to include before each match. What counts as a "line" follows the unit peekdocs indexes per file format: a literal line for plain text and source code, a paragraph for Word (.docx) and PDF, a row for Excel. Paragraph-heavy formats can include several sentences per "line." |
| `context_after` | `int` | `0` | Lines to include after each match. Same per-format meaning as `context_before` — see above. |
| `proximity` | `int` | `0` | Require terms within N words of each other |
| `line_proximity` | `int` | `0` | Require terms within N lines of each other (the line-proximity counterpart to `proximity`, which is word-proximity) |
| `cores` | `int` | Auto | CPU cores for parallel processing |
| `use_index` | `bool` | Auto | Use search index if available |
| `progress` | `callable` | `None` | Callback `progress(done, total, filename)` |
| `range_filters` | `list[str]` | `None` | Range filter specs (e.g. `["amount:1000..5000", "date:2024-01-01..2024-12-31"]`). Use `fn:` prefix for filename ranges (e.g. `["fn:date:2024-01-01..2024-12-31"]`) |
| `max_file_size_mb` | `int` | `100` | Skip files larger than this (in MB). Prevents slow searches and memory issues from very large files. Set to `0` for no limit |

## Return Value

`search()` returns a `SearchResult` with these fields:

| Field | Type | Description |
|-------|------|-------------|
| `matches` | `list[SearchMatch]` | List of matches found |
| `files_searched` | `list[str]` | Absolute paths of all files examined |
| `skipped_files` | `list[tuple]` | Files that couldn't be read: `(filename, error_msg)` |
| `elapsed` | `float` | Search time in seconds |
| `used_index` | `bool` | Whether the indexed search path was used |
| `index_bypass_reason` | `str` | Non-empty when the index was requested but bypassed (e.g., regex / fuzzy / wildcard / proximity queries fall through to direct scan because FTS5 can't accelerate them). Empty string otherwise |
| `index_stale_notice` | `str` | Non-empty when the index's stored parameters don't match the current `max_file_size_mb` (e.g., the index was built with a 100 MB limit but the call passes 0 / no limit). The notice text names the mismatch and points the user at `peekdocs --index` to rebuild. The search still runs against the existing index; this is informational, not a failure. Empty string otherwise |

Each `SearchMatch` has fields: `file_dir`, `filename`, `line_num`, `text`.

## Search Suites

Run saved search suites programmatically. Suites are groups of saved searches created in the GUI (Tools → Search Suites) and stored per-folder in `.peekdocs_collection.json`.

### List suites in a folder

```python
from peekdocs import list_suites

suites = list_suites("/path/to/docs")
print(suites)  # e.g. {'Weekly Code Scan': ['Find passwords', 'Find TODOs', 'Find drafts']}
```

### Run a suite

```python
from peekdocs import run_suite

def main():
    result = run_suite(
        "Weekly Code Scan",
        directory="/path/to/docs",
    )

    print(f"Suite: {result.suite}")
    print(f"Total matches: {result.total_matches}")
    print(f"Elapsed: {result.elapsed:.2f}s")
    print(f"Skipped searches: {result.skipped_searches}")

    for sr in result.search_results:
        print(f"  {sr.search_name} ({sr.mode}): {len(sr.matches)} matches in {len(sr.files_searched)} files")
        for match in sr.matches[:3]:  # first 3 per search
            print(f"    {match.filename}:{match.line_num}: {match.text[:80]}")

if __name__ == "__main__":
    main()
```

### With progress tracking

```python
from peekdocs import run_suite

def main():
    def on_progress(i, total, name):
        if i < total:
            print(f"  [{i+1}/{total}] {name}")

    result = run_suite(
        "Weekly Code Scan",
        directory="/path/to/docs",
        progress=on_progress,
    )

if __name__ == "__main__":
    main()
```

### run_suite() Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | *(required)* | Name of a saved search suite |
| `directory` | `str` | Current directory | Directory containing the suite's `.peekdocs_collection.json` |
| `progress` | `callable` | `None` | Callback `progress(search_index, total_searches, search_name)` |
| `max_file_size_mb` | `int` | `100` | Skip files larger than this (MB). 0 = no limit |

### Return Value

`run_suite()` returns a `SuiteResult` with these fields:

| Field | Type | Description |
|-------|------|-------------|
| `suite` | `str` | Suite name |
| `search_results` | `list[SuiteSearchResult]` | Per-search results |
| `total_matches` | `int` | Sum of all search match counts |
| `elapsed` | `float` | Total time in seconds |
| `skipped_searches` | `list[tuple]` | Searches not found: `(name, reason)` |

Each `SuiteSearchResult` has fields: `search_name`, `search_terms`, `matches` (list of `SearchMatch`), `files_searched`, `elapsed`, `mode` ("ALL" or "ANY").

### Error Handling

| Exception | When |
|-----------|------|
| `FileNotFoundError` | No collection file exists in the directory |
| `KeyError` | Named suite not found (message lists available suites) |
| `ValueError` | Suite has no searches |

## Regex Collections

Run saved regex collections programmatically. Collections are created in the GUI (Regex Search → Save Collection As) and stored in `~/.peekdocs_regex_collections.json`.

### List saved collections

```python
from peekdocs import list_regex_collections

names = list_regex_collections()
print(names)  # e.g. ['Code Patterns', 'Financial', 'Invoice Extraction']
```

### Run a collection

```python
from peekdocs import run_regex_collection

def main():
    result = run_regex_collection(
        "Code Patterns",
        directory="/path/to/project",
        recursive=True,
    )

    print(f"Collection: {result.collection}")
    print(f"Total matches: {result.total_matches}")
    print(f"Elapsed: {result.elapsed:.2f}s")
    print(f"Skipped patterns: {result.skipped_patterns}")

    for pr in result.pattern_results:
        print(f"  {pr.name}: {len(pr.matches)} matches in {pr.files_matched} files")
        for match in pr.matches[:3]:  # first 3 per pattern
            print(f"    {match.filename}:{match.line_num}: {match.text[:80]}")

if __name__ == "__main__":
    main()
```

### With progress tracking

```python
from peekdocs import run_regex_collection

def main():
    def on_progress(i, total, name):
        if i < total:
            print(f"  [{i+1}/{total}] {name}")

    result = run_regex_collection(
        "Code Review",
        directory=".",
        recursive=True,
        progress=on_progress,
    )

if __name__ == "__main__":
    main()
```

### run_regex_collection() Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | *(required)* | Name of a saved regex collection |
| `directory` | `str` | Current directory | Directory to search in |
| `recursive` | `bool` | `False` | Search subdirectories |
| `progress` | `callable` | `None` | Callback `progress(pattern_index, total_patterns, pattern_name)` |
| `max_file_size_mb` | `int` | `100` | Skip files larger than this (MB). 0 = no limit |

### Return Value

`run_regex_collection()` returns a `CollectionResult` with these fields:

| Field | Type | Description |
|-------|------|-------------|
| `collection` | `str` | Collection name |
| `pattern_results` | `list[PatternResult]` | Per-pattern results |
| `total_matches` | `int` | Sum of all pattern match counts |
| `files_searched` | `list[str]` | Absolute paths of all files examined |
| `elapsed` | `float` | Total time in seconds |
| `skipped_patterns` | `list[tuple]` | Patterns with invalid regex: `(name, error_msg)` |

Each `PatternResult` has fields: `name`, `regex`, `matches` (list of `SearchMatch`), `files_matched` (int).

### Error Handling

| Exception | When |
|-----------|------|
| `FileNotFoundError` | No collections file exists (`~/.peekdocs_regex_collections.json`) |
| `KeyError` | Named collection not found (message lists available names) |
| `ValueError` | Collection has no enabled patterns |

## Notes

- **No match limit:** The API returns all matches. The CLI's `-m` (max matches) flag caps report output only — it does not exist in the API. If you need to limit results, slice `result.matches` after the search.
- **No inverse mode:** Inverse search (listing files that do *not* contain terms) is a GUI/CLI feature. To achieve the same result with the API, compare `result.files_searched` against `result.matches` to find files with zero matches.

## Error Handling

`search()` raises `ValueError` for invalid parameter combinations (e.g. combining regex + fuzzy) and `FileNotFoundError` if specified files are not found.

```python
from peekdocs import search

def main():
    try:
        result = search([r"[invalid"], use_regex=True)
    except ValueError as e:
        print(f"Invalid search: {e}")

if __name__ == "__main__":
    main()
```

**Stuck on something `try/except` won't catch?** If your script crashes with `ModuleNotFoundError`, hangs without finishing, or behaves differently than the CLI, first run `peekdocs --check` from your terminal — it verifies your Python version, dependencies, Tesseract availability, SQLite, and free disk space, and tells you exactly what's missing. If that's clean, see [FAQ & Troubleshooting](TROUBLESHOOTING.md) for common Python-API and install pitfalls (especially the `multiprocessing` / `__main__` guard issue if your script crashes on Mac or Windows).

## Next Steps

For richer end-to-end automation patterns, see the User Guide's [worked nightly source-tree watch example](USER_GUIDE.md#a-worked-example-nightly-source-tree-watch) (a complete cron pipeline using `--stdout`, `--hash`, `--diff`, and an alert step) and the [Search Suite Use Cases](USER_GUIDE.md#search-suite-use-cases) section (driving suites and regex collections in Python loops). The complete CLI flag reference lives in the [Flag Use Summary](USER_GUIDE.md#flag-use-summary).
