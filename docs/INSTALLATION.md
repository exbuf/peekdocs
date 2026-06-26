# peekdocs Installation — Deep Dive

This document expands on the [Installation](../README.md#installation) section of the README. The README has the quick paths (standalone download, one-line pipx install); this document covers per-platform Python prerequisites, optional tool installation (Tesseract, UnRAR, libpff-python), and the various niche install paths (macOS Python version selection, no-git ZIP install, Windows pipx fallback, CLI-on-Windows quirks).

## Contents

- [Python prerequisites by platform](#python-prerequisites-by-platform)
- [Optional tools](#optional-tools)
- [Niche install paths](#niche-install-paths)
- [CLI-on-Windows footnotes](#cli-on-windows-footnotes)
- [Source install for contributors](#source-install-for-contributors)

## Python prerequisites by platform

peekdocs needs Python 3.10 or newer for the pipx / pip install paths (Option B). The [Standalone Download](../README.md#option-a-standalone-download-no-python-needed) bundles Python and needs none of this.

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

OCR (Optical Character Recognition) reads text from scanned PDFs and images (.png, .jpg, .tiff, .bmp). It's only needed for documents that are pictures of text (scans, screenshots, photos of a page) rather than actual text — if all your files were created digitally, you can skip this.

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
### CLI standalone startup time — what to expect per platform

The standalone CLI uses PyInstaller in different modes per platform:

- **macOS:** `--onedir` — ships as a `peekdocs/` folder containing the launcher binary plus an `_internal/` directory with Python and the bundled libraries already extracted. No per-launch unpack cost.
- **Windows and Linux:** `--onefile` — a single binary that self-extracts to a temp directory on every invocation. Self-extraction is the dominant cost on these platforms.

Typical wall-clock startup for `peekdocs --version`:

| Platform | Typical startup | What contributes |
|---|---|---|
| **macOS** | **~1–2 seconds** | XProtect / AMFI signature check on every execution of an unsigned binary (cached for ~1 hour after first run). No PyInstaller unpack — that cost was eliminated when the macOS CLI moved from `--onefile` to `--onedir`, matching how the GUI `.app` ships. |
| **Windows** | **2–4 seconds** | PyInstaller `--onefile` self-extraction + Defender scan of unpacked temp files (cached after first scan of a given file hash). SmartScreen runs only on the first launch of a freshly-downloaded binary. |
| **Linux** | **0.5–1.5 seconds** | PyInstaller `--onefile` self-extraction. No OS-level signing or notarization checks. |

#### The `sudo mv` quarantine gotcha (macOS-specific)

Moving the `peekdocs/` folder into a system location preserves *extended attributes*, including `com.apple.quarantine` — the flag your browser attached when you first downloaded the zip. macOS Gatekeeper sees that flag at the new path and re-verifies the binary on each launch, adding cost on top of the inherent startup time documented above. Remove the attribute once after moving:

```bash
sudo xattr -dr com.apple.quarantine /usr/local/lib/peekdocs
```

(Adjust the path if you put the folder somewhere other than `/usr/local/lib/peekdocs/`.) One-time, immediate; subsequent invocations skip the Gatekeeper re-verify.

#### The faster alternative: pipx (any OS)

If startup time still matters and you have Python installed (or are willing to install it), the pipx path skips the PyInstaller pipeline entirely — pipx drops peekdocs into a real Python venv and the `peekdocs` shim invokes Python directly. Typical startup: **0.2–0.5 seconds on any OS**.

```bash
brew install pipx                                                  # macOS, if you don't have it
pipx install peekdocs                                              # from PyPI (released version)
sudo rm /usr/local/bin/peekdocs                                    # remove the symlink (macOS)
sudo rm -rf /usr/local/lib/peekdocs                                # remove the unpacked folder (macOS)
which peekdocs                                                     # now points at the pipx shim
```

After the switch, `peekdocs` from any terminal runs the pipx version directly — same code, same features, same exit codes; just no per-invocation extract step and no macOS security round-trip.

### macOS — choosing a Python version for pipx

If your system `python3` is still 3.9 and you installed a newer Python alongside it, tell pipx which to use:

```bash
pipx install --python python3.13 peekdocs
```

Replace `3.13` with the version you installed.

### No internet at install time? Install from a downloaded ZIP

Download the ZIP from the **Code** button on [github.com/exbuf/peekdocs](https://github.com/exbuf/peekdocs) and point pipx at the file instead of fetching from PyPI:

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
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org peekdocs
```

`--trusted-host` skips certificate validation for the listed hosts only. If the install succeeds with `--trusted-host` but fails without it, the root cause is certifi / CA bundle, not network reachability — fix pip + certifi as above.

### Windows pipx fallback — pipx reports success but `peekdocs` says `ModuleNotFoundError`

On some Windows machines pipx creates the venv but the package files silently fail to land in it. Install directly with pip instead — a different code path that bypasses the issue:

```powershell
python -m pip install --user --upgrade peekdocs
```

`--upgrade` overwrites any existing install. Trade-off: no isolated venv (peekdocs's dependencies live alongside any other `pip --user` packages on your Python), which on a personal Windows install is typically fine.

## CLI-on-Windows footnotes

The Releases page has command-line standalone executables (`peekdocs-cli-windows.exe`, `peekdocs-cli-macos.zip`, `peekdocs-cli-linux`) alongside the GUI standalones. A few things to know if you use the CLI standalone on Windows:

1. **Run from an already-open terminal.** Double-clicking a CLI `.exe` just flashes a Command Prompt and closes — it ran with no arguments and exited. Open Command Prompt or PowerShell first, then run the executable.
2. **PowerShell and `--flag` arguments.** PowerShell rejects `--flag` arguments unless you use the `--%` stop-parsing token (e.g., `.\peekdocs-cli-windows.exe --% --check`) or switch to plain `cmd.exe`.
3. **Friendlier name.** You may rename `peekdocs-cli-windows.exe` to `peekdocs.exe` for a shorter command.
4. **`.rar` and `.pst` in the bundled CLI.** WinRAR is needed for `.rar`; `.pst` must be converted to `.mbox` first. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

**Windows standalone `.pst` note:** Neither the Windows GUI nor CLI standalone supports `.pst` (Outlook archive) files — `libpff-python` has no Windows wheel and cannot be bundled. If you need `.pst` support, install via pipx on macOS or Linux, or convert `.pst` to `.mbox` first. All other email formats (`.eml`, `.msg`, `.mbox`) work normally in the Windows standalone.

## Source install for contributors

If you want to modify peekdocs and submit changes back, see the [Development Setup](../CONTRIBUTING.md#development-setup) section of CONTRIBUTING.md. It covers the editable-mode install (`pip install -e .`), the venv activation pattern, and the test-suite invocation.
