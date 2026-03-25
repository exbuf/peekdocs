"""Command-line interface for DocSearch."""

import logging
import multiprocessing
import os
import platform
import re
import shutil
import signal
import sys
import threading
import time
import traceback
from datetime import datetime
from importlib.metadata import version as pkg_version

logging.getLogger("pymupdf").setLevel(logging.ERROR)

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


VERSION = pkg_version("docsearch")

HIGHLIGHT = "\033[1;94m"
RESET = "\033[0m"

from docsearch.constants import SUPPORTED_TYPES, OCR_IMAGE_TYPES, FUZZY_THRESHOLD, _default_cores  # noqa: E402

BANNER_TOP = (
    '\n OR search — finds paragraphs containing ANY of the search terms. Example: docsearch term1 term2 term3\n'
    'AND search — finds paragraphs containing ALL of the search terms. Example: docsearch -a term1 term2 term3\n'
    'Use option flag -a for AND searches. Example: docsearch -a term1 term2 term3\n'
    'Use option flag -A to show lines after each match. Example: docsearch -A 5 term1\n'
    'Use option flag -B to show lines before each match. Example: docsearch -B 5 term1\n'
    'Use option flag -c to set number of CPU cores. Example: docsearch -c 4 budget revenue\n'
    'Use option flag -f to search specific files. Example: docsearch -f report.pdf,notes.txt term1\n'
    'Use option flag -h for help. Example: docsearch -h     (Also displays common Regex patterns)\n'
    'Use option flag -n to exclude lines matching specified terms. Example: docsearch -n draft budget\n'
    'Use option flag -o to output additional formats (csv, json). Example: docsearch -o csv budget\n'
    'Use option flag -O to enable OCR for scanned PDFs and images. Example: docsearch -O budget\n'
    'Use option flag -p to find terms within N words of each other. Example: docsearch -p 5 budget revenue'
)

BANNER_BOTTOM = (
    'Use option flag -r to search subdirectories. Example: docsearch -r term1 term2 term3\n'
    'Use option flag -s to save the last search report. Example: docsearch -s name_of_my_file\n'
    'Use option flag -sa to search and auto-append results to a named file. Example: docsearch -sa my_report budget revenue\n'
    'Use option flag -t to filter by file type. Example: docsearch -t pdf,docx term1 term2\n'
    'Use option flag -v for version. Example: docsearch -v\n'
    'Use option flag -w for wildcard pattern matching (* and ?). Example: docsearch -w "budg*"\n'
    'Use option flag -x for regex searches. Example: docsearch -x "\\d{3}-\\d{3}-\\d{4}"\n'
    'Use option flag -z for fuzzy matching (approximate matches, typo-tolerant). Example: docsearch -z budgt\n'
    'Special characters (<, >, [, ], *, ?, $, |, etc.) must be enclosed in quotes\n'
    'More details here: https://github.com/exbuf/docsearch/blob/main/README.md'
)

REGEX_PATTERNS = (
    '\nCommon Regex Search Patterns (enclose in quotes):\n'
    '  \\d{3}-\\d{3}-\\d{4}                              US phone numbers (555-123-4567)\n'
    '  [A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z]{2,}    Email addresses (jane@example.com)\n'
    '  \\d{4}-\\d{2}-\\d{2}                              Dates, YYYY-MM-DD (2026-03-17)\n'
    '  \\$\\d+(\\.\\d{2})?                                 Dollar amounts ($45.99)\n'
    '  \\d{3}-\\d{2}-\\d{4}                              SSN format (123-45-6789)\n'
    '  \\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}              IP addresses (192.168.1.1)\n'
    '  https?://\\S+                                    URLs (https://example.com)\n'
    '  \\b[A-Z]{2,}\\b                                   Acronyms, all caps (NASA, FBI)\n'
    '  \\b\\d{5}(-\\d{4})?\\b                              US ZIP codes (12345 or 12345-6789)\n'
    '  \\(\\d{3}\\)\\s?\\d{3}-\\d{4}                         Phone with area code parens ((555) 123-4567)\n'
    '  \\b[A-Z][a-z]+\\s[A-Z][a-z]+\\b                    Proper names (John Smith)\n'
    '  \\b\\d+%                                          Percentages (92%)\n'
    '  Q[1-4]\\s?\\d{4}                                  Fiscal quarters (Q1 2026)\n'
)


CONFIG_BOOL_KEYS = {"recursive", "quiet", "match_all", "regex", "ocr", "fuzzy", "wildcard"}
CONFIG_INT_KEYS = {"cores", "context_before", "context_after"}
CONFIG_STR_KEYS = {"file_types"}
CONFIG_ALL_KEYS = CONFIG_BOOL_KEYS | CONFIG_INT_KEYS | CONFIG_STR_KEYS


