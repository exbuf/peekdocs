#!/bin/bash
# ============================================================================
# peekdocs_global_test_unix.sh — Automated test of every peekdocs search mode
# Version: 1.3 — 2026-05-01
# ============================================================================
#
# Purpose: Developer/QA integration test for peekdocs. Exercises every search
# mode and flag combination to verify the application runs without errors across
# all supported features. This script is for app debugging and regression testing
# — not intended for end-user consumption.
#
# Runs peekdocs with every search flag and combination against the files
# in the current folder (recursively), capturing all output to
# peekdocs_global_test_results.txt in the current folder.
#
# Usage:
#     cd /path/to/your/documents
#     bash /path/to/peekdocs_global_test_unix.sh "your search terms"
#     bash /path/to/peekdocs_global_test_unix.sh "term1" "term2"
#
# The script can live anywhere — it searches wherever you cd to.
# Works on macOS and Linux only. For Windows, use peekdocs_global_test_windows.ps1.
#
# Safe with peekdocs --clear and --clear-all: these scripts and their output
# file (peekdocs_global_test_results.txt) start with "peekdocs_global", which
# does not match any of the delete patterns (peekdocs_standard_results*,
# peekdocs_regex_results*, peekdocs_suite_results*, peekdocs_report_*,
# peekdocs_accumulated_*, peekdocs_errors.log, .peekdocs.db).
#
# Notes for cross-platform use:
#   - Copy the entire test-files folder (with all 105 sample files) to each
#     machine. If transferring via email, FTP, or git, zip the folder first —
#     these tools can silently modify file contents or strip certain extensions.
#     Direct copy (USB drive, scp, network share) is fine without zipping.
#   - sample.doc was created with macOS textutil — verify it reads on Linux/Windows.
#   - sample.pst will always show [F] unless libpff-python is installed. Expected.
#   - sample.rar has only a RAR header, no extractable content. It won't match
#     search terms. Create a real .rar with WinRAR on Windows if needed.
#   - Line endings: if this .sh file is copied through Windows (git clone, email,
#     etc.), it may get \r\n line endings and bash will fail with errors like
#     "/bin/bash^M: bad interpreter". Fix with: sed -i 's/\r$//' peekdocs_global_test_unix.sh
#
# Known behavior:
#   - The results file (peekdocs_global_test_results.txt) is hidden during each
#     test so peekdocs does not search its own growing output. This prevents
#     inflated match counts from self-matching.
#
# Not tested (by design):
#   - -sa (append/accumulate) — requires multiple sequential runs to validate
#   - --open — launches a GUI application, can't automate
#   - --config — would modify ~/.peekdocsrc and affect the user's real settings
# ============================================================================

