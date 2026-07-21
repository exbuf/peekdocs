"""Subprocess plumbing + command/result parsing for the GUI's CLI runner.

Splitting concern from the former ``gui/_helpers.py`` grab-bag. The
GUI runs peekdocs searches by shelling out to the CLI (or calling
``peekdocs.cli.main()`` in-process when PyInstaller-frozen); this
module owns:

* :func:`_run_peekdocs_cli` — the two-path subprocess-or-in-process
  runner that handles both distribution modes.
* :func:`_build_command_from_values` — assembling a CLI argv list
  from the GUI form widget values.
* :func:`_parse_summary_text`, :func:`_parse_matched_files`,
  :func:`_parse_inverse_files` — reading the CLI's stdout summary
  and the on-disk results files back into structures the GUI can
  render into result popups.
"""
from __future__ import annotations

import io
import os
import re
import shlex
import subprocess
import sys


class _StderrLineStreamer(io.StringIO):
    """StringIO subclass that also streams completed lines to a callback.

    Used only inside the PyInstaller-frozen path of
    :func:`_run_peekdocs_cli` so that phase markers written to stderr by
    the CLI (``print("PHASE: writing-docx", file=sys.stderr, flush=True)``
    and similar) reach the GUI's status-line callback in real time,
    matching the subprocess path's streaming behavior.

    Without this class, the frozen path's stderr redirected to a plain
    ``io.StringIO()`` that was only readable after ``_cli_main`` returned
    — so the GUI status line skipped every intermediate PHASE marker and
    the ``.exe`` user saw a static "Searching..." while the pipx / pip
    user saw the report-writing progression. Reported by a user on
    1.2.79. See :func:`_run_peekdocs_cli` for context.

    Buffering strategy: accumulate writes in ``_pending``; each time a
    newline arrives, split, emit all-but-last as completed lines, keep
    the tail (possibly empty) as pending. This handles partial writes,
    multi-line writes, and the trailing-newline print() case correctly.
    Callback exceptions are swallowed so a buggy status-line updater
    can't break the search.

    ``getvalue()`` still returns the full stderr content at the end
    because the underlying ``io.StringIO`` buffer receives every write
    unchanged before the streaming logic runs.
    """

    def __init__(self, on_line):
        super().__init__()
        self._on_line = on_line
        self._pending = ""

    def write(self, s):
        # Preserve full-content semantics for getvalue().
        result = super().write(s)
        # Additionally, forward completed lines to the callback.
        self._pending += s
        if "\n" in self._pending:
            parts = self._pending.split("\n")
            # All but last are complete lines; last is partial (or "").
            for line in parts[:-1]:
                try:
                    self._on_line(line.rstrip("\r"))
                except Exception:
                    # A buggy callback must not break the search.
                    pass
            self._pending = parts[-1]
        return result


