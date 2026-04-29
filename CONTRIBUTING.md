# Contributing to peekdocs

Thanks for your interest in peekdocs!

## Bug Reports and Feature Requests

The best way to contribute is to open an issue on GitHub:

- **Bug reports:** Include your OS, Python version, what you did, what you expected, and what happened. Run `peekdocs --check` and include the output. If `peekdocs_errors.log` exists, include that too.
- **Feature requests:** Describe the use case — what problem would the feature solve?

Check the [FAQ and Troubleshooting](docs/TROUBLESHOOTING.md) first — your issue may already be covered. Search [existing issues](https://github.com/exbuf/peekdocs/issues) to avoid duplicates.

## Pull Requests

PRs are welcome, but please open an issue first to discuss the change. This avoids duplicate work and ensures the change fits the project's direction.

Before submitting a PR:

1. Run the test suite: `pytest tests/ -v` (all 669+ tests should pass)
2. Keep changes focused — one fix or feature per PR
3. Follow the existing code style (no linters enforced, just be consistent)
4. Add tests for new features in `tests/`

## Development Setup

```bash
git clone https://github.com/exbuf/peekdocs.git
cd peekdocs
python -m venv venv
source venv/bin/activate    # macOS/Linux
pip install -e .
pytest tests/ -v
```

## Project Structure

```
peekdocs/
  cli.py              — CLI entry point and argument parsing
  api.py              — Public Python API (search function)
  scanner.py          — File discovery and text extraction (99 file types)
  reporter.py         — Report generation (TXT, DOCX, CSV, JSON, PDF, HTML)
  indexer.py          — SQLite FTS5 search index
  sensitive_patterns.py — PII scan regex patterns
  expr_parser.py      — Boolean expression parser (AND, OR, NOT, parentheses)
  constants.py        — Shared constants
  gui/                — GUI package (customtkinter), split into mixins:
    _app.py           — Main application class
    _helpers.py       — Free functions (safe file opening, cloud detection)
    _mixin_build.py   — UI construction
    _mixin_search.py  — Search execution and results
    _mixin_tools.py   — PII scan, wizard, help windows
    _mixin_data.py    — Settings, history, bookmarks
tests/                — Pytest test suite (669+ tests)
docs/                 — Documentation (user guide, API, troubleshooting)
```

## Project Model

peekdocs is MIT-licensed and free. Every feature works without paying anything — no artificial limits, no feature gating. The free version is not crippled.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

## Questions?

Open an issue or check the [documentation](docs/).
