# Changelog

All notable changes to peekdocs are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Versions are listed in reverse chronological order (newest first). Each release groups its changes under **Added** (new features), **Changed** (modifications to existing behavior), **Removed** (features taken out), and **Fixed** (bug fixes).

**To upgrade to the latest version:**

- **pipx** (recommended, Mac / Linux / Windows): `pipx install --force git+https://github.com/exbuf/peekdocs.git`
- **pip** (advanced): `pip install --upgrade git+https://github.com/exbuf/peekdocs.git`
- **Standalone download**: grab the new file from the [Releases page](https://github.com/exbuf/peekdocs/releases/latest) and replace your existing copy. Your settings and saved searches live in your home directory, not in the executable — nothing is lost on upgrade.

## [Unreleased]

### Added

- **Regex Wizard rename.** The categorized regex picker popup formerly titled *Search Wizard* is now titled **Regex Wizard** to disambiguate from the main-screen **Search Wizard** button (which opens the category-cards search-type wizard — a separate popup). The picker's old card label on the search-type wizard (*Regex pattern builder*) is also renamed to *Regex Wizard* for consistency. Window title, header label, help popup title, and every user-facing reference in docstrings / tooltips / help bodies are updated; the internal method name `_open_search_wizard` is unchanged for git-history continuity. Side-fix in the same touch: the search-type wizard's *Regex Wizard* card help bullet dropped a stale `SSNs, invoice numbers, part numbers` example (violates the neutral-language voice rule) and now lists the six neutral categories instead.
- **Regex Tester — Pick from Wizard… button.** New button in the Regex Tester popup's pattern-action row opens the **Regex Wizard** (the 35-pattern × 6-category picker reached from the main screen's *Search Wizard* → *Regex Wizard* card) with its Apply target rewired to the Tester's Pattern field instead of the main search bar. Users get a ready-made starting pattern (dates, money, identifiers, contacts, code patterns, networking), can combine multiple via OR / AND, can mix in a custom regex, then tweak inside the Tester with live highlighting in the sample area. No UI duplication: the Regex Wizard popup is unchanged for its existing main-screen invocation; only the Apply callback differs based on caller context. Implementation refactors `_open_search_wizard()` to accept an optional `on_apply=callable` parameter — when provided, the Apply button calls it with the combined regex string instead of routing through `_apply_wizard` (which mutates the main search bar, enables regex mode, etc.). Tester help popup updated with a new bullet describing the button and the OR-only constraint.
- **Regex Wizard — ? help button.** New blue chip in the Regex Wizard's header opens a dedicated help popup (`_show_regex_builder_help`). The load-bearing section is **OR vs AND**: OR produces a single regex via `|` alternation and works in every Apply target (main search bar, Regex Tester, Regex Search popup row); AND produces multi-term search-bar syntax (`"pat1" "pat2"`) which is only meaningful for the main search bar — pasted into the Tester or a Regex Search popup row it'd compile as a literal-character regex that matches nothing. Help spells out "✓ where AND applies" and "✗ where it doesn't" with the rule of thumb: pick OR unless your target is the main search bar. Also documents categories (35 patterns across 6 categories — dates, money, identifiers, contacts, code patterns, networking), Custom regex field, and what Apply does per caller context. Close button lives on a dedicated bottom row inside its own `close_frame`, centered, matching the close-button pattern the Regex Wizard popup itself uses (`pack(side="bottom")` reserves the row before the scrollable Text takes the rest).
- **Regex Search popup — Pick from Wizard… button.** Same Wizard-integration pattern landed on the Regex Search popup itself. Button is right-edge aligned on the Whole Word row (the same row that carries the *Whole Word (wrap each pattern with `\b` at run time)* checkbox). Click → open the Regex Wizard → pick patterns / mode / custom regex → Apply drops the combined regex into the **first empty pattern row** above, enables that row, and seeds the Name field with "Wizard pattern" if it was blank. If all 10 visible rows are full, surfaces an informational dialog telling the user to clear a row first (via the row's − button or by emptying the regex text) and click again. Tooltip on the button names the six Regex Wizard categories so users know what's behind the click without opening it, and flags the OR-only constraint.

### Changed

- **Search Wizard — `_open_search_wizard()` accepts an `on_apply` callback.** Backwards-compatible API change for the GUI mixin. Existing call sites (Tools menu, search-wizard guide, etc.) pass nothing and get the original main-search-bar Apply behavior; the new Regex Tester call site passes a callback that routes the combined regex into the Tester. Internal API only — no CLI / public-API surface change.

## [1.1.2] — 2026-06-12

Point release fixing the Standard Search Cancel button. It has been silently broken for an indeterminate number of releases — clicking Cancel mid-search showed an error popup with a half-formed CLI banner ("`peekdocs -q -r -W --max-file-size 0 budget` / Searching ... / Error: An unexpected error occurred"), and the original search kept running to completion in the background.

### Fixed

- **Standard Search — Cancel button now actually cancels.** Three causes compounded into the symptom:
  1. **`self.process` was never given the live `Popen` handle.** `_run_search` set `self.process = None` and called `_run_peekdocs_cli`, which spawned its own local `proc` variable — the GUI held no reference to the running subprocess. So the Cancel branch (`if self.process is not None: terminate`) was always skipped silently.
  2. **The "Cancel" button fell through and started a SECOND search.** With the cancel branch skipped, `start_search()` continued into validation + command-building + thread-start. Two subprocesses then ran simultaneously, colliding on `peekdocs_standard_results.txt` and the SQLite index; one of them raised an exception that the CLI caught and printed as "An unexpected error occurred. Details logged to peekdocs_errors.log". The GUI surfaced that stdout in an error popup, with the second command's banner still in the buffer — which is where the mysterious "`--max-file-size 0`" artifact came from.
  3. **SIGTERM returncode is platform-dependent.** Even after wiring (1) correctly, `-15` on Unix lands in the cancel branch but `1` on Windows (Python's `TerminateProcess` convention) collides with peekdocs's "no matches" exit code — so a Windows cancel would silently say "Search complete. No matches found."

  Fix:
  - `peekdocs/gui/_helpers.py` — `_run_peekdocs_cli` accepts a new optional `on_process_started` callback invoked with the live `Popen` immediately after spawn on the subprocess path. Backwards-compatible; ignored on the PyInstaller in-process path.
  - `peekdocs/gui/_mixin_search.py` — `_run_search` passes the callback to stash the Popen on `self.process` so Cancel can `terminate()` it.
  - `peekdocs/gui/_mixin_search.py` — `start_search()` sets `self._search_cancelled = True` before calling `terminate()`, and resets the flag at the start of every new search. `_search_finished()` checks the flag *before* the returncode dispatch and short-circuits to a clean "Search was cancelled." status line — bypassing the platform-dependent SIGTERM returncode entirely so the Windows-vs-Unix exit-code disparity becomes moot.

  No behavior change for Search Suites or Regex Search cancel paths — those have always used their own cooperative cancellation flags (`_multi_folder_cancelled`, etc.) and were never affected by this bug.

## [1.1.1] — 2026-06-11

Point release fixing the v1.1.0 desktop-notification feature on macOS — it shipped broken in two independent ways and no notification fired when the user clicked away to another app. Both root causes addressed; no behavior change on Linux or Windows.

### Fixed

- **Notify on Search Complete — macOS focus detection.** The v1.1.0 implementation used Tk's `focus_displayof()` to decide whether to suppress the notification when the GUI was already focused. That API is per-application on macOS, not per-OS-foreground — it kept reporting our toplevel as focused even after the user had clicked to Terminal or any other app, so the suppression check fired in every case and the notification never went out. Replaced with an event-driven flag (`self._gui_has_focus`) maintained by `<FocusIn>` / `<FocusOut>` handlers bound to the root toplevel. These events DO fire on real OS-level app transitions across all three platforms, which is the standard cross-platform Tk approach. Default flag value is `True` so notifications don't fire spuriously before the first focus event has been observed.
- **Notify on Search Complete — macOS notification delivery.** Even with focus detection fixed, the v1.1.0 `osascript display notification` path is silently dropped on macOS Sequoia (15+) because Apple Script Editor is the host bundle for AppleScript notifications and isn't approved for notifications by default. The notification was being sent into a denied path with no error, no banner, no Notification Center entry. Switched the preferred macOS delivery to **`terminal-notifier`** (Homebrew: `brew install terminal-notifier`) — a tiny Cocoa app with its own bundle ID that registers for notification permissions properly. Falls back to `osascript` automatically when terminal-notifier isn't installed so the dep-free guarantee still holds for downstream packagers, but the on-disk recommendation is now to install terminal-notifier on macOS. `-group com.peekdocs.search-complete` collapses repeated completion notifications into the most recent one so they don't pile up in Notification Center after a long session.

### Changed

- **Docs — macOS notification setup guidance.** USER_GUIDE per-platform mechanism table and the troubleshooting section now lead with `brew install terminal-notifier` as the macOS recommendation, with the osascript fallback and Script-Editor-not-listed-in-System-Settings symptom documented for users who hit the old path. Checkbox tooltip in Advanced Search Options updated to mention the `brew install terminal-notifier` line.

## [1.1.0] — 2026-06-11

First minor-version bump since 1.0.0. The release leads with two
genuinely new public features and three new modules. **`peekdocs
--watch`** is a long-running CLI mode that tails a folder and emits
matches as NDJSON for log-shipper pipelines (`watcher.py`, new
dependency `watchdog>=4.0,<7.0`). **Desktop notification on search
complete** fires a native OS notification when a Standard / Suite
/ Regex run finishes (`notifier.py`, dep-free across macOS / Linux
/ Windows). Plus a **Regex Tester** scratchpad popup, **bash-style
↑ / ↓ history recall** in the search bar, **Run Multiple Search
Suites** + **Run Multiple Regex Collections** multi-run pickers,
report-accuracy fixes (yellow-highlight word dropping, file-count
header, dedup + sort order), and a round of voice / accuracy
polish across the user-facing docs. The 1.0.x → 1.1.0 bump reflects
the new CLI flag, the two new public modules, and the new
dependency — semantic-versioning correct.

### Added

- **`peekdocs --watch` — folder watcher with NDJSON streaming output.** Long-running mode that watches a folder via the `watchdog` library, re-runs a named regex collection on every file create / modify / move event, and emits one self-contained JSON record per match to stdout. Each record carries `timestamp` / `file` / `line` / `matched_text` / `pattern_name` / `pattern_regex` / `collection`, on its own line — the standard NDJSON / JSON Lines shape that any log shipper and any shell pipeline (`jq`, `grep`, `awk`) consume natively. Usage: `peekdocs --watch -d <folder> --regex-collection NAME [-r]`. Status / warnings go to stderr so the stdout stream stays a clean NDJSON pipe; `Ctrl-C` shuts down cleanly with exit 0; per-file debounce absorbs the duplicate `on_created` + `on_modified` events that platforms emit for a single save. Refuses to run as root by default (`--allow-root` overrides); warns when the watch target looks like a system path or another user's home directory (`--allow-system-paths` suppresses). Reuses the existing `api.search()` per-file extraction + matching pipeline so the watcher inherits the 100-format matrix and every regex-engine improvement the one-shot search path carries. Pairs with the seeded Examples collection (email, URL, IPv4/v6, ISO date / time, UUID, semver, hex color, Markdown link, TODO / FIXME, JIRA ticket, ISBN, DOI, USD amount, env var) or any user-built collection — the watcher inherits whatever patterns the collection contains and emits matches in real time as files arrive. New watcher module at `peekdocs/watcher.py`; new dependency `watchdog>=4.0,<7.0`; 18 new tests in `tests/test_watcher.py` covering safety checks, the legacy-string `"on"` / `"off"` enabled-flag, and per-file scan emission.
- **Regex Search — Run Multiple Collections.** New button at the bottom of the Regex Search popup opens a checkbox picker listing every saved collection and pattern count. Check two or more, click **Run Selected**, and all their patterns run together against the popup's folder. Pattern display names in the results popup are prefixed with their source collection (`[Examples] Email address`, `[Common Code Patterns] UPPER_CASE constant`, …) so per-pattern hit counts attribute matches to a specific collection. Reuses the popup's Whole Word toggle and report-mode checkbox. The 10-row visible cap doesn't apply — patterns come straight off disk.
- **Regex Search results popup — Open TXT / Open DOCX / Open Folder buttons.** Three buttons appear under the "Reports saved to:" line so users can launch the saved reports directly from the popup. Buttons are hidden in screen-only mode (no files to open).
- **Regex Search — per-row remove button.** A small red **−** button next to each pattern row removes that row from the visible 10-slot list (shifts the rows below up by one). Display-only; persist the change via Save Collection As → same name (overwrite).
- **Regex Search — active collection label.** A bold blue **Currently loaded: X** label next to Save / Restore buttons and the popup title bar tells users which saved collection produced the rows they're seeing. Persisted across sessions via `~/.peekdocsrc`. Auto-detected on open by comparing row regexes against saved collections when no name has been persisted yet.
- **Regex Search — Whole Word toggle.** Checkbox below the pattern rows wraps each enabled pattern with `\b(?:…)\b` at run time (non-capturing so alternation like `cat|dog` stays correct). State persists across sessions.
- **Search Suites — Run Multiple Search Suites.** New button on its own row, just above Close in the Search Suites popup, opens a checkbox picker listing every saved suite with its search count. Check two or more, click **Run Selected**, and every saved search across the picked suites runs as a single combined run (saved-search names that appear in more than one picked suite run only once). The combined run reuses the existing suite-run pipeline so cancel, status updates, and report formatting all behave identically — there are just more sections in the merged report. Status / report header use the label `Suite A + Suite B` (≤3 picked) or `N suites` (more than 3).
- **Search Suites — completion popup with Open buttons (multi-run path).** Run Multiple Search Suites ends with a small modal listing the resolved report paths and **Open TXT** / **Open DOCX** / **Open Folder** buttons. Distinguishes the just-finished combined-suite reports from leftover-looking main-page report buttons that look identical regardless of which run produced them. Single-suite runs still flow straight to the main page unchanged.
- **Desktop notification on search complete.** New **Notify on Search Complete** checkbox in Advanced Search Options. When checked, every Standard / Suite / Multi-Suite / Regex / Multi-Collection run ends with a native desktop notification carrying the match count, file count, and elapsed time. macOS uses Notification Center via `osascript`; Linux uses `notify-send` (libnotify); Windows uses a PowerShell-spawned `System.Windows.Forms.NotifyIcon` balloon. Dep-free on all three platforms — no `plyer`, no `BurntToast`. Suppressed when the peekdocs window currently has focus (`focus_displayof()` is not None) so users staring at the GUI don't get redundantly pinged. Useful for long scans where the user starts the search and switches to another app. New module `peekdocs/notifier.py` with a single `desktop_notify(title, body)` function that returns `None` on success or a short error string — callers swallow failures silently. Tooltip on the checkbox notes that no data leaves the machine (notification is delivered by the local OS notification daemon).
- **Search bar — ↑ / ↓ recent-search recall.** With the search bar focused, **↑** walks backward through the same persisted last-10 list the Recent Searches popup shows (most recent first); **↓** walks forward. **↓** past the most recent entry restores whatever the user had typed before navigation started — pressing Up by accident never costs the in-flight query. Typing or backspacing resets the cursor so the next ↑ press treats the new content as a fresh draft. Pure cursor / modifier keys (Left, Right, Home, End, Shift, Ctrl) preserve navigation state so the user can edit a recalled query in place. No popup, no mouse — `bash`-style history navigation in the search bar. Tooltip on the search bar and the Recent Searches help popup both updated to mention the shortcut.

### Changed

- **Regex Search Save Collection As — rich popup.** Replaces the original single-name prompt with a popup that includes a live status line ("Will CREATE / OVERWRITE / ADD …"), a scrollable list of existing collections, and three explicit save modes: CREATE (new name), OVERWRITE (typed name matches existing — case-insensitive), ADD (clicked an entry in the list). Saves only the enabled (checked) rows with non-empty regex; legacy disabled entries are no longer persisted.
- **Regex Search reports — yellow highlighting accuracy.** The docx highlighter now uses `re.finditer` + span positions instead of `split`/`findall`, which fixes word-dropping when any user pattern contains capturing groups (e.g. `(TODO|FIXME)`). Each highlight pattern is also wrapped in `(?:…)` defensively. Per-pattern case sensitivity is now decided from explicit `[A-Z]` / `[a-z]` character classes — `[A-Z][A-Z0-9_]{3,}` (UPPER_CASE constant) only highlights uppercase tokens; `\bTODO\b` still highlights `todo` via IGNORECASE.
- **Regex Search search engine — case-intent inline scoping.** Patterns whose character classes use one-sided letter ranges (`[A-Z]`-only or `[a-z]`-only) are now wrapped with `(?-i:…)` before being passed to the search engine, matching the highlighter's case decision. Eliminates report bloat from `[A-Z][A-Z0-9_]{3,}` matching every 4+ char word under the otherwise-IGNORECASE search.
- **Regex Search reports — dedup + ordering.** When several patterns match the same line of the same file, that line is deduplicated and the final match list is sorted by `(file_dir, filename, line_num)`. Reports now read naturally instead of being interleaved in pattern-iteration order with N copies of each match.
- **Seeded Examples collection — substring-match hardening.** The IPv4, IPv6, ISO date, ISO time, USD amount, and Semantic version patterns gained negative lookbehind / lookahead anchors so `1.2.3` no longer matches inside `192.168.1.100`, `192.168.1.1` doesn't match inside `192.168.1.100.5`, etc.
- **Main-page Step 4 report buttons — repoint after every search type.** Single-Suite and Multi-Suite runs already re-pointed the DOCX / TXT / CSV / JSON / PDF / HTML buttons at `peekdocs_suite_results.*` via `_show_action_buttons`. Standard Search has always pointed them at `peekdocs_standard_results.*`. Regex Search and Run Multiple Collections now do the same — after a non-screen-only run that produced matches, the main-page buttons re-point to `peekdocs_regex_results.*` so clicking DOCX opens the just-written regex report rather than the prior standard-search report. CSV / JSON / PDF / HTML flip red because Regex Search doesn't write those formats (by design).
- **Main-page Step 4 button colors — mtime-gated, not just file-existence.** A leftover `peekdocs_standard_results.pdf` from a prior session no longer shows as green after a CSV-only run. `_show_action_buttons` now compares each candidate file's mtime against `self._last_search_start_time` (a new field captured at the top of every search path that survives the `search_start_time = None` reset at finish) and treats green as "this run wrote it" instead of "the file exists." Two-second buffer absorbs filesystem timestamp coarseness on Windows and network shares.
- **Output-format scope — spelled out everywhere.** The CSV / JSON / PDF / HTML checkboxes under "Also output report as ==>" in Advanced Search Options apply to Standard Search only — Suites have their own picker inside the Suites popup, Regex Search always writes just TXT and DOCX. Now documented in: the four format-checkbox tooltips and the "Also output report as ==>" label tooltip, the Getting Started step 4 paragraph (both surfaces), README's "Word report" section, and a USER_GUIDE blockquote in the Advanced Search Options walkthrough.
- **Regex Search reports — `Files searched ==>` and document order.** The header line now shows the real file count and total bytes (was showing `0 (0 bytes)` on every run because `_run_regex_search_per_pattern` passed an empty list as the `all_files` arg to `write_txt_report`). The deduped match list is sorted by filename (case-insensitive) → folder → line_num, so the report reads as one straight A-Z pass through document names regardless of which subfolder each lives in.
- **Save Collection As — paste detection.** The "came-from-listbox-click" flag now clears on `<<Paste>>` and `<<Cut>>` virtual events in addition to `<KeyRelease>` — Cmd-V / Ctrl-V / context-menu paste paths that don't always emit a KeyRelease the binding can observe. Status line and Save action now flip correctly when the user pastes a name over a list-picked one.
- **Multi-run pickers — anchored over parent Run buttons.** Run Multiple Collections and Run Multiple Search Suites pickers now anchor their bottom to the parent popup's bottom edge, overlaying the parent's Run button — keeps the user from misclicking the parent's Run while the picker is open, and visually confirms "this is the active picker now."

## [1.0.23] — 2026-06-08

A licensing-track release. No code changes, no GUI fixes, no API
changes — every commit between v1.0.22 and v1.0.23 was on the path
toward making peekdocs's dependency-license picture accurate and
visible to downstream consumers before any PyPI publication. The
runtime behavior of peekdocs is byte-identical to v1.0.22.

### Added

- **`THIRD_PARTY_NOTICES.md` at the repo root.** Per-library license
  listing of every direct dependency declared in `pyproject.toml`,
  grouped by license category (permissive / choose-your-license /
  LGPL / GPL / AGPL), with version constraints, upstream repository
  URLs, and the `pip show` recipe to regenerate or audit the file
  from a fresh install. The result of an actual `pip show` audit of
  the installed venv rather than a guess — and the audit corrected
  a wrong claim in the previous release's README addition (see
  Changed below). Specifically names PyMuPDF (AGPL v3 OR commercial
  from Artifex Software) and EbookLib (AGPL v3, no commercial-license
  alternative) as the two strong-copyleft dependencies, extract-msg
  (GPL) as the one strong-copyleft non-AGPL dependency, and py7zr /
  fpdf2 / libpff-python as the weak-copyleft (LGPL) dependencies.
  Eleven other deps confirmed permissive (MIT / BSD / Apache 2.0 /
  ISC / CC0 / MIT-CMU).

- **`NOTICE` file at the repo root.** Apache-convention sibling to
  LICENSE. Five-line pointer file that explicitly names the
  copyleft tiers (LGPL / GPL / AGPL) so a reader knows there's
  substantive content to look up in `THIRD_PARTY_NOTICES.md` before
  drilling. LICENSE itself stays as the standard MIT text — license-
  scan tools (FOSSA / ScanCode / Snyk Licenses) look for the
  verbatim MIT phrase boundaries to classify the project's primary
  license, and modifying LICENSE would risk misclassification. NOTICE
  catches the reviewer who only opens LICENSE; THIRD_PARTY_NOTICES.md
  carries the detail.

- **PEP 639 `license-files` wiring in `pyproject.toml`.** Three
  changes to make sure the new licensing files actually ship inside
  the wheel and surface on PyPI:
  - `[build-system] requires` bumped from `setuptools>=68.0` to
    `setuptools>=77.0` (the first release with native PEP 639
    `license-files` support under `[project]`).
  - `license-files = ["LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md"]`
    added under `[project]`. Setuptools embeds all three at
    `peekdocs-<version>.dist-info/licenses/` in the built wheel. PyPI
    surfaces files in this location on the project page sidebar so a
    license-compliance reviewer can find them without leaving
    pypi.org.
  - `"Third-Party Notices"` URL added under `[project.urls]` so the
    per-library license listing is one click away from the PyPI
    project page even for readers who never inspect the wheel.

  Verified end-to-end by building a wheel locally
  (`python -m build --wheel`) — `dist-info/licenses/` contains all
  three files; `METADATA` shows `License-Expression: MIT` plus three
  `License-File:` entries plus the new `Project-URL` entry.

### Changed

- **`README.md` `## License` section now includes a `### Note on
  dependencies` subsection.** Up to v1.0.22 the README asserted
  peekdocs's MIT licensing in seven places but said nothing about
  its dependencies' licenses anywhere. The PyMuPDF AGPL chain
  transitively constrains downstream developers who depend on
  peekdocs's MIT-licensed code; the MIT badge alone was misleading
  them by implication.

  The first draft of this addition (commit 68d4cd2) made a mistake:
  it claimed "the other Python libraries peekdocs depends on ... are
  all permissively licensed (MIT, BSD, Apache 2.0, or similar) and
  present no comparable compatibility tension." A `pip show` audit
  of every declared dependency (which became
  `THIRD_PARTY_NOTICES.md`) showed that claim was wrong — there are
  actually six copyleft dependencies, including a second AGPL one
  (EbookLib) the first draft missed entirely. Commit e801699
  corrected the addition: it now names PyMuPDF, EbookLib (AGPL),
  extract-msg (GPL), and the LGPL trio explicitly, points at
  `THIRD_PARTY_NOTICES.md` for the full picture, and offers three
  practical options for downstream developers integrating peekdocs
  into work that isn't AGPL-compatible (accept AGPL terms, acquire
  a commercial PyMuPDF license *and* avoid the `.epub` reading code
  path, or vendor / replace these libraries).

  Also adjusted the opening line of the License section from "This
  project is licensed under the MIT License" to "peekdocs's own
  source code is licensed under the MIT License" — slight but
  important shift that foreshadows the dependency note and is more
  accurate (the runtime composition isn't purely MIT; the source
  written here is).

  End-user impact stays explicitly called out as zero: AGPL governs
  distribution and modification, not use. A user installing peekdocs
  to search their own documents triggers no obligations.

