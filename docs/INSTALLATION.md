# peekdocs Installation — Deep Dive

This document expands on the [Installation](../README.md#installation) section of the README. The README has the quick paths (standalone download, one-line pipx install); this document covers per-platform Python prerequisites, optional tool installation (Tesseract, UnRAR, libpff-python), and the various niche install paths (macOS Python version selection, no-git ZIP install, Windows pipx fallback, CLI-on-Windows quirks).

## Contents

- [Python prerequisites by platform](#python-prerequisites-by-platform)
- [Optional tools](#optional-tools)
- [Niche install paths](#niche-install-paths)
- [CLI-on-Windows footnotes](#cli-on-windows-footnotes)
- [Source install for contributors](#source-install-for-contributors)

## Python prerequisites by platform

peekdocs needs Python 3.10 or newer for the pipx / pip install paths (Option B). The [Standalone Download](../README.md#1-option-a-standalone-download-no-python-needed) bundles Python and needs none of this.

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

<a id="linux-gui-first-launch"></a>
### Linux GUI first-launch — `chmod`, the `./` prefix, and common startup issues

peekdocs Linux binaries are unsigned PyInstaller bundles (~114 MB for the GUI). There's no Gatekeeper or SmartScreen equivalent on Linux — the friction is minimal: telling Linux you actually want to run the file (the executable bit) plus a small chance of one distro-specific dependency you'll need to install. This section walks through the whole path from the downloaded file to a running GUI, with troubleshooting for what can go wrong.

#### Step-by-step: from download to running

Assumes the file landed in `~/Downloads` (default for most browsers).

**1. Confirm the file downloaded fully.**

```bash
cd ~/Downloads
ls -lh peekdocs-gui-linux
```

You should see something like `-rw-r--r-- 1 you you 114M ... peekdocs-gui-linux`. If the size is noticeably smaller than ~114 MB, the download was truncated — redownload and re-check.

**2. Verify SHA-256 (optional but worth the habit).**

```bash
wget https://github.com/exbuf/peekdocs/releases/latest/download/peekdocs_SHA256SUMS.txt
sha256sum -c peekdocs_SHA256SUMS.txt --ignore-missing 2>&1 | grep peekdocs-gui-linux
```

Should print `peekdocs-gui-linux: OK`. If it says `FAILED`, the file was corrupted mid-transfer — redownload. This step is especially valuable if you're carrying the binary on a USB stick or if the network path between you and GitHub isn't fully trusted.

**3. Set the executable bit.**

```bash
chmod +x peekdocs-gui-linux
```

Linux — unlike Windows — doesn't decide runnability from the filename extension. It checks a bit in the file's permission mask. Files downloaded from a browser arrive without the executable bit set, as a safety default. `chmod +x` flips that bit, telling the kernel "yes, treat this as a program." One-time per downloaded file; every fresh download (including upgrades) needs `chmod +x` again.

**4. Run it.**

```bash
./peekdocs-gui-linux
```

The `./` prefix is required — see [Why `./` before the binary name](#linux-why-dot-slash) below. On a modern desktop with a graphical session, a peekdocs window should appear in about 0.5–1 second. First launch may be slightly slower (~1–2s) because PyInstaller unpacks the bundle to `/tmp/_MEIxxxxxx` before starting; subsequent launches are faster because the unpacked cache stays until reboot.

#### Common startup issues

**"Permission denied" from `./peekdocs-gui-linux`**
You skipped step 3 (`chmod +x`) or the executable bit didn't stick. Verify with `ls -l peekdocs-gui-linux` — the leftmost column should include an `x` (e.g., `-rwxr-xr-x`). If not, run `chmod +x peekdocs-gui-linux` again.

**"cannot execute binary file" or "Exec format error"**
The binary was built for x86-64 Linux. If your machine is ARM (Raspberry Pi, ARM-based laptops) or you're running a 32-bit distro, the x86-64 standalone won't run. Install via pipx from source instead: `pipx install git+https://github.com/exbuf/peekdocs.git`. Requires Python 3.10+ on the system.

**Nothing happens, no error, no window**
Either you're not in a graphical session (headless server, TTY console, or SSH without X11 forwarding), or an early error was suppressed. Check the display with `echo $DISPLAY` — if it's empty, you're not in an X11/Wayland session and a GUI app can't render. If you're SSH'd in, reconnect with `ssh -Y user@host` (`-Y` is more permissive than `-X` for X11 forwarding; both add `$DISPLAY` on the remote side).

**Window flashes open and closes immediately**
A Python traceback is being written to stderr faster than you can read it. Rerun and capture the output:

```bash
./peekdocs-gui-linux 2>&1 | tee /tmp/peekdocs-launch.log
```

Then read `/tmp/peekdocs-launch.log` for the error. Most common: a missing GUI-toolkit shared library (see next item).

**"ImportError" or "cannot load libxcb-cursor.so.0" (or similar libxcb libraries)**
Older or minimal distros may be missing the X11 client libraries that tkinter / customtkinter transitively use. peekdocs's PyInstaller bundle deliberately doesn't ship these because they must match your host system's X server. Install them from your distro's package manager:

```bash
# Debian, Ubuntu, Mint, Pop!_OS:
sudo apt install libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1

# Fedora, RHEL, CentOS, Rocky:
sudo dnf install libxcb-cursor libxcb-icccm libxcb-image libxcb-keysyms

# Arch, Manjaro:
sudo pacman -S libxcb
```

**SELinux "Access denied" (Fedora, RHEL, CentOS, Rocky)**
SELinux under its default policy sometimes blocks executables in `~/Downloads`. Two options: (1) move the binary to `~/.local/bin/` where SELinux's context is more permissive, or (2) explicitly restore the context: `restorecon -v peekdocs-gui-linux`. If either fails and you want to confirm SELinux is the cause, temporarily test with `sudo setenforce 0`, then re-enable with `sudo setenforce 1`. **Do not** leave SELinux in permissive mode as a workaround.

<a id="linux-why-dot-slash"></a>
#### Why `./` before the binary name

`./peekdocs-gui-linux` means "run the file called `peekdocs-gui-linux` in *this* folder." Without the `./`, your shell searches `$PATH` — a colon-separated list of directories the shell considers safe places to look for programs. The current directory (`.`) isn't on `$PATH` by default on modern Linux, macOS, and PowerShell (a security precaution — prevents accidentally running a malicious binary someone dropped into a folder you happened to `cd` into).

Once you install the binary to a folder that *is* on `$PATH` (see next section), the `./` prefix becomes unnecessary and `peekdocs-gui` works from any directory.

#### Optional: install for easy launch from anywhere

**Per-user (recommended for personal use)**:

```bash
mkdir -p ~/.local/bin
mv ~/Downloads/peekdocs-gui-linux ~/.local/bin/peekdocs-gui
```

`~/.local/bin` is on the default `$PATH` on modern distros (Ubuntu 22.04+, Fedora 34+, Debian 12+, Mint 21+). Confirm:

```bash
echo $PATH | grep -q ".local/bin" && echo "on PATH" || echo "not on PATH"
```

If it prints `not on PATH`, add it once:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

(Use `~/.zshrc` if you're on Zsh.) After that, `peekdocs-gui` from any terminal launches the app.

**System-wide (all users on the machine)**:

```bash
sudo mv ~/Downloads/peekdocs-gui-linux /usr/local/bin/peekdocs-gui
```

`/usr/local/bin` is on every user's `$PATH` by default; no shell-config edit needed. Root permissions required because `/usr/local/bin` is owned by root.

#### Notes

- **No first-launch security prompt.** Unlike macOS (Gatekeeper) or Windows (SmartScreen), Linux doesn't put unsigned binaries through a "click to allow" gate. The kernel simply refuses to execute files without the executable bit set — that's `chmod +x`'s job, no policy override needed.
- **The executable bit does not survive a fresh download.** Upgrading to a new release means running `chmod +x` on the new file. If you moved the binary to `~/.local/bin/peekdocs-gui` and want to upgrade, `chmod +x` the new download *before* replacing the old one.
- **PyInstaller unpack cost is per launch.** Every invocation of the `--onefile` bundle self-extracts to `/tmp/_MEIxxxxxx` before starting. On modern SSDs this adds ~0.5–1 second to launch time. If you launch peekdocs many times per day (unusual for GUI use), consider installing via `pipx install git+https://github.com/exbuf/peekdocs.git` — pipx gives ~0.2s launch time because there's no unpack step.
- **Wayland vs X11.** peekdocs works under both. tkinter's Wayland support runs via XWayland (a compatibility layer), so behavior may differ subtly from a native X11 session (window decorations, tooltip positioning, HiDPI scaling). Anything that looks off is worth reporting.
- **AppImage / Flatpak / Snap.** peekdocs doesn't ship as any of these today — the standalone binary is a plain PyInstaller bundle. If you want tighter sandboxing, the pipx-from-source route runs inside a Python virtual environment.

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
pipx install git+https://github.com/exbuf/peekdocs.git
sudo rm /usr/local/bin/peekdocs                                    # remove the symlink (macOS)
sudo rm -rf /usr/local/lib/peekdocs                                # remove the unpacked folder (macOS)
which peekdocs                                                     # now points at the pipx shim
```

(For subsequent upgrades, run `pipx upgrade peekdocs` — it's cleaner than `pipx install --force`, which can leave stale `.dist-info` directories around in the venv.)

After the switch, `peekdocs` from any terminal runs the pipx version directly — same code, same features, same exit codes; just no per-invocation extract step and no macOS security round-trip.

### macOS — choosing a Python version for pipx

If your system `python3` is still 3.9 and you installed a newer Python alongside it, tell pipx which to use:

```bash
pipx install --python python3.13 git+https://github.com/exbuf/peekdocs.git
```

Replace `3.13` with the version you installed.

### No git? Install from a downloaded ZIP

Download the ZIP from the **Code** button on [github.com/exbuf/peekdocs](https://github.com/exbuf/peekdocs) and point pipx at the file instead of the URL:

```bash
pipx install ~/Downloads/peekdocs-main.zip                              # macOS / Linux
pipx install C:\Users\YourName\Downloads\peekdocs-main.zip              # Windows
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

The Releases page has command-line standalone executables (`peekdocs-cli-windows.exe`, `peekdocs-cli-macos.zip`, `peekdocs-cli-linux`) alongside the GUI standalones. A few things to know if you use the CLI standalone on Windows:

1. **Run from an already-open terminal.** Double-clicking a CLI `.exe` just flashes a Command Prompt and closes — it ran with no arguments and exited. Open Command Prompt or PowerShell first, then run the executable.
2. **PowerShell and `--flag` arguments.** PowerShell rejects `--flag` arguments unless you use the `--%` stop-parsing token (e.g., `.\peekdocs-cli-windows.exe --% --check`) or switch to plain `cmd.exe`.
3. **Friendlier name.** You may rename `peekdocs-cli-windows.exe` to `peekdocs.exe` for a shorter command.
4. **`.rar` and `.pst` in the bundled CLI.** WinRAR is needed for `.rar`; `.pst` must be converted to `.mbox` first. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

**Windows standalone `.pst` note:** Neither the Windows GUI nor CLI standalone supports `.pst` (Outlook archive) files — `libpff-python` has no Windows wheel and cannot be bundled. If you need `.pst` support, install via pipx on macOS or Linux, or convert `.pst` to `.mbox` first. All other email formats (`.eml`, `.msg`, `.mbox`) work normally in the Windows standalone.

## Source install for contributors

If you want to modify peekdocs and submit changes back, see the [Development Setup](../CONTRIBUTING.md#development-setup) section of CONTRIBUTING.md. It covers the editable-mode install (`pip install -e .`), the venv activation pattern, and the test-suite invocation.
