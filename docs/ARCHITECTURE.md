# peekdocs Architecture

Contributor-facing map of how peekdocs works internally. If you want to add a file type, change how searches run, extend the GUI, or understand why something is the shape it is — this document is for you. Users looking for how to *use* peekdocs should read [USER_GUIDE.md](USER_GUIDE.md) instead.

## Purpose and scope

peekdocs is a document search platform with three interchangeable user surfaces (CLI, GUI, Python API) that share a single search engine. Everything below traces back to three load-bearing design invariants: **deterministic output**, **local-only operation**, and **observable behavior**. If a change would violate any of those, the change is architecturally wrong regardless of how appealing the feature is.

## System overview

```
┌────────────────────────────────────────────────────────┐
│                    User surfaces                       │
│  ┌─────────┐   ┌─────────┐   ┌────────────────────┐   │
│  │  CLI    │   │  GUI    │   │  Python API        │   │
│  │ cli.py  │   │  gui/   │   │  api.py            │   │
│  └────┬────┘   └────┬────┘   └─────────┬──────────┘   │
│       │             │                  │              │
│       │        (subprocess or          │              │
│       │        in-process CLI          │              │
│       │        invocation)             │              │
│       │             │                  │              │
│       └─────────────┴──────────────────┘              │
└─────────────────────┬──────────────────────────────────┘
                      │  all share the same
                      ▼  engine below
┌────────────────────────────────────────────────────────┐
│                    Search engine                       │
│  ┌────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ parser.py  │  │  scanner.py  │  │  indexer.py   │  │
│  │ (query     │  │  (files,     │  │  (SQLite FTS5 │  │
│  │  parse,    │  │   OCR,       │  │   optional    │  │
│  │  normalize │  │   extract    │  │   index)      │  │
│  └────────────┘  └──────────────┘  └───────────────┘  │
│  ┌────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │expr_parser │  │ range_query  │  │  watcher.py   │  │
│  │ (Boolean   │  │ (metadata    │  │  (long-lived  │  │
│  │  AND/OR)   │  │  ranges)     │  │   folder      │  │
│  │            │  │              │  │   watcher)    │  │
│  └────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────┬──────────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────────┐
│                   Output layer                         │
│  ┌────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ reporter   │  │   diff.py    │  │  run_log.py   │  │
│  │ (TXT/DOCX/ │  │  (snapshot   │  │  (structured  │  │
│  │  CSV/JSON/ │  │   compare)   │  │   audit log)  │  │
│  │  PDF/HTML) │  │              │  │               │  │
│  └────────────┘  └──────────────┘  └───────────────┘  │
└────────────────────────────────────────────────────────┘
```

The engine and output layers know nothing about which surface invoked them. That decoupling is what lets us change GUI behavior without touching search logic, and vice versa.

## Package layout

### Core engine (`peekdocs/`)

