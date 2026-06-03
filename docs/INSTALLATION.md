# peekdocs Installation — Deep Dive

This document expands on the [Installation](../README.md#installation) section of the README. The README has the quick paths (standalone download, one-line pipx install); this document covers per-platform Python prerequisites, optional tool installation (Tesseract, UnRAR, libpff-python), and the various niche install paths (macOS Python version selection, no-git ZIP install, Windows pipx fallback, CLI-on-Windows quirks).

## Contents

- [Python prerequisites by platform](#python-prerequisites-by-platform)
- [Optional tools](#optional-tools)
- [Niche install paths](#niche-install-paths)
- [CLI-on-Windows footnotes](#cli-on-windows-footnotes)
- [Source install for contributors](#source-install-for-contributors)

## Python prerequisites by platform

peekdocs needs Python 3.10 or newer for the pipx / pip install paths (Option B). The [Standalone Download](../README.md#option-a-standalone-download-recommended-for-most-users) bundles Python and needs none of this.

**Note:** Python version numbers are not decimals — 3.13 is newer than 3.9 (it's the 13th release, not "three point one three").

### macOS

Your Mac may come with an older Python (3.9.x) pre-installed. If `python3 --version` shows 3.9.x, you need a newer version. Install from [python.org/downloads](https://www.python.org/downloads/) or via Homebrew (`brew install python`).

Installing a newer Python does **not** replace or affect the old version. Each version installs to its own folder (e.g., system Python lives at `/usr/bin/python3`, Homebrew Python at `/opt/homebrew/bin/python3.13`). They live side by side, and any programs that use the older version continue to work. After installing, the plain `python3` command may still point to the old 3.9 — use `python3.13` (or whichever version you installed) instead.

You also need tkinter for the GUI: `brew install python-tk@3.13` (replace 3.13 with your version if different).

### Windows

Windows does not come with Python pre-installed, but you may have installed it previously. Open a Command Prompt and type `python --version`. If you see a version number (e.g., `Python 3.12.4`), Python is already installed and in your PATH — you're good to go.

If the version is older than 3.10, install a newer one — it won't replace the old version (each installs to its own folder, e.g., `C:\Users\YourName\AppData\Local\Programs\Python\Python313\`).

If you see "not recognized" or the Microsoft Store opens, Python is either not installed or not in your PATH. Download it from [python.org/downloads](https://www.python.org/downloads/) and **make sure to check "Add Python to PATH"** at the bottom of the first installer screen. This ensures `pip`, `python`, and `peekdocs` commands work from any Command Prompt window. If you've already installed Python without this option, the easiest fix is to re-run the Python installer and check the box.

### Linux (Ubuntu, Debian, Linux Mint, Pop!_OS)

Most distros include Python 3.10+ already. If yours is older, you can install a newer version alongside it (e.g., via the `deadsnakes` PPA: `sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt install python3.13`) — this won't replace your system Python (it installs to `/usr/bin/python3.13` alongside the existing `/usr/bin/python3`).

The base `python3` package does not include `venv`, `pip`, or `tkinter`. You must install them before creating a virtual environment. Run this single command to get everything peekdocs needs:

```bash
sudo apt install python3-venv python3-pip python3-tk
```

Without `python3-venv` and `python3-pip`, `python3 -m venv venv` will fail with an `ensurepip` error. Without `python3-tk`, the CLI works but the GUI (`peekdocs-gui`) will not launch. This is a one-time setup.

### Tkinter (required for GUI)

- **Windows:** included automatically by the Python installer — no action needed.
- **macOS (Homebrew Python):** `brew install python-tk@3.13` (replace 3.13 with your version).
- **macOS (python.org installer):** already included.
- **Linux:** `sudo apt install python3-tk` (already in the Linux command above).

## Optional tools

These tools are only needed for specific file types or workflows. peekdocs runs fine without them — it just can't search those particular formats.

### Tesseract (for OCR)

OCR (Optical Character Recognition) reads text from scanned PDFs and images (.png, .jpg, .tiff, .bmp). Most users don't need this — it's only for documents that are pictures of text rather than actual text.

- **macOS:** `brew install tesseract`
- **Windows:** [download](https://github.com/UB-Mannheim/tesseract/wiki) — during installation, check **"Add to PATH"** so peekdocs can find it. If you missed this step, run `peekdocs --check` to confirm whether Tesseract is detected.
- **Linux:** `sudo apt install tesseract-ocr`

### UnRAR (for .rar archives)

Only needed if you want to search inside .rar files.

- **macOS:** `brew install unrar`
- **Windows:** comes with [WinRAR](https://www.win-rar.com/)
- **Linux:** `sudo apt install unrar`

### libpff-python (for .pst archives)

Only needed if you want to search inside Outlook `.pst` mailbox archives.

- **macOS:** `pip install libpff-python`
- **Linux:** `pip install libpff-python` (may need `sudo apt install build-essential` first)
- **Windows:** no working wheel — convert `.pst` to `.mbox` first using Thunderbird's ImportExportTools NG extension or the [readpst](https://github.com/pst-format/libpst) utility, then search the resulting `.mbox`. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for full details.

## Niche install paths

<a id="macos-gatekeeper"></a>
### macOS first-launch — Gatekeeper "could not be verified"

peekdocs is free, open-source, and not signed with an Apple Developer ID (the kind that costs $99/year). When you download the standalone GUI from the Releases page, macOS attaches a quarantine flag to it and refuses to open it on the first double-click. The exact warning depends on your macOS version:

- **Sequoia (macOS 15) and Sonoma (macOS 14):** dialog says "Apple could not verify..." and offers only **Done** and **Move to Trash** — *no* **Open** button.
- **Earlier macOS versions:** dialog says "...cannot be opened because the developer cannot be verified" and offers **Cancel** and **Move to Trash**, but right-clicking the app and choosing **Open** from the context menu still works.

#### Path 1 — System Settings (no terminal)

This is the recommended path on Sequoia and Sonoma since the right-click trick no longer reliably shows an Open option.

1. Click **Done** to dismiss the warning.
2. Open **System Settings → Privacy & Security**.
3. Scroll down to the *Security* section. You'll see a line like *"peekdocs-gui.app was blocked because it is not from an identified developer."* with an **Open Anyway** button.
4. Click **Open Anyway**. (macOS may prompt you for your password to confirm.)
5. macOS will show one more confirmation dialog — this one *does* have an **Open** button. Click it.
6. From then on, a regular double-click works normally.

#### Path 2 — Terminal one-liner

If you'd rather skip the System Settings detour:

```bash
xattr -dr com.apple.quarantine ~/Downloads/peekdocs-gui.app
```

This strips the quarantine flag macOS attaches to anything downloaded from the internet. After running it, double-click works on the first try. (Adjust the path if you moved the app out of `~/Downloads`. Tip: type `xattr -dr com.apple.quarantine ` with a trailing space, then drag the app onto the Terminal window to auto-fill its path.)

#### Path 3 — Right-click → Open (older macOS only)

On Ventura (macOS 13) and earlier, this is the canonical bypass:

1. Right-click (or Control-click) `peekdocs-gui.app` → **Open**.
2. The warning dialog now has an **Open** button. Click it.
3. From then on, a regular double-click works.

If you're on Sequoia or Sonoma and the right-click menu doesn't show **Open** in the warning dialog, fall back to Path 1 or Path 2.

#### Notes

- **Safari auto-unzips downloads.** If you downloaded `peekdocs-gui-macos.zip` with Safari and see `peekdocs-gui.app` directly in `~/Downloads` instead of the `.zip`, that's expected. Safari's "Open safe files after downloading" preference (on by default) auto-extracts `.zip` archives. The `.app` is ready to launch — no double-click on the zip needed.
- **The Gatekeeper bypass is per-download, not per-app.** Once you've taught macOS to trust the copy of `peekdocs-gui.app` you have right now, every subsequent double-click on *that file* works without prompts. But **every fresh download triggers Gatekeeper again** — including upgrading to a new release. The quarantine flag (`com.apple.quarantine` xattr) is attached by your browser to each downloaded file, regardless of whether you previously approved a different copy of the same app, because peekdocs isn't signed with an Apple Developer ID (which would let macOS auto-trust approved bundle IDs across downloads). So plan on running through Path 1 or Path 2 once each time you upgrade. The Terminal one-liner is the fastest path if you upgrade often.
- **No installation, no system changes.** The `.app` is a fully self-contained bundle. Drag it to `/Applications` if you want it in Launchpad, or leave it in Downloads. There's nothing to uninstall later — just delete the `.app` and (if you want a clean wipe) `~/.peekdocsrc`.

<a id="macos-cli-startup-slowness"></a>
### CLI standalone startup time — what to expect per platform (especially macOS)

The standalone CLI is a PyInstaller `--onefile` binary — a single executable that bundles its own Python interpreter and every library peekdocs uses. On every invocation, the binary extracts those bundled contents to a temp directory before any peekdocs code runs. That extraction is the dominant cost. On top of it, each OS adds its own security-check overhead that varies wildly. Rough expectations for a `peekdocs --version` invocation on the bundled CLI:

| Platform | Typical startup | What contributes |
|---|---|---|
| **macOS** | **5–7 seconds** | PyInstaller unpack (~2s) + XProtect / AMFI / Notarization round-trip on every execution of an unsigned binary (~3–4s). macOS is by far the slowest. |
| **Windows** | **2–4 seconds** | PyInstaller unpack (~2s) + Windows Defender scan of unpacked temp files (faster than macOS and aggressively cached after first scan of a given file hash). SmartScreen runs only on the first launch of a freshly-downloaded binary; subsequent runs skip it. |
| **Linux** | **0.5–1.5 seconds** | PyInstaller unpack only. No OS-level signing or notarization checks, ELF loading is the lightest of the three. |

**Why macOS is so much slower than the other two:** macOS runs XProtect (malware scan), AMFI (Apple Mobile File Integrity, kernel-level signature check), and a Notarization round-trip on every execution of an unsigned binary. Even after you remove the `com.apple.quarantine` xattr, those background checks fire on every launch because peekdocs isn't signed with an Apple Developer ID. Linux has no equivalent layers. Windows Defender does similar scanning but is significantly faster and better-cached. The actual peekdocs Python code finishes in roughly the same wall-clock time on all three platforms; the difference is the macOS security model running underneath.

#### Why the GUI standalone has no equivalent delay

The macOS GUI (`peekdocs-gui.app`) and the macOS CLI (`peekdocs`) are built differently. From `build_app.py`:

- **GUI** uses PyInstaller `--onedir` mode (the `.app` bundle is actually a folder of unpacked Python files). Nothing to extract on launch — the bundled Python and libraries are already on disk, ready to run. Launch time is normal app-startup speed (~1s).
- **CLI** uses PyInstaller `--onefile` mode (single binary). Extraction to `/var/folders/_MEIxxxxxx/` happens on every invocation.

PyInstaller documented this asymmetry: `--onefile` is being deprecated for windowed (GUI) apps because the unpack overhead is so noticeable on first launch, but it remains the standard for CLI tools that need to ship as a single distributable file. The CLI pays the unpack cost on every invocation; the GUI pays it once at build time (the unpacked files ship inside the `.app`).

That's also why a Gatekeeper warning for the GUI fires only on first launch (the `.app` bundle has a stable identity macOS can remember), while CLI invocations re-extract to fresh temp directories that macOS treats as new executions each time.

#### The `sudo mv` quarantine gotcha (macOS-specific)

`sudo mv ~/Downloads/peekdocs /usr/local/bin/peekdocs` preserves *extended attributes* on the moved file — including `com.apple.quarantine`, the flag your browser attached when you first downloaded the zip. macOS Gatekeeper sees the quarantine flag at the new path and re-verifies the binary on each launch, adding cost *on top* of the inherent CLI startup time documented above. Even if you Gatekeeper-allowed the file at the *download* location, the move to a new path can re-trigger checks because Gatekeeper's "approved" memory keys off path + code-signature, not file content.

Fix the avoidable half (xattr):

```bash
sudo xattr -dr com.apple.quarantine /usr/local/bin/peekdocs
```

One-time, immediate. Subsequent invocations skip the Gatekeeper re-verify (you still pay the inherent CLI startup, but not the Gatekeeper delta on top of it).

#### Diagnose what kind of slowness you have (macOS)

```bash
time peekdocs --version
time peekdocs --version    # run twice in the same terminal session
```

Read zsh's output for the **`total`** column (wall-clock seconds; zsh confusingly drops the `s` suffix on `total`):

- **First run ~5–7s, second run ~5–7s:** consistent PyInstaller unpack tax. Inherent for `--onefile` standalone CLIs on macOS; the only way to eliminate it is the pipx path below.
- **First run ~5–7s, second run <1s:** the first run paid a one-time XProtect / signature-check round-trip; macOS cached the result. Subsequent runs in this session (and typically for the next hour or so) skip it. You'll see the slow first run again in a fresh terminal session or after the cache expires.
- **High `total` but low `user + system` CPU time (e.g., 6.5s total / 1.1s CPU):** the binary is mostly *waiting* on macOS security checks and disk I/O, not computing. Confirms the slowness is OS overhead, not peekdocs being slow.

#### The faster alternative: pipx (any OS)

If startup time matters and you have Python installed (or are willing to install it), the pipx path skips the PyInstaller unpack entirely — pipx drops peekdocs into a real Python venv and the `peekdocs` shim invokes Python directly. Typical startup: **0.2–0.5 seconds on any OS**, regardless of macOS's security overhead, because there's no unpacked binary for macOS to inspect.

```bash
brew install pipx                                                  # macOS, if you don't have it
pipx install --force git+https://github.com/exbuf/peekdocs.git
sudo rm /usr/local/bin/peekdocs                                    # remove standalone CLI (macOS / Linux)
which peekdocs                                                     # now points at the pipx shim
```

After the switch, `peekdocs` from any terminal runs the pipx version directly — same code, same features, same exit codes; just no per-invocation extract step and no macOS security round-trip.

### macOS — choosing a Python version for pipx

If your system `python3` is still 3.9 and you installed a newer Python alongside it, tell pipx which to use:

```bash
pipx install --force --python python3.13 git+https://github.com/exbuf/peekdocs.git
```

Replace `3.13` with the version you installed.

### No git? Install from a downloaded ZIP

Download the ZIP from the green **Code** button on [github.com/exbuf/peekdocs](https://github.com/exbuf/peekdocs) and point pipx at the file instead of the URL:

```bash
pipx install --force ~/Downloads/peekdocs-main.zip                              # macOS / Linux
pipx install --force C:\Users\YourName\Downloads\peekdocs-main.zip              # Windows
```

<a id="windows-cmd-ssl"></a>
### Windows — cmd.exe SSL / SNI / certificate errors

If `pipx install` or `pip install <git-url>` fails in **Command Prompt** (`cmd.exe`) with an SSL, SNI, or certificate-validation error, but the same command works in **PowerShell**, the two terminals are routing through different Python installs. Common cause: `cmd.exe` is picking up the Microsoft Store Python stub or an older system Python with a stale `certifi` / CA bundle, while PowerShell finds your real install.

Quick check — compare the Python path between the two terminals:

```cmd
:: Command Prompt
where python
set | findstr /i "proxy cert ssl"
```

```powershell
# PowerShell
Get-Command python
Get-ChildItem env: | Where-Object Name -match 'PROXY|CERT|SSL'
```

If the two `python` paths differ: simplest fix is to **use PowerShell**. If you must install from `cmd.exe`, refresh the failing Python's pip and CA bundle:

```cmd
python -m pip install --upgrade pip certifi
```

Emergency override (only to confirm cert validation is the cause — don't leave it in your install habit, since it disables a real security check):

```cmd
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host github.com --trusted-host codeload.github.com git+https://github.com/exbuf/peekdocs.git
```

`--trusted-host` skips certificate validation for the listed hosts only. If the install succeeds with `--trusted-host` but fails without it, the root cause is certifi / CA bundle, not network reachability — fix pip + certifi as above.

### Windows pipx fallback — pipx reports success but `peekdocs` says `ModuleNotFoundError`

On some Windows machines pipx creates the venv but the package files silently fail to land in it. Install directly with pip instead — a different code path that bypasses the issue:

```powershell
python -m pip install --user --upgrade git+https://github.com/exbuf/peekdocs.git
```

`--upgrade` is the pip-side equivalent of pipx's `--force` — overwrites any existing install. Trade-off: no isolated venv (peekdocs's dependencies live alongside any other `pip --user` packages on your Python), which on a personal Windows install is typically fine.

## CLI-on-Windows footnotes

The Releases page has command-line standalone executables (`peekdocs-cli-windows.exe`, `peekdocs-cli-macos.zip`, `peekdocs-cli-linux`) alongside the GUI standalones. Two things to know if you use the CLI standalone on Windows:

1. **Run from an already-open terminal.** Double-clicking a CLI `.exe` just flashes a Command Prompt and closes — it ran with no arguments and exited. Open Command Prompt or PowerShell first, then run the executable.
2. **PowerShell and `--flag` arguments.** PowerShell rejects `--flag` arguments unless you use the `--%` stop-parsing token (e.g., `.\peekdocs-cli-windows.exe --% --check`) or switch to plain `cmd.exe`.
3. **Friendlier name.** You may rename `peekdocs-cli-windows.exe` to `peekdocs.exe` for a shorter command.
4. **`.rar` and `.pst` in the bundled CLI.** WinRAR is needed for `.rar`; `.pst` must be converted to `.mbox` first. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

**Windows standalone `.pst` note:** Neither the Windows GUI nor CLI standalone supports `.pst` (Outlook archive) files — `libpff-python` has no Windows wheel and cannot be bundled. If you need `.pst` support, install via pipx on macOS or Linux, or convert `.pst` to `.mbox` first. All other email formats (`.eml`, `.msg`, `.mbox`) work normally in the Windows standalone.

## Source install for contributors

If you want to modify peekdocs and submit changes back, see the [Development Setup](../CONTRIBUTING.md#development-setup) section of CONTRIBUTING.md. It covers the editable-mode install (`pip install -e .`), the venv activation pattern, and the test-suite invocation.
