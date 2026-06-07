# Release smoke test

A short, runnable checklist for verifying peekdocs behaves correctly on Windows, Linux, and macOS before tagging a release. Designed to catch the things the automated test suite doesn't catch — without becoming a chore.

## What CI already covers

`.github/workflows/test.yml` runs the full pytest suite (~630 tests) on **Windows + macOS + Linux × Python 3.10 / 3.11 / 3.12 / 3.13 / 3.14** with `fail-fast: false`. Every internal Python code path is exercised cross-platform on every push and pull request. `build-release.yml` additionally builds the PyInstaller standalones on all three OSes on every release tag.

That coverage is the heavy lifting. **You can trust that the search engine, indexer, reporter, scanner, expression parser, and API behave identically across the matrix.**

## What this smoke test catches

What CI does *not* exercise is the **shell ↔ binary boundary on Windows**, because the test suite invokes the CLI in-process via `from peekdocs.cli import main(...)` rather than through `subprocess.run([...])`. That bypasses:

- PowerShell vs cmd.exe argument parsing
- Shell wildcard handling (cmd.exe passes literal `*`; Unix shells expand it)
- Backslash quoting across shell → argparse → regex
- `cp1252` console output vs UTF-8 in filenames and match text
- The PyInstaller `peekdocs-cli-windows.exe` itself (vs. the `pip install -e .` console-script wrapper that tests use)
- The `--on-match` hook on Windows (four hook tests are skipped on `win32` by `_posix_only`)
- The case sensitivity of `-t pdf` vs `-t PDF`
- Long paths (>260 characters without long-path support)

Linux behaves enough like macOS that a short parity check covers it. macOS is included for completeness.

---

## Setup

Pick a throwaway folder. Drop a few fixture files in it. Use the same folder for every command below.

```
cd $TEMP   (Windows: %TEMP%)
mkdir peekdocs_smoke && cd peekdocs_smoke
echo budget > a.txt
echo budgets > b.txt
echo budgeting > c.txt
echo REF-12345 > order.txt
peekdocs --version
peekdocs --check
```

**Expected:** version string and a clean dependency report. **Watch for:** exit code 0, no Unicode mojibake in `--check` output, Tesseract status accurate to what's actually installed.

---

## Windows checks

Run each check in **both cmd.exe and PowerShell**. The two shells parse arguments differently enough that "works in cmd" is not evidence for "works in PowerShell."

### 1. PowerShell `--%` token

```powershell
.\peekdocs --version                 # may or may not work
.\peekdocs --% --version             # known-good escape
.\peekdocs --% -t pdf budget .
```