def _run_peekdocs_cli(cmd, folder, env=None, on_process_started=None, on_stderr_line=None):
    """Run a peekdocs CLI command and return ``(stdout, stderr, returncode)``.

    ``on_process_started`` is an optional callback invoked with the
    live ``subprocess.Popen`` object immediately after spawn on the
    subprocess path — the caller can stash it (``self.process = proc``)
    so a Cancel button can ``proc.terminate()`` mid-flight. Ignored on
    the in-process (PyInstaller) path because there's no subprocess to
    expose. Exceptions raised by the callback are swallowed so a buggy
    caller can't break the search.

    Two paths, chosen by ``sys.frozen``:

    * **Normal pip / pipx install** — spawn a subprocess via the cmd list
      (typically ``[sys.executable, "-m", "peekdocs", "-q", ...flags...]``).
      stdout / stderr are captured through pipes, env is the inherited
      environment with UTF-8 encoding forced.

    * **PyInstaller-bundled standalone exe** — call
      ``peekdocs.cli.main()`` directly, in-process, with stdout / stderr
      redirected to string buffers. The first three elements of ``cmd``
      (``[sys.executable, "-m", "peekdocs"]``) are stripped — they're
      meaningless inside the bundle because ``sys.executable`` IS the
      GUI exe. Re-launching it via subprocess just opens another GUI
      window (which is exactly the bug that prompted this helper); the
      in-process call sidesteps that entirely.

    Notes:

    * Cancellation only works on the subprocess path. In frozen mode the
      caller cannot kill an in-flight search; the GUI's Cancel button
      becomes a no-op for the duration of the search. Acceptable
      trade-off for the standalone build's first release.
    * ``on_stderr_line`` streaming works on **both** paths as of 1.2.80.
      Subprocess uses a background reader thread; frozen mode uses a
      :class:`_StderrLineStreamer` in place of the plain ``StringIO`` so
      the CLI's ``print(..., file=sys.stderr, flush=True)`` phase markers
      reach the callback synchronously as they're written.
    * Working directory is restored on the way out even if the CLI
      raises.
    * SystemExit from the CLI is caught and converted to a return code.
    """
    if getattr(sys, "frozen", False):
        # PyInstaller bundle: run in-process. The CLI module already
        # accepts an argv list and returns an exit code.
        import contextlib
        from peekdocs.cli import main as _cli_main

        cli_argv = list(cmd[3:])  # drop [sys.executable, "-m", "peekdocs"]
        buf_out = io.StringIO()
        # Match the subprocess path: when the caller provided a status-
        # line callback, stream completed stderr lines to it in real
        # time instead of only exposing them at the end. Fixes the
        # 1.2.79 report where the .exe skipped the "building txt report"
        # step in the status line while the pipx install showed it.
        buf_err = (
            _StderrLineStreamer(on_stderr_line)
            if on_stderr_line is not None
            else io.StringIO()
        )
        old_cwd = os.getcwd()
        rc = 0
        try:
            os.chdir(folder)
            with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
                try:
                    rc = _cli_main(cli_argv)
                except SystemExit as e:
                    rc = e.code if isinstance(e.code, int) else 0
                except Exception:
                    # Surface any exception in stderr so the GUI's
                    # existing "show stderr if stdout is empty" path
                    # picks it up.
                    import traceback as _tb
                    _tb.print_exc()
                    rc = 2
        finally:
            try:
                os.chdir(old_cwd)
            except Exception:
                pass
        return buf_out.getvalue(), buf_err.getvalue(), int(rc or 0)

    # Normal pip / pipx install: subprocess path.
    if env is None:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
    proc = subprocess.Popen(
        cmd, cwd=folder,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", env=env,
    )
    if on_process_started is not None:
        try:
            on_process_started(proc)
        except Exception:
            pass
    if on_stderr_line is None:
        stdout, stderr = proc.communicate()
        return stdout, stderr, proc.returncode

    # Streaming mode: read stderr line-by-line in a background thread
    # so the caller can react to phase markers (e.g. 'PHASE: writing-docx')
    # while the subprocess is still running. stdout is collected
    # synchronously via proc.stdout.read() at the end. Exceptions in
    # the callback are swallowed so a buggy caller can't deadlock the
    # subprocess.
    import threading as _threading
    stderr_buf = []

    def _stderr_reader():
        try:
            for raw_line in proc.stderr:
                stderr_buf.append(raw_line)
                line = raw_line.rstrip("\r\n")
                try:
                    on_stderr_line(line)
                except Exception:
                    pass
        except Exception:
            pass

    t = _threading.Thread(target=_stderr_reader, daemon=True)
    t.start()
    stdout = proc.stdout.read() if proc.stdout else ""
    proc.wait()
    t.join(timeout=2.0)
    return stdout, "".join(stderr_buf), proc.returncode


