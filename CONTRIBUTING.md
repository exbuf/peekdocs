# Contributing to peekdocs

Thanks for your interest in peekdocs — a privacy-first local document search and analysis tool for Windows, macOS, and Linux. There are several ways to help.

## Bug Reports and Feature Requests

The best way to contribute is to open an issue on GitHub:

- **Bug reports:** Include your OS, Python version, what you did, what you expected, and what happened. Run `peekdocs --check` (CLI) or open **Tools → System Check** in the GUI and include the output. If `peekdocs_errors.log` exists, include that too.
- **Feature requests:** Describe the use case — what problem would the feature solve?

Check the [FAQ and Troubleshooting](docs/TROUBLESHOOTING.md) first — your issue may already be covered. Search [existing issues](https://github.com/exbuf/peekdocs/issues) to avoid duplicates.

**Looking for somewhere to start?** Browse the open issues for any tagged `good first issue` or `help wanted`, or pick anything that catches your eye and mention in the issue that you'd like to take it on.

**Translation contributions.** peekdocs ships an experimental partial i18n surface in five languages (English, Español, Français, Deutsch, 日本語). The initial translations were AI-authored — native-speaker corrections are explicitly welcomed. See [CONTRIBUTING_i18n.md](CONTRIBUTING_i18n.md) for what's already translated, how to fix existing translations, and how to add a new language.

## Pull Requests

PRs are welcome, but please open an issue first to discuss the change. This avoids duplicate work and ensures the change fits the project's direction.

Before submitting a PR:

1. Run the test suite: `pytest tests/ -v` (all 630 tests should pass).
2. For search or scanner changes, also run the integration script against the sample corpus: `cd samples/test-files && bash peekdocs_global_test_unix.sh "test"` (or `peekdocs_global_test_windows.ps1` on Windows). It exercises every search mode and flag combination against 100+ sample files.
3. For GUI changes, launch `peekdocs-gui` and verify the affected workflow visually — the test suite can't catch every layout or interaction issue.
4. Keep changes focused — one fix or feature per PR.
5. Follow the existing code style (no linters enforced, just be consistent with surrounding code).
6. Add tests for new features in `tests/`.

**CI runs automatically.** When you push to your branch or open a PR, GitHub Actions runs the test suite on Linux, macOS, and Windows across Python 3.10–3.14. Watch for the green checks before requesting review.

**Maintainer handles the CHANGELOG.** Don't worry about updating `CHANGELOG.md` in your PR — the maintainer adds entries when merging. Commit messages don't need to follow any particular convention; clear is enough.

**Response times are best-effort.** peekdocs is a solo project — review, merge, and bug-fix happen when the maintainer has time. There's no service-level commitment, no fixed triage cadence, and no guarantee that any specific PR or issue will be accepted or fixed. An extended review period or a declined PR is not a quality judgment on the contribution; it most often means the change doesn't fit the project's current direction, or the maintainer hasn't had time to evaluate it in depth yet. If your change is time-sensitive (e.g., a security-class fix) please mark it clearly in the issue or PR title.

**Stale issues may be closed.** Issues without activity for a few months are sometimes closed to keep the open-issues list focused. A closed-stale issue is not a rejection — feel free to reopen if it's still relevant, ideally with a fresh repro or a one-line "still hitting this on vX.Y.Z" update so the maintainer can pick it up from where you are.

**No commercial-support tier or vendor-management artifacts.** peekdocs does not provide paid support, custom builds, NDA-bound consulting, SOC 2 / HIPAA / ISO 27001 attestations, or signed SBOMs. Organizations whose vendor-management process requires those artifacts should evaluate peekdocs against their internal risk-acceptance framework. See [SECURITY.md → Support model and response expectations](docs/SECURITY.md#support-model-and-response-expectations) for the IT-evaluator-facing version of the same boundaries.

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

The peekdocs codebase is organized as follows. The core package lives in `peekdocs/`; the GUI is in `peekdocs/gui/`; tests, docs, and sample files live alongside.

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
tests/                — Pytest test suite (630 tests)
docs/                 — User Guide, API Reference, FAQ & Troubleshooting
samples/              — Test corpus and integration test scripts
```

## No Paid Tier

peekdocs is MIT-licensed and free. Every feature is included — no paid tier, no feature gating, no upsell.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

## Questions?

Open an issue or check the [documentation](docs/).