PowerShell can intercept `--flag` arguments as parameters of its own. The `--%` stop-parsing token tells PowerShell to pass everything that follows verbatim. Confirm `.\peekdocs --% ...` always works, regardless of whether the bare form does. Documented in [INSTALLATION.md → CLI on Windows footnotes](INSTALLATION.md#cli-on-windows-footnotes).

### 2. Shell wildcard handling

```
peekdocs -w "budg*" .
```

cmd.exe and PowerShell both pass `budg*` literally to peekdocs (unlike Unix shells, which expand `*` before the program sees it). peekdocs's own wildcard engine handles it. Expect three matches on the fixture files. If you get a "no such file" error, the shell is expanding the pattern — confirm by trying the same command with single-quoted forward slashes.

### 3. Backslash in regex

```
peekdocs -x "\bREF-\d{4,}\b" .
```

PowerShell variant: `.\peekdocs --% -x "\bREF-\d{4,}\b" .`

**Watch for:** the backslashes must survive shell parsing intact. If `\b` becomes literal `b`, the regex changes meaning silently (matches `bREF-12345b` instead of "REF-12345 as a whole word"). Expect a single match in `order.txt`.

### 4. Unicode filename

```
copy nul "北京报告.txt"
echo budget > "北京报告.txt"
peekdocs budget .
```

**Watch for two distinct things:**

- The filename rendering in the terminal output. cp1252 console may show `?` for CJK characters — the binary is still finding the file, it's just the console that can't display the name.
- The filename inside the `peekdocs_standard_results.txt` and `peekdocs_standard_results.docx` reports. Reports are UTF-8 and should always display the CJK filename correctly. If the report file itself shows `?`, that's a real bug.

### 5. Path separators in arguments

```
peekdocs budget C:\Users\%USERNAME%\Documents
peekdocs budget "C:\Users\With Space\Documents"
```

PowerShell variant of the second form uses `"$HOME\With Space\Documents"`. Watch for backslashes in paths conflicting with regex escapes when both appear in the same command.

### 6. `-t` extension case sensitivity

```
echo budget > test.pdf
peekdocs -t pdf budget .
peekdocs -t PDF budget .
peekdocs -t .pdf budget .
```

**Watch for:** all three should produce the same result (all find or all skip the file). Inconsistency would be a real bug not currently covered by the test suite.

### 7. Long path

Create a folder hierarchy whose total path length exceeds 260 characters:

```powershell
$d = "a" * 240
mkdir $d
cd $d
echo budget > deep.txt
cd ..
peekdocs budget .
```

Windows truncates paths at 260 characters by default. Long-path support can be enabled via Group Policy or a registry key but is off by default on most installs. **Watch for:** does peekdocs surface this as a clean "skipped — path too long" message in the error log, or does it crash / silently miss the file?

### 8. `--on-match` hook on Windows

```
echo budget > hit.txt
peekdocs budget . --on-match "echo HIT > hook_fired.txt"
type hook_fired.txt
```

The CI test suite skips four `--on-match` tests on Windows via the `_posix_only` marker (`tests/test_cli.py:11–20`), so this path is genuinely untested in CI. Confirm:

- `hook_fired.txt` is created and contains `HIT`
- Exit code is 0
- Hook command doesn't time out at 30 seconds (documented limit in CLI help)

### 9. PyInstaller exe startup tax

```powershell
Measure-Command { .\peekdocs-cli-windows.exe --version }
```

**Expected:** 2–4 seconds total time (the PyInstaller unpack cost on Windows). If consistently >5s, something's compounding the overhead.

### 10. Both binaries side-by-side

```
peekdocs-cli-windows.exe --version
peekdocs-gui-windows.exe
```

The GUI binary should launch a window; the CLI binary should print a version. Confirm neither tries to load the other's dependencies (a sign of build pollution).

---

## Linux checks

Linux behaves like macOS for most CLI surface — Bash/Zsh handle arguments and wildcards the same way macOS does. The main differences are no Gatekeeper, a lighter PyInstaller startup tax (0.5–1.5 s), and tighter case sensitivity on common filesystems.

```bash
./peekdocs-cli-linux --version
./peekdocs-cli-linux --check
./peekdocs-cli-linux -x '\bREF-\d{4,}\b' ~/Documents
touch ~/Documents/'北京报告.txt'
echo budget > ~/Documents/'北京报告.txt'
./peekdocs-cli-linux budget ~/Documents
time ./peekdocs-cli-linux --version    # expect 0.5–1.5 s
```

**Watch for:** Unicode filename renders in the terminal (Linux terminals are typically UTF-8 by default), startup time falls in the expected range, regex pattern produces the same match count as it does on macOS.

---

## macOS parity check

If most testing has happened on macOS, this is the simplest leg. Run from the standalone `.app`/binary location to confirm Gatekeeper has been bypassed:

```bash
./peekdocs --version
./peekdocs --check
./peekdocs -x '\bREF-\d{4,}\b' ~/Documents
time ./peekdocs --version    # expect 5–7 s without xattr fix; 0.2–0.5 s after
```

**Watch for:** the `xattr -dr com.apple.quarantine` step on the binary has actually been applied (documented in INSTALLATION.md). Without it, every invocation re-pays the Gatekeeper check — the slowness compounds.

---

## Sample corpus check

The bundled `samples/engineering_test/` corpus is the same one used in the README and User Guide first-experience demos. It should produce identical results on all three platforms:

```
cd samples/engineering_test
peekdocs BUILD -r
```

**Expected:** `Found 29 match(es) in 5 file(s). Files searched: 38` and matching files in sh / tcl / vhd / vhdl / makefile. If the file count differs, the corpus has drifted and the README / User Guide / CHANGELOG counts need updating.

---

## Results checklist

For each platform, record:

- [ ] Sanity (`--version`, `--check`) passes with exit 0
- [ ] Sample-corpus BUILD demo produces 29 matches in 5 files
- [ ] Regex with backslash survives shell quoting
- [ ] Unicode filename renders correctly in the report file
- [ ] PyInstaller startup time falls in the expected per-platform range
- [ ] Windows only: `--on-match` hook fires and creates the output file
- [ ] Windows only: `-t pdf` and `-t PDF` produce consistent results

A clean pass on all three platforms is the green light for `git tag` and `gh release create`.

---

## When to update this document

Add a check whenever:

- A new shell or argument-parsing surface lands (e.g. a new flag with non-trivial quoting)
- A test gets a `skipif sys.platform == "win32"` or equivalent skip
- A platform-specific bug ships to a release and a regression test for it would be welcome

Remove a check whenever the underlying CI gains coverage that makes the manual check redundant (e.g. if a future CI job runs `subprocess.run` against the built PyInstaller binary, items 9–10 here become CI's job).
