# Contributing to docsearch

Thank you for your interest in contributing to docsearch!

## Reporting Bugs

1. Check the [FAQ and Troubleshooting](docs/TROUBLESHOOTING.md) first — your issue may already be covered
2. Search [existing issues](https://github.com/exbuf/docsearch/issues) to avoid duplicates
3. Open a new issue with:
   - What you expected to happen
   - What actually happened
   - Steps to reproduce
   - Your OS (Windows/macOS/Linux) and Python version (`python3 --version`)
   - The contents of `docsearch_errors.log` if it exists
   - The output of `docsearch --check`

## Suggesting Features

Open an issue with the "enhancement" label. Describe:
- What you want to do
- Why the current tool doesn't support it
- How you'd expect it to work

## Submitting Code

1. Fork the repository
2. Create a feature branch: `git checkout -b my-feature`
3. Make your changes
4. Run the tests: `pytest tests/ -v`
5. Ensure all tests pass (currently 550 tests)
6. Commit with a clear message describing what and why
7. Push and open a pull request

### Code Style

- Python 3.10+ with type hints where practical
- Functions and methods have docstrings
- Tests for new features go in `tests/`
- Keep dependencies minimal — prefer stdlib when possible

### Project Structure

```
docsearch/
  cli.py          — CLI entry point and argument parsing
  gui.py          — GUI (customtkinter)
  api.py          — Public Python API (search function)
  scanner.py      — File discovery and text extraction
  reporter.py     — Report generation (TXT, DOCX, CSV, JSON, PDF, suite reports)
  indexer.py      — SQLite FTS5 search index
  collection.py   — Saved searches and suite persistence
  parser.py       — CLI argument parsing and config file handling
  range_query.py  — Range query parsing and evaluation
  expr_parser.py  — Boolean expression parser (AND, OR, NOT, parentheses)
  compliance_templates.py — Industry starter templates for Compliance Wizard
  email_alert.py  — Email notifications for suite auto-runs
  constants.py    — Shared constants
tests/            — Pytest test suite
docs/             — Documentation (user guide, compliance guide, API, troubleshooting)
```

### Running Tests

```bash
source venv/bin/activate
pip install -e .
pytest tests/ -v
```

## Questions?

Open an issue or check the [documentation](docs/).
