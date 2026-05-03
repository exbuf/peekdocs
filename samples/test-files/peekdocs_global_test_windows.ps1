# ============================================================================
# peekdocs_global_test_windows.ps1 — Automated test of every peekdocs search mode
# Version: 1.3 - 2026-05-01
# ============================================================================
#
# Purpose: Developer/QA integration test for peekdocs. Exercises every search
# mode and flag combination to verify the application runs without errors across
# all supported features. This script is for app debugging and regression testing
# -- not intended for end-user consumption.
#
# Runs peekdocs with every search flag and combination against the files
# in the current folder (recursively), capturing all output to
# peekdocs_global_test_results.txt in the current folder.
#
# Works on Windows only. For macOS and Linux, use peekdocs_global_test_unix.sh.
#
# Usage:
#     cd C:\path\to\your\documents
#     powershell -ExecutionPolicy Bypass -File C:\path\to\peekdocs_global_test_windows.ps1 "your search terms"
#     powershell -ExecutionPolicy Bypass -File C:\path\to\peekdocs_global_test_windows.ps1 "term1" "term2"
#
# The script can live anywhere — it searches wherever you cd to.
#
# Safe with peekdocs --clear and --clear-all: these scripts and their output
# file (peekdocs_global_test_results.txt) start with "peekdocs_global", which
# does not match any of the delete patterns (peekdocs_results*, peekdocs_report_*,
# peekdocs_accumulated_*, peekdocs_errors.log, .peekdocs.db).
#
# Notes for cross-platform use:
#   - Copy the entire test-files folder (with all 105 sample files) to each
#     machine. If transferring via email, FTP, or git, zip the folder first --
#     these tools can silently modify file contents or strip certain extensions.
#     Direct copy (USB drive, scp, network share) is fine without zipping.
#   - sample.doc was created with macOS textutil -- verify it reads on Windows.
#   - sample.pst will always show [F] unless libpff-python is installed. Expected.
#   - sample.rar has only a RAR header, no extractable content. It won't match
#     search terms. Create a real .rar with WinRAR on Windows if needed.
#   - If "scripts are disabled" error: run this first:
#     Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#
# Known behavior:
#   - The results file (peekdocs_global_test_results.txt) is hidden during each
#     test so peekdocs does not search its own growing output. This prevents
#     inflated match counts from self-matching.
#
# Not tested (by design):
#   - -sa (append/accumulate) -- requires multiple sequential runs to validate
#   - --open -- launches a GUI application, can't automate
#   - --config -- would modify ~/.peekdocsrc and affect the user's real settings
# ============================================================================

param(
    [Parameter(Position=0, ValueFromRemainingArguments=$true)]
    [string[]]$SearchTerms
)

if (-not $SearchTerms -or $SearchTerms.Count -eq 0) {
    Write-Host "Usage: powershell -File $($MyInvocation.MyCommand.Name) TERM [TERM ...]"
    Write-Host ""
    Write-Host "  Runs every peekdocs search mode against the current folder (recursively)"
    Write-Host "  and saves results to peekdocs_global_test_results.txt"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  powershell -File $($MyInvocation.MyCommand.Name) `"test file for peekdocs`""
    Write-Host "  powershell -File $($MyInvocation.MyCommand.Name) budget revenue"
    Write-Host "  powershell -File $($MyInvocation.MyCommand.Name) hello"
    exit 1
}

# Build search terms
$TERMS = $SearchTerms -join " "
$TERM1 = $SearchTerms[0]
$TERM2 = if ($SearchTerms.Count -ge 2) { $SearchTerms[1] } else { $TERM1 }

$SCRIPT_VERSION = "1.3"
$SCRIPT_DATE = "2026-05-03"
$OUTFILE = "peekdocs_global_test_results.txt"
$script:PASS = 0
$script:FAIL = 0
$script:SKIP = 0
$DIVIDER = "=" * 78
$SUBDIV = "-" * 78