def _build_command_from_values(
    search_text,
    folder,
    and_mode,
    recursive,
    fuzzy,
    wildcard,
    ocr,
    regex,
    exclude,
    file_types,
    proximity,
    context_before,
    context_after,
    cores="",
    specific_files="",
    append_name="",
    output_docx=False,
    output_csv=False,
    output_json=False,
    output_pdf=False,
    output_html=False,
    index_search=False,
    inverse=False,
    expression=False,
    whole_word=False,
    rank=False,
    max_matches="",
    max_file_size_mb="",
    timestamp_suffix="",
    output_dir="",
    range_filters="",
):
    """Build a peekdocs CLI command list from GUI values.

    Returns None on validation error, or "FLAGS_IN_SEARCH" if flags are
    detected in the search text.
    """
    if not search_text.strip() and not range_filters.strip():
        return None

    if not folder or not os.path.isdir(folder):
        return None

    # Block flags typed into the search box
    _CLI_FLAGS = {"-a", "-A", "-B", "-c", "-e", "-f", "-h", "-m", "-n", "-o", "-O", "-p", "-q", "-r", "-R", "-s", "-sa", "-t", "-v", "-w", "-W", "-x", "-z", "--config", "--inverse", "--range", "--timestamp", "--ts-suffix", "--output-dir"}
    if not expression:
        tokens = search_text.strip().split()
        if any(token in _CLI_FLAGS for token in tokens):
            return "FLAGS_IN_SEARCH"

    cmd = [sys.executable, "-m", "peekdocs", "-q"]

    if not index_search:
        cmd.append("--no-index")

    # DOCX is opt-in via -o docx as of peekdocs 1.2.6 (the CLI default
    # is now TXT-only). Plumbed below alongside csv/json/pdf/html.

    if expression:
        cmd.append("-e")
        cmd.append(search_text.strip())
    if not expression and and_mode:
        cmd.append("-a")
    if recursive:
        cmd.append("-r")
    if fuzzy:
        cmd.append("-z")
    if wildcard:
        cmd.append("-w")
    if ocr:
        cmd.append("-O")
    if regex:
        cmd.append("-x")
    if whole_word:
        cmd.append("-W")
    if rank:
        cmd.append("--rank")
    if inverse:
        cmd.append("--inverse")

    if not expression and exclude.strip():
        cmd.extend(["-n", exclude.strip()])

    if file_types.strip():
        cmd.extend(["-t", file_types.strip()])

    if not expression and proximity.strip():
        if not proximity.strip().isdigit() or int(proximity.strip()) < 1:
            return None
        cmd.extend(["-p", proximity.strip()])

    if context_before.strip():
        if not context_before.strip().isdigit():
            return None
        cmd.extend(["-B", context_before.strip()])

    if context_after.strip():
        if not context_after.strip().isdigit():
            return None
        cmd.extend(["-A", context_after.strip()])

    if cores.strip():
        if not cores.strip().isdigit() or int(cores.strip()) < 1:
            return None
        cmd.extend(["-c", cores.strip()])

    if specific_files.strip():
        cmd.extend(["-f", specific_files.strip()])

    if append_name.strip():
        cmd.extend(["-sa", append_name.strip()])

    output_parts = []
    if output_docx:
        output_parts.append("docx")
    if output_csv:
        output_parts.append("csv")
    if output_json:
        output_parts.append("json")
    if output_pdf:
        output_parts.append("pdf")
    if output_html:
        output_parts.append("html")
    if output_parts:
        cmd.extend(["-o", ",".join(output_parts)])

    mm_val = str(max_matches).strip()
    if mm_val and mm_val != "1000":
        cmd.extend(["-m", mm_val])

    if str(max_file_size_mb).strip() and str(max_file_size_mb).strip() != "100":
        cmd.extend(["--max-file-size", str(max_file_size_mb).strip()])

    if timestamp_suffix:
        cmd.extend(["--ts-suffix", timestamp_suffix])

    if output_dir.strip():
        cmd.extend(["--output-dir", output_dir.strip()])

    if range_filters.strip():
        for spec in range_filters.split(","):
            spec = spec.strip()
            if spec:
                cmd.extend(["-R", spec])

    if expression:
        pass  # already appended right after -e
    elif regex:
        # Preserve backslashes for regex patterns (shlex.split eats them)
        lex = shlex.shlex(search_text.strip(), posix=True)
        lex.escape = ""
        lex.commenters = ""
        lex.whitespace_split = True
        try:
            terms = list(lex)
        except ValueError:
            terms = search_text.strip().split()
        cmd.extend(terms)
    else:
        try:
            terms = shlex.split(search_text.strip())
        except ValueError:
            terms = search_text.strip().split()
        cmd.extend(terms)

    return cmd


def _parse_summary_text(stdout):
    """Parse CLI summary output into a short status string."""
    if not stdout:
        return ""
    clean = re.sub(r"\033\[[0-9;]*m", "", stdout)
    files_match = re.search(r"Files searched:\s*(\d+)", clean)
    size_match = re.search(r"Files searched:\s*\d+\s*\(([\d.]+ [KMGT]?B)\)", clean)
    found_match = re.search(r"Found\s+(\d+)\s+match", clean)
    matched_files_match = re.search(r"match\(es\)\s+in\s+(\d+)\s+file\(s\)", clean)
    capped_match = re.search(r"Reports capped at ([\d,]+)", clean)
    inverse_match = re.search(r"Found\s+(\d+)\s+file\(s\)\s+WITHOUT\s+matches", clean)
    elapsed_match = re.search(r"Elapsed time:\s*([\d.]+)\s*seconds", clean)

    parts = []
    # Lead with files searched + elapsed time so the headline metric
    # ('N files searched in T seconds') reads first — that's the
    # impressive number for the hero video and the most useful
    # 'is this fast?' signal for everyday use. Match count and the
    # report cap follow as secondary information.
    if files_match:
        try:
            files_n_str = f"{int(files_match.group(1)):,}"
        except (TypeError, ValueError):
            files_n_str = files_match.group(1)
        file_part = f"{files_n_str} file(s) searched"
        if size_match:
            file_part += f" ({size_match.group(1)})"
        parts.append(file_part)
    if elapsed_match:
        parts.append(f"in {elapsed_match.group(1)}s")
    if inverse_match:
        parts.append(f"— found {inverse_match.group(1)} file(s) WITHOUT matches")
    elif found_match:
        count = found_match.group(1)
        in_files = f" in {matched_files_match.group(1)} file(s)" if matched_files_match else ""
        parts.append(f"— found {count} match(es){in_files}")
        if capped_match:
            parts.append(f"— reports capped at {capped_match.group(1)}")

    errors_match = re.search(r"(\d+)\s+error\(s\)", clean)
    if errors_match:
        err_count = errors_match.group(1)
        parts.append(f"— {err_count} file(s) could not be read")

    # Surface the "Note: index bypassed — …" line emitted by the CLI when
    # the user asked for the index but the engine fell through to direct
    # scan (regex / fuzzy / wildcard / proximity queries). The bypass is
    # silent on disk; here we keep the user informed about what happened.
    bypass_match = re.search(r"Note: index bypassed — ([^\n.]+)", clean)
    if bypass_match:
        parts.append(f"— index bypassed ({bypass_match.group(1).strip()})")

    # Surface the "Note: index built with max-file-size=N MB; …" stale-index
    # notice emitted when the saved index parameters don't match the current
    # search settings. The condensed status-line version just calls it out
    # as "stale" — the user can re-run `peekdocs --index` for the full text.
    stale_match = re.search(r"Note: index (built with max-file-size|lacks max-file-size|has unparseable)", clean)
    if stale_match:
        parts.append("— index settings out of sync (run --index to refresh)")

    return " ".join(parts) if parts else ""


