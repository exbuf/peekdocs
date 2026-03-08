# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Claude-DocSearch is a Python CLI tool for searching and retrieving content from documents. Entry point: `docsearch/cli.py` → `main()`.

## Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Install in development mode
pip install -e .

# Run the CLI
docsearch <query>

# Run all tests
pytest tests/ -v

# Run a single test
pytest tests/test_cli.py::test_query -v
```

## Architecture

- `docsearch/` — Main package. `cli.py` contains the argparse-based CLI entry point registered as the `docsearch` console script.
- `tests/` — Pytest test suite.
- `pyproject.toml` — Project metadata, dependencies, and console script configuration. Uses setuptools as build backend.