# Count files recursively (excludes peekdocs output files, index files, and this
# script itself — so this count may be lower than a full directory listing)
$FILE_COUNT = (Get-ChildItem -Recurse -File |
    Where-Object { $_.Name -notlike "peekdocs_*" -and $_.Name -notlike ".peekdocs*" -and $_.Name -ne "peekdocs_global_test_windows.ps1" } |
    Measure-Object).Count

# Clean up any leftover peekdocs output before we start
& peekdocs --clear 2>$null | Out-Null

# Start the results file
$header = @"
$DIVIDER
  peekdocs Search Mode Test Results
  Script:       peekdocs_global_test_windows.ps1 v${SCRIPT_VERSION} (${SCRIPT_DATE})
  Generated:    $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
  Folder:       $(Get-Location)
  Files found:  $FILE_COUNT (recursive, excludes peekdocs output/index/script files)
  Search terms: $TERMS
$DIVIDER

Key:
  [PASS]       -- test ran successfully
  [FAIL]       -- test crashed or produced unexpected output
  [SKIP]       -- test skipped (missing dependency)
  [P] file (N) -- peekdocs found N matching lines in this file
  [F] file     -- peekdocs could not read this file (corrupt, locked, or missing library)
  [OK] file    -- output file was created successfully
  [MISSING]    -- expected output file was not created

  [P] and [F] are informational, not pass/fail. A [P] file could return wrong
  matches; an [F] file might be expected (e.g. .pst without libpff). Compare
  across runs to spot regressions.

"@
Set-Content -Path $OUTFILE -Value $header -Encoding UTF8

# ── Helper: write to both console and file ────────────────────────────────
function Write-Both {
    param([string]$Text)
    Write-Host $Text
    Add-Content -Path $OUTFILE -Value $Text -Encoding UTF8
}

# ── verify_file ───────────────────────────────────────────────────────────
# Check that an output file was created and is non-empty.
# ──────────────────────────────────────────────────────────────────────────
function Verify-File {
    param(
        [string]$FilePath,
        [string]$Label
    )
    if (Test-Path $FilePath) {
        $size = (Get-Item $FilePath).Length
        if ($size -gt 0) {
            Write-Both "         [OK] $Label created ($size bytes)"
        } else {
            Write-Both "         [MISSING] $Label is empty (0 bytes)"
            $script:FAIL++
            $script:PASS--
        }
    } else {
        Write-Both "         [MISSING] $Label was NOT created"
        $script:FAIL++
        $script:PASS--
    }
}

