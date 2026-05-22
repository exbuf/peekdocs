# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

peekdocs is a document search tool with CLI, GUI, and Python API. Searches 100+ file types with highlighted reports, regex search, and 8 built-in folder analysis tools.

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
  - `cli.py` — argparse CLI entry point (`peekdocs` console script)
  - `gui/` — customtkinter GUI package (`peekdocs-gui` console script), split into mixins:
    - `_app.py` — PeekDocsApp class inheriting all mixins
    - `_helpers.py` — free functions (importable without customtkinter)
    - `_tooltip.py` — Tooltip widget
    - `_mixin_build.py` — UI construction
    - `_mixin_search.py` — search execution, multi-folder, results
    - `_mixin_tools.py` — Tools menu features, regex search, wizard, help
    - `_mixin_data.py` — settings, history, bookmarks, index management
  - `api.py` — public Python API (`search()`, `SearchMatch`, `SearchResult`)
  - `scanner.py` — file processing and discovery (100+ file types)
  - `reporter.py` — report generation (TXT, DOCX, CSV, JSON, PDF, HTML)
  - `indexer.py` — optional SQLite FTS5 search index
- `tests/` — Pytest test suite (559 tests).
- `pyproject.toml` — Project metadata, dependencies, and console script configuration. Uses setuptools as build backend.
