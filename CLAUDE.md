# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

peekdocs is a privacy-first local document search and analysis platform for Windows, macOS, and Linux. Search across 100+ file types using keyword, fuzzy, OCR, and advanced regex workflows. Features batch analysis, highlighted reports, automated reporting, reusable search profiles, and interfaces for CLI, GUI, and Python automation. Free and open-source under the MIT license.

- CLI entry point: `peekdocs/cli.py` → `main()`
- GUI entry point: `peekdocs/gui/__init__.py` → `main()`

## Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Install in development mode
pip install -e .

# Run the CLI
peekdocs <query>

# Run the GUI
peekdocs-gui

# Run all tests
pytest tests/ -v

# Run a single test
pytest tests/test_cli.py::test_query -v
```

## Architecture

- `peekdocs/` — Main package.
  - `cli.py` — argparse CLI entry point (`peekdocs` console script). Delegates diagnostic subcommands to `commands/*.py`.
  - `commands/` — Extracted CLI subcommand handlers (Phase 1): `check.py`, `diff.py`, `runs.py`. Each exposes `handle_*(args) -> int`. Standard search, `--suite`, and `--regex-collection` remain in `cli._main_inner` for now.
  - `gui/` — customtkinter GUI package (`peekdocs-gui` console script), split into feature-based mixins after the v1.2.76 mixin-tools-split refactor:
    - `_app.py` — `PeekDocsApp` class inheriting all mixins
    - `_helpers.py` — free functions (importable without customtkinter)
    - `_tooltip.py` — `Tooltip` widget
    - `_mixin_build.py` — UI construction, widget layout, tooltips
    - `_mixin_search.py` — search execution, multi-folder handling, results rendering
    - `_mixin_data.py` — settings, history, bookmarks, About dialog, `~/.peekdocsrc` I/O
    - `_mixin_tools.py` — Miscellaneous Tools menu features (System Check, Diff Snapshots, Schedule Search) — 873 LOC after the split
    - `_mixin_wizard.py` — Search Wizard + Regex Wizard picker
    - `_mixin_regex_search.py` — Regex Search feature + Regex Tester + both help panels
    - `_mixin_suites.py` — Search Suites picker + execution
    - `_mixin_file_analysis.py` — Nine folder-scanning tools (File Inventory, Duplicate Finder, Large Files, etc.)
    - `_mixin_help_panels.py` — Eight "?"-help popups
  - `api.py` — public Python API (`search()`, `SearchMatch`, `SearchResult`, plus `run_suite`, `run_regex_collection`, `list_*`)
  - `errors.py` — public exception hierarchy (`PeekdocsError`, `QueryError`, `RangeError`, `NameNotFoundError`)
  - `paths.py` — shared path + platform helpers (`resource_path`, `find_tesseract`, `format_bytes`)
  - `scanner.py` — file processing and discovery (100+ file types)
  - `parser.py` — CLI flag parsing and OCR/fuzzy preflight
  - `reporter.py` — report generation (TXT, DOCX, CSV, JSON, PDF, HTML)
  - `indexer.py` — optional SQLite FTS5 search index
  - `range_query.py`, `expr_parser.py`, `diff.py`, `watcher.py`, `run_log.py`, `notifier.py`, `translator.py`, `collection.py`, `suite_index.py`, `i18n.py`, `regex_examples.py`, `wizard_patterns.py`, `constants.py` — engine + persistence + platform utilities
- `tests/` — Pytest test suite (22 test files, 711 tests).
- `pyproject.toml` — Project metadata, dependencies, console script configuration, and `[tool.mypy]` config (8 files in the typed public surface). Uses setuptools as build backend.