# ── run_test ──────────────────────────────────────────────────────────────
# Runs one peekdocs command and logs the outcome.
#   $Label = test label
#   $PeekArgs = the peekdocs arguments as a string
#
# Per-file indicators (these are not pass/fail judgements):
#   [P] filename (N) — peekdocs found N matching lines in this file
#   [F] filename     — peekdocs recognized the file type but could not read it
#                       (e.g. corrupt file, missing optional library, binary format)
# A [P] file could still be returning wrong matches; an [F] file might be
# expected (e.g. .pst without libpff). Review the lists to spot regressions.
# ──────────────────────────────────────────────────────────────────────────
function Run-Test {
    param(
        [string]$Label,
        [string]$PeekArgs
    )

    $cmd = "peekdocs $PeekArgs"

    $testHeader = @"
$SUBDIV
TEST: $Label
CMD:  $cmd
$SUBDIV
"@
    Add-Content -Path $OUTFILE -Value $testHeader -Encoding UTF8

    # Hide the results file so peekdocs doesn't search its own growing output
    if (Test-Path $OUTFILE) { Rename-Item $OUTFILE ".$OUTFILE.tmp" }

    # Run peekdocs and capture output (ignore exit code)
    try {
        $output = Invoke-Expression "$cmd 2>&1" | Out-String
    } catch {
        $output = $_.Exception.Message
    }

    # Restore the results file
    if (Test-Path ".$OUTFILE.tmp") { Rename-Item ".$OUTFILE.tmp" $OUTFILE }

    # Strip ANSI color codes for reliable parsing
    $clean = $output -replace '\x1b\[[0-9;]*m', ''
    Add-Content -Path $OUTFILE -Value $clean -Encoding UTF8

    # Extract the "Found" line
    $foundLine = ($clean -split "`n" | Where-Object { $_ -match "^Found [0-9]" }) | Select-Object -First 1

    # Judge pass/fail by output content
    if ($foundLine) {
        Write-Both "[PASS] $Label"
        $script:PASS++
    } elseif ($clean -match "Traceback|usage: peekdocs") {
        Write-Both "[FAIL] $Label"
        $script:FAIL++
    } else {
        # Utility commands (--check, --list-files, --index, etc.) don't print "Found"
        Write-Both "[PASS] $Label"
        $script:PASS++
    }

    # Print per-file results if this was a search
    if ($foundLine) {
        Write-Both "       $($foundLine.Trim())"
        # Matched files: "  sample.go: 3"
        $clean -split "`n" | Where-Object { $_ -match '^\s+\S+\.\S+: [0-9]+' } | ForEach-Object {
            $line = $_.Trim()
            if ($line -match '^(.+): (\d+)$') {
                $fname = $Matches[1]
                $count = $Matches[2]
                Write-Both "         [P] $fname ($count)"
            }
        }
        # Failed files: "  Warning: Could not read sample.pst (...)"
        $clean -split "`n" | Where-Object { $_ -match "Warning: Could not read" } | ForEach-Object {
            if ($_ -match 'Could not read (\S+)') {
                $fname = $Matches[1]
                Write-Both "         [F] $fname  (could not read)"
            }
        }
    }

    Add-Content -Path $OUTFILE -Value "" -Encoding UTF8

    # Clean up reports between tests
    Remove-Item -Path "peekdocs_results.txt" -ErrorAction SilentlyContinue
    Remove-Item -Path "peekdocs_results.docx" -ErrorAction SilentlyContinue
}

# ── run_skip ──────────────────────────────────────────────────────────────
function Run-Skip {
    param(
        [string]$Label,
        [string]$Reason
    )
    Write-Both "[SKIP] $Label  ($Reason)"
    $script:SKIP++
}


# ============================================================================
#  BASELINE SEARCH — establishes reference match count and file type coverage
# ============================================================================