## [1.0.22] — 2026-06-08

Release driven by a set of related Search Suites GUI fixes (Matched
Files button vs popup count mismatch, status-line number consistency,
per-file highlights in the Text View popup), a multi-monitor fix for
the Text View popup that was stranding it on the wrong screen, three
new demo videos embedded in the README Screenshots area, two voice /
values discipline passes (structural audience splits + a sweep for
latent-compliance phrasing), and the CI improvement that makes this
release's GitHub Release body the first one pulled from the CHANGELOG
section instead of just an auto-generated compare link.

### Fixed

- **Search Suites: orange Matched Files button now matches the popup
  it opens.** Running a suite (e.g. Code Hygiene) was advertising one
  count on the orange `N Matched File(s)` button on the main page,
  showing a different count when the user clicked the button, and
  reporting "No matches in this file" with no yellow highlights when
  the user clicked any file in the popup — three distinct symptoms,
  all in one workflow. Three commits fixed the three components:
  - The button label was using `sum(matched_file_count)` across
    sub-searches, which double-counted any file that hit in more
    than one sub-search (a file matching both `TODO` and `FIXME`
    counted twice). The popup, meanwhile, used a de-duplicated
    `self.matched_files` list, so the button promised e.g. 177 files
    and the popup contained 73. Button label now uses
    `len(self.matched_files)` so it matches what the popup will
    actually display.
  - Per-file highlights in the Text View popup were being built from
    the main search bar, which is empty after a suite run — so the
    popup built no regex, no yellow highlights appeared, and the
    "Matching lines:" label dropped to "No matches in this file"
    even though the file genuinely contained hits for one or more
    sub-searches. The suite-finish handler already builds a combined
    highlight regex from every sub-search's terms (with each sub-
    search's regex / wildcard / whole-word flags honored) for the
    preview pane. That same regex is now stashed on
    `self._suite_highlight_re` and the popup reads it with priority
    over the main search bar.
  - The status line above the preview pane was using the same
    summed file count as the button had, and the "N file(s) searched"
    figure was using `sum(len(s["all_files"]))` — both inflated the
    real numbers by the number of sub-searches. Status line now
    matches the popup; "files searched" uses `max()` across sub-
    searches (the right answer for the typical case where every sub-
    search runs against the same corpus).
  - `total_matches` (the "Found N match(es)" figure) stays summed
    because match-locations across sub-searches really are distinct
    hits — three TODO hits plus three FIXME hits in one file is
    genuinely six matches, not three.

