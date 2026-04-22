# peekdocs Library API Reference

Use peekdocs programmatically from Python code. For CLI and GUI usage, see the [User Guide](USER_GUIDE.md) or [README](../README.md).

## Table of Contents

- [Basic Usage](#basic-usage)
- [With Options](#with-options)
- [Parameters](#parameters)
- [Return Value](#return-value)
- [Notes](#notes)
- [Error Handling](#error-handling)

## Basic Usage

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

    # Search emails for SSNs
    result = search(
        [r"\d{3}-\d{2}-\d{4}"],
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
| `context_before` | `int` | `0` | Lines to include before each match |
| `context_after` | `int` | `0` | Lines to include after each match |
| `proximity` | `int` | `0` | Require terms within N words of each other |
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

Each `SearchMatch` has fields: `file_dir`, `filename`, `line_num`, `text`.

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