# ── Require at least one search term ──────────────────────────────────────
if [ $# -eq 0 ]; then
    echo "Usage: bash $0 TERM [TERM ...]"
    echo ""
    echo "  Runs every peekdocs search mode against the current folder (recursively)"
    echo "  and saves results to peekdocs_global_test_results.txt"
    echo ""
    echo "Examples:"
    echo "  bash $0 \"test file for peekdocs\""
    echo "  bash $0 budget revenue"
    echo "  bash $0 hello"
    exit 1
fi

# Build the search terms string (space-separated for multi-term tests)
TERMS="$*"
# First term only (for single-term tests)
TERM1="$1"
# If we have 2+ terms, grab the second for proximity/AND tests
TERM2="${2:-$1}"

SCRIPT_VERSION="1.3"
SCRIPT_DATE="2026-05-03"
OUTFILE="peekdocs_global_test_results.txt"
PASS=0
FAIL=0
SKIP=0
DIVIDER="$(printf '=%.0s' {1..78})"
SUBDIV="$(printf -- '-%.0s' {1..78})"

# Count files recursively (excludes peekdocs output files, index files, and this
# script itself — so this count may be lower than a full directory listing)
FILE_COUNT=$(find . -type f ! -name "peekdocs_*" ! -name ".peekdocs*" ! -name "peekdocs_global_test_unix.sh" | wc -l | tr -d ' ')

# Clean up any leftover peekdocs output before we start
peekdocs --clear 2>/dev/null || true

# Start the results file
{
echo "$DIVIDER"
echo "  peekdocs Search Mode Test Results"
echo "  Script:       peekdocs_global_test_unix.sh v${SCRIPT_VERSION} (${SCRIPT_DATE})"
echo "  Generated:    $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Folder:       $(pwd)"
echo "  Files found:  $FILE_COUNT (recursive, excludes peekdocs output/index/script files)"
echo "  Search terms: $TERMS"
echo "$DIVIDER"
echo ""
echo "Key:"
echo "  [PASS]       — test ran successfully"
echo "  [FAIL]       — test crashed or produced unexpected output"
echo "  [SKIP]       — test skipped (missing dependency)"
echo "  [P] file (N) — peekdocs found N matching lines in this file"
echo "  [F] file     — peekdocs could not read this file (corrupt, locked, or missing library)"
echo "  [OK] file    — output file was created successfully"
echo "  [MISSING]    — expected output file was not created"
echo ""
echo "  [P] and [F] are informational, not pass/fail. A [P] file could return wrong"
echo "  matches; an [F] file might be expected (e.g. .pst without libpff). Compare"
echo "  across runs to spot regressions."
echo ""
} > "$OUTFILE"

# ── run_test ──────────────────────────────────────────────────────────────
# Runs one peekdocs command and logs the outcome.
#   $1  = test label
#   $2+ = the peekdocs command (without "peekdocs" itself)
#
# Per-file indicators (these are not pass/fail judgements):
#   [P] filename (N) — peekdocs found N matching lines in this file
#   [F] filename     — peekdocs recognized the file type but could not read it
#                       (e.g. corrupt file, missing optional library, binary format)
# A [P] file could still be returning wrong matches; an [F] file might be
# expected (e.g. .pst without libpff). Review the lists to spot regressions.
# ──────────────────────────────────────────────────────────────────────────
run_test() {
    local label="$1"
    shift
    local cmd="peekdocs $*"

    {
    echo "$SUBDIV"
    echo "TEST: $label"
    echo "CMD:  $cmd"
    echo "$SUBDIV"
    } >> "$OUTFILE"

    # Hide the results file so peekdocs doesn't search its own growing output
    mv "$OUTFILE" ".${OUTFILE}.tmp" 2>/dev/null || true

    # Capture output regardless of exit code (peekdocs may return non-zero
    # when individual files fail to read, e.g. .pst — that's not a test failure)
    output=$(eval "$cmd" 2>&1) || true

    # Restore the results file
    mv ".${OUTFILE}.tmp" "$OUTFILE" 2>/dev/null || true

    # Strip ANSI color codes for reliable parsing
    clean=$(echo "$output" | sed 's/\x1b\[[0-9;]*m//g')
    echo "$clean" >> "$OUTFILE"

    # Extract per-file results from peekdocs output
    # Matched files appear as "  sample.go: 3" (indented, name: count)
    # Warnings appear as "  Warning: Could not read sample.pst (...)"
    local found_line
    found_line=$(echo "$clean" | grep -E "^Found [0-9]" || true)

    # Judge pass/fail by output content, not exit code
    if [ -n "$found_line" ]; then
        echo "[PASS] $label" | tee -a "$OUTFILE"
        PASS=$((PASS + 1))
    elif echo "$clean" | grep -qiE "Traceback|usage: peekdocs"; then
        echo "[FAIL] $label" | tee -a "$OUTFILE"
        FAIL=$((FAIL + 1))
    else
        # Utility commands (--check, --list-files, --index, etc.) don't print "Found"
        echo "[PASS] $label" | tee -a "$OUTFILE"
        PASS=$((PASS + 1))
    fi

    # Print per-file results if this was a search (not a utility command)
    if [ -n "$found_line" ]; then
        echo "       $found_line" | tee -a "$OUTFILE"
        # Matched files: "  sample.go: 3"
        echo "$clean" | grep -E '^\s+\S+\.\S+: [0-9]+' | while IFS= read -r line; do
            fname=$(echo "$line" | sed 's/^ *//' | sed 's/: [0-9]*//')
            count=$(echo "$line" | grep -oE '[0-9]+$')
            echo "         [P] $fname ($count)" | tee -a "$OUTFILE"
        done
        # Failed files: "  Warning: Could not read sample.pst (...)"
        echo "$clean" | grep -i "Warning: Could not read" | while IFS= read -r line; do
            fname=$(echo "$line" | sed 's/.*Could not read //' | sed 's/ (.*//')
            echo "         [F] $fname  (could not read)" | tee -a "$OUTFILE"
        done
    fi
    echo "" >> "$OUTFILE"

    # Clean up reports between tests so they don't clutter
    rm -f peekdocs_standard_results.txt peekdocs_standard_results.docx 2>/dev/null
}

# ── verify_file ───────────────────────────────────────────────────────────
# Check that an output file was created and is non-empty.
# ──────────────────────────────────────────────────────────────────────────
verify_file() {
    local filepath="$1"
    local label="$2"
    if [ -f "$filepath" ] && [ -s "$filepath" ]; then
        local size
        size=$(wc -c < "$filepath" | tr -d ' ')
        echo "         [OK] $label created ($size bytes)" | tee -a "$OUTFILE"
    else
        echo "         [MISSING] $label was NOT created" | tee -a "$OUTFILE"
        FAIL=$((FAIL + 1))
        PASS=$((PASS - 1))
    fi
}

# ── run_skip ──────────────────────────────────────────────────────────────
# Log a test that can't run in this environment.
# ──────────────────────────────────────────────────────────────────────────
run_skip() {
    local label="$1"
    local reason="$2"
    echo "[SKIP] $label  ($reason)" | tee -a "$OUTFILE"
    SKIP=$((SKIP + 1))
}


# ============================================================================
#  1. BASIC SEARCH MODES
# ============================================================================

echo "" | tee -a "$OUTFILE"
echo "=== BASIC SEARCH MODES ===" | tee -a "$OUTFILE"

# The first search establishes the baseline match count and matched file list.
# We run it without -q so we can capture the file listing, then store the results.
# Hide the results file so it doesn't get searched (it contains the search terms).
mv "$OUTFILE" ".${OUTFILE}.tmp" 2>/dev/null || true
BASELINE_OUTPUT=$(peekdocs -r "$TERM1" 2>&1) || true
mv ".${OUTFILE}.tmp" "$OUTFILE" 2>/dev/null || true
BASELINE_CLEAN=$(echo "$BASELINE_OUTPUT" | sed 's/\x1b\[[0-9;]*m//g')
BASELINE_FOUND=$(echo "$BASELINE_CLEAN" | grep -E "^Found [0-9]" || true)
BASELINE_COUNT=$(echo "$BASELINE_FOUND" | grep -oE "Found [0-9]+ match" | grep -oE "[0-9]+" || echo "0")
BASELINE_FILES=$(echo "$BASELINE_CLEAN" | grep -E '^\s+\S+\.\S+: [0-9]+' | sed 's/^ *//' | sed 's/: [0-9]*//' | sort)
BASELINE_WARNED=$(echo "$BASELINE_CLEAN" | grep -i "Warning: Could not read" | sed 's/.*Could not read //' | sed 's/ (.*//' | sort)
rm -f peekdocs_standard_results.txt peekdocs_standard_results.docx 2>/dev/null

{
echo "$SUBDIV"
echo "BASELINE SEARCH (reference for all subsequent tests)"
echo "CMD:  peekdocs -r \"$TERM1\""
echo "$SUBDIV"
echo "$BASELINE_FOUND"
echo ""
echo "Matched files (baseline):"
echo "$BASELINE_FILES" | while IFS= read -r f; do [ -n "$f" ] && echo "  [P] $f"; done
if [ -n "$BASELINE_WARNED" ]; then
    echo ""
    echo "Warned files (could not read):"
    echo "$BASELINE_WARNED" | while IFS= read -r f; do [ -n "$f" ] && echo "  [F] $f"; done
fi
echo ""

# ── File type coverage check ──────────────────────────────────────────
# Compare matched extensions against all file extensions present in the folder.
echo "── File Type Coverage ──────────────────────────────────────────"
ALL_EXTENSIONS=$(find . -type f -name "sample.*" -o -name "Dockerfile" -o -name "Makefile" | \
    sed 's|.*/||' | sort)
MATCHED_NAMES=$(echo "$BASELINE_FILES")
MISSING=""
while IFS= read -r testfile; do
    [ -z "$testfile" ] && continue
    if ! echo "$MATCHED_NAMES" | grep -qx "$testfile"; then
        MISSING="$MISSING $testfile"
    fi
done <<< "$ALL_EXTENSIONS"

MATCHED_TYPE_COUNT=$(echo "$BASELINE_FILES" | grep -c "^sample\." || echo "0")
TOTAL_TYPE_COUNT=$(echo "$ALL_EXTENSIONS" | grep -c "^sample\." || echo "0")
echo "  Matched: $MATCHED_TYPE_COUNT of $TOTAL_TYPE_COUNT sample.* test files"

if [ -n "$MISSING" ]; then
    echo "  Not matched (may not contain your search term, or could not be read):"
    for f in $MISSING; do
        # Check if it was in the warnings
        if echo "$BASELINE_WARNED" | grep -q "$f"; then
            echo "    [F] $f  (could not read)"
        else
            echo "    [ ] $f  (no match — verify content contains \"$TERM1\")"
        fi
    done
else
    echo "  All test files matched."
fi
echo ""
} >> "$OUTFILE"

echo "[INFO] Baseline: $BASELINE_FOUND" | tee -a "$OUTFILE"
echo ""

run_test "Default OR search (single term)" \
    "-q -r \"$TERM1\""

if [ $# -ge 2 ]; then
    run_test "Default OR search (multi-term)" \
        "-q -r $TERMS"
else
    run_test "Default OR search (multi-term)" \
        "-q -r \"$TERM1\""
fi

run_test "AND search (-a)" \
    "-q -r -a $TERM1 $TERM2"

run_test "Boolean expression (-e)" \
    "-q -r -e \"($TERM1 AND $TERM2) OR $TERM1\""

run_test "Boolean expression with NOT (-e)" \
    "-q -r -e \"$TERM1 AND NOT xyznonexistent\""

run_test "Regex search (-x)" \
    "-q -r -x \"$TERM1\""

run_test "Regex search — digit pattern (-x)" \
    '-q -r -x "\d{3}-\d{4}"'

run_test "Wildcard search (-w)" \
    "-q -r -w \"${TERM1}*\""

run_test "Fuzzy search (-z)" \
    "-q -r -z \"$TERM1\""

run_test "Whole-word search (-W)" \
    "-q -r -W \"$TERM1\""

run_test "Exact phrase search (quoted)" \
    "-q -r \"$TERMS\""


# ============================================================================
#  2. PROXIMITY SEARCHES
# ============================================================================

echo "" | tee -a "$OUTFILE"
echo "=== PROXIMITY SEARCHES ===" | tee -a "$OUTFILE"

run_test "Word proximity — 5 words (-p)" \
    "-q -r -p 5 $TERM1 $TERM2"

run_test "Word proximity — 2 words (-p)" \
    "-q -r -p 2 $TERM1 $TERM2"

run_test "Line proximity — 3 lines (-P)" \
    "-q -r -P 3 $TERM1 $TERM2"


# ============================================================================
#  3. FILTER FLAGS
# ============================================================================

echo "" | tee -a "$OUTFILE"
echo "=== FILTER FLAGS ===" | tee -a "$OUTFILE"

run_test "File type filter — Python only (-t py)" \
    "-q -r -t py \"$TERM1\""

run_test "File type filter — multiple types (-t py,js,go)" \
    "-q -r -t py,js,go \"$TERM1\""

run_test "File type filter — documents (-t pdf,docx,txt)" \
    "-q -r -t pdf,docx,txt \"$TERM1\""

run_test "Recursive search (-r)" \
    "-q -r \"$TERM1\""

run_test "Exclude terms (-n)" \
    "-q -r -n xyznonexistent \"$TERM1\""

run_test "Inverse search (--inverse)" \
    "-q -r --inverse xyznonexistent"


# ============================================================================
#  4. RANGE FILTERS
# ============================================================================

echo "" | tee -a "$OUTFILE"
echo "=== RANGE FILTERS ===" | tee -a "$OUTFILE"

run_test "Amount range (-R amount:)" \
    "-q -r -R amount:0..999999 \"$TERM1\""

run_test "Number range (-R number:)" \
    "-q -r -R number:0..999999 \"$TERM1\""

run_test "File size range (-R filesize:)" \
    "-q -r -R filesize:0kb..100mb \"$TERM1\""

run_test "Multiple ranges (-R -R)" \
    "-q -r -R number:0..999999 -R filesize:0kb..100mb \"$TERM1\""


# ============================================================================
#  5. CONTEXT LINES
# ============================================================================

echo "" | tee -a "$OUTFILE"
echo "=== CONTEXT LINES ===" | tee -a "$OUTFILE"

run_test "Context before (-B 3)" \
    "-q -r -B 3 \"$TERM1\""

run_test "Context after (-A 3)" \
    "-q -r -A 3 \"$TERM1\""

run_test "Context both (-B 2 -A 2)" \
    "-q -r -B 2 -A 2 \"$TERM1\""


# ============================================================================
#  6. OUTPUT OPTIONS
# ============================================================================

echo "" | tee -a "$OUTFILE"
echo "=== OUTPUT OPTIONS ===" | tee -a "$OUTFILE"

# -s is a post-search command (copies existing results), so run a search first
peekdocs -q -r "$TERM1" >/dev/null 2>&1 || true
run_test "Save named report (-s)" \
    "-s test_report"
verify_file "peekdocs_report_test_report.txt" "peekdocs_report_test_report.txt"
verify_file "peekdocs_report_test_report.docx" "peekdocs_report_test_report.docx"
rm -f peekdocs_report_test_report.txt peekdocs_report_test_report.docx 2>/dev/null

run_test "CSV output (-o csv)" \
    "-q -r -o csv \"$TERM1\""
verify_file "peekdocs_standard_results.csv" "peekdocs_standard_results.csv"
rm -f peekdocs_standard_results.csv 2>/dev/null

run_test "JSON output (-o json)" \
    "-q -r -o json \"$TERM1\""
verify_file "peekdocs_standard_results.json" "peekdocs_standard_results.json"
rm -f peekdocs_standard_results.json 2>/dev/null

run_test "HTML output (-o html)" \
    "-q -r -o html \"$TERM1\""
verify_file "peekdocs_standard_results.html" "peekdocs_standard_results.html"
rm -f peekdocs_standard_results.html 2>/dev/null

run_test "Multiple output formats (-o csv,json,html)" \
    "-q -r -o csv,json,html \"$TERM1\""
verify_file "peekdocs_standard_results.csv" "peekdocs_standard_results.csv"
verify_file "peekdocs_standard_results.json" "peekdocs_standard_results.json"
verify_file "peekdocs_standard_results.html" "peekdocs_standard_results.html"
rm -f peekdocs_standard_results.csv peekdocs_standard_results.json peekdocs_standard_results.html 2>/dev/null

run_test "Max matches (-m 5)" \
    "-q -r -m 5 \"$TERM1\""

run_test "Quiet mode (-q)" \
    "-q -r \"$TERM1\""

run_test "Extra quiet mode (-qq)" \
    "-qq -r \"$TERM1\""

run_test "Timestamp flag (--timestamp)" \
    "-q -r --timestamp \"$TERM1\""
# Check that timestamped files were created (peekdocs_standard_results_YYYYMMDD_HHMMSS.*)
TS_TXT=$(ls peekdocs_standard_results_*.txt 2>/dev/null | head -1)
TS_DOCX=$(ls peekdocs_standard_results_*.docx 2>/dev/null | head -1)
if [ -n "$TS_TXT" ]; then
    verify_file "$TS_TXT" "timestamped .txt report"
else
    echo "         [MISSING] No timestamped .txt report found" | tee -a "$OUTFILE"
    FAIL=$((FAIL + 1)); PASS=$((PASS - 1))
fi
if [ -n "$TS_DOCX" ]; then
    verify_file "$TS_DOCX" "timestamped .docx report"
else
    echo "         [MISSING] No timestamped .docx report found" | tee -a "$OUTFILE"
    FAIL=$((FAIL + 1)); PASS=$((PASS - 1))
fi
rm -f peekdocs_standard_results_*.txt peekdocs_standard_results_*.docx 2>/dev/null


# ============================================================================
#  7. COMBINED MODES
# ============================================================================

echo "" | tee -a "$OUTFILE"
echo "=== COMBINED MODES ===" | tee -a "$OUTFILE"

run_test "AND + file type (-a -t)" \
    "-q -r -a -t py,js $TERM1 $TERM2"

run_test "Regex + file type (-x -t)" \
    "-q -r -x \"$TERM1\" -t py"

run_test "Wildcard + exclude (-w -n)" \
    "-q -r -w \"${TERM1}*\" -n xyznonexistent"

run_test "Fuzzy + recursive (-z -r)" \
    "-q -r -z \"$TERM1\""

run_test "Whole-word + AND (-W -a)" \
    "-q -r -W -a $TERM1 $TERM2"

run_test "AND + context (-a -B -A)" \
    "-q -r -a -B 2 -A 2 $TERM1 $TERM2"

run_test "File type + range (-t -R)" \
    "-q -r -t csv,tsv -R number:0..999999 \"$TERM1\""

run_test "Inverse + file type (--inverse -t)" \
    "-q -r --inverse -t py xyznonexistent"

run_test "Expression + file type (-e -t)" \
    "-q -r -e \"$TERM1 AND $TERM2\" -t py,js,go"

run_test "Proximity + file type (-p -t)" \
    "-q -r -p 5 -t py,js $TERM1 $TERM2"


# ============================================================================
#  8. SPECIAL FEATURES
# ============================================================================

echo "" | tee -a "$OUTFILE"
echo "=== SPECIAL FEATURES ===" | tee -a "$OUTFILE"

run_test "PII scan (--pii-scan)" \
    '-q -r --pii-scan'

run_test "System check (--check)" \
    '--check'

run_test "List files (--list-files)" \
    '--list-files'

# OCR — only if Tesseract is installed
if command -v tesseract &>/dev/null; then
    run_test "OCR search (-O)" \
        "-q -r -O \"$TERM1\""
else
    run_skip "OCR search (-O)" "Tesseract not installed"
fi

# Index — build, search, then clear
run_test "Build index (--index)" \
    '--index'

run_test "Index status (--index-status)" \
    '--index-status'

run_test "Search with index" \
    "-q \"$TERM1\""

run_test "Search bypassing index (--no-index)" \
    "-q --no-index \"$TERM1\""

run_test "Clear index (--index-clear)" \
    '--index-clear'


# ============================================================================
#  9. MATCH COUNT CONSISTENCY CHECK
# ============================================================================

echo "" | tee -a "$OUTFILE"
echo "=== MATCH COUNT CONSISTENCY ===" | tee -a "$OUTFILE"

# Re-run the same baseline search and verify the count hasn't changed.
# This catches subtle bugs where earlier tests (index build, config changes,
# output format generation) leave behind side effects that alter results.
# Temporarily hide the results file so it doesn't inflate the match count
# (it grows during the run as test output is appended to it).
mv "$OUTFILE" ".${OUTFILE}.tmp" 2>/dev/null || true
RECHECK_OUTPUT=$(peekdocs -q -r "$TERM1" 2>&1) || true
mv ".${OUTFILE}.tmp" "$OUTFILE" 2>/dev/null || true
RECHECK_CLEAN=$(echo "$RECHECK_OUTPUT" | sed 's/\x1b\[[0-9;]*m//g')
RECHECK_FOUND=$(echo "$RECHECK_CLEAN" | grep -E "^Found [0-9]" || true)
RECHECK_COUNT=$(echo "$RECHECK_FOUND" | grep -oE "Found [0-9]+ match" | grep -oE "[0-9]+" || echo "0")
rm -f peekdocs_standard_results.txt peekdocs_standard_results.docx 2>/dev/null

if [ "$RECHECK_COUNT" = "$BASELINE_COUNT" ]; then
    echo "[PASS] Match count stable: $RECHECK_COUNT matches (same as baseline)" | tee -a "$OUTFILE"
    PASS=$((PASS + 1))
else
    echo "[FAIL] Match count CHANGED: baseline=$BASELINE_COUNT, recheck=$RECHECK_COUNT" | tee -a "$OUTFILE"
    FAIL=$((FAIL + 1))
fi


# ============================================================================
#  SUMMARY
# ============================================================================

{
echo ""
echo "$DIVIDER"
echo "  SUMMARY"
echo "$DIVIDER"
echo "  Passed:  $PASS"
echo "  Failed:  $FAIL"
echo "  Skipped: $SKIP"
echo "  Total:   $((PASS + FAIL + SKIP))"
echo ""
echo "  Search terms: $TERMS"
echo "  Folder:       $(pwd)"
echo "  Files found:  $FILE_COUNT (recursive, excludes peekdocs output/index/script files)"
echo "  Baseline:     $BASELINE_COUNT matches in baseline search"
echo "  Generated:    $(date '+%Y-%m-%d %H:%M:%S')"
echo "$DIVIDER"
} | tee -a "$OUTFILE"

# Final cleanup
peekdocs --clear 2>/dev/null || true
rm -f peekdocs_errors.log 2>/dev/null

echo ""
echo "Results saved to: $(pwd)/$OUTFILE"
