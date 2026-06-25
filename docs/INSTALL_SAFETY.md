# Is peekdocs safe to install?

If you're cautious about downloading apps from GitHub — good. That's a sensible default. This page lays out what peekdocs is, what it does and doesn't do, what your operating system's warnings actually mean, and how to verify the download yourself if you want to.

---

## What peekdocs is, in plain English

peekdocs is a free, open-source program for searching the text inside your files. It runs on your computer, reads files you already have, and shows you which ones contain what you searched for. That's all.

- **Local.** Everything happens on your machine. peekdocs has no website, no account, no cloud back-end, no servers — nothing for your documents to be uploaded *to*.
- **Read-only.** peekdocs opens your files to read them. It does not write to them, rename them, move them, or delete them. The only files peekdocs creates are its own search-result reports (`.txt`, `.docx`, etc.) and an optional cached search index, both saved alongside your documents in the folder you chose. You control where those go.
- **No network calls.** While peekdocs is running, it never opens an internet connection. No telemetry, no "check for updates," no license check, no crash reports, no analytics — nothing leaves your machine. You can verify this yourself; see [How to verify](#how-to-verify) below.
- **Open source under the MIT License.** Every line of code is on [GitHub](https://github.com/exbuf/peekdocs). Anyone — including independent security researchers — can read it, audit it, modify it, and republish it.

---

## What your operating system's warning actually means

The first time you run peekdocs after downloading the standalone version, your operating system will show a warning:

- **Windows:** "Microsoft Defender SmartScreen prevented an unrecognized app from starting." Click **More info** → **Run anyway**.
- **macOS:** "peekdocs can't be opened because Apple cannot check it for malicious software." Open **System Settings → Privacy & Security**, scroll to the bottom, and click **Open Anyway**.
- **Linux:** No system-level warning, but the downloaded file isn't marked as executable. Run `chmod +x peekdocs-gui-linux` once.

**These warnings appear for every unsigned download, regardless of whether the program is safe or not.** They are not a malware verdict. They mean: *the operating system has not received a signed certificate from the developer telling it who made this file.* Code-signing certificates cost $99–$800 per year per platform, and peekdocs — a solo, no-revenue, MIT-licensed project — does not have one. The same warnings appear when you download many widely-used open-source tools (FFmpeg, MKVToolNix, HandBrake for some versions, ImageMagick) from their own websites.

For full per-platform install walkthroughs including these warnings, see the [main Installation section in the README](../README.md#installation) and the [Troubleshooting guide](TROUBLESHOOTING.md).

---

## How to verify

In order of effort, lowest to highest:

### 1. Check the published checksum

Every peekdocs release includes a SHA-256 checksum for each binary on the [Releases page](https://github.com/exbuf/peekdocs/releases/latest). After you download, run a one-liner that computes the SHA-256 of the file you have and compares it to the one published:

- **Windows (PowerShell):** `Get-FileHash peekdocs-gui-windows.exe -Algorithm SHA256`
- **macOS:** `shasum -a 256 peekdocs-gui-macos.zip`
- **Linux:** `sha256sum peekdocs-gui-linux`

If the value matches the one on the release page, you have the exact file that was built by GitHub Actions from the source code — not something an attacker substituted in transit.

### 2. Scan it with VirusTotal

Upload the downloaded file (or paste its SHA-256 checksum) to [virustotal.com](https://www.virustotal.com/). VirusTotal runs the file through 60+ antivirus engines and shows you a consolidated verdict.

Note: unsigned binaries from small developers occasionally pick up one or two false positives from less-popular engines that flag *any* unsigned PyInstaller-packaged Python program. A clean scan is ideal; a near-clean scan (with only obscure engines disagreeing) is normal for unsigned open-source software.

### 3. Watch the network with your eyes

To confirm peekdocs makes no internet connections while it runs:

- **macOS:** Install [Little Snitch](https://www.obdev.at/products/littlesnitch), launch peekdocs-gui, and run a search. Little Snitch will alert you to any outbound network attempt. peekdocs should make none.
- **Windows:** Open **Task Manager → Performance → Open Resource Monitor → Network tab**. Watch the per-process network activity while peekdocs runs. peekdocs-gui should show 0 bytes sent and 0 bytes received.
- **Linux:** Run `sudo lsof -i -P | grep peekdocs` in a terminal while peekdocs is running. The command should return nothing.

### 4. Read the source

Every release is built from the [public source code](https://github.com/exbuf/peekdocs) on GitHub. Look for `import requests`, `import urllib`, `import socket`, `import http`, `import aiohttp` — any of the standard Python ways to make a network call. You won't find them. The [Glossary](GLOSSARY.md) lists these libraries explicitly, partly so cautious users can grep for them.

You don't have to be a Python programmer to do this. GitHub's search box on the [repository page](https://github.com/exbuf/peekdocs) lets you search the entire codebase. Try searching for the term `urllib` — you'll see it only in dependency-tree metadata, never in peekdocs's own code.

### 5. Run it in a sandbox first

If you'd rather not run peekdocs on the same computer where you keep sensitive documents, install it on a different machine first — an old laptop, a freshly created user account, a virtual machine, or a USB-bootable Linux setup. Search a folder of throwaway files. Convince yourself the program behaves the way this page describes. Then install it where you actually want to use it.

---

## What peekdocs cannot guarantee

In the spirit of honest disclosure, here is what this page is *not* claiming:

- **peekdocs is not code-signed.** macOS Gatekeeper and Windows SmartScreen will warn you on every download, including upgrades. This is real friction, not a sign of compromise.
- **peekdocs is not third-party audited.** No outside security firm has reviewed the code. The source is public, but no formal audit has been commissioned or published.
- **peekdocs is provided "as is" under the MIT License**, without warranty of any kind, express or implied. See the [LICENSE](../LICENSE) file. This is standard for open-source software.
- **peekdocs is solo-maintained.** Bug-fix turnaround depends on the maintainer's availability. There is no commercial support tier and no SLA.

These are real limitations, not implied promises. If your situation requires a vendor with a code-signing certificate, a published audit report, and a support contract, peekdocs is not that vendor and isn't trying to be. If your situation calls for a local, transparent, no-network search tool whose code you can read, peekdocs is that tool.

---

## If you're still unsure

That's fine. A few options:

- Read the [README](../README.md) and the [User Guide](USER_GUIDE.md) end-to-end. The depth and tone of the documentation are themselves signals about how seriously the project is maintained.
- Skim the [Features](../README.md#features) list and the [What peekdocs Is Not](../README.md#what-peekdocs-is-not) section — both name limits and caveats explicitly. Software that openly states what it cannot do tends to be more honest about what it can.
- Ask someone you trust who reads code to spend 15 minutes looking at the repository.
- Wait. Open-source projects accumulate reputation slowly. If peekdocs is still being actively maintained and used a year from now, that itself is information.

Either way: a thoughtful "no, not yet" is a perfectly good answer. The author would rather you take your time than feel pressured into installing something you're uncertain about.