| Module | Responsibility |
|--------|---------------|
| `api.py` | Public Python API. External code that embeds peekdocs imports this file. Wraps the engine into `search()`, `run_suite()`, `run_regex_collection()`. |
| `cli.py` | Argparse CLI entry point + all flag dispatch. Called directly by the `peekdocs` console script; invoked as subprocess by the GUI. |
| `scanner.py` | File discovery + text extraction across 100+ file types. Lazy imports keep memory bounded; per-file try/except captures errors without aborting the search. |
| `parser.py` | Query preprocessing: Tesseract check for `-O`, OCR flag handling, fuzzy setup, `-e` expression handoff. |
| `expr_parser.py` | Boolean expression tokenizer + evaluator (AND / OR / NOT / parentheses). Independent of search — just returns a match predicate. |
| `range_query.py` | Metadata range filters (`amount:1000..5000`, `date:2024-01-01..2024-06-30`, `filesize`, `filedate`, etc.). Repeatable via `-R`. |
| `indexer.py` | Optional SQLite FTS5 content-extraction cache. Speeds repeated searches by 10–100×; falls back gracefully if disabled. |
| `watcher.py` | Long-running folder watcher (watchdog library + NDJSON streaming). Fires on file create/modify. |
| `reporter.py` | Report generation for six formats (TXT, DOCX, CSV, JSON, PDF, HTML). TXT is always written; others opt-in via `-o`. Consumer of match data; no search logic. |
| `diff.py` | Snapshot comparison. Buckets deltas into new / removed / changed / modified. When both inputs carry `--hash`, detects "content changed under an unchanged match pattern." |
| `run_log.py` | Structured JSONL audit trail at `~/.peekdocs_runs.log`. Every non-`--no-log` run appends one line. Consumed by `peekdocs --runs`. |
| `notifier.py` | Desktop notification wrapper (macOS `osascript`, Windows toast, Linux `libnotify`). |
| `translator.py` | OCR text preprocessing (Latin-1 normalization, whitespace collapsing). |
| `collection.py` | Search suite + regex collection JSON persistence (`<folder>/.peekdocs_collection.json`, `~/.peekdocs_regex_collections.json`). |
| `suite_index.py` | Global suite discovery cache (`~/.peekdocs_suites_index.json`) — powers `--suite NAME` without a per-folder scan. |
| `i18n.py` | 7-language translation dict + `t()` lookup. Intentionally narrow coverage — see [Historical decisions](#historical-decisions). |
| `regex_examples.py` | Bundled universal-pattern regex collection (email, URL, IPv4, ISO date, semver, JIRA ticket, etc.). |
| `wizard_patterns.py` | Search Wizard's 20 pre-built forms and 35 regex patterns across 6 categories. |
| `constants.py` | `SUPPORTED_TYPES`, `OCR_IMAGE_TYPES`, category groups used across scanner, reporter, GUI. |
| `paths.py` | `resource_path()` helper for locating bundled files (LICENSE, NOTICE, customtkinter assets). Handles the `sys._MEIPASS` case for PyInstaller bundles and the repo-root case for source checkouts. See docstring for the pip/pipx install caveat. |
| `__init__.py` | Package version resolution + public API re-exports. |
| `__main__.py` | `python -m peekdocs` entry point → `cli.main()`. |

### GUI (`peekdocs/gui/`)

| Module | Responsibility |
|--------|---------------|
| `_app.py` | `PeekDocsApp` class inheriting all mixins. Application lifecycle owner: window creation, first-run detection, initial tab selection, settings load/save orchestration. |
| `_mixin_build.py` | UI construction — widget layout, tooltips, checkboxes, buttons, toggle handlers. |
| `_mixin_data.py` | Settings, history, bookmarks, About dialog, index management, `~/.peekdocsrc` I/O. |
| `_mixin_search.py` | Search execution, multi-folder handling, results rendering, cancel/retry logic, `_search_finished` dispatch. |
| `_mixin_tools.py` | Miscellaneous Tools menu features that didn't cluster with a feature domain: System Check, Diff Snapshots, Schedule Search. Formerly ~10K LOC as the "and this feature too" bucket; split across five feature mixins in the mixin-tools-split refactor. Now ~870 LOC. |
| `_mixin_wizard.py` | Search Wizard (the 20-form category-cards popup) and Regex Wizard (the categorized regex-pattern picker with 35 patterns across 6 categories). |
| `_mixin_regex_search.py` | Regex Search feature end-to-end: per-pattern search execution, cancel handler, Regex Tester dialog, and the "?" help panels for both. |
| `_mixin_suites.py` | Search Suites: picker popup, per-search execution loop, combined-report assembly, cancel/elapsed handling, completion popup. |
| `_mixin_file_analysis.py` | Nine folder-scanning tools: File Inventory, Duplicate Finder, Large Files, Empty Files, Recent Changes, File Age Distribution, Protected Files, Unsearchable Files, Collection Summary. Also owns the shared `_format_file_size` helper and Categories-view helpers. |
| `_mixin_help_panels.py` | Eight orphan "?"-help popups that don't belong to a specific feature mixin: search options help, search primer, Advanced Options deep dive, save/load help, matched/excluded files help, index help, three-mode side-by-side compare. |
| `_helpers.py` | Standalone free functions used across mixins — cloud-output guard, CLI runner (subprocess vs in-process), path resolution. |
| `_tooltip.py` | Custom `Tooltip` widget for CTk buttons (customtkinter doesn't ship one). |
| `__init__.py` | `peekdocs-gui` console script entry → instantiate `PeekDocsApp`. |

## Design invariants

These are load-bearing. Every code change must preserve them.

**Deterministic output.** Same input → same output every time. Alphabetical file ordering (by absolute path), fixed line numbering (per format: literal line for text/code, paragraph for Word/PDF, row for Excel — see the *Line vs paragraph* concept in Glossary), versioned JSON schema (`generator` field). Enables `--diff`, reproducible scheduled scans, and CI pipelines that depend on stable exit codes. No sampling, no ranking, no ML inference.

**Local-only.** No network calls anywhere in the runtime path. Docs (`README.md`, `docs/GLOSSARY.md`) explicitly list absent Python networking libraries (`aiohttp`, `requests`, `urllib3`, `httpx`, `pycurl`, `ftplib`) so a reviewer can `grep`-verify. There is no telemetry, no phone-home, no update check.

**Observable behavior.** peekdocs tells you why anything didn't work. `peekdocs_errors.log` lists skipped files with reasons; `--dry-run` reports scope before search; `--check` diagnoses the environment; the progress bar exposes phase markers; per-file try/except captures errors without silent skipping. The principle is stated in the README and enforced by convention across the codebase.

**Cross-interface consistency.** CLI, GUI, and Python API produce identical results for the same inputs. GUI invokes CLI as subprocess (or in-process for standalone PyInstaller bundles). Changing search behavior only requires changing one place — usually `scanner.py` or `api.py`. UI changes never fork search logic.

**Single config file.** `~/.peekdocsrc` is the only config surface. No system-wide config; no per-project config. Simplicity buys us predictable behavior and simple onboarding.

## Data flow: a search request

1. **Invocation.** `peekdocs "budget" -r` (CLI), or Run Standard Search click (GUI), or `api.search(...)` (Python).
2. **Argument parsing.** `cli.py` normalizes argv → options dict; `api.search()` accepts kwargs directly.
3. **Query preprocessing** (`parser.py`) — Tesseract check for `-O`, `-e` expression handoff, mode-conflict validation.
4. **Filter setup** — `expr_parser.py` if `-e`; `range_query.py` if `-R`.
5. **File discovery** (`scanner.py`) — walk folder, filter by `-t`, apply cloud-output guard, honor `--max-file-size`.
6. **Index check** (`indexer.py`) — if index exists and is current, take fast path.
7. **Per-file extraction** (`scanner.py`) — OCR, PDF, Word, archive traversal (recursive but bounded).
8. **Per-line matching** — regex / fuzzy / wildcard / exact / expression, per the mode selected.
9. **Report generation** (`reporter.py`) — always TXT; DOCX / CSV / JSON / PDF / HTML if opted in via `-o`.
10. **Notification** — desktop notification if opted in (`notifier.py`); `--on-match` hook if configured.
11. **Structured log** — one JSONL line to `~/.peekdocs_runs.log` (unless `--no-log`).
12. **Exit code** — 0 (matches), 1 (none), 2 (error). GUI translates to status text.

## Extension points

**Adding a file type.**
1. Add extension to `constants.SUPPORTED_TYPES` (or `OCR_IMAGE_TYPES` if OCR is required).
2. Add extraction branch in `scanner._extract_lines`: `elif ext == '.newtype': ...`.
3. Update `README.md` supported-types table and the "100+ file types" claim if the count changes.
4. Add smoke test coverage in `tests/`.

**Adding an output format.**
1. Add branch in `reporter.write_report` following existing format patterns.
2. Update `cli.py` `-o` handler validation and `--open` dispatch.
3. Update `_mixin_build.py` Advanced Search Options output-format checkboxes.
4. Update `USER_GUIDE.md` output-formats section.

**Adding a search mode.**
1. Add flag in `cli.py` argparse.
2. Add branch in `scanner` search loop OR in `api.search()` dispatch.
3. Add checkbox in `_mixin_build.py`; wire up toggle handler if it conflicts with other modes.
4. Update Complete CLI Reference table and README's three-mode primer if it becomes a top-level mode.

**Adding a translatable string.**
1. Add key to `i18n.TRANSLATIONS`.
2. Wrap consumer with `t("key")`.
3. Contribute translations for all 7 target languages, or accept English fallback.

## Historical decisions

**GUI mixin architecture.** Chosen to keep composition simple without introducing dependency-injection framework overhead. The original four mixins grouped by lifecycle stage (`_build`, `_data`, `_search`, `_tools`) rather than by feature; `_mixin_tools.py` grew to 10K LOC as the "and this feature too" bucket. Split across five feature mixins (`_mixin_wizard`, `_mixin_regex_search`, `_mixin_suites`, `_mixin_file_analysis`, `_mixin_help_panels`) in the mixin-tools-split refactor, reducing the bucket file to ~870 LOC. `PeekDocsApp` inherits from all nine mixins; the pattern still routes everything through `self` so cross-mixin calls resolve via MRO without needing signature changes.

**PyInstaller `--onefile` vs `--onedir`.** macOS CLI uses `--onedir` to skip the 5–7 s per-invocation self-extraction cost that stacks with Gatekeeper checks on unsigned binaries. Windows / Linux CLI use `--onefile` because the extraction cost is smaller (~2 s on Windows, ~0.5 s on Linux) and a single .exe / binary is the conventional CLI shape on those platforms. Windows GUI is `--onefile`; macOS GUI is `--onedir` inside the `.app` bundle.

**GUI-to-CLI subprocess (not direct `api.search()`).** The GUI runs `cli.main()` via `subprocess.Popen` (or via `runpy.run_module` in-process for PyInstaller bundles) rather than importing `api.search()` directly. Keeps a strict boundary; means the CLI is the single source of truth for search behavior. Cost: subprocess serialization overhead and output-parsing complexity. A structured "search request → search result" layer between GUI and CLI would be cleaner but hasn't been necessary yet.

**No plugin architecture.** File type support and output formats are compiled into `scanner.py` and `reporter.py`. Adding a plugin registry would allow community extensions but adds surface area (plugin API versioning, load-time discovery, security concerns for third-party code). Deferred until user demand justifies the cost.

**No unified async model.** Search is synchronous; watcher is event-driven (watchdog); GUI runs searches in threaded subprocess. Not unified. Current scale doesn't require asyncio; growth may push toward it eventually.

**i18n narrow coverage.** Translation covers ~10 strings (four Step badges, three action buttons + tooltips, adjacent bottom-row labels). Everything else is English. Intentional scope — full-UI translation is a maintenance burden without volunteer translators for each release. Signals "we thought about internationalization" without committing to a moving target.

**`~/.peekdocsrc` as sole config source.** No system-wide config, no per-project config. Simplifies fleet-deployment scenarios (push one file); prevents "which config wins?" bug reports.

**PEP 639 for license bundling.** Uses `license-files = [...]` in `pyproject.toml` so pipx installs carry LICENSE / NOTICE / THIRD_PARTY_NOTICES.md in the wheel's `.dist-info/` directory. Standalone PyInstaller binaries bundle the same three files via `--add-data` in `build_app.py`. License travels with the code on both distribution paths.

## Testing strategy

Tests live in `tests/`, run with `pytest`. ~15 test files, ~8K LOC.

- **Core engine.** Strong unit coverage. `test_api.py`, `test_cli.py`, `test_expr_parser.py`, `test_range_query.py`, `test_translator.py`.
- **GUI.** Integration + smoke coverage. `test_gui.py`, `test_headless.py` (verifies CLI import path works without Tk).
- **Feature-specific.** `test_watcher.py`, `test_wizard.py`, `test_suites.py`, `test_collection.py`, `test_suite_index.py`, `test_cloud_guard.py`, `test_exclusion.py`.
- **Standalone binary.** `test_smoke_cli.py` runs against the built `.exe` on Windows CI. Catches PyInstaller-specific regressions the in-process tests would miss.

Philosophy: unit test the search engine (deterministic, high-value); integration test the interfaces; smoke test the binaries. GUI has less unit coverage than the core — the mixin architecture makes isolated testing awkward without instantiating `PeekDocsApp`.

## Known weaknesses (contribution opportunities)

These are documented candidly here so anyone reading the code understands the shape and the reasons.

- **Mixin architecture may be over-abstracted.** Explicit composition (helper classes + method calls) might read more directly than mixins at this codebase scale. The mixin-tools-split refactor removed the "10K-LOC bucket file" symptom but kept the mixin pattern itself. Full conversion to explicit composition would touch every file in `gui/`.
- **No formal error taxonomy.** Users see raw `pytesseract`, PDF library, archive-extraction errors in the error log. A `PeekDocsError` hierarchy would improve error-log signal and let callers branch on error type.
- **State management in GUI is manual sync.** Tkinter `StringVar`s scattered across mixins; toggle-handler methods coordinate changes. Grows fragile with feature count.
- **No plugin architecture** (see Historical decisions).
- **No async model unification** (see Historical decisions).

The strengths cluster around *the search product itself* — correctness, cross-platform consistency, deterministic output. The weaknesses cluster around *code shape* — organic growth into large mixins, no plugin system. Fixable one at a time as long as growth stays manageable.