# Hide the results file so it doesn't get searched (it contains the search terms)
if (Test-Path $OUTFILE) { Rename-Item $OUTFILE ".$OUTFILE.tmp" }
try {
    $BASELINE_OUTPUT = Invoke-Expression "peekdocs -r `"$TERM1`" 2>&1" | Out-String
} catch {
    $BASELINE_OUTPUT = ""
}
if (Test-Path ".$OUTFILE.tmp") { Rename-Item ".$OUTFILE.tmp" $OUTFILE }

$BASELINE_CLEAN = $BASELINE_OUTPUT -replace '\x1b\[[0-9;]*m', ''
$BASELINE_FOUND = ($BASELINE_CLEAN -split "`n" | Where-Object { $_ -match "^Found [0-9]" }) | Select-Object -First 1
if ($BASELINE_FOUND -match "Found (\d+) match") {
    $BASELINE_COUNT = $Matches[1]
} else {
    $BASELINE_COUNT = "0"
}
$BASELINE_FILES = @($BASELINE_CLEAN -split "`n" |
    Where-Object { $_ -match '^\s+\S+\.\S+: [0-9]+' } |
    ForEach-Object { ($_.Trim() -replace ': \d+$', '') } |
    Sort-Object)
$BASELINE_WARNED = @($BASELINE_CLEAN -split "`n" |
    Where-Object { $_ -match "Warning: Could not read" } |
    ForEach-Object { if ($_ -match 'Could not read (\S+)') { $Matches[1] } } |
    Sort-Object)

Remove-Item -Path "peekdocs_results.txt" -ErrorAction SilentlyContinue
Remove-Item -Path "peekdocs_results.docx" -ErrorAction SilentlyContinue

# Write baseline section to results file
$baselineHeader = @"
$SUBDIV
BASELINE SEARCH (reference for all subsequent tests)
CMD:  peekdocs -r "$TERM1"
$SUBDIV
$BASELINE_FOUND

Matched files (baseline):
"@
Add-Content -Path $OUTFILE -Value $baselineHeader -Encoding UTF8
foreach ($f in $BASELINE_FILES) {
    if ($f) { Add-Content -Path $OUTFILE -Value "  [P] $f" -Encoding UTF8 }
}

if ($BASELINE_WARNED.Count -gt 0) {
    Add-Content -Path $OUTFILE -Value "" -Encoding UTF8
    Add-Content -Path $OUTFILE -Value "Warned files (could not read):" -Encoding UTF8
    foreach ($f in $BASELINE_WARNED) {
        if ($f) { Add-Content -Path $OUTFILE -Value "  [F] $f" -Encoding UTF8 }
    }
}

# File type coverage check
Add-Content -Path $OUTFILE -Value "" -Encoding UTF8
Add-Content -Path $OUTFILE -Value "-- File Type Coverage ----------------------------------------------------------" -Encoding UTF8

$ALL_TEST_FILES = @(Get-ChildItem -Recurse -File |
    Where-Object { $_.Name -like "sample.*" -or $_.Name -eq "Dockerfile" -or $_.Name -eq "Makefile" } |
    ForEach-Object { $_.Name } |
    Sort-Object)

$SAMPLE_TOTAL = ($ALL_TEST_FILES | Where-Object { $_ -like "sample.*" }).Count
$SAMPLE_MATCHED = ($BASELINE_FILES | Where-Object { $_ -like "sample.*" }).Count

Add-Content -Path $OUTFILE -Value "  Matched: $SAMPLE_MATCHED of $SAMPLE_TOTAL sample.* test files" -Encoding UTF8

$MISSING = @()
foreach ($testfile in $ALL_TEST_FILES) {
    if ($testfile -and $BASELINE_FILES -notcontains $testfile) {
        $MISSING += $testfile
    }
}

if ($MISSING.Count -gt 0) {
    Add-Content -Path $OUTFILE -Value "  Not matched (may not contain your search term, or could not be read):" -Encoding UTF8
    foreach ($f in $MISSING) {
        if ($BASELINE_WARNED -contains $f) {
            Add-Content -Path $OUTFILE -Value "    [F] $f  (could not read)" -Encoding UTF8
        } else {
            Add-Content -Path $OUTFILE -Value "    [ ] $f  (no match -- verify content contains `"$TERM1`")" -Encoding UTF8
        }
    }
} else {
    Add-Content -Path $OUTFILE -Value "  All test files matched." -Encoding UTF8
}

Add-Content -Path $OUTFILE -Value "" -Encoding UTF8
Write-Both "[INFO] Baseline: $BASELINE_FOUND"
Write-Both ""


# ============================================================================
#  1. BASIC SEARCH MODES
# ============================================================================

Write-Both ""
Write-Both "=== BASIC SEARCH MODES ==="

Run-Test 'Default OR search (single term)' `
    "-q -r `"$TERM1`""

if ($SearchTerms.Count -ge 2) {
    Run-Test 'Default OR search (multi-term)' `
        "-q -r $TERMS"
} else {
    Run-Test 'Default OR search (multi-term)' `
        "-q -r `"$TERM1`""
}

Run-Test 'AND search (-a)' `
    "-q -r -a $TERM1 $TERM2"

Run-Test 'Boolean expression (-e)' `
    "-q -r -e `"($TERM1 AND $TERM2) OR $TERM1`""

Run-Test 'Boolean expression with NOT (-e)' `
    "-q -r -e `"$TERM1 AND NOT xyznonexistent`""

Run-Test 'Regex search (-x)' `
    "-q -r -x `"$TERM1`""

Run-Test 'Regex search - digit pattern (-x)' `
    "-q -r -x `"\d{3}-\d{4}`""

Run-Test 'Wildcard search (-w)' `
    "-q -r -w `"${TERM1}*`""

Run-Test 'Fuzzy search (-z)' `
    "-q -r -z `"$TERM1`""

Run-Test 'Whole-word search (-W)' `
    "-q -r -W `"$TERM1`""

Run-Test 'Exact phrase search (quoted)' `
    "-q -r `"$TERMS`""


# ============================================================================
#  2. PROXIMITY SEARCHES
# ============================================================================

Write-Both ""
Write-Both "=== PROXIMITY SEARCHES ==="

Run-Test 'Word proximity - 5 words (-p)' `
    "-q -r -p 5 $TERM1 $TERM2"

Run-Test 'Word proximity - 2 words (-p)' `
    "-q -r -p 2 $TERM1 $TERM2"

Run-Test 'Line proximity - 3 lines (-P)' `
    "-q -r -P 3 $TERM1 $TERM2"


# ============================================================================
#  3. FILTER FLAGS
# ============================================================================

Write-Both ""
Write-Both "=== FILTER FLAGS ==="

Run-Test 'File type filter - Python only (-t py)' `
    "-q -r -t py `"$TERM1`""

Run-Test 'File type filter - multiple types (-t py,js,go)' `
    "-q -r -t py,js,go `"$TERM1`""

Run-Test 'File type filter - documents (-t pdf,docx,txt)' `
    "-q -r -t pdf,docx,txt `"$TERM1`""

Run-Test 'Recursive search (-r)' `
    "-q -r `"$TERM1`""

Run-Test 'Exclude terms (-n)' `
    "-q -r -n xyznonexistent `"$TERM1`""

Run-Test 'Inverse search (--inverse)' `
    "-q -r --inverse xyznonexistent"


# ============================================================================
#  4. RANGE FILTERS
# ============================================================================

Write-Both ""
Write-Both "=== RANGE FILTERS ==="

Run-Test 'Amount range (-R amount:)' `
    "-q -r -R amount:0..999999 `"$TERM1`""

Run-Test 'Number range (-R number:)' `
    "-q -r -R number:0..999999 `"$TERM1`""

Run-Test 'File size range (-R filesize:)' `
    "-q -r -R filesize:0kb..100mb `"$TERM1`""

Run-Test 'Multiple ranges (-R -R)' `
    "-q -r -R number:0..999999 -R filesize:0kb..100mb `"$TERM1`""


# ============================================================================
#  5. CONTEXT LINES
# ============================================================================

Write-Both ""
Write-Both "=== CONTEXT LINES ==="

Run-Test 'Context before (-B 3)' `
    "-q -r -B 3 `"$TERM1`""

Run-Test 'Context after (-A 3)' `
    "-q -r -A 3 `"$TERM1`""

Run-Test 'Context both (-B 2 -A 2)' `
    "-q -r -B 2 -A 2 `"$TERM1`""


# ============================================================================
#  6. OUTPUT OPTIONS
# ============================================================================

Write-Both ""
Write-Both "=== OUTPUT OPTIONS ==="

# -s is a post-search command (copies existing results), so run a search first
& peekdocs -q -r "$TERM1" 2>$null | Out-Null
Run-Test 'Save named report (-s)' `
    "-s test_report"
Verify-File "peekdocs_report_test_report.txt" "peekdocs_report_test_report.txt"
Verify-File "peekdocs_report_test_report.docx" "peekdocs_report_test_report.docx"
Remove-Item -Path "peekdocs_report_test_report.txt" -ErrorAction SilentlyContinue
Remove-Item -Path "peekdocs_report_test_report.docx" -ErrorAction SilentlyContinue

Run-Test 'CSV output (-o csv)' `
    "-q -r -o csv `"$TERM1`""
Verify-File "peekdocs_results.csv" "peekdocs_results.csv"
Remove-Item -Path "peekdocs_results.csv" -ErrorAction SilentlyContinue

Run-Test 'JSON output (-o json)' `
    "-q -r -o json `"$TERM1`""
Verify-File "peekdocs_results.json" "peekdocs_results.json"
Remove-Item -Path "peekdocs_results.json" -ErrorAction SilentlyContinue

Run-Test 'HTML output (-o html)' `
    "-q -r -o html `"$TERM1`""
Verify-File "peekdocs_results.html" "peekdocs_results.html"
Remove-Item -Path "peekdocs_results.html" -ErrorAction SilentlyContinue

Run-Test 'Multiple output formats (-o csv,json,html)' `
    "-q -r -o csv,json,html `"$TERM1`""
Verify-File "peekdocs_results.csv" "peekdocs_results.csv"
Verify-File "peekdocs_results.json" "peekdocs_results.json"
Verify-File "peekdocs_results.html" "peekdocs_results.html"
Remove-Item -Path "peekdocs_results.csv" -ErrorAction SilentlyContinue
Remove-Item -Path "peekdocs_results.json" -ErrorAction SilentlyContinue
Remove-Item -Path "peekdocs_results.html" -ErrorAction SilentlyContinue

Run-Test 'Max matches (-m 5)' `
    "-q -r -m 5 `"$TERM1`""

Run-Test 'Quiet mode (-q)' `
    "-q -r `"$TERM1`""

Run-Test 'Extra quiet mode (-qq)' `
    "-qq -r `"$TERM1`""

Run-Test 'Timestamp flag (--timestamp)' `
    "-q -r --timestamp `"$TERM1`""
# Check that timestamped files were created
$tsTxt = Get-ChildItem "peekdocs_results_*.txt" -ErrorAction SilentlyContinue | Select-Object -First 1
$tsDocx = Get-ChildItem "peekdocs_results_*.docx" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($tsTxt) {
    Verify-File $tsTxt.Name "timestamped .txt report"
} else {
    Write-Both "         [MISSING] No timestamped .txt report found"
    $script:FAIL++; $script:PASS--
}
if ($tsDocx) {
    Verify-File $tsDocx.Name "timestamped .docx report"
} else {
    Write-Both "         [MISSING] No timestamped .docx report found"
    $script:FAIL++; $script:PASS--
}
Remove-Item -Path "peekdocs_results_*.txt" -ErrorAction SilentlyContinue
Remove-Item -Path "peekdocs_results_*.docx" -ErrorAction SilentlyContinue


# ============================================================================
#  7. COMBINED MODES
# ============================================================================

Write-Both ""
Write-Both "=== COMBINED MODES ==="

Run-Test 'AND + file type (-a -t)' `
    "-q -r -a -t py,js $TERM1 $TERM2"

Run-Test 'Regex + file type (-x -t)' `
    "-q -r -x `"$TERM1`" -t py"

Run-Test 'Wildcard + exclude (-w -n)' `
    "-q -r -w `"${TERM1}*`" -n xyznonexistent"

Run-Test 'Fuzzy + recursive (-z -r)' `
    "-q -r -z `"$TERM1`""

Run-Test 'Whole-word + AND (-W -a)' `
    "-q -r -W -a $TERM1 $TERM2"

Run-Test 'AND + context (-a -B -A)' `
    "-q -r -a -B 2 -A 2 $TERM1 $TERM2"

Run-Test 'File type + range (-t -R)' `
    "-q -r -t csv,tsv -R number:0..999999 `"$TERM1`""

Run-Test 'Inverse + file type (--inverse -t)' `
    "-q -r --inverse -t py xyznonexistent"

Run-Test 'Expression + file type (-e -t)' `
    "-q -r -e `"$TERM1 AND $TERM2`" -t py,js,go"

Run-Test 'Proximity + file type (-p -t)' `
    "-q -r -p 5 -t py,js $TERM1 $TERM2"


# ============================================================================
#  8. SPECIAL FEATURES
# ============================================================================

Write-Both ""
Write-Both "=== SPECIAL FEATURES ==="

Run-Test 'PII scan (--pii-scan)' `
    "-q -r --pii-scan"

Run-Test 'System check (--check)' `
    "--check"

Run-Test 'List files (--list-files)' `
    "--list-files"

# OCR — only if Tesseract is installed
if (Get-Command tesseract -ErrorAction SilentlyContinue) {
    Run-Test 'OCR search (-O)' `
        "-q -r -O `"$TERM1`""
} else {
    Run-Skip "OCR search (-O)" "Tesseract not installed"
}

# Index — build, search, then clear
Run-Test 'Build index (--index)' `
    "--index"

Run-Test 'Index status (--index-status)' `
    "--index-status"

Run-Test 'Search with index' `
    "-q `"$TERM1`""

Run-Test 'Search bypassing index (--no-index)' `
    "-q --no-index `"$TERM1`""

Run-Test 'Clear index (--index-clear)' `
    "--index-clear"


# ============================================================================
#  9. MATCH COUNT CONSISTENCY CHECK
# ============================================================================

Write-Both ""
Write-Both "=== MATCH COUNT CONSISTENCY ==="

# Re-run the same baseline search and verify the count hasn't changed.
# Temporarily hide the results file so it doesn't inflate the match count.
if (Test-Path $OUTFILE) { Rename-Item $OUTFILE ".$OUTFILE.tmp" }
try {
    $RECHECK_OUTPUT = Invoke-Expression "peekdocs -q -r `"$TERM1`" 2>&1" | Out-String
} catch {
    $RECHECK_OUTPUT = ""
}
if (Test-Path ".$OUTFILE.tmp") { Rename-Item ".$OUTFILE.tmp" $OUTFILE }

$RECHECK_CLEAN = $RECHECK_OUTPUT -replace '\x1b\[[0-9;]*m', ''
$RECHECK_FOUND = ($RECHECK_CLEAN -split "`n" | Where-Object { $_ -match "^Found [0-9]" }) | Select-Object -First 1
if ($RECHECK_FOUND -match "Found (\d+) match") {
    $RECHECK_COUNT = $Matches[1]
} else {
    $RECHECK_COUNT = "0"
}
Remove-Item -Path "peekdocs_results.txt" -ErrorAction SilentlyContinue
Remove-Item -Path "peekdocs_results.docx" -ErrorAction SilentlyContinue

if ($RECHECK_COUNT -eq $BASELINE_COUNT) {
    Write-Both "[PASS] Match count stable: $RECHECK_COUNT matches (same as baseline)"
    $script:PASS++
} else {
    Write-Both "[FAIL] Match count CHANGED: baseline=$BASELINE_COUNT, recheck=$RECHECK_COUNT"
    $script:FAIL++
}


# ============================================================================
#  SUMMARY
# ============================================================================

$summary = @"

$DIVIDER
  SUMMARY
$DIVIDER
  Passed:  $($script:PASS)
  Failed:  $($script:FAIL)
  Skipped: $($script:SKIP)
  Total:   $($script:PASS + $script:FAIL + $script:SKIP)

  Search terms: $TERMS
  Folder:       $(Get-Location)
  Files found:  $FILE_COUNT (recursive, excludes peekdocs output/index/script files)
  Baseline:     $BASELINE_COUNT matches in baseline search
  Generated:    $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
$DIVIDER
"@
Write-Host $summary
Add-Content -Path $OUTFILE -Value $summary -Encoding UTF8

# Final cleanup
& peekdocs --clear 2>$null | Out-Null
Remove-Item -Path "peekdocs_errors.log" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Results saved to: $(Join-Path (Get-Location) $OUTFILE)"
