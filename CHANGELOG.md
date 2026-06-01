# Changelog

All notable changes to peekdocs are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Versions are listed in reverse chronological order (newest first). Each release groups its changes under **Added** (new features), **Changed** (modifications to existing behavior), **Removed** (features taken out), and **Fixed** (bug fixes).

**To upgrade to the latest version:**

- **pipx** (recommended, Mac / Linux / Windows): `pipx install --force git+https://github.com/exbuf/peekdocs.git`
- **pip** (advanced): `pip install --upgrade git+https://github.com/exbuf/peekdocs.git`
- **Standalone download**: grab the new file from the [Releases page](https://github.com/exbuf/peekdocs/releases/latest) and replace your existing copy. Your settings and saved searches live in your home directory, not in the executable — nothing is lost on upgrade.

## [Unreleased]

Documentation right-sizing pass plus a round of GUI polish and
safety hardening for destructive actions.

Documentation: README trimmed from ~1,240 lines to ~920 (-26%) by
moving deep-reference material into /docs companion files, while
keeping every selling point inline. Added a privacy-first
justification callout, a typical-workflow GUI-path clarifier, and
honest fixes to a few claims that had drifted out of sync with the
source.

GUI: layout fixes (Advanced Search Options auto-fits to content,
Schedule Search popup slightly taller, Error Log viewer gains a
Clear Log button, white bar around System Check Copy to Clipboard
removed, About dialog aligned with workbench framing), and safety
hardening on the four destructive actions (Clean Folder, Delete
Now, Delete Index, Restore Factory Settings) — each now spells out
scope, says "this cannot be undone", and reports failures rather
than swallowing them silently.

### Added

- **`docs/GLOSSARY.md`** — 70 peekdocs terms (FTS5, regex modes,
  deterministic, exit codes, Tesseract, jq, SIEM, MSP technician,
  and more — including a list of Python networking libraries
  peekdocs deliberately does *not* use). Migrated from the README's
  inline Glossary section.

- **`docs/SECURITY.md`** — IT/Security deep dive: data architecture
  tables with per-file sensitivity notes (per-folder files, home
  directory, in-memory-only data) and documented limitations
  outside the application's control (CLI process arguments, swap
  space, force-kill behavior, backup software, etc.). Migrated
  from the README's "For IT and Security Teams" section, whose
  at-a-glance Q&A table stays in the README.

- **`docs/INSTALLATION.md`** — per-platform Python prerequisites
  (macOS / Windows / Linux deep prose), optional tool installation
  (Tesseract, UnRAR, libpff-python), less-common install paths
  (macOS Python version selection for pipx, no-git ZIP install,
  Windows pipx fallback), and CLI-on-Windows footnotes. Migrated
  from the README's Installation section, whose quick-path code
  blocks (Standalone, Option B pipx, Upgrading) stay inline.

- **"Local-only by design" README callout** — concentrates the
  privacy assertions (no network, no telemetry, no cloud, no
  account, no admin required, works air-gapped) in one prominent
  block at the top, paired with the existing "Transparency over
  magic" callout. Replaces the scattered privacy claims that the
  FAQ migration left dilute.

