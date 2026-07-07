# peekdocs Release Checklist

A reusable checklist for cutting a new peekdocs release. Most of the
mechanical work is automated by `.github/workflows/build-release.yml`,
which fires when you push a `v*` tag. This document covers the
preparation that comes before the tag push and the verification that
comes after — the parts that can't be automated.

**How to use this for a release:** copy the **Per-release checklist**
section below into the PR description or a scratch note, replace
`vX.Y.Z` with the actual version, and tick boxes as you go. Keep this
file as the canonical template.

---

## Background — what the workflow does for you

When you push a tag matching `v*` (e.g. `v1.2.0`):

1. **`build-release.yml`** triggers on `push: tags: 'v*'`.
2. PyInstaller builds the GUI and CLI binaries on `windows-latest`,
   `macos-latest`, and `ubuntu-latest`. Each platform produces a
   GUI binary and a CLI binary — six artifacts total.
3. The Windows CLI binary runs `tests/test_smoke_cli.py` in CI before
   any artifact uploads — a broken Windows build aborts the release.
4. The `release` job extracts the `## [vX.Y.Z]` section from
   `CHANGELOG.md` via the awk script in the workflow, writes it to
   `release_notes.md`, and feeds it to `softprops/action-gh-release@v2`
   as the release body. GitHub's auto-generated "Full Changelog: …"
   compare link gets appended after the CHANGELOG content.
5. The Release is published with the six binaries attached.

Typical end-to-end runtime: **5-6 minutes**.

Things the workflow **does not** do:
- Smoke-test the GUI binaries (only the Windows CLI is tested in CI).
- Test the standalone binaries on a real fresh machine.
- Refresh screenshots in `docs/images/`.
- Upload to PyPI (`twine upload`).

Those are the steps below.

---

## Per-release checklist

### Pre-tag — content + version

- [ ] `pyproject.toml` `version = "vX.Y.Z"` updated.
- [ ] `peekdocs/__init__.py` fallback `__version__ = "vX.Y.Z"` updated
      (keep in sync with `pyproject.toml` for the PyInstaller bundle
      path that can't read `.dist-info`).
- [ ] `CHANGELOG.md` has a new `## [vX.Y.Z] — YYYY-MM-DD` section
      under `## [Unreleased]`. Use the Keep-a-Changelog convention:
      Added / Changed / Removed / Fixed sub-sections.
- [ ] Run the full test suite: `pytest tests/` → all pass.
- [ ] All changes committed and pushed to the release branch (usually
      `main`, but a feature branch is fine if the tag is created from
      its tip).

### Tag + auto-build

- [ ] Tag the release: `git tag -a vX.Y.Z -m "vX.Y.Z — <one-line headline>"`
- [ ] Push the tag: `git push origin vX.Y.Z`
- [ ] Watch the workflow: `gh run watch` or
      https://github.com/exbuf/peekdocs/actions
- [ ] Workflow completes successfully.
- [ ] Confirm the GitHub Release page exists with all 6 binaries:
      `gh release view vX.Y.Z --json assets`

### Manual smoke test — standalone binaries

The CI smoke test covers the Windows CLI only. Verify the GUI
binaries by hand, per platform you can reach.

#### macOS

- [ ] Download `peekdocs-gui-macos.zip` from the Release page.
- [ ] Unzip, drag `peekdocs-gui.app` to `/Applications` (or run from
      `~/Downloads`).
- [ ] First launch: Gatekeeper prompt appears, right-click → Open
      works. (peekdocs is unsigned; this is expected.)
- [ ] Title bar shows `👀 peekdocs vX.Y.Z`.
- [ ] Search tab opens with horizontal split, sash draggable.
- [ ] Expand Advanced Search Options, run a search, verify the
      results headline + Matched/Excluded buttons on right pane.
- [ ] Click Chart button → matplotlib popup opens.
- [ ] Quit, relaunch — confirm Recent Searches popup restores full
      config from a prior search.
- [ ] (If applicable) verify any release-specific new feature.

#### Windows

- [ ] Download `peekdocs-gui-windows.exe` from the Release page.
- [ ] Run on a Windows machine without a prior pipx install of
      peekdocs (clean state).
- [ ] SmartScreen warning → "More info" → "Run anyway" works.
- [ ] Same GUI smoke as macOS.
- [ ] (If applicable) verify any Windows-specific fix shipped in this
      release.

#### Linux

- [ ] Download `peekdocs-gui-linux`, `chmod +x`, run.
- [ ] Same GUI smoke as macOS.
- [ ] (Optional) Test on a second distro (Ubuntu LTS + Fedora,
      Ubuntu + Debian, etc.) if available.

### Manual smoke test — pipx install path

The README documents `pipx install git+https://github.com/exbuf/peekdocs.git`
for first-time installs and `pipx upgrade peekdocs` as the upgrade
path. After a tag is pushed and `main` is updated, the upgrade
command pulls the new version.

- [ ] Run on macOS in a clean shell: install command works, no
      build failures (matplotlib wheel installs cleanly,
      tkinter is found, etc.).
- [ ] `peekdocs --version` reports `vX.Y.Z`.
- [ ] `peekdocs-gui` launches and the title bar shows the right
      version.
- [ ] Run on Windows: same verification.
- [ ] (If install fails on a specific platform): diagnose, fix,
      and either patch the package or document a workaround in
      `README.md` Option B before announcing the release.

### Documentation

- [ ] Screenshots in `docs/images/` reflect the release's GUI state.
      The hero clip in `README.md` and any walkthroughs in
      `docs/WALKTHROUGHS.md` should all show the current layout.
- [ ] `README.md` Option B install command still points at the correct
      install path (usually `git+https://github.com/exbuf/peekdocs.git`,
      sometimes `@vX.Y.Z` for pinned releases).
- [ ] `CHANGELOG.md` mentions any **new dependencies** added in this
      release (in the intro paragraph or under Added) so users know
      about the install-size delta.
- [ ] `CHANGELOG.md` mentions any **breaking changes or migrations**
      (storage format changes, removed CLI flags, etc.) so upgraders
      know what to watch for.

### PyPI upload (optional)

The GitHub Release covers both documented install paths (standalone
binaries + `pipx install git+…` / `pipx upgrade peekdocs`). PyPI upload is a separate
decision — see the maintainer's PyPI launch posture (currently
"deferred indefinitely; the GitHub-as-PyPI path is sufficient").

