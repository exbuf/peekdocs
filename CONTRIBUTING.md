# Contributing to peekdocs

Thanks for your interest in peekdocs — a privacy-first local document search and analysis tool for Windows, macOS, and Linux. There are several ways to help.

## Bug Reports and Feature Requests

The best way to contribute is to open an issue on GitHub:

- **Bug reports:** Include your OS, Python version, what you did, what you expected, and what happened. Run `peekdocs --check` (CLI) or open **Tools → System Check** in the GUI and include the output. If `peekdocs_errors.log` exists, include that too.
- **Feature requests:** Describe the use case — what problem would the feature solve?

Check the [FAQ and Troubleshooting](docs/TROUBLESHOOTING.md) first — your issue may already be covered. Search [existing issues](https://github.com/exbuf/peekdocs/issues) to avoid duplicates.

**Looking for somewhere to start?** Browse the open issues for any tagged `good first issue` or `help wanted`, or pick anything that catches your eye and mention in the issue that you'd like to take it on.

## Pull Requests

PRs are welcome, but please open an issue first to discuss the change. This avoids duplicate work and ensures the change fits the project's direction.

Before submitting a PR:

1. Run the test suite: `pytest tests/ -v` (all 627 tests should pass).
2. For search or scanner changes, also run the integration script against the sample corpus: `cd samples/test-files && bash peekdocs_global_test_unix.sh "test"` (or `peekdocs_global_test_windows.ps1` on Windows). It exercises every search mode and flag combination against 100+ sample files.
3. For GUI changes, launch `peekdocs-gui` and verify the affected workflow visually — the test suite can't catch every layout or interaction issue.
4. Keep changes focused — one fix or feature per PR.
5. Follow the existing code style (no linters enforced, just be consistent with surrounding code).
6. Add tests for new features in `tests/`.

**CI runs automatically.** When you push to your branch or open a PR, GitHub Actions runs the test suite on Linux, macOS, and Windows across Python 3.10–3.14. Watch for the green checks before requesting review.

**Maintainer handles the CHANGELOG.** Don't worry about updating `CHANGELOG.md` in your PR — the maintainer adds entries when merging. Commit messages don't need to follow any particular convention; clear is enough.

**Response times are best-effort.** peekdocs is a solo project — review and merge happen when the maintainer has time. There's no service-level commitment.

## Development Setup

Requires **Python 3.10 or newer**.

```bash
git clone https://github.com/exbuf/peekdocs.git
cd peekdocs
python -m venv venv
source venv/bin/activate              # macOS / Linux
venv\Scripts\activate                 # Windows (PowerShell or CMD)
pip install -e .
pytest tests/ -v
```

**GUI development on macOS or Linux also needs Tkinter** (Windows already has it via the Python installer):

- **Linux (Debian/Ubuntu):** `sudo apt install python3-tk`
- **macOS (Homebrew Python):** `brew install python-tk@3.13` (replace `3.13` with your Python version)
- **macOS (python.org installer):** Tkinter is already included.

After install, verify with `peekdocs --check` and optionally launch the GUI with `peekdocs-gui`.

## Project Structure

```
peekdocs/
  __init__.py        — Package init, re-exports library API
  __main__.py        — Enables `python -m peekdocs`
  api.py             — Public Python API (search, run_suite, run_regex_collection, list_*)
  cli.py             — CLI entry point and argument dispatch
  collection.py      — Saved searches and search suites (.peekdocs_collection.json)
  constants.py       — Shared constants and defaults
  diff.py            — --diff command (compare two JSON snapshots)
  expr_parser.py     — Boolean expression parser (AND, OR, NOT, parentheses)
  indexer.py         — SQLite FTS5 search index
  parser.py          — CLI flag parsing
  range_query.py     — Range filter parsing (amount, date, percent, size, age)
  reporter.py        — Report generation (TXT, DOCX, CSV, JSON, PDF, HTML)
  run_log.py         — Per-run JSONL log (~/.peekdocs_runs.log)
  scanner.py         — File discovery and text extraction (100+ file types)
  suite_index.py     — Cross-folder index of where suites live
  translator.py      — Plain-English translation of commands and regex
  wizard_patterns.py — Search Wizard pattern presets
  gui/               — GUI package (customtkinter), split into mixins:
    _app.py             — Main application class
    _helpers.py         — Free functions (safe file opening, cloud detection)
    _tooltip.py         — Tooltip widget
    _mixin_build.py     — UI construction
    _mixin_search.py    — Search execution and results
    _mixin_tools.py     — Tools menu features, regex search, wizard, help
    _mixin_data.py      — Settings, history, bookmarks, index management
tests/                — Pytest test suite (627 tests)
docs/                 — User Guide, API Reference, FAQ & Troubleshooting
samples/              — Test corpus and integration test scripts
```

## No Paid Tier

peekdocs is MIT-licensed and free. Every feature is included — no paid tier, no feature gating, no upsell.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

## Questions?

Open an issue or check the [documentation](docs/).