- **"Why local?" README callout** — short paragraph between the
  Local-only and Transparency-over-magic callouts that justifies
  the design choice (some documents you don't want to hand over)
  and acknowledges the tradeoff (peekdocs doesn't summarize, infer
  meaning, or do anything cloud AI tools do well). The three
  callouts now form a coherent trio: the *what*, the *why*, and
  the *honesty principle*.

- **Typical-workflow GUI-path clarifier (README)** — one-line italic
  note under the workflow sentence naming where each step lives in
  the GUI (first four on the main screen, suites under the green
  Run Search Suites button, schedules under Tools → Schedule Search
  generating a cron / Task Scheduler command you paste yourself).
  Eliminates the friction of a first-time user looking for a
  "Manage Suites" or "Schedule" button that doesn't exist.

- **README Documentation table now catalogs all `/docs` files** —
  added INSTALLATION, GLOSSARY, and SECURITY entries so the central
  catalog matches what's actually in `/docs`.

### Changed

- **FAQ section migrated from README to `docs/TROUBLESHOOTING.md`**
  — 10 unique-value entries (privacy/data-sending, admin
  permissions, Microsoft Word not needed, network drives, search
  entire computer, PDF Latin-1 caveat, full uninstall, Gmail /
  Outlook export, dependencies audit, default search folder)
  migrated; the rest of the 25-entry FAQ section was either
  duplicated elsewhere or moved to the IT/Security deep dive.
  README replaced with an 8-line "Questions and troubleshooting"
  pointer block. -113 README lines.

- **Platform Notes per-platform prose moved to USER_GUIDE.md.** The
  File Handling cross-platform table — a real sell ("peekdocs
  handles every weird OS edge case automatically") — stays in the
  README. The "Details by platform" prose explaining the *why*
  behind each table row moved to USER_GUIDE's Platform Notes
  section as a new "File-handling details by platform" sub-section.

- **Features section tightened.** Dropped the "For Developers"
  sub-section entirely (every bullet duplicated content in Feature
  Highlights, Why peekdocs?, or the new Local-only callout).
  Tightened five long bullets (Results preview, HTML export, Delete
  on Close, Safe defaults, Excluded Files view, Collection Summary,
  Unsearchable Files) by cutting step-by-step GUI button paths that
  belong in the User Guide and keeping the *what* and *why*.

- **README Feature Highlights intro paragraph tightened** to drop
  the file-type list that was already in the lede sentence above
  it. The four pillars (search, characterize, report, drive via any
  interface) carry the workbench framing without restating the file
  mix.

- **USER_GUIDE Glossary cross-references `docs/GLOSSARY.md`.** The
  two glossaries overlap on common terms but each is curated for a
  different scope — USER_GUIDE's covers operational/in-tool terms
  (flags, error names, packaging quirks); `docs/GLOSSARY.md` covers
  broader vocabulary including industry context and the
  networking-libraries-not-used list. A short paragraph at the top
  of the USER_GUIDE Glossary names both scopes.

- **`.gitignore` covers current peekdocs output filename patterns**
  — added `peekdocs_standard_results.*`, `peekdocs_regex_results.*`,
  `peekdocs_snapshot_*`, and `peekdocs_diff_*`. The old
  `peekdocs_results.*` pattern is retained for backwards
  compatibility with any reports left over from older versions.

### Fixed

- **Search Wizard count corrected throughout the README** —
  previously claimed "35 pre-built search types" in four places.
  The source has two separate counts: 20 search-type forms in the
  main wizard (`peekdocs/gui/_mixin_tools.py` `patterns` list) and
  35 regex patterns across 6 categories in the separate regex
  pattern builder (`peekdocs/wizard_patterns.py`). The 35 figure
  belonged to the regex builder, not the search types. All four
  README mentions now describe both pieces honestly. Also fixed
  "6 profession-themed tabs" — five are profession-themed; one
  (Common / General) isn't.

- **USER_GUIDE button-color descriptions corrected.** The Search
  Bar table row called the Standard Search button "green" and the
  Regex Search button "purple". Actual colors from
  `peekdocs/gui/_mixin_build.py`: Standard `#2196F3` (Material
  blue), Suites `#76BA1B` (green), Regex `#FF9800` (orange).

- **Stale README anchor refs in `/docs` updated to current
  install-option labels.** Five references in USER_GUIDE.md and
  TROUBLESHOOTING.md pointed at install-option anchors that had
  been renamed in earlier sessions (e.g., `option-b-manual-install-with-git`,
  `option-c-manual-install-no-git-no-sign-up`); fixed to point at
  current anchors or at `CONTRIBUTING.md#development-setup` /
  `docs/INSTALLATION.md` as appropriate.

- **Stale Diff Snapshots disclaimer removed.** The migrated FAQ
  contained a stale claim that peekdocs lacked a built-in diff or
  comparison feature; Diff Snapshots has shipped and is documented.
  Dropped during the FAQ migration rather than carrying the
  outdated statement forward.

- **Advanced Search Options window auto-fits to content.** The popup
  had a fixed 900x760 geometry while its content only filled ~560px,
  leaving ~200px of empty space between Reset All Fields and the
  bottom action row (because `advanced_frame` was packed with
  `expand=True`). Now sums the children's requested heights directly
  at the end of `_build_advanced_panel` and resizes the window to
  that plus 8px of breathing room. Robust against future content
  additions and font / DPI variations.

- **Schedule Search popup geometry bumped from 680x650 to 680x720.**
  The previous height crowded the step-by-step instruction text
  against the Close button.

- **Error Log viewer now has a Clear Log button.** Previously the
  only way to clear the error log from the GUI was Tools -> Clear
  Files -> check the `peekdocs_errors.log` row. The viewer popup
  now has a red Clear Log button (left-anchored, one row above
  Close) wired to the existing `_clear_error_log()` method. The
  viewer auto-closes after a successful deletion since its content
  is then stale.

- **White bar around System Check Copy to Clipboard button removed.**
  The button sat inside a `tk.Frame` with explicit `bg="white"` packed
  with `fill="x"`, rendering as a visible full-width bar across the
  popup. Replaced with packing the button directly on the popup with
  `anchor="w"` — same visual position, no white bar, dark theme still
  handled by CTk button styling.

- **About dialog tagline aligned with workbench framing.** Was still
  calling peekdocs a "platform"; updated to "workbench" to match the
  README rebrand.

### Hardened (destructive actions)

- **Clean Folder.** Highest-risk destructive Tools entry (operates on
  any folder the user picks, not just the current Search Folder).
  Refactored to:
  - Two-stage confirm. Auto-generated files (results, index, error
    log) prompted first; user-saved reports (`peekdocs_report_*` /
    `peekdocs_accumulated_*`) prompted separately with `default=NO`.
    Skipping either stage doesn't delete its files.
  - "This cannot be undone." in both dialogs.
  - IMPORTANT clause in both dialogs naming the exact prefixes so
    users with manually-named files matching them know they'll be
    caught by the pattern match.
  - Deletion failures surfaced (up to 5 filenames + reasons) in a
    warning dialog and an orange `Cleaned N; M failed.` status bar.
    Previously `except OSError: pass` swallowed them silently.

- **Delete Now (main-screen button).** Color changed from teal
  `#0D9488` to red `#CC3333` to match other destructive actions
  (Reset All Fields, Restore Factory Settings). The confirm dialog
  now computes the folder set BEFORE prompting and lists every
  folder where peekdocs has files — previously the multi-folder
  scope (every folder searched this session + current Search
  Folder + `~/peekdocs_reports` + folders saved in config) was
  hidden. Added "This cannot be undone." Tracks deletion failures
  and surfaces them like Clean Folder does.

- **Delete Index (Tools -> Indexes).** Previously had no confirmation
  at all — single click destroyed the index. Now confirms with an
  honest description of the rebuild cost ("seconds for small folders,
  minutes for large or PDF-heavy ones; searches stay correct
  regardless") and "you can rebuild later." `default=NO`.

- **Restore Factory Settings (Advanced Search Options).** Confirm
  dialog now enumerates the nine setting categories about to be
  reset (search mode, regex/fuzzy/wildcard/OCR flags, file types,
  output formats, max matches and file size, CPU cores, proximity
  and context lines, recent searches and last folder, appearance)
  instead of just saying "settings reset to factory defaults."
  Added "This cannot be undone." `default=NO`.

## [1.0.4] — 2026-05-30

Polish release focused on first-run experience and onboarding clarity:
new System Check tool, a conditional CLI banner notice that explains
the first-index-build delay, an expanded sample corpus, persistence
fixes for the main-screen search-option toggles, and a sweeping
documentation pass across README, USER_GUIDE, TROUBLESHOOTING,
CONTRIBUTING, and API_REFERENCE.

### Added

- **Tools → System Check** — GUI equivalent of `peekdocs --check`. Opens a color-coded popup showing Python version, required and optional dependency status, Tesseract availability, SQLite version, and free disk space. Includes a Copy to Clipboard button for pasting the diagnostic into GitHub issues. Both the CLI and GUI now share a single `run_system_check()` function under the hood, so output stays consistent.

- **Conditional first-run index banner notice (CLI).** When running a search in a folder that doesn't yet have a `.peekdocs.db` index, the banner prints a one-time note: "no search index for this folder yet — the first search builds one (may take longer); subsequent searches are much faster." The check is folder-aware (parses `-d`/`--directory` from argv, defaulting to cwd) and respects the `-qq` / `-q` / `--stdout` quiet contracts so it never leaks into piped output. Eliminates the "is it stuck?" reaction when an initial scan of a large corpus takes 30–60 seconds while subsequent searches finish in under a second.

- **`engineering_test` sample corpus** — 35 source-code and engineering file types (`sample.asm`, `sample.cpp`, `sample.f90`, `sample.dxf`, `sample.sv`, `sample.vhdl`, etc.) added under `samples/engineering_test/`. Pairs with the existing `test-files/` corpus for integration testing and gives users a concrete starting point for searching their own engineering source trees.

### Changed

- **Renamed GUI button "Delete Everything Now" → "Delete Now".** The previous name implied it deleted everything peekdocs-related (saved searches, settings, bookmarks, documents); in fact it only deletes recent result files and the search index, plus clears UI state. The new name pairs naturally with the adjacent **Delete on Close** checkbox and doesn't overpromise. Tooltip and confirmation dialog still explain the exact scope.

- **Renamed GUI bottom-row button "Hover" → "Tooltips"** — clearer label for the toggle that enables or disables tooltip popups across the app.

- **Tools menu jargon scrub** — three Tools menu entries rephrased for home users so they don't read like internal dev tooling.

- **CI workflow actions bumped to current majors** — `actions/checkout@v4 → v6` and `actions/setup-python@v5 → v6`. Clears the Node 20 deprecation warning ahead of the June 2026 cutoff when GitHub forces all actions to Node 24 by default.

### Fixed

- **Main-screen search-option toggles weren't persisting across launches.** Whole Word, Recursive, AND/OR mode, and Use Index all updated their in-memory StringVars when clicked but never wrote to `~/.peekdocsrc` — the settings file was only written when the user explicitly invoked "Save Settings as Default." Each toggle now writes its single key via the existing `_save_ui_preference()` primitive (narrow blast radius, no transient session state dragged along). Use Index continues to auto-check when the folder has a `.peekdocs.db` — that's intentional smart-default behavior and was preserved across this fix.

- **Step 3 label alignment on the main page.** The Step 3 cell's content is the 44px-tall Run button, much taller than the Step 1 / Step 2 rows. The label was using `sticky="w"`, which vertically centers in the cell — visually dropping it below the other Step labels. Switched to `sticky="nw"` with a small top pad so it tracks the top of the cell instead.

- **Diff-snapshot demo JSON files contained a sensitive-sounding filename string.** `staff_training_hipaa.txt` was visible inside the downloadable `peekdocs-snapshot-todo-before.json` and `peekdocs-snapshot-todo-after.json` demos. Renamed to `staff_training_policy.txt` to match the corresponding test-corpus rename. Snapshots still parse cleanly and the diff demo still works.

### Docs

- **README** — major onboarding pass: opening lines (positioning sentence, format list, plainer naming for GUI/CLI), Quick Start gap-close, Feature Highlights reordering, "with surrounding context" and "Scriptable" bullets surfaced, three TOC entries added (Feature Highlights, Testing, Disclaimer), Disclaimer paragraph tightened into a single cohesive sentence, "Who Is It For" connector softened, four unbolded bullets fixed, Performance section gained a "First-run timing and the banner notice" subsection with a conditional-behavior table, suite-result and TODO screenshots refreshed with current numbers and matching captions.

- **USER_GUIDE** — TOC expanded from ~45 to ~104 lines with comprehensive subsection coverage; one-line intros added to Output and Project Structure sections; 11 glossary entries added plus a "CI pipeline" entry; three range-query bullets bolded; Search Suites help points at the CLI docs; opening line includes a brief category statement and install pointer.

- **TROUBLESHOOTING** — opening surfaces a new "Where to Start" navigation section; FAQ entry added: "Why is my first search slow but later searches are fast?" covering `--no-index` and `2>/dev/null` guidance; 10 glossary entries added plus 4 covering TROUBLESHOOTING-specific jargon.

- **CONTRIBUTING** — 8 onboarding gaps closed; opening gains category statement and section preview; "Project Model" section renamed to "No Paid Tier" for clarity; Project Structure section gets an intro line.

- **API_REFERENCE** — opening gains category statement; one-line intros added to Basic Usage and With Options sections; sensitive-data reference replaced with neutral language; 4 onboarding gaps closed.

- **Getting Started tab** — added a Tip about tooltips and the `?` help buttons; the Quick Start GUI section now mentions the Getting Started tab so users know it's there.

- **Help windows** — "What is this?" intros added to Advanced Search Options and Indexes help popups.

- **CLI** — `--clear-all` output gained a trailing blank line for readability; `-h` help text documents cleanup scope explicitly; `--check` Prerequisites list adds `libpff-python` for parity with Tesseract and `unrar`.

## [1.0.3] — 2026-05-26

Point release fixing the standalone Windows GUI spawning **multiple**
duplicate windows when the user runs a search with the Index
checkbox unchecked.

### Fixed

- **Multiple duplicate GUI windows when searching without the
  index.** Reported on Windows v1.0.2 standalone after 10
  successful index-backed searches: unchecking "Index" and
  running another search opened many peekdocs windows at once,
  scaling with the CPU count.

  Root cause: when the index is bypassed, the search engine
  parallelizes file scanning with ``multiprocessing.Pool`` across
  cores. On Windows, ``multiprocessing`` uses the ``spawn`` start
  method (the only option), which creates each worker process by
  re-launching ``sys.executable``. In a PyInstaller-bundled exe,
  ``sys.executable`` IS the GUI exe — each worker re-launches
  the GUI. With four cores, you got four extra peekdocs windows;
  with sixteen, sixteen.

  Fix: call ``multiprocessing.freeze_support()`` at the very top
  of both entry points (``peekdocs/gui/__init__.py`` and the
  ``__main__`` guard of ``peekdocs/cli.py``). This is the
  canonical PyInstaller + multiprocessing workaround: when a
  spawned worker process starts and recognizes (via a special
  argv that multiprocessing sets) that it is a frozen child, it
  short-circuits and behaves as a worker only, never re-executing
  the entry point's main code. No more duplicate GUI windows
  during multiprocessing-parallelized searches.

  freeze_support() is a no-op on a normal pip / pipx install
  (sys.frozen is False) — so the existing subprocess and
  threading paths are unaffected.

## [1.0.2] — 2026-05-26

Point release fixing two more sites that bypassed the v1.0.1
in-process helper and still spawned a duplicate GUI window in
PyInstaller-bundled standalone exes, and a cosmetic but
user-visible version-display bug in the standalone GUI title.

### Fixed

- **Standalone GUI spawned a duplicate window at the end of a
  search.** v1.0.1 fixed the main search subprocess but missed
  two related call sites that still used the bare
  ``subprocess.Popen([sys.executable, "-m", "peekdocs", ...])``
  pattern: the post-search ``-s save_name`` save step (fires
  when the user fills in the "Save as" field) and the
  ``--index-clear`` step in the Manage Indexes tool. In the
  standalone exe both re-launched the GUI as a subprocess,
  popping up a duplicate window. User noticed the save case
  because it fires at the end of every named search.

  Fix: both sites now go through
  ``peekdocs.gui._helpers._run_peekdocs_cli``, the same helper
  added in v1.0.1 that picks subprocess vs in-process based on
  ``sys.frozen``. No more duplicate window in the standalone
  build's save and index-clear paths.

- The remaining ``sys.executable`` reference in the GUI is the
  Schedule Search dialog (Tools → Schedule Search), which
  generates a cron / Task Scheduler command STRING for the user
  to copy-paste into their scheduler. That string would still
  point at the standalone exe in a PyInstaller bundle, but it
  is never executed by the GUI itself — and a user running both
  the standalone exe AND Schedule Search is an unusual combo. To
  be addressed in a future release if it surfaces in practice.

- **Standalone GUI title bar showed "peekdocs" with no version.**
  The title is built from ``importlib.metadata.version("peekdocs")``,
  which reads installed-package metadata. PyInstaller doesn't
  copy that metadata into the bundle by default, so the lookup
  failed silently and the title fell through to an empty version
  string. Also, ``peekdocs/__init__.py``'s ``__version__`` was
  pinned at a stale "1.0.0".

  Fix:

  * ``peekdocs/__init__.py`` now resolves ``__version__`` from
    installed metadata first and falls back to a hardcoded value
    that stays in sync with pyproject.toml on every bump.
  * GUI title (``peekdocs/gui/_app.py``) now imports from
    ``peekdocs.__version__`` rather than calling pkg_version
    directly, so it picks up the fallback.
  * ``build_app.py`` adds ``--copy-metadata peekdocs`` to both
    the GUI and CLI PyInstaller invocations as defence in depth,
    so future bundles will have the .dist-info available too.

## [1.0.1] — 2026-05-26

Point release fixing one bug introduced by the v1.0.0 standalone
Windows / macOS executables shipping for the first time.

### Fixed

- **Standalone GUI exe couldn't actually run a search.** Clicking
  Run Standard Search (or any Run button) on the bundled GUI
  opened a *second* peekdocs GUI window and returned zero matches.
  Root cause: the GUI invokes searches via
  ``subprocess.Popen([sys.executable, "-m", "peekdocs", ...])``,
  which works in a normal pip / pipx install because
  ``sys.executable`` is ``python``. In a PyInstaller-bundled exe,
  ``sys.executable`` is the GUI exe itself — re-launching it
  ignores the ``-m peekdocs`` argv and just opens another GUI
  window. Bug was invisible in a Mac dev environment because the
  pip-installed peekdocs that runs there is not a frozen exe.

  Fix: new helper ``peekdocs.gui._helpers._run_peekdocs_cli`` that
  detects ``sys.frozen`` and runs the search in-process (calling
  ``peekdocs.cli.main()`` directly with stdout/stderr redirected
  to string buffers) instead of spawning a subprocess. Three call
  sites refactored to use it: the main standard search, the
  multi-folder search loop, and the suite runner.

  Trade-off in frozen mode: the Cancel button can't actually
  terminate an in-flight search (no PID to kill). The button is
  still present and resets the GUI state visually, but the search
  runs to completion regardless. Acceptable for v1.0.1; a
  cooperative-cancellation hook can come later.

  Normal pip / pipx installs are unaffected — they still use
  subprocess and Cancel still works.

## [1.0.0] — 2026-05-25

First 1.0 release. Brings a major new feature (Regex Search), removes PII Scan to eliminate legal liability, adds Schedule Search, builds out the automation/IT-use CLI surface (`--diff`, `--hash`, `--on-match`, `--dry-run`, run log), expands the Python API, polishes the main-screen UI (color-coded Run buttons, hyperlink-styled Advanced/Wizard, tinted options row), and rewrites large portions of the README and User Guide. Not yet published to PyPI.

### Added

- **Regex Search** — new purple GUI button next to Standard Search. Run up to 10 named regex patterns per collection, each executed separately with per-pattern results, View Files / View Text buttons, and a Cancel button (turns red mid-run). Create unlimited named collections via Save Collection As / Restore From Collection — keep separate profiles for different tasks (code patterns, log analysis, invoice extraction). Clear All erases all patterns; Restore All undoes the last clear. Help screen includes 50 common regex patterns to copy and paste, custom-pattern guidance (regex101, web search, AI), and Performance/Index notes. Always scans files directly (index bypassed) for fresh results
- **Regex Search screen-only mode** — "Do not save regex match contents to reports" checkbox displays results in a screen-only popup that is never written to disk, piped, or returned via API. Inherited from the removed PII Scan design for sensitive-data workflows
- **`--regex-collection NAME` CLI flag** — run a saved regex collection from the command line with per-pattern progress. Supports `-r`, `-d DIR`, `--stdout` for JSON output, and `--timestamp` for unique report filenames. `--regex-collection --list` lists all saved collections
- **`--timestamp` for `--suite` and `--regex-collection`** — both batch CLI paths now honor `--timestamp` and produce uniquely named reports (`peekdocs_suite_results_YYYYMMDD_HHMMSS.{txt,docx}` and `peekdocs_regex_results_YYYYMMDD_HHMMSS.{txt,docx}`). Required for IT automation that loops over multiple suites or collections without overwriting reports
- **Schedule Search dialog** (Tools menu) — generates a ready-to-paste cron (Mac/Linux) or schtasks (Windows) command for any saved search suite or regex collection. Step-by-step instructions, frequency picker (daily/weekly/monthly), time selector, optional `--timestamp` and `--stdout`, Copy to Clipboard button. No terminal experience required
- **Clean Folder** (Tools menu) — browse to any folder and selectively delete peekdocs-created files. Includes a review-before-delete confirmation dialog
- **`run_suite()` and `run_regex_collection()` Python API** — run a saved suite or regex collection programmatically and get a `SuiteResult` / `RegexCollectionResult` with per-search/per-pattern matches, files searched, elapsed time, and skipped entries. Added `list_suites(directory)` and `list_regex_collections()` for enumeration
- **Search Wizard screenshot** in README, with 21 pre-built search patterns documented
- **Multiple new README screenshots** — Search Suites, Advanced Search Options, heart search (main/HTML/docx), highlighted Word report, HTML report
- **`Who Is It For?` README restructure** — audience profiles (developers, researchers, technical writers, investigators, archivists, IT, consultants, business power users, engineers, AI/ML, data researchers, programmers, home users, email archives) with outcome-oriented value statements
- **`Why Not Just Use Grep?` README section** — credit to grep, side-by-side capability table covering 20+ features, honest summary on when each tool is appropriate
- **FAQ entries** — email export, post-search workflow, sharing reports, default folders, search comparison
- **README intro sentence** describing CLI, GUI, and Python API interfaces and the type-and-click workflow
- **CLI exit codes documented** in README, plus zero-match report behavior and non-recursive search hints
- **Tooltips** with section titles ("Main Search Bar:", "Search Folder Bar:", "Results Preview:") on Search Suites buttons, Delete Everything Now, Clear Preview, and many others
- **Tagline reworked** — "Easy to Use", "Free and Open-Source (MIT License)", "yellow-highlighted reports" added; project tagline now synchronized across README, pyproject.toml, CLI banner, GUI, and CLAUDE.md
- **`--diff OLD NEW` CLI command** — compare two peekdocs JSON snapshots (from `--stdout` or `-o json`) and report what changed across NEW / REMOVED / CHANGED / MODIFIED files. Default human-readable output; `--json` for a structured payload. Diff-flavored exit codes (0 = nothing changed, 1 = actionable findings detected, 2 = error). Works with standard, inverse, and regex-collection JSON shapes
- **`--hash` flag** — adds SHA-256 of each matched file's raw bytes to `matches_per_file` / `inverse_files` JSON entries for chain-of-custody and content-integrity workflows. Hashed once per file regardless of match count. Field is omitted when the flag is off
- **`--on-match HOOK` flag** — runs an arbitrary command on exit 0 (matches found) with env vars `PEEKDOCS_MATCH_COUNT`, `PEEKDOCS_REPORT_TXT`, `PEEKDOCS_REPORT_DOCX`, etc. Skipped on exit 1 / exit 2 / `--dry-run` / informational commands. 30 s timeout; hook stdout/stderr captured to `peekdocs_errors.log`; broken hook never overrides the search's exit code
- **`--dry-run` flag** — preflight that validates flags and resolves suites/collections without scanning anything. Returns 0 if the scope is valid, 2 if not. Explicit error when combined with `--suite` / `--regex-collection` (the user expectation was that dry-run applies, not that the real run silently fires)
- **Per-run structured log (`~/.peekdocs_runs.log`)** — every CLI invocation appends a JSON Lines record with timestamp, args, exit code, match count, and report paths. Readable via `peekdocs --runs [N] [--json]`
- **Diff Snapshots GUI** (Tools menu) — two file pickers for old and new snapshot JSONs, a Compare button, and a scrollable color-coded results pane (green NEW, red REMOVED, orange CHANGED, purple MODIFIED). A status line summarizes counts and turns red/green based on `is_actionable`. Calls the same code as `--diff`, so output matches the CLI byte for byte
- **Global suite index (`~/.peekdocs_suite_index.json`)** — `peekdocs --suite "Name"` now auto-locates the folder a suite lives in. Removes the per-folder `cd` requirement that made the CLI suite path unworkable before. `--list-suites` reads the index; `--list-suites --rescan` walks `~/Documents` and `~/Desktop` to rebuild it
- **Suite section summary** — TXT, DOCX, and HTML suite reports now include a "Section summary:" block at the top listing each saved search's name and match count. HTML uses anchor links. GUI Results Preview shows the same summary. Fixes the "buried section" UX bug where 7,700 lines of "heart" matches hid 93 matches of "password" at the bottom
- **Suite preview highlighting** — matched terms in the GUI suite Results Preview now get the yellow "match" tag, same as Standard Search results
- **"What's the difference?" link** — muted-blue underlined link under the three Run buttons opens a comparison popup with one-paragraph "best for" guidance per mode (Standard / Suite / Regex)
- **"Diff Snapshots" Tools-menu entry** alongside Bookmarks, Indexes, Schedule Search, etc.
- **Automation and IT Use section** in User Guide — exit codes, JSON output schemas, scheduled-scan patterns, `--diff` / `--hash` / `--on-match` reference, where reports and logs live on disk, service-account permissions, sharing collections across machines, useful CLI references for IT
- **Headless servers and containers** subsection in User Guide — explicit guarantee that the CLI imports and runs without `tkinter` or `customtkinter`, with a minimal Dockerfile and the contract for `--check` on headless boxes
- **"Why compare snapshots? (and why JSON?)" subsection** in User Guide — EE-friendly framing of `--diff` as drift detection (multimeter vs strip-chart recorder), JSON as structured plain text (SPICE-netlist / BOM analogy), and five concrete IT use cases: credential leaks, cleanup verification, stale references, unexpected file edits, and trend analysis
- **`&&` vs `;` exit-code gotcha callout** in User Guide — explains why `peekdocs --diff ... > diff.txt && open diff.txt` silently fails when the diff finds changes (exit 1 short-circuits `&&`), with corrected patterns for both interactive and cron use
- **Search Modes overview** in README and User Guide — three-mode summary (Standard / Regex / Suite) with example commands and produced report-file paths
- **Platform Notes** section in User Guide — macOS Full Disk Access guidance, Windows Defender behavior, Linux Tk install commands
- **Windows PowerShell examples** in Search Suite Use Cases
- **Glossary entries** in README and User Guide — cron, Diff, JSON Lines, jq, SIEM, Webhook, Hash, CI pipeline
- **"Home users and individuals"** subsection at the top of README's Who Is It For audience profiles
- **Snapshot/diff filename convention** — `peekdocs_snapshot_<label>.json` for snapshots, `peekdocs_diff_<label>.json` for diff outputs, mirroring the existing `peekdocs_*_results.*` report-file convention. Documented in User Guide and applied consistently in CLI help, GUI help, and all worked examples
- **Python 3.13 and 3.14 in tested range** — `TESTED_PYTHON_MAX` bumped to (3, 14); 3.13 and 3.14 added to the `Programming Language` trove classifiers in `pyproject.toml`
- **Cross-platform CI matrix** — GitHub Actions Tests workflow now runs `pytest tests/` on ubuntu-latest, macos-latest, and windows-latest across Python 3.10-3.14 (15 matrix cells, `fail-fast: false`). Plus a dedicated `test-headless-install` job that installs peekdocs without `customtkinter` on Linux and runs `tests/test_headless.py` against a genuinely Tk-less environment
- **tests/test_headless.py** (4 tests) — installs a `MetaPathFinder` blocking every Tk module, then asserts `peekdocs.cli` imports cleanly, `--help` / `--check` run with exit 0, and a real `--stdout` search emits valid JSON. Regression guard against any future CLI code path that grows a quiet Tk dependency

### Removed

- **PII Scan** — entire feature deleted on 2026-05-21 (~1,000 lines across 15 files): GUI button, CLI flag (`--pii-scan`), sensitive pattern detection (`sensitive_patterns.py`), all tests (`test_pii_patterns.py`), and every PII-related reference in docs and UI. Eliminated to remove implicit legal/compliance promises. Regex Search replaces it for user-defined sensitive-data workflows
- **Compliance-adjacent language** purged from all documentation. Example names changed from "security audit" to neutral alternatives ("code patterns", "log analysis", "invoice extraction"). peekdocs is positioned as a general-purpose search tool, not a security or compliance tool
- **"Coming soon" features** (Scheduled scans, Search templates) removed from README — Schedule Search shipped and Search Wizard provides templates
- **"Most likely early adopters" subsection** removed from README — covered by the new audience profile table

### Changed

- **Search button renamed to Standard Search** — green main-screen button now reads "🔍 Standard Search" (was "🔍 Search"), widened to 220px. Disambiguates from the purple Regex Search button. All post-search reset paths updated so the label stays consistent after completion or cancel. Tooltips, Step 3 badge label, and disambiguation sections in README and help text updated
- **`Standard Search vs Regex Search` decision table** in main help screen — when to use each, with green/purple button labels and a feature-by-feature breakdown
- **`Regex Search vs Search Suites` section** in main help — clarifies that suites group saved searches (any mode), while regex collections group regex patterns only
- **Regex Search results popup** — per-pattern View Files buttons (replaces show-files checkboxes), per-pattern match counts, View Text with highlighted content
- **README "Why peekdocs?" tightening** — credit paragraph compressed, off-topic LibreOffice tangent removed from highlighted-reports bullet, three application-feature bullets merged, summary shortened
- **Cloud language softened** — "blocks" → "avoids" across all docs for cloud-based applications (Google Docs, Apple Pages)
- **PII/security definitive claims softened** in remaining mentions before full PII removal — "ensures" → "helps prevent", "finds" → "scans for patterns"
- **CLI help text reorganized** — `--regex-collection` and related flags grouped with `--suite` in Settings & Info section
- **Result-file rename** — `peekdocs_results.*` split into three families to disambiguate which mode produced each report: `peekdocs_standard_results.*` for Standard Search, `peekdocs_regex_results.*` for Regex Search, `peekdocs_suite_results.*` for Suite. No backward-compatibility layer (the app has no users yet)
- **Main-screen run-buttons row** — parallel "Run X" verbs: Run Standard Search, Run Search Suites (moved from Tools menu), Run Regex Search. Search Wizard renamed to Wizard. Buttons color-coded: blue (#2196F3) Standard, green (#76BA1B) Suites, orange (#FF9800) Regex
- **Options row tinted light blue (#90CAF9)** to visually associate the options (AND/OR, Recursive, Whole Word, Use Index) with the Run Standard Search button — they apply only to that mode. Step labels and the "Main page" header use the same blue. All `?` help-chip buttons unified to a single blue style (`#1565C0`)
- **Advanced and Wizard styled as hyperlinks** — blue, underlined, matching standard hyperlink affordance to signal "click to open another panel"
- **"Main page" header** added at the top of the search tab to disambiguate the main screen from the various Tools popups
- **`--diff` error visibility** — error messages now go to stderr (was stdout), so they remain visible even when stdout is redirected to a file. When the input has a known document extension (`.odt`, `.docx`, `.pdf`, etc.) the error includes a hint explaining `--diff` compares snapshots, not source documents, with a runnable example of producing snapshots first and a pointer to LibreOffice's Compare Document feature for the actual document-vs-document case
- **`--diff` usage examples** — every snapshot filename in CLI help, GUI help, and User Guide examples now uses the `peekdocs_snapshot_*.json` convention; diff outputs use `peekdocs_diff_*.json`
- **Final liability audit and language sweep** — README, User Guide, and User Guide footer pass-through to remove regulation names, compliance/forensic/PII framing, and fitness-flavored examples. CHANGELOG retains historical mentions as a project record. MIT-License "as is" disclaimer added to the README Who Is It For section

### Fixed

- **`--stdout` with `--regex-collection`** — JSON output now correctly suppresses banner and progress output; works in pipelines
- **Regex Search hang on large match counts** — lazy widget creation for pattern rows, report match cap at 10000, background-thread report writing prevents GUI freeze
- **Cancel button** — skips report writing and results popup when cancelled mid-run; cleans up partial state
- **Config persistence** for dynamic `regex_search_*` keys (and former `pii_scan_*` keys) — settings now survive across sessions
- **Results Preview double-highlighting** with capturing-group regex patterns
- **Regex Search settings persistence** on Close — pattern names, regex text, and enabled state retained; inline flags stripped from combined regex before execution
- **Indexed whole-word search** — no longer matches inside underscored identifiers
- **PDF and HTML report highlighting** for regex, wildcard, whole-word, and Boolean expression modes
- **View Files button alignment** — fixed inner-frame width to match canvas; button now aligns to right edge with proper pack ordering
- **FAQ correction** — clarify that grep results inside the source tree (XML namespaces, URLs in help text) are not network calls
- **Three exaggerated claims softened** — removed "air-gapped" (peekdocs runs locally but doesn't enforce air-gap), "milliseconds" (replaced with real benchmarks), and inflated search-mode counts
- **Pre-publication hardening** — PyPI URL placeholders, path sanitization in error log, `.gitignore` for `SearchTheseDocuments`, PyPI keywords, JSON `directory` field, README example fix
- **GUI Search Suites hang** — `UnboundLocalError` in the suite worker thread on cloud-folder redirect. Root cause was a closure-and-assignment gotcha: reassigning the `folder` variable inside the inner function made it function-local throughout the closure. Fixed by extracting the output path into a separate `output_folder` variable
- **`--diff` errors going to the wrong stream** — were printed to stdout, which got swallowed by `> diff.txt`. Now go to stderr so they survive a redirect

## [0.3.41] — 2026-05-06

### Added

- **100+ file types** — added Jupyter notebooks, .env, Dockerfile, CSS, SCSS, Scala, Lua, GraphQL, Protobuf, Terraform, .properties, .gradle, .cmake, .conf, Apple Numbers/Keynote, Visio .vsdx, and 31 source code/engineering formats (up from 86)
- **Search Suites** — group saved searches and run them together with per-suite output format options (DOCX, TXT, HTML, CSV, JSON, PDF) and progress bar during execution
- **--pii-scan CLI flag** — terminal-based PII scanning, safe to pipe, never shows actual sensitive data; works on remote/SSH servers
- **--open flag** — auto-open reports after search; auto-enables the requested output format (docx, txt, pdf, json, html)
- **--list-files CLI command** — show all peekdocs-created files in the current directory
- **--config --reset CLI command** — restore factory default settings
- **--clear and --clear-all CLI commands** — delete peekdocs files from the current directory
- **Line proximity search (-P N flag)** — find terms within N lines of each other across all file types
- **-q and -qq flags** — quiet mode (suppress banner) and minimal output
- **HTML report for suites** — search suites now generate HTML reports alongside DOCX and TXT
- **Cloud folder protection** — blocks searches to cloud-synced folders (Google Drive, OneDrive, iCloud, Dropbox); auto-redirects report output to ~/peekdocs_reports
- **Safe file opening** — blocks cloud-uploading apps (Apple Pages, Google Docs) from opening .docx and PDF reports to prevent data leaks
- **Delete on Close checkbox** — auto-delete all reports, index, and tracked session folders when the app closes
- **Delete Everything Now button** — one-click cleanup of all peekdocs files including search index, terms, and folder fields
- **Clear Preview button** — instantly clear the results preview pane
- **Clear History on Close option** — auto-clear search history when the app closes
- **Clear Files popup** — per-file checkbox popup replacing multiple clear buttons
- **Recent Searches persistence** — recent searches now saved across sessions in ~/.peekdocsrc
- **Hover Text ON/OFF toggle** — on main screen bottom row to control tooltips
- **Step 1–4 badges** — blue step labels replace numbered text on the main screen
- **PII Scan on main screen** — moved from Tools menu to a prominent green/teal button next to Search
- **PII Scan independence** — PII scan uses its own folder, recursive setting, and file types, independent from main search
- **PII scan report improvements** — READ BEFORE ACTING disclaimer, Think Before You Print warning, page break before summary, category name in View Text window
- **Suites button on main screen** — moved from Tools menu for easier access
- **README button** — added to bottom row next to User Guide
- **View Report HTML button** — added to main screen report row
- **Network folder support** — documented and tested searching network/NFS/SMB shares
- **Performance section** — benchmarks for 1K/10K/50K/1M files with real-world data (105 Word docs in 4.4s, index: 0.24s)
- **Glossary of technical terms** — added to both README and User Guide
- **Data Architecture section** — for IT and security teams in README
- **PyInstaller build script** — standalone .exe/.app builds with GitHub Actions release workflow
- **Integration test suite** — added alongside existing unit tests

### Fixed

- **Linux PII scan hang** — fixed blocking issue on Linux
- **Linux tooltip flicker and sticking** — use delayed hide instead of pointer check
- **Linux SPDX license format** — fixed PEP 639 compatibility for setuptools
- **Linux Browse double-click behavior** — documented and added tooltip note
- **Windows popups behind main window** — fixed Excluded Files, Matched Files, and all other popups appearing behind the main window
- **Windows dark mode** — fixed white flash, invisible popups, stuck-offscreen popups, and CTkToplevel crash
- **Windows path-too-long error** in tar archive extraction
- **Windows Unicode progress bar** — fixed encoding issue
- **Four Windows file handling issues** — hardened for cross-platform edge cases
- **Named pipes, sockets, and virtual filesystems** — prevent hangs during file discovery
- **.env and Dockerfile discovery** — handle dotfiles and extensionless files correctly
- **--open with -sa** — now opens the accumulated report, not the regular one
- **--pii-scan flag order** — works with -r in any position
- **Duplicate version/CPU lines** in CLI banner output
- **AND mode** — corrected 'same paragraph' to 'same line' with nuance
- **Whole-word matching** for terms with punctuation
- **View Text highlighting** for quoted phrases
- **Duplicate Finder crash** — added missing @staticmethod to _format_file_size
- **File Inventory crash** — removed stray @staticmethod decorator
- **Suite runner crashes** — fixed _update_status missing method, subprocess hang, 0-file count parsing, inflated file counts, and match limit issues
- **Max matches confusion** — reverted blank-means-unlimited; explicit 0 means no limit, defaults shown as 1000/100
- **Confusing status** when max matches caps the report
- **PII scan false positives** — fixed credit card matches on URLs, SSN matches on DOIs/ISBNs, password matches in URL query parameters
- **macOS file opening** — fall back to TextEdit when default app fails; Linux fallback added too
- **Dark mode fixes** — themed all 35 popups, fixed TOC text color, menu separators, PII scan status text, Search Wizard plain tk widgets

### Changed

- **GUI layout overhaul** — Search and PII Scan buttons enlarged with #76BA1B green/teal colors; AND/OR toggle changed to checkbox blue; Advanced and Wizard as icon buttons on options row; preview moved directly under status line; Cancel mode for Search and PII Scan buttons
- **Rename Proximity to Word Proximity** — clarify that line proximity is CLI-only
- **Rename Run Search to Search** — shorter button label
- **Rename Reset Saved Defaults to Restore Factory Settings**
- **Rename App Files to View All peekdocs Files** in Tools menu
- **Rename DO_NOT_SEARCH_ prefix to peekdocs_ prefix** for easier file identification
- **PII Scan report removed as file** — results shown on screen only, no file written
- **PII credential detection expanded** — added passcode, pin, passphrase, signin, logon, signon, p/w, user_id, uid, login, username keywords with hyphen/underscore variants
- **Token detection narrowed** to api_token/auth_token/access_token only (reduces false positives)
- **PII Scan folder persistence** — remembers folder between invocations and across sessions
- **Auto-save** for text size, appearance, hover text, preview size, and CSV/JSON/PDF/HTML checkbox states
- **Moved PII Scan and Manage Indexes** from main screen to Tools menu, then PII Scan back to main screen
- **Renamed Manage Indexes to Indexes** — shows search folder in popup
- **CLI banner reorganized** — version at top, CPU cores and README URL prominent, search modes at bottom, common options section added
- **Report headers** — added peekdocs version, 'Saved as' filepath, removed boilerplate
- **Browse/+Folder/Single File enclosed in visible frame** with border
- **Oversized files now shown in Excluded Files list** with Max File Size / Max Matches interaction documented
- **Dependencies documented** in User Guide and README prerequisites

## [0.3.0] — 2026-04-16

### Added

- **Tools menu** — eight new folder analysis and user utilities: File Inventory, Duplicate Finder, Large Files, Empty Files, Recent Changes, Protected Files, Search History, and Bookmarks
- **Search Options group** on main screen with AND/OR toggle buttons, Recursive and Whole Word checkboxes, and help button
- App Size and Preview Size dropdowns on the Results Preview header, both persisted between sessions
- Status line now leads with files-searched count
- Recursive and Whole Word default to ON at startup
- **Multi-folder search** — search across multiple folders at once via +Folder button or semicolon-separated paths
- **HTML export** — new `-o html` output format with styled, highlighted results for sharing via email or browser
- **Search status shows active modes** — status line now displays AND/OR, Regex, Fuzzy, Wildcard, Whole Word, Inverse, and Index indicators while searching
- **Dark mode** — Appearance toggle in Tools menu: Dark, Light, or System (follows OS). Saved between sessions
- PII pattern test suite (74 tests validating sensitivity and specificity of all 8 categories)
- Index corruption now notifies the user with a warning dialog and logs to peekdocs_errors.log
- Config file (~/.peekdocsrc) now written with owner-read-write-only permissions

### Fixed

- Wildcard search now matches punctuation (e.g., `budg*` matches "budget!" and "budget.")
- Single-file selection no longer persists after changing the search folder

### Removed

- **Compliance feature removed — peekdocs is now a focused home-user document search tool.** The following features were removed to simplify the product, eliminate legal-exposure concerns, and match peekdocs's actual audience of individuals and small teams searching their own files:
  - Compliance Wizard and the 9 industry starter templates (SOX, HIPAA, Legal, Government, ISO, FERPA, Real Estate, Insurance, HR)
  - Search Suites (Manage Suites panel, suite builder, cascade mode, pass/fail criteria, suite execution)
  - Auto-run scheduling for suites
  - Email alerts (SMTP configuration, test email, alert sending)
  - Suite reports (`.txt`/`.docx`/`.json` consolidated suite reports, stage reports, source file manifest, report fingerprint)
  - Search Wizard pattern categories that were compliance-specific
  - `compliance_templates.py` and `email_alert.py` modules (deleted)
  - `docs/COMPLIANCE_GUIDE.md` (deleted)
- Saved searches are preserved. Collection files with a legacy `test_suites` key continue to load — the key is silently dropped.

### Changed

- PII Scan, Save Search, Load Search, Search Wizard, and all other core features are unchanged and fully supported.
- README and User Guide rewritten to focus on home-user workflows: search, PII Scan, saved searches, highlighted reports.
- Disclaimers simplified — peekdocs is now described straightforwardly as a local document search and pattern-matching tool.

## [0.2.0] — 2026-03-30

### Added
- **Sensitive Data Scan** — one-click scan for PII and sensitive data: SSNs, credit cards, tax IDs, emails, phone numbers, passwords, dates of birth, and large dollar amounts. Results categorized by severity (HIGH/MODERATE/INFO) with per-file details, line numbers, and a highlighted `.docx` report with yellow-highlighted matches. Click any category to see affected files
- **Email support** — search .eml (standard email), .msg (Outlook), and .pst (Outlook mailbox archive) files. Searches headers (From, To, Subject, Date) and message body
- **Archive support** — search inside .zip, .tar, .gz, .bz2, .tgz, .7z, and .rar archives transparently. Each match shows which file inside the archive it came from
- **Legacy Office formats** — search .doc (Word 97-2003), .xls (Excel 97-2003), and .ppt (PowerPoint 97-2003) files
- **Email alerts** — optional SMTP email notifications when scheduled suite runs detect failures. Configure via GUI (Configure Email Alerts in suite panel)
- **Consolidated suite .docx report** — formatted Word document with color-coded PASS/FAIL summary table, per-stage details, report fingerprint for tamper detection, and source file manifest listing every document in scope
- **View Suite Report button** — appears in suite panel after each run to open the .docx report directly
- **Results preview pane** — inline scrollable preview in the main GUI window showing matches with highlighted terms, filenames, and directory paths after each search
- **Matched files popup with line numbers** — clickable "View N matched file(s)" link on the status line opens a popup listing each file with match count and line numbers (e.g., "contract.docx (3 matches — lines 12, 47, 89)")
- **View Text (with line numbers)** — new button in the matched files popup that displays the file's extracted content with line numbers and highlighted matches, scrolled to the first match. Works for all 46 file types
- **Determinate progress bar** — shows actual file count progress (e.g., "47/200 files") for direct file scanning; indeterminate spinner for indexed searches
- **Text Size dropdown** — Small/Normal/Large/Extra Large scaling for all GUI text and widgets. Auto-saves to config. Located on bottom toolbar
- **Advanced Search Options popup** — moved from collapsible inline panel to a separate window, keeping the main window compact
- **First-run welcome dialog** — getting-started guide appears on first launch with 4-step quick start
- **Clear Error Log button** — on bottom toolbar next to View Error Log
- **Clear Auto-Run History button** — in suite panel next to Open Auto-Run History
- **46 supported file types** (up from 25) — documents, spreadsheets, emails (.eml, .msg, .pst, .mbox), archives, Apple Pages, calendars (.ics), contacts (.vcf), data/config files, and images (OCR)
- **Comprehensive -h help** — rewritten with description, usage syntax, file type list, and sections grouped by purpose (Search Modes, Filters, Output, Index, Settings)
- **Troubleshooting section** expanded to 31 entries covering Windows, macOS, and Linux
- **Compliance Wizard** — pick an industry starter template (9 available), review and customize checks, create a search suite with one click. Starter templates for Financial Services/SOX, Healthcare/HIPAA, Legal, Government, Manufacturing/ISO, Education/FERPA, Real Estate, Insurance, and HR
- **Run Suite button** — on the main screen next to Run Search; opens the Manage Suites panel. Green when suites exist, red when none
- **Suite report preview** — after a suite run, the txt report is displayed in the main preview pane
- **Import Template** — new button in Manage Suites to load saved searches and suites from an external .json file, merging into the existing collection without overwriting non-conflicting items
- **Export Suite** — new button in Manage Suites to save the selected suite and all its referenced saved searches to a `.json` file for sharing with colleagues, clients, or other machines
- **Max File Size field** — in Advanced Search Options; files over the limit (default 100 MB) are skipped to prevent memory issues. New `--max-file-size` CLI flag. Changing the value automatically rebuilds the index on the next indexed search so results stay consistent
- **Excluded Files view** — "View N excluded file(s)" button appears after each search, opens a popup listing every file that was NOT searched, grouped by reason (unsupported type, prior output files, oversized, hidden, etc.)
- **Compliance and auditing guide** with industry examples, step-by-step instructions, and 9 pre-built sample suites
- **Limits and Constraints documentation**
- **Files Created by peekdocs reference** — complete catalog of every file peekdocs generates
- **Index and subfolder documentation** — explains how indexes work across folder hierarchies and with search suites
- **Search Wizard** — guided search configuration with 21 patterns (SSN, phone, email, dates, dollar amounts, etc.). Pick a type, click Apply, and the search bar is configured automatically
- **Recent Searches dropdown** — button next to the search bar remembers your last 10 searches for quick recall
- **PDF highlighted reports** — optional `.pdf` output with yellow-highlighted matches, matching the `.docx` report style. Enable with the PDF checkbox or `-o pdf` on the CLI
- **App Files button** — bottom toolbar button listing all peekdocs-created files in the search folder with full paths, grouped by category
- **All Collections button** — bottom toolbar button that scans your home directory for all `.peekdocs_collection.json` files, showing saved searches and suites across every folder. Double-click a folder to switch to it
- **Fuzzy search highlighting** — fuzzy matches are now highlighted in the results preview and reports, not just exact matches

### Changed
- **"Save Settings" buttons renamed** — Search Bar button is now "Save Search" (saves to collection for suites); Advanced Search Options button is now "Save Defaults" (saves to ~/.peekdocsrc)
- **Advanced Search Options, Search Suites, Manage Indexes** consolidated onto one row
- **README restructured** — slim landing page with detailed docs in `docs/` directory
- **Marketing summary** updated to mention emails, archives, email alerts, and all three interfaces (terminal, GUI, API)
- **Introduction** lists Word docs before PDFs (primary audience is Windows users)
- **.peekdocs_collection.json excluded** from search results on all platforms (was already hidden on macOS/Linux but not Windows)
- **peekdocs_errors.log and .peekdocsrc** also excluded from search results

### Fixed
- Last run label disappeared when auto-run schedule set to Off
- Auto-run suite reports now include .docx format (was only TXT and JSON)
- Suite reports auto-generated on manual runs (previously only on scheduled runs)
- CTkToplevel widget variables reset during initialization (recursive checkbox not persisting)

## [0.1.0] — 2026-03-28

### Initial release
- Search 25 file types (PDF, DOCX, XLSX, PPTX, EPUB, ODT, ODS, ODP, RTF, HTML, CSV, JSON, XML, YAML, YML, TOML, MD, RST, TEX, INI, CFG, SQL, LOG, TSV, TXT)
- CLI with full flag set (-a, -A, -B, -c, -e, -f, -m, -n, -o, -O, -p, -r, -R, -s, -sa, -t, -v, -w, -W, -x, -z)
- GUI with customtkinter (peekdocs-gui)
- Boolean expression search with AND, OR, NOT, parentheses
- Range queries on dates, dollar amounts, percentages, ages, file metadata
- Fuzzy matching via rapidfuzz
- Wildcard and whole-word matching
- Proximity search
- OCR via Tesseract
- SQLite FTS5 search index with auto-refresh
- Search suites with pass/fail criteria and cascade mode
- Suite scheduling (auto-run) with persistent schedules
- Highlighted .docx and .txt reports
- CSV, JSON, and PDF export
- Save and append report archiving
- Library API (Python search() function)
- Cross-platform: Windows, macOS, Linux