If you do publish:

- [ ] Verify the local build: `python -m build`
- [ ] `twine check dist/*` — validates the README rendering + PyPI
      metadata.
- [ ] `twine upload dist/*` — requires PyPI maintainer credentials.
- [ ] After upload, `pipx install peekdocs` (no `git+`) installs the
      new version.

### Post-release cleanup

- [ ] In `CHANGELOG.md`, ensure `## [Unreleased]` is back to empty
      (or has a placeholder) so the next release's changes have a
      place to land. Some maintainers prefer to keep `[Unreleased]`
      and add changes there continuously; the existing peekdocs
      pattern is to add a section per release.
- [ ] Working tree cleanup — review untracked files
      (`diff.txt`, sample artifacts in `samples/`, `docs/images/*.mp4`
      that may or may not be the latest, etc.) and decide whether
      to commit, gitignore, or just delete locally.
- [ ] Close any GitHub issues that this release fixes.
- [ ] If a feature branch was used for the release, delete it once
      `main` has absorbed the work.

---

## When something goes wrong

### The workflow fails

- Check the Actions log: `gh run view --log-failed`. The Windows
  CLI smoke test is the most common failure point — if a test
  in `tests/test_smoke_cli.py` regressed, the workflow blocks the
  release on purpose so a broken binary never publishes.
- A failed build for one platform does **not** prevent the release
  from being created — the `release` job uses
  `actions/download-artifact@v4` with `merge-multiple: true`, so
  whatever did upload gets attached. Re-run the failed job to
  produce the missing platform's binary, or delete the tag and
  re-cut after a fix.

### The release exists but a binary is wrong

- Delete the bad asset: `gh release delete-asset vX.Y.Z <name>`
- Rebuild locally (`python build_app.py`) or re-run the workflow's
  build job.
- Upload the replacement: `gh release upload vX.Y.Z <path>`

### The CHANGELOG section didn't extract

- The awk script in the workflow walks `CHANGELOG.md` for a line
  matching `## \[<version>\]`. If the tag's version doesn't match
  any `## [` heading (e.g., you tagged `v1.2.0-rc1` but the
  CHANGELOG section reads `## [1.2.0]`), the release body is just
  the auto-generated compare link.
- Fix: edit the release body manually via `gh release edit
  vX.Y.Z --notes-file <path>` after adjusting `CHANGELOG.md`.

### A user reports the standalone binary doesn't work

- Reproduce on a fresh machine matching their OS.
- If the issue is a missing system dependency
  (`libxcb-cursor0` on some Linux distros, etc.), update the README
  with the install command and consider documenting it under
  TROUBLESHOOTING.md.
- PyInstaller bundles include a Python interpreter and all peekdocs
  dependencies, but they do not include OS-level shared libraries —
  any "missing library" error is almost always an OS-level missing
  package.