def _config_path():
    """Return the path to ~/.docsearchrc."""
    return os.path.join(os.path.expanduser("~"), ".docsearchrc")


def _load_config():
    """Load defaults from ~/.docsearchrc if it exists."""
    path = _config_path()
    if not os.path.exists(path):
        return {}
    config = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key in CONFIG_BOOL_KEYS:
                config[key] = value.lower() in ("true", "yes", "1")
            elif key in CONFIG_INT_KEYS:
                try:
                    config[key] = int(value)
                except ValueError:
                    pass
            elif key in CONFIG_STR_KEYS:
                if value:
                    config[key] = value
    return config


def _save_config(settings):
    """Write settings dict to ~/.docsearchrc."""
    path = _config_path()
    with open(path, "w") as f:
        f.write("# ~/.docsearchrc - docsearch defaults\n")
        f.write("# Command-line flags always override these settings\n\n")
        for key in sorted(settings):
            value = settings[key]
            if isinstance(value, bool):
                f.write(f"{key} = {'true' if value else 'false'}\n")
            else:
                f.write(f"{key} = {value}\n")


# Re-export from scanner so tests can monkeypatch via docsearch.cli
from docsearch.scanner import _process_file, _ocr_image, discover_files  # noqa: E402
from docsearch.parser import parse_flags  # noqa: E402
from docsearch.reporter import (  # noqa: E402
    fmt_size, write_txt_report, write_docx_report,
    insert_file_sizes, write_csv_report, write_json_report,
    append_results,
)