- **Clear Preview button now also clears the Matched Files / Excluded
  Files buttons.** Clicking Clear Preview on the main screen cleared
  the preview text and the count label but left the orange Matched
  Files and Excluded Files buttons visible — so a user who had just
  cleared the preview saw an empty pane while those buttons still
  claimed "47 Matched File(s)" against no on-screen evidence, and
  clicking either button reopened a popup populated from the prior
  search. `_clear_preview` now mirrors the reset block already used
  at search start: hide both buttons via `pack_forget()` and drop
  the underlying `matched_files` / `_excluded_files` lists. Tooltip
  updated to advertise the new behavior.

- **Text View popup now follows the main app's screen on multi-
  monitor setups.** Double-clicking a file in the Matched Files popup
  opened the Text View popup with `win.geometry("900x720")` — size
  but no explicit position, so Tk picked a default (cursor's display
  on macOS, primary display's center on X11) that did not necessarily
  match where the rest of the workflow lived. A user on a laptop +
  external monitor setup with peekdocs on the external monitor saw
  the Text View pop up on the laptop. Fix: read the main app
  window's `winfo_rootx` / `winfo_rooty` / `winfo_width` /
  `winfo_height` before sizing and pass an explicit centered
  position; the OS window manager keeps the new window on the same
  screen as the main app. Wrapped in try/except so a coordinate-read
  failure falls back gracefully to the original no-position
  behavior.

### Changed

- **Structural audience-split audit follow-up.** The previous audit
  caught phrase-level violations (`power users`, `most users`,
  `intimidating`). This pass caught splits that were structural
  rather than phrase-level — places where ordering or implicit
  prioritization disadvantaged one audience even when the literal
  text was neutral. Four clear-tier fixes landed:
  - README's top-of-page install picker was running "Quick install
    (Python users):" first and "No Python? Download the standalone
    app" 33 lines below the demo block. A non-Python visitor reading
    top-down hit the "Python users" label first and could reasonably
    bail before reaching the standalone path. Restructured the top
    of the README as a numbered "Quick install" block — item 1 is
    the standalone download for non-Python users, item 2 is the
    pipx command for Python users.
  - Quick Start subsections reordered from Terminal → GUI → Python
    API to GUI → Terminal → Python API. The platforms banner
    advertises the canonical order as `GUI · CLI · Python API`; the
    subsections now match.
  - "Detailed use cases by role" `<details>` block reordered to lead
    with non-developer roles (Home users → Small businesses →
    Documentation teams → Researchers → Engineers → Data researchers
    → AI/ML engineers → Programmers) so a reader expanding the
    optional details doesn't read four developer-flavored entries
    first.
  - The in-app "WHO IS IT FOR?" help text in
    `peekdocs/gui/_mixin_tools.py` was leading with Developers; a
    home user opening Help inside the GUI saw "Developers" before
    themselves. Reordered to lead Home users → Small businesses →
    Researchers → Engineers → Legal → IT/Operations → Developers.
  - The "every available power-user feature" survivor of the
    previous audit at `README.md:213` swapped to "every Tools-menu
    feature" — describes the structural fact without the audience
    label.

- **Latent-compliance phrasing pass — three commits.** Started with
  "weekly compliance reviews" in the Diff Snapshots use-case list
  and grew into a focused sweep across the docs.
  THEORY_OF_OPERATION principle 7 forbids parking peekdocs in the
  regulatory drawer through use-case framing — not only the
  literal naming of HIPAA / SEC / FERPA / SSN that the previous
  audit caught, but also the more subtle "audits / reviews /
  compliance / audit trails" capability-pitch vocabulary. Five
  clear-tier swaps (`audits` / `reviews` in capability claims at
  `README.md:328` Schedule Search, `README.md:460` Search Suites,
  `docs/USER_GUIDE.md:543` Tools menu table, `README.md:377`
  Technical writers row, `docs/USER_GUIDE.md:2206` example code
  comment) and six borderline-tier swaps (four `"Weekly Audit"`
  → `"Weekly Code Scan"` API examples, `"audit trails"` →
  `"reproducible-output workflows"` in the Deterministic glossary
  entries, `"audits"` → `"completeness checks"` in the Inverse
  search glossary entry, `"vendor audit"` → `"release checklist"`
  in shell-loop examples, `"retention policy"` → `"license header"`
  in an inverse-search example, `"Audit Patterns"` →
  `"Code Patterns"` in a scheduled-task example). Defensive
  disclaimers using `compliance` / `forensic` / `evidence`
  vocabulary stay — they do the load-bearing "we are not this"
  disavowal work.

### Added

- **Three demo videos embedded in the README Screenshots area.** The
  static labeled screenshots are still there; the videos sit above
  them as a "watch the demos first" pair (now trio). All three use
  the same pattern — GitHub `user-attachments` upload (size cap 10 MB
  per file, the recompression line documented in the surrounding
  HTML comments produces ~1–3 MB files at 720p / 30fps), `<video>`
  tag with a poster image (the existing main-page screenshot for the
  hero, suite setup for the Suites demo, regex setup for the
  Regex demo), controls + muted + playsinline, and an `<a>` fallback
  link for feed readers that strip `<video>`:
  - **#### Watch peekdocs in action** — ~60s TODO search end-to-end:
    pick a folder, run the search, view highlighted results in the
    preview pane, browse the Matched Files list, open the
    auto-generated `.docx` report. Same workflow the static
    screenshots in section 1 break down.
  - **#### Watch Search Suites in action** — Code Hygiene suite
    end-to-end, with a caption note clarifying that "Code Hygiene"
    is ad-hoc for this demo (peekdocs ships no pre-built suites),
    that any number of suites can be defined, and that suites also
    run unattended via cron / Task Scheduler.
  - **#### Watch Regex Search in action** — a saved regex collection
    running, with a caption note on the 10-patterns-per-collection
    limit, the unlimited number of collections, and the
    `peekdocs --regex-collection` CLI surface that also composes
    into cron / Task Scheduler.
  - A new `### Labeled walkthroughs` H3 separates the videos from
    the static numbered screenshots so a reader scrolling down has
    an unambiguous "videos are over, here come the stills" signal.

- **PyInstaller / Gatekeeper startup tax glossary entry.** The phrase
  was used in the README's Screenshots disclosure note but defined
  nowhere. New `docs/GLOSSARY.md` entry names the two components
  (PyInstaller unpack + macOS Gatekeeper / XProtect / AMFI rechecks),
  gives per-platform numbers, notes that pipx skips both, and carries
  an inline `<a id>` anchor so the README's disclosure note can deep-
  link directly. A short Gatekeeper one-liner entry was also added,
  pointing readers at the compound term for the full breakdown.
  Both entries name Option A and Option B explicitly to match the
  README's install-picker vocabulary.

- **Hardware and install context note under Screenshots.** The
  screenshots show search times like 0.51s / 0.50s / 0.3s. A reader
  on different hardware would reasonably wonder whether those are
  achievable on a CI runner, a five-year-old laptop, or just on the
  developer's machine. Added a hardware-context italicized note
  upfront — MacBook Pro / Apple M4 Pro / 24 GB of memory — and a
  separate install-method note clarifying that peekdocs was running
  via pipx (Option B), not the standalone download. Closes one of
  the followups surfaced by yesterday's smoke-test debugging arc.

- **Diff Snapshots — preserving snapshots across recurring runs.**
  The Diff Snapshots section showed the demo command using manual
  filename redirection (`> snapshot-before.json` /
  `> snapshot-after.json`) but never explained why those names
  mattered. A reader thinking about their own recurring workflow
  hit a silent overwrite trap: each `peekdocs ... > snap.json`
  overwrites the previous file, so without distinct names or
  `--timestamp`, today's run has nothing to diff against last week's.
  New paragraph right after the demo block names the problem and
  the two ways to solve it (manual date-redirect or
  `--timestamp -o json`), and cross-links to Schedule Search which
  enables `--timestamp` by default for the same reason.

- **CI: GitHub Release body now pulls from the CHANGELOG.md section
  for the tag's version.** The release workflow was using
  `softprops/action-gh-release@v2` with `generate_release_notes: true`,
  which produced 79-byte bodies like "**Full Changelog**:
  ...compare...". The substantive narrative in CHANGELOG.md never
  made it to the release page. Added a checkout step + an awk-based
  "Extract CHANGELOG section for this release" step that parses the
  `## [<version>]` block matching the tag (stripping the leading "v")
  and passes it via `body_path` to `action-gh-release`.
  `generate_release_notes: true` is kept so the auto-generated
  compare link still appears after the body. Verified across a
  throwaway tag where the version isn't in CHANGELOG — the
  extraction produces an empty file and the action falls back to
  just the auto-generated notes, so existing throwaway-tag workflow
  patterns aren't broken. v1.0.22 is the first real release to
  exercise this path; the v1.0.21 / v1.0.20 release bodies were
  manually backfilled.

### Docs

- **Refreshed the `screenshot-searchsuite-result-mainpage.png`
  screenshot** to match the post-fix counts. The previous capture
  showed the pre-fix totals (`177 Matched Files` button label,
  `in 177 file(s)` status, `2225 file(s) searched`) — all artifacts
  of the Search Suites summing bugs fixed in this release. The new
  capture shows the corrected numbers all agreeing.

## [1.0.21] — 2026-06-07

Release driven by two real product fixes — a Windows non-TTY Unicode
crash and a macOS CLI standalone startup tax cut from ~5–7s to
~1–2s — plus a release-time CI gate that exercises the shell-binary
boundary on Windows, and a sweeping documentation accuracy pass
across the docs/ tree.

### Fixed

- **Python API `file_types="pdf,docx"` was silently buggy.** The
  signature declares `file_types: list[str]`, but the implementation
  at `peekdocs/api.py:199` does `set(file_types) if file_types else
  None`. Passing a string therefore became `set("pdf,docx")` — a
  set of single characters `{'p','d','f',',','o','c','x'}` — which
  extension-matched against parts of any filename containing those
  letters rather than rejecting the malformed input. Both
  `docs/API.md:96` and `samples/api_example.py:27` demonstrated the
  buggy idiom, teaching it to API consumers. Fixed both call sites
  to `file_types=[".pdf", ".docx"]`. The signature itself isn't
  tightened — that's a v1.1 break-the-API decision; for v1.0.21 we
  just stop demonstrating the wrong form.

- **First-experience demo command returned zero hits.** Both the
  README's "Want a quick demo first?" line and the USER_GUIDE's
  "Want to try peekdocs on a sample corpus first?" pitch told
  readers to run `cd samples/engineering_test && peekdocs TODO -r`
  — but none of the 38 sample files in that corpus contain the
  word `TODO`. A new user following the docs literally saw
  `Found 0 match(es) in 0 file(s)`, the worst possible first
  impression. Swapped to `peekdocs BUILD -r`, which finds 29
  matches across 5 language files (sh, tcl, vhd, vhdl, makefile)
  and shows the engine doing its job.

- **`line_proximity` and `use_whole_word` undocumented in source
  docstring.** Both are in the public `search()` signature at
  `peekdocs/api.py:60-83`, but the docstring at lines 87-128
  omitted them. `help(search)` now shows both; `docs/API.md`'s
  Parameters table got a fresh `line_proximity` row to match
  (the `use_whole_word` row was already there).

- **`run_suite()` `FileNotFoundError` missing from the Error
  Handling table.** The function's docstring at
  `peekdocs/api.py:458-466` listed three raised exceptions, but
  `docs/API.md`'s table only documented two (`KeyError`,
  `ValueError`). Added the missing row.

- **macOS Homebrew install command referenced a non-existent
  formula.** `docs/INSTALLATION.md` instructed macOS users to
  `brew install python-tk@3.14` in two places (lines 25 and 50),
  but no `python-tk@3.14` formula exists at the time of writing —
  only `python-tk@3.13`. A copy-paste user got
  `Error: No available formula`. Corrected both to `3.13`; the
  "replace with your version" hedge is preserved.