def _parse_matched_files(results_dir, results_filename="peekdocs_standard_results.txt"):
    """Parse a .txt result report and return a list of (filepath, filename, count, line_nums) tuples.

    Handles both normal results (Document: ..., Line: ...) and inverse results
    (Files WITHOUT matches: ... followed by filename/directory pairs).
    """
    results_path = os.path.join(results_dir, results_filename)
    if not os.path.exists(results_path):
        return []
    data = {}  # filepath -> {"filename": ..., "count": int, "lines": [int, ...]}
    order = []
    with open(results_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    i = 0
    in_inverse = False
    while i < len(lines):
        line = lines[i].strip()

        # Detect inverse results section
        if line.startswith("Files WITHOUT matches:"):
            in_inverse = True
            i += 1
            continue

        # Parse inverse file list: filename on one line, (directory) on next
        if in_inverse:
            if line and not line.startswith("("):
                filename = line
                if i + 1 < len(lines):
                    dir_line = lines[i + 1].strip()
                    if dir_line.startswith("(") and dir_line.endswith(")"):
                        file_dir = dir_line[1:-1]
                        filepath = os.path.join(file_dir, filename)
                        if filepath not in data:
                            data[filepath] = {
                                "filename": filename,
                                "count": 0,
                                "lines": [],
                            }
                            order.append(filepath)
                        i += 2
                        continue
            i += 1
            continue

        # Parse normal results: Document: ..., Line: ...
        if line.startswith("Document: ") and ", Line: " in line:
            if i + 1 < len(lines):
                dir_line = lines[i + 1].strip()
                if dir_line.startswith("(") and dir_line.endswith(")"):
                    file_dir = dir_line[1:-1]
                    raw_name = line.split("Document: ")[1].split(", Line: ")[0]
                    filename = re.sub(r"\s+\(\d+ match(?:es)?\)$", "", raw_name)
                    line_num_str = line.split(", Line: ")[1].strip()
                    line_num_match = re.match(r"(\d+)", line_num_str)
                    line_num = int(line_num_match.group(1)) if line_num_match else None
                    filepath = os.path.join(file_dir, filename)
                    if filepath in data:
                        data[filepath]["count"] += 1
                        if line_num is not None:
                            data[filepath]["lines"].append(line_num)
                    else:
                        data[filepath] = {
                            "filename": filename,
                            "count": 1,
                            "lines": [line_num] if line_num is not None else [],
                        }
                        order.append(filepath)
        i += 1
    return [(fp, data[fp]["filename"], data[fp]["count"], data[fp]["lines"]) for fp in order]


def _parse_inverse_files(results_dir, results_filename="peekdocs_standard_results.txt"):
    """Parse a .txt result report for inverse search and return (filepath, filename, 0, []) tuples."""
    results_path = os.path.join(results_dir, results_filename)
    if not os.path.exists(results_path):
        return []
    result = []
    with open(results_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    in_inverse = False
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("Files WITHOUT matches:"):
            in_inverse = True
            i += 1
            continue
        if in_inverse:
            # Stop at the first Document: line (match details section)
            if line.startswith("Document:"):
                break
            # Each inverse file is two lines: "  filename" then "  (directory)"
            if line and not line.startswith("("):
                if i + 1 < len(lines):
                    dir_line = lines[i + 1].strip()
                    if dir_line.startswith("(") and dir_line.endswith(")"):
                        file_dir = dir_line[1:-1]
                        filename = line
                        filepath = os.path.join(file_dir, filename)
                        result.append((filepath, filename, 0, []))
                        i += 2
                        continue
        i += 1
    return result