def main(argv=None):
    try:
        return _main_inner(argv)
    except KeyboardInterrupt:
        print("\nSearch cancelled.\n")
        return 2
    except Exception:
        error_log_path = os.path.join(os.getcwd(), "docsearch_errors.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(error_log_path, "a") as log_f:
            log_f.write(f"\n{'='*60}\n")
            log_f.write(f"{timestamp}  CRASH REPORT\n")
            log_f.write(f"docsearch {VERSION}\n")
            log_f.write(f"Python {sys.version}\n")
            log_f.write(f"OS: {platform.system()} {platform.release()}\n")
            cmd = " ".join(argv) if argv else " ".join(sys.argv[1:])
            log_f.write(f"Command: docsearch {cmd}\n")
            log_f.write(f"{'='*60}\n")
            traceback.print_exc(file=log_f)
            log_f.write("\n")
        print(f"\nAn unexpected error occurred. Details logged to docsearch_errors.log\n")
        return 2


def _main_inner(argv=None):
    if argv is None:
        args = sys.argv[1:]
    else:
        args = list(argv)

    original_args = list(args)

    config = _load_config()

    quiet = "-q" in args or config.get("quiet", False)
    if "-q" in args:
        args.remove("-q")

    cpu_count = os.cpu_count() or 1
    is_help = args and args[0] in ("-h", "-help", "--help")
    if not quiet:
        print(BANNER_TOP)
        if is_help:
            print('Use option flag -q to suppress the output banner. Example: docsearch -q budget revenue')
        else:
            print('Use option flag -q to suppress this output banner. Example: docsearch -q budget revenue')
        print(BANNER_BOTTOM)
        print(f'Your system has {cpu_count} CPU cores (default for -c: {max(1, cpu_count // 2)})')
        print()

    if args and args[0] in ("-v", "-version"):
        print(f"docsearch {VERSION}\n")
        return 0

    if is_help:
        if quiet:
            print(BANNER_TOP)
            print('Use option flag -q to suppress the output banner. Example: docsearch -q budget revenue')
            print(BANNER_BOTTOM)
            print(f'Your system has {cpu_count} CPU cores (default for -c: {max(1, cpu_count // 2)})')
            print()
        print(REGEX_PATTERNS)
        return 0

    if not args:
        return 0

    if args and args[0] in ("-s", "-save"):
        if len(args) < 2:
            print("No filename provided. Usage: docsearch -s name_of_your_file\n")
            return 2
        name = "_".join(args[1:]).replace(" ", "_")
        cwd = os.getcwd()
        src_docx = os.path.join(cwd, "docsearch_results.docx")
        src_txt = os.path.join(cwd, "docsearch_results.txt")
        dest_docx = os.path.join(cwd, f"DO_NOT_SEARCH_{name}.docx")
        dest_txt = os.path.join(cwd, f"DO_NOT_SEARCH_{name}.txt")
        if not os.path.exists(src_docx) or not os.path.exists(src_txt):
            print("No search results found. Run a search first.\n")
            return 2
        shutil.copy2(src_docx, dest_docx)
        shutil.copy2(src_txt, dest_txt)
        print(f"Results saved to {os.path.basename(dest_docx)} and {os.path.basename(dest_txt)}\n")
        return 0

    if args and args[0] == "--config":
        config_args = args[1:]
        if not config_args:
            # Show current config
            current = _load_config()
            if not current:
                print("No config file found.\n")
            else:
                print("Current settings (~/.docsearchrc):\n")
                for key in sorted(current):
                    print(f"  {key} = {current[key]}")
                print()
            return 0
        # Set or remove values
        current = _load_config()
        bool_values = {"true", "false", "yes", "no", "1", "0"}
        for pair in config_args:
            if "=" not in pair:
                print(f"Invalid format: {pair}. Use key=value (e.g., --config recursive=true)\n")
                return 2
            key, _, value = pair.partition("=")
            key = key.strip()
            value = value.strip()
            if key not in CONFIG_ALL_KEYS:
                valid = ", ".join(sorted(CONFIG_ALL_KEYS))
                print(f"Unknown setting: {key}. Valid settings: {valid}\n")
                return 2
            if not value:
                # Remove the key
                current.pop(key, None)
                print(f"Removed: {key}")
            elif key in CONFIG_BOOL_KEYS:
                if value.lower() not in bool_values:
                    print(f"Invalid value for {key}: {value}. Use true or false.\n")
                    return 2
                current[key] = value.lower() in ("true", "yes", "1")
                print(f"Set: {key} = {current[key]}")
            elif key in CONFIG_INT_KEYS:
                try:
                    int_val = int(value)
                    if int_val < 1:
                        raise ValueError
                except ValueError:
                    print(f"Invalid value for {key}: {value}. Must be a positive integer.\n")
                    return 2
                current[key] = int_val
                print(f"Set: {key} = {int_val}")
            elif key in CONFIG_STR_KEYS:
                current[key] = value
                print(f"Set: {key} = {value}")
        if current:
            _save_config(current)
        else:
            # All keys removed — delete the file
            path = _config_path()
            if os.path.exists(path):
                os.remove(path)
        print()
        return 0

    # Parse all flags
    parsed = parse_flags(args, config)
    if isinstance(parsed, tuple):
        print(parsed[1])
        return parsed[0]

    search_terms = parsed["search_terms"]
    match_all = parsed["match_all"]
    recursive = parsed["recursive"]
    use_regex = parsed["use_regex"]
    use_ocr = parsed["use_ocr"]
    use_fuzzy = parsed["use_fuzzy"]
    use_wildcard = parsed["use_wildcard"]
    exclude_terms = parsed["exclude_terms"]
    file_types = parsed["file_types"]
    file_names = parsed["file_names"]
    context_before = parsed["context_before"]
    context_after = parsed["context_after"]
    use_context = parsed["use_context"]
    proximity = parsed["proximity"]
    use_proximity = parsed["use_proximity"]
    append_name = parsed["append_name"]
    cores = parsed["cores"]
    output_formats = parsed["output_formats"]
    mode = parsed["mode"]
    report_mode = parsed["report_mode"]

    command_str = "docsearch " + " ".join(f'"{a}"' if " " in a else a for a in original_args)
    print(command_str)
    print(f"Searching ({mode}) on [{HIGHLIGHT}{', '.join(search_terms)}{RESET}] ...")
    if exclude_terms:
        print(f"Excluding [{', '.join(exclude_terms)}]")
    start_time = time.time()
    cwd = os.getcwd()

    # Discover files
    result = discover_files(cwd, recursive, use_ocr, file_types, file_names)
    if isinstance(result, tuple):
        print(result[1])
        return result[0]
    all_files = result

    search_config = {
        "search_terms": search_terms,
        "use_regex": use_regex,
        "match_all": match_all,
        "use_proximity": use_proximity,
        "proximity": proximity,
        "use_context": use_context,
        "context_before": context_before,
        "context_after": context_after,
        "use_ocr": use_ocr,
        "use_fuzzy": use_fuzzy,
        "exclude_terms": exclude_terms,
        "use_wildcard": use_wildcard,
        "_ocr_image_func": _ocr_image,
    }

    matches = []
    skipped_files = []
    total = len(all_files)
    bar_width = 40
    spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    try:
        term_width = os.get_terminal_size().columns
    except OSError:
        term_width = 80

    spinner_lock = threading.Lock()
    spinner_stop = threading.Event()
    spinner_state = {"done": 0, "filename": ""}

    def _render_progress(done, total_count, filename, spinner=""):
        if total_count == 0:
            return
        pct = done / total_count
        filled = int(bar_width * pct)
        bar = "█" * filled + "░" * (bar_width - filled)
        if spinner:
            line = f"\r  [{bar}] {done}/{total_count} {filename} {spinner}"
        else:
            line = f"\r  [{bar}] {done}/{total_count} {filename}"
        line = line.ljust(term_width)[:term_width]
        sys.stdout.write(line)
        sys.stdout.flush()

    def _spinner_thread():
        idx = 0
        while not spinner_stop.is_set():
            with spinner_lock:
                done = spinner_state["done"]
                filename = spinner_state["filename"]
            _render_progress(done, total, filename, spinner_chars[idx % len(spinner_chars)])
            idx += 1
            spinner_stop.wait(0.15)

    spinner = threading.Thread(target=_spinner_thread, daemon=True)
    spinner.start()

    try:
        if len(all_files) < 10 or cores == 1:
            for i, filepath in enumerate(all_files):
                filename = os.path.relpath(filepath, cwd)
                with spinner_lock:
                    spinner_state["done"] = i
                    spinner_state["filename"] = filename
                _render_progress(i, total, filename)
                file_matches, file_skipped = _process_file((filepath, search_config))
                matches.extend(file_matches)
                skipped_files.extend(file_skipped)
        else:
            # Workers ignore SIGINT so only the main process handles Ctrl+C
            pool = multiprocessing.Pool(processes=cores, initializer=signal.signal, initargs=(signal.SIGINT, signal.SIG_IGN))
            try:
                result_iter = pool.imap(_process_file, [(f, search_config) for f in all_files])
                for i in range(total):
                    # Show the file we're about to wait on BEFORE blocking
                    filename = os.path.relpath(all_files[i], cwd)
                    with spinner_lock:
                        spinner_state["done"] = i
                        spinner_state["filename"] = filename
                    _render_progress(i, total, filename)
                    # Now block waiting for this file's result
                    file_matches, file_skipped = next(result_iter)
                    matches.extend(file_matches)
                    skipped_files.extend(file_skipped)
            finally:
                pool.terminate()
                pool.join()
    except KeyboardInterrupt:
        spinner_stop.set()
        spinner.join()
        sys.stdout.write("\n")
        print("\nSearch cancelled.\n")
        return 2

    spinner_stop.set()
    spinner.join()

    if total > 0:
        _render_progress(total, total, "done")
        sys.stdout.write("\n")
        sys.stdout.flush()

    for skipped_name, error_msg in skipped_files:
        print(f"Warning: Could not read {skipped_name} ({error_msg})")

    if skipped_files:
        error_log_path = os.path.join(cwd, "docsearch_errors.log")
        with open(error_log_path, "a") as log_f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for skipped_name, error_msg in skipped_files:
                log_f.write(f"{timestamp}  Could not read {skipped_name} ({error_msg})\n")

    search_elapsed = time.time() - start_time

    # Generate reports
    output_path = os.path.join(cwd, "docsearch_results.txt")
    docx_output_path = os.path.join(cwd, "docsearch_results.docx")

    total_bytes, size_str = write_txt_report(
        output_path, matches, all_files, search_terms, command_str,
        report_mode, use_ocr, exclude_terms, use_context,
        use_fuzzy, use_regex, use_wildcard,
        search_elapsed, cores, cpu_count,
    )

    result_doc = write_docx_report(docx_output_path, output_path)
    txt_size, docx_size = insert_file_sizes(output_path, docx_output_path, result_doc)

    csv_output_path = None
    json_output_path = None

    if "csv" in output_formats:
        csv_output_path = os.path.join(cwd, "docsearch_results.csv")
        write_csv_report(csv_output_path, matches)

    if "json" in output_formats:
        json_output_path = os.path.join(cwd, "docsearch_results.json")
        write_json_report(
            json_output_path, matches, search_terms, report_mode,
            len(all_files), search_elapsed,
        )

    if append_name is not None:
        append_results(append_name, cwd, output_path, docx_output_path)

    elapsed = time.time() - start_time
    print()
    print(f"Files searched: {len(all_files)} ({size_str})")
    print(f"Found {HIGHLIGHT}{len(matches)}{RESET} match(es).")
    print(f"Results ==> {cwd}")
    print(f"  docsearch_results.txt ({fmt_size(txt_size)}), docsearch_results.docx ({fmt_size(docx_size)})")
    if csv_output_path:
        print(f"  docsearch_results.csv ({fmt_size(os.path.getsize(csv_output_path))})")
    if json_output_path:
        print(f"  docsearch_results.json ({fmt_size(os.path.getsize(json_output_path))})")
    if append_name is not None:
        print(f"Results appended to DO_NOT_SEARCH_ACCUMULATED_{append_name}.txt and DO_NOT_SEARCH_ACCUMULATED_{append_name}.docx")
    print(f"Elapsed time: {elapsed:.2f} seconds, Cores used: {cores} of {cpu_count}")
    if skipped_files:
        print(f"Errors logged to docsearch_errors.log ({len(skipped_files)} error(s))")
    print()
    return 0 if matches else 1


if __name__ == "__main__":
    sys.exit(main())