- **Windows non-TTY UnicodeEncodeError ('charmap' codec).** The CLI's
  `main()` had an `isatty()` guard on its `sys.stdout.reconfigure(...)`
  call, so the UTF-8 encoding switch only fired when peekdocs was
  attached to a real terminal. Every non-TTY invocation — `subprocess.run`
  with `capture_output=True`, shell pipes (`peekdocs ... | tool`),
  cron jobs logging to a file — left stdout on cp1252 and crashed with
  `'charmap' codec can't encode characters ...` the first time a CJK
  filename hit the progress bar or a regular `print(...)`. Caught by
  the new Windows smoke test (commit 4608237, marked xfail at the time);
  fix in `peekdocs/cli.py:643-657` removes the `isatty()` gate so the
  reconfigure runs unconditionally. The GUI's subprocess invocation
  already sets `PYTHONIOENCODING=utf-8` (`peekdocs/gui/_helpers.py:76`),
  so the unconditional reconfigure is an idempotent no-op for that
  path — no GUI-side change required.

- **Post-v1.0.20 README accuracy audit caught seven stale UI / count
  references.** Verified each against the actual code (`_mixin_build.py`,
  `cli.py`) and the README's own internal counts before fixing:
  - **"Tools → Search Suites" → "green Search Suites button on the
    main screen"** in three places (`README.md:364`, `:446`, `:711`).
    Search Suites was promoted from a Tools-menu item to a green
    main-screen button (verified `peekdocs/gui/_mixin_build.py:621`
    and the explicit comment at `:1552` "Search Suites moved to main
    screen next to Wizard").
  - **Wizard location**: `README.md:711` claimed both Wizard and
    Search Suites were "in the Tools menu" — both are actually
    main-screen buttons (Wizard at `_mixin_build.py:487`). Sentence
    rewritten to "the **Wizard** button on the main screen" and
    "both ... live on the main screen next to the search bar, not
    in the Tools menu."
  - **"Run Search" → "Run Standard Search"** across four lines
    (`:322, :708, :847, :711`). Actual blue button label is
    "Run Standard Search" (the `:15` and `:403` mentions already
    used the correct form; the others were inconsistent).
  - **"File button" → "Single File button"** (`README.md:706`).
    Actual button label is "Single File" per `_mixin_build.py:576`.
  - **"Regex Search ... GUI only"** (`README.md:356`) — Regex
    collections also run from the CLI (`peekdocs --regex-collection
    NAME`) and Python API (`run_regex_collection()`). The README's
    own line 27 and 404 already say so; the "GUI only" parenthetical
    contradicted them. Reworded.
  - **".docx report opens in ... Apple Pages"** (`README.md:152`) —
    contradicts the README's privacy stance (`:355, :383, :389`) that
    explicitly says peekdocs avoids opening reports in Apple Pages.
    Dropped Apple Pages from the demo opener list and added a
    pointer to the Report security section.
  - **"28 source-code and shell-script extensions"** (`README.md:314`)
    → **31**. The README's own Source Code table row at `:475` lists
    31 distinct extensions (asm, bat, c, cmake, cpp, cs, css, f, f90,
    go, gradle, h, hpp, java, js, kt, lua, pl, ps1, py, r, rb, rs, s,
    scala, scss, sh, swift, tcl, ts, vb). Updated.
  - **"Source code (48 languages)"** (`README.md:773`, grep
    comparison row) → **"Source code (31 extensions)"** to align
    with the actual count. The previous "48" matched neither the
    table nor reality.
  - **"11 search modes" but the list contains 12** (`README.md:357`
    and `:356`) — "quoted phrases" was added to the list in an
    earlier session without bumping the count. Updated both mentions
    from 11 → 12.

### Changed

- **macOS CLI standalone build mode: `--onefile` → `--onedir`.**
  Previously the macOS CLI binary was a PyInstaller `--onefile`
  build, meaning each invocation paid a ~2s self-extraction cost
  to `/var/folders/_MEIxxxxxx/` before any peekdocs code ran.
  Stacked with the ~3–4s of Gatekeeper / XProtect / AMFI rechecks
  that fire on every execution of an unsigned binary, total
  startup came to ~5–7s per invocation — the worst per-OS user
  experience in the project. Switching the macOS CLI to `--onedir`
  (matching how the GUI `.app` has always shipped) eliminates the
  self-extraction cost entirely; startup drops to ~1–2s, dominated
  only by the inherent macOS signing checks. User-facing impact:
  `peekdocs-cli-macos.zip` now contains a `peekdocs/` folder (the
  launcher binary at `peekdocs/peekdocs` plus an `_internal/`
  directory with bundled Python and libs) rather than a single
  binary. The README CLI download row, the `./` prefix-rule block,
  the `docs/SMOKE_TEST.md` macOS parity section, and the
  `docs/INSTALLATION.md` startup-time discussion are all updated
  to match. Windows and Linux continue to ship `--onefile` single
  binaries — the gap there is smaller and a single binary is the
  conventional CLI shape.

- **Audience voicing pass across README and USER_GUIDE.** Dropped
  six audience-splitting phrases that survived previous voice
  audits, plus six borderline talking-down phrasings:
  - Two `power users` audience-table headers (`README.md:279, :301`).
  - Three `most users` qualifiers (the Option A heading at
    `README.md:502`, "direct search is fast enough for most
    users" at `:847`, and "20-form Wizard for non-terminal users"
    at `docs/USER_GUIDE.md:576`).
  - One direct jab at `pip install` in the "No dependency breakage"
    paragraph (`README.md:559`).
  - Six borderlines: a praise-then-jab VS Code comparison
    (`README.md:312`), "no regex or technical knowledge needed"
    (`:362`), "no terminal experience required" in two parallel
    places (`:450` and `docs/USER_GUIDE.md:545`), an LLM-tradeoffs
    coda (`README.md:796`), "intimidating at first" terminal
    framing (`docs/USER_GUIDE.md:271`), and a "no more terminal
    commands needed" tail (`:425`).

- **Option A (Standalone Download) framing flipped.** The section
  heading changed from "recommended for most users" to "no Python
  needed", and the intro paragraph now explicitly steers
  Python-having users to Option B (pipx) with the per-platform
  startup-tax tradeoff surfaced ("starts noticeably faster —
  especially on macOS"). The
  `#option-a-standalone-download-no-python-needed` anchor replaces
  the old one; all four inbound references updated
  (`README.md:87, :485, :900`; `docs/INSTALLATION.md:15`).

- **CHANGELOG v1.0.0 release date.** Header said
  `## [1.0.0] — 2026-05-25`. The git tag is
  `2026-05-26 12:43:47 -0400` and the GitHub release is
  `2026-05-26T16:52:07Z` — both unambiguously May 26. Off by one
  day; corrected.

### Added

- **Release-time Windows smoke test gate.** Three components:
  - **`docs/SMOKE_TEST.md`** — a runnable cross-platform
    release-time checklist documenting what the existing
    630-test pytest matrix already covers (every internal
    Python code path on Windows + macOS + Linux × Python
    3.10-3.14) and what manual smoke testing catches (the
    shell-binary boundary).
  - **`tests/test_smoke_cli.py`** — seven pytest tests that
    invoke the built CLI via `subprocess.run` rather than the
    in-process `from peekdocs.cli import main` path. Covers
    `--version`, `--check`, backslash regex survival through
    shell parsing, shell wildcard handling (cmd / PowerShell
    pass `*` literally; peekdocs handles it), `-t pdf` vs
    `-t PDF` case parity, CJK filename round-trip through the
    UTF-8 report file, and a 20-second startup-time ceiling
    that catches a hung binary without policing performance
    variance the test can't control. Skips cleanly when
    `PEEKDOCS_BINARY` is unset or `sys.platform` is not
    `win32`, so an ordinary `pytest tests/` run is unaffected.
  - **`.github/workflows/build-release.yml`** — new Windows-only
    steps inserted between the PyInstaller build and the
    artifact upload. A smoke-test failure blocks the artifact
    upload; the `release` job depends on `build`, so a broken
    binary cannot publish. Adds ~30-60s of CI time to
    release-tag pushes. Proven across five throwaway-tag runs
    before being trusted with a real release: the gate caught
    real bugs in three of the five (the Windows charmap
    `isatty()` regression, a test-infrastructure encoding
    issue, and a CI-runner timing tolerance miss).

- **ocrmypdf coverage across the docset.** README's "Preparing
  Your Documents" section gets a new item walking through the
  per-platform install lines and a safe-to-rerun batch loop
  with `--skip-text`. A new `ocrmypdf` glossary entry lands in
  `docs/GLOSSARY.md`. `docs/USER_GUIDE.md` adds an OCR-bullet
  pointer and a matching glossary entry. `docs/TROUBLESHOOTING.md`'s
  "OCR is enabled but peekdocs doesn't find text" section closes
  with the ocrmypdf alternative. Voice rule consistent across all
  four surfaces: "peekdocs itself never modifies your PDFs;
  ocrmypdf is a separate tool you opt into for permanent
  conversion."

### Docs

- **Substantial accuracy pass across USER_GUIDE, TROUBLESHOOTING,
  API.md, INSTALLATION, GLOSSARY, and CHANGELOG.**
  - **PII-coded examples replaced with neutral patterns.** Two
    SSN-shaped regex examples in `docs/USER_GUIDE.md`
    (`\d{3}-\d{2}-\d{4}` in an inverse-search row and a
    `"has_ssn"` saved-search label) and three explicit "SSN
    pattern" mentions in `samples/api_example.py` swapped to a
    generic reference-number pattern (`\bREF-\d{4,}\b`). One
    additional structural SSN in `docs/API.md:213` (worded as
    "9-digit ID pattern" but using the 3-2-4 shape) replaced
    with a structured-reference example. Aligned with the
    project's long-standing rule of never naming regulated
    industries or PII categories in user-facing material.
  - **USER_GUIDE grep section reframed strengths-only.** Renamed
    from `## Why peekdocs Instead of grep?` to `## peekdocs and
    grep` and rewritten to describe what peekdocs adds for
    document-search workflows instead of what grep can't do.
  - **USER_GUIDE Search Wizard section restructured.** Previously
    described only the embedded regex pattern builder; now
    describes both levels — the top-level 20 pre-built search-
    type forms and the embedded sub-wizard with 35 regex
    patterns across 6 categories.
  - **USER_GUIDE stale version literals in JSON examples.**
    `peekdocs v1.0.4` (two places) and `1.0.0` (per-run log
    example) bumped to current.
  - **TROUBLESHOOTING numbered-list bug.** "OCR is enabled but
    peekdocs doesn't find text" had two consecutive items
    numbered `2.` (copy-paste artifact from when "Stale index"
    was inserted between "OCR not enabled" and "Tesseract not
    installed"). Renumbered the trailing items.
  - **CHANGELOG v1.0.4 git-tag gap explained.** v1.0.4 has a
    full CHANGELOG entry dated 2026-05-30 but no v1.0.4 git tag
    or GitHub release exists — `gh release list` jumps directly
    from v1.0.3 to v1.0.5. Added a parenthetical at the top of
    the entry noting the EXE-only ship and the direct succession
    to v1.0.5.

## [1.0.20] — 2026-06-04

### Docs

- **README voice: four soft-touch fixes for slightly overstated
  phrasings.** Audit prompted by "do we exaggerate anything?" —
  most claims hold up under scrutiny (verified "100+ file types"
  via `len(SUPPORTED_TYPES | OCR_IMAGE_TYPES) = 103`; "never
  modifies your files," "no telemetry," "11 search modes,"
  "three interfaces / one engine" all check out). Four passages
  used stronger words than the underlying truth strictly supports:
  - `README.md:132` — "works **equally well** on personal
    documents..." → "works **well** across..." Drops "equally"
    because search quality genuinely varies with file type
    (PDF text extraction quality, OCR accuracy on scanned docs,
    email metadata).
  - `README.md:333` — "See matches **instantly** inside peekdocs"
    → "See matches **right inside** peekdocs". Drops the marketing
    "instantly" — actual UX is 0.5s on indexed/warm, several
    seconds on cold/first-search.
  - `README.md:365` — "Build once, search in **sub-second time**"
    → "Build once, search in **typically sub-second time on most
    folders**". For 50,000+-file folders even indexed searches can
    exceed 1 second on result rendering — adds the "typically /
    most" hedge so the reader knows it's not a guarantee.
  - `README.md:383` — "Cloud-based apps (e.g., Google Docs, Apple
    Pages) are **never used**" → "...are **never used by
    peekdocs**." The original was strictly true *for peekdocs's
    behavior* but read as a global rule (users can still manually
    open peekdocs reports in cloud apps if they want; peekdocs
    doesn't prevent that). Three-word scope clarifier.

- **README readability pass — six denser passages tightened.**
  Follow-up to the v1.0.19 accuracy fixes. The same audit flagged
  six readability issues; this commit closes all of them:
  - **Programmers bullet** (~ 182 words → ~ 110): kept the VS Code
    framing and the auth-requirement anecdote, dropped the inline
    27-extension list (already in Supported File Types), and split
    the "search across codebases" content into its own paragraph.
    Updated the extension count from 27 → 28 to match
    `peekdocs/constants.py`.
  - **Built-in file analysis tools bullet** (was a wall with nested
    parentheticals + 4 em-dashes) converted to a 12-item sub-list,
    one tool per line. Also renamed "App Files" → "View All
    peekdocs Files" to match the actual Tools-menu label.
  - **Python library count claim** corrected — original said
    "about 50 packages, ~244 MB total" but actual runtime
    dependency closure is around 200 packages (verified by walking
    `importlib.metadata.requires()` from the 17 declared
    dependencies) and venv-on-disk is several hundred MB.
    Reworded to "around 200 packages and a few hundred megabytes
    of disk space."
  - **Windows CLI table cell** (113-word wall) split: cell now
    carries only the "run from download folder" path + a pointer
    to the new section below the table; the rename + PATH +
    PowerShell one-liner moved into a dedicated **"Windows: make
    `peekdocs` work from any terminal"** section with the
    one-liner as a fenced code block (4 separate lines instead of
    one inline string).
  - **`samples/engineering_test/` count** corrected from 35 to 38
    (the sample directory holds 38 distinct file types now, up
    from 35 when the prose was written).
  - **Terminal-section paragraph** (137-word run-on blending 6
    topics) split into 3 short paragraphs: where reports land →
    overwrite/keep semantics → which apps open the report.

### Fixed

- **README demo code didn't work when copy-pasted.** Two of the three
  examples in the top "What running peekdocs looks like" demo block
  silently failed for any user trying them:
  - The CLI demo `peekdocs "budget" ~/Documents` doesn't work — the
    CLI doesn't take a positional folder argument, so `~/Documents`
    was treated as a *second search term* and the search ran in the
    current working directory. Verified live: with cwd off the
    target, the example reports `Found 0 match(es)`. Fix: rewrote
    the CLI demo to `cd ~/Documents && peekdocs "budget"`, with an
    inline comment explaining that peekdocs searches the current
    directory.
  - The Python API demo `search(["budget"], directory="~/Documents")`
    returns 0 matches because the API does no `os.path.expanduser()`
    on `directory`. Verified live: the literal `~/Documents` is
    treated as a missing folder; expanding it via `os.path.expanduser`
    returns the real path and the search returns matches. Fix: added
    `import os` and changed the call to
    `directory=os.path.expanduser("~/Documents")`, with an inline
    comment ("pass a real path — no shell ~ expansion here").

### Docs

- **README cross-reference fixes from a v1.0.19 accuracy audit.**
  - Line 873 ("Corporate firewalls") pointed at *"the ZIP-based pipx
    install (described under Option B's 'No git?' subsection)"* — but
    the no-git ZIP install was removed from Option B in 7a112d9 and
    now lives only in `docs/INSTALLATION.md`. Repointed the link to
    `docs/INSTALLATION.md#no-git-install-from-a-downloaded-zip`.
  - Line 446 ("Read-only") said *"Tools → Clear Files, Delete Index"*
    which reads as if **Delete Index** were a sibling Tools-menu
    item. The actual Tools-menu entry is **Indexes**; Delete Index
    is the button inside the Indexes popup. Reworded as
    "Tools → Clear Files, Tools → Indexes → Delete Index(es)".

## [1.0.19] — 2026-06-03

### Docs

- **README "After download" column headers in the Direct GUI and
  Direct CLI download tables now link to "First-launch security
  warnings."** Users following the per-platform "after download"
  instructions hit OS-level security warnings on first launch
  (macOS Gatekeeper, Windows SmartScreen) that aren't mentioned
  in the table cell. Appended a clickable `*` to each "After
  download" column heading that jumps to the security-warnings
  paragraph below; added a matching `*` prefix to the destination
  heading plus an explicit `<a id="first-launch-security">` anchor
  so the link resolves regardless of how GitHub would slug the
  bold heading. Alerts the user before they commit to a platform's
  setup steps.

- **README top-of-file install instructions consolidated.** The top
  had drifted from "copy-paste-and-try" into a mini-Installation
  section: install command + Windows tip + a 40-line code block
  combining install / upgrade explanation / GUI prereqs / uninstall
  commands / usage examples, plus the "Two ways to install" framing
  with its bullets and follow-on standalone callout. All of that
  reference material was already documented in the dedicated
  Installation section (Option B), creating the awkward two-place
  spread a user flagged. Restructured the top to a focused
  copy-paste-and-try block:
  - **Quick install (Python users):** one-line `pipx install` command
    + a one-sentence "what it gets you" caption + a link to the
    dedicated Installation section for the standalone download,
    pip alternative, per-platform notes, upgrade, and uninstall.
  - **Windows tip** kept as an inline blockquote callout — moving
    it down would mean the user has to scroll to figure out why
    the very first command failed.
  - **What running peekdocs looks like:** the three-interface
    usage code block (search from terminal / GUI / Python API)
    split out from the install block so it scans as "demo" rather
    than "install command."
  - **No Python?** one-line pointer to the standalone download.

  All install/upgrade/uninstall reference material now lives in
  exactly one place — the dedicated Installation section's Option B,
  which gained the `pip install --upgrade` alternative, the
  `--force` / `--upgrade` semantics explanation, and the **GUI
  prerequisite** sub-bullets (`brew install python-tk@3.14`,
  `sudo apt install python3-tk`) that previously only appeared in
  the now-removed top install code block.

  Net: top of README dropped from ~50 lines of install content to
  ~25 lines, with no information loss — duplication eliminated.

## [1.0.18] — 2026-06-03

### Fixed

- **Suite search left stale standard-search results in the Results
  Preview pane.** When the user clicked **Run Search Suite** with a
  previous standard search's matches still on screen, the suite
  kicked off — status line correctly switched to
  `Suite: <name> (N searches)...` and the progress bar started — but
  the Results Preview pane kept showing the prior standard search's
  matches, including its Matched Files link, Excluded Files button,
  and the *"N match(es) in M file(s)"* count label above the preview.
  The contradiction (status says "suite running," preview shows
  unrelated keyword results from earlier) confused users about which
  search they were looking at. Two stacking causes:
  - `_run_suite_searches` didn't clear stale state at start — it
    only set the new suite-progress text on the status line. The
    standard-search start path does a state-reset block at
    `_mixin_search.py:215-220` (matched_files, inverse_results,
    action_buttons, files_list, preview, matched_files_link,
    excluded_files_btn). The suite path was missing all of it.
  - The `_preview_count_label` (the *"N match(es) in M file(s)"*
    header above the preview pane) is **not** touched by
    `_hide_preview()` — only `_clear_preview()` resets it, and the
    standard-search start uses `_hide_preview`. The reason it's
    not user-visible after a standard search is that the next
    `_show_preview()` call updates the count within a fraction of
    a second; the user never sees the stale count flash. But the
    suite takes seconds to run before its `_suite_finished` writes
    new content, so the previous standard search's count stays
    on screen for the whole suite duration.

  Fix: added a state-reset block to the top of `_run_suite_searches`
  in `_mixin_tools.py` mirroring the standard-search reset, plus an
  explicit `self._preview_count_label.configure(text="")` to close
  the count-label gap that `_hide_preview` leaves open. The Preview
  now goes fully blank (text + count) the moment the suite starts;
  only the suite's own combined results fill it back in when the
  suite finishes.

## [1.0.17] — 2026-06-03

### Docs

- **README voice: softened three "Most users / Power users" claims
  that conflicted with the actual audience.** The project's audience
  is developers landing on GitHub (per the user-audience memory; no
  advertising planned to general public), but three README passages
  defaulted to "Most users only need the GUI" / "Most users never
  leave the search bar. Power users can go deeper..." / "Most users
  won't need anything beyond the search bar" — modeling a GUI-only
  casual user as the default, which doesn't match the
  CLI-curious technical visitors who actually arrive here. Three
  edits:
  - `README.md:504` (Option A intro for GUI vs CLI standalones):
    "Most users only need the GUI. Download the CLI as well if..."
    → "Grab whichever fits how you'll use peekdocs — or both. The
    GUI is the click-driven interface for interactive search and
    report viewing; the CLI is for scripting from the terminal,
    running on a schedule (cron / Task Scheduler), and piping JSON
    output into other tools. They're independent — installing one
    doesn't require the other."
  - `README.md:252` (lead-in to the advanced-modes paragraph):
    "Most users never leave the search bar. Power users can go
    deeper with..." → "The search bar covers the common case; for
    more, peekdocs has..."
  - `README.md:686` (Wizard / Advanced Search section lead):
    "Most users won't need anything beyond the search bar — type
    your keywords..." → "The search bar covers the common case —
    type your keywords..."

  Other "Most users / Most people" mentions in README and INSTALLATION
  were audited and left as-is — they model real majorities about
  general human behavior or genuinely niche features (privacy
  intuition, accumulated digital files, OCR being niche, standalone
  vs pipx for users without Python, indexing for users who can
  search large folders fast enough without it).

## [1.0.16] — 2026-06-03

### Docs

- **GLOSSARY: added six Linux command entries.** Inserted in
  alphabetical order to cover every Unix command that appears in
  peekdocs's installation, troubleshooting, and uninstall paths.
  Each entry follows the existing single-row format with a brief
  definition, peekdocs-specific usage examples, and a note about
  the Windows equivalent where applicable:
  - **apt** (between API and Binaries) — Debian/Ubuntu package
    manager used for `sudo apt install python3-venv python3-pip
    python3-tk` etc. Includes pointers to dnf / pacman / zypper
    for other distros.
  - **chmod** (between Boolean expression and CI pipeline) —
    used to mark the Linux standalone binaries executable
    (`chmod +x peekdocs-gui-linux`).
  - **chown** (between chmod and CI pipeline) — used in Linux
    permission-troubleshooting (`sudo chown -R $USER /path`).
  - **mv** (between MSP technician and OCR) — used by the
    `sudo mv ... /usr/local/bin/peekdocs` global-install step
    on macOS and Linux.
  - **rm** (between requests and Sandbox) — used by the
    Uninstalling section's `sudo rm /usr/local/bin/peekdocs`
    and factory-reset `rm -rf ~/peekdocs_reports`.
  - **sudo** (between Stemming and Symlink) — used everywhere
    install instructions touch system directories or install
    packages.

- **Documentation currency audit and cleanup pass.** A post-v1.0.15
  audit caught residual stale UI references after the rapid v1.0.5–
  v1.0.15 iteration. All user-facing accuracy gaps resolved:
  - **"Manage Indexes" everywhere → "Indexes"**. The Manage Indexes
    collapsible toggle below Advanced Search Options was removed
    when the controls were moved to a Tools menu popup labeled just
    **Indexes** (see `_mixin_build.py:1549`). Renamed across
    `README.md` (1 occurrence), `docs/USER_GUIDE.md` (5),
    `docs/TROUBLESHOOTING.md` (4), and in-app help text in
    `_mixin_tools.py:3952`.
  - **`docs/USER_GUIDE.md` main-screen region table** had a
    "Manage Indexes" row describing a collapsible toggle that no
    longer exists (removed). The "Toolbar" row listed buttons that
    are now Tools-menu items (View All peekdocs Files, All
    Collections, Error Log, Maintenance, Text Size) — rewritten as
    "Bottom row" with the actual buttons (README / User Guide /
    Close / Tools ▲ / Tooltips / About) and a note that
    everything else moved into the Tools menu.
  - **`docs/USER_GUIDE.md` "Manage Indexes:" subsection** rewritten
    to describe the Tools → Indexes popup instead of a collapsible
    panel below Advanced Search Options.
  - **`docs/USER_GUIDE.md:2454`** "Clear Error Log on the bottom
    toolbar" — no such button exists; replaced with the
    Tools → Clear Files path.
  - **In-app Tools-menu help (`peekdocs/gui/_mixin_tools.py`)**:
    three stale references to UI labels ("Clear Results",
    "Delete Index" singular, "Clear Error Log", "Click Manage
    Indexes below Advanced Search Options") updated to point at
    current Tools-menu paths.
  - **Test count claims**: `README.md:950` "627 pytest tests" →
    630 (actual count after v1.0.10's `test_version_flag_double_dash`
    + `test_save_flag_double_dash` and v1.0.14's
    `test_check_success_footer`). `CLAUDE.md:50` "559 tests" → 630.
  - **`python-tk@<version>` consistency**: README and TROUBLESHOOTING
    used `@3.14`; INSTALLATION and USER_GUIDE used `@3.13`.
    Standardized on `@3.14` across all four files; INSTALLATION's
    "replace 3.13 with your version" parentheticals updated to
    match.

## [1.0.15] — 2026-06-03

### Fixed

- **`peekdocs --check` showed `(v?)` for every dependency in the
  standalone bundles.** v1.0.14 added a `v` prefix to make the
  parenthesized version unambiguous (`ok (v1.27.2.3)` instead of
  `ok (1.27.2.3)`). A user testing the v1.0.14 macOS CLI standalone
  reported the output was literally `ok (v?)` — a question mark
  where the version number should be. Root cause: PyInstaller does
  *not* ship `.dist-info` directories into bundles by default, so
  `importlib.metadata.version(pkg)` fails at runtime, and the
  `_get_pkg_version` fallback returns `"?"` (`peekdocs/cli.py:392`).
  This is the same problem peekdocs's own version already worked
  around at `peekdocs/__init__.py:13` via a hardcoded fallback —
  and `build_app.py:95` already did `--copy-metadata peekdocs` to
  ship peekdocs's metadata. The dep metadata was never copied.
  Fix: added a `COPY_METADATA` list to `build_app.py` covering all
  12 packages (peekdocs + 7 required deps + 4 optional deps) and
  threaded it into both `build_gui` and `build_cli` so each
  produces `--copy-metadata <pkg>` flags for the PyInstaller
  invocation. The list is documented as the single source of truth
  with a comment pointing at `peekdocs/cli.py:_REQUIRED_MODULES`
  / `_OPTIONAL_MODULES` to keep in sync. After this fix the
  v1.0.15 standalone CLI's `--check` output will read
  `ok (v1.27.2.3)` for every dep on every platform, matching what
  the pipx-installed CLI already shows.

## [1.0.14] — 2026-06-03

### Changed

- **`peekdocs --check` output: `v` prefix on version numbers and an
  `All checks passed.` success footer.** A user testing the CLI on
  all three platforms observed that each dependency line read
  `ok (1.27.2.3)` — the parenthetical value with no label was
  ambiguous (could be mistaken for a question mark or unknown
  value). And when every check passed, the output ended silently
  after the disk-space line, forcing the reader to scan every
  individual line to confirm nothing said MISSING. Two fixes in
  `peekdocs/cli.py`:
  - Dep lines now read `ok (v1.27.2.3)` — the `v` makes the
    parenthetical unambiguously a version number.
  - Success path now ends with `All checks passed.`, mirroring the
    failure path's existing `Fix missing dependencies with: pip
    install --upgrade peekdocs` footer so the output has a closing
    message either way.
  Regression-guard tests in `tests/test_cli.py`: existing
  `test_check_shows_versions` now asserts `"ok (v"` (was `"ok ("`),
  and a new `test_check_success_footer` asserts exit code 0 +
  `"All checks passed."` is present + the failure-path footer is
  NOT present.

## [1.0.13] — 2026-06-03

### Docs

- **README Option A: explicit `./` / `.\` prefix rule + concrete
  Windows global-install commands.** Two related additions a user
  asked for:
  1. A blockquote callout under the Direct CLI downloads table
     explaining the prefix rule across the three OSes — macOS /
     Linux need `./peekdocs ...`, Windows PowerShell needs
     `.\peekdocs-cli-windows.exe ...`, Windows cmd.exe accepts
     the bare name. Reason given: shells search `$PATH` (`$env:Path`
     on Windows) for executables, and current directory isn't on
     PATH by default on macOS / Linux / PowerShell as a security
     measure.
  2. The Windows CLI table row now includes the concrete
     PowerShell one-liner for global install (Rename-Item to
     `peekdocs.exe`, create `$HOME\bin`, move there, append to
     user PATH via `[Environment]::SetEnvironmentVariable`), so
     a Windows user gets the same `peekdocs "query" /path` UX
     from any terminal that the macOS row already documented via
     `sudo mv /usr/local/bin/peekdocs`.

## [1.0.12] — 2026-06-03

### Docs

- **GLOSSARY: added "Shim" entry.** Inserted between Search suite
  and SIEM (alphabetical: Search → Shim → SIEM). Covers what a
  shim is (a small wrapper executable forwarding calls to a real
  program), how pipx uses shims for peekdocs
  (`~/.local/bin/peekdocs` invoking `python -m peekdocs.cli:main`
  in the isolated venv), and why this matters in context — the
  pipx shim's near-zero startup (~0.2–0.5s) versus the PyInstaller
  standalone's 5–7s on macOS, because there's no bundled Python
  to unpack. The standalone has no shim layer; you run the bundled
  executable directly.

## [1.0.11] — 2026-06-03

### Docs

- **CLI standalone startup time docs corrected and broadened to all
  platforms.** A user testing v1.0.10 on macOS reported `peekdocs
  --version` taking 6.56 seconds (timed via `time`) — well beyond
  the "1–3 seconds" the original INSTALLATION.md section claimed.
  The 1–3s estimate was based on PyInstaller unpack alone and
  missed macOS XProtect / AMFI / Notarization overhead, which adds
  3–4 seconds on every execution of an unsigned binary. Updated
  `docs/INSTALLATION.md#macos-cli-startup-slowness` (now renamed
  more honestly to "CLI standalone startup time — what to expect
  per platform (especially macOS)") with:
  - A per-platform expectations table: macOS 5–7s, Windows 2–4s,
    Linux 0.5–1.5s, with what contributes to each.
  - Explicit explanation of why macOS is so much slower (XProtect
    + AMFI + Notarization on every execution of an unsigned binary;
    Linux has no equivalent layers; Windows Defender is similar
    but faster and better-cached).
  - New "Why the GUI standalone has no equivalent delay" subsection
    explaining the PyInstaller `--onedir` vs `--onefile` build
    asymmetry visible in `build_app.py:63` (GUI is `--onedir`,
    files already unpacked inside the `.app` bundle) vs `build_app.py:94`
    (CLI is `--onefile`, extracts on every invocation). Same user
    noted no GUI delay on macOS — this explains why.
  - Diagnostic guidance now reads zsh's `time` output honestly
    (zsh drops the `s` suffix on the `total` column, which threw
    the user off) and explains the user-vs-system-vs-wall-clock
    interpretation (low CPU % + high total = waiting on macOS
    security, not slow peekdocs).
  - pipx startup-time claim revised from "0.2–0.4s" to "0.2–0.5s
    on any OS regardless of macOS's security overhead" because
    the pipx path bypasses XProtect/AMFI entirely (no unpacked
    binary for macOS to inspect).

## [1.0.10] — 2026-06-03

### Fixed

- **`peekdocs --save my_report` had the same bug pattern as
  `--version`: it ran a search for the literal string "--save"
  instead of saving the previous run's results.** The CLI's
  save-flag check at `peekdocs/cli.py:1107` matched only `-s` and
  `-save` (single dash). When a user typed the GNU/POSIX-conventional
  double-dash form `peekdocs --save my_report`, the check fell
  through to the search code and treated `--save` as a literal
  search term — wiping the existing results files and replacing
  them with a search for `--save`. Fix: added `--save` to the
  matched options at `cli.py:1107`, matching the same pattern
  the `--version` fix used. Test: added `test_save_flag_double_dash`
  in `tests/test_cli.py` that calls `main(["--save"])` (no filename
  argument), asserts exit code 2 with the "No filename provided"
  error, AND asserts "Searching" is *not* in the output. Audit
  of every other manual `args[0]` flag check in `cli.py` confirms
  this was the only remaining parallel — `-h`/`-help`/`--help`
  was already covered, and every other flag (`--check`, `--clear`,
  `--diff`, `--runs`, `--suite`, `--regex-collection`, etc.) uses
  only the GNU `--<flag>` convention, which is what users type
  anyway.

- **`peekdocs --version` ran a full directory search instead of
  printing the version and exiting.** The CLI's version-flag check
  at `peekdocs/cli.py:850` only matched `-v` and `-version` (single
  dash). When the user typed the GNU/POSIX-conventional double-dash
  form `peekdocs --version`, the check fell through and the search
  code path treated `--version` as a literal search term: it
  printed its own startup banner (which a user could easily
  mistake for the `--version` output), then ran a recursive scan
  of the current working directory looking for files containing
  `--version` — and wrote `peekdocs_standard_results.txt` and
  `.docx` reports to disk as a side effect. A user testing the
  v1.0.8 macOS CLI standalone in their Documents folder reported
  a 442-file / 806 MB scan in 3.6 seconds when they expected a
  one-line version print.

  Fix: added `--version` to the matched options at `cli.py:850`,
  matching the same `-h` / `-help` / `--help` triple already
  used for `is_help` two lines above. Now `-v`, `-version`, and
  `--version` all print `peekdocs {VERSION}` and exit 0 without
  touching the filesystem.

  Test: added `test_version_flag_double_dash` in `tests/test_cli.py`
  to lock in the fix — explicitly asserts the output contains the
  version string AND does *not* contain "Searching" (the search
  code path's startup signature).

## [1.0.9] — 2026-06-03

### Docs

- **macOS CLI standalone startup slowness documented.** A user
  installed the macOS CLI to `/usr/local/bin/peekdocs` via
  `sudo mv` and found every invocation took 1–3 seconds. Root
  cause is two stacking issues: (1) PyInstaller single-file
  bundles unpack their bundled Python interpreter + dependencies
  on each invocation, which is inherent to the format and
  unavoidable for the standalone CLI; (2) `sudo mv` preserves
  the `com.apple.quarantine` xattr, so macOS Gatekeeper re-
  verifies the binary at the new path on every launch, adding
  cost on top of the unpack. New
  `docs/INSTALLATION.md#macos-cli-startup-slowness` section
  covers both, with: `sudo xattr -dr com.apple.quarantine
  /usr/local/bin/peekdocs` as the one-shot fix for the avoidable
  half; a `time peekdocs --version` diagnostic to distinguish
  cold-cache slowness from inherent unpack cost; and pipx as
  the faster alternative (~0.2–0.4s startup vs 1–3s for
  standalone) for users who care about per-command latency.

- **macOS CLI binary filename corrected in the README CLI table.**
  The macOS CLI zip (`peekdocs-cli-macos.zip`) contains a binary
  named just `peekdocs`, not `peekdocs-cli` as the README
  previously stated. The workflow at `.github/workflows/build-release.yml:59`
  packages it as `zip peekdocs-cli-macos.zip peekdocs`, so the
  README's `cd ~/Downloads && ... peekdocs-cli` line silently
  failed for any user following the literal instructions.
  README CLI table macOS row updated to use the correct
  filename, plus added the post-`sudo mv` `sudo xattr -dr
  com.apple.quarantine` step (with a "this matters for startup
  speed" callout) and a link to the new slowness section.

## [1.0.8] — 2026-06-03

### Docs

- **README "Uninstalling" section added; upgrade-without-uninstall
  made explicit.** A user asked whether they need to uninstall an
  earlier version before installing a new one and how to uninstall
  generally. The README's existing `### Upgrading` section covered
  what's preserved but had no parallel `### Uninstalling` section
  and didn't say "no uninstall needed before upgrade." Three
  updates:
  - Option A's inline "Upgrading." paragraph now leads with
    "No need to uninstall the old version first — just download
    the new version ... and overwrite the existing file" and
    links to the new Uninstalling section for full removal
    instructions.
  - The `### Upgrading` section's per-method bullets each add
    a short clarifying clause ("No need to uninstall first" for
    standalone; "`--force` overwrites cleanly; no separate
    uninstall step" for pipx).
  - New `### Uninstalling` section right after Upgrading covers
    all four install paths (standalone GUI/CLI per-OS commands,
    pipx, pip, source install) and a "Factory reset (complete
    wipe)" subsection with copy-pasteable bash and PowerShell
    one-liners to remove every persisted user-data file
    (`~/.peekdocsrc`, history, bookmarks, `~/peekdocs_reports`,
    per-folder `.peekdocs_collection.json` / `.peekdocs.db*`).

- **GLOSSARY: added "Binaries" entry.** Inserted between API and BOM
  (alphabetical: Bi precedes Bo). Covers what binaries are (compiled
  executables that don't need Python), how many peekdocs ships (six —
  GUI and CLI for Windows / macOS / Linux), the PyInstaller bundling
  rationale, and the pipx alternative.

- **Documentation audit cleanup pass.** A readability + accuracy
  audit caught residual references to the removed Delete Now button
  and a couple of stale UI claims:
  - USER_GUIDE "How to delete" line replaced "Click Clear Results on
    the bottom toolbar" (no such button) with the current
    Tools → Clear Files → Choose Files / Wipe Session paths.
  - Tools menu sub-list in USER_GUIDE corrected "Clean Up Practice
    Files" to "Clean Folder".
  - In-app Tools-menu help (`_mixin_tools.py:7757`) updated from
    "click Delete Now on the main screen" to
    "use Tools → Clear Files → Wipe Session".
  - Timestamp checkbox tooltip (`_mixin_build.py:926`) updated from
    "use Delete on Close or Delete Now to clean up" to the Tools →
    Clear Files → Wipe Session path.
  - README intro bullet line 23 now says "offers a one-click Wipe
    Session (under Clear Files)" rather than the vague "lets you
    delete them in one click".
  - README line 317 "delivers all of them in a single install" was
    a stale claim equivalent to the line 59 one fixed in 1.0.7;
    softened to "delivers all of them in one tool".
  - README macOS Gatekeeper bullet (line 529) was a 110-word
    single-sentence wall; reformatted into a numbered list for the
    three System Settings steps, then a single follow-up paragraph
    for the per-download caveat and terminal alternative.

## [1.0.7] — 2026-06-02

### Docs

- **README intro corrected: "single install gets you everything" is
  pipx-only.** The intro line claimed a single install gives you the
  GUI, CLI, and Python API — true for `pipx install`, but the
  standalone download path bundles GUI and CLI as separate binaries.
  A user testing v1.0.6 hit this when they downloaded the GUI `.app`
  and found no CLI bundled in. Reworded as: "A single pipx / pip
  install gets you everything — the GUI, the CLI, and the Python
  API all from one command. (The standalone download path bundles
  them as separate binaries — pick the GUI, the CLI, or both as
  needed; see Option A below.)"

- **Option A split into separate GUI + CLI download tables.**
  Previously: one "Direct downloads" table for the GUI plus a
  paragraph cramming the three CLI binaries inline. Now: a
  "Direct GUI downloads" table (existing content) and a parallel
  "Direct CLI downloads" table with the same Platform | Download
  | After-download structure. Each CLI row includes the platform-
  specific invocation (`cd`, `chmod`, `xattr -dr com.apple.quarantine`,
  PowerShell quirks via cross-link), and an "optionally rename and
  put on PATH" tip so users get the same `peekdocs "query" /path`
  UX from any terminal that pipx-install users get. Short intro
  above the tables explains who needs the CLI separately ("script
  peekdocs from the terminal, run it from cron / Task Scheduler,
  or pipe its JSON output into other tools") so most readers
  correctly skip the CLI table.

- **"Why two standalone binaries instead of one?" rationale added
  to Option A.** Inline paragraph right after the "separate
  downloads" sentence covers: PyInstaller bundle has one entry
  point; combining would force the CLI to carry tkinter /
  customtkinter or the GUI to carry CLI-only argument-parsing
  surface; the pipx / pip path doesn't have this constraint
  because it drops both `peekdocs` and `peekdocs-gui` console
  scripts into one shared venv. Anchor link to Option B for
  readers who realize "single command for both" is what they
  actually want.

## [1.0.6] — 2026-06-02

### Fixed

- **Searches re-discovered legacy `peekdocs_results.*` report files
  as user documents.** Commit `492583a` (2026-05-23) renamed report
  files from `peekdocs_results.*` to `peekdocs_{standard,regex,suite}_results.*`
  to stop the three search modes from silently overwriting each
  other's reports. That rename also dropped `"peekdocs_results"`
  from the scanner's `_EXCLUDE_PREFIXES` set, replacing it with
  the three new prefixes via `RESULT_FILE_PREFIXES`. Folders that
  had been searched by any pre-rename peekdocs version still
  contain files like `peekdocs_results.html`, `.json`, `.pdf` —
  and v1.0.4 / v1.0.5 picked them up as user documents and
  searched their contents. A user running `peekdocs budget` saw
  three "matches" that were just words from earlier search reports.
  Added `"peekdocs_results"` back to `_EXCLUDE_PREFIXES` in
  `peekdocs/scanner.py:971` as a legacy-compatibility prefix.
  Scoped to **search exclusion only** — not added to
  `RESULT_FILE_PREFIXES` because the cleanup paths
  (Delete on Close, Wipe Session, etc.) shouldn't silently sweep
  files a user may have intentionally kept from a pre-rename
  install. The comment explains the legacy rationale so the
  prefix doesn't get garbage-collected by a future cleanup.

### Docs

- **macOS Gatekeeper bypass clarified as per-download, not per-app.**
  Original phrasing claimed the bypass was "one-time per app" with
  upgrades not re-triggering Gatekeeper "as long as the bundle ID
  stays the same." That's the rule for *signed* apps with an Apple
  Developer ID — peekdocs is unsigned, so macOS attaches a fresh
  `com.apple.quarantine` xattr to every downloaded copy regardless
  of bundle ID. Every upgrade re-triggers the same warning. README
  and `docs/INSTALLATION.md#macos-gatekeeper` now explicitly say
  the bypass is per downloaded file, the warning fires again on
  each new download (including upgrades), and recommend the
  Terminal `xattr -dr com.apple.quarantine` one-liner for users
  who upgrade often.

- **macOS first-launch Gatekeeper walkthrough rewritten for Sequoia
  / Sonoma.** A user testing the v1.0.5 standalone `.app` reported
  that the warning dialog on a recent macOS only offered **Done**
  and **Move to Trash** — no **Open** button — so the README's
  "right-click → Open" instruction left them stuck. Three changes:
  - README `Option A` Gatekeeper bullet rewritten to describe the
    modern System Settings → Privacy & Security → Open Anyway path
    as the primary route, with the `xattr -dr com.apple.quarantine`
    one-liner as the no-terminal-detour alternative. Also notes
    that Safari auto-unzips downloads, so users see
    `peekdocs-gui.app` directly in Downloads rather than the
    `.zip` they clicked.
  - New `docs/INSTALLATION.md` section (anchor `macos-gatekeeper`,
    placed at the top of "Niche install paths") with three paths
    (System Settings, Terminal one-liner, right-click → Open for
    older macOS), per-macOS-version notes, the Safari auto-unzip
    explanation, and a per-download (re-triggers on upgrade) note.
  - README's Gatekeeper bullet links through to the new
    INSTALLATION.md section for the full walkthrough.

## [1.0.5] — 2026-06-02

Documentation right-sizing pass, a round of GUI polish and safety
hardening for destructive actions, a main-screen button rename for
honest labeling, and two performance-relevant bug fixes
(`api.search` no longer wastes 30+ seconds per call on a silently
failing index rebuild when index metadata and current params don't
match; CLI `-qq` now actually honors "minimal output" by suppressing
the Searching announcement, spinner thread, progress bar, and final
completion line in addition to the banner).

Documentation: README trimmed from ~1,240 lines to ~920 (-26%) by
moving deep-reference material into /docs companion files, while
keeping every selling point inline. Added a privacy-first
justification callout, a typical-workflow GUI-path clarifier, and
honest fixes to a few claims that had drifted out of sync with the
source.

GUI: layout fixes (Advanced Search Options auto-fits to content,
Schedule Search popup slightly taller, Error Log viewer gains a
Clear Log button, white bar around System Check Copy to Clipboard
removed, About dialog aligned with workbench framing); main-screen
button rename so labels match behavior ("Run Search Suites" ->
**Search Suites**, "Run Regex Search" -> **Regex Search** because
both open management popups rather than executing immediately); and
safety hardening on the four destructive actions (Clean Folder,
Delete Now, Delete Index, Restore Factory Settings) — each now
spells out scope, says "this cannot be undone", and reports failures
rather than swallowing them silently.

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

- **Main-screen button rename: "Run X" -> "X" for the popup-openers.**
  "Run Search Suites" -> **Search Suites**, "Run Regex Search" ->
  **Regex Search**. Only Run Standard Search keeps the "Run" prefix
  because it's the only main-screen button that actually executes
  on click — the other two open management popups. Reinforced by
  the recent in-popup rename to **Run Search Suite** (singular,
  the actual immediate-run action inside the suites popup): having
  a "Run Search Suites" button that opens a popup containing "Run
  Search Suite" read as "click Run to open Run".

  Side effects: the main-screen hyperlink "3 Run Buttons — what's
  the difference?" became "3 Search Buttons — what's the
  difference?"; button widths shrank to 200 each (was 260 for Suites
  and 240 for Regex Search — both now visually identical); the
  in-popup execute buttons are unchanged (they really do run); the
  Getting Started Step 3 text and the Standard Search button
  tooltip were updated to use the new names; both buttons' hover
  colors were set equal to their fg colors so they no longer darken
  on hover (the in-popup execute buttons keep their darker hover
  feedback). README's typical-workflow clarifier was rewritten to
  match. The main-page and CLI screenshots in docs/images/ were
  recaptured and committed (b8ee5fd, 7d42b9c) along with caption
  updates for the new file count and elapsed times. CHANGELOG
  entries referencing the old labels in historical release notes
  are deliberately left untouched.

### Fixed

- **Suite Matched File(s) button showed inverse zero-match files
  after a mixed normal+inverse suite.** A suite with two sub-searches
  (e.g. "bowling" normal + "bowling" inverse) correctly showed
  `9 Matched File(s)` on the main page and a correct Results Preview
  and .docx report, but clicking the Matched Files button opened a
  popup listing only the zero-match files from the inverse sub-search.
  Root cause: `_suite_finished` rebuilt `self.matched_files` by
  re-reading `peekdocs_standard_results.txt` from the search folder
  after the run — but each sub-search subprocess overwrites that file,
  so the re-read only ever saw the last sub-search's output. When the
  last sub-search was inverse, the file's "Files WITHOUT matches:"
  section parsed (correctly, by design) into count=0 entries, and
  those populated the popup. Fix: aggregate `parsed_files` across all
  `sections` (each section's `parsed_files` was already captured in
  `_run_suite_searches` before the next subprocess overwrote the
  file), filtering to count>0 so inverse sub-searches contribute
  nothing. The status label was already right because it sums each
  section's `matched_file_count`, parsed from stdout's "match(es)
  in N file(s)" line — a line an inverse run never prints.

- **macOS popups stayed dark after switching the app to light mode.**
  Regex Search, Search Suites, Wizard, and other popups that go
  through `_themed_toplevel` were destroyed by `_set_appearance_mode`
  when the user switched modes — but when re-opened in light mode,
  their plain tk widgets (tk.Text, tk.Listbox, tk.Canvas) still used
  dark colors. Root cause: `_themed_toplevel` called `win.option_add`
  for two dozen tk widget defaults, but only inside an
  `if _is_dark and platform != "win32":` block. tk's `option add`
  writes to Tcl's *application-wide* option database (not per-window),
  so values set during a dark-mode popup persisted in the option DB
  after that popup was destroyed. The next popup opened in light mode
  ran no option_add calls and inherited the stale dark values. Windows
  was unaffected because the entire block was gated behind the
  platform check. Fix: always set mode-appropriate option_add values
  on Mac/Linux (introduced an explicit light-mode color set:
  `#f0f0f0` bg, black fg, white entry/text bg, `#e1e1e1` button bg).
  Dark-mode startup white-flash mitigation (`win.geometry("+99999+99999")`
  + `_ensure_onscreen` safety net) still runs only in dark mode.

- **Delete Now button removed from the main page; its function moved
  into Tools → Clear Files as a "Wipe Session" tab.** The main page
  previously had three "delete files" entry points (Delete Now button,
  Delete on Close checkbox, and Tools → Clear Files), which were each
  individually justified but together created a "too many options"
  feeling. The Delete Now button is gone; the popup formerly known as
  "Clear Files" is now a two-tab CTkTabview:
  - **Wipe Session** tab (default on open when there's anything to
    wipe) replicates the old Delete Now behavior exactly — deletes
    all peekdocs result files and search indexes across every folder
    searched this session plus saved-config folders and
    `~/peekdocs_reports`, clears the Results Preview, deletes
    `~/.peekdocs_history.json`, clears recent searches, and blanks
    the Search Terms + Folder fields. The tab body lists the affected
    folders and what gets deleted vs. what's preserved before the
    user clicks the red Wipe Session button. One Yes/No confirm
    follows.
  - **Choose Files** tab is the existing per-file picker for the
    current Search Folder, unchanged.
  - The default tab on open is Wipe Session when there are session
    folders to wipe, otherwise Choose Files.

  Files touched: removed `_delete_everything_now` from
  `_mixin_search.py`, removed `_delete_everything_btn` creation in
  `_mixin_build.py` and its pack/pack_forget call sites in
  `_app.py:117`, `_mixin_search.py:1014` (post-search) and
  `_mixin_search.py:1032` (`_clear_action_buttons`), refactored
  `_clear_files` into the tabbed structure, updated the Tools menu
  label from "Clear Files — choose which peekdocs files to delete"
  to "Clear Files — wipe session files or choose specific files to
  delete", and updated the Delete on Close tooltip to point at the
  new Wipe Session path for mid-session cleanup. README.md,
  docs/USER_GUIDE.md, and docs/SECURITY.md mentions of "Delete Now"
  renamed to "Wipe Session" with the Tools → Clear Files path
  appended where the location was previously "main screen". Older
  CHANGELOG entries describing the historical Delete Now button
  are left as-is — they're a point-in-time record.

- **Delete Now and main-page Close button spaced apart to prevent
  misclicks.** The main page had two single-click destructive (or
  app-ending) buttons sitting near the horizontal center of the
  bottom area: **Delete Now** in the report-button row (red, drops
  indexes and deletes session reports) and the main-page **Close**
  button at the bottom row (exits peekdocs). Popup Close buttons,
  when popups were centered, also fell near that same center
  column — so dismissing a popup and quickly clicking again could
  land on either main-page button. Two coordinated moves:
  - Delete Now's left padding bumped from `padx=(30, 0)` to
    `padx=(400, 0)` in both pack call sites (`_app.py:117` startup
    placement and `_mixin_search.py:1180` post-search re-pack),
    shifting it to the right end of the report row.
  - Main-page Close button (`close_main_btn` in `_mixin_build.py`)
    moved out of `bottom_frame` column 1 (centered) and into the
    existing `left_frame` group, packed `side="left"` after the
    README and User Guide buttons. It now sits with the other
    navigation buttons at the left of the bottom row.

  The two main-page buttons are now at opposite horizontal ends,
  with popup Close buttons (still centered) in between but separated
  from both.

- **Advanced Search Options popup opened at 100px tall on Windows.**
  `_build_advanced_panel` sets the popup's initial geometry to
  `900x100`, then computes the actual content height after laying
  out its widgets and re-applies it with
  `advanced_window.geometry(f"900x{content_h}")`. Both calls happen
  while the window is withdrawn. On Windows, geometry changes
  against a withdrawn Toplevel may not commit until `deiconify()`,
  so when `toggle_advanced` later read `advanced_window.geometry()`
  to compute the popup's centered position, Windows returned the
  initial `"900x100"` instead of the resized value — the popup
  opened at 100px tall. macOS Aqua commits the change immediately,
  so the same code worked there. Fix: cache the computed height as
  `self._advanced_size = (900, content_h)` in `_build_advanced_panel`
  and use that directly in `toggle_advanced`, instead of parsing the
  withdrawn window's `geometry()` string.

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

- **`api.search` no longer silently fails a doomed rebuild on every
  search when the index's stored `max_file_size_mb` doesn't match
  the current parameter.** Previous behavior: the rebuild check
  fired `build_index()` inside `try: ... except Exception: pass`,
  the rebuild silently failed (on a 449-file/806 MB folder it was
  burning 30-60s every search without surfacing why), and the meta
  was never updated so it kept failing. New behavior: detect the
  mismatch, set `SearchResult.index_stale_notice` with a
  human-readable explanation, and let the user run `peekdocs
  --index` explicitly when they're ready. CLI prints the notice
  after Found/Elapsed; GUI status line condenses it to
  `— index settings out of sync (run --index to refresh)`. The bare
  `except Exception: pass` is gone — any future regression in
  `index_status()` now surfaces its error in the same field.
  Added `SearchResult.index_stale_notice: str = ""` field;
  documented in API Reference, USER_GUIDE Search Index section,
  and TROUBLESHOOTING.

- **Context-line searches with the index are ~67x faster.** Setting
  Lines Before > 0 or Lines After > 0 used to trip
  `_can_use_fts5_fast_path` into returning False, sending the
  search through `_parse_cache_search` — which iterates every
  indexed file and reads every paragraph of every file from the
  DB. On the same 449-file / 749K-paragraph workload, the reported
  search went from ~27 seconds (context = 5) to 0.40 seconds; the
  context-0 baseline is unchanged at 0.33 seconds. New behavior:
  FTS5 still finds the matching paragraphs, then a single targeted
  range query per matched file (`WHERE file_id = ? AND line_num
  BETWEEN ? AND ?`) fetches the surrounding lines, and
  `scanner.apply_context` does the same grouping the non-indexed
  path uses — output shape (file_dir, filename, first_match_line,
  joined text) is identical. Added a `(file_id, line_num)` index on
  the paragraphs table to the schema; older indexes built before
  this change get it created idempotently on the first context
  search without needing a rebuild.

- **GUI status no longer shows "Rebuilding index with new Max File
  Size, then searching..." when no rebuild fires and Max File Size
  wasn't touched.** Since the `api.search` stale-notice fix above,
  no rebuild actually happens during a search; meanwhile the GUI's
  separate pre-search probe was still labelling the wait as caused
  by Max File Size — even when the user had only changed context
  lines or hadn't touched anything in Advanced Search Options at
  all. The probe is gone. The post-search `index_stale_notice`
  surfaces the real condition (config-vs-meta mismatch) in the
  status-line suffix where it belongs. The now-dead
  `current.startswith("Rebuilding index")` branch in
  `_update_elapsed` was removed as well.

- **CLI `-qq` now honors "minimal output" as the help text claims.**
  The help string says `-qq` shows "only Found/Elapsed lines (no
  file list, warnings, or report paths)," but four call sites in
  `cli.py` gated their output on `not stdout_json` alone, so `-qq`
  still printed the `Searching ({mode}) on [...] ...` announcement,
  started the spinner thread, ran `_cli_progress` with its rolling
  progress bar, and printed the final `[done]` render. With the
  fix, all four sites also gate on `not minimal`. Terminal output
  under `-qq` now actually matches the screenshot in the README
  (just Found / Elapsed).

- **Delete Now tooltip flicker loop with tooltips enabled.** A long
  `anchor="above"` tooltip on the Delete Now button could overlap
  the button after Tk's `winfo_height()` returned a partial value
  during measurement, causing the cursor to "fall under" the
  tooltip, fire `<Leave>` on the button, schedule a hide, then
  re-fire `<Enter>` 150 ms later when the tooltip disappeared —
  an endless Enter/Leave loop. Two defenses: the Delete Now
  tooltip was shortened from ~600 to ~310 characters (the
  confirmation dialog already lists everything; the tooltip just
  needs a hover hint), and `peekdocs/gui/_tooltip.py` now clamps
  `tip_h` to at least 60 px and widens the safety gap above the
  widget from 6 px to 24 px so even a partial height measurement
  can't put the tooltip on top of the widget.

- **Inverse-mode state persisting across searches.** Three related
  defects produced the reported "Inverse persists even after being
  unchecked" symptom (commits 1552123, 7ee7acf, fe1c491):
  (1) `_hide_preview` only grid-removed the frame, leaving
  highlighted-match content from the previous search in the Text
  widget for any later code path to display; (2) `_show_preview`
  guarded the inverse-render block on
  `self._inverse_results AND self.matched_files`, falling through
  to highlighted-match rendering when `matched_files` was empty —
  including the exact "Inverse on, status says no matches, preview
  shows highlighted matches" inconsistency the user observed; and
  (3) the `returncode == 1` "no matches" path never refreshed
  `_inverse_results` or `matched_files` from the current checkbox
  state, and hardcoded the matched-files link to red (the
  inverse-mode color). Now `_hide_preview` clears the Text widget,
  `_show_preview` always uses inverse layout when
  `_inverse_results` is True (with an empty-state message when no
  inverse files are returned), the `returncode == 1` branch
  refreshes both fields and uses inverse-state-appropriate link
  colors, and `.txt` / `.docx` result files are unconditionally
  deleted at search start so a returncode-2 recovery branch can't
  parse the *previous* search's report and display it as the
  current one's. Together these close every path through the
  inverse-toggle plumbing that could carry stale state forward.

- **Advanced Search Options popup opened on the wrong monitor.**
  Every other Tools popup uses `_center_popup_on_main` to
  re-center on the main window's screen each time it opens. The
  Advanced popup just called `deiconify()` + `lift()`, leaving it
  wherever Tk first placed it — typically the laptop's primary
  monitor even when the main window had been dragged to a second
  display. `toggle_advanced` now reads the popup's already-fit
  width and height and computes centered coordinates relative to
  the main window's `winfo_rootx/y` before deiconifying. Last
  popup that wasn't in the multi-monitor sweep.

### Docs

- **Windows cmd.exe SSL / SNI / certificate-error gotcha documented.**
  A Windows user reported that `pipx install --force git+...` and
  `pip install ...` both fail in **Command Prompt** with an SSL /
  SNI / certificate-validation error, but succeed in **PowerShell**.
  Root cause is environmental: the two terminals can route through
  different Python installs (cmd.exe often finds the Microsoft Store
  Python stub or an older system Python with a stale `certifi` / CA
  bundle, while PowerShell finds the real install). Added a new
  section in `docs/INSTALLATION.md` (anchor `windows-cmd-ssl`)
  covering the diagnosis (`where python` in cmd vs `Get-Command
  python` in PowerShell, env-var comparison), the simplest fix (use
  PowerShell), the pip+certifi refresh path, and an emergency
  `--trusted-host` override with a clear "don't leave this in your
  habit" caveat. The README's "Two ways to install" bullet list
  also picks up a one-line Windows tip linking through to the new
  section, since that's where a Windows user lands when the install
  fails the first time.

- **README pipx install commands now uniformly include `--force`.**
  A Windows user followed the README's bare `pipx install
  git+https://github.com/exbuf/peekdocs.git` command and got
  `ModuleNotFoundError` because `pipx install` is a no-op when the
  package name is already present — it does not re-fetch the git URL
  or re-resolve dependencies, so the user kept running an old commit
  that lacked newer modules (`peekdocs.diff`, mixin files, etc.).
  All `pipx install <git-url>` examples in the README now use
  `--force` (developer-install bullet at line 55, install code block
  at line 62, FAQ "How is it installed?" at line 885), and the
  install code block consolidates the previously-separate "Reinstall
  or upgrade" subsection — the same `--force` / `--upgrade`-flavored
  command serves both purposes, with an inline note explaining why
  the flag matters. The canonical Option B install (line 533) and
  the Upgrading section (line 556) already used `--force`. INSTALLATION.md
  unchanged — it already used `--force` throughout.

- **TROUBLESHOOTING "Why is my first search slow but later searches
  are fast?" FAQ distinguishes two causes.** The existing entry
  only covered first-time index build cost. Users who already have
  an index built reported a second kind of first-search slowness
  (~2.5 s first, ~0.5 s subsequent) with no rebuild in between.
  Expanded to cover both: (1) first index build for a brand-new
  folder; (2) cold OS filesystem cache on the first invocation in
  a session, plus Python interpreter startup paid by each fresh
  invocation, plus `refresh_index`'s `os.stat()` pass hitting disk
  before the directory cache warms. Steady-state performance is
  the sub-second figure; the first-search penalty is the price of
  being absent from the OS cache. Mitigation: pre-warm via a
  scheduled `peekdocs --index-refresh` at login. README's
  First-run timing section gets a matching cold-cache paragraph
  with a pointer to the FAQ.

- **Screenshots section reframed from "Same search, four ways" to
  "Same search, three interfaces — plus the report."** The auto-
  generated Word report is the *output* of a search, not a fourth
  way to perform one. Heading and lead now match the existing
  "Three interfaces, one engine" framing in Feature Highlights.
  Sub-block labels (a)/(b)/(c)/(d) and their content unchanged.

- **`-B N` / `-A N` and GUI Lines Before / Lines After now spell out
  what "line" means across file formats.** AND mode (`-a`) and line
  proximity (`-P N`) docs already explained that "line" varies by
  format — paragraph for Word/PDF, row for Excel, literal line for
  plain text and source code — but the Lines Before / Lines After
  flag had inherited the same ambiguity without the explanation.
  Updated in USER_GUIDE flag table, CLI `-h` help text, both GUI
  tooltips on the Advanced Search Options entry fields, and the
  API Reference `context_before` / `context_after` parameter rows.
  No behavior change — just disclosure that on paragraph-heavy
  formats a small `-B` / `-A` value can pull in several sentences
  or pages of surrounding text.

- **"Why I built this" in the Author section rewritten.** The
  previous one-line three-clause version ("I needed it, I wanted an
  AI learning project, and sharing it cost nothing") understated
  every part of the story. Replaced with a three-sentence narrative
  that names the concrete problem (searching large collections of
  mixed-format documents locally, privately, and efficiently), the
  real ambition (exploring what a single developer can build with
  today's AI-assisted tools), the dogfooding step ("After relying
  on it in my own workflow"), and the share decision under MIT.

- **`docs/images/screenshot-advanced-screen.png` recaptured** after
  the Advanced Search Options auto-fit fix in 433a5ec. The panel
  now sizes to its actual content without the ~200 px of empty
  space below Reset All Fields that earlier captures showed.

- **"3 Search Buttons — what's the difference?" popup tightened
  for accuracy and reach.** Opening sentence updated from
  "three Run buttons" to "three Search buttons" to match the
  post-rename main-screen labels and "(Step 1)" added to the
  folder reference for clarity. Two accuracy fixes: Standard
  Search regex was described as "a single regex term" but the
  code supports multiple patterns (replaced with "regex (one or
  more patterns)"), and "above the run-buttons row" was stale
  vocabulary (changed to "above the search-buttons row"). New
  paragraph between the Regex Search section and the closing Tip
  notes that Search Suites and Regex Search collections can both
  be run on a schedule via Tools → Schedule Search. Popup width
  bumped from 720 → 820 px so the tightened body has room to
  breathe.

- **"Can't find a file you expected?" tip relocated to three
  discoverable places.** Previously buried five layers deep
  inside README's "Who Is It For?" section (Highlighted Results →
  Results Preview → sub-bullet), where the user who hit the
  problem couldn't find it. Now lives in: README's Screenshots
  section as a blockquote under the GUI screenshot caption; a new
  TROUBLESHOOTING.md FAQ entry "I searched for a term I know is
  in a file, but the file doesn't appear in my results — what
  happened?" adjacent to the report-cap entry, with a three-part
  answer covering scroll position, overly broad query (with
  AND / proximity / expression remedies), and excluded files; and
  USER_GUIDE.md "Results Preview vs. Reports" section with a
  back-link to the FAQ entry.

## [1.0.4] — 2026-05-30

*(EXE-only release; no `v1.0.4` git tag exists — `gh release list` skips from v1.0.3 to v1.0.5. The standalone GUI and CLI binaries described below were built and published, but the tag was never created. v1.0.5 succeeds it directly in the tag history.)*

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

## [1.0.0] — 2026-05-26

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
