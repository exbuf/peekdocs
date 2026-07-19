# Changelog

All notable changes to peekdocs are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Versions are listed in reverse chronological order (newest first). Each release groups its changes under **Added** (new features), **Changed** (modifications to existing behavior), **Removed** (features taken out), and **Fixed** (bug fixes).

**To upgrade to the latest version:**

- **pipx** (recommended, Mac / Linux / Windows): `pipx upgrade peekdocs` (or `pipx install git+https://github.com/exbuf/peekdocs.git` for a first-time install)
- **pip** (advanced): `pip install --upgrade git+https://github.com/exbuf/peekdocs.git`
- **Standalone download**: grab the new file from the [Releases page](https://github.com/exbuf/peekdocs/releases/latest) and replace your existing copy. Your settings and saved searches live in your home directory, not in the executable — nothing is lost on upgrade.

## [Unreleased]

### Added
- **MCP setup helper — generate and (optionally) write the LM Studio
  `mcp.json` so an AI assistant can drive peekdocs.** Available three ways,
  all sharing one core module (`peekdocs/mcp_setup.py`): (a) `peekdocs-mcp`
  CLI flags — `--print-config` (prints the config, writes nothing),
  `--write-lmstudio-config` (merges peekdocs into `~/.lmstudio/mcp.json`,
  preserving any other servers and backing the file up first), `--setup`
  (interactive: opens a native folder picker when no `--root` is given, then
  writes the config), and `--config-path FILE` (write to a host's mcp.json
  elsewhere); (b) the folder picker inside `--setup`; and (c) a new GUI
  Tools-menu dialog, **"AI Assistant Setup (MCP)"**, with a folders list,
  editable config-file path, OCR/subfolders/index/backup toggles, and
  Write / Copy to clipboard / Save-to-file buttons. As a failsafe, the CLI
  and GUI never create `~/.lmstudio` behind your back — if LM Studio isn't
  installed they show the config instead of writing it.
- **New `peekdocs-mcp` server defaults `--recursive`, `--ocr`, and
  `--allow-index`.** These set the default behavior for tool calls that don't
  specify the value (an assistant can still override per call). `--allow-index`
  is the only one that writes anything — a `.peekdocs.db` in searched folders —
  and is off by default, keeping the server read-only.
- **MCP tool responses now report the folder searched — so an AI assistant
  can state its scope accurately.** *Found while testing the MCP server
  through an AI assistant:* when the assistant summarized a search it could
  describe its coverage as the whole working/launch directory (e.g. "I
  searched all of your Documents folder") when it had in fact only searched
  the fenced `--root`. peekdocs's results were correct and correctly scoped —
  the overstatement was the *assistant's narration*, because the tool
  responses never told it **where** the search actually ran, so it inferred
  the location from its working directory. Fix: every directory-scoped tool
  (`search_documents`, `get_document_context`, `inventory_folder`,
  `run_search_suite`, `run_regex_collection`) now returns a
  `searched_directory` field — the exact resolved folder searched (the
  server's `--root` unless a `directory` argument is passed) — and
  `search_documents`'s description tells the model to describe scope from that
  value. With the ground truth in hand, an assistant reports the real root
  (and distinguishes it from the working directory) instead of overstating
  coverage. Additive and backward-compatible.
- **Truncated MCP responses now carry a plain-language `note` explaining the
  cut.** *Found while testing through a local model:* when results were capped,
  the assistant told the user they were truncated "due to time constraints or
  file size limits" — both invented; the real and only reason is the
  `max_results` cap. peekdocs was already returning the machine fields
  (`truncated`, `total`, `returned`), but the model reconstructed a cause from
  the bare numbers and guessed wrong. Fix: on truncation the response envelope
  now includes a ready-made sentence — e.g. *"Showing 25 of 47 results — capped
  by max_results (25). To see more, ask to narrow the request … or raise the
  max_results limit."* — and `search_documents`'s description tells the model to
  relay the `note` verbatim rather than guess. Assistants reliably pass along a
  supplied sentence but tend to confabulate from raw counts. Additive and
  backward-compatible.

### Changed
- **Generated MCP configs now suggest `--max-results 25` by default (down from
  the server's own 200).** *Found while testing through a local model:* a
  broad search (a term appearing in many files) returned up to 200 matches,
  and feeding all of them into a small local model's context window overflowed
  it — LM Studio raised *"request exceeds the available context size."* Since
  an AI assistant reads every returned match, 200 is tuned for scripts/CLI, not
  for a chat context. The setup helper (`--print-config`, `--setup`,
  `--write-lmstudio-config`, and the GUI dialog) now writes `--max-results 25`,
  small enough to fit a typical local window; users can raise it. The **running
  server's** own default is unchanged at 200 — only *generated configs* changed.

### Docs
- **MCP data-flow diagram** (e623640, f27550a, `README.md`,
  `docs/USER_GUIDE.md`). Added a "How the flow works" diagram to the
  User Guide's MCP section and a compact version to the README,
  showing the round-trip request path (assistant → `peekdocs-mcp` →
  deterministic search → matches carrying file + line → assistant)
  and attributing the summarizing/citing step to the AI host, not
  peekdocs.
- **"AI-agnostic and stateless by design" subsection**
  (e623640, daef946, `docs/USER_GUIDE.md`). Documents that the server
  calls no model and works with any MCP host, and that each tool call
  is self-contained with no cross-call state — the only persistence is
  the fixed startup policy (`--root`, `--max-results`) and the opt-in,
  off-by-default index. Verified against `mcp_server.py`; wording
  tightened afterward for precision.
- **README MCP intro reframed around local models**
  (66eb0c4, ca9ab63, `README.md`). The MCP section now leads with
  pairing a free local model (Llama/Qwen/Mistral via Ollama or
  LM Studio) and peekdocs's data-stays-local promise; a cloud
  assistant such as Claude Desktop or Claude Code is noted as an
  option, with the caveat that only the local setup keeps your data
  entirely on your machine.
- **AI-assistant framing in the intro and audience list**
  (a1fb998, bae2722, `README.md`). The intro flags the optional
  AI-assistant interface (via MCP) as a single clause, and "Who Is
  peekdocs For?" gained an AI-assistant bullet with per-persona
  plain-language example queries.
- **Heading rename** (c7c2ecb, `README.md`, `docs/USER_GUIDE.md`).
  "Who Is It For?" → "Who Is peekdocs For?", with the two internal
  links to its anchor updated.

## [1.2.86] — 2026-07-10

### Added
- **Optional read-only MCP server (`peekdocs-mcp`).** A [Model Context
  Protocol](https://modelcontextprotocol.io) server that lets any
  MCP-capable AI assistant — Claude Desktop, Claude Code, and
  local-model hosts (LM Studio, Ollama-based clients) — search local
  documents over the same `peekdocs.api` engine the CLI and GUI use. It
  is a thin adapter, so an assistant's search returns the same matches
  your own would. Install with the optional extra
  (`pip install "peekdocs[mcp]"`) and run over stdio. Eight read-only
  tools: `search_documents`, `get_document_context`, `inventory_folder`,
  `list_supported_file_types`, `list_search_suites`, `run_search_suite`,
  `list_regex_collections`, `run_regex_collection` — with **no** write,
  move, rename, delete, or report-generation surface (those code paths
  are never imported by the server).
  - **Guardrails.** `--root DIR` is **required** and confines every
    search to the folders you name; out-of-root and path-traversal
    requests are rejected. `--max-results` caps results per call with a
    truncation notice. Searches never write the on-disk index by
    default; opt in per call with `allow_index_write`.
  - **Privacy.** peekdocs stays local and initiates nothing (the
    exchange is one-way — the assistant asks, peekdocs answers; the MCP
    "sampling" capability is deliberately not implemented). A *cloud*
    assistant still receives the returned snippets as part of the
    conversation; pairing with a *local* downloadable model (Llama,
    Qwen, Mistral) keeps everything on your machine.
  - **New public API helpers** `inventory_folder()` (+ the
    `FileInventoryItem` dataclass) and `list_supported_file_types()`,
    re-exported at the top level
    (`from peekdocs import inventory_folder, list_supported_file_types`),
    back the folder-listing tools.
  - Documented across the README (Feature Highlights, "How these
    compose", "Why peekdocs?"), the User Guide (setup, "Who benefits"
    with per-persona examples, one-way/sampling and data-locality notes,
    and a fully-local downloadable-model setup), the API reference, and
    the Glossary.
- **Schedule Search dialog — `?` help panel and Close button (GUI).**
  The Schedule Search dialog (Tools menu) gained a `?` help button, the
  only Tools dialog that lacked one. Its panel explains what the feature
  does and why peekdocs generates a scheduler command for you to paste
  rather than registering the schedule itself (the OS scheduler owns the
  job; peekdocs stays out of your system). The help popup also gained a
  Close button, matching the other help panels.
- **Internal documentation link check in CI.** New
  `scripts/check_doc_links.py` (stdlib-only) plus a `doc-links` CI job
  verify that every internal Markdown link resolves — the target file
  and, for `.md` targets, the `#anchor` against the target's real
  heading slugs / explicit HTML anchors. A broken internal link (missing
  file or renamed/removed anchor) now fails CI.

### Fixed
- Fixed 5 broken internal documentation links (anchors left stale by
  renamed / renumbered sections, plus a glossary term that needed an
  explicit anchor).
- CI `mypy` job no longer fails on recent numpy's PEP 695 `type`
  statements in its bundled stubs — a numpy-scoped `follow_imports`
  override skips the stub that mypy rejected under the
  `python_version = "3.10"` target. (Pytest was never affected.)

## [1.2.85] — 2026-07-07

### Changed
- **Type-check gate widened to `scanner.py` + `indexer.py` — the
  engine is now type-checked end to end.** The two largest
  untyped modules (scanner: file discovery + extraction for 100+
  formats; indexer: SQLite FTS5 build / refresh / search) carry
  full top-level signatures and sit in the mypy CI gate (14
  files, was 12). The whole engine path — api → cli/commands →
  scanner → indexer → reporter — is now covered; only GUI mixins
  and small helpers remain deliberately out of scope. The
  checker forced real internal fixes: a mixed tuple/list ranges
  list in `apply_context`, variable reuse across scanner's
  per-format extraction branches, and a `result` variable in
  `cli._main_inner` that held an index-stats dict and a
  `SearchResult` at different points. Also removed a latent
  footgun: `_dry_run_report`'s file-filter params claimed to
  accept a bare `str`, which `discover_files` would have
  iterated character-wise.
- **Asset sweep.** Orphaned `hero.gif` (3.2 MB, replaced by
  hero2) and never-embedded `screenshot-getting-started.png`
  removed; RELEASE_CHECKLIST updated to track only embedded
  assets.

## [1.2.84] — 2026-07-07

### Changed
- **License popup widened 560 → 700px.** The MIT text's
  ~75-character lines soft-wrapped in Courier 10 at the old
  width; 700px renders every line unwrapped. Height unchanged.
- **New hero clip.** The top-of-README walkthrough replaced with
  a re-recorded version (`hero2.gif`); caption updated to the new
  run's stats (10,412 files in 2.98s) and retitled "A Standard
  Search" to match the clip's name on the maintainer's site.

## [1.2.83] — 2026-07-06

### Changed
- **README top-of-file restructure.** Installation moved from line
  434 to ~line 159; Quick Start follows immediately. The hero clip
  (46-second walkthrough: 10,411 files searched in 3.17s, File
  Types + Categories charts) is now the above-the-fold visual, and
  the Contents (TOC) moved from line 556 — where it navigated
  nothing — to right before Installation, rebuilt in document
  order. Installation subsections reordered to Option A → Option B
  → Prerequisites → Upgrading → Uninstalling with a numbered nav
  list matching numbered headings (anchor fragments rewritten
  across README, USER_GUIDE, and TROUBLESHOOTING). A follow-up
  cold-read audit fixed seven orphaned references the moves left
  behind (stale "below" pointers, a stranded duplicate
  Quick-install block, a footnote marker with no referent, and a
  "(one-time, per platform)" claim its own section's body text
  contradicted — now "(per download, per platform)").
- **Repo-root hygiene.** 18 stray local files (old sample docs,
  logs, search outputs, legacy `docsearch_*` artifacts) and four
  build directories deleted; `.gitignore` extended with annotated
  blocks for dev-scratch patterns, local WIP demo videos, and
  personal sample corpora. None of it ever shipped (sdist audit
  confirmed setuptools' `packages.find` scope holds) — this is
  maintainer-workbench discipline, not a shipping fix.

## [1.2.82] — 2026-07-06

### Fixed
- **About → View License now finds LICENSE in pipx / pip installs.**
  User reported on 1.2.81 that the pipx install on macOS showed
  "LICENSE file not found in this build" — same fallback text as
  the 1.2.80 `.app` bug, but different root cause. pipx installs
  place LICENSE in the sibling `.dist-info/licenses/` directory
  (PEP 639's `license-files` mechanism via setuptools ≥ 77), not
  inside the peekdocs package itself. `resource_path` deliberately
  doesn't chase into `.dist-info/` per its docstring, so the About
  viewer hit the fallback. New universal
  `peekdocs.paths.read_bundled_text(name)` helper tries three
  sources in order — `resource_path`, PEP 639
  `.dist-info/licenses/<name>`, legacy pre-PEP-639
  `.dist-info/<name>` — covering LICENSE, NOTICE, and
  THIRD_PARTY_NOTICES.md across every install method (pipx, pip,
  editable, PyInstaller `.exe`, `.app`, source checkout).

## [1.2.81] — 2026-07-06

### Fixed
- **About → View License now finds LICENSE in the macOS `.app`
  bundle.** User reported on 1.2.80 that both the standalone macOS
  `.app` and Windows `.exe` showed "LICENSE file not found in this
  build" instead of the actual MIT text. Diagnosed by inspecting
  the released binaries: LICENSE ships correctly at
  `peekdocs-gui.app/Contents/Resources/LICENSE`, but
  `sys._MEIPASS` on a PyInstaller `--onedir --windowed` `.app`
  bundle points at `Contents/Frameworks/` (runtime + libs), so
  the traditional `os.path.join(sys._MEIPASS, "LICENSE")` lookup
  missed the file entirely. Extended
  `peekdocs.paths.resource_path()` to search a small ordered
  candidate list — `_MEIPASS/relative_path` first (works on
  Windows, Linux, macOS CLI), then
  `_MEIPASS/../Resources/relative_path` (macOS `.app` fallback)
  — and return the first candidate that exists on disk. If
  neither exists, returns the traditional path so the caller's
  own "not found" fallback still runs cleanly. 4 new tests cover
  the multi-candidate lookup logic.

## [1.2.80] — 2026-07-06

### Fixed
- **PyInstaller-frozen GUI now streams stderr phase markers in
  real time.** User reported on 1.2.79 that the standalone `.exe`
  and the pipx install find identical results, but the `.exe`
  status line skipped the report-writing progression
  ("building txt report", "building docx report") that the pipx
  install showed. Root cause: the frozen path in
  `peekdocs.gui._cli_runner._run_peekdocs_cli` redirected stderr
  into a plain `io.StringIO()` that was only readable after
  `_cli_main` returned, so every `print("PHASE: ...",
  file=sys.stderr, flush=True)` in `cli.py` got buffered and the
  GUI never saw intermediate markers. Fix: new
  `_StderrLineStreamer(io.StringIO)` subclass that intercepts
  writes, buffers partial lines, and forwards completed
  newline-terminated lines to `on_stderr_line` synchronously —
  matches the subprocess path's background-reader behavior.
  `getvalue()` at the end still returns the full transcript, so
  any completion-time consumer of the buffered stderr keeps
  working. 7 new tests cover the streaming logic including CRLF
  handling and callback-exception swallowing.

## [1.2.79] — 2026-07-06

### Added
- **`peekdocs.errors` — public exception hierarchy for library
  consumers.** New module exports `PeekdocsError` (root),
  `QueryError` (bad search input — invalid mode combinations, empty
  terms, malformed regex, boolean-expression syntax), `RangeError`
  (malformed `-R` range spec), and `NameNotFoundError` (missing
  suite or regex collection). Each subclass inherits from the
  closest stdlib exception (`ValueError` / `KeyError`) so existing
  consumer code that catches those types keeps working — this is a
  non-breaking upgrade for anyone already handling errors from
  `peekdocs.api`. Re-exported from the top-level `peekdocs` package
  for import convenience. Raise sites in `api.py`, `range_query.py`,
  and `expr_parser.py` (32 total) now raise the typed subclasses
  instead of raw stdlib exceptions.
- **`peekdocs/commands/` package** — extracted six self-contained
  CLI subcommand handlers from `cli.py`'s `_main_inner`
  mega-dispatcher into focused per-subcommand modules. Phase 1:
  `--check`, `--diff`, `--runs`. Phase 2: `--list-files`,
  `--list-suites`, `--clear` / `--clear-all`. Establishes the
  extraction pattern for future subcommand splits; `cli.py` reduced
  by 215 LOC cumulative (2781 → 2566, -8%). Standard search +
  `--suite` + `--regex-collection` + `--watch` + the `--index-*`
  cluster remain in `cli._main_inner` because they share
  flag-parsing plumbing that spans several output-format branches
  — factoring that shared surface cleanly is its own larger
  refactor. See `commands/__init__.py` for the "adding a new
  subcommand" pattern + the circular-import defense (lazy imports
  of `peekdocs.cli` symbols inside handler bodies).
- **`peekdocs.gui._error_guard` — controlled exception swallowing.**
  New module ships two context managers replacing the ~149
  ambient `except Exception: pass` sites across the GUI mixins:
  `gui_guard(operation)` swallows AND logs the exception name +
  traceback tail to `peekdocs_errors.log` with the operation
  label; `gui_race_guard()` swallows silently for known Tk
  timing races (grab_set-on-not-yet-viewable, focus_set on
  destroyed widget) where a companion retry-with-`after()`
  handles correctness. Four persistence sites in `_mixin_data.py`
  (factory-reset rc-file remove, config write, history-file
  clear, bookmarks save) converted as pattern demonstration; the
  remaining conversion is one-at-a-time future work.
- **API reference row for public exceptions** in `docs/API.md`
  quick-reference table (was previously implicit; scanners of the
  top-of-page table now find `peekdocs.errors` there).
- **GLOSSARY.md entries** for `PeekdocsError`, `QueryError`,
  `RangeError`, `NameNotFoundError` — each row names the module,
  the raise sites, and the stdlib back-compat inheritance.

### Changed
- **Byte-formatter consolidation.** Three drifting implementations
  (SI 1000-based in reports + CLI, IEC 1024-based in the GUI file-
  analysis dialogs) collapsed to a single `peekdocs.paths.format_bytes`
  helper — SI decimal is now the peekdocs convention across every
  user-visible surface. A 2 100 000-byte file used to show as
  "2.10 MB" in reports and "2.00 MiB" in the dupe finder; both now
  render identically. `reporter.fmt_size` becomes a thin re-export
  for back-compat with `peekdocs.reporter.fmt_size` importers.
- **Type-check gate widened to 12 files.** All six `commands/`
  handlers plus `peekdocs.errors` plus `gui/_error_guard.py` are
  now in mypy scope, bringing the CI-typed public surface to
  `api.py`, `paths.py`, `reporter.py`, `cli.py`, `errors.py`,
  `commands/check.py`, `commands/diff.py`, `commands/runs.py`,
  `commands/list_files.py`, `commands/list_suites.py`,
  `commands/clear.py`, and `gui/_error_guard.py`. Docs updated on
  four surfaces (README, USER_GUIDE, ARCHITECTURE, CLAUDE) to
  reflect the wider scope.
- **`gui/_helpers.py` split into three focused modules.** The
  former 850-LOC grab-bag identified in the code-health review
  became `_cli_runner.py` (subprocess + command build + result
  parsing, 478 LOC), `_cloud_guard.py` (cloud-folder detection +
  policy guard, 267 LOC), and `_dialogs.py` (themed `askstring`
  + OS file-open shim, 105 LOC). `_helpers.py` shrinks from 850
  to 71 LOC as a re-export shim so existing imports through
  `peekdocs.gui._helpers` continue to work — the ~30 import sites
  across the CLI and GUI mixins don't need to change. New code
  should import from the specific submodule.

### Fixed
- **Stale numeric claims across docs.** Test count (`~630` → 718
  in `docs/SMOKE_TEST.md`, `CLAUDE.md`, `docs/ARCHITECTURE.md`;
  the count moved from 695 → 703 → 710 → 718 across three
  sync-and-add cycles as new test files landed); sample-corpus
  extension count (`41` → 38 in `README.md`, excluding
  auto-generated peekdocs report files); `_mixin_tools.py` LOC
  (`~870` → 873 in `docs/ARCHITECTURE.md`); test-file count
  (`~15` → 23). Discovered in the docs-vs-code audit agent pass;
  a five-minute pre-release grep over `[0-9]{3,4} test`,
  `~[0-9]{3} LOC`, and `[0-9]+ extensions` would catch this whole
  class next time.
- **`commands/runs.py` int-parse error routes to stderr.** Was
  going to stdout, carried forward verbatim from the pre-refactor
  code. Now consistent with `--diff`'s error-message convention.

## [1.2.78] — 2026-07-06

### Added
- **OCR integration test with real Tesseract on CI.** New
  `tests/test_ocr_integration.py` generates a small PNG containing
  known text via Pillow, runs `peekdocs.api.search()` with
  `use_ocr=True` on that directory, and asserts the extracted
  text lands in `SearchResult.matches`. Exercises the full
  `find_tesseract → cmd-pin → pytesseract.image_to_string →
  SearchResult` contract with a real Tesseract binary — the
  gap that let the 1.2.77 detection-vs-execution bug slip past
  the mocked unit tests. A new `ocr-integration` job in
  `.github/workflows/test.yml` `apt install`s Tesseract on
  Ubuntu and runs just this file. Skipped locally when Tesseract
  isn't installed, so no dev-machine friction.

### Changed
- **Type hint coverage widened to `cli.py` and `reporter.py`.**
  The mypy CI gate introduced in 1.2.76 for `api.py` + `paths.py`
  now also enforces signatures on `peekdocs/cli.py` (the CLI
  entrypoint and its 22 top-level helpers) and
  `peekdocs/reporter.py` (18 report-writer functions consumed
  by `cli.py` and by anyone extending output formats). All four
  files are listed in `pyproject.toml`'s `[tool.mypy]` block;
  signature drift on any of them fails the build. Docs updated
  in `README.md`, `USER_GUIDE.md`, and `ARCHITECTURE.md` to
  name the widened scope.

## [1.2.77] — 2026-07-06

### Fixed
- **Tesseract detection now checks well-known install locations
  in addition to `PATH`.** macOS GUI launches (Finder / Dock /
  Spotlight) inherit a stripped `PATH` that omits Homebrew's
  `/opt/homebrew/bin` (Apple Silicon) and `/usr/local/bin`
  (Intel), so `shutil.which("tesseract")` used to return `None`
  even when Tesseract was correctly installed. Users would
  install Tesseract via `brew install tesseract`, see the
  "Tesseract not detected" modal anyway, and have no path
  forward without launching peekdocs from a terminal. The new
  `peekdocs.paths.find_tesseract()` helper falls back to the
  standard Homebrew and MacPorts locations on macOS, standard
  Program Files locations on Windows, and standard `/usr/bin` /
  `/usr/local/bin` on Linux. The scanner's OCR call also pins
  `pytesseract.pytesseract.tesseract_cmd` to the located
  absolute path so the actual OCR execution doesn't fall back
  to PATH lookup. The four detection sites (parser, CLI
  `--check`, GUI OCR-toggle modal, scanner) share the single
  helper.

## [1.2.76] — 2026-07-06

### Changed
- **`_mixin_tools.py` split from ~10,873 LOC into six feature-
  based mixin files** (merge `9072d1f`, branch
  `refactor/mixin-tools-split`). The single largest architectural
  weakness identified in `docs/ARCHITECTURE.md` (the 10K-LOC
  "and this feature too" bucket file) is now gone. Five commits
  extracted 80 methods across five feature domains; the sixth
  commit updated the architecture doc:
  - `_mixin_wizard.py` (889 LOC, 4 methods) — Search Wizard +
    Regex Wizard picker
  - `_mixin_file_analysis.py` (2,825 LOC, 46 methods) — nine
    folder-analysis tools (File Inventory, Duplicate Finder,
    Large Files, Empty Files, Recent Changes, File Age
    Distribution, Protected Files, Unsearchable Files,
    Collection Summary)
  - `_mixin_regex_search.py` (3,126 LOC, 7 methods) — Regex
    Search + Regex Tester + both help panels
  - `_mixin_suites.py` (1,598 LOC, 7 methods) — Search Suites
    picker + execution + completion popup
  - `_mixin_help_panels.py` (1,829 LOC, 8 methods) — orphan
    `?`-help popups (search options, save/load, matched files,
    excluded files, index, three-mode compare, etc.)
  - `_mixin_tools.py` reduced to 873 LOC (4 misc methods —
    System Check, Diff Snapshots, Schedule Search)
  Cumulative reduction: **10,873 → 873 LOC (−92%)**.
  Zero behavior changes: PeekDocsApp still inherits from all
  mixins, cross-mixin calls resolve via Python MRO, all 678
  tests pass at every commit on the branch. Pre-refactor
  state preserved as tag `pre-mixin-split-1.2.75` on origin.
  Full commit-by-commit walkthrough in the merge commit body.
- **`docs/ARCHITECTURE.md` updated to reflect the split**
  (20e5e36). GUI package table now lists all nine feature-based
  mixins with their responsibilities. Historical decisions
  section notes the split preserved the mixin pattern (nine
  mixins in PeekDocsApp's MRO; cross-mixin calls still route
  through `self`). Known weaknesses list cleaned up: three
  items removed since they were fixed
  (`_mixin_tools.py` 10K-LOC bucket, `sys._MEIPASS` reinvention,
  sparse public-API type hints).
- **README + USER_GUIDE surface the ARCHITECTURE.md deep dive
  and the public-API type hints** (810bd98). README's
  Documentation table gained an `Architecture` row between
  API Reference and Glossary. USER_GUIDE's Python API section
  gained a type-hint note enumerating the typed surface
  (`search`, `list_suites`, `run_suite`, `list_regex_collections`,
  `run_regex_collection` + all 6 dataclasses) so IDEs and mypy
  work out of the box against the shipped `.py` files.

## [1.2.75] — 2026-07-06

### Docs
- **Glossary — "Provenance audit" entry added** (674250b,
  `docs/GLOSSARY.md`). The named workflow ("Provenance audit —
  `--diff` + `--hash`") appeared in three surfaces (README's
  *How these compose*, USER_GUIDE's Complete CLI Reference row
  194, USER_GUIDE's worked-example section) without a dedicated
  glossary entry. Entry covers mechanism (baseline / current /
  diff sequence, new-removed-changed-**modified** buckets),
  match-scoped vs folder-scoped (cross-refs FIM entry as the
  folder-scoped complement), placement in the trio of named
  compositions (cross-refs Live pattern sweep and Scheduled
  pattern scan), and use cases (audit engagements, due-diligence
  sweeps). Placed between `pipx` and `Proximity search` —
  alphabetically "Prov" comes before "Prox" (V < X).

## [1.2.74] — 2026-07-06

### Added
- **LICENSE now travels with standalone binaries + "View License"
  button in the About dialog** (a3e5153). Closes the "MIT license
  doesn't ship with the standalone binary" gap uncovered by a
  distribution-mechanics question. The pipx install path already
  shipped LICENSE / NOTICE / THIRD_PARTY_NOTICES.md via PEP 639
  (`pyproject.toml:59` — `license-files = [...]`) into the
  wheel's `.dist-info` directory. The standalone-binary path
  didn't. Two coordinated changes:
  - **`build_app.py`** — both `build_gui()` and `build_cli()`
    now pass three `--add-data` flags copying LICENSE, NOTICE,
    and THIRD_PARTY_NOTICES.md to the bundle root. `--onefile`
    modes (Windows GUI/CLI, Linux GUI/CLI) extract the files to
    `_MEIxxxxxx/` at launch (accessible via `sys._MEIPASS` while
    the process runs); `--onedir` modes (macOS GUI/CLI) keep
    them permanently at the bundle root.
  - **`peekdocs/gui/_mixin_data.py`** — About dialog's single
    Close button becomes a two-button row: **View License** +
    Close. New `_show_license` method opens a themed 560×420
    toplevel with a scrollable read-only `Text` widget in Courier
    10, showing the bundled LICENSE text. Path resolution tries
    `sys._MEIPASS/LICENSE` (PyInstaller bundle) first, then
    `<repo root>/LICENSE` (pip/pipx source install), then a
    fallback message pointing at the GitHub URL if neither
    resolves. Dialog height bumped 245px → 265px to give the
    button row breathing room.
  - **Net effect**: copyright holder → binary → running user,
    the license text travels through the whole loop with no
    external network access required to read it.

## [1.2.73] — 2026-07-04

### Docs
- **`docs/INSTALL_SAFETY.md` — same-release caveat added to the
  checksum-verification walkthrough** (ee2a9a5). Real user hit
  the trap: downloaded `peekdocs-gui-windows.exe` on 2026-07-03,
  then downloaded `peekdocs_SHA256SUMS.txt` on 2026-07-04 —
  between the two downloads three releases had been cut
  (v1.2.70, 1.2.71, 1.2.72), so the hashes were from different
  builds and the check failed with a misleading *"did NOT
  match"* result even though nothing was actually wrong. New
  heads-up between step 1 and step 2 explains the pitfall
  (fast-cadence + `releases/latest/download/...` auto-tracking)
  and offers two mitigations: (a) download both files
  back-to-back in one session, or (b) lock to a specific
  tagged release URL by replacing `latest` with the version
  tag (e.g., `releases/download/v1.2.72/...`). Tag lock is the
  belt-and-suspenders approach, immune to any number of future
  release bumps.

## [1.2.72] — 2026-07-04

### Docs
- **OCR modal behavior documented in the two surfaces where a
  user learning about OCR would look** (78e23d5). Search Wizard
  `?` help panel's Tesseract footnote now mentions the new modal
  ("checking the OCR box in Advanced Search Options without
  Tesseract installed shows a modal with the platform-specific
  install command"). USER_GUIDE's `-O` flag row (line 733) now
  documents both surfaces' proactive checks — GUI (as of 1.2.71)
  fires a modal, CLI aborts with the same install commands.
  README deliberately not touched — its existing "requires
  Tesseract" mentions remain accurate and adding modal-behavior
  detail bloats a top-of-funnel surface.
- **README INSTALL_SAFETY.md pointer reframed** (c4a0e94, line
  438). Prior wording *"Cautious about installing?"* implied
  verification is for paranoid users only and discouraged normal
  downloaders from clicking through. New wording *"Want to
  verify the download?"* invites verification as a normal
  action. Same target link, same enumeration of five methods
  (checksum, VirusTotal, network monitor, source-code grep,
  sandbox install), but leads with the checksum-check commands
  (the most common actual use) rather than treating all five
  as equal peers.

## [1.2.71] — 2026-07-03

### Added
- **Proactive Tesseract check when the OCR checkbox is toggled
  on** (892e9b8, `peekdocs/gui/_mixin_build.py`). Before this
  release the GUI's OCR checkbox had no toggle handler — a user
  could enable OCR, set up a search, run it, and only discover
  Tesseract wasn't installed after the search finished (image
  files silently skipped, message buried in `peekdocs_errors.log`
  or in the results-preview area). Now, checking the OCR box
  fires an immediate detection check via `shutil.which("tesseract")`;
  if Tesseract isn't found, a modal (askyesno) shows per-OS
  install instructions:
  - **macOS:** `brew install tesseract`
  - **Windows:** Download from
    `https://github.com/UB-Mannheim/tesseract/wiki`
  - **Linux:** `sudo apt install tesseract-ocr` (or distro
    equivalent)
  Default "No" unchecks OCR automatically for the safer path.
  "Yes" lets the user proceed with OCR enabled anyway — image
  files will be skipped at scan time but other file types
  still search normally. Mirrors the proactive check the CLI
  already does at `parser.py:28`.

### Fixed
- **False-success handling in `_search_finished` when a
  pre-search error meets a stale results file** (892e9b8,
  `peekdocs/gui/_mixin_search.py`). When the CLI aborted at
  parser level (Tesseract missing, `pytesseract`/`Pillow`
  Python packages missing) BEFORE the search ran, and a
  `peekdocs_standard_results.txt` from a previous OCR-off
  search happened to sit in the results dir, the GUI's
  returncode-2 handler misread the stale file as "this search
  partially succeeded" and showed *"Search complete (with
  warnings)"*. Now the returncode-2 branch pattern-matches
  stdout for known pre-search error markers (`"Tesseract OCR
  is not installed"`, `"OCR requires the pytesseract"`, `"OCR
  requires the Pillow"`) and — when any of those are present
  — skips the stale-results interpretation entirely and shows
  the CLI's actual error message via `_show_error`. Genuine
  degraded-success cases (search ran, DOCX generation failed)
  still take the existing branch; the fix is narrow to known
  pre-search errors only.

## [1.2.70] — 2026-07-03

### Docs
- **Linux GUI first-launch deep-dive section added to
  `docs/INSTALLATION.md`** (c521609). New section
  `### Linux GUI first-launch — chmod, the ./ prefix, and
  common startup issues` inserted between the macOS Gatekeeper
  deep-dive and the CLI startup-time section (anchor
  `#linux-gui-first-launch`). Structure mirrors the macOS
  Gatekeeper section for parity:
  - Step-by-step (confirm download size, optional SHA-256
    verify, `chmod +x` with explanation, run with `./`)
  - Six common-issue troubleshooting entries (permission
    denied, cannot execute binary file / ARM architecture,
    nothing happens with SSH X11 forwarding + `$DISPLAY`
    check, window flashes closed with `tee` capture, `libxcb`
    shared library errors with per-distro apt/dnf/pacman
    commands, SELinux Access denied with restorecon and
    permissive-mode diagnostics)
  - Why `./` prefix is required (`$PATH` explanation)
  - Optional install to `~/.local/bin` (per-user) or
    `/usr/local/bin` (system-wide) with `$PATH` check
  - Five notes: no Linux Gatekeeper equivalent, executable
    bit doesn't survive re-download, PyInstaller per-launch
    unpack cost, Wayland via XWayland, no AppImage / Flatpak /
    Snap today
- **README Linux GUI paragraph now cross-links to the deep-
  dive** (c521609, `README.md`), matching the pattern the
  macOS row already uses to reach its Gatekeeper deep-dive.
  README's Linux install row stays terse; first-time Linux
  downloaders reach the walkthrough in one click.

## [1.2.69] — 2026-07-02

### Fixed
- **README release badge was rendering as "release: invalid"**
  (3089566, `README.md:4`). A shields.io routing bug: passing
  a `label=release` (lowercase) query param that matches the
  endpoint's default label made shields.io return "invalid"
  instead of the tag name. Confirmed by curl — `?label=release`
  → invalid, `?label=Release` → v1.2.68, `?color=blue` alone
  → v1.2.68, `?label=release&color=blue` → invalid. Fix:
  dropped the redundant `label=release&` from the URL,
  keeping `?color=blue`. The default label is already
  "release," so removing the parameter preserves the exact
  same visual and works around the shields.io conflict. The
  badge worked earlier in the evening — likely a recent
  shields.io deploy regression.

## [1.2.68] — 2026-07-02

### Docs
- **Two accuracy/consistency fixes from a comprehensive README +
  USER_GUIDE audit** (6e0f062). README came back completely
  clean; USER_GUIDE had two small items:
  - **PDF framing aligned with the canonical line/paragraph/row
    rule** (`docs/USER_GUIDE.md:735`). The `-P` (line-proximity)
    row in Flag Use Summary said "for PDF, a line is a text
    block (variable)" while every other place in the doc uses
    "paragraph" for PDF. Merged Word and PDF into one clause
    matching the tooltip and the four other canonical sites.
  - **Composition rows 196–197 relabeled to make variant
    relationship unambiguous** (`docs/USER_GUIDE.md:1327-1328`).
    The Compositions cluster in the Complete CLI Reference has
    three named compositions plus two variant rows for the
    Scheduled pattern scan. Row labels now explicitly say
    "Scheduled pattern scan — variant with… (extends row 195)"
    instead of the generic "Scheduled scan with…" — a reader
    scanning the table no longer risks counting five compositions
    where there are three.

## [1.2.67] — 2026-07-02

### Changed
- **`peekdocs -h` / banner examples extended so a consultant with
  no external docs can compose workflows from the CLI alone**
  (a98c8c7, `peekdocs/cli.py`). Five additions:
  - **`--output-dir`** now names the cloud-output guard as a
    possible reason a write can fail, and points at the one-off
    override (`--allow-cloud-output`) and the persistent config
    key (`redirect_cloud_output=true`).
  - **`--diff`** now flags its NON-standard exit codes (0=no
    change, 1=actionable change, 2=error — opposite of most CLI
    tools) and warns about `&&` chains.
  - **`--on-match`** now enumerates every env var passed to the
    hook (`PEEKDOCS_MATCH_COUNT`, `PEEKDOCS_FILE_COUNT`,
    `PEEKDOCS_ELAPSED_SECONDS`, `PEEKDOCS_ARGV`, `PEEKDOCS_CWD`,
    `PEEKDOCS_REPORT_TXT/DOCX/JSON/CSV/PDF/HTML`) and pins the
    "batch searches only, NOT `--watch`" scope up front.
  - **Compositions** — new example section covering the three
    named workflows from the README's *How these compose*:
    Live pattern sweep (`--watch` + `--regex-collection`),
    Provenance audit (`--diff` + `--hash` three-command
    sequence), Scheduled pattern scan (cron +
    `--regex-collection` + `--timestamp`).
  - **Portable use** — new example section for the USB-carried
    workflow: `--check`, `--output-dir` + `--no-index` +
    `--timestamp`, `--hash` provenance snapshot back to the USB,
    and the cleanup story.

### Docs
- **Portable use section restructured to serve non-consultant
  audiences too** (a98c8c7, `docs/USER_GUIDE.md`). The USB
  workflow's three properties (zero install on host, zero
  footprint with `--no-index` + `--output-dir` back to USB,
  zero Python dependency) apply to more than IT consultants —
  section broadened accordingly:
  - Section renamed: `Portable / consulting use` → `Portable use`.
  - Intro rewritten to name both audiences: IT consultants +
    personal users (evaluation, locked-down machines, privacy,
    air-gapped/shared, cross-machine mobility). Inline note tells
    personal-use readers to read "engagement" as generic "session"
    downstream.
  - **Common engagement types** split into **Common use cases —
    IT consultants** (5 existing) + **Common use cases —
    personal and evaluation** (5 new: evaluation-before-commit,
    locked-down machines, privacy/minimalism, air-gapped/shared,
    cross-machine mobility).
  - Common-thread paragraph rewritten to unify what all use
    cases share: "the host machine isn't yours to install into"
    for one reason or another.
  - Downstream "client machine/drive/site/engagement" language
    swapped for generic "host machine/drive" and "session" in
    the load-bearing prose. Consulting-flavored language kept
    where it describes real consultant concerns rather than
    universal ones.
- **Six cross-references updated** (a98c8c7) — README's IT
  consultant bullet, USER_GUIDE's TOC + Where to Start bullet +
  Getting Started "What's next?" bullet, and both CLI banner
  section headers. Anchor migrated from
  `#portable--consulting-use--running-peekdocs-from-a-usb-stick`
  to `#portable-use--running-peekdocs-from-a-usb-stick`.

## [1.2.66] — 2026-07-02

### Docs
- **Portable / consulting use section — GUI variants now
  covered end-to-end** (788487c). Setup paragraph gained bolded
  CLI-vs-GUI decision guidance so a consultant chooses which
  binaries to carry before seeing the workflow commands. Gotcha
  4 (Startup tax and Gatekeeper) expanded from three cost rows
  to four to name the macOS GUI's larger `.app` bundle (~200 MB
  vs ~103 MB CLI zip) and higher first-launch cost (3–6 s vs
  1–3 s), plus the `.app`-bundle form of the quarantine strip
  (`xattr -d com.apple.quarantine peekdocs-gui.app` on the whole
  bundle). New intro sentence clarifies that both CLI and GUI
  inherit the same OS security prompts because peekdocs is
  unsigned regardless of variant.
- **Portable / consulting use section — "Preparing the USB —
  one-time setup" walkthrough added, plus two new gotchas**
  (6b3b57c). Prior "Setup — done once" one-liner replaced with
  a full one-time-setup walkthrough:
  - Explicit "no Python on the USB, no Python on the client"
    statement at the top — the standalone binaries ARE Python
    + deps + peekdocs in one executable; a portable-Python
    distribution is not part of this workflow.
  - Six-binary + checksums-file listing with per-file sizes.
  - SHA-256 verification step (macOS/Linux one-liner, Windows
    PowerShell equivalent).
  - macOS `.app` pre-unzip guidance with the ExFAT-doesn't-
    preserve-xattrs rationale.
  - Recommended USB folder structure (per-OS subdirs +
    checksums + reports target + wrapper-scripts directory).
  - Rehearsal step ("run the actual command on a scratch folder
    matching the client's OS before you're on the clock").
- **Four gotchas → Six gotchas** in the same section:
  - **#5 Corporate Windows execution restrictions.** Group
    Policy and Windows Defender Controlled Folder Access can
    block `.exe` launches from removable drives; verify with
    client IT before assuming the workflow works. Fallback
    options: temporary whitelist / pipx-install on client /
    launch from a Group-Policy-permitted directory.
  - **#6 Tesseract for OCR is NOT bundled.** The standalone
    binaries carry Python + Python dependencies only. Options
    if OCR is in engagement scope: install Tesseract on the
    client, pre-OCR docs on own machine, or scope OCR out.
    Cross-links `peekdocs --check` as the on-site diagnostic
    for Tesseract presence.

## [1.2.65] — 2026-07-02

### Docs
- **Complete CLI Reference — 33 rows added covering the
  automation surface + compositions** (bee6e12,
  `docs/USER_GUIDE.md`). The existing 164-row Command Examples
  table covered the core search surface (basic / filter /
  regex / boolean / range / index / expression / OCR / fuzzy /
  wildcard) exhaustively but had zero examples for `--watch`,
  `--diff`, `--hash`, `--suite`, `--on-match`,
  `--allow-cloud-output`, `--dry-run`, or `--runs`. New rows
  165–197 grouped into seven feature clusters (Search Suites,
  Folder Watcher, Content-Fingerprint Diff, Notification Hook,
  Cloud-Output Guard, Preflight & Structured Logs) plus an
  explicit **Compositions** cluster naming the three from the
  README's *How these compose* section (Live pattern sweep,
  Provenance audit, Scheduled pattern scan) with anchor links
  to the corresponding worked examples in Automation and IT
  Use.
- **Section repositioned as the canonical CLI reference,
  cross-linked from the README** (bee6e12). With comprehensive
  coverage now in place, the table earns canonical status:
  - Renamed `Command Examples` → `Complete CLI Reference` +
    intro paragraph calling it the canonical reference, stating
    the 197+ count, listing what it covers, and telling readers
    to search it with Cmd+F / Ctrl+F.
  - TOC entry, Getting Started "What's next?" bullet, and the
    Usage section pointer all updated with the rename (and the
    stale "150+ commands" bumped to "197+").
  - README's *How these compose* section gained a closing
    italic pointer to the Complete CLI Reference — bidirectional
    discovery loop between the README's composition prose and
    the USER_GUIDE's one-liner reference.

## [1.2.64] — 2026-07-02

### Added
- **`docs/images/getting-started.gif`** (09e35a2, 12.7 MB) — the
  first-time on-ramp clip, positioned as the very first video
  in the "Watch peekdocs in action" section before the four
  mode/discoverability clips. Three-mode primer's closing
  sentence updated to lead readers into the new sequence
  (getting-started → hero → Suites → Regex → settings tour).

### Docs
- **"Who Is It For?" list reorganized for GitHub/PyPI adopters**
  (183a5e9). The list opened with "Home user" (least likely
  PyPI/GitHub discoverer) and buried the technical roles
  (AI/ML engineer, Engineer, Developer) at positions #10–12.
  Reordered so Developer / programmer, Sysadmin, AI/ML engineer,
  and IT consultant land at the top; less technical roles
  (Small business owner, Office worker) at the bottom. Dropped
  two bullets — **Home user** (its "everybody is a home user"
  framing now lives in the section's opening paragraph; tax-
  search scenario folded into Small business owner) and
  **Email archives** (was a file type, not a role; already in
  the intro's file-type list). Enhanced two one-liners:
  **Sysadmin** gained `--watch` NDJSON streaming and native
  archive-format handling detail; **IT consultant** gained
  the standalone-binary-on-USB workflow and a cross-link to
  the Portable / consulting use section.
- **"Blue button" disambiguation in three-mode primer**
  (9609db7). Standard Search was described as "(blue button)"
  but the Step 4 row has two blue buttons — the large Run
  Standard Search button and the smaller Search Wizard square
  next to it. Rewrote the parenthetical to distinguish by
  size + position and briefly identify the Wizard as a form-
  builder on-ramp with 20 pre-built search-type forms, not a
  fourth mode.
- **Pausable MP4 versions of the demo clips linked from the
  README** (4acebe6). One-sentence italic note between the
  primer's closing line and the first clip points readers at
  the maintainer's personal site (robertdschoening.com/peekdocs)
  where every clip is also available as a pausable, seekable
  MP4. Bidirectional discovery: the repo's homepageUrl has
  always pointed at the personal site; this closes the loop.

## [1.2.63] — 2026-07-01

### Docs
- **USER_GUIDE stale-info reconciliation** (87cf236). Three fixes
  surfaced by a Getting Started audit:
  - **"GUI is English only" claim replaced with an accurate
    partial-i18n description** (line 3376, Multilingual Support
    section). Predated the v1.1.4–v1.1.7 seven-language rollout.
    New text matches the canonical scope statement in the
    language-picker tooltip (`peekdocs/gui/_mixin_build.py:1865`)
    — translated: four main-page Step labels + tooltips, three
    action buttons + tooltips, and a handful of adjacent
    bottom-row strings. English-only: help popups, Advanced
    Search Options labels, Tools menu items, error messages,
    CLI banner and all `--help` output, every report, every
    doc file. Closes with the "experiment, not completed
    effort" framing and points at CONTRIBUTING.md.
  - **Advanced Search Options cloud-redirect checkbox added to
    the GUI Mode inventory** (line 382). The **Redirect
    cloud-synced output paths to ~/peekdocs_reports** sticky
    checkbox shipped with the cloud-output guard but wasn't in
    the prose describing what Advanced Search Options contains.
    Added between "output directory" and "additional output
    formats" with a parenthetical + cross-link to the
    Cloud-synced folders section.
  - **"What's next?" pointers extended** (end of Getting Started
    with the Terminal). Two bullets added for the automation
    surface (`--diff` / `--hash` / `--watch`, three worked
    examples) and the Portable / consulting use workflow.
    Getting Started now has a guide-internal path to both.

## [1.2.62] — 2026-07-01

### Docs
- **New section: "Portable / consulting use — running peekdocs
  from a USB stick"** (fc9fd98, ad3766b, `docs/USER_GUIDE.md`).
  Documents the IT-consultant workflow of carrying peekdocs's
  standalone binaries on a USB stick and running against a
  client machine's drive without installing anything. Contents:
  - **Common engagement types** — legacy knowledge extraction,
    migration / cutover planning, due-diligence sweeps,
    response-to-inquiry discovery, post-incident analytical
    triage (with an explicit boundary against evidentiary /
    forensic work).
  - **Typical engagement command** — Windows and macOS/Linux
    forms with `--output-dir` back to the USB, `--timestamp`,
    `--no-index`, `-o docx,csv,json`. Cross-linked to the
    audit-provenance worked example for the `--hash` pairing.
  - **Four gotchas** — permissions (no privilege escalation),
    cloud-output guard as a *feature* (confidentiality control
    on OneDrive / Google Drive / iCloud / Dropbox targets),
    zero-artifact hygiene (`peekdocs_` / `.peekdocs` prefix
    cleanup commands for Windows PowerShell and macOS/Linux
    `find`), startup tax + Gatekeeper (per-OS launch times +
    quarantine-strip bypass).
  - **What this is not** — not a forensic acquisition tool
    (names FTK Imager / X-Ways / Autopsy as the right scope for
    that need), not for adversarial endpoint-detection
    environments, not a substitute for written authorization.
  - Cross-linked from USER_GUIDE TOC and the "Where to Start"
    navigation bullet at the top of the guide.

## [1.2.61] — 2026-07-01

### Added
- **`CODE_OF_CONDUCT.md`** (118c866). Contributor Covenant 2.1,
  with the maintainer email as the enforcement contact. Closes
  the last GitHub community-standards gap (CONTRIBUTING.md and
  SECURITY.md already existed).

### Docs
- **Getting Started section reconciled against current CLI
  output** (118c866, `docs/USER_GUIDE.md`). Four fixes so the
  walkthrough matches what a new user will actually see:
  - New bullet in "Where to Start" pointing to the third worked
    example (real-time pattern monitoring with `--watch`) added
    in c71a821 — was cross-linked from the README but not from
    USER_GUIDE's top-of-guide navigation.
  - `samples/engineering_test` extension count corrected from
    "41 extensions" to "38 extensions" (verified by enumeration).
  - Example CLI output at Step 3 rewritten to match current
    output shape: ordering swapped from
    `Files searched: X — Found N` to
    `Found N match(es) in M file(s). Files searched: X (Y KB).`,
    and the per-file match count breakdown added.
  - Regex example at line 263 swapped from `\d{3}-\d{2}-\d{4}`
    ("a 9-digit ID with dashes") to `\bJIRA-\d+\b` ("a JIRA
    ticket ID like `JIRA-1234`"). The prior pattern was
    technically not naming SSN, but it's recognizably SSN-shaped
    to a US reader — a boundary case under the "no PII categories
    in docs" voice rule. The JIRA pattern is a better fit for the
    peekdocs audience.
- **README freshness marker bumped** (118c866, `README.md:10`) —
  "Actively maintained — last reviewed June 2026" → July 2026.

### Changed
- **GitHub repo topics extended** (live via `gh repo edit`, not
  in the repo tree). Added 8 topics — `batch-analysis`,
  `cross-platform`, `local-only`, `mit-license`, `no-cloud`,
  `ocr`, `regex`, `report-generation` — bringing the total from
  10 to 18 of 20 allowed. Improves discoverability via GitHub's
  topic-based search and trending pages.

## [1.2.60] — 2026-07-01

### Docs
- **"How these compose" section added to the README** (e8d10fd).
  Feature Highlights lists eight-ish workflow primitives as
  individual bullets; first-time readers don't stumble into the
  combinations on their own. New H2 section between Feature
  Highlights and the design-principle blockquotes names three
  compositions worth knowing about, each with a working CLI
  example verified against the actual flag surface:
  - **Live pattern sweep** — `--watch` + `--regex-collection`,
    streaming NDJSON matches with `--on-match` for notifications.
  - **Provenance audit** — `--diff` + `--hash`, layering
    content-hash change detection on top of match-level diffing.
    Cross-links to the worked example in
    `docs/USER_GUIDE.md § A worked example: audit engagement
    provenance` (line 1496+).
  - **Scheduled pattern scan** — cron / Task Scheduler +
    `--regex-collection` via Tools → Schedule Search's generated
    command, `--timestamp` for dated output.

  TOC entry added between Feature Highlights and CLI at a Glance.

## [1.2.59] — 2026-07-01

### Changed
- **Voice audit — cloud-output guard no longer described in
  warranty-flavored language** (c7d148f). Three sites described
  the cloud-output guard as a "no-cloud confidentiality
  **promise / guarantee**" — SLA-adjacent framing that reads as a
  support commitment. peekdocs is MIT-licensed with zero support
  obligations; the guard is a *check* the code runs at write
  time, not a warranty. Rewrites all three sites to "no-cloud
  confidentiality **check**" language — same meaning, without
  the SLA valence:
  - `README.md:197` (Feature Highlights bullet)
  - `README.md:888` (Security FAQ table row)
  - `peekdocs/gui/_mixin_build.py:1045` (cloud-redirect checkbox
    tooltip)
- **Match-All-Terms tooltip aligned with canonical line-vs-
  paragraph framing** (c7d148f, `peekdocs/gui/_mixin_build.py:1062`).
  Previous tooltip said "a line is typically a paragraph" for
  PDF/Word and omitted Excel entirely. Rewrites to the canonical
  shape used in five other places (CLI help, User Guide,
  GLOSSARY, cli.py argparse, expression-mode tooltip): "a line
  for text and source code, a paragraph for Word and PDF, a
  row for Excel."

## [1.2.58] — 2026-07-01

### Docs
- **Discoverability tour clip added to the README as the fourth
  demo** (0f14c3e). `docs/images/discoverability.gif` (8.87 MB,
  720p) sits after the three mode clips (Standard / Suites /
  Regex) and shows the settings surface: sliding open the left
  curtain, expanding the Advanced Search Options row, and cycling
  through App Size, Language (7 UI translations), Tooltips toggle,
  Light / Dark mode, and Preview Size. The three-mode primer's
  closing sentence now promises this fourth clip too — "then a
  short tour of the settings surface — every knob one click away."
  Rounds out the demo section: viewers see what peekdocs does
  (three mode clips) and then how it feels to run (discoverability
  clip).

## [1.2.57] — 2026-07-01

### Docs
- **Demo captions no longer imply the on-screen collections ship
  with the app** (e9f1698). The Regex Search caption previously
  named "**Code patterns** collection" and the Search Suites
  caption named "**Quarterly Content Audit** suite" with bold
  treatment — both read as if a first-time user could find them
  already loaded. They can't: both are scaffolds in `samples/`
  that have to be imported via Restore From Collection / suite
  import. Rewrites both captions to "a user-built collection /
  suite of …" so the framing is honest about who built the
  set; the pattern and search enumerations stay so the clips
  are still accurately described.

## [1.2.56] — 2026-07-01

### Docs
- **Search Suites demo clip added to the README** (10ca0af).
  `docs/images/suites-hero.gif` (18 MB, 720p) slots between the
  Standard Search hero clip and the Regex Search clip added in
  1.2.55, giving all three main-page modes a matching demo in
  section order (Standard → Suites → Regex). The clip runs the
  **Quarterly Content Audit** suite — a saved bundle of standard
  searches (draft / stale / TODO / owner-missing / outdated-link
  / deprecated-terminology sweeps) fired together on one click,
  with results merged into one combined highlighted report.
  Completes the three-mode primer promised in 3c0392e.

## [1.2.55] — 2026-07-01

### Docs
- **Regex Search demo clip added below the hero clip in the
  README** (0a93d91). `docs/images/regex-hero.gif` (4.25 MB,
  720p) lands the Regex Search half of the three-mode primer
  (3c0392e). Follow-on caption updated (348ddb4) to name the
  **Code patterns** collection specifically and enumerate the
  10 patterns on screen — TODO / FIXME / HACK markers, Python
  and JavaScript debug statements, breakpoint / pdb drops,
  `@deprecated` markers, UPPER_CASE constants, SemVer version
  strings. Search Suites clip still to come.

## [1.2.54] — 2026-07-01

### Fixed
- **README flag emojis rendered as letter codes on Windows**
  (10311da). Regional-indicator emoji pairs (🇪🇸 = 🇪 + 🇸)
  render as their two-letter code on Windows because Segoe UI
  Emoji doesn't include flag glyphs. User-visible symptom: the
  top-of-README language row read "ES FR DE JP CN BR" instead
  of flags. Replaced all seven flag emojis with `<img>` tags
  pointing at flagcdn.com's PNGs — cross-platform reliable, with
  alt text (`ES`, `FR`, `DE`, `JP`, `CN`, `BR`) as the graceful
  fallback if the CDN is ever unreachable. Both the summary line
  and the six per-language section headers were converted.

## [1.2.53] — 2026-07-01

### Docs
- **Regex Search popup wording** (427705b) — the "peekdocs does
  not validate correctness" note now reads "peekdocs does not
  validate regex pattern correctness", clarifying what
  "correctness" refers to.
- **README "Who Is It For?" consolidated into one list**
  (c9c2fac). The section used to have a 9-bullet visible short
  list and an 11-bullet `<details>` block with more depth; some
  roles appeared in both under different phrasings. Merged into
  a single 12-bullet visible list, one entry per role, each
  combining the punchy example with the depth. The `<details>`
  block is gone.
- **README three-mode primer added before the hero clip**
  (3c0392e). "Watch peekdocs in action" now leads with a short
  intro naming Standard Search (blue), Search Suites (green),
  and Regex Search (orange) so a first-time reader is set up
  to interpret follow-up demos of Suites and Regex Search
  when they land.

## [1.2.52] — 2026-07-01

### Fixed
- **GUI Regex Search returned zero matches for every pattern
  (regression from 1.2.50's cloud-guard threading fix).** The
  `folder = _rs_resolved_folder` reassignment added at the top of
  the write block inside `_thread` made `folder` local throughout
  the closure per Python's scoping rule, so every earlier read
  (including `directory=folder` in the `api_search` loop) became
  a read of a local not yet assigned, raising `UnboundLocalError`
  that was swallowed by `_thread`'s outer exception handler.
  Reported symptom: `Code patterns` and `Common Code Patterns`
  collections returned 0 matches in the GUI against
  `peekdocs_demo_codebase`, while the same collection via CLI
  returned 80 matches. Fix: `nonlocal folder` at the top of
  `_thread` so reads see the enclosing parameter and the write-
  block reassignment updates it in place with no shadow local.
  The Suite runner's `_run` closure doesn't have the same bug
  (it uses a distinct variable name, `output_folder =
  _resolved_output_folder`).

## [1.2.51] — 2026-07-01

### Fixed
- **Expression-mode saved searches inside a suite crashed with
  `AttributeError: 'bool' object has no attribute 'strip'`.** The
  save path (`_mixin_data.py:1062`) stores `expression` as a
  boolean flag (True/False) — the actual expression string lives
  in `search_text`. Three consumer paths (`cli.py:1716`,
  `api.py:519`, `_mixin_tools.py:6336`) treated the boolean *as*
  the expression string via
  `expr = params.get("expression") if params.get("expression") else None`,
  passing `True` to `api_search`'s `expression=` kwarg, which then
  raised in `expr_parser.tokenize()` trying to `.strip()` a
  boolean. Symptom the user reported: Quarterly Content Audit
  suite (which has two expression-mode saved searches) ran the
  first 3 searches fine, then died silently on search #4; GUI
  status stuck at "Writing reports…" forever because the worker
  thread crashed and `_suite_finished` was never called. **Not
  caused by** the 1.2.43 cloud-guard threading bug (that fix from
  1.2.50 stays in — that was a real bug, just not the one causing
  this symptom). Fix pattern at all three sites: three-way branch
  on mode (expression / regex-or-wildcard / plain text) rather
  than the previous two-way branch plus a broken expression
  extraction.

## [1.2.50] — 2026-07-01

### Fixed
- **Search Suite hang on "Writing reports…" (regression from
  1.2.43).** The GUI Suite runner and Regex Search per-pattern
  cloud-output guards were installed inside the worker thread
  that runs those searches. Tkinter modals from worker threads
  hang on `wait_window()` — user-visible symptom: searches
  complete in a few seconds, then the report-writing status
  never finishes. The 6 subprocesses in a suite run fine because
  `subprocess.Popen` doesn't care about GUI threads; but the
  cloud-guard modal spawn from the worker thread deadlocks the
  whole worker. Reported by the user filming the Quarterly
  Content Audit suite demo. Fix: hoist both guard calls out of
  the worker thread and run them on the main thread BEFORE
  spawning the worker. If the user cancels the modal we abort
  cleanly before any UI state changes (no stale progress bar or
  status text left behind). Resolved output folder is passed
  into the worker's closure via a local variable. Regex Search
  screen-only runs skip the guard entirely — nothing gets
  written, so there's no output directory to check.

## [1.2.49] — 2026-07-01

### Docs
- **USER_GUIDE — new "How saves persist" blockquote** (570466d).
  Companion to the existing "Why one canonical file per location?"
  blockquote (the *where*); this new one covers the *how it gets
  there safely*. Documents the three save paths (Save Collection
  As → global file only; ▶ Save on the main page → per-folder file
  only with the 20-key `SEARCH_PARAM_KEYS` snapshot; Add / Edit /
  Delete Suite → double-write, per-folder file first as source of
  truth, then the global suite index as cache). Explains the
  `--list-suites --rescan` reconciliation path when the two
  disagree, and the atomic-write pattern
  (`tempfile.mkstemp` + `os.replace`) that keeps every save
  crash-safe (no partial JSON left on disk after a crash).

## [1.2.48] — 2026-07-01

### Docs
- **GLOSSARY — new "File-integrity monitoring (FIM)" entry**
  (30092e1). Fills in what peekdocs's `--hash` doesn't cover
  (whole-folder change detection). Three tiers: shell one-liner,
  purpose-built (`hashdeep` / `restic` / `borgbackup`),
  enterprise (AIDE / Wazuh / Tripwire). Includes the realistic
  belt-and-suspenders audit workflow combining a FIM baseline
  with peekdocs `--hash` for findings provenance. Back-pointer
  added in the SHA-256 reproducibility entry.
- **USER_GUIDE — new worked example: audit engagement
  provenance** (c35b5cb). Parallel to the existing nightly-
  source-tree-watch example. Walks through baseline → citation
  → verify → diff with copy-pasteable commands; highlights the
  MODIFIED diff bucket as the auditor's key signal (same file,
  same match count, different SHA-256 → someone silently edited
  around your citation). Names the scope constraint
  (`--hash` is match-scoped, not folder-scoped), points at the
  FIM glossary entry for whole-folder coverage, and includes an
  explicit "not a chain-of-custody system" disclaimer. TOC
  entry added, plus a new reader-hint ("Running an audit /
  review engagement?") aimed at readers who came from the
  README auditor bullet.

## [1.2.47] — 2026-07-01

### Docs
- **GLOSSARY SHA-256 reproducibility entry tightened** (5a5566a).
  The original phrasing implied SHA-256 alone tells you which
  files changed content across two scans. Actual scope: requires
  `--hash` on both scans, `peekdocs --diff` to do the comparison,
  and only works for files that matched in **both** scans. A file
  that dropped out of the match set (edited to no longer contain
  the term) shows up as `removed`, not `modified`. That constraint
  is now stated explicitly, plus a pointer at dedicated file-
  integrity tools for whole-folder monitoring.

## [1.2.46] — 2026-07-01

### Docs
- **README language-bullet reordered and rephrased** (46032c5).
  Leads with the broader Unicode-content-matching claim (applies
  to every user) before the narrower GUI-translation claim.
  "Uncommon for a search tool at this scale" replaces the earlier
  "unlike most search tools" comparative framing, per the voice
  rule against comparative jabs at peer tools.
- **GLOSSARY gains "SHA-256 reproducibility" entry** (49e58bb).
  The term appears in the README auditor bullet, the `--hash`
  flag documentation, INSTALL_SAFETY.md, and the run-log schema,
  but no glossary entry tied the pieces together. New entry
  covers what the hash is, how peekdocs surfaces it (`--hash`),
  the two workflows it serves (audit chain-of-custody, `--diff`
  snapshots), and cross-references the release-artifact
  `peekdocs_SHA256SUMS.txt`.

## [1.2.45] — 2026-07-01

### Docs
- **README documents the 1.2.43 cloud-output guard.** Two edits:
  a new Feature Highlights bullet between "Local-only by design"
  and "Search depth beyond grep" that names the four detected
  services (iCloud Drive / OneDrive / Google Drive / Dropbox) and
  the prompt-or-redirect UX; and an updated IT/Security Q&A row
  ("Does it store what it finds?") replacing the pre-1.2.43
  "automatically redirects" description with the full write-time
  guard behavior (GUI modal, CLI exit 2 without
  `--allow-cloud-output`, sticky checkbox for silent redirect).

## [1.2.44] — 2026-07-01

### Docs
- **README language-toggle blurb** — dropped the
  `(partial UI translation)` parenthetical. Each language intro
  already explains its own translation scope. `click here for an
  intro in yours` reads more like an invitation than the bare
  `click for`.

## [1.2.43] — 2026-06-30

### Added
- **Cloud-output guard at every report-write path.** The "no-cloud
  confidentiality" claim in the README auditor bullet was a
  search-time guarantee only — peekdocs auto-redirected suite
  reports if the *search folder* was cloud-synced, but a user
  picking a cloud-synced *output_dir* explicitly (or running the
  CLI inside `~/Documents` on a Mac where Documents is iCloud-
  mirrored) could still leak reports to iCloud / OneDrive / Google
  Drive / Dropbox. Now every report-write path — CLI Standard /
  Suite / Regex-collection, GUI Suite runner, GUI Regex Search per-
  pattern — goes through a central policy check before any writes
  happen. Four outcomes: SAFE (proceed unchanged), REDIRECTED
  (sticky config `redirect_cloud_output=true` → silent redirect to
  `~/peekdocs_reports`), ALLOWED (CLI `--allow-cloud-output` or
  GUI "Write here anyway" → proceed with warning), PROMPT (no
  policy: CLI aborts exit 2 with instructions; GUI shows modal
  with Redirect / Write here anyway / Cancel).
- **New CLI flag `--allow-cloud-output`** — one-off override that
  lets the current run write to a cloud-synced output_dir with a
  stderr warning.
- **New config key `redirect_cloud_output`** — sticky preference
  in `~/.peekdocsrc` for users who want silent-strict enforcement
  (auditors / consultants who need the no-cloud confidentiality
  guarantee locked in).
- **New Advanced Search Options checkbox** — "Redirect cloud-synced
  output paths to ~/peekdocs_reports". Auto-saves the config key on
  toggle. Off by default (the runtime prompt still catches
  accidental leaks for users who leave this off).

### Changed
- **GUI Suite runner cloud handling upgraded.** Previously
  auto-redirected without asking (always redirected when the search
  folder was cloud-synced, no user choice). Now goes through the
  same interactive-modal policy path as other write sites so users
  who *want* their suite reports in a cloud folder (team handoff,
  for example) can still get that with one click.

### Tests
- **18 new tests in `tests/test_cloud_guard.py`**: 11 parametrized
  detection cases (iCloud / OneDrive / Google Drive / Dropbox
  variants + control paths), 7 policy-resolution tests, 2 end-to-
  end CLI tests that patch `detect_cloud_service` to simulate cloud
  detection on `tmp_path`. Total suite: 678 passing.

## [1.2.42] — 2026-06-30

### Docs
- **README — auditor / review-specialist use case added.** A new
  bullet in the visible "Who Is It For?" quick-examples list calls
  out the engagement shape (sweep a folder of contracts and
  exhibits with a saved collection of evidentiary patterns) plus
  the four capabilities that map to audit work: repeatable
  methodology, OCR for scanned exhibits, SHA-256 reproducibility,
  no-cloud confidentiality. The expandable "Detailed use cases by
  role" section gains a longer entry covering the full feature
  mapping (Suites for methodology, Regex Search workbench for
  reusable pattern collections, `--hash` for fingerprint-based
  reproducibility, DOCX / HTML reports as handoff artifacts) and —
  important — an explicit scope statement: peekdocs is a finding
  tool, not an engagement-management platform; it doesn't track
  reviewer assignments, redactions, or time. Targets the solo /
  boutique / small-firm slice; explicitly tells the enterprise-
  platform tier to pair it with whatever case-management workflow
  the firm already uses. Honors the documented voice rules — no
  regulated framework names, no peer-tool comparisons.

## [1.2.41] — 2026-06-30

### CI
- **`auto-tag-on-version-bump.yml` now actually triggers
  `build-release.yml`.** GitHub Actions has a documented anti-
  recursion rule that suppresses workflow runs for events fired
  by `GITHUB_TOKEN`. The tag push from the auto-tag workflow used
  `GITHUB_TOKEN`, so the tag-triggered build never fired —
  v1.2.32 through v1.2.40 all needed a manual `git push origin
  :refs/tags/vX.Y.Z && git tag -d vX.Y.Z && git tag -a … && git
  push` dance to get binaries built. `repository_dispatch` is on
  the exception list, so auto-tag now creates the tag *and*
  fires a `release-build` dispatch event with the tag in
  `client_payload[tag]`. `build-release.yml` listens for both
  `push: tags v*` and `repository_dispatch: release-build`, with
  the checkout step, CHANGELOG-extraction step, and
  `softprops/action-gh-release` action all falling back to
  `client_payload.tag` when triggered via dispatch. v1.2.41 is
  the first version that should fully self-build from a plain
  `pyproject.toml` bump.

### Docs
- **Focused pass on stale GUI help text.** Five categories of
  drift caught in `_mixin_tools.py`: (1) a button label name
  mismatch ("Save Settings" → "Save As Defaults"), (2) the
  Matched Files button described as "orange" in three help
  popups when it's actually green (`#81C784`), (3) the Run
  Standard Search button described as "green" in six help popup
  spots when it's actually blue (`#2196F3`), (4) the
  `_show_index_help` popup gained two bullets that mirror the
  recent USER_GUIDE clarification — Suites honor each saved
  search's Use Index flag, Regex Search never uses the index —
  so readers who reach the Index help from Tools → Indexes
  get the same answer. No production-code change; only help
  text catches up.
- **README opening paragraph rewritten** to surface the
  differentiator combination (saved-search suites, regex pattern
  workbench, OCR for scanned documents) in the first sentence
  rather than burying it in feature sections further down. No
  peer tools named, per the documented voice rule. Non-English
  intros (es / fr / de / ja / zh / pt) intentionally untouched
  per the i18n translation-scope rule.

## [1.2.40] — 2026-06-30

### Changed
- **Matched Files popup — "View Text (with line numbers)" button
  is now peekdocs green** (`#76BA1B`, hover `#5E9516`). Was a
  plain gray (`#888888`). The button is the primary action inside
  the popup that any of the three Search workflows can open, and
  the green call-out makes it stand out without falsely signaling
  the Regex Search workflow (orange is reserved for that). The
  parallel "View Text" button inside the regex-results sensitive-
  category dialog stays orange to preserve the workflow color
  rule (blue = Standard, green = Suites, orange = Regex).

## [1.2.39] — 2026-06-30

### Fixed
- **Suite runs with regex / wildcard saved searches now highlight
  matches in the Results Preview and the Matched Files popup.**
  Suite runners were passing every saved-search's `search_text`
  through `shlex.split()` to build the `display_terms` list. For
  regex and wildcard saved searches, shlex treats backslashes as
  escape characters and silently strips them — `r'print\('` became
  `'print('` (unbalanced paren), `r'console\.(?:log|debug)\('`
  became `'console.(?:log|debug)('`, etc. The downstream impact in
  the GUI: the highlighter built a single combined regex via
  `"|".join(hl_patterns)`, one malformed arm made `re.compile`
  fail, `hl_re` became `None`, the entire Results Preview showed
  zero yellow highlights, and the Matched Files popup reported
  "no matches in this file" on click — even though the subprocess
  found matches correctly (the command builder already preserved
  backslashes). Three call sites carried the bug: GUI suite runner
  (`_mixin_tools.py`), CLI `--suite` handler (`cli.py`), and the
  Python API `run_suite()` (`api.py`). All three now branch on
  `params.get('regex')` or `params.get('wildcard')` and treat the
  search_text as a single literal token in those modes — only
  shlex-splitting plain-text searches (where quoted phrases like
  `"insecure core"` still need shlex handling). The Standard
  Search highlighter (`_mixin_search.py:1067-1069`) already had
  the correct branch — only the suite paths had drifted.

### Tests
- New regression test in `tests/test_suites.py` that creates a
  suite with a single `r'print\('` regex saved search, runs it
  via `peekdocs.api.run_suite()`, and asserts the run finds
  matches AND the match text actually contains `print(`. Pinned
  end-to-end behavior so this bug can't silently re-appear.
  Suite total: 660 passing.

## [1.2.38] — 2026-06-30

### Tests
- **Cross-platform path-separator fix in `test_exclusion.py`.** The
  new `test_discover_files_skips_peekdocs_prefixed` test (added in
  1.2.37) extracted basenames with `p.split("/")[-1]`, which on
  Windows returns the full backslash-separated path (e.g.
  `C:\Users\runneradmin\...\budget.txt`) instead of `budget.txt`.
  CI failed on windows-latest / py3.12 while macOS and Linux ran
  green. Switched to `os.path.basename()` so the test passes on
  every platform. No production-code change — v1.2.37 binaries
  remain correct; only the test assertion was platform-buggy.

## [1.2.37] — 2026-06-30

### Fixed
- **Search now blanket-skips every `peekdocs_` / `.peekdocs`-
  prefixed file at discovery time.** Previously the scanner held
  an enumerated list of seven specific peekdocs prefixes to skip;
  files peekdocs writes that weren't in the list —
  `peekdocs_file_age_distribution.txt`, `peekdocs_collection_
  summary.txt`, the new `peekdocs_SHA256SUMS.txt`, and the
  `peekdocs_{regex,suite}_collection_*.json` scaffolds — would be
  searched as user content, inflating match counts and creating
  self-reference noise. New `is_peekdocs_internal_file(basename)`
  helper in `scanner.py` returns True for any name starting with
  `peekdocs_` (visible) or `.peekdocs` (hidden); the scanner's
  `discover_files` and the GUI's Find Duplicates tool both use
  it, so the two surfaces agree. Runtime now matches the
  documented "no exceptions" naming-convention rule and future
  peekdocs file types inherit the exclusion automatically.

### Scope note
- `--clear` and the Tools "list peekdocs files" cleanup paths
  intentionally still enumerate specific prefixes via
  `RESULT_FILE_PREFIXES`. Those identify peekdocs files to delete
  or show, where blanket prefix-matching could sweep unrelated
  content (e.g. `samples/peekdocs_demo_codebase/foo.py`). Search-
  time exclusion is purely additive — at worst a user-created
  `peekdocs_*.*` file is silently skipped, never deleted.

### Tests
- New `tests/test_exclusion.py` (4 tests) pins the helper's behavior
  and the end-to-end discover_files exclusion. Total suite: 659
  passing.

## [1.2.36] — 2026-06-29

### Changed
- **`SHA256SUMS.txt` renamed to `peekdocs_SHA256SUMS.txt`** in
  the release workflow so every shipped artifact follows the
  peekdocs-prefix naming convention with no exceptions. The
  release-build glob was also tightened from `sha256sum *` to
  `sha256sum peekdocs-*` so the checksums file (underscore-
  prefixed) is naturally excluded from its own hash (binaries
  use the dash variant `peekdocs-`). Downloaders of releases
  v1.2.17 through v1.2.35 still find the file under the old
  name; v1.2.36 onward uses the new name. INSTALL_SAFETY.md
  walkthrough updated accordingly.

### Docs
- **Naming convention stated explicitly in README and
  USER_GUIDE.** The rule "every file peekdocs creates uses the
  `peekdocs_` prefix (visible) or `.peekdocs` prefix (hidden) —
  no exceptions" was previously stated comprehensively only in
  the deep-dive `docs/SECURITY.md`; the two README mentions
  covered only the visible prefix. Both README's workflow-
  families overview and USER_GUIDE's file-families section now
  carry an explicit "Naming convention — no exceptions"
  blockquote with a cross-link to SECURITY.md for the per-file
  inventory. The IT/Security Q&A row and the "Not a file
  manager…" disclaimer bullet in the README were also tightened
  to cover both prefixes.

### Samples
- **Five demo scaffolds added under `samples/`** to support
  filming the Search Suites and Regex Search GUI feature
  videos. Two regex collections (Code patterns — 10 hygiene-
  themed patterns; Log triage — 10 log-severity / exception /
  HTTP-error / slow-op patterns), two suite collections (Code
  hygiene sweep — 6 saved searches; Quarterly content audit —
  6 saved searches), and one Python generator script that
  produces a `.docx` + `.pdf` consulting-doc set for the
  quarterly-audit demo. Binary outputs from the generator stay
  off-repo (reproducible from the script).

## [1.2.35] — 2026-06-29

### Docs
- **Getting Started tab + first-launch Welcome popup — six
  accuracy fixes.** Both surfaces had drifted from the current
  policy / layout: Step 3 listed `CSV / JSON / PDF / HTML (under
  'Also ==>')` even though DOCX has been in that checkbox row
  since 1.2.6 and the "Also ==>" label was removed when DOCX moved
  into column 0; the Highlighted Reports feature card claimed
  "Every search produces a Word report" (contradicts the opt-in
  policy); the Search Wizard feature card pointed to "Tools →
  Search Wizard" even though the wizard was promoted to a main-
  page button between Run Standard Search and Search Suites; Step
  4's Search Suites bullet listed the popup picker as `HTML / CSV
  / JSON / PDF` even though DOCX joined that picker in 1.2.26; and
  the first-launch Welcome popup's intro paragraph said "Results
  are saved to a highlighted Word report" and its Step 3
  walkthrough still mentioned the removed "Also ==>" label. All
  six now match current behavior.

## [1.2.34] — 2026-06-29

### Fixed
- **Broken `pip install --upgrade peekdocs` instruction** corrected
  in five user-facing locations. The CLI's ImportError handler,
  startup dependency check, `--check` missing-deps message, and the
  GUI System Check tool all told users to run that command if their
  install was broken — but peekdocs isn't on PyPI, so the command
  fails with "No matching distribution found." Replaced with
  `pipx upgrade peekdocs  (or see <readme#installation>)` so the
  instruction works regardless of which install method the user
  picked.
- **Stale "DOCX defaults ON" claim in the on-screen Step 3 tooltip
  (i18n.py)** — separate surface from the Getting Started ? popup
  corrected earlier, and was still telling users to "uncheck DOCX
  (or pass --no-docx) to skip the Word report." Updated to match
  the current policy (DOCX / CSV / JSON / PDF / HTML all default
  OFF; opt in via checkbox or `-o`).

## [1.2.33] — 2026-06-29

### Docs
- **`pipx upgrade peekdocs` is now the documented upgrade path**,
  replacing `pipx install --force git+…`. Surfaced after a Mac
  install reported the wrong version (1.2.25 under working-tree-
  loaded 1.2.32 code). Root cause: repeated `pipx install --force`
  invocations leave the previous release's `.dist-info` directories
  in the venv's site-packages, and `importlib.metadata.version()`
  picks them up alphabetically so the oldest wins. `pipx upgrade`
  replaces package contents in place and doesn't accumulate stale
  dist-info entries. Updated across README quick-start, README
  Option B, README Upgrading section, README IT/Security table,
  USER_GUIDE "tired of activating", three INSTALLATION.md commands,
  CHANGELOG upgrade-banner, and RELEASE_CHECKLIST. The Windows-
  lockup troubleshooter now covers both `pipx upgrade` and
  `pipx install --force`, and gained a stable explicit anchor so
  the cross-doc links don't rot.

### CI
- **`auto-tag-on-version-bump.yml` workflow added** (1.2.32). Every
  push to main that touches `pyproject.toml` is checked against
  existing tags; if `version = "X.Y.Z"` doesn't have a matching
  `vX.Y.Z` tag, the workflow creates and pushes it. The tag push
  then triggers the existing `build-release.yml` to build the
  Mac/Windows/Linux artifacts and create the GitHub Release.
  Closes the gap that left v1.2.26 through v1.2.32 untagged on
  GitHub while `main` advanced.

## [1.2.32] — 2026-06-29

### Docs
- **TROUBLESHOOTING DOCX opt-in sweep follow-up** (042f6f5).
  The "Where are results saved?" opener still claimed both
  `peekdocs_standard_results.txt` AND `.docx` are saved by
  default; rewritten to spell out TXT-always plus DOCX / CSV /
  JSON / PDF / HTML opt-in. The "DOCX report won't open"
  troubleshooter led with "no word processor installed" but the
  more common cause now is "DOCX wasn't checked for this run" —
  added that as the new first bullet with the red-Open-Report-
  button hint.
- **TROUBLESHOOTING "reports capped at 1,000 matches" claim
  corrected to 5,000** (3c39fca). The default-cap was bumped
  from 1,000 to 5,000 in 1.2.7; the FAQ entry hadn't caught up.
  Updated question, body, example `-m` raise-the-cap value, and
  added a note on the underlying python-docx-render-cost reason
  the cap exists.

### GUI help text
- **Regex Search ? help — workbench-doesn't-show-rows-11+
  disclosure** (d48217b). The "What This Is" section advertised
  that collections can grow beyond 10 patterns (Save Collection
  As → ADD, run via CLI / Run Multiple Collections) but glossed
  over a real gap: Restore From Collection loads only the first
  10 patterns into the workbench, and there's no GUI surface to
  view, edit, or remove rows 11+. New paragraph names the
  asymmetry plainly and points users at
  `~/.peekdocs_regex_collections.json` for editing beyond the
  workbench (plain JSON; inline schema description).
- **Surfaced the multi-collection split workaround** (67b62ab).
  Follow-up to d48217b. Most users who want to RUN more than 10
  patterns at once don't need to hand-edit JSON — they can split
  the patterns across two or more collections of ≤10 each and
  combine them via Run Multiple Collections… The help now leads
  with that simpler path and keeps the JSON hand-edit advice for
  the niche case of preserving a single >10-pattern named
  collection.

## [1.2.31] — 2026-06-28

### Docs
- **Nine stale "DOCX defaults ON" / "Suites and Regex always write
  TXT + DOCX" claims caught and corrected** across GUI help text,
  a code comment, USER_GUIDE, and WALKTHROUGHS. DOCX has been
  opt-in for Standard Search since 1.2.6, for Regex Search since
  1.2.25, and for Search Suites since 1.2.26, but the older
  always-on framing persisted in several spots. Fixed:
  - `_mixin_build.py` step-3 tooltip + Getting Started step-3 help
  - `_mixin_build.py` output-format scope tooltip
  - `_mixin_build.py` DOCX checkbox inline tooltip (Default OFF,
    not ON)
  - `cli.py` code comment on suite-handler `-o` behavior
  - USER_GUIDE Search Suites table row
  - USER_GUIDE `-o` flag table row
  - USER_GUIDE privacy section file-name list
  - WALKTHROUGHS Standard Search walkthrough (drops `--no-docx`
    framing; Regex Search has its own picker, doesn't auto-write
    DOCX)
  - WALKTHROUGHS Suites walkthrough (TXT always; DOCX is one of
    the optional checkboxes)

## [1.2.30] — 2026-06-28

### Added
- **`--suite` and `--regex-collection` now warn on stderr when
  passed flags they do not honor.** Both handlers walk argv
  manually looking only for the few flags they read (`--suite`:
  `--timestamp`, `-o`; `--regex-collection`: `-r`, `-d`, `-o`,
  `--timestamp`, `--stdout`). Anything else — `-t`, `-A`, `-B`,
  `-p`, `-P`, `-m`, `--max-file-size`, `-O`, `-n`, `--inverse`,
  `-e`, `-c` — was silently dropped, so a reasonable invocation
  like `peekdocs --regex-collection "code patterns" -t py,js -A 5
  -m 100` ran the collection with none of those filters applied
  and no signal to the user. The warning prints one stderr line
  listing the ignored flags plus a second line listing the
  supported ones; stdout, exit codes, and `--stdout` JSON
  pipelines are untouched. Three new tests pin the behavior.

## [1.2.29] — 2026-06-28

### Docs
- **Regex Search ? help "Advanced Search Options" section
  rewritten** to match real behavior. The previous text claimed
  non-screen-only Regex Search "triggers a standard search and
  respects most Advanced Search Options settings" (Max Matches,
  Max File Size, Context Lines, Output formats, File type filters,
  Exclude terms, Save report as, Delete on Close, Notify on Search
  Complete) — none of which are actually read. The Regex Search
  code path calls the in-process API with only `directory`,
  `recursive`, `use_regex=True`, `use_index=False` in both
  screen-only and non-screen-only modes. The corrected text states
  plainly that Regex Search ignores Advanced Search Options
  entirely and lists the popup's own folder / Recursive / Also-
  write checkboxes as the only inputs.
- **Step 4 (tooltip + Getting Started walkthrough)** gains a
  parallel "Advanced Search Options do NOT apply" disclaimer for
  Regex Search, matching the disclaimer that already existed for
  Search Suites.
- **Step 3 tooltip** "Regex Search always writes just TXT and
  DOCX" sentence updated; the Regex Search popup gained DOCX /
  HTML / CSV / JSON / PDF opt-in checkboxes in 1.2.25.

## [1.2.28] — 2026-06-28

### Fixed
- **`--regex-collection -o csv|json|pdf|html` no longer crashes the
  standard-search path with `UnboundLocalError`.** The 1.2.25 work
  added `from peekdocs.reporter import write_csv_report` (and
  siblings) inside `_main_inner` for the regex-collection branch.
  Those names were already imported at module level, but Python's
  scoping rules turned the local re-imports into function-local
  variables, shadowing the module bindings throughout `_main_inner`.
  Any standard-search invocation with `-o csv`, `-o json`, `-o pdf`,
  or `-o html` then hit `UnboundLocalError` at the standard-path
  write call. Removed the four shadowing imports.

### Tests
- **5 suite/regex-collection CLI tests updated to add `-o docx`**,
  catching up to the 1.2.6 / 1.2.25 opt-in DOCX policy. The tests
  still verify their original intent (`--timestamp` produces unique
  stamped filenames, the plain filename is used without
  `--timestamp`, path-prefixed `--suite` writes to the suite's
  folder); they just had to explicitly request DOCX, which is no
  longer produced by default.
- Test suite: 652 passing, 0 failing.

## [1.2.27] — 2026-06-28

### Changed
- **Open Report now uses your OS default app** for every report
  format (DOCX, PDF, CSV, JSON, plus the formats that already did).
  Previous behavior maintained a hardcoded allowlist (Microsoft Word
  / LibreOffice for DOCX, Preview / Acrobat / Skim for PDF, etc.)
  and blocked anything else with a popup recommending users install
  Word or LibreOffice. The block fired on macOS systems whose
  default `.docx` app is Pages, and the popup wording named
  competing apps directly. Reports now open with whatever app you've
  set as your OS default for that file type — the standard developer
  expectation. peekdocs itself still never uploads anything; what
  happens after the handoff to the OS is the user's chosen default.
- **Docs updated** in README, USER_GUIDE, TROUBLESHOOTING, and
  WALKTHROUGHS to drop the "peekdocs avoids opening reports in
  Google Docs / Apple Pages" promise that the new behavior no longer
  makes.

## [1.2.26] — 2026-06-28

### Fixed
- **Regex Tester "Load from file…" no longer dumps raw container
  bytes for DOCX / PDF / XLSX / archives / images.** The UTF-8
  fast-path read used `errors="replace"`, which silently "succeeds"
  on binary inputs and produced replacement-character soup (e.g.
  `PK...word/numbering.xml...`) in the sample area instead of
  routing the file through the extractor. An extension allowlist
  now sends binary container formats directly to
  `scanner._extract_lines`; plain text still takes the fast path.

## [1.2.25] — 2026-06-28

Suite-run UX polish, button-color consistency across the three
search-workflow families, and a proactive FAQ pass closing 5 of
the 14 doc gaps surfaced by the audit.

### Added
- **"Writing reports..." status** now shows between the last
  per-search update and the final results line during single-suite
  AND multi-suite runs. Closes a multi-second silent gap on big
  suites with all output formats (TXT + DOCX + HTML + CSV + JSON +
  PDF) enabled.

### Changed
- **Run Multiple Search Suites…** button in the Search Suites
  popup is now peekdocs green (`#76BA1B` / hover `#5E9516`),
  matching the main-page Search Suites button and the Run Selected
  button inside the multi-suite picker. Three suite-related
  surfaces now share one consistent "green = suite execution"
  color.
- **Run Multiple Collections…** button in the Regex Search popup
  is now peekdocs orange (`#FF9800` / hover `#F57C00`), matching
  the main-page Regex Search button. Color logic is now consistent
  across all three workflow families — **blue** = Standard Search,
  **green** = Search Suites, **orange** = Regex Search — with
  matching "Run Multiple..." buttons inheriting the family color.

### Docs
- **Search Suites `?` help gains a "Can a Suite Include Searches
  from Different Folders?" section** that directly answers no,
  explains why (suite references searches by name; names only exist
  inside one folder's collection), and lists three workarounds:
  multi-folder Standard Search via +Folder, shell loop with
  `peekdocs --suite NAME`, Python API `run_suite(name, directory=d)`.
- **5 high-priority FAQ entries added** from the proactive doc-gap
  audit. TROUBLESHOOTING.md: *"What happens if I cancel mid-run?"*,
  *"Why is peekdocs's file count different from `ls -1` / `find`?"*,
  *"Can peekdocs search inside password-protected ZIPs / PDFs?"*,
  *"Why does fuzzy search return so many results?"*. USER_GUIDE.md
  Search Index section: new *"When the index is bypassed
  automatically"* paragraph naming the four modes (fuzzy / wildcard /
  regex / expression) that fall back to direct scan and explaining
  why each does. 9 of the 14 audit gaps remain (5 medium-priority +
  4 lower-priority) for future passes.

## [1.2.24] — 2026-06-28

Search Suites UX polish — every fix here is a clarity / phrasing
tightening, no behavior changes.

### Fixed
- **Suite-run status line now says `Search [i/t] {name}…` instead of
  `Suite [i/t] {name}…`.** The counter is the search index across the
  run, but the word "Suite" next to the count visually read as "1 of
  3 suites." Especially confusing on a multi-suite run via Run
  Multiple Search Suites (e.g. two suites with 3 total searches
  looked like "3 of 3 suites" instead of "3 of 3 searches"). The
  initial line one step earlier still says `Suite: {name} (N
  searches)…` so the suite context is still established up front.

### Changed
- **"Add Search to Suite" popup now has a Close button** on its own
  row at the bottom of the popup, below the Add button. The popup
  previously only had Add; a user who opened it and decided not to
  add anything had to hunt for the window close box in the title
  bar.
- **"Nothing to add" message split into two precise variants** that
  each give the right next-step instruction:
  - *No saved searches yet* → "Save a search first (main screen →
    Save button), then come back to add it to this suite."
  - *All saved searches already in suite* → "Every saved search in
    this folder is already in this suite. Save another search first
    (main screen → Save button) before adding it here."

  Previously a single message ("No saved searches available to add —
  save a search first") fired for both cases, even though only the
  first case actually needed "save a search first" advice.

## [1.2.23] — 2026-06-26

GUI tooltip + help clarifications, two new Feature Highlights
bullets, and auto-updating release-version badges on all four
top-level doc surfaces.

### Changed
- **"Reset All Fields" help and tooltip clarified.** Both surfaces
  now explicitly say the button resets to FACTORY defaults (not the
  user-saved values from Save Defaults), and point at Restore
  Settings as the way to reload saved defaults. Each section ends
  with a cross-reference to the other (Reset All Fields ↔ Restore
  Factory Settings) so the in-session-vs-on-disk distinction is
  unambiguous.
- **Preview cap tooltip now explains *why*** matches are capped at
  all (Tk text widget gets sluggish past ~10K lines; visual scan of
  that many matches isn't useful; full result is in the report
  files regardless).

### Docs
- **Release-version badge added to the top of README, USER_GUIDE,
  API, and TROUBLESHOOTING** via shields.io's
  `github/v/release/exbuf/peekdocs` endpoint. Auto-updates on every
  tagged release; zero per-release maintenance. Lets external sites
  (e.g., a maintainer's personal website mirroring the live docs)
  confirm the displayed docs match the latest release.
- **Two new Feature Highlights bullets** (caps at 8 total — won't
  grow further): **Polished GUI** (yellow-highlighted matches,
  tooltips on every control, dark/light/system theme, adjustable
  text size, contextual `?` help popups) and **Works in any
  language** (GUI workflow translated into 7 languages, partial;
  Unicode-based exact-character matching framed honestly as "like
  most modern search tools" rather than a peekdocs-specific claim).
- **README Quick install** bullet 2 now spells out "Have Python
  3.10+?" so readers with older Pythons see the version requirement
  at the decision point.

## [1.2.22] — 2026-06-25

Test-fixture and docs accuracy maintenance.

### Fixed
- **`samples/test-files/sample.bmp` regenerated as a valid 200×60
  BMP** (was a 0-byte placeholder causing OCR to fail with "image
  file is truncated"). Post-fix verification: a recursive search
  across `samples/test-files/` with OCR enabled now succeeds on
  103 of 104 supported file types — the remaining error is the
  documented optional `sample.pst` libpff-python dependency.

### Docs
- **USER_GUIDE — two stale "Tools → Regex Search" references
  corrected** to point at the main-page Regex Search button
  (promoted from Tools menu during the 1.2.11 work alongside the
  Search Wizard).

## [1.2.21] — 2026-06-25

GUI polish on the Excluded Files popup and its chart, plus a new
worked example in the User Guide.

### Changed
- **Excluded Files popup top text** now wraps to one sentence per
  row instead of running past the popup edge ("These files were in
  your search folder but were not searched." / "Each is shown with
  the reason why.").
- **Excluded Files by Reason donut chart** redesigned: window
  bumped from 760×500 to 1100×650; reason labels moved out of the
  pie into a right-side legend (eliminates the title-vs-radial-
  label collision that no amount of padding could fix); legend
  shows full reason text plus per-reason file count; percentages
  and counts still display inside the wedges as before. The chart
  helper gained a `skip_tight_layout` opt-out used here so the
  custom subplots_adjust survives.

### Docs
- **User Guide gains Example 8** in the *Your First Advanced
  Search* section — fully worked walkthrough of "find all invoices
  over $10,000 from 2024" with both **GUI** and **CLI** surfaces
  (first example to model the cross-surface walkthrough; the
  other seven are GUI-only). Combines two range filters (amount +
  filedate) with file-type restriction and recursive search.
  Includes a *Quicker on-ramp via the Search Wizard* note pointing
  at the "Find vendor with dollar amounts in range" form for the
  keyword + amount part, with manual finish-up in Advanced Search
  Options for the rest.
- **README's Office-worker example** in the Who Is It For? table
  now cross-links to the new User Guide Example 8 so readers
  scanning the example bullets get a one-click path to the actual
  command and step-by-step.

## [1.2.20] — 2026-06-25

Docs-only release. Hero asset migrated from inline `<video>` to a
looping GIF to fix cross-browser rendering.

### Docs
- **Hero swapped from `<video>` to looping GIF (`docs/images/hero.gif`).**
  The MP4 embedded via `<video>` rendered only in Safari — Chrome
  and DuckDuckGo showed a small black box that only painted on
  click, plus a pause-blank quirk that wouldn't yield to any
  combination of `preload` / `poster` / `playsinline` attributes
  (likely a Chromium / privacy-browser CORP issue with GitHub's
  user-attachments redirect chain). Replaced with a 720p / 10fps
  palette-optimized looping GIF that renders identically on
  GitHub, PyPI, mobile, Chrome, Firefox, Safari, and DuckDuckGo.
  Sized to a fixed 720px display width via `<img width="720">`
  so cross-browser sizing is locked. ~3.4 MB on disk. The
  previously-separate static screenshot + caption are gone — the
  GIF's first frame serves the same still-image role.
- **`peekdocs-GUI.png` still in use by USER_GUIDE's GUI Mode section**
  as a layout anchor — file stays on disk, no longer referenced
  from the README.
- **HTML comment above the hero now teaches the exact ffmpeg
  one-liner** used to generate the GIF, so future re-records
  produce a drop-in replacement.

## [1.2.19] — 2026-06-25

Docs-only release.

### Docs
- **`docs/SECURITY.md` accuracy pass.** Removed 'HIPAA business
  associate agreements' from the compliance-attestation
  parenthetical (violates the standing rule about not naming
  regulated-industry compliance frameworks in user-facing docs);
  SOC 2 and ISO 27001 stay since they're general enterprise
  standards. Refreshed code line counts from the stale ~9,000
  non-GUI / ~17,000 GUI to the current ~11,000 / ~20,500 — the
  codebase has grown ~22% since that paragraph was last updated.

## [1.2.18] — 2026-06-25

Docs-only release.

### Docs
- **Glossary adds 'SLA' entry.** INSTALL_SAFETY.md uses 'no SLA'
  in its honest-limits section; the term isn't obvious to the
  non-technical downloaders that doc targets. New entry explains
  what an SLA is, what it commits a vendor to, and why peekdocs
  (solo-maintained, MIT, no commercial tier) doesn't have one.
  README Glossary count bumped to 85 in both the Documentation
  table and the standalone Glossary section paragraph.

## [1.2.17] — 2026-06-24

Trust / install-safety pass — addresses the friction non-technical
downloaders feel when GitHub serves them an unsigned binary with a
SmartScreen / Gatekeeper warning.

### Added
- **`SHA256SUMS.txt` published with every release.** New step in
  `.github/workflows/build-release.yml` runs `sha256sum *` over the
  six binaries in the release job and uploads the resulting
  `SHA256SUMS.txt` alongside them via the existing
  `softprops/action-gh-release@v2` glob. Cautious users can now
  verify their download is byte-for-byte identical to what GitHub
  Actions built. Effective on this release and later; earlier
  releases stay checksum-less.

### Docs
- **`docs/INSTALL_SAFETY.md` — new doc.** Plain-English answer to
  "is this safe to install?" — targets non-technical downloaders
  who are hesitant about unsigned GitHub binaries. Covers what
  peekdocs is and isn't, what the SmartScreen / Gatekeeper warnings
  actually mean (and why peekdocs doesn't have a code-signing cert),
  five verification paths in order of effort (checksum match,
  VirusTotal scan, network monitor, source-code grep, sandbox
  install), and honest limits (not code-signed, not third-party
  audited, MIT 'as is', solo-maintained). Linked from a callout at
  the top of the README's Installation section.
- **Glossary `Network calls` entry — tightened lead sentence.**
  Dropped the 'at runtime' qualifier; the followup sentence about
  the install-time PyPI / GitHub fetch already does the
  disambiguation work, so the lead can read 'peekdocs makes none.'
- **README Glossary section term count corrected** from 82 → 84
  (matches the Documentation table count which was already 84).

## [1.2.16] — 2026-06-24

Docs-only release.

### Docs
- **Glossary adds 'Network calls' entry.** Defines what counts as a
  network call (HTTP / DNS / telemetry / license checks / update
  checks / crash reports), peekdocs's runtime guarantee against
  making any, three platform-specific verification paths (Little
  Snitch on macOS, Resource Monitor on Windows, `lsof -i` on
  Linux), and the one install-time exception (pipx / pip fetch
  from PyPI / GitHub) so the no-network claim isn't misread as
  "never touches the network." README Documentation table term
  count corrected to 84 (was 82 in copy, but already 83 in
  reality — the new entry plus the prior drift).

## [1.2.15] — 2026-06-24

Docs-only release.

### Docs
- **Lead hook line translated into all 6 language sections.** The
  English lead "You have files. You need to find something in them."
  introduced in the marketability pass now also opens each language
  section inside the `<details>` block (Español / Français / Deutsch
  / 日本語 / 简体中文 / Português brasileiro). Translations are
  AI-drafted per the existing `CONTRIBUTING_i18n.md` disclosure and
  want native-speaker review.
- **6 language sections synced with the post-marketability English
  prolog.** Each language section: description paragraph compressed
  to ~50 words (dropped the search-mode enumeration the English
  version moved to Feature Highlights); "Built for…" line gains the
  second sentence ("No cloud, no telemetry, no network calls");
  italic "All steps are GUI-accessible…" line removed (English moved
  its content to Quick Start); new "**Typical workflow:**" bullet
  chain added.
- **Hero video caption footnotes the MacBook M4 Pro hardware** on
  the 3.17-second claim, so the speed number is anchored to the
  specific machine it was measured on.

## [1.2.14] — 2026-06-24

Docs-only release. Adds a static hero screenshot so PyPI renders
imagery above the fold, and fixes a sample-corpus extension count
contradiction between the README and the USER_GUIDE.

### Docs
- **Hero screenshot added to README and USER_GUIDE.** New
  `docs/images/peekdocs-GUI.png` shows the GUI mid-run on the same
  `budget` search the hero video demonstrates (yellow chip,
  10,411-file metric, Matched / Excluded chips, highlighted matches).
  Solves the PyPI rendering gap (PyPI strips `<video>` tags, so
  visitors landing on the project page had no imagery above the
  caption). On the README the still sits below the hero video with
  an italic subtitle; on the USER_GUIDE it anchors the GUI Mode
  section right where the prose first mentions the window. The
  `<video poster=...>` attribute also points at the new image so
  GitHub viewers see the v1.2.13 still before clicking play.
- **USER_GUIDE sample-corpus extension count corrected** from 38 to
  41 — README was already correct; the USER_GUIDE had picked up the
  file-count number (38) and mis-stated it as the distinct-extension
  count.

## [1.2.13] — 2026-06-24

Right-pane headline restyle and a timing-accuracy pass — the
right-pane elapsed figure and the left-pane status breakdown now
agree on what "search time" means.

### Added
- **`PHASE: search-done elapsed=X.XX` CLI marker.** The CLI emits
  the engine-only elapsed value to stderr when the search engine
  finishes (before report writing). The GUI picks it up via the
  existing stderr-streaming infrastructure so the right pane shows
  the search-only elapsed instead of the total subprocess time
  (which inflates by however long report writing takes).
- **Yellow highlight chip on the right-pane results headline.** The
  file count + elapsed (e.g. `10,411 files searched in 3.17s`)
  renders inside a yellow chip; the size in MB and the rest of the
  headline (match count, capped-reports note, etc.) follow in the
  normal blue color and wrap to a second line if the pane is narrow.
  File count uses thousands-separator commas.

### Changed
- **Right-pane elapsed time uses the search-engine-only value** from
  the new `PHASE: search-done` marker. Previously the right pane
  reported total subprocess time, which inflated the elapsed figure
  by the report-writing duration (e.g. "in 8.9s" when the engine
  itself ran in 3.0s).
- **Left-pane "Search complete." status now shows the phase breakdown**
  — `Search complete. (search: 3.0s, reports: 5.9s)` — so the search
  vs. report split is visible at a glance and consistent with the
  right-pane headline.
- **Right-pane results headline now leads with files searched + elapsed
  time**; match count and capped-reports notes follow.
- **Open Report buttons (TXT, DOCX, CSV, JSON, PDF, HTML)** recolored
  to the Matched / Excluded chip palette — light Material green
  (`#81C784` / hover `#66BB6A`) for "open" actions, light Material
  red (`#E57373` / hover `#EF5350`) for "delete/clear" actions. Was
  the older orange/gray palette.
- **Search Suites popup is 20% narrower** (576 px wide, was 720). The
  four-sentence top blurb now wraps one sentence per line for easier
  scanning, and adds an explicit note that the Search Folder is
  controlled by the main page's Step 1.
- **DOCX cap-status warning** now reads "for large collections" so it
  doesn't misread as a general warning on small folders.

### Fixed
- **Search Suites and Regex Search buttons stayed rectangular** after
  a run completed. Both now restore to their original 44×44 square
  shape with the stacked-label format used pre-search.

### Docs
- README hero video (`bc5feeae-a903-4614-9f8d-53bafe215935`) promoted
  above Feature Highlights with a rewritten 46-second caption matching
  the new clip (10,411 files / 3.17s / "budget"). Screenshots and
  Labeled walkthroughs sections removed from the README; WALKTHROUGHS.md
  surfaced from the Documentation table instead.
- USER_GUIDE accuracy pass: corrected three stale references to the
  Search Wizard's location (it's now a main-page button between Run
  Standard Search and Search Suites, not in the Tools menu); Getting
  Started Step 3 now uses `peekdocs budget -o docx` so the Step 4
  open-in-Word flow still works under the 1.2.6 DOCX-opt-in default.
- README accuracy pass: four stale claims fixed — Typical workflow
  ("DOCX or HTML report" reflects 1.2.6 opt-in default), Quick Start
  Step 4 (tells users to enable DOCX in Advanced Search Options
  before searching rather than assuming it's auto-generated), Quick
  Start Wizard pointer (main-page button, was Tools menu), and the
  hero-video update-instructions comment (~45s target instead of the
  stale 15-30s).
- README marketability restructure: lifted "You have files. You need
  to find something in them." to the lead (was buried at line 264);
  compressed Feature Highlights from 14 multi-line bullets in 4
  named groups to 6 one-liners with a pointer to Features for
  detail; trimmed Who Is It For? from 6 audience subsections to
  one short opener + the existing 8-row examples table.
- USER_GUIDE marketability restructure: capability-first lead
  reordering (three operational H2s — Python installation impact,
  Security Best Practices, Dependencies — moved out of the lead
  block down to the operational-concerns zone before Files Created
  by peekdocs); "Your First Advanced Search — Step by Step" (seven
  worked examples) promoted from 91% of the doc to ~15%, right
  after GUI Mode; four advanced search-mode H2s (Inverse / Boolean /
  Range / Combining) nested under one new "Advanced search modes"
  H2 (TOC entry count for that block: 14 → 6).

## [1.2.12] — 2026-06-24

Two small status-line polish fixes — both make GUI behavior easier
to interpret on first encounter.

### Added
- **`PHASE: ocr-running` status marker.** When the user enables OCR
  and runs a search, the GUI status line now reads "Running OCR —
  first run on a folder takes longer; later searches are much
  faster... (Ns elapsed)" while Tesseract is extracting text from
  images and scanned PDFs. Previously the status sat on
  "Searching..." for the whole 20–30+ second window with no
  explanation. cli.py emits the marker to stderr when `use_ocr` is
  True; GUI catches it via the existing stderr-streaming
  infrastructure (built for the DOCX status fix). When OCR results
  are already cached in the index, the marker flashes briefly and
  is superseded immediately by writing-txt — harmless.

### Changed
- Preview cap-status line — "All N matches rendered below." now
  reads "All N matches rendered alphabetically below." Adds the
  alphabetical-ordering hint that explains the Max Matches
  truncation behavior (cap of 5000 truncates at the first 5000
  alphabetically).

## [1.2.11] — 2026-06-24

Visual polish pass on the main page and Advanced Search Options panel.
Five small UX-focused changes that together make the GUI more
discoverable without changing how anything works.

### Added
- **Search Wizard button on the main page.** Promoted from the
  Tools menu (where first-time users rarely found it) into the
  run-buttons row between Run Standard Search and Search Suites.
  Same square 44×44 shape and stacked label as Suites and Regex;
  blue (`#2196F3` / `#1976D2`) matching Run Standard Search so the
  two blue buttons read as "the standard-search family." Wizard's
  intro sentence updated to reference Step 2 (search bar) and
  Step 3 (Advanced Search Options) by their step numbers, and to
  point at "Run Standard Search on the Main page" as the next
  action after Apply.

### Changed
- **Matched Files button is now light green** (`#81C784`, hover
  `#66BB6A`); **Excluded Files is light red** (`#E57373`, hover
  `#EF5350`). Replaces the previous orange/gray pair. Material
  Design 300-level palette — high enough saturation to stay
  legible with white text, light enough to read as "soft" rather
  than "alert." The inverse-search red (`#CC3333` for "files
  WITHOUT matches") is kept distinct from the new Excluded red so
  the two reds remain visually different at a glance.
- **Right-pane chart buttons ship with a visible gray button
  background.** `Match Count`, `File Types`, and `Categories` used
  `fg_color="transparent"`, so they rendered as flat text until
  the user clicked one. New users couldn't tell they were
  clickable. Now use `("gray85", "gray25")` (the post-click
  appearance) as their default fg_color; hover-color bumped to
  `("gray75", "gray35")` so the hover affordance stays visible.
- **Tools menu font size 12pt → 10pt.** Tools menu items are
  long descriptive labels ('Collection Summary — one-page overview
  combining all file-analysis insights' etc.); 12pt made the menu
  sprawl horizontally. 10pt keeps the descriptive labels intact
  without the sprawl.
- **Restrict file permissions and Max Matches / Max File Size
  swapped positions** in the Advanced Search Options panel. Max
  Matches now lives inside `output_frame` at row 2 (where Restrict
  was); Restrict lives in `advanced_frame` at row 7 (where Max
  Matches was). Max Matches is frequently tuned — especially after
  the 1.2.7 default raise to 5,000 — so giving it the more-
  discoverable higher position respects the frequency-of-use
  ordering principle for this panel; Restrict is a rarely-touched
  security setting and drops down.

## [1.2.10] — 2026-06-23

Docs-only release. The "first OCR run on a folder is dramatically
slower than subsequent runs (peekdocs caches OCR-extracted text in
the search index)" explanation was already in the OCR checkbox
tooltip and the Advanced help ? popup; this release fills in the
two user-facing spots that were missing it.

### Docs
- README OCR feature bullet — extended with the "first run is much
  slower; subsequent searches read from the cached index" note plus
  the ".peekdocs.db deletion forces the cost again" caveat.
- TROUBLESHOOTING "Can I search scanned PDFs or images?" answer —
  full paragraph added on the first-vs-subsequent-run cost
  difference. Also clarifies that regular PDFs with a text layer
  never need OCR (only image-only / scanned PDFs do).

## [1.2.9] — 2026-06-23

User-reported UX gap on the preview cap-status line. After raising
Max Matches default to 5,000 in 1.2.7, users could still hit
truncated previews and not understand why — they'd set Preview cap
to 'No cap' expecting to see everything, but the .txt report itself
was already capped at 5,000 by Max Matches before preview rendering
even started. The old cap-status line only mentioned the preview
cap, leaving the report cap invisible.

### Changed
- Preview cap-status line now distinguishes three cases instead of
  two. Priority order: **report-capped** (Max Matches limit hit;
  reads "Report capped at 5,000 of 46,741 matches (Max Matches
  limit hit). Raise Max Matches in Advanced Search Options to see
  more, or set it to 0 for unlimited. Heads-up: at unlimited, DOCX
  render can take minutes.") → **preview-capped** (existing
  "Preview shows the first M of N…" message) → **fully rendered**
  (existing "All N matches rendered below" message). `_search_finished`
  now parses `Found N match(es)` and `Reports capped at M` from CLI
  stdout to populate `self._total_match_count` and
  `self._report_cap_value`; `_update_preview_cap_status` reads
  these and adds the report-capped branch. Falls back to the pre-
  1.2.9 two-case behavior if stdout parsing fails (e.g., older CLI).

## [1.2.8] — 2026-06-23

Two first-run / factory-reset polish fixes following user testing
of the 1.2.7 build.

### Fixed
- **Split-pane sash collapse on first run / factory reset.** First
  launch puts users on the Getting Started tab; the Search tab's
  paned widget isn't mapped yet at the 1150 ms-after-deiconify
  schedule for `_set_initial_pane_split`. `winfo_width()` returned
  0, `sashpos(0, 0)` collapsed the left pane to zero width, and
  the right pane took the full screen when the user clicked Done.
  After three attempts (timer-based retry, event-driven
  `<Configure>` handler, polling with backoff) — the third
  approach landed: `_poll_apply_sash` retries `_try_apply_sash`
  every 250 ms for up to 10 s until the paned has a usable width
  (≥ 200 px) and self-stops on success. Width threshold of 200 px
  catches both unmapped width-1 and partially-laid-out narrow
  widths that would still produce a visibly collapsed split.

### Changed
- **Tooltips default OFF on first install / factory reset.**
  First-time users got a noisy hover-popup explaining things they
  were already looking at. The Tooltips: OFF button at the bottom
  toolbar flips them on; users who want them on click once and
  click Save Defaults to make ON sticky. Existing users with
  `hover_text=true` explicitly saved in `~/.peekdocsrc` still see
  tooltips ON — their preference persists. Existing users who
  never explicitly saved a hover_text preference will see tooltips
  disappear after upgrade (re-enable via the toolbar toggle).

### Docs
- USER_GUIDE chart entry-point table (lines 450–452) updated to
  the short chart-button names (`Match Count` / `File Types` /
  `Categories`); added a row for the previously-undocumented
  `Categories` button.
- USER_GUIDE Results-pane description (line 466) updated likewise.
- USER_GUIDE bottom-row description (line 468) notes Tooltips
  toggle defaults OFF on first install / factory reset as of 1.2.8.
- USER_GUIDE config-key table `max_matches` row updated from the
  old 1,000 default to the 5,000 default (with the 1.2.7
  provenance call-out).

## [1.2.7] — 2026-06-23

Max Matches default raised from 1,000 → 5,000 after real-world
demo runs ('budget' against the 5,400-file mixed corpus hit 46,741
matches) showed the lower cap was truncating common searches. 5,000
covers significantly more 'find every X' workflows without uncapping
into the minutes-long DOCX render zone — unlimited as the default
was considered and rejected because python-docx is slow at inserting
tens of thousands of highlighted runs, and a first-time user clicking
DOCX on a 50K-match search and waiting five minutes would conclude
the tool is broken. Users who genuinely want every match (typical
case: jq-pipeline scenarios with `--stdout` JSON or `-o json` where
the DOCX render cost doesn't apply) set `-m 0` for unlimited.

Bundles the 1.2.6 work (DOCX-opt-in for Standard Search) — that
release was bumped in pyproject.toml + __init__.py + CHANGELOG but
never tagged-and-pushed. The 1.2.6 section is preserved below as a
record of the DOCX-opt-in work.

### Changed
- **Max Matches default raised 1,000 → 5,000.** Affects fresh
  installs / factory-reset state; users with a saved
  `max_matches` in `~/.peekdocsrc` still get whatever they saved.
  Eight code sites updated (parser, cli, three GUI mixins, i18n);
  USER_GUIDE flag-table entry + safeguards-table entry + 'why
  raising Max File Size can show fewer matches' callout updated to
  the new default; Advanced help ? popup Max Matches section
  rewritten with the full tradeoff discussion (DOCX bottleneck,
  TXT size at huge counts, 5,000 sweet spot, unlimited via -m 0,
  the 1,000 → 5,000 provenance).
- Max Matches GUI tooltip rewritten with the same rationale — the
  cap exists to protect from minutes-long DOCX renders on huge
  result sets and from massive report files; raise it (or 0 = no
  limit) when you really want every match.

## [1.2.6] — 2026-06-23

**DOCX is now opt-in for Standard Search.** Following user feedback
that the CLI was producing a DOCX every time even when only TXT was
needed, the default flips: `peekdocs <terms>` now writes only the
`.txt` report. To get the highlighted Word report, pass
`peekdocs -o docx <terms>` (combinable: `-o docx,csv,html`). The
existing `--no-docx` flag is kept as a tolerated no-op for one
release so any scripts that pass it don't break. **Suites and
Regex collections are unchanged** — both still write TXT + DOCX
unconditionally (the user explicitly scoped the change to Standard
Search; Suites' combined DOCX is load-bearing to the workflow,
Regex's DOCX is a distinct report type).

In the GUI, the **DOCX** checkbox under Advanced Search Options
default-state flips from ON to OFF. Existing users with
`output_docx=true` in `~/.peekdocsrc` will still see the checkbox
come up checked (their preference persisted from before the change).

Also bundles two small GUI polish fixes from the same hover-test
pass: CSV / JSON / PDF / HTML PHASE markers now flash in the status
line even though they complete in milliseconds (the recurring timer
would have missed them), and the output-format checkboxes pack flush
in a sub-frame instead of inheriting the surrounding column widths
(JSON used to have a wide gap because col 2 of cb_frame was sized by
'OCR (images + scanned PDFs)' above).

### Changed
- **CLI default for DOCX flips to opt-in.** `peekdocs -o docx` now
  writes the highlighted Word report; bare `peekdocs <terms>` only
  produces `peekdocs_standard_results.txt`. Help text and `-o`
  examples updated to show `-o docx,csv,json,pdf,html`. Suites and
  Regex collections still write TXT + DOCX unconditionally.
- **GUI DOCX checkbox default flips ON → OFF.** Stored preferences
  in `~/.peekdocsrc` still take precedence on launch, so users who
  saved DOCX-on as their default still get DOCX-on. The new default
  applies only to fresh installs / factory-reset state.
- **GUI plumbs DOCX through `-o docx`** (replacing the old
  `--no-docx`-when-unchecked path). _helpers.py's
  `_build_command_from_values` `output_docx` kwarg default flips
  True → False to match the GUI checkbox.
- `--no-docx` flag is now a tolerated no-op (kept for one release
  so existing scripts don't error). USER_GUIDE flag-table entry
  marks it as deprecated.
- Documentation: README and USER_GUIDE updated in eight places to
  reflect the new opt-in behavior — main results-saved paragraph,
  FAQ entry, output-formats blockquote, `-o` flag-table entry,
  `-o` qualifier bullet, and the report-files bullet.

### Fixed
- **Fast PHASE markers now visible in the GUI status line.** CSV /
  JSON / PDF / HTML report-writes complete in milliseconds; the
  recurring 1-second elapsed-timer tick was overwriting their phase
  before the user could see it. `_update_elapsed` split into
  `_render_phase_status` (pure render) and `_update_elapsed`
  (recurring tick that renders + reschedules). The marker callback
  now schedules an immediate `_render_phase_status` via
  `self.after(0, ...)` without restarting the timer.
- **Output-format checkboxes pack flush in their own sub-frame.**
  DOCX / CSV / JSON / PDF / HTML used to share `cb_frame`'s 3-column
  grid; col 2's width is sized by the 'OCR (images + scanned PDFs)'
  checkbox above, so JSON sat in a wide cell with a big visual gap
  before PDF / HTML. New sub-frame on row 3 ignores the parent's
  column widths and packs all five buttons flush with 10-px spacing.

### Tests
- Three CLI tests (`test_search_finds_matches`, `test_search_save_
  append`, the `--on-match` hook test) updated to add `-o docx` to
  their `main(...)` invocations since they specifically verify DOCX
  output. All 652 tests pass.

## [1.2.5] — 2026-06-23

GUI chart-and-discoverability release. Three new right-pane chart
buttons surface what peekdocs found by extension, file-type
category, and match count — the differentiator-from-grep story made
visible. Matched Files / Excluded Files popups and all chart titles
now lead with the active search terms so it's always clear which
result set you're looking at. Tools → File Inventory grows a
View-by-Type (A-Z) companion popup. README first-launch security
warnings move from a hidden asterisk-footnote into inline per-platform
bypass instructions inside the download tables.

- **File Types** chart button on the right pane — opens a
  horizontal bar chart grouping the matched files by extension
  (alphabetical), with per-type match counts, a 'total matches /
  matched file types / file types searched, 100+ supported'
  composite title, and vertical scroll for result sets with many
  types.
- **Categories** chart button on the right pane — rolls
  per-extension counts up into 13 human-named buckets (Office,
  PDF, Email, Images / OCR, Archives, Code, Notebooks, Data /
  Config, Markup / Docs, Calendar / Contacts, Plain text, CAD /
  Engineering, E-books) plus 'Other'. Useful for the at-a-glance
  "where did my matches come from?" view.
- **Tools → File Inventory → View by Type (A-Z)** — second popup
  positioned to the right of the parent inventory window with the
  same per-extension counts and sizes sorted alphabetically.
- Search-terms prefix on Matched Files popup, Excluded Files popup,
  and all three right-pane chart titles. Format: `'budget' —
  Matched Files (50)` etc. Long expressions trim at 80 chars.
- README: 'GUI available in 7 languages' framing on the language
  picker summary; 'Composes with standard Unix tools' integration
  bullet; `peekdocs --dry-run` preflight example with the
  large-tree caveat.

### Changed
- Right-pane Chart button renamed to **Match Count** (was just
  'Chart') to disambiguate which dimension is being charted now
  that there are three chart options. The three chart buttons in
  the Results pane share the row as: **Match Count · File Types ·
  Categories**, each with a tooltip describing what it shows.
- OCR checkbox label expanded to **OCR (images + scanned PDFs)**.
  Regex and OCR grid positions swapped so the longer OCR label
  lives in the rightmost column where it can extend without
  pushing other checkboxes off-screen at narrow Windows sash widths.
- OCR tooltip now states explicitly that OCR is a per-search toggle
  (resets to OFF each launch; use Save Defaults to make it sticky),
  spells out the Tesseract-cost rationale, and clarifies that
  regular PDFs with a text layer are always searched regardless of
  this setting — OCR only applies to image-only / scanned PDFs.
- USER_GUIDE Advanced Search Options walkthrough gains a new
  blockquote listing which checkboxes auto-persist (Recursive,
  Whole Word, Use Index) versus which require Save Defaults (AND/OR,
  Fuzzy, Wildcard, Regex, OCR, Expression, Inverse).
- README download tables — first-launch security bypass instructions
  now inline in each cell (SmartScreen click-path for Windows,
  System Settings → Privacy & Security + xattr command for macOS,
  'no warning' for Linux) instead of behind an easy-to-miss
  asterisk-footnote link. Adds 'expected for unsigned open-source
  software, does not indicate the app is unsafe' framing.
- README tagline rewritten: 'Built for people who prefer private,
  transparent, deterministic tools. No cloud, no telemetry, no
  network calls.'
- Hero demo video URL on README swapped to the final recording.
- Stale '50,000 files' typical-workflow claims in README
  genericized to 'a folder of mixed-format documents' /
  'dozens of files or many thousands' — peekdocs has zero shipped
  users at this stage, so claiming any specific scale as 'typical'
  is aspirational. The two benchmark-table rows that report
  measured 50,000-file timings are unchanged (those are facts).
- Right-pane chart titles all now split to two lines: search terms
  on line 1, count breakdown on line 2.
- Chart-File Type Count window widens to 1100×520 with figsize
  10.6×4.8 so the long composite title fits.

### Fixed
- **Accurate report-writing status in the GUI status line.** The
  status line used to read `Searching... (Ns elapsed)` for the full
  subprocess duration — which on big result sets meant 60+ seconds
  of misleading 'Searching' while the CLI was actually writing the
  DOCX report (the slow step at tens of thousands of highlighted
  matches). cli.py now emits stable `PHASE: writing-{txt,docx,csv,
  json,pdf,html}` markers to stderr before each report-write call;
  `_run_peekdocs_cli` streams stderr line-by-line on a background
  thread and invokes a callback per line; the elapsed-timer reads
  the parsed phase and renders e.g. `Writing DOCX report... (47s
  elapsed)` instead of stale `Searching...`.
- **macOS tooltip persistence in Advanced Search Options** —
  tooltips opened, didn't close, and sat behind other windows
  until the app quit. Root cause was the earlier mac-only skip of
  `<Leave>` bindings on inner children of CTk composite widgets:
  the cursor could enter via an inner canvas/label and exit
  without ever touching the outer frame, so the outer `<Leave>`
  never fired and the hide timer never started. Re-bind `<Leave>`
  on children, bump macOS hide delay 150 ms → 300 ms so internal
  Enter/Leave bounces are absorbed by the cancel-on-Enter path,
  and replace `tw.attributes('-topmost', True)` with `tw.lift()`
  (the `-topmost` attribute doesn't reliably keep
  `wm_overrideredirect` Toplevels above the main window on Cocoa,
  which is what produced the 'sits behind' part of the symptom).

## [1.2.4] — 2026-06-22

CLI progress-feedback release. Long recursive runs (the classic
`peekdocs -r budget` launched from a home-directory parent) used to
sit silent for many minutes between the "Searching..." line and the
first result. peekdocs now prints two hints during every search: a
one-line cancel reminder right after the start banner and a
"Scanning files..." line during the file-enumeration phase before
the existing live progress bar takes over for content reads. The
"Document: " prefix on every filename line in the Results pane is
also stripped — redundant since everything peekdocs searches is a
file.

### Added
- `(Press Ctrl+C to cancel)` hint printed to stdout immediately after
  the "Searching (mode) on [folder] ..." line on every CLI search.
  Ctrl+C is universal across macOS Terminal / iTerm, Windows cmd /
  PowerShell / Windows Terminal, and any Linux terminal.
- `Scanning files (this may take a while on large folders)...`
  printed to stderr during the file-enumeration phase. The existing
  search-phase progress bar (`[██░░] N/M file.pdf ⠋`) only animates
  once content reads begin; the new hint covers the silent
  `glob.glob()`-per-extension tree walk that precedes it. Fires from
  both `_dry_run_report` and the main search path.
- New "Progress feedback during long searches" subsection in USER_GUIDE
  explaining the two phases and which feedback lands on which stream.

### Changed
- Results-pane filename lines no longer carry a leading "Document: "
  prefix. The prefix stays in the on-disk `.txt` report (PDF, Matched
  Files popup, heatmap chart, and external scripts all parse it); only
  the right-pane preview render strips it. Suites build their preview
  lines differently and never had the prefix; Regex Search renders to
  its own popup.
- README `CLI at a Glance` adds a `peekdocs --dry-run` preflight
  example and a callout explaining that home-directory or root-volume
  searches take 5–10+ minutes even for `--dry-run`, with the `-t`
  filter workaround.
- USER_GUIDE `--dry-run` flag table entry and preflight bullet
  extended with the "dry-run is the tree walk, not a free preview"
  caveat and the macOS Spotlight / iCloud `stat()`-overhead rationale.
- Right-pane **Chart** button renamed to **Chart-File Match Count**
  in all 7 languages to disambiguate which dimension is being charted
  (top 10 files by match count for the most recent search). Button
  width bumped from 70 to 180 to fit the longer label.

### Fixed
- The `Scanning files...` stderr hint was documented in 1.2.3's docs
  follow-up but the cli.py code was never actually committed; it's
  now in both the `_dry_run_report` and main search paths as the docs
  describe.

## [1.2.3] — 2026-06-22

Minor follow-up to 1.2.2 covering an i18n sweep and three hero-video
refreshes. Five widget labels on the post-1.2.0 split-pane layout
were still hardcoded English (`Search` title on the left pane,
`Open Report:` on the report row, `Chart` and `Preview cap:` on the
right pane, and the `Browse` button inside Advanced Search Options'
output-directory entry); all five now flow through the language
picker. The non-English `results_preview_label` translations had been
left as stale "X Preview" placeholders that overflowed into the
neighbouring Preview Size widget on the same row — shortened across
all six non-English languages so the right-pane title row reads
cleanly at every language. The Save tooltip on Step 2 was also
extended to mention that saved searches can be composed into Search
Suites, not just reloaded.

### Added
- Four new i18n keys (`search_pane_title`, `open_report_label`,
  `preview_cap_label`, `chart_button_label`) × 7 languages = 28 new
  translation entries.

### Changed
- Five widget labels switched from hardcoded English to i18n lookups:
  the left-pane 24pt **Search** title, the **Open Report:** row label,
  the **Chart** button, the **Preview cap:** label, and the **Browse**
  button inside the Advanced Search Options output-directory entry
  (the last reuses the existing `browse_button_label` key).
- Language-refresh callback (`_set_language`) updated to retranslate
  all five widgets on live language switch.
- `results_preview_label` shortened across all six non-English
  languages — the post-1.2.1 "Results Preview → Results" rename had
  only updated English, leaving the non-English translations as
  stale long-form strings that visually overlapped the Preview Size
  text on the same row:

  | Language | Before | After |
  |---|---|---|
  | Spanish    | Vista previa de resultados:        | Resultados |
  | French     | Aperçu des résultats :             | Résultats |
  | German     | Ergebnisvorschau:                  | Ergebnisse |
  | Japanese   | 結果プレビュー:                      | 結果 |
  | Chinese    | 结果预览：                          | 结果 |
  | Portuguese | Pré-visualização dos resultados:   | Resultados |

- `save_tooltip` first sentence updated to mention Search Suite
  composition alongside the ▶ Reload workflow.
- README hero demo video swapped to a new recording (final URL
  `b04dcd71-c62a-480b-8908-e8a724ead74e`; three intermediate swaps
  during the recording cycle).

## [1.2.2] — 2026-06-21

Bug-fix release following close hover-testing of 1.2.1 on macOS and
Windows. The headline fix restores the progress bar, which was created
correctly by the 1.2.0 split-pane redesign but rendered invisible
because its grid call landed at the same row as the relocated
status_row; the row collision made every Standard, Suite, and Regex
run feel unresponsive. Two consistency fixes round out the GUI work:
Search Suites now show the Excluded Files button (previously omitted),
and the right-pane preview now clears at the start of every Regex run
so prior Standard / Suite results don't sit there looking authoritative
while the regex popup is open.

Documentation work includes a new TROUBLESHOOTING entry for the
Windows-only pipx upgrade failure (cascading "Access is denied" errors
on locked `.pyd` / `.dll` / `python.exe` files when a peekdocs process
or a `cd`-into-the-venv terminal is still open), cross-referenced from
the upgrade bullets in README and USER_GUIDE. A sweep of stale
"TXT and DOCX always generated" claims across README, USER_GUIDE,
WALKTHROUGHS, i18n tooltips, and the Getting Started welcome cards
caught five spots that pre-dated the 1.2.0 `--no-docx` flag.

### Added
- TROUBLESHOOTING entry for the Windows-only `pipx install --force`
  failure mode where the upgrade fails with cascading "Access is
  denied" errors on `.pyd` / `.dll` / `python.exe` files. Includes the
  5-step recovery walkthrough (close peekdocs, `cd` out of the venv,
  try `pipx uninstall`, fall back to `Remove-Item`, reboot if antivirus
  still holds the locks) and a note that macOS and Linux aren't
  affected. Cross-referenced from the "Jump to your problem area"
  index in TROUBLESHOOTING and from the Option B upgrade bullets in
  README + USER_GUIDE.
- `--no-docx` row added to the CLI flag table in USER_GUIDE — the flag
  shipped in 1.2.0 but was never documented in this table.

### Changed
- Advanced Search Options tooltip now explicitly states selections take
  effect immediately on the next search — no need to press Save
  Defaults (that button persists settings for future sessions).
- Clear button in the Results pane now also wipes the results-summary
  headline ("N files searched · N matches · Ns elapsed") along with
  the preview text, Matched / Excluded buttons, and cap-status line.
- Preview cap dropdown tooltip now enumerates the configurable options
  (100 / 500 / 1000 / 5000 / No cap) instead of reading as if 500 is
  hardcoded.
- Regex Search clears the right-pane preview at run start so prior
  Standard / Suite results don't sit there looking authoritative while
  the user reads the regex results popup. Regex Search still never
  writes to the preview — its results live in the popup as before.
- Search Suites now populate and display the Excluded Files button in
  the right pane (same `_compute_excluded_files()` helper Standard
  Search uses). Previously only Standard Search showed it.
- Step 3 tooltip on the main page (`step_3_tooltip`) and the Getting
  Started welcome-card prose rewritten to remove the stale "TXT and
  DOCX reports are always generated" claim and correctly distinguish
  TXT (always), DOCX (default-on, `--no-docx` skips), and CSV / JSON /
  PDF / HTML (default-off, opt-in).

### Fixed
- **Progress bar restored.** The 1.2.0 split-pane redesign moved
  `status_row` from row 4 to row 5 of `_input_frame` but didn't
  update the `progress_bar.grid(row=5, ...)` calls in
  `_mixin_search.py` and `_mixin_tools.py`. Both widgets ended up at
  the same row; Tk stacked them and status_row visually hid the
  progress bar across all three search types. Renumbered `status_row`
  to row 6, `report_btn_frame` to row 7, `_advanced_container` to
  row 8, freeing row 5 for the progress bar to claim.
- Stale "50/50 by default" sash-split claim updated to "52%, left-pane
  biased" in README and USER_GUIDE.
- Stale "Save Search / Load Search" button names updated to "▶ Save /
  ▶ Reload" in README to match the 1.2.0 rename.
- `WALKTHROUGHS.md` walkthrough 1d and the i18n `step_3_tooltip` no
  longer claim DOCX is generated "automatically" / "always" — both
  now match the post-1.2.0 default-on-but-skippable reality.
- `USER_GUIDE.md` "Report files" prose and `-o` CLI flag description
  split correctly into TXT (always) vs DOCX (default-on, skippable)
  instead of grouping them as a single mandatory pair.

## [1.2.1] — 2026-06-19

Post-1.2.0 GUI polish driven by hover-testing the split-pane redesign
on both macOS and Windows. The Advanced Search Options panel is
reorganized so the most-frequently-used controls (Proximity / context
lines, output format checkboxes, Exclude, File types) sit above the
scroll fold; the panel's introductory paragraph moves into the `?`
help popup so it opens directly to controls. The five output-format
checkboxes (DOCX / CSV / JSON / PDF / HTML) collapse to a single row
aligned under the search-mode column grid. Use Index and Timestamp
filename pair on one row; Delete on Close and Clear history on close
pair on another. Initial sash split biases slightly to the left pane
(52%) so the format row fits at first paint. Right pane gains a 24pt
"Results" title on the top row alongside the Preview Size / Preview
cap dropdowns, mirroring a new 24pt "Search" title on the left pane.

Tooltips received a substantial rewrite to handle Cocoa quirks: a
`platform.system() == "Darwin"` flag drives several macOS-only
mitigations including a larger widget-to-tooltip gap, `withdraw` /
`deiconify` around the placeholder-paint dance, skipping `<Leave>`
binding on CTk composite children, and skipping the children-bind loop
entirely for CTkOptionMenu widgets. Cross-platform fixes include
`-topmost` on the Toplevel so it never sits behind the main window, a
defensive guard in `_show` that ignores Enter events whose cursor
position falls outside the bound widget, and a new `above-row` /
`above-row-left` anchor that top-aligns bottom-toolbar tooltips at a
common screen Y regardless of text length. The Results Preview
tooltips on the right pane were removed entirely after their
interaction proved unreadable. The Step 3 tooltip on the main page,
which had gone missing during the 1.2.0 redesign, is restored.

Documentation updates: README adds a "Composes with standard Unix
tools" headline bullet to the Integration block, naming the
`--stdout`, `--watch`, `--diff --json`, and `--runs --json` modes and
the exit-code contract. The ? help popups, tooltips, and Getting
Started body text receive a post-1.2.0 audit to remove stale
references to the pre-redesign GUI surface (the deleted main-row
checkboxes, the renamed Save / Reload buttons, the configurable
preview cap, the now-mandatory TXT report).

### Added
- `above-row` and `above-row-left` Tooltip anchor variants that
  top-align bottom-toolbar tooltips at a common screen Y.
- `position_widget` and `center` anchor on Tooltip (added during the
  Results Preview centering experiment; left in place for future use).

### Changed
- Advanced Search Options panel reorganized by frequency of use:
  Proximity row 2, output-format checkboxes row 3, Exclude row 4,
  File types row 5, Cores row 6, Max Matches row 7, Range row 8,
  Specific files row 9, Save row 10, Append row 11, Output Dir row 12,
  Use Index moved into the output_frame above Timestamp filename.
- Output-format checkboxes (DOCX / CSV / JSON / PDF / HTML) now share
  a single row in cb_frame aligned under Inverse / Expression /
  Whole Word.
- Use Index + Timestamp filename pair on one row; Delete on Close +
  Clear history on close pair on another.
- Right pane "Results Preview" title shortened to "Results", moved to
  the top row alongside Preview Size and Preview cap dropdowns at
  24pt bold to mirror a new 24pt "Search" title on the left pane.
- Initial PanedWindow sash position changed from 50% to 52% favoring
  the left pane so the five-wide format checkbox row fits at first
  paint.
- Advanced Search Options panel intro paragraph moved into the `?`
  help popup; the panel header shrinks to the `?` button alone.
- Bottom-toolbar tooltips (README, User Guide, Close, About, App Size,
  Language, Tools) switched from anchor `above` / `above-left` to the
  new `above-row` / `above-row-left` for consistent top-alignment.
- Step 2 tooltip rewritten to describe ▼ Recent / ▶ Save / ▶ Reload
  and point users at Advanced Search Options for AND/OR / Recursive /
  Whole Word / Regex; results_preview tooltip text updated to describe
  the configurable Preview cap dropdown; advanced tooltip updated to
  describe the inline expand/collapse panel.

### Fixed
- Tooltips no longer persist on Windows after the cursor leaves a
  widget (Search Suites / Regex Search buttons most visible). The
  defensive bounding-box guard in `_schedule_hide` treated genuine
  widget-exits as internal bounces.
- Tooltip jitter on macOS damped via four mitigations: larger
  widget-to-tooltip gap, withdraw/deiconify around the placeholder
  paint, skipping `<Leave>` on CTk composite children, and skipping
  the children-bind loop entirely for CTkOptionMenu widgets.
- Tooltips no longer appear partially behind the main window on macOS
  (`-topmost` attribute applied to every tooltip Toplevel).
- Step 3 tooltip restored — was missing after the 1.2.0 redesign
  turned Step 3 into a pointer to Advanced Search Options.
- DOCX / CSV / JSON / PDF / HTML checkboxes now correctly left-align
  in their cells (`sticky="w"` added; previously default-centered).
- Use Index checkbox displays in the same color as other Advanced
  panel controls when an index exists (it appeared lighter because
  the widget was put into `state="disabled"` until an index existed —
  no code change; documented in CLAUDE.md).

### Removed
- Two Results-Preview-area tooltips on the right pane (the title-label
  tooltip and the body-text tooltip). Their interaction was unreadable
  when the cursor moved between them. The same content remains
  accessible via the `?` help popups.

## [1.2.0] — 2026-06-18

Major GUI redesign and a batch of new visualizations. The Search tab
now opens as a horizontal split — scrollable controls on the left,
results preview on the right, with a draggable sash between — so the
desktop GUI reads visually the same as the experimental browser GUI
that prototyped the layout. Seven matplotlib-backed charts surface
across the Tools menu, Matched Files popup, Search History popup,
Excluded Files popup, and the results pane itself. Advanced Search
Options graduates from a separate `CTkToplevel` popup into an inline
collapsible panel in the left pane. Recent Searches now snapshots the
full search configuration (terms + folder + every Advanced Search
Options setting) instead of just the search-terms text — selecting
one from the popup restores the whole context in a single click; the
↑ / ↓ arrows in the search bar still copy only the terms. New CLI
flag `--no-docx` makes the .docx report optional. The 1.1.x → 1.2.0
bump reflects the new dependency (`matplotlib>=3.7,<4.0`), the new
CLI flag, and the Recent Searches storage format change — semantic
versioning correct.

**New dependency:** `matplotlib>=3.7,<4.0` (~10 MB). Required for the
seven chart popups. Lazy-imported on first chart click, so GUI launch
time is unaffected if you never open a chart. Stays well under the
100 MB PyPI package-size cap; airgapped / corporate-installed users
just need network access for the initial `pipx install` or `pip
install`. No new dependency in the CLI itself — `peekdocs` (the CLI
binary) runs without matplotlib installed.

**Recent Searches storage format migration:** entries in older
`~/.peekdocsrc` files round-trip as terms-only restores (the new
format is a list of dicts; the legacy format was a list of strings).
`_recent_entry_terms()` accepts either form, so the popup and the
↑ / ↓ arrows keep working immediately on upgrade. No active migration
or rewriting of the config file is performed — entries get upgraded
in place as soon as you run a search and the new snapshot pushes
older legacy entries past the 10-entry rolling window. If you want
the full-context restore right away, run any saved search via the
Reload popup, then run it once; that entry will be re-captured in the
new format and any older legacy entries with the same search terms
will be replaced.

### Added

- **Split-pane Search tab.** `ttk.PanedWindow` with a draggable
  styled sash divides the Search tab into a left pane (scrollable
  controls) and a right pane (results preview). Sash opens at the
  exact 50/50 mark on first paint (the weight=1 default in
  `ttk.PanedWindow.add` only governs how resize deltas are shared,
  not the initial position — so `_set_initial_pane_split()` forces it
  to `winfo_width() // 2` after `deiconify`). Sash is styled
  peekdocs-blue and 10 px wide with `gripcount=14`, so it's
  visible and obviously draggable; default ttk renders it as a 4 px
  hairline that users routinely failed to notice. The right pane
  shows the search-results headline at the top, the Matched /
  Excluded Files count buttons, a Preview Size / Preview cap
  dropdown row, the Results Preview label row, a cap-status line,
  and the matches themselves. The left pane carries Steps 1–4, the
  status row, the Open Report buttons, and the collapsible Advanced
  Search Options panel. The split mirrors the layout the
  experimental browser GUI prototyped on the
  `experiment/web-phase0` branch.
- **Advanced Search Options inline.** Replaces the former
  `CTkToplevel` popup with a `CTkFrame` collapsible panel gridded
  into the scrollable left pane. Header reads **▶ Advanced Search
  Options** when collapsed and **▼ Advanced Search Options** when
  expanded; clicking the header toggles the body. Inside, every
  search-tuning option from the old popup is preserved (AND/OR,
  Recursive, Fuzzy, Wildcard, OCR, Regex, Whole Word, Inverse,
  Expression, Use Index, file types, exclude terms, proximity /
  context lines, max matches, max file size, cores, range filters,
  specific files, save / append report names, output directory,
  output format checkboxes including the new DOCX toggle, timestamp
  filenames, Delete on Close, Clear history on close, Restrict
  permissions, Notify on Search Complete). Save Defaults / Restore
  Saved Defaults / Inspect .peekdocsrc / Reset All Fields / Restore
  Factory Settings all live in stacked button rows at the bottom of
  the panel.
- **Seven matplotlib chart popups.** Lazy-imported (the matplotlib
  ~300 ms first-import cost is paid only when a user actually opens a
  chart). Shared by all entry points via a single
  `_open_chart_window(title, plot_fn)` helper that handles the
  themed `Toplevel` + `FigureCanvasTkAgg` + Close button + cleanup.
  Entry points:
  - **Top 10 files by match count** — Chart button next to Clear in
    the results preview pane. Horizontal bar chart of the current
    search's matched files ranked by hit count.
  - **Per-file match heatmap** — Heatmap button per row in the
    Matched Files popup. Histogram of match positions by line
    number for the selected file, with faint blue ticks at every
    individual match line so single hits stay visible even when no
    histogram bin is tall. Useful for triaging which of many
    matching files to open first (clusters at the top of the
    document vs. scattered throughout).
  - **File Age Distribution** — View Chart button in the existing
    Tools → File Age Distribution popup. Bar chart of files per age
    bucket (today / week / month / 3 months / 6 months / 1 year /
    older).
  - **File Inventory by type** — View Chart button in the existing
    Tools → File Inventory popup. Horizontal bar of top 15
    file-type extensions by count.
  - **Largest Files size distribution** — View Chart button in the
    existing Tools → Large Files popup. Log-scale histogram with 6
    evenly-spaced tick labels (so narrow distributions — every file
    in the 100–200 MB band — get the same labelling treatment as
    wide ones spanning KB to GB).
  - **Search History timeline** — View Timeline button in the
    existing Tools → Search History popup. Twin-y line chart over
    timestamps: matches in peekdocs-blue on the left axis, elapsed
    seconds in peekdocs-green on the right axis. Pulls from
    `~/.peekdocs_history.json`.
  - **Excluded Files by reason** — View Chart button in the
    existing Excluded Files popup. Donut chart of skip-reason
    proportions (too large / password-protected / unsupported
    binary / read error / …) with the peekdocs colour palette
    cycled.
- **Recent Searches — full-config snapshot.** Each entry in the
  ▼ Recent dropdown now captures the FULL search context: the search
  terms, the search folder, and every Advanced Search Options setting
  (AND/OR, Recursive, Whole Word, Regex, Fuzzy, Wildcard, OCR,
  Expression, Inverse, Use Index, file types, exclude terms,
  proximity, context lines, CPU cores, max matches, max file size,
  range, specific files, output formats, output directory,
  timestamp, delete-on-close, clear-history-on-close, restrict
  permissions, notify on complete). Selecting an entry from the
  popup restores all of those settings in a single click. The
  ↑ / ↓ arrows in the search bar still recall the search-terms text
  only — useful when you want to reuse just the wording without
  touching your current Advanced options. Help text in the popup
  spells out both paths and the contrast.
- **DOCX checkbox + `--no-docx` CLI flag.** Standard Search now
  treats the .docx report as optional, alongside the existing
  CSV / JSON / PDF / HTML format checkboxes inside Advanced Search
  Options. DOCX defaults ON (preserving 1.1.x behaviour). Uncheck it
  to skip the .docx report and only keep the .txt report on disk.
  CLI users get the same toggle as `peekdocs --no-docx <terms>`.
  TXT remains mandatory — the GUI's preview pane and the Matched
  Files popup both parse the .txt report, and so does the matplotlib
  match heatmap, so disabling TXT would break those features. The
  TXT button's tooltip explains this; the README's "Results are
  saved to …" paragraph documents the mandatory-TXT / optional-DOCX
  split.
- **Match counting in OR mode — explained in the GUI help and
  README.** Inclusion-exclusion principle (`|A ∪ B| = |A| + |B| −
  |A ∩ B|`) explained with a worked example
  (bowling = 342, tunick = 23, bowling OR tunick = 350 → 15
  overlap) so users don't read OR matches as a counting bug. Lives
  inside Advanced Search Options → **?** help under the AND Mode
  section, and in README's Quick Start as a "Why doesn't the OR
  match count add up?" callout.
- **Heatmap definition — in-app help + README glossary.** New
  HEATMAP section in the Matched Files popup's **?** help explains
  the chart axes, how to read tall-bars-left vs tall-bars-right vs
  flat profiles, what it's useful for, and the per-match line-number
  prerequisite. `docs/GLOSSARY.md` gains a parallel Heatmap entry
  between Headless and Homebrew.

### Changed

- **Status reporting routes to the right pane; status_label stays on
  the left.** After every search-completion path, the search-results
  summary (files searched · matches · elapsed time) goes to the new
  `_results_summary_label` at the top of the right pane (bold blue,
  wraps as the sash is dragged via a `<Configure>` binding that
  recomputes wraplength dynamically). The left pane's `status_label`
  carries a short verb-form status — `"Searching {terms}…"`,
  `"Search complete."`, `"No matches found."`,
  `"Cancelling…"`, etc. — and wraps as the pane narrows. Matched /
  Excluded file count buttons relocated to the right pane below the
  headline.
- **Recent Searches button label.** `▼ Recent Searches` →
  `▼ Recent` (the popup window title stays "Recent Searches"
  unchanged, so it remains discoverable through search).
- **Open Report row.** Renamed from "View Report:". TXT is now the
  leftmost button in the row (it's the always-written report;
  putting it first matches its always-green status). Open Report row
  sits below the status row at left-pane row 6 with an "Open
  Report:" label to the left of TXT.
- **Square Suites / Regex Search buttons with stacked text.**
  `Search Suites` (green) and `Regex Search` (orange) reshaped from
  wide horizontal buttons (240 px) into ~50 × 44 squares with
  two-line stacked labels (`Search` / `Suites`, `Regex` /
  `Search`). Run Standard Search font dropped from 24 → 15 to match
  the row's reduced visual weight. The three Run buttons share the
  Step 4 row.
- **App Size + Language pickers moved to the bottom toolbar.** Both
  use a new `_UpwardOptionMenu` subclass that overrides
  `_open_dropdown_menu` to position the dropdown ABOVE the button
  instead of CTk's default below — so the dropdown doesn't overflow
  the bottom edge of the window when the user clicks them. Page
  header row at the top of the Search tab is now just the "Main
  page" label on the left.
- **Step 3 row.** Now a label-only pointer ("Use 'Advanced Search
  Options' below to configure search parameters"). The four format
  checkboxes (CSV / JSON / PDF / HTML) that used to live here are
  gone — they were always duplicates of the same `output_*_var`
  StringVars driven by the Advanced Search Options panel below.
  Selecting a format now happens in one place only.
- **Tools menu absorbs Search Wizard.** The Wizard hyperlink button
  on the main page is gone; the Wizard is launched from
  `Tools ▲ → Search Wizard — pick a search type…`.
- **Preview cap.** The 500-line cap that the preview pane used to
  apply silently is now a user-visible dropdown (100 / 500 / 1000 /
  5000 / No cap) on the Results Preview row, persisted via
  `~/.peekdocsrc`. The cap is on MATCHES, not lines (matches the
  browser-GUI convention). Below the dropdown, a status line
  (`"All N matches rendered below."` or `"Preview shows the first M
  of N matches…"`) explains what's visible, using inclusion-exclusion
  vocabulary.
- **Regex tooltip in Advanced Search Options.** Rewritten to make
  the single-pattern constraint explicit: the whole search bar is
  ONE regex pattern; spaces are part of the pattern, not separators
  between terms. Points multi-pattern users at the orange Regex
  Search button (which uses a saved collection where each pattern is
  independent and not subject to `shlex.split()` quirks). Fixes a
  long-standing surprise around `\d{3}` becoming `d{3}` after shlex
  stripping.
- **Advanced Search Options entry alignment.** Every input field in
  the panel (exclude, file types, range, specific files, cores,
  max matches, save report as, append report to, output dir) now
  sits at the same x position (col 1 of `advanced_frame`). Cores to
  Use, Max Matches + Max File Size, Save Report As, and Append
  Report To each get their own row instead of pairing horizontally.
  Use Index moved to col 0 (left-flush with the panel margin)
  instead of indented under the entry column.
- **Output formats row — 5-checkbox layout split to 3 + 2.** DOCX,
  CSV, JSON on the first internal row of `output_frame`; PDF, HTML
  on the second. The cleanup checkboxes (Add date+time, Delete on
  Close, Clear history on close, Restrict permissions, Notify on
  Search Complete) each get their own row instead of pairing.
  `output_frame` natural width dropped 33% on macOS (512 → 345 px);
  on Windows the same restructure clears the right-side clipping
  that occurred at narrow sash positions.
- **Tooltips on the bottom Advanced checkboxes** (Add date+time,
  Delete on Close, Clear history on close, Restrict permissions) all
  anchor `"above"` so they don't get clipped at the bottom of the
  collapsible panel.
- **i18n change.** `advanced_label` (English) `"Advanced"` →
  `"Advanced Search Options"`. `recent_searches_label` (English)
  `"Recent Searches"` → `"Recent"`. `clear_preview_label`
  (English) `"Clear Preview"` → `"Clear"`. `adv_also_output_label`
  (English) `"Also output report as ==>"` → `"Also ==>"`.
  Other-language values left for native-speaker corrections per
  CONTRIBUTING_i18n.md.

### Removed

- **Search Options blue bar.** The tinted blue options bar at row 2
  of the input frame (formerly holding AND/OR, Recursive, Whole
  Word, Use Index, the `?` help button, the Advanced toggle
  hyperlink, the Wizard hyperlink, and the Save / Reload group) is
  gone. Every control inside it was either relocated (Save / Reload
  next to Recent on Step 2; Use Index into Advanced; Wizard into the
  Tools menu) or deleted as a duplicate (AND/OR / Recursive / Whole
  Word lived double-bound to the Advanced panel checkboxes the
  whole time).
- **Clear button** next to Recent on Step 2. Select-all + delete in
  the search bar replaces it.
- **Step 3 format checkboxes** (CSV / JSON / PDF / HTML) — moved
  fully to Advanced Search Options (the Step 3 versions were always
  duplicates sharing the same StringVars).
- **Delete on Close checkbox** on the main page next to the open-
  report buttons — the Advanced Search Options version is the single
  source of truth now.
- **"What's the difference?" hyperlink** under the three Run
  buttons — the tooltips on Suites / Regex Search cover the same
  territory.
- **Preview pane outer box.** Removed `corner_radius` and
  `fg_color`, set padding to 0 so the matches text fills the right
  pane edge to edge.

### Fixed

- **Step 3 row disappearing on Run Standard Search.** Clicking Run
  Standard Search would turn the button red (correct) AND visually
  collapse the Step 3 label row above it, making the run row "move
  up" into Step 3's space. Root cause: `_clear_action_buttons` was
  calling `self.report_frame.grid_remove()` on every search start,
  which made sense when `report_frame` held the format checkboxes
  but became a regression after the row was reduced to a label-only
  pointer. The `grid_remove()` call and its `grid()` re-show
  counterpart in `_show_action_buttons` are gone; `report_frame`
  stays at row 3 throughout the app lifetime.
- **`preview_frame` losing its `pack()` layout after every search.**
  Three call sites in `_mixin_search.py` and `_mixin_tools.py`
  re-attached `preview_frame` with `.grid(row=7, …)` after a search,
  which switched the geometry manager back to grid and collapsed the
  frame to a tiny default-sized cell at the top of the right pane.
  All three call sites now use `.pack(fill="both", expand=True)` and
  the matching `.grid_remove()` in `_hide_preview` was switched to
  `.pack_forget()`.
- **Sash invisibility on first paint.** ttk's default sash colour is
  the same as the window background, so users routinely didn't
  realize the panes were draggable. Custom ttk style applied to the
  PanedWindow: 10 px sash, peekdocs-blue background, darker active
  state, `gripcount=14`.

## [1.1.7] — 2026-06-13

Pre-PyPI testing-phase point release adding Brazilian Portuguese (pt-BR) as the seventh UI language. No other behavior changes — the rest of the release is the surrounding paperwork (README intro block, contributor style notes, PyPI keywords). Translation quality remains AI-authored across the non-English surfaces and needs native-speaker review per language.

### Added

- **i18n — added Brazilian Portuguese (pt-BR, Português brasileiro) as the seventh language.** All 134 keys translated (938 entries total across the seven languages). Picker in the preview-header row now offers `English` / `Español` / `Français` / `Deutsch` / `日本語` / `简体中文` / `Português brasileiro`. Reasoning for the addition: Brazil has one of the largest Python developer populations on PyPI, and Portuguese-language search terms had no chance of surfacing peekdocs prior to this. Brazilian Portuguese (pt-BR, ~215M speakers) is the variant shipped; European Portuguese (pt-PT) is not currently shipped but is welcomed as a separate language entry — a Portugal-based contributor opening an issue would unblock it. Vocabulary conventions: Brazilian forms (`Arquivos` not `Ficheiros`, `Tela` not `Ecrã`), formal register on buttons (`Salvar`, `Procurar`, `Executar`), Boolean operators kept as English `AND` / `OR` (same convention as Spanish — avoids single-letter ambiguity of `E` / `OU`). The `README` button translates to `Leia-me`. PyPI discovery: added `busca-documentos` and `busca-arquivos` to the multilingual keywords in `pyproject.toml`. README intro `<details>` block gains a 🇧🇷 Português brasileiro section mirroring the structure of the other six. `CONTRIBUTING_i18n.md` extended with a Brazilian Portuguese style-notes section. Translations carry the same AI-authored caveat as the existing six languages and need native-speaker review.

## [1.1.6] — 2026-06-13

Pre-PyPI testing-phase point release. Three pieces of work since 1.1.5: a translation refinement (Spanish AND/OR), a test-infrastructure fix (integration script filename drift), and an i18n expansion batch (Tier A+B status-line messages + an enriched non-English README intro that captures the full feature set + tagline). No new features per the user's "testing and debug only before PyPI launch" stance — every change refines or fixes something that already exists.

### Fixed

- **Integration scripts — refresh stale `peekdocs_results.*` references.** Both `peekdocs_global_test_unix.sh` and `peekdocs_global_test_windows.ps1` were checking for output files named `peekdocs_results.*` — but peekdocs has produced `peekdocs_standard_results.*` (and `peekdocs_suite_results.*`, `peekdocs_regex_results.*`) since the report-prefix split that gave each search mode its own report namespace. The scripts' filename checks were therefore false positives on every CSV / JSON / HTML / timestamped report test. Before this fix the Unix integration script reported 48 passed / 8 failed on a clean 1.1.5 install — every "failure" being a `[MISSING]` marker against an outdated filename. After: **56 passed / 0 failed.** Changes: 17 references in `_unix.sh`, 23 references in `_windows.ps1`, plus both scripts' header comments now list the actual current three-prefix delete pattern (`peekdocs_standard_results*`, `peekdocs_regex_results*`, `peekdocs_suite_results*`) instead of the outdated single `peekdocs_results*` glob.

### Changed

- **Spanish AND/OR → English loanwords (avoid single-letter ambiguity).** Single-letter `Y` / `O` as button labels are linguistically correct Spanish (and the convention in Spanish Boolean search interfaces), but visually ambiguous — a Spanish-speaking user reading `[Y] [O]` on a search-mode toggle row might briefly parse them as initials before recognizing the Boolean meaning. The other six languages don't have this problem because their AND/OR forms are 2+ characters (FR `ET/OU`, DE `UND/ODER`, JA `かつ/または`, ZH `与/或`). Switching Spanish AND/OR to English loanwords matches the existing convention of keeping OCR and Regex as English loanwords in Spanish (both common in Spanish tech UIs). Five tooltip sites also updated for consistency (`and_tooltip`, `or_tooltip`, `adv_and_mode_label`, `advanced_tooltip`, `search_options_tooltip`).
- **i18n — Tier A + B status_label sweep (17 keys × 6 languages = 102 new entries).** 13 simple static status-line messages — "Copied to clipboard.", "Recent searches cleared.", "Suite cancelled.", "Regex Search cancelled.", "Cancelling multi-folder search...", "No results files to clear.", "No error log to clear.", "Error log cleared.", "No files deleted.", "No peekdocs files found to clear.", "Scanning for saved collections…", "Index build cancelled.", "Cancelling index build..." — now translate. Plus 4 format-string templates with `{n}` / `{terms}` / `{err}` placeholders for "Searching ({terms})...", "Deleted {n} results file(s).", "Deleted {n} file(s).", "Index build failed: {err}". Tier C messages (complex composed search-complete summaries with N matches + N files + elapsed time + optional skip notice; suite-progress with "N of M searches"; Wipe Session multi-line reports) still English — they compose text from too many variables to translate without restructuring. Coverage inventory in `peekdocs/i18n.py`'s module docstring updated accordingly. Total now **134 keys × 6 languages = 804 translation entries**.
- **README — expanded non-English intro paragraphs.** The `<details>`-collapsible "Non-English speakers" block now uses `###` headings per language and each paragraph captures the **full** feature set from the English opening (was a 3-sentence summary that under-sold what peekdocs does). Added: "search and analysis workbench" framing (was just "search"), the two missing search modes (proximity, range), the Office breakdown (Word / Excel / PowerPoint), email archives + ZIP/7z explicitly, scanned documents via OCR, yellow-highlighted reports, automate-recurring-searches, batch analysis, reusable search profiles, the MIT License mention, and the tagline ("Built for people who prefer local, transparent, deterministic tools.") in each language. The partial-translation note also reframed positively — leads with what IS in your language (main page, search buttons, Advanced options, common status messages) before naming what stays English (help windows, detailed dialogs, CLI, output reports). Replaces the earlier "interface partially translated" framing that under-sold available coverage.

## [1.1.5] — 2026-06-13

Point release rolling up the post-1.1.4 i18n work: a sixth language (Simplified Chinese / 简体中文), a click-test round of bug fixes across all six languages, several batches of additional translated elements (the Matched / Excluded count buttons, App Size + Preview Size labels, the App Size dropdown values themselves), a contributor-facing `CONTRIBUTING_i18n.md` inviting native-speaker corrections, and PyPI-discovery groundwork (multi-language intro paragraphs in the README plus multilingual keywords in `pyproject.toml`). Translation quality remains AI-authored across the non-English surfaces and needs native-speaker review per language; see `CONTRIBUTING_i18n.md` for how to contribute corrections.

### Added

- **i18n — added Simplified Chinese (zh-CN, 简体中文) as the sixth language.** All 102 keys translated (612 entries total across the six languages). Picker in the preview-header row now offers `English` / `Español` / `Français` / `Deutsch` / `日本語` / `简体中文`. Reasoning for the addition: the original five-language pick was a US-centric / European bias on the maintainer-AI's part; Chinese is the largest single non-English language by Python developer count on PyPI and Japanese alone doesn't really represent CJK script coverage. Simplified Chinese (`zh-CN`) covers mainland China + Singapore + Malaysia (~1B speakers); Traditional Chinese (`zh-TW`, `繁體中文`) is not currently shipped but is welcomed as a separate language entry — a Taiwan / Hong Kong contributor opening an issue would unblock it. Translations carry the same AI-authored caveat as the existing five languages, with the additional note that Chinese is particularly likely to need native-speaker idiom review (AI translation of Chinese tech UI tends to be more literal than idiomatic). The `README` button currently translates to `自述文件` (the standard Chinese translation, "self-description file"); the literal English `README` is also commonly seen in Chinese OSS and is a defensible alternative. Boolean operators (`AND` / `OR`) kept as English uppercase per the prevailing convention in Chinese tech UIs. `CONTRIBUTING_i18n.md` extended with a Simplified Chinese style-notes section.

## [1.1.4] — 2026-06-13

Point release shipping the experimental partial-i18n surface that landed over a single session. The Search workflow's most visible labels now translate across five languages — English, Español, Français, Deutsch, 日本語 — via a new `peekdocs/i18n.py` module and a language picker that lives in the preview-header row. The pattern is intentionally minimal (dict-of-dicts, no gettext / .po / .mo files, no external deps) so future extensions are mechanical. Coverage is partial by design: the main page workflow + the Advanced Search Options panel labels are translated, but help popups / dialogs / status-line dynamic text / CLI banner / report content are all still English. Treat this as polish for users who happen to read multiple languages — English remains the load-bearing UI until native-speaker review.

### Added

- **Experimental partial i18n — five languages, ~100 translated labels.** New `peekdocs/i18n.py` module (~250 lines) and a language picker in the preview-header row that lives next to the App Size dropdown. Five languages ship: **English, Español, Français, Deutsch, 日本語**. The picker drives module-level state via `set_language(code)`; widgets stashed on `self` are re-rendered via `_set_language` calling `configure(text=t(...))` per widget. Tooltip text is rewritten in place (the Tooltip class reads `self.text` lazily on each hover, so no widget recreation is needed). Language preference persists to `~/.peekdocsrc` and is restored before any widgets are built — so the first paint is in the right language. **Coverage today (~102 translation keys × 5 languages = 510 entries):** Main page workflow surface — Getting Started tab + "Main page" header + folder row (Browse / +Folder / Single File) + search row (Clear / ▼ Recent Searches) + options row (AND / OR / Recursive / Whole Word / Advanced / Use Index / Wizard / ▶ Save / ▶ Reload) + three Run buttons + the "3 Search Buttons — what's the difference?" link + Status / Results Preview / Clear Preview + bottom row (README / User Guide / Close / About / Tools ▲ / Tooltips: ON-OFF) + Delete on Close checkboxes + App Size + Language: labels. The **Advanced Search Options panel labels** are also covered (window title, 9 search-mode checkboxes, 13 form labels, 5 output-row labels, 5 bottom buttons). **NOT covered:** Advanced panel tooltips, status line dynamic text (needs format-arg templates), all help popups (~1000+ strings), Tools-menu popups (Bookmarks / Diff Snapshots / Indexes / Schedule / History / Clear Files), Search Suites popup, Regex Search popup, Search Wizard popup, dialogs / error popups, CLI banner, notifier body text, watcher status, report file content. The full coverage inventory lives in the `peekdocs/i18n.py` module docstring as the canonical reference. **Translation-quality caveat:** translations were authored by Claude (non-native for ES/FR/DE/JA). Grammar parses; idiom may not. Treat the partial i18n as **polish for users who happen to read multiple languages** — English remains the load-bearing UI until native-speaker review per language. Reset sites scattered across `_mixin_search.py`, `_mixin_data.py`, and `_mixin_tools.py` are also routed through `t()` so the active-language button text survives search-finish / cancel transitions on the three Run buttons. Universal affordances (▼ ▲ ▶ arrow indicators on dropdown / Tools / Save / Reload / Recent Searches) are concatenated at runtime, not part of any translation. CTk's tab-name identity quirk (the tab's internal name IS its lookup key) is sidestepped on the Getting Started tab by keeping the internal name English and overriding the visible button text via `_segmented_button._buttons_dict`.

## [1.1.3] — 2026-06-12

Point release rolling up the post-1.1.2 Regex Wizard work — rename, UI reuse via "Pick from Wizard…" buttons in two places (the Regex Tester and the Regex Search popup), a dedicated ? help popup explaining the OR-vs-AND choice and where each applies, and a small height bump on the picker popup. No CLI / public-API change.

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
