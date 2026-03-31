"""Graphical interface for DocSearch."""

import os
import platform
import re
import shlex
import subprocess
import sys
import threading
import time
from datetime import datetime


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
    output_csv=False,
    output_json=False,
    index_search=False,
    inverse=False,
    expression=False,
    whole_word=False,
    max_matches="",
    timestamp_suffix="",
    output_dir="",
    range_filters="",
):
    """Build a docsearch CLI command list from GUI values.

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

    cmd = [sys.executable, "-m", "docsearch", "-q"]

    if not index_search:
        cmd.append("--no-index")

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
    if output_csv:
        output_parts.append("csv")
    if output_json:
        output_parts.append("json")
    if output_parts:
        cmd.extend(["-o", ",".join(output_parts)])

    if str(max_matches).strip() and str(max_matches).strip() != "1000":
        cmd.extend(["-m", str(max_matches).strip()])

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
    capped_match = re.search(r"Reports capped at ([\d,]+)", clean)
    inverse_match = re.search(r"Found\s+(\d+)\s+file\(s\)\s+WITHOUT\s+matches", clean)
    elapsed_match = re.search(r"Elapsed time:\s*([\d.]+)\s*seconds", clean)

    parts = []
    if inverse_match:
        searched = files_match.group(1) if files_match else "?"
        parts.append(f"Found {inverse_match.group(1)} file(s) WITHOUT matches (of {searched} searched)")
    elif found_match:
        count = found_match.group(1)
        if capped_match:
            parts.append(f"Found {count} match(es) — reports capped at {capped_match.group(1)}")
        else:
            parts.append(f"Found {count} match(es)")
    if files_match and not inverse_match:
        parts.append(f"in {files_match.group(1)} files")
    if size_match:
        parts.append(f"({size_match.group(1)})")
    if elapsed_match:
        parts.append(f"in {elapsed_match.group(1)}s")

    errors_match = re.search(r"(\d+)\s+error\(s\)", clean)
    if errors_match:
        err_count = errors_match.group(1)
        parts.append(f"— {err_count} file(s) could not be read")

    return " ".join(parts) if parts else ""


def _parse_matched_files(results_dir, results_filename="docsearch_results.txt"):
    """Parse docsearch_results.txt and return a list of (filepath, filename, count) tuples."""
    results_path = os.path.join(results_dir, results_filename)
    if not os.path.exists(results_path):
        return []
    counts = {}  # filepath -> (filepath, filename, count)
    order = []   # preserve first-appearance order
    with open(results_path, "r") as f:
        lines = f.readlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("Document: ") and ", Line: " in line:
            # Next line has the directory in parentheses
            if i + 1 < len(lines):
                dir_line = lines[i + 1].strip()
                if dir_line.startswith("(") and dir_line.endswith(")"):
                    file_dir = dir_line[1:-1]
                    raw_name = line.split("Document: ")[1].split(", Line: ")[0]
                    # Strip per-file match count suffix e.g. "report.pdf (5 matches)"
                    filename = re.sub(r"\s+\(\d+ match(?:es)?\)$", "", raw_name)
                    filepath = os.path.join(file_dir, filename)
                    if filepath in counts:
                        counts[filepath] = (filepath, filename, counts[filepath][2] + 1)
                    else:
                        counts[filepath] = (filepath, filename, 1)
                        order.append(filepath)
        i += 1
    return [counts[fp] for fp in order]


def _parse_inverse_files(results_dir, results_filename="docsearch_results.txt"):
    """Parse docsearch_results.txt for inverse search and return (filepath, filename, 0) tuples."""
    results_path = os.path.join(results_dir, results_filename)
    if not os.path.exists(results_path):
        return []
    result = []
    with open(results_path, "r") as f:
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
                        result.append((filepath, filename, 0))
                        i += 2
                        continue
        i += 1
    return result


def _build_wizard_regex(selected_patterns):
    """Combine selected (label, regex) tuples into a single regex.

    Returns a regex string joining patterns with '|' (OR).
    """
    if not selected_patterns:
        return ""
    return "|".join(f"({regex})" for _, regex in selected_patterns)


def _launch_gui():
    """Import customtkinter and build the GUI. Separated to keep module importable without tkinter."""
    try:
        import customtkinter as ctk
    except ImportError:
        print("GUI mode requires customtkinter. Install it with: pip install customtkinter")
        sys.exit(1)

    import webbrowser
    from tkinter import filedialog, messagebox
    from importlib.metadata import version as pkg_version

    class Tooltip:
        """Simple hover tooltip for any widget."""

        enabled = True

        def __init__(self, widget, text):
            self.widget = widget
            self.text = text
            self.tip_window = None
            widget.bind("<Enter>", self._show)
            widget.bind("<Leave>", self._hide)
            # Bind to internal children (needed for CTk composite widgets)
            for child in widget.winfo_children():
                child.bind("<Enter>", self._show)
                child.bind("<Leave>", self._hide)

        def _show(self, event=None):
            if self.tip_window or not Tooltip.enabled:
                return
            import tkinter as tk
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
            self.tip_window = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            label = tk.Label(
                tw, text=self.text, background="#333333", foreground="white",
                relief="solid", borderwidth=1, font=("TkDefaultFont", 12),
                padx=6, pady=4, wraplength=300, justify="left",
            )
            label.pack()

        def _hide(self, event=None):
            if self.tip_window:
                self.tip_window.destroy()
                self.tip_window = None

    class DocSearchApp(ctk.CTk):
        def __init__(self):
            super().__init__()

            try:
                version = pkg_version("docsearch")
            except Exception:
                version = ""
            self.title(f"docsearch {version}".strip())
            self.geometry("700x720")
            self.minsize(750, 620)
            self._center_window(900, 720)

            ctk.set_appearance_mode("System")
            ctk.set_default_color_theme("blue")

            self.process = None
            self.search_thread = None
            self.results_dir = None
            self.advanced_visible = False
            self.suite_visible = False
            self.suite_running = False
            self.suite_cancel_requested = False
            self.elapsed_timer_id = None
            self.search_start_time = None
            self._refresh_timer_id = None
            self._refresh_running = False
            self._suite_schedule_timer_id = None
            self._suite_schedule_running = False
            self._suite_scheduled_run = False
            self._scheduled_suite_name = None
            self._scheduled_suite_interval = None
            self._scheduled_next_run_time = None
            self._countdown_timer_id = None
            self._text_size_var = ctk.StringVar(value="Normal")

            self.grid_columnconfigure(1, weight=1)
            self.grid_rowconfigure(8, weight=1)

            # Shared toggle row for Advanced Options, Search Suites, Index Options
            self._toggle_row = ctk.CTkFrame(self, fg_color="transparent")
            self._toggle_row.grid(
                row=2, column=0, columnspan=3, padx=15, pady=(10, 0), sticky="ew"
            )

            self._build_search_row()
            self._build_folder_row()
            self._build_advanced_toggle()
            self._build_advanced_panel()
            self._build_progress_area()
            self._build_open_report()
            self._build_index_panel()
            self.suite_window = None
            self._build_bottom_row()
            # Check for first run before loading settings (which creates the config file)
            from docsearch.cli import _config_path
            self._is_first_run = not os.path.exists(_config_path())
            self._load_saved_settings()
            # Re-apply settings after event loop starts (CTkToplevel widgets may
            # reset their variables during initialization)
            self.after(100, self._load_saved_settings)
            self._update_index_button_color()
            self._refresh_load_search_menu()
            if self._is_first_run:
                self.after(300, self._show_welcome)
            self.after(500, self._resume_suite_schedule)

        def _center_window(self, width, height):
            self.update_idletasks()
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            x = (screen_w - width) // 2
            y = (screen_h - height) // 2
            self.geometry(f"{width}x{height}+{x}+{y}")

        # ── Layout builders ──────────────────────────────────────

        def _build_search_row(self):
            self.search_bar_frame = ctk.CTkFrame(self)
            self.search_bar_frame.grid(
                row=0, column=0, columnspan=3, padx=10, pady=(10, 2), sticky="ew"
            )
            self.search_bar_frame.grid_columnconfigure(0, minsize=130)
            self.search_bar_frame.grid_columnconfigure(1, weight=1)
            self.search_bar_frame.grid_columnconfigure(2, minsize=170)

            ctk.CTkLabel(
                self.search_bar_frame, text="Search Bar",
                font=ctk.CTkFont(size=10), text_color=("gray50", "gray50"),
            ).grid(row=0, column=0, columnspan=2, padx=10, pady=(4, 0), sticky="w")

            search_help_btn = ctk.CTkButton(
                self.search_bar_frame, text="?", width=28, height=28,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self._show_search_help,
            )
            search_help_btn.grid(row=0, column=2, padx=(0, 10), pady=(4, 0), sticky="e")
            Tooltip(search_help_btn, "Search examples and quick-start guide")

            label = ctk.CTkLabel(self.search_bar_frame, text="Search Terms:", font=ctk.CTkFont(size=14))
            label.grid(row=1, column=0, padx=(15, 5), pady=(0, 8), sticky="e")

            self.search_entry = ctk.CTkEntry(
                self.search_bar_frame, placeholder_text="Enter search terms...", font=ctk.CTkFont(size=14)
            )
            self.search_entry.grid(row=1, column=1, columnspan=2, padx=(5, 105), pady=(0, 8), sticky="ew")
            self.search_entry.bind("<Return>", lambda e: self.start_search())

            clear_button = ctk.CTkButton(
                self.search_bar_frame, text="Clear", width=90,
                command=lambda: self.search_entry.delete(0, "end"),
                font=ctk.CTkFont(size=14),
            )
            clear_button.grid(row=1, column=2, padx=(5, 10), pady=(0, 8), sticky="e")

            # Row 2: action buttons below the search entry
            btn_frame = ctk.CTkFrame(self.search_bar_frame, fg_color="transparent")
            btn_frame.grid(row=2, column=1, columnspan=3, padx=5, pady=(0, 8), sticky="w")

            self.search_button = ctk.CTkButton(
                btn_frame, text="Run Search", width=100, command=self.start_search,
                font=ctk.CTkFont(size=14),
            )
            self.search_button.pack(side="left", padx=(0, 5))

            self.wizard_button = ctk.CTkButton(
                btn_frame, text="Wizard", width=80, command=self._open_search_wizard,
                font=ctk.CTkFont(size=14),
            )
            self.wizard_button.pack(side="left", padx=(0, 5))
            Tooltip(self.wizard_button, "Open the Search Wizard to build regex patterns from presets")

            self.save_to_collection_btn = ctk.CTkButton(
                btn_frame, text="Save Search", width=100, command=self._save_to_collection,
                font=ctk.CTkFont(size=14),
            )
            self.save_to_collection_btn.pack(side="left", padx=(0, 5))
            Tooltip(self.save_to_collection_btn, "Save the current search settings to the folder's collection for reuse in search suites")

            self.load_search_btn = ctk.CTkButton(
                btn_frame, text="Load Settings ▼", width=140,
                font=ctk.CTkFont(size=14),
                command=self._open_load_search_popup,
            )
            self.load_search_btn.pack(side="left", padx=(0, 5))
            Tooltip(self.load_search_btn, "Load a saved search into the GUI to review, edit, or re-run it")
            self._load_search_popup = None

            self.suite_toggle = ctk.CTkButton(
                self._toggle_row,
                text="\u25b6 Search Suites",
                width=110,
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                anchor="w",
                command=self._toggle_suite_panel,
                font=ctk.CTkFont(size=13),
            )
            self.suite_toggle.pack(side="left", padx=(10, 0))

            Tooltip(self.search_entry, "Type one or more search terms separated by spaces — there is no limit to the number of terms. Use quotes for phrases (e.g., \"annual report\"). All searches are case-insensitive. Do not use commas. Do not enter flags here — the checkboxes under Advanced Options handle that. When Expression is checked, enter a boolean expression instead (e.g., \"(bob AND amy) OR fred NOT draft\").")

        def _show_welcome(self):
            """Show a getting-started guide for first-time users."""
            import tkinter as tk
            win = tk.Toplevel(self)
            win.title("Welcome to docsearch")
            win.geometry("620x480")
            win.resizable(True, True)
            win.transient(self)
            win.grab_set()

            text_frame = tk.Frame(win)
            text_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))

            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side="right", fill="y")

            txt = tk.Text(
                text_frame, wrap="word", font=("TkDefaultFont", 12),
                state="normal", yscrollcommand=scrollbar.set,
                padx=12, pady=10, spacing3=2,
            )
            txt.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=txt.yview)

            txt.tag_configure("heading", font=("TkDefaultFont", 14, "bold"), spacing1=8, spacing3=4)
            txt.tag_configure("subhead", font=("TkDefaultFont", 12, "bold"), spacing1=8, spacing3=2)
            txt.tag_configure("body", font=("TkDefaultFont", 12), lmargin1=20, lmargin2=20)
            txt.tag_configure("step", font=("TkDefaultFont", 12, "bold"), lmargin1=20, lmargin2=40)
            txt.tag_configure("example", font=("Courier", 12), lmargin1=30, lmargin2=30)

            def h(text):
                txt.insert("end", text + "\n", "heading")
            def s(text):
                txt.insert("end", text + "\n", "subhead")
            def b(text):
                txt.insert("end", text + "\n", "body")
            def st(text):
                txt.insert("end", text + "\n", "step")
            def e(text):
                txt.insert("end", text + "\n", "example")
            def blank():
                txt.insert("end", "\n")

            h("Welcome to docsearch!")
            b("docsearch lets you search Word docs, PDFs, spreadsheets,")
            b("emails, and 38 other file types \u2014 all at once, all offline.")
            b("Results are saved to a highlighted Word report.")
            blank()

            h("Quick Start \u2014 Your First Search")
            blank()
            st("Step 1: Choose a folder")
            b("Click the Browse button next to the Search Folder field")
            b("and navigate to the folder containing your documents.")
            blank()
            st("Step 2: Type your search terms")
            b("In the Search Terms field, type what you're looking for.")
            b("Separate multiple terms with spaces.")
            e("budget revenue")
            blank()
            st("Step 3: Click Run Search")
            b("docsearch scans every supported file in the folder and")
            b("shows a summary when finished. Your results appear in")
            b("a preview below, and are saved to two report files:")
            e("docsearch_results.txt   (plain text)")
            e("docsearch_results.docx  (Word, with highlights)")
            blank()
            st("Step 4: View your results")
            b("Click the DOCX button next to View Report to open the")
            b("Word report with your matches highlighted in yellow.")
            blank()

            h("What's Next?")
            blank()
            s("Search subfolders")
            b("Open Advanced Options and check Recursive to search")
            b("all subfolders, not just the selected folder.")
            blank()
            s("Use advanced search modes")
            b("Open Advanced Options for regex, fuzzy matching,")
            b("wildcards, Boolean expressions, range queries, and more.")
            b("Click the ? button inside Advanced Options for help.")
            blank()
            s("Build compliance suites")
            b("Save individual searches and group them into suites")
            b("that run as a batch with pass/fail tracking. Click")
            b("Search Suites to get started.")
            blank()
            s("Get help anytime")
            b("Click the ? button in the bottom-left corner for the")
            b("full search guide with examples.")
            blank()

            b("This welcome screen appears only on first launch.")
            b("You won't see it again.")

            txt.configure(state="disabled")

            close_btn = ctk.CTkButton(
                win, text="Get Started", width=120,
                command=win.destroy,
                font=ctk.CTkFont(size=14),
            )
            close_btn.pack(pady=(5, 10))

        def _show_search_help(self):
            """Show a quick-start guide with search examples by category."""
            import tkinter as tk
            help_win = tk.Toplevel(self)
            help_win.title("Search Examples & Quick-Start Guide")
            help_win.geometry("750x520")
            help_win.resizable(True, True)
            help_win.transient(self)
            help_win.grab_set()

            # Scrollable text widget
            text_frame = tk.Frame(help_win)
            text_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))

            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side="right", fill="y")

            txt = tk.Text(
                text_frame, wrap="word", font=("TkDefaultFont", 12),
                state="normal", yscrollcommand=scrollbar.set,
                padx=12, pady=10, spacing3=2,
            )
            txt.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=txt.yview)

            # Configure tags
            txt.tag_configure("heading", font=("TkDefaultFont", 13, "bold"), spacing1=12, spacing3=4)
            txt.tag_configure("subhead", font=("TkDefaultFont", 12, "bold"), spacing1=10, spacing3=2)
            txt.tag_configure("example", font=("Courier", 12), lmargin1=20, lmargin2=20)
            txt.tag_configure("body", font=("TkDefaultFont", 12), lmargin1=20, lmargin2=20)

            def h(text):
                txt.insert("end", text + "\n", "heading")

            def s(text):
                txt.insert("end", text + "\n", "subhead")

            def e(text):
                txt.insert("end", text + "\n", "example")

            def b(text):
                txt.insert("end", text + "\n", "body")

            def blank():
                txt.insert("end", "\n")

            h("GETTING STARTED")
            b("All searches are case-insensitive. Type your terms in the Search Bar,")
            b("pick a folder with Browse, and click Run Search. Use the checkboxes")
            b("under Advanced Options to change search modes \u2014 do not type flags in")
            b("the search box. Results are saved to docsearch_results.txt and .docx.")
            blank()

            h("SIMPLE SEARCH")
            b("Type one or more terms separated by spaces. By default, any term matches (OR mode).")
            e("budget                \u2192  finds lines containing \"budget\"")
            e("budget revenue        \u2192  finds lines with \"budget\" OR \"revenue\"")
            e("\"annual report\"       \u2192  exact phrase match (use quotes)")
            blank()

            h("AND MODE")
            b("Check the AND mode checkbox. All terms must appear in the same line.")
            e("budget revenue        \u2192  line must contain both words")
            e("\"Q1\" \"2024\"           \u2192  line must contain both phrases")
            blank()

            h("BOOLEAN EXPRESSIONS")
            b("Check the Expression checkbox. Combine AND, OR, NOT with parentheses.")
            e("budget AND revenue")
            e("(bob AND amy) OR fred")
            e("contract NOT draft")
            e("(salary OR bonus) AND NOT confidential")
            blank()

            b("For help with Fuzzy, Regex, Wildcard, Whole Word, Proximity,")
            b("Range Filters, Context Lines, and other advanced options, click")
            b("the ? button inside the Advanced Options window.")
            blank()

            h("BREAKING DOWN COMPLEX SEARCHES")
            b("When a single search becomes too complex, break it into")
            b("several focused searches and combine them in a suite.")
            blank()
            s("Why this helps")
            b("\u2022 Each search is simpler to configure and understand")
            b("\u2022 You see which specific check passed or failed")
            b("\u2022 Different criteria per search (>= 1, == 0, <= N)")
            b("\u2022 Easy to update one check without affecting others")
            b("\u2022 Reusable across multiple suites")
            blank()
            s("Example: Contract compliance audit")
            b("Instead of one giant search, create these saved searches:")
            e("1. \"has_signature\"     \u2014 Regex: Authorized\\s+Signature  (>= 1)")
            e("2. \"has_date\"          \u2014 Regex: \\d{2}/\\d{2}/\\d{4}      (>= 1)")
            e("3. \"no_draft_stamp\"    \u2014 Terms: DRAFT                   (== 0)")
            e("4. \"amount_in_range\"   \u2014 Range: amount:1000..50000      (>= 1)")
            e("5. \"no_pii\"            \u2014 Regex: \\d{3}-\\d{2}-\\d{4}      (== 0)")
            b("Group them into a 'contract_review' suite. Run with one click")
            b("and get a report showing exactly which checks passed or failed.")
            blank()
            s("Example: Cascade pipeline")
            b("Use cascade mode to progressively narrow results:")
            e("Stage 1: Find all PDFs mentioning \"contract\"")
            e("Stage 2: Of those, find ones with \"termination\"")
            e("Stage 3: Of those, find ones with dollar amounts")
            b("Each stage feeds its matched files into the next stage.")
            blank()

            h("TIPS")
            b("\u2022 Use Save Search to save a search for reuse in Search Suites.")
            b("\u2022 Click Open Readme.md in the toolbar for full documentation.")
            blank()

            h("SEARCH SUITES")
            b("Search Suites let you save individual searches, group them into named")
            b("suites, and run them as a batch with pass/fail tracking. This turns")
            b("docsearch into an audit automation tool.")
            blank()
            s("How to use")
            b("1. Configure a search in the main GUI and click Save Search.")
            b("2. Click Search Suites in the Search Bar to open the suites window.")
            b("3. Click Build a New Suite, give it a name, and use the dual-panel selector")
            b("   to choose and order your saved searches (\u2192/\u2190 to add/remove,")
            b("   \u25b2/\u25bc to reorder).")
            b("4. Select a suite and click Run Selected Suite. Each search runs")
            b("   sequentially with real-time PASS/FAIL indicators.")
            b("5. Reports are auto-generated with timestamps after each run.")
            blank()
            s("Cascade mode")
            b("Check Cascade when creating a suite to enable progressive narrowing.")
            b("Each stage's matched files become the input for the next stage,")
            b("creating a pipeline that narrows results step by step.")
            e("Stage 1: \"contract\"       \u2192  finds 50 files")
            e("Stage 2: \"termination\"    \u2192  searches only those 50 files")
            e("Stage 3: \"penalty\"        \u2192  searches only Stage 2's matches")
            blank()
            s("Auto-Run scheduling")
            b("Select a suite and use the Auto-Run dropdown to schedule it at")
            b("an interval (30 min, 1 hour, 4 hours, 12 hours, 24 hours).")
            b("Scheduled runs are skipped if a search or build is in progress.")
            b("The Last Run label shows the suite name and timestamp of its")
            b("most recent run (manual or scheduled).")
            blank()
            s("Pass criteria")
            b("By default, a search passes if it finds >= 1 match. You can set")
            b("custom criteria per-search in the suite editor. Select a search")
            b("in the right panel and use the Pass criteria dropdown:")
            e(">= N    Pass if matches >= N   (e.g., >= 5 = at least 5)")
            e("<= N    Pass if matches <= N   (e.g., <= 3 = at most 3)")
            e("== N    Pass if matches == N   (e.g., == 0 = no matches)")
            b("Results show the criteria: [PASS] search \u2014 12 match(es) (need >= 1)")
            blank()
            s("Output & cleanup")
            b("Each search produces its own stage report file. Set Output Dir to")
            b("write suite files to a separate folder. All generated files use a")
            b("DO_NOT_SEARCH prefix so they are never re-searched. Use the")
            b("Clean Up Suite Files button to delete all generated suite files.")
            blank()
            s("Use cases")
            b("\u2022 Compliance audits \u2014 repeat the same checks on document sets")
            b("\u2022 Quality assurance \u2014 verify required terms exist in deliverables")
            b("\u2022 Data discovery \u2014 batch-find SSNs, emails, account numbers")
            b("\u2022 Due diligence \u2014 systematic contract or financial review")
            b("\u2022 Expressions and range filters are fully preserved in saved searches")
            blank()

            h("FILES CREATED BY DOCSEARCH")
            b("docsearch never modifies your original documents. It creates")
            b("its own files for reports, indexes, and settings. All are safe")
            b("to delete \u2014 docsearch recreates them as needed.")
            blank()
            s("Search reports (overwritten each search)")
            e("docsearch_results.txt       \u2014 text report")
            e("docsearch_results.docx      \u2014 Word report with highlights")
            e("docsearch_results.csv       \u2014 optional (-o csv)")
            e("docsearch_results.json      \u2014 optional (-o json)")
            blank()
            s("Saved/archived reports")
            e("DO_NOT_SEARCH_{name}.txt/docx          \u2014 saved with -s")
            e("DO_NOT_SEARCH_ACCUMULATED_{name}.*     \u2014 appended with -sa")
            blank()
            s("Suite files (auto-generated per run)")
            e("DO_NOT_SEARCH_SUITE_{suite}_stage*.*   \u2014 per-stage results")
            e("DO_NOT_SEARCH_docsearch_suite_*.*      \u2014 suite summary (.docx/.txt/.json)")
            e("DO_NOT_SEARCH_autorun_log.txt          \u2014 scheduled run history")
            blank()
            s("Error log")
            e("docsearch_errors.log        \u2014 files that couldn't be read + crash reports")
            blank()
            s("Index (optional)")
            e(".docsearch.db               \u2014 search index (SQLite)")
            e(".docsearch.db-wal/-shm      \u2014 temporary SQLite files")
            blank()
            s("Settings & data")
            e(".docsearch_collection.json  \u2014 saved searches & suites (per folder)")
            e("~/.docsearchrc              \u2014 user settings (home directory)")
            b("The 'rc' in .docsearchrc stands for 'run commands' \u2014 a Unix naming")
            b("convention meaning 'config file' (same as .bashrc, .vimrc, etc.).")
            blank()
            s("Key points")
            b("\u2022 All DO_NOT_SEARCH_ files are automatically excluded from searches")
            b("\u2022 All docsearch internal files (.db, .log, .json config) are excluded")
            b("\u2022 Most files are safe to delete \u2014 docsearch recreates them as needed")
            b("\u2022 EXCEPTION: .docsearch_collection.json contains your saved searches")
            b("  and suites. Do NOT delete it unless you want to lose that work.")
            b("\u2022 EXCEPTION: ~/.docsearchrc contains your settings and email config.")
            blank()
            s("If ~/.docsearchrc is deleted")
            b("Nothing breaks \u2014 docsearch uses built-in defaults. To recover:")
            b("1. Open Advanced Options, set your preferences, click Save Defaults")
            b("2. Re-enter email alerts via Configure Email Alerts in Search Suites")
            b("3. Change Text Size dropdown if needed (auto-saves immediately)")
            b("\u2022 Use Clean Up Suite Files, Clear Auto-Run History, Clear Error Log,")
            b("  or Delete Index to manage files from the GUI")
            blank()
            s("Building a search index")
            b("1. Browse to the folder you want to index")
            b("2. Click Index Options (below Search Suites)")
            b("3. Click Build Index(es)")
            b("4. Check Search Using Index(es) in Advanced Options")
            b("The index automatically includes all subfolders \u2014 one")
            b("index in your top folder covers everything underneath it.")
            b("You don't need to build separate indexes in each subfolder.")
            b("The index speeds up repeated searches on large folders.")
            b("\u2022 See the full file reference in the README for details on each file")

            txt.configure(state="disabled")

            # Close button
            close_btn = ctk.CTkButton(
                help_win, text="Close", width=100,
                command=help_win.destroy,
            )
            close_btn.pack(pady=(5, 10))

        def _show_advanced_help(self):
            """Show help for all Advanced Options with examples."""
            import tkinter as tk
            help_win = tk.Toplevel(self.advanced_window or self)
            help_win.title("Advanced Options — Help")
            help_win.geometry("750x520")
            help_win.resizable(True, True)
            if self.advanced_window:
                help_win.transient(self.advanced_window)

            text_frame = tk.Frame(help_win)
            text_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))
            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side="right", fill="y")
            txt = tk.Text(
                text_frame, wrap="word", font=("TkDefaultFont", 12),
                state="normal", yscrollcommand=scrollbar.set,
                padx=12, pady=10, spacing3=2,
            )
            txt.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=txt.yview)

            txt.tag_configure("heading", font=("TkDefaultFont", 13, "bold"), spacing1=12, spacing3=4)
            txt.tag_configure("subhead", font=("TkDefaultFont", 12, "bold"), spacing1=10, spacing3=2)
            txt.tag_configure("example", font=("Courier", 12), lmargin1=20, lmargin2=20)
            txt.tag_configure("body", font=("TkDefaultFont", 12), lmargin1=20, lmargin2=20)

            def h(text):
                txt.insert("end", text + "\n", "heading")
            def s(text):
                txt.insert("end", text + "\n", "subhead")
            def e(text):
                txt.insert("end", text + "\n", "example")
            def b(text):
                txt.insert("end", text + "\n", "body")
            def blank():
                txt.insert("end", "\n")

            h("SEARCH MODE CHECKBOXES")
            blank()

            s("AND Mode")
            b("All search terms must appear in the same line (paragraph).")
            b("Without AND mode, any single term matching is enough (OR mode).")
            e("budget revenue        \u2192  line must contain BOTH words")
            blank()

            s("Recursive")
            b("Search all subfolders, not just the selected folder.")
            b("Without this, only files directly in the search folder are checked.")
            blank()

            s("Fuzzy")
            b("Finds approximate/misspelled matches using similarity scoring.")
            b("Useful for OCR text (which often has recognition errors) and")
            b("documents with typos.")
            e("accomodation          \u2192  finds \"accommodation\"")
            e("recieve               \u2192  finds \"receive\"")
            e("comp1iance            \u2192  finds \"compliance\" (OCR error)")
            blank()

            s("Wildcard")
            b("Use * (any characters) and ? (exactly one character) for")
            b("simple pattern matching. Matches whole words only.")
            e("report*               \u2192  report, reports, reporting, ...")
            e("inv??ce               \u2192  invoice, inv01ce, ...")
            e("budg*                 \u2192  budget, budgets, budgeting, budgetary")
            blank()

            s("OCR")
            b("Extract text from scanned PDFs and image files (PNG, JPG, TIFF, BMP)")
            b("using optical character recognition. Requires Tesseract to be installed.")
            b("Slower than regular text search — use only when needed.")
            blank()

            s("Regex")
            b("Use regular expression patterns for precise matching.")
            e("\\d{3}-\\d{2}-\\d{4}     \u2192  SSN pattern (123-45-6789)")
            e("\\$[\\d,]+\\.\\d{2}       \u2192  dollar amounts ($1,234.56)")
            e("[A-Z]{2}-\\d{4,}       \u2192  ID codes (AB-12345)")
            e("\\d{2}/\\d{2}/\\d{4}     \u2192  dates (03/15/2026)")
            b("Tip: Use the Wizard button for pre-built regex patterns.")
            blank()

            s("Whole Word")
            b("Only matches complete words using word boundaries.")
            e("tax                   \u2192  matches \"tax\" but NOT \"taxi\" or \"taxation\"")
            e("bob                   \u2192  matches \"bob\" but NOT \"bobcat\" or \"bobby\"")
            e("log                   \u2192  matches \"log\" but NOT \"login\" or \"catalog\"")
            blank()

            s("Expression")
            b("Enable boolean expression search with AND, OR, NOT, and parentheses.")
            b("Type the expression in the Search Terms field.")
            e("budget AND revenue")
            e("(bob AND amy) OR fred")
            e("contract AND NOT draft")
            e("(salary OR bonus) AND NOT confidential")
            b("Range specs can be embedded: budget AND amount:1000..5000")
            blank()

            s("Inverse")
            b("Show files that do NOT contain the search terms.")
            b("Useful for compliance: \"which files are missing a required clause?\"")
            e("Terms: Authorized Signature    Inverse: ON")
            e("\u2192  lists files WITHOUT \"Authorized Signature\"")
            blank()

            h("TEXT FIELDS")
            blank()

            s("Exclude")
            b("Filter out lines that match these terms, even if they match your search.")
            b("Comma-separated for multiple exclude terms.")
            e("Search: budget    Exclude: draft,preliminary")
            e("\u2192  finds \"budget\" but skips lines also containing \"draft\" or \"preliminary\"")
            blank()

            s("File Types")
            b("Limit search to specific file extensions. Comma-separated, no dots.")
            e("pdf,docx              \u2192  only search PDFs and Word docs")
            e("eml,msg,pst           \u2192  only search email files")
            e("zip,7z                \u2192  only search inside archives")
            blank()

            s("Proximity")
            b("Find terms that appear within N words of each other.")
            b("Requires 2 or more search terms. AND mode is applied automatically.")
            e("Terms: breach contract    Proximity: 5")
            e("\u2192  both words must appear within 5 words of each other")
            blank()

            s("Context Before / After")
            b("Show N lines before and/or after each match for context.")
            e("Before: 2    After: 2")
            e("\u2192  shows 2 lines above and 2 lines below each match")
            blank()

            s("Cores")
            b("Number of CPU cores to use for parallel searching.")
            b("Default is half your available cores. Use 1 for minimal resource usage.")
            blank()

            s("Max Matches")
            b("Cap the number of matches written to report files. Default: 1000.")
            b("The total count is always accurate — only the report is capped.")
            b("Set to 0 for unlimited.")
            blank()

            s("Range")
            b("Filter by numeric values, dates, or file metadata within matched lines.")
            e("amount:1000..5000     \u2192  dollar amounts between 1000 and 5000")
            e("date:2024-01..2024-12 \u2192  dates in 2024")
            e("percent:5..15         \u2192  percentages between 5% and 15%")
            e("age:18..65            \u2192  ages between 18 and 65")
            e("fn:date:2024-01..12   \u2192  files with 2024 dates in the filename")
            e("filesize:..1M         \u2192  only files under 1 MB")
            b("Multiple ranges combine with AND logic. Open-ended ranges allowed")
            b("(e.g., amount:1000.. for \"at least 1000\").")
            blank()

            s("Specific Files")
            b("Search only these named files. Comma-separated.")
            e("report.pdf,notes.txt  \u2192  only search these two files")
            blank()

            s("Save As / Append To")
            b("Save As archives the current results with a name you choose.")
            b("Append To accumulates results from multiple searches into one file.")
            b("Both use a DO_NOT_SEARCH prefix so they are never re-searched.")
            blank()

            s("Output Directory")
            b("Write report files to a different folder instead of the search folder.")
            blank()

            s("Output Formats")
            b("Check CSV and/or JSON to generate additional report files.")
            b("Check Timestamp to add a timestamp to report filenames.")
            blank()

            s("Search Using Index(es)")
            b("Use the search index for faster repeated searches.")
            b("Build the index first using Index Options on the main screen.")
            blank()

            h("COMBINING MODES")
            b("You can mix multiple options for more powerful searches.")
            blank()
            s("Regex + AND + Recursive")
            b("Find files with both an SSN and a dollar amount in subfolders:")
            e("      Terms:  \\d{3}-\\d{2}-\\d{4}  \\$[\\d,]+\\.\\d{2}")
            e("Checkboxes:  Regex, AND mode, Recursive")
            blank()
            s("Wildcard + File Types")
            b("Find 'report' variations in PDFs only:")
            e("      Terms:  report*")
            e("Checkboxes:  Wildcard       File Types: pdf")
            blank()
            s("Expression + Range + Context")
            b("Budget or revenue (not draft) with amounts over 10,000:")
            e("Expression:  (budget OR revenue) AND NOT draft")
            e("Range:       amount:10000..999999")
            e("Context:     Before=2, After=2")
            blank()
            s("Whole Word + Proximity")
            b("'breach' and 'contract' as whole words within 5 words:")
            e("      Terms:  breach contract")
            e("Checkboxes:  Whole Word     Proximity: 5")
            blank()
            s("Fuzzy + Recursive + File Types")
            b("Find misspelled names across all Word docs in subfolders:")
            e("      Terms:  accommodation  occurrence")
            e("Checkboxes:  Fuzzy, Recursive   File Types: docx")
            blank()
            s("Inverse + Regex")
            b("Find files missing a required signature line:")
            e("      Terms:  Authorized\\s+Signature")
            e("Checkboxes:  Regex, Inverse")
            blank()

            h("SETTINGS BUTTONS")
            s("Inspect .docsearchrc")
            b("View the current saved settings file (read-only).")
            s("Save Defaults")
            b("Save all current Advanced Options as defaults to ~/.docsearchrc.")
            b("These are restored automatically when docsearch starts.")
            s("Restore Settings")
            b("Reload saved defaults from ~/.docsearchrc into the GUI.")
            s("Reset")
            b("Clear all fields and reset to defaults. Does not modify the config file.")

            txt.configure(state="disabled")

            close_btn = ctk.CTkButton(
                help_win, text="Close", width=100,
                command=help_win.destroy,
            )
            close_btn.pack(pady=(5, 10))

        def _build_folder_row(self):
            self.folder_bar_frame = ctk.CTkFrame(self)
            self.folder_bar_frame.grid(
                row=1, column=0, columnspan=3, padx=10, pady=2, sticky="ew"
            )
            self.folder_bar_frame.grid_columnconfigure(0, minsize=130)
            self.folder_bar_frame.grid_columnconfigure(1, weight=1)
            self.folder_bar_frame.grid_columnconfigure(2, minsize=170)

            ctk.CTkLabel(
                self.folder_bar_frame, text="Folder Bar",
                font=ctk.CTkFont(size=10), text_color=("gray50", "gray50"),
            ).grid(row=0, column=0, columnspan=3, padx=10, pady=(4, 0), sticky="w")

            label = ctk.CTkLabel(self.folder_bar_frame, text="Search Folder:", font=ctk.CTkFont(size=14))
            label.grid(row=1, column=0, padx=(15, 5), pady=(0, 8), sticky="e")

            self.folder_entry = ctk.CTkEntry(self.folder_bar_frame, font=ctk.CTkFont(size=14))
            self.folder_entry.grid(row=1, column=1, columnspan=2, padx=(5, 105), pady=(0, 8), sticky="ew")
            self.folder_entry.insert(0, os.path.expanduser("~"))

            self.browse_button = ctk.CTkButton(
                self.folder_bar_frame, text="Browse", width=90, command=self.browse_folder,
                font=ctk.CTkFont(size=14),
            )
            self.browse_button.grid(row=1, column=2, padx=(5, 10), pady=(0, 8), sticky="e")

            Tooltip(self.folder_entry, "The folder to search. Click Browse to choose a different folder")

        def _build_advanced_toggle(self):
            self.advanced_toggle = ctk.CTkButton(
                self._toggle_row,
                text="\u25b6 Advanced Options",
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                anchor="w",
                command=self.toggle_advanced,
                font=ctk.CTkFont(size=13),
            )
            self.advanced_toggle.pack(side="left")

        def _build_advanced_panel(self):
            # Create popup window for Advanced Options
            self.advanced_window = ctk.CTkToplevel(self)
            self.advanced_window.title("Advanced Options")
            self.advanced_window.geometry("720x520")
            self.advanced_window.resizable(True, True)
            self.advanced_window.protocol("WM_DELETE_WINDOW", self._close_advanced_window)
            # Withdraw after event loop starts to avoid flash
            self.advanced_window.withdraw()
            self.after(10, self.advanced_window.withdraw)

            self.advanced_frame = ctk.CTkFrame(self.advanced_window)
            self.advanced_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # ? help button in upper-right corner
            adv_header_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
            adv_header_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=(0, 0), sticky="ew")
            adv_header_frame.grid_columnconfigure(0, weight=1)
            adv_help_btn = ctk.CTkButton(
                adv_header_frame, text="?", width=28, height=28,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self._show_advanced_help,
            )
            adv_help_btn.grid(row=0, column=1, sticky="e")
            Tooltip(adv_help_btn, "Help — explains every Advanced Option with examples")

            # Build all widgets into advanced_frame

            # Rows 0-1: checkboxes in own frame so entry columns don't stretch them
            cb_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
            cb_frame.grid(row=1, column=0, columnspan=3, padx=15, pady=(10, 5), sticky="w")

            self.and_mode_var = ctk.StringVar(value="off")
            self.recursive_var = ctk.StringVar(value="off")
            self.fuzzy_var = ctk.StringVar(value="off")

            cb_and = ctk.CTkCheckBox(
                cb_frame, text="AND mode", variable=self.and_mode_var,
                onvalue="on", offvalue="off", command=self._on_and_toggle,
            )
            cb_and.grid(row=0, column=0, padx=(0, 15), pady=(0, 5), sticky="w")
            cb_rec = ctk.CTkCheckBox(
                cb_frame, text="Recursive", variable=self.recursive_var,
                onvalue="on", offvalue="off",
            )
            cb_rec.grid(row=0, column=1, padx=(0, 15), pady=(0, 5), sticky="w")
            cb_fuz = ctk.CTkCheckBox(
                cb_frame, text="Fuzzy", variable=self.fuzzy_var,
                onvalue="on", offvalue="off", command=self._on_fuzzy_toggle,
            )
            cb_fuz.grid(row=0, column=2, padx=(0, 15), pady=(0, 5), sticky="w")

            self.wildcard_var = ctk.StringVar(value="off")
            self.ocr_var = ctk.StringVar(value="off")
            self.regex_var = ctk.StringVar(value="off")

            cb_wild = ctk.CTkCheckBox(
                cb_frame, text="Wildcard", variable=self.wildcard_var,
                onvalue="on", offvalue="off", command=self._on_wildcard_toggle,
            )
            cb_wild.grid(row=1, column=0, padx=(0, 15), pady=0, sticky="w")
            cb_ocr = ctk.CTkCheckBox(
                cb_frame, text="OCR", variable=self.ocr_var,
                onvalue="on", offvalue="off",
            )
            cb_ocr.grid(row=1, column=1, padx=(0, 15), pady=0, sticky="w")
            cb_regex = ctk.CTkCheckBox(
                cb_frame, text="Regex", variable=self.regex_var,
                onvalue="on", offvalue="off", command=self._on_regex_toggle,
            )
            cb_regex.grid(row=1, column=2, padx=(0, 15), pady=0, sticky="w")

            self.whole_word_var = ctk.StringVar(value="off")
            cb_whole_word = ctk.CTkCheckBox(
                cb_frame, text="Whole Word", variable=self.whole_word_var,
                onvalue="on", offvalue="off",
            )
            cb_whole_word.grid(row=1, column=3, padx=(0, 15), pady=0, sticky="w")
            Tooltip(cb_whole_word, "Matches complete words only. 'bob' matches 'bob' but not 'bobcat'")

            self.expression_var = ctk.StringVar(value="off")
            cb_expr = ctk.CTkCheckBox(
                cb_frame, text="Expression", variable=self.expression_var,
                onvalue="on", offvalue="off", command=self._on_expression_toggle,
            )
            cb_expr.grid(row=0, column=3, padx=(0, 15), pady=(0, 5), sticky="w")

            self.inverse_var = ctk.StringVar(value="off")
            cb_inverse = ctk.CTkCheckBox(
                cb_frame, text="Inverse", variable=self.inverse_var,
                onvalue="on", offvalue="off",
            )
            cb_inverse.grid(row=0, column=4, padx=(0, 15), pady=(0, 5), sticky="w")
            Tooltip(cb_inverse, "Show files that do NOT contain the search terms — useful for finding missing content")

            # Row 1: exclude
            ctk.CTkLabel(self.advanced_frame, text="Exclude:").grid(
                row=7, column=0, padx=(15, 5), pady=5, sticky="e"
            )
            self.exclude_entry = ctk.CTkEntry(
                self.advanced_frame, placeholder_text="Ex: draft,obsolete"
            )
            self.exclude_entry.grid(row=3, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="ew")

            # Row 2: file types
            ctk.CTkLabel(self.advanced_frame, text="File types:").grid(
                row=2, column=0, padx=(15, 5), pady=5, sticky="e"
            )
            self.file_types_entry = ctk.CTkEntry(
                self.advanced_frame, placeholder_text="Ex: pdf,docx,txt"
            )
            self.file_types_entry.grid(row=2, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="ew")

            # Row 3: proximity + context lines
            ctk.CTkLabel(self.advanced_frame, text="Proximity:").grid(
                row=3, column=0, padx=(15, 5), pady=5, sticky="e"
            )
            num_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
            num_frame.grid(row=5, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="w")

            self.proximity_entry = ctk.CTkEntry(num_frame, width=60)
            self.proximity_entry.grid(row=0, column=0)

            num_frame.grid_columnconfigure(1, minsize=110)
            ctk.CTkLabel(num_frame, text="Lines Before:").grid(row=0, column=1, padx=(20, 5), sticky="e")
            self.context_before_entry = ctk.CTkEntry(num_frame, width=60)
            self.context_before_entry.grid(row=0, column=2)

            ctk.CTkLabel(num_frame, text="Lines After:").grid(row=0, column=3, padx=(20, 5))
            self.context_after_entry = ctk.CTkEntry(num_frame, width=60)
            self.context_after_entry.grid(row=0, column=4)

            # Row 4: cores
            self._default_cores = max(1, (os.cpu_count() or 1) // 2)
            ctk.CTkLabel(self.advanced_frame, text="Cores to Use:").grid(
                row=4, column=0, padx=(15, 5), pady=5, sticky="e"
            )
            cores_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
            cores_frame.grid(row=4, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="w")

            self.cores_entry = ctk.CTkEntry(cores_frame, width=60)
            self.cores_entry.insert(0, str(self._default_cores))
            self.cores_entry.grid(row=0, column=0)

            cores_frame.grid_columnconfigure(1, minsize=110)
            ctk.CTkLabel(cores_frame, text="Max Matches:").grid(row=0, column=1, padx=(20, 5), sticky="e")
            self.max_matches_entry = ctk.CTkEntry(cores_frame, width=60)
            self.max_matches_entry.insert(0, "1000")
            self.max_matches_entry.grid(row=0, column=2)

            # Row 5: range filters
            ctk.CTkLabel(self.advanced_frame, text="Range:").grid(
                row=5, column=0, padx=(15, 5), pady=5, sticky="e"
            )
            self.range_entry = ctk.CTkEntry(
                self.advanced_frame, placeholder_text="Ex: amount:1000..5000, date:2024-01-01..2024-12-31"
            )
            self.range_entry.grid(row=7, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="ew")
            Tooltip(self.range_entry, "Range filter: field:min..max (comma-separated for multiple). Fields: date, amount, number, percent, age, time, filesize, filedate. Use fn: prefix for filename ranges (e.g. fn:date:2024-01-01..2024-12-31). Open-ended ranges: amount:1000.. or amount:..5000")

            # Row 6: specific files
            ctk.CTkLabel(self.advanced_frame, text="Specific files:").grid(
                row=6, column=0, padx=(15, 5), pady=5, sticky="e"
            )
            self.specific_files_entry = ctk.CTkEntry(
                self.advanced_frame, placeholder_text="Ex: report.pdf,notes.txt"
            )
            self.specific_files_entry.grid(row=6, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="ew")

            # Row 7: save as + append to
            ctk.CTkLabel(self.advanced_frame, text="Save report as:").grid(
                row=8, column=0, padx=(15, 5), pady=(5, 10), sticky="e"
            )
            save_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
            save_frame.grid(row=8, column=1, columnspan=2, padx=(0, 15), pady=(5, 10), sticky="w")

            self.save_name_entry = ctk.CTkEntry(save_frame, width=140, placeholder_text="Ex: my_report")
            self.save_name_entry.grid(row=0, column=0, padx=(0, 20))

            ctk.CTkLabel(save_frame, text="Append report to:").grid(row=0, column=1, padx=(0, 5))
            self.append_name_entry = ctk.CTkEntry(save_frame, width=140, placeholder_text="Ex: combined_report")
            self.append_name_entry.grid(row=0, column=2)

            # Row 8: output directory
            ctk.CTkLabel(self.advanced_frame, text="Output Dir:").grid(
                row=9, column=0, padx=(15, 5), pady=(0, 5), sticky="e"
            )
            outdir_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
            outdir_frame.grid(row=9, column=1, columnspan=2, padx=(0, 15), pady=(0, 5), sticky="ew")

            self.output_dir_entry = ctk.CTkEntry(outdir_frame, width=300, placeholder_text="Leave empty to write to search folder")
            self.output_dir_entry.grid(row=0, column=0, padx=(0, 5), sticky="ew")
            outdir_frame.grid_columnconfigure(0, weight=1)

            outdir_browse_btn = ctk.CTkButton(
                outdir_frame, text="Browse", width=70,
                command=self._browse_output_dir,
                font=ctk.CTkFont(size=12),
            )
            outdir_browse_btn.grid(row=0, column=1, padx=(0, 0))
            Tooltip(self.output_dir_entry, "Directory for search output files (reports, error log, CSV, JSON). Leave empty to write to the search folder. This is independent from the Output Dir on the Search Suites panel — each can point to a different location")

            # Row 9: additional output formats
            output_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
            output_frame.grid(row=10, column=0, columnspan=3, padx=15, pady=(0, 10), sticky="w")

            ctk.CTkLabel(output_frame, text="Also output report as ==>").grid(row=0, column=0, padx=(0, 10))
            self.output_csv_var = ctk.StringVar(value="off")
            self.output_json_var = ctk.StringVar(value="off")
            cb_csv = ctk.CTkCheckBox(
                output_frame, text="CSV", variable=self.output_csv_var,
                onvalue="on", offvalue="off",
            )
            cb_csv.grid(row=0, column=1, padx=(0, 15))
            cb_json = ctk.CTkCheckBox(
                output_frame, text="JSON", variable=self.output_json_var,
                onvalue="on", offvalue="off",
            )
            cb_json.grid(row=0, column=2)
            self.timestamp_var = ctk.StringVar(value="on")
            cb_ts = ctk.CTkCheckBox(
                output_frame, text="Timestamp Filename", variable=self.timestamp_var,
                onvalue="on", offvalue="off",
            )
            cb_ts.grid(row=0, column=3, padx=(15, 0))
            Tooltip(cb_ts, "Add timestamp to report filenames (e.g., docsearch_results_20260327_143022.txt)")

            # Row 10: Save Defaults + Restore Settings buttons
            settings_btn_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
            settings_btn_frame.grid(row=11, column=0, columnspan=3, padx=(0, 15), pady=(0, 10), sticky="e")

            inspect_settings_btn = ctk.CTkButton(
                settings_btn_frame, text="Inspect .docsearchrc", width=155,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self._inspect_settings,
                font=ctk.CTkFont(size=12),
            )
            inspect_settings_btn.pack(side="left", padx=5)
            Tooltip(inspect_settings_btn, "View the current saved settings in ~/.docsearchrc (read-only)")

            save_settings_btn = ctk.CTkButton(
                settings_btn_frame, text="Save Defaults", width=120,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self._save_current_settings,
                font=ctk.CTkFont(size=12),
            )
            save_settings_btn.pack(side="left", padx=5)
            Tooltip(save_settings_btn, "Save the current Advanced Options as defaults in ~/.docsearchrc")

            restore_settings_btn = ctk.CTkButton(
                settings_btn_frame, text="Restore Settings", width=130,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self._load_saved_settings,
                font=ctk.CTkFont(size=12),
            )
            restore_settings_btn.pack(side="left", padx=5)
            Tooltip(restore_settings_btn, "Load saved defaults from ~/.docsearchrc into the GUI")

            reset_btn = ctk.CTkButton(
                settings_btn_frame, text="Reset", width=90,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self.reset_form,
                font=ctk.CTkFont(size=12),
            )
            reset_btn.pack(side="left", padx=5)
            Tooltip(reset_btn, "Clear all fields and reset the GUI to its default state. This does not change the config file — only Save Defaults writes to it")


            # Row 11: Search Using Index(es)
            self.index_search_var = ctk.StringVar(value="off")
            self.cb_index_search = ctk.CTkCheckBox(
                self.advanced_frame, text="Search Using Index(es)", variable=self.index_search_var,
                onvalue="on", offvalue="off", font=ctk.CTkFont(size=12),
            )
            self.cb_index_search.grid(row=12, column=0, columnspan=2, padx=15, pady=(5, 10), sticky="w")
            Tooltip(self.cb_index_search, "Use the search index for faster searches. Uncheck to search files directly — useful for verifying that both methods find identical results. Disabled when no index exists")

            self.advanced_frame.grid_columnconfigure(0, minsize=130)
            self.advanced_frame.grid_columnconfigure(1, weight=1)

            # Tooltips
            Tooltip(cb_and, "All search terms must appear in the same paragraph")
            Tooltip(cb_rec, "Search subfolders inside the Search Folder")
            Tooltip(cb_fuz, "Find approximate matches for typos, misspellings, and for scans (e.g., 'budgt' matches 'budget').\nFuzzy and Regex are mutually exclusive.")
            Tooltip(cb_wild, "Use * for any characters and ? for one character (e.g., budg* matches budget, budgets)")
            Tooltip(cb_ocr, "Extract text from scanned PDFs and image files (bmp, jpg, jpeg, png, tif, tiff). Requires Tesseract to be installed (see Readme.md)")
            Tooltip(cb_expr, (
                "Boolean Expression Search — use AND, OR, NOT, and parentheses for complex queries.\n"
                "\n"
                "Examples:\n"
                "  budget AND revenue\n"
                "  budget OR revenue\n"
                "  budget AND NOT draft\n"
                "  (budget OR revenue) AND (cost OR profit)\n"
                "  (bob AND amy) OR (fred AND wilma)\n"
                '  "annual report" AND (2023 OR 2024)\n'
                "\n"
                "Operators: AND, OR, NOT (case-insensitive). Parentheses group expressions.\n"
                "Precedence: NOT > AND > OR. Use parentheses to override.\n"
                "Cannot combine with AND mode, Exclude, or Proximity."
            ))
            Tooltip(cb_regex, "Use regular expressions for advanced pattern matching (e.g., \\d{3}-\\d{4} for phone numbers).\nFuzzy and Regex are mutually exclusive.")
            Tooltip(self.exclude_entry, "Comma-separated terms to skip (e.g., draft,obsolete)")
            Tooltip(self.file_types_entry, "Comma-separated file extensions to search — no limit to the number of types. Supported types: 7z, bz2, cfg, csv, doc, docx, eml, epub, gz, html, ini, json, log, md, msg, odp, ods, odt, pdf, ppt, pptx, pst, rar, rst, rtf, sql, tar, tex, tgz, toml, tsv, txt, xls, xlsx, xml, yaml, yml, zip. With OCR enabled: bmp, jpg, jpeg, png, tif, tiff")
            Tooltip(self.proximity_entry, "Find terms within this many words of each other")
            Tooltip(self.context_before_entry, "Number of lines to show before each match")
            Tooltip(self.context_after_entry, "Number of lines to show after each match")
            Tooltip(self.cores_entry, f"Number of CPU cores to use. This machine has {os.cpu_count()}, default is {self._default_cores}")
            Tooltip(self.max_matches_entry, "Maximum matches included in reports. Default 1000. Set to 0 for no limit.")
            Tooltip(self.specific_files_entry, "Comma-separated filenames to search — no limit to the number of files (e.g., report.pdf,notes.txt)")
            Tooltip(self.save_name_entry, "Save the report with a custom name after search completes. DO_NOT_SEARCH_ will be added to the front of your file name")
            Tooltip(self.append_name_entry, "Append results to a named report file (creates or extends it). DO_NOT_SEARCH_ will be added to the front of your file name")
            Tooltip(cb_csv, "Also save results as a CSV file (docsearch_results.csv) — open in Excel or Google Sheets to sort, filter, and analyze")
            Tooltip(cb_json, "Also save results as a JSON file (docsearch_results.json) — machine-readable format for automation and integration")

        def _build_progress_area(self):
            self.progress_bar = ctk.CTkProgressBar(self, mode="determinate")
            self.progress_bar.set(0)
            # Starts hidden — shown only during search

            ctk.CTkLabel(
                self.search_bar_frame, text="Status:", font=ctk.CTkFont(size=13),
            ).grid(row=3, column=0, padx=(10, 5), pady=(0, 4), sticky="w")
            self.status_label = ctk.CTkLabel(
                self.search_bar_frame, text="", font=ctk.CTkFont(size=13), anchor="w"
            )
            self.status_label.grid(
                row=3, column=1, columnspan=2, padx=(0, 15), pady=(0, 4), sticky="ew"
            )

            self.matched_files = []
            self._inverse_results = False

            # Results preview pane — hidden until search completes
            self.preview_frame = ctk.CTkFrame(self)
            # Don't grid yet — shown by _show_preview after search

            import tkinter as tk
            preview_header = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
            preview_header.pack(fill="x", padx=5, pady=(5, 0))
            ctk.CTkLabel(preview_header, text="Results Preview:",
                         font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            self._preview_count_label = ctk.CTkLabel(
                preview_header, text="", font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray50"))
            self._preview_count_label.pack(side="left", padx=(8, 0))

            preview_text_frame = tk.Frame(self.preview_frame)
            preview_text_frame.pack(fill="both", expand=True, padx=5, pady=(2, 5))

            preview_scroll = tk.Scrollbar(preview_text_frame)
            preview_scroll.pack(side="right", fill="y")

            self.preview_text = tk.Text(
                preview_text_frame, wrap="word", font=("Courier", 11),
                state="disabled", yscrollcommand=preview_scroll.set,
                padx=8, pady=5, height=10,
            )
            self.preview_text.pack(side="left", fill="both", expand=True)
            preview_scroll.config(command=self.preview_text.yview)

            # Configure tags for highlighting
            self.preview_text.tag_configure("filename", font=("Courier", 11, "bold"),
                                            foreground="#1a73e8")
            self.preview_text.tag_configure("match", background="#FFFF00")
            self.preview_text.tag_configure("line_num", foreground="#888888")

        def _build_open_report(self):
            # Buttons are children of the main window, gridded directly at row 6
            self.matched_files_button = ctk.CTkButton(
                self,
                text="Matched Files",
                width=140,
                command=self._show_matched_files_popup,
                font=ctk.CTkFont(size=13),
            )
            Tooltip(self.matched_files_button, "View the list of files that contained matches (click a file to open it)")

            self.report_frame = ctk.CTkFrame(self, fg_color=self.cget("fg_color"))
            report_lbl = ctk.CTkLabel(
                self.report_frame, text="View Report:", font=ctk.CTkFont(size=13),
            )
            report_lbl.pack(side="left", padx=(0, 4))

            btn_font = ctk.CTkFont(size=12)
            btn_w = 60
            self.report_btn_txt = ctk.CTkButton(
                self.report_frame, text="TXT", width=btn_w, font=btn_font,
                command=lambda: self._open_report_format("txt"),
            )
            self.report_btn_docx = ctk.CTkButton(
                self.report_frame, text="DOCX", width=btn_w, font=btn_font,
                command=lambda: self._open_report_format("docx"),
            )
            self.report_btn_csv = ctk.CTkButton(
                self.report_frame, text="CSV", width=btn_w, font=btn_font,
                command=lambda: self._open_report_format("csv"),
            )
            self.report_btn_json = ctk.CTkButton(
                self.report_frame, text="JSON", width=btn_w, font=btn_font,
                command=lambda: self._open_report_format("json"),
            )

        def _build_index_panel(self):
            # Index toggle button — in the shared toggle row
            self.index_toggle_btn = ctk.CTkButton(
                self._toggle_row,
                text="\u25b6 Index Options",
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                anchor="w",
                command=self._toggle_index_options,
                font=ctk.CTkFont(size=13),
            )
            self.index_toggle_btn.pack(side="left", padx=(10, 0))

            # Index contents frame — collapsible, on its own row
            self.index_frame = ctk.CTkFrame(self, fg_color="transparent")
            # Don't grid yet — shown when toggled

            self.index_contents = ctk.CTkFrame(self.index_frame)
            self.index_visible = False

            # Row 0 inside contents: Auto-Refresh + Build/Delete buttons
            idx_row0 = ctk.CTkFrame(self.index_contents, fg_color="transparent")
            idx_row0.grid(row=0, column=0, columnspan=3, padx=0, pady=(5, 5), sticky="ew")

            ctk.CTkLabel(
                idx_row0, text="Auto-Refresh Index:",
                font=ctk.CTkFont(size=12),
            ).grid(row=0, column=0, padx=(0, 2), pady=0, sticky="w")

            self.refresh_interval_var = ctk.StringVar(value="Off")
            self.refresh_interval_menu = ctk.CTkOptionMenu(
                idx_row0,
                values=["Off", "5 min", "15 min", "30 min", "1 hour"],
                variable=self.refresh_interval_var,
                command=self._on_refresh_interval_changed,
                width=100,
                font=ctk.CTkFont(size=12),
            )
            self.refresh_interval_menu.grid(row=0, column=1, padx=(2, 10), pady=0, sticky="w")
            Tooltip(self.refresh_interval_menu,
                    "Automatically refresh the index at this interval while the app is open. "
                    "Adds new files, re-indexes changed files, removes deleted files.")

            self.build_index_button = ctk.CTkButton(
                idx_row0, text="Build Index(es)", width=120,
                command=self.build_index_action, font=ctk.CTkFont(size=12),
            )
            self.build_index_button.grid(row=0, column=2, padx=5, pady=0, sticky="e")
            Tooltip(self.build_index_button, "Build a search index for faster repeated searches. Indexes all subfolders automatically. Warning: Navigate to the right folder (Browse button) before Building Index(es)")

            self.delete_index_button = ctk.CTkButton(
                idx_row0, text="Delete Index(es)", width=120,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self.delete_index_action, font=ctk.CTkFont(size=12),
            )
            self.delete_index_button.grid(row=0, column=3, padx=5, pady=0, sticky="e")
            Tooltip(self.delete_index_button, "Delete the search index from the selected folder")

            self.index_status_button = ctk.CTkButton(
                idx_row0, text="Index Status", width=100,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self.index_status_action, font=ctk.CTkFont(size=12),
            )
            self.index_status_button.grid(row=0, column=4, padx=5, pady=0, sticky="e")
            Tooltip(self.index_status_button, "Show index info — file count, size, and settings")

            self.about_index_button = ctk.CTkButton(
                idx_row0, text="About Index", width=100,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self.about_index_action, font=ctk.CTkFont(size=12),
            )
            self.about_index_button.grid(row=0, column=5, padx=5, pady=0, sticky="e")
            Tooltip(self.about_index_button, "Overview of how indexes work in docsearch")

            # Row 1: Index last updated
            self.refresh_status_label = ctk.CTkLabel(
                self.index_contents, text="", font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray50"), anchor="w",
            )
            self.refresh_status_label.grid(row=1, column=0, columnspan=3, padx=0, pady=(0, 5), sticky="w")

        def _build_suite_panel(self):
            """Build the Search Suites window (standalone, shown/hidden)."""
            import tkinter as tk
            from tkinter import ttk

            self.suite_window = ctk.CTkToplevel(self)
            self.suite_window.title("Search Suites")
            self.suite_window.geometry("650x580")
            self.suite_window.protocol("WM_DELETE_WINDOW", self._on_suite_window_close)

            self.suite_frame = ctk.CTkFrame(self.suite_window)
            self.suite_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Header with Help button
            header_frame = ctk.CTkFrame(self.suite_frame, fg_color="transparent")
            header_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=(5, 0), sticky="ew")
            help_btn = ctk.CTkButton(
                header_frame, text="?", width=28, height=28,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self._show_suite_help,
            )
            help_btn.pack(side="right")
            Tooltip(help_btn, "How Search Suites work")

            # Suites
            right = ctk.CTkFrame(self.suite_frame, fg_color="transparent")
            right.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
            self.suite_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(right, text="Suites", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
            suite_selector_frame = tk.Frame(right)
            suite_selector_frame.pack(fill="x", pady=(2, 5))
            self.suite_selector = tk.Listbox(suite_selector_frame, height=4, selectmode="extended", font=("TkDefaultFont", 11))
            suite_sel_scroll = tk.Scrollbar(suite_selector_frame, command=self.suite_selector.yview)
            self.suite_selector.configure(yscrollcommand=suite_sel_scroll.set)
            self.suite_selector.pack(side="left", fill="both", expand=True)
            suite_sel_scroll.pack(side="right", fill="y")
            self.suite_selector.bind("<<ListboxSelect>>", lambda e: self._on_suite_selected())

            ctk.CTkLabel(right, text="These searches are in the selected suite", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
            suite_contents_frame = tk.Frame(right)
            suite_contents_frame.pack(fill="both", expand=True, pady=(0, 5))
            self.suite_contents_listbox = tk.Listbox(suite_contents_frame, height=8, width=25, font=("TkDefaultFont", 11))
            suite_contents_scroll = tk.Scrollbar(suite_contents_frame, command=self.suite_contents_listbox.yview)
            self.suite_contents_listbox.configure(yscrollcommand=suite_contents_scroll.set)
            self.suite_contents_listbox.pack(side="left", fill="both", expand=True)
            suite_contents_scroll.pack(side="right", fill="y")

            suite_btn_frame = ctk.CTkFrame(right, fg_color="transparent")
            suite_btn_frame.pack(fill="x")
            ctk.CTkButton(
                suite_btn_frame, text="Build a New Suite", width=130, font=ctk.CTkFont(size=12),
                command=self._create_suite_dialog,
            ).pack(side="left", padx=(0, 5))
            ctk.CTkButton(
                suite_btn_frame, text="Edit Suite", width=90, font=ctk.CTkFont(size=12),
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self._edit_suite_dialog,
            ).pack(side="left", padx=(0, 5))
            ctk.CTkButton(
                suite_btn_frame, text="Delete Suite", width=90, font=ctk.CTkFont(size=12),
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self._delete_suite,
            ).pack(side="left", padx=(0, 5))
            self.cleanup_suite_btn = ctk.CTkButton(
                suite_btn_frame, text="Clean Up Suite Files", width=160, font=ctk.CTkFont(size=12),
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self._cleanup_suite_files,
            )
            self.cleanup_suite_btn.pack(side="left")
            Tooltip(self.cleanup_suite_btn, "Delete all generated suite and stage report files from the search folder")

            # Status label (under Suites column)
            status_frame = ctk.CTkFrame(self.suite_frame, fg_color="transparent")
            status_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=(5, 0), sticky="ew")
            ctk.CTkLabel(status_frame, text="Messages:", font=ctk.CTkFont(size=12)).pack(side="left")
            self.suite_status_label = ctk.CTkLabel(status_frame, text="", font=ctk.CTkFont(size=12))
            self.suite_status_label.pack(side="left", padx=(5, 10))
            self.cancel_suite_btn = ctk.CTkButton(
                status_frame, text="Cancel", width=80, font=ctk.CTkFont(size=13),
                fg_color="red", hover_color="darkred",
                command=self._cancel_suite,
            )
            # Cancel hidden by default

            # Schedule + Last Run row
            schedule_frame = ctk.CTkFrame(self.suite_frame, fg_color="transparent")
            schedule_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=(5, 0), sticky="ew")

            ctk.CTkLabel(schedule_frame, text="Auto-Run every:", font=ctk.CTkFont(size=12)).grid(row=0, column=0, padx=(0, 5))
            self.suite_schedule_var = ctk.StringVar(value="Off")
            self.suite_schedule_menu = ctk.CTkOptionMenu(
                schedule_frame, variable=self.suite_schedule_var,
                values=["Off", "30 min", "1 hour", "4 hours", "12 hours", "24 hours"],
                width=100, font=ctk.CTkFont(size=12),
                command=self._on_suite_schedule_changed,
            )
            self.suite_schedule_menu.grid(row=0, column=1, padx=(0, 15))

            ctk.CTkLabel(schedule_frame, text="Last run:", font=ctk.CTkFont(size=12)).grid(row=0, column=2, padx=(0, 5))
            self.suite_last_run_label = ctk.CTkLabel(
                schedule_frame, text="Never", font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray50"),
            )
            self.suite_last_run_label.grid(row=0, column=3, padx=(0, 15))

            ctk.CTkLabel(schedule_frame, text="Next Auto-Run:", font=ctk.CTkFont(size=12)).grid(row=0, column=4, padx=(0, 5))
            self.suite_next_run_label = ctk.CTkLabel(
                schedule_frame, text="—", font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray50"),
            )
            self.suite_next_run_label.grid(row=0, column=5, padx=(0, 5))

            ctk.CTkLabel(schedule_frame, text="Auto-Run Suite:", font=ctk.CTkFont(size=12)).grid(row=1, column=0, padx=(0, 5), pady=(5, 0))
            autorun_name = self._scheduled_suite_name or "None"
            self.suite_autorun_name_label = ctk.CTkLabel(
                schedule_frame, text=autorun_name, font=ctk.CTkFont(size=12, weight="bold"),
                text_color=("gray50", "gray50"),
            )
            self.suite_autorun_name_label.grid(row=1, column=1, columnspan=5, padx=(0, 5), pady=(5, 0), sticky="w")

            # Output Dir row for suites
            suite_outdir_frame = ctk.CTkFrame(self.suite_frame, fg_color="transparent")
            suite_outdir_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=(15, 0), sticky="ew")

            ctk.CTkLabel(suite_outdir_frame, text="Output Dir:", font=ctk.CTkFont(size=12)).grid(row=0, column=0, padx=(0, 5))
            self.suite_output_dir_entry = ctk.CTkEntry(suite_outdir_frame, width=300, placeholder_text="Leave empty to write to search folder")
            self.suite_output_dir_entry.grid(row=0, column=1, padx=(0, 5), sticky="ew")
            saved_sod = getattr(self, '_saved_suite_output_dir', '')
            if saved_sod:
                self.suite_output_dir_entry.insert(0, saved_sod)
            suite_outdir_frame.grid_columnconfigure(1, weight=1)

            suite_outdir_browse_btn = ctk.CTkButton(
                suite_outdir_frame, text="Browse", width=70,
                command=self._browse_suite_output_dir,
                font=ctk.CTkFont(size=12),
            )
            suite_outdir_browse_btn.grid(row=0, column=2)
            Tooltip(self.suite_output_dir_entry, "Directory for suite output files (stage reports, suite reports). Leave empty to write to the search folder. This is independent from the Output Dir in Advanced Options — each can point to a different location")

            # Auto-Run History + Email Alerts links row
            links_frame = ctk.CTkFrame(self.suite_frame, fg_color="transparent")
            links_frame.grid(row=7, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="ew")

            autorun_label = ctk.CTkLabel(
                links_frame, text="Open Auto-Run History",
                font=ctk.CTkFont(size=12, underline=True),
                text_color=("dodgerblue", "deepskyblue"), cursor="hand2",
            )
            autorun_label.pack(side="left")
            autorun_label.bind("<Button-1>", lambda e: self._open_autorun_history())
            Tooltip(autorun_label, "Open the auto-run log file (DO_NOT_SEARCH_autorun_log.txt)")

            sep_label = ctk.CTkLabel(links_frame, text="  |  ", font=ctk.CTkFont(size=12),
                                     text_color=("gray60", "gray40"))
            sep_label.pack(side="left")

            clear_autorun_label = ctk.CTkLabel(
                links_frame, text="Clear Auto-Run History",
                font=ctk.CTkFont(size=12, underline=True),
                text_color=("dodgerblue", "deepskyblue"), cursor="hand2",
            )
            clear_autorun_label.pack(side="left")
            clear_autorun_label.bind("<Button-1>", lambda e: self._clear_autorun_history())
            Tooltip(clear_autorun_label, "Delete the auto-run log file (DO_NOT_SEARCH_autorun_log.txt)")

            email_alert_label = ctk.CTkLabel(
                links_frame, text="Configure Email Alerts",
                font=ctk.CTkFont(size=12, underline=True),
                text_color=("dodgerblue", "deepskyblue"), cursor="hand2",
            )
            email_alert_label.pack(side="right")
            email_alert_label.bind("<Button-1>", lambda e: self._configure_email_alerts())
            Tooltip(email_alert_label, "Configure email notifications for suite auto-run results")

            # View Suite Report button (hidden until a suite run completes)
            self.view_suite_report_btn = ctk.CTkButton(
                self.suite_frame, text="View Suite Report", width=160, font=ctk.CTkFont(size=13),
                command=self._open_suite_report,
            )
            self._suite_report_path = None
            Tooltip(self.view_suite_report_btn, "Open the .docx suite report from the last run")

            # Run Selected Suite button (centered)
            self.run_suite_btn = ctk.CTkButton(
                self.suite_frame, text="Run Selected Suite", width=160, font=ctk.CTkFont(size=14, weight="bold"),
                command=self._run_suite,
            )
            self.run_suite_btn.grid(row=8, column=0, columnspan=2, pady=(10, 10))

        def _open_autorun_history(self):
            """Open the auto-run log file in the default text editor."""
            import subprocess, sys
            folder = self.folder_entry.get().strip()
            report_dir = getattr(self, '_saved_suite_output_dir', '') or folder
            if not report_dir or not os.path.isdir(report_dir):
                self._show_error("Select a valid folder first.")
                return
            log_path = os.path.join(report_dir, "DO_NOT_SEARCH_autorun_log.txt")
            if not os.path.exists(log_path):
                self._show_error("No auto-run history found yet.")
                return
            if sys.platform == "darwin":
                subprocess.Popen(["open", log_path])
            elif sys.platform == "win32":
                os.startfile(log_path)
            else:
                subprocess.Popen(["xdg-open", log_path])

        def _clear_autorun_history(self):
            """Delete the auto-run log file after confirmation."""
            folder = self.folder_entry.get().strip()
            report_dir = getattr(self, '_saved_suite_output_dir', '') or folder
            if not report_dir or not os.path.isdir(report_dir):
                self._show_error("Select a valid folder first.")
                return
            log_path = os.path.join(report_dir, "DO_NOT_SEARCH_autorun_log.txt")
            if not os.path.exists(log_path):
                self.suite_status_label.configure(text="No auto-run history to clear.")
                return
            from tkinter import messagebox
            if messagebox.askyesno("Clear Auto-Run History",
                                   f"Delete {os.path.basename(log_path)}?\n\nThis cannot be undone."):
                try:
                    os.remove(log_path)
                    self.suite_status_label.configure(text="Auto-run history cleared.")
                except OSError as e:
                    self._show_error(f"Could not delete log file: {e}")

        def _cleanup_suite_files(self):
            """Delete all generated suite and stage report files from the search/output folder."""
            import glob
            from tkinter import messagebox

            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Select a valid folder first.")
                return

            # Scan both search folder and output dir (if different)
            try:
                od = self.suite_output_dir_entry.get().strip() if self._suite_window_open() and hasattr(self, 'suite_output_dir_entry') else ""
            except Exception:
                od = getattr(self, '_saved_suite_output_dir', '')
            dirs_to_scan = [folder]
            if od and od != folder and os.path.isdir(od):
                dirs_to_scan.append(od)

            # Find suite-generated files only (not user-saved -s/-sa reports)
            files = []
            for d in dirs_to_scan:
                patterns = [
                    os.path.join(d, "DO_NOT_SEARCH_SUITE_*"),
                    os.path.join(d, "DO_NOT_SEARCH_docsearch_suite_*"),
                ]
                for pat in patterns:
                    files.extend(glob.glob(pat))
            files = sorted(set(files))

            if not files:
                self.suite_status_label.configure(text="No suite files found to clean up.")
                return

            names = "\n".join(os.path.basename(f) for f in files[:20])
            if len(files) > 20:
                names += f"\n... and {len(files) - 20} more"
            if not messagebox.askyesno(
                "Clean Up Suite Files",
                f"Delete {len(files)} suite file(s) from:\n{folder}\n\n{names}",
            ):
                return

            for f in files:
                try:
                    os.remove(f)
                except OSError:
                    pass
            self.suite_status_label.configure(text=f"Deleted {len(files)} suite file(s).")

        def _show_suite_help(self):
            """Show an informational popup explaining how Search Suites work."""
            import tkinter as tk
            help_win = tk.Toplevel(self.suite_window)
            help_win.title("Search Suites — How They Work")
            help_win.geometry("750x520")
            help_win.resizable(True, True)
            help_win.transient(self.suite_window)
            help_win.grab_set()

            # Scrollable text widget
            text_frame = tk.Frame(help_win)
            text_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))

            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side="right", fill="y")

            txt = tk.Text(
                text_frame, wrap="word", font=("TkDefaultFont", 12),
                state="normal", yscrollcommand=scrollbar.set,
                padx=12, pady=10, spacing3=2,
            )
            txt.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=txt.yview)

            # Configure tags
            txt.tag_configure("heading", font=("TkDefaultFont", 13, "bold"), spacing1=12, spacing3=4)
            txt.tag_configure("subhead", font=("TkDefaultFont", 12, "bold"), spacing1=10, spacing3=2)
            txt.tag_configure("example", font=("Courier", 12), lmargin1=20, lmargin2=20)
            txt.tag_configure("body", font=("TkDefaultFont", 12), lmargin1=20, lmargin2=20)

            def h(text):
                txt.insert("end", text + "\n", "heading")

            def s(text):
                txt.insert("end", text + "\n", "subhead")

            def e(text):
                txt.insert("end", text + "\n", "example")

            def b(text):
                txt.insert("end", text + "\n", "body")

            def blank():
                txt.insert("end", "\n")

            b("Search Suites let you save individual searches, group them into")
            b("named suites, and run them as a batch with pass/fail tracking.")
            blank()

            h("HOW TO USE")
            b("1. Save a search: configure in the main GUI, click Save Search, give it a name.")
            b("2. Build a suite: click Build a New Suite, name it, add searches and set execution order.")
            b("3. Run: select a suite, click Run Selected Suite.")
            b("4. Reports are generated automatically with timestamps.")
            blank()

            h("CASCADE MODE")
            b("Check 'Cascade mode' to enable progressive narrowing \u2014 each stage's")
            b("matched files become the file list for the next stage. Use the order")
            b("controls (\u25b2/\u25bc) to set the pipeline sequence.")
            blank()

            h("SEARCH ORDER")
            b("When creating or editing a suite, use the dual-panel selector to pick")
            b("and reorder searches. \u2192/\u2190 move searches between panels; \u25b2/\u25bc set")
            b("execution order. Order matters for cascade mode.")
            blank()

            h("PASS CRITERIA")
            b("Each search in a suite can have its own pass/fail criteria:")
            e(">= N   pass if match count is at least N (default: >= 1)")
            e("<= N   pass if match count is at most N")
            e("== N   pass if match count is exactly N (e.g., == 0 for 'no matches')")
            b("Set criteria when creating or editing a suite. Searches without")
            b("explicit criteria default to >= 1 (at least one match to pass).")
            blank()

            h("WHAT IT'S GOOD FOR")
            b("\u2022 Compliance audits: repeat checks on document sets")
            b("\u2022 Quality assurance: verify required terms exist")
            b("\u2022 Data discovery: batch-find SSNs, emails, etc.")
            b("\u2022 Due diligence: systematic contract review")
            blank()

            h("COMPLIANCE AUDIT PATTERNS")
            b("Combine search modes with pass criteria to build document-level")
            b("compliance checks that flag exactly which files pass or fail:")
            blank()
            s("Every file must contain a term")
            b("Search for the term with Inverse on. Set criteria to == 0.")
            b("Passes if all files have it. If it fails, the stage report")
            b("lists every file missing the term.")
            blank()
            s("No file should contain a term")
            b("Search for the term normally. Set criteria to == 0.")
            b("Passes if no file contains it. If it fails, the stage report")
            b("lists every file that still has it.")
            blank()
            s("Required clause with complex wording")
            b("Use an Expression like (signature AND date) AND NOT draft")
            b("with Inverse on. Set criteria to == 0.")
            b("Flags files missing the required combination.")
            blank()
            s("Limit violations")
            b("Search for 'TBD' or 'TODO' normally. Set criteria to <= 3.")
            b("Passes if 3 or fewer matches remain across all files.")
            blank()
            s("Sensitive data detection")
            b("Search for SSN/PII patterns with Regex on. Set criteria to == 0.")
            b("Flags every file containing sensitive data.")
            blank()

            h("FILES GENERATED")
            b("All report filenames are automatically timestamped.")
            b("\u2022 Stage reports: \u2026_stage{NN}_{search}_{timestamp}.txt/.docx")
            b("  Each search gets its own report file.")
            b("\u2022 Suite report: \u2026_suite_{name}_{timestamp}.docx/.txt/.json")
            b("  Consolidated pass/fail summary with color-coded results.")
            b("\u2022 Collection: .docsearch_collection.json")
            b("  Saves searches & suite definitions per folder.")
            b("\u2022 Auto-run log: DO_NOT_SEARCH_autorun_log.txt")
            b("  Persistent history of all scheduled runs.")
            blank()

            h("HOW THE COLLECTION FILE WORKS")
            b("When you save a search or build a suite, docsearch stores")
            b("everything in .docsearch_collection.json inside the search folder.")
            blank()
            b("\u2022 Created automatically when you first save a search")
            b("\u2022 One per folder \u2014 each folder has its own collection")
            b("\u2022 Lives with your documents \u2014 copy/move a folder and")
            b("  the suites travel with it")
            b("\u2022 Contains all saved searches (names + settings) and all")
            b("  suites (names + ordered search lists + pass criteria)")
            b("\u2022 Updated instantly by the GUI when you save, edit, or delete")
            b("\u2022 Loaded automatically when you browse to a folder")
            b("\u2022 Do NOT delete \u2014 it contains all your suite work")
            b("\u2022 Back it up \u2014 it's a JSON text file you can copy anywhere")
            b("\u2022 You never need to edit it directly \u2014 the GUI manages it")
            blank()

            h("OUTPUT DIRECTORY")
            b("Set Output Dir to write suite files to a separate folder.")
            b("Independent from the Output Dir in Advanced Options.")
            b("All files use DO_NOT_SEARCH prefix to auto-exclude from future searches.")
            b("This setting is automatically saved to ~/.docsearchrc when you close")
            b("the Suites window and restored on next launch.")
            blank()

            h("AUTO-RUN SCHEDULING")
            b("Use the Auto-Run every: dropdown to schedule periodic suite runs.")
            b("Intervals: Off, 30 min, 1 hour, 4 hours, 12 hours, 24 hours.")
            b("Only one suite can be scheduled for auto-run at a time.")
            b("The Auto-Run Suite: label shows which suite is scheduled. This is")
            b("independent of the listbox selection — you can select and run a")
            b("different suite manually without affecting the auto-run schedule.")
            b("To change which suite auto-runs, select it in the list and")
            b("pick an interval from the dropdown. This replaces any previous schedule.")
            b("Safety guards skip a scheduled run if a")
            b("search, index build, or another suite is already in progress.")
            blank()
            s("Display")
            b("\u2022 Auto-Run Suite: shows the name of the scheduled suite.")
            b("\u2022 Last run: shows the suite name and timestamp of the most recent run.")
            b("\u2022 Next Auto-Run: shows a countdown timer (e.g., 4h 22m, 15m, <1m)")
            b("  that updates every minute.")
            blank()
            s("Persistence")
            b("Schedules persist across app restarts. On launch, the app reads")
            b("the last run time from the collection, calculates when the next")
            b("run is due, and resumes automatically. If a run is overdue (e.g.,")
            b("the app was closed during the interval), it runs shortly after")
            b("launch. The Suites window does not need to be open. When you")
            b("reopen the Suites window, the scheduled suite is automatically")
            b("re-selected and highlighted in the list.")
            blank()
            s("Auto-Run Output")
            b("When a scheduled run completes, three things happen automatically:")
            blank()
            b("1. Suite reports are generated with timestamps:")
            e("DO_NOT_SEARCH_docsearch_suite_{name}_{timestamp}.docx")
            e("DO_NOT_SEARCH_docsearch_suite_{name}_{timestamp}.txt")
            e("DO_NOT_SEARCH_docsearch_suite_{name}_{timestamp}.json")
            b("The .docx report includes a color-coded summary table, per-stage")
            b("details, a report fingerprint, and a source file manifest.")
            blank()
            b("2. An entry is appended to the auto-run log:")
            e("DO_NOT_SEARCH_autorun_log.txt")
            b("Each entry records the suite name, time, pass/fail summary,")
            b("and per-search results:")
            e("[2026-03-28 14:30:00] Suite: quarterly_compliance \u2014 4/5 passed \u2014 FAILED")
            e("  [PASS] find_contracts \u2014 12 match(es) (need >= 1)")
            e("  [FAIL] no_pii \u2014 2 match(es) (need == 0)")
            blank()
            b("3. An email alert is sent (if configured) with the suite name,")
            b("pass/fail summary, and per-test details. By default, alerts are")
            b("sent only when a suite has FAIL results.")
            blank()
            b("Files are written to the suite's Output Dir if set, otherwise")
            b("to the search folder. The DO_NOT_SEARCH prefix ensures they")
            b("are never re-searched.")
            blank()
            b("Click Open Auto-Run History to view the log file.")
            b("Click Clear Auto-Run History to delete it.")
            b("The log is automatically recreated on the next auto-run.")
            blank()

            h("EMAIL ALERTS")
            b("Click Configure Email Alerts to set up email notifications.")
            b("docsearch sends alerts via your email provider's SMTP server.")
            b("You need your email address, an app password (not your regular")
            b("login password), and your provider's SMTP server address.")
            blank()
            s("Quick Setup")
            e("Gmail:     smtp.gmail.com, port 587")
            e("Outlook:   smtp.office365.com, port 587")
            e("Yahoo:     smtp.mail.yahoo.com, port 587")
            e("Corporate: ask your IT department")
            blank()
            b("App passwords: Most providers require an app password instead")
            b("of your regular password. For Gmail, go to myaccount.google.com")
            b("\u2192 Security \u2192 App passwords. For Outlook, go to")
            b("account.microsoft.com \u2192 Security \u2192 App passwords.")
            blank()
            s("Alert Options")
            b("\u2022 failure \u2014 only send when a suite has FAIL results (default)")
            b("\u2022 always \u2014 send after every scheduled run")
            b("\u2022 off \u2014 no emails")
            blank()
            b("Click Send Test Email to verify your settings before saving.")
            b("Settings are saved to ~/.docsearchrc.")

            txt.configure(state="disabled")

            close_btn = ctk.CTkButton(
                help_win, text="Close", width=100,
                command=help_win.destroy,
            )
            close_btn.pack(pady=(5, 10))

        def _capture_suite_output_dir(self):
            """Save the suite output dir entry value and persist to ~/.docsearchrc."""
            if hasattr(self, 'suite_output_dir_entry'):
                try:
                    val = self.suite_output_dir_entry.get().strip()
                    self._saved_suite_output_dir = val
                    # Persist to ~/.docsearchrc
                    from docsearch.cli import _save_config, _load_config
                    config = _load_config()
                    if val:
                        config["suite_output_dir"] = val
                    else:
                        config.pop("suite_output_dir", None)
                    _save_config(config)
                except Exception:
                    pass

        def _on_suite_window_close(self):
            """Handle the suite window close button."""
            if self.suite_running:
                return  # Don't close while a suite is running
            self._capture_suite_output_dir()
            self.suite_window.destroy()
            self.suite_window = None
            self.suite_toggle.configure(text="\u25b6 Search Suites")
            self.suite_visible = False

        def _toggle_suite_panel(self):
            if self.suite_visible:
                if self.suite_running:
                    return
                self._capture_suite_output_dir()
                self.suite_window.destroy()
                self.suite_window = None
                self.suite_toggle.configure(text="\u25b6 Search Suites")
                self.suite_visible = False
            else:
                # Guard against schedule reset during panel construction
                self._restoring_schedule = True
                self._build_suite_panel()
                self.suite_toggle.configure(text="\u25bc Search Suites")
                self.suite_visible = True
                self._refresh_suite_panel()
                # Re-select the scheduled suite if any
                self._restore_suite_selection()
                # Refresh schedule display without resetting the timer
                if self._scheduled_suite_interval:
                    self.suite_schedule_var.set(self._scheduled_suite_interval)
                self._restoring_schedule = False
                self._update_last_run_label()
                self._update_countdown()
                self._update_autorun_name_label()

        def _refresh_suite_panel(self):
            """Reload saved searches and suites from the collection file."""
            if not hasattr(self, "suite_selector"):
                return
            from docsearch.collection import load_collection
            folder = self.folder_entry.get().strip()
            self.suite_selector.delete(0, "end")
            self.suite_contents_listbox.delete(0, "end")
            if not folder or not os.path.isdir(folder):
                return
            data = load_collection(folder)
            for name in sorted(data["test_suites"]):
                self.suite_selector.insert("end", name)

        def _restore_suite_selection(self):
            """Re-select the scheduled suite in the listbox after rebuild."""
            name = self._scheduled_suite_name
            if not name or not hasattr(self, 'suite_selector'):
                return
            for i in range(self.suite_selector.size()):
                if self.suite_selector.get(i) == name:
                    self.suite_selector.selection_set(i)
                    self.suite_selector.see(i)
                    self._on_suite_selected()
                    break

        def _on_suite_selected(self, event=None):
            """Populate the suite contents listbox from all selected suites."""
            from docsearch.collection import get_suite
            folder = self.folder_entry.get().strip()
            self.suite_contents_listbox.delete(0, "end")
            sel = self.suite_selector.curselection()
            if not sel or not folder:
                self._update_last_run_label()
                return
            seen = set()
            for idx in sel:
                suite_name = self.suite_selector.get(idx)
                suite = get_suite(folder, suite_name)
                if suite:
                    suite_pc = suite.get("pass_criteria", {})
                    for search_name in suite["searches"]:
                        if search_name not in seen:
                            seen.add(search_name)
                            pc = suite_pc.get(search_name, {"op": ">=", "n": 1})
                            label = f"{search_name}  ({pc['op']} {pc['n']})"
                            self.suite_contents_listbox.insert("end", label)
            self._update_last_run_label()

        def _open_load_search_popup(self):
            """Open a popup with saved searches listbox and Select/Delete buttons."""
            import tkinter as tk
            from docsearch.collection import load_collection
            if self._load_search_popup and self._load_search_popup.winfo_exists():
                self._load_search_popup.destroy()
                self._load_search_popup = None
                return

            folder = self.folder_entry.get().strip()
            names = []
            if folder and os.path.isdir(folder):
                data = load_collection(folder)
                names = sorted(data.get("saved_searches", {}).keys())

            popup = tk.Toplevel(self)
            popup.title("Load Settings")
            popup.resizable(False, False)
            popup.transient(self)
            self._load_search_popup = popup

            # Position below the button
            btn = self.load_search_btn
            x = btn.winfo_rootx()
            y = btn.winfo_rooty() + btn.winfo_height()
            popup.geometry(f"+{x}+{y}")

            frame = ctk.CTkFrame(popup)
            frame.pack(fill="both", expand=True)

            listbox = tk.Listbox(frame, width=30, height=min(len(names), 10) or 1,
                                 font=("TkDefaultFont", 13), selectmode="browse",
                                 exportselection=False, activestyle="none")
            if names:
                for n in names:
                    listbox.insert("end", n)
                listbox.selection_set(0)
            else:
                listbox.insert("end", "(no saved searches)")
            listbox.pack(side="top", fill="both", expand=True, padx=4, pady=(4, 2))

            _motion_active = [True]

            def _on_motion(event):
                if not _motion_active[0]:
                    return
                idx = listbox.nearest(event.y)
                if idx >= 0:
                    listbox.selection_clear(0, "end")
                    listbox.selection_set(idx)

            def _on_click(event):
                _motion_active[0] = False

            listbox.bind("<Motion>", _on_motion)
            listbox.bind("<ButtonPress-1>", _on_click)

            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.pack(side="top", fill="x", padx=4, pady=(2, 4))

            def on_select():
                sel = listbox.curselection()
                if not sel:
                    return
                name = listbox.get(sel[0])
                if name == "(no saved searches)":
                    return
                from docsearch.collection import get_search_params
                params = get_search_params(folder, name)
                if params:
                    self._apply_params_to_gui(params)
                    self.status_label.configure(
                        text=f"Loaded search '{name}' from collection.",
                        text_color=("gray30", "gray70"), font=ctk.CTkFont(size=13),
                    )
                popup.destroy()
                self._load_search_popup = None

            def on_delete():
                sel = listbox.curselection()
                if not sel:
                    return
                name = listbox.get(sel[0])
                if name == "(no saved searches)":
                    return
                from tkinter import messagebox
                from docsearch.collection import remove_saved_search
                if not messagebox.askyesno("Delete Saved Search",
                                           f"Delete saved search '{name}'?",
                                           parent=popup):
                    return
                remove_saved_search(folder, name)
                listbox.delete(sel[0])
                self._refresh_suite_panel()
                self.status_label.configure(
                    text=f"Deleted saved search '{name}'.",
                    text_color=("gray30", "gray70"), font=ctk.CTkFont(size=13),
                )
                if listbox.size() == 0:
                    listbox.insert("end", "(no saved searches)")

            def close_popup(event=None):
                if self._load_search_popup and self._load_search_popup.winfo_exists():
                    self._load_search_popup.destroy()
                    self._load_search_popup = None

            ctk.CTkButton(btn_frame, text="Cancel", width=70, font=ctk.CTkFont(size=12),
                          command=close_popup).pack(side="left", padx=(0, 5))
            ctk.CTkButton(btn_frame, text="Select", width=70, font=ctk.CTkFont(size=12),
                          command=on_select).pack(side="left")
            ctk.CTkButton(btn_frame, text="Delete", width=70, font=ctk.CTkFont(size=12),
                          fg_color="firebrick", hover_color="darkred",
                          command=on_delete).pack(side="right")

            listbox.bind("<Double-1>", lambda e: on_select())
            popup.bind("<Escape>", close_popup)
            popup.protocol("WM_DELETE_WINDOW", close_popup)
            listbox.focus_set()

        def _refresh_load_search_menu(self):
            """No-op — popup rebuilds its list each time it opens."""
            pass


        def _build_search_shuttle(self, dialog, available, selected_order, criteria=None):
            """Build a dual-listbox shuttle widget for ordering suite searches.

            Args:
                dialog: Parent tk.Toplevel.
                available: List of search names to show on the left (not yet selected).
                selected_order: List of search names for the right (pre-selected, in order).
                criteria: Dict of per-search pass criteria, e.g. {"s1": {"op": ">=", "n": 1}}.

            Returns:
                A callable that returns (search_list, criteria_dict).
            """
            import tkinter as tk

            _criteria = dict(criteria) if criteria else {}

            # Labels row
            label_frame = tk.Frame(dialog)
            label_frame.pack(padx=15, fill="x")
            tk.Label(label_frame, text="Available searches:", font=("TkDefaultFont", 13)).pack(
                side="left", expand=True, anchor="w"
            )
            tk.Label(label_frame, text="Selected (run order):", font=("TkDefaultFont", 13)).pack(
                side="right", expand=True, anchor="w", padx=(40, 0)
            )

            # Main shuttle frame
            shuttle = tk.Frame(dialog)
            shuttle.pack(padx=15, fill="both", expand=True)

            # Left listbox — available searches
            left_frame = tk.Frame(shuttle)
            left_frame.pack(side="left", fill="both", expand=True)
            left_scroll = tk.Scrollbar(left_frame)
            left_scroll.pack(side="right", fill="y")
            left_lb = tk.Listbox(
                left_frame, font=("TkDefaultFont", 12), selectmode="extended",
                yscrollcommand=left_scroll.set, activestyle="none",
            )
            left_lb.pack(side="left", fill="both", expand=True)
            left_scroll.config(command=left_lb.yview)

            # Center buttons — Add / Remove
            center_frame = tk.Frame(shuttle)
            center_frame.pack(side="left", padx=8, anchor="center")
            tk.Button(center_frame, text="\u2192", width=3, command=lambda: _add()).pack(pady=2)
            tk.Button(center_frame, text="\u2190", width=3, command=lambda: _remove()).pack(pady=2)

            # Right listbox — selected searches in order
            right_frame = tk.Frame(shuttle)
            right_frame.pack(side="left", fill="both", expand=True)
            right_scroll = tk.Scrollbar(right_frame)
            right_scroll.pack(side="right", fill="y")
            right_lb = tk.Listbox(
                right_frame, font=("TkDefaultFont", 12), selectmode="extended",
                yscrollcommand=right_scroll.set, activestyle="none",
            )
            right_lb.pack(side="left", fill="both", expand=True)
            right_scroll.config(command=right_lb.yview)

            # Right-side buttons — Up / Down
            order_frame = tk.Frame(shuttle)
            order_frame.pack(side="left", padx=(8, 0), anchor="center")
            tk.Button(order_frame, text="\u25b2 Up", width=5, command=lambda: _move_up()).pack(pady=2)
            tk.Button(order_frame, text="\u25bc Down", width=5, command=lambda: _move_down()).pack(pady=2)

            # Pass criteria row — below the shuttle
            criteria_frame = tk.Frame(dialog)
            criteria_frame.pack(padx=15, fill="x", pady=(5, 0))
            tk.Label(criteria_frame, text="Pass criteria:", font=("TkDefaultFont", 12)).pack(side="left")
            criteria_op_var = tk.StringVar(value=">=")
            op_menu = tk.OptionMenu(criteria_frame, criteria_op_var, ">=", "<=", "==")
            op_menu.config(font=("TkDefaultFont", 12), width=3)
            op_menu.pack(side="left", padx=(5, 2))
            criteria_n_var = tk.StringVar(value="1")
            criteria_n_entry = tk.Entry(criteria_frame, textvariable=criteria_n_var, width=5, font=("TkDefaultFont", 12))
            criteria_n_entry.pack(side="left", padx=(0, 5))
            tk.Label(criteria_frame, text="match(es)", font=("TkDefaultFont", 12)).pack(side="left")
            criteria_hint = tk.Label(
                criteria_frame, text="  (select a search on the right to set its criteria)",
                font=("TkDefaultFont", 10), fg="gray50",
            )
            criteria_hint.pack(side="left", padx=(10, 0))

            _current_search = [None]  # track which search's criteria we're editing

            def _save_current_criteria():
                """Save the current criteria UI values back to the dict."""
                name = _current_search[0]
                if name is None:
                    return
                op = criteria_op_var.get()
                try:
                    n = int(criteria_n_var.get())
                except ValueError:
                    n = 1
                _criteria[name] = {"op": op, "n": n}

            def _load_criteria_for_selection(event=None):
                """Load criteria for the selected search in the right listbox."""
                _save_current_criteria()
                sel = right_lb.curselection()
                if not sel:
                    _current_search[0] = None
                    criteria_hint.config(text="  (select a search on the right to set its criteria)")
                    return
                name = right_lb.get(sel[0])
                _current_search[0] = name
                pc = _criteria.get(name, {"op": ">=", "n": 1})
                criteria_op_var.set(pc["op"])
                criteria_n_var.set(str(pc["n"]))
                criteria_hint.config(text=f"  for: {name}")

            right_lb.bind("<<ListboxSelect>>", _load_criteria_for_selection)

            # Save criteria when op or n changes
            criteria_op_var.trace_add("write", lambda *_: _save_current_criteria())
            criteria_n_var.trace_add("write", lambda *_: _save_current_criteria())

            # Populate
            for name in sorted(available):
                left_lb.insert("end", name)
            for name in selected_order:
                right_lb.insert("end", name)

            # Double-click to add/remove
            left_lb.bind("<Double-Button-1>", lambda e: _add())
            right_lb.bind("<Double-Button-1>", lambda e: _remove())

            def _add():
                sel = list(left_lb.curselection())
                if not sel:
                    return
                names = [left_lb.get(i) for i in sel]
                for i in reversed(sel):
                    left_lb.delete(i)
                for name in names:
                    right_lb.insert("end", name)

            def _remove():
                sel = list(right_lb.curselection())
                if not sel:
                    return
                names = [right_lb.get(i) for i in sel]
                for i in reversed(sel):
                    right_lb.delete(i)
                # Clean up criteria for removed searches
                for name in names:
                    _criteria.pop(name, None)
                _current_search[0] = None
                criteria_hint.config(text="  (select a search on the right to set its criteria)")
                for name in sorted(names):
                    # Insert in alphabetical position (re-read each time)
                    left_items = list(left_lb.get(0, "end"))
                    pos = len(left_items)
                    for j, existing in enumerate(left_items):
                        if name.lower() < existing.lower():
                            pos = j
                            break
                    left_lb.insert(pos, name)

            def _move_up():
                sel = list(right_lb.curselection())
                if not sel or sel[0] == 0:
                    return
                for i in sel:
                    text = right_lb.get(i)
                    right_lb.delete(i)
                    right_lb.insert(i - 1, text)
                    right_lb.selection_set(i - 1)

            def _move_down():
                sel = list(right_lb.curselection())
                if not sel or sel[-1] >= right_lb.size() - 1:
                    return
                for i in reversed(sel):
                    text = right_lb.get(i)
                    right_lb.delete(i)
                    right_lb.insert(i + 1, text)
                    right_lb.selection_set(i + 1)

            def _get_result():
                _save_current_criteria()
                return list(right_lb.get(0, "end")), dict(_criteria)

            return _get_result

        def _create_suite_dialog(self):
            """Open dialog to create a new search suite."""
            import tkinter as tk
            from docsearch.collection import load_collection, add_test_suite

            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Select a valid folder first.")
                return
            data = load_collection(folder)
            search_names = sorted(data["saved_searches"])
            if not search_names:
                self._show_error("Save at least one search to the collection first.")
                return

            parent = self.suite_window or self
            dialog = tk.Toplevel(parent)
            dialog.title("Create Search Suite")
            dialog.resizable(True, True)
            w, h = 700, 480
            x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
            y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
            dialog.geometry(f"{w}x{h}+{x}+{y}")
            dialog.transient(parent)
            dialog.grab_set()

            tk.Label(dialog, text="Suite name:", font=("TkDefaultFont", 13)).pack(
                padx=15, pady=(15, 2), anchor="w"
            )
            name_entry = tk.Entry(dialog, font=("TkDefaultFont", 13))
            name_entry.pack(padx=15, fill="x")
            name_entry.focus_set()

            tk.Label(dialog, text="Description (optional):", font=("TkDefaultFont", 13)).pack(
                padx=15, pady=(10, 2), anchor="w"
            )
            desc_entry = tk.Entry(dialog, font=("TkDefaultFont", 13))
            desc_entry.pack(padx=15, fill="x")

            cascade_var = tk.BooleanVar(value=False)
            tk.Checkbutton(
                dialog, text="Cascade mode (each stage searches only files matched by previous stage)",
                variable=cascade_var, font=("TkDefaultFont", 11),
            ).pack(padx=15, pady=(5, 5), anchor="w")

            # Buttons at the bottom (pack first so they're never pushed off)
            btn_frame = tk.Frame(dialog)
            btn_frame.pack(side="bottom", pady=(10, 15))

            get_selected = self._build_search_shuttle(dialog, search_names, [])

            def do_create():
                suite_name = name_entry.get().strip()
                if not suite_name:
                    return
                selected, criteria = get_selected()
                if not selected:
                    return
                desc = desc_entry.get().strip()
                add_test_suite(folder, suite_name, desc, selected, cascade=cascade_var.get(),
                               pass_criteria=criteria)
                dialog.destroy()
                self._refresh_suite_panel()
                # Select the newly created suite
                for i in range(self.suite_selector.size()):
                    if self.suite_selector.get(i) == suite_name:
                        self.suite_selector.selection_set(i)
                        break
                self._on_suite_selected()

            tk.Button(btn_frame, text="Create", width=10, command=do_create).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Cancel", width=10, command=dialog.destroy).pack(side="left", padx=5)

        def _edit_suite_dialog(self):
            """Open dialog to edit an existing search suite's search list."""
            import tkinter as tk
            from docsearch.collection import load_collection, add_test_suite

            sel = self.suite_selector.curselection()
            if not sel or len(sel) != 1:
                return
            suite_name = self.suite_selector.get(sel[0])
            folder = self.folder_entry.get().strip()
            data = load_collection(folder)
            suite = data["test_suites"].get(suite_name)
            if not suite:
                return
            all_search_names = sorted(data["saved_searches"])
            current_order = suite["searches"]
            current_set = set(current_order)
            available = [n for n in all_search_names if n not in current_set]

            parent = self.suite_window or self
            dialog = tk.Toplevel(parent)
            dialog.title(f"Edit Suite: {suite_name}")
            dialog.resizable(True, True)
            w, h = 700, 480
            x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
            y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
            dialog.geometry(f"{w}x{h}+{x}+{y}")
            dialog.transient(parent)
            dialog.grab_set()

            tk.Label(dialog, text="Description:", font=("TkDefaultFont", 13)).pack(
                padx=15, pady=(15, 2), anchor="w"
            )
            desc_entry = tk.Entry(dialog, font=("TkDefaultFont", 13))
            desc_entry.pack(padx=15, fill="x")
            desc_entry.insert(0, suite.get("description", ""))

            cascade_var = tk.BooleanVar(value=suite.get("cascade", False))
            tk.Checkbutton(
                dialog, text="Cascade mode (each stage searches only files matched by previous stage)",
                variable=cascade_var, font=("TkDefaultFont", 11),
            ).pack(padx=15, pady=(5, 5), anchor="w")

            # Buttons at the bottom (pack first so they're never pushed off)
            btn_frame = tk.Frame(dialog)
            btn_frame.pack(side="bottom", pady=(10, 15))

            existing_criteria = suite.get("pass_criteria", {})
            get_selected = self._build_search_shuttle(dialog, available, current_order, criteria=existing_criteria)

            def do_save():
                selected, criteria = get_selected()
                if not selected:
                    return
                desc = desc_entry.get().strip()
                add_test_suite(folder, suite_name, desc, selected, cascade=cascade_var.get(),
                               schedule=suite.get("schedule", "Off"),
                               last_run_time=suite.get("last_run_time"),
                               pass_criteria=criteria)
                dialog.destroy()
                self._refresh_suite_panel()
                for i in range(self.suite_selector.size()):
                    if self.suite_selector.get(i) == suite_name:
                        self.suite_selector.selection_set(i)
                        break
                self._on_suite_selected()

            tk.Button(btn_frame, text="Save", width=10, command=do_save).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Cancel", width=10, command=dialog.destroy).pack(side="left", padx=5)

        def _delete_suite(self):
            """Delete the selected search suite(s)."""
            from tkinter import messagebox
            from docsearch.collection import remove_test_suite
            sel = self.suite_selector.curselection()
            if not sel:
                return
            names = [self.suite_selector.get(i) for i in sel]
            label = ", ".join(names)
            if not messagebox.askyesno("Delete?", f"Delete suite(s): {label}?"):
                return
            folder = self.folder_entry.get().strip()
            for name in names:
                remove_test_suite(folder, name)
            # Cancel suite schedule if active
            if self._suite_schedule_timer_id is not None:
                self.after_cancel(self._suite_schedule_timer_id)
                self._suite_schedule_timer_id = None
            self._scheduled_suite_name = None
            self._scheduled_suite_interval = None
            self.suite_schedule_var.set("Off")
            self._update_last_run_label()
            self._refresh_suite_panel()

        # ── Suite Execution ────────────────────────────────────

        def _run_suite_by_name(self, folder, suite_name):
            """Run a suite by name — works even when the Suites window is closed."""
            from docsearch.collection import load_collection, get_search_params
            data = load_collection(folder)
            suite = data["test_suites"].get(suite_name)
            if not suite:
                self._suite_schedule_running = False
                self._suite_scheduled_run = False
                self._reschedule_suite()
                return

            searches = []
            search_criteria = {}
            suite_pc = suite.get("pass_criteria", {})
            for name in suite["searches"]:
                params = get_search_params(folder, name)
                if params:
                    searches.append((name, params))
                if name in suite_pc:
                    search_criteria[name] = suite_pc[name]
            if not searches:
                self._suite_schedule_running = False
                self._suite_scheduled_run = False
                self._reschedule_suite()
                return

            # Set up suite state
            self.suite_running = True
            self.suite_cancel_requested = False
            self.search_button.configure(state="disabled")

            # UI elements — only touch if the suites window is open
            suite_window_open = hasattr(self, 'suite_window') and self.suite_window is not None
            if suite_window_open:
                try:
                    self.run_suite_btn.configure(state="disabled")
                    self.cancel_suite_btn.pack(side="left", padx=(0, 5))
                    self.suite_status_label.configure(text=f"Running 0/{len(searches)}...")
                except Exception:
                    pass

            self._suite_results_data = []
            self._suite_start_time = time.time()
            self._suite_name = suite_name
            self._suite_names_list = [suite_name]
            od = ""
            if self._suite_window_open() and hasattr(self, 'suite_output_dir_entry'):
                try:
                    od = self.suite_output_dir_entry.get().strip()
                except Exception:
                    pass
            if not od:
                od = getattr(self, '_saved_suite_output_dir', '')
            self._suite_output_dir = od if od else folder
            self._search_criteria = search_criteria

            thread = threading.Thread(
                target=self._suite_execution_thread,
                args=(folder, searches),
                daemon=True,
            )
            thread.start()

        def _run_suite(self):
            """Run all searches in the selected suite(s) sequentially."""
            from docsearch.collection import load_collection, get_search_params
            sel = self.suite_selector.curselection()
            if not sel:
                return
            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Select a valid folder.")
                return
            data = load_collection(folder)

            # Gather searches and pass criteria from all selected suites (dedup, preserve order)
            suite_names = [self.suite_selector.get(i) for i in sel]
            searches = []
            search_criteria = {}
            seen = set()
            for sn in suite_names:
                suite = data["test_suites"].get(sn)
                if not suite:
                    continue
                suite_pc = suite.get("pass_criteria", {})
                for name in suite["searches"]:
                    if name not in seen:
                        seen.add(name)
                        params = get_search_params(folder, name)
                        if params:
                            searches.append((name, params))
                        if name in suite_pc:
                            search_criteria[name] = suite_pc[name]
            if not searches:
                self._show_error("No valid searches found in selected suite(s).")
                return

            suite_label = ", ".join(suite_names)

            # Disable UI
            self.suite_running = True
            self.suite_cancel_requested = False
            self.run_suite_btn.configure(state="disabled")
            self.cancel_suite_btn.pack(side="left", padx=(0, 5))
            self.search_button.configure(state="disabled")

            self._suite_results_data = []
            self._suite_start_time = time.time()
            self._suite_name = suite_label
            self._suite_names_list = suite_names

            od = ""
            if self._suite_window_open() and hasattr(self, 'suite_output_dir_entry'):
                try:
                    od = self.suite_output_dir_entry.get().strip()
                except Exception:
                    pass
            if not od:
                od = getattr(self, '_saved_suite_output_dir', '')
            self._suite_output_dir = od if od else folder

            self.suite_status_label.configure(text=f"Running 0/{len(searches)}...")

            self._search_criteria = search_criteria
            thread = threading.Thread(
                target=self._suite_execution_thread,
                args=(folder, searches),
                daemon=True,
            )
            thread.start()

        def _suite_execution_thread(self, folder, searches):
            """Run each search in sequence in a background thread."""
            import re as _re
            from docsearch.reporter import copy_stage_reports, cleanup_stage_reports

            results = []
            total = len(searches)
            output_dir = self._suite_output_dir

            # Collect source file manifest for the suite report
            from docsearch.constants import SUPPORTED_TYPES, OCR_IMAGE_TYPES
            all_exts = SUPPORTED_TYPES | OCR_IMAGE_TYPES
            source_files = []
            try:
                for fname in sorted(os.listdir(folder)):
                    fpath = os.path.join(folder, fname)
                    if os.path.isfile(fpath) and os.path.splitext(fname)[1].lower() in all_exts:
                        stat = os.stat(fpath)
                        mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                        source_files.append((fpath, stat.st_size, mod_time))
            except OSError:
                pass
            self._suite_source_files = source_files

            # Clean up stage files from any previous run of this suite
            cleanup_stage_reports(output_dir, self._suite_name)

            # Cascade: active only for single-suite runs with cascade=True
            cascade_active = False
            if len(self._suite_names_list) == 1:
                from docsearch.collection import load_collection
                sd = load_collection(folder)["test_suites"].get(self._suite_names_list[0], {})
                cascade_active = sd.get("cascade", False)
            cascade_files = None  # None = no restriction

            for i, (name, params) in enumerate(searches):
                if self.suite_cancel_requested:
                    break

                self.after(0, lambda idx=i, n=name, t=total, p=params:
                    (self._apply_params_to_gui(p),
                     self.suite_status_label.configure(text=f"Running {idx+1}/{t}: {n}...")))

                cmd = _build_command_from_values(
                    search_text=params.get("search_text", ""),
                    folder=folder,
                    and_mode=params.get("and_mode", False),
                    recursive=params.get("recursive", False),
                    fuzzy=params.get("fuzzy", False),
                    wildcard=params.get("wildcard", False),
                    ocr=params.get("ocr", False),
                    regex=params.get("regex", False),
                    exclude=params.get("exclude", ""),
                    file_types=params.get("file_types", ""),
                    proximity=params.get("proximity", ""),
                    context_before=params.get("context_before", ""),
                    context_after=params.get("context_after", ""),
                    cores=params.get("cores", ""),
                    specific_files=params.get("specific_files", ""),
                    index_search=params.get("index_search", False),
                    inverse=params.get("inverse", False),
                    expression=params.get("expression", False),
                    whole_word=params.get("whole_word", False),
                    max_matches=params.get("max_matches", ""),
                    range_filters=params.get("range_filters", ""),
                )

                # Cascade: track input file count and inject file list
                cascade_input_count = len(cascade_files) if (cascade_active and cascade_files is not None) else None
                # Inject --output-dir when output directory differs from search folder
                if output_dir != folder and cmd is not None and cmd != "FLAGS_IN_SEARCH":
                    cmd.extend(["--output-dir", output_dir])

                if cascade_active and cascade_files is not None and cmd is not None and cmd != "FLAGS_IN_SEARCH":
                    # Remove any existing -f flag from saved search params
                    if "-f" in cmd:
                        f_idx = cmd.index("-f")
                        cmd = cmd[:f_idx] + cmd[f_idx + 2:]
                    cmd.extend(["-f", ",".join(cascade_files)])

                if cmd is None or cmd == "FLAGS_IN_SEARCH":
                    result = {
                        "name": name,
                        "search_text": params.get("search_text", ""),
                        "inverse": params.get("inverse", False),
                        "return_code": 2,
                        "passed": False,
                        "match_count": 0,
                        "pass_criteria": self._search_criteria.get(name, {"op": ">=", "n": 1}),
                        "summary": "Invalid search configuration",
                        "stage_files": {},
                        "cascade_input_count": cascade_input_count,
                        "cascade_file_count": None if not cascade_active else 0,
                    }
                    if cascade_active:
                        cascade_files = None  # break chain
                    results.append(result)
                    self.after(0, self._suite_test_completed, result)
                    continue

                try:
                    proc = subprocess.Popen(
                        cmd, cwd=folder,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True,
                    )
                    stdout, _ = proc.communicate()
                    returncode = proc.returncode
                except Exception as exc:
                    result = {
                        "name": name,
                        "search_text": params.get("search_text", ""),
                        "inverse": params.get("inverse", False),
                        "return_code": 2,
                        "passed": False,
                        "match_count": 0,
                        "pass_criteria": self._search_criteria.get(name, {"op": ">=", "n": 1}),
                        "summary": str(exc),
                        "stage_files": {},
                        "cascade_input_count": cascade_input_count,
                        "cascade_file_count": None if not cascade_active else 0,
                    }
                    if cascade_active:
                        cascade_files = None  # break chain
                    results.append(result)
                    self.after(0, self._suite_test_completed, result)
                    continue

                # Parse match count from stdout
                match_count = 0
                if stdout:
                    clean = _re.sub(r"\033\[[0-9;]*m", "", stdout)
                    m = _re.search(r"Found (\d+) match", clean)
                    if m:
                        match_count = int(m.group(1))
                    else:
                        m = _re.search(r"Found (\d+) file\(s\) WITHOUT", clean)
                        if m:
                            match_count = int(m.group(1))

                # Copy per-stage reports before the next search overwrites them
                stage_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                stage_files = copy_stage_reports(output_dir, self._suite_name, i + 1, name, timestamp_suffix=stage_ts)

                # Evaluate pass/fail using per-search criteria
                pc = self._search_criteria.get(name, {"op": ">=", "n": 1})
                if returncode == 2:
                    passed = False
                elif pc["op"] == ">=":
                    passed = match_count >= pc["n"]
                elif pc["op"] == "<=":
                    passed = match_count <= pc["n"]
                elif pc["op"] == "==":
                    passed = match_count == pc["n"]
                else:
                    passed = returncode == 0

                result = {
                    "name": name,
                    "search_text": params.get("search_text", ""),
                    "inverse": params.get("inverse", False),
                    "return_code": returncode,
                    "passed": passed,
                    "match_count": match_count,
                    "pass_criteria": pc,
                    "summary": _parse_summary_text(stdout) if stdout else "",
                    "stage_files": stage_files,
                    "cascade_input_count": cascade_input_count,
                    "cascade_file_count": None,
                }

                # Cascade: extract matched files for next stage
                if cascade_active:
                    if result["passed"] and match_count > 0:
                        matched = _parse_matched_files(output_dir)
                        cascade_files = list({filename for _fp, filename, _count in matched})
                        result["cascade_file_count"] = len(cascade_files)
                    else:
                        cascade_files = None  # break chain
                        result["cascade_file_count"] = 0

                results.append(result)
                self.after(0, self._suite_test_completed, result)

            self.after(0, self._suite_finished, results)

        def _suite_window_open(self):
            """Check if the suite window and its widgets are available."""
            return (hasattr(self, 'suite_window') and self.suite_window is not None
                    and self.suite_window.winfo_exists())

        def _suite_test_completed(self, result):
            """Record one test result (results text area removed)."""
            pass

        def _suite_finished(self, results):
            """All tests done. Show summary and re-enable UI."""
            from docsearch.collection import update_suite_field
            self._suite_results_data = results
            self._suite_end_time = time.time()

            passed = sum(1 for r in results if r["passed"])
            total = len(results)
            verdict = "PASSED" if passed == total else "FAILED"

            suite_open = self._suite_window_open()

            elapsed = self._suite_end_time - self._suite_start_time
            if suite_open:
                if self.suite_cancel_requested:
                    self.suite_status_label.configure(text=f"Cancelled after {elapsed:.1f}s")
                else:
                    self.suite_status_label.configure(text=f"Done in {elapsed:.1f}s — {verdict}")

            # Record last_run_time for each suite that was run
            folder = self.folder_entry.get().strip()
            run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if folder:
                for sn in self._suite_names_list:
                    update_suite_field(folder, sn, "last_run_time", run_time)
            self._update_last_run_label()

            # Auto-generate suite reports
            if results and not self.suite_cancel_requested:
                self._generate_suite_report()

            # Re-enable UI
            self.suite_running = False
            if suite_open:
                self.run_suite_btn.configure(state="normal")
                self.cancel_suite_btn.pack_forget()
                # Show View Suite Report button if a report was generated
                if self._suite_report_path and os.path.exists(self._suite_report_path):
                    self.view_suite_report_btn.grid(row=9, column=0, columnspan=2, pady=(0, 10))
            self.search_button.configure(state="normal")

            # Handle scheduled run completion
            if self._suite_scheduled_run:
                self._suite_scheduled_run = False
                self._suite_schedule_running = False
                self._log_autorun(folder, results, run_time, passed, total, verdict)
                self._reschedule_suite()


        def _cancel_suite(self):
            """Signal the suite execution thread to stop after the current test."""
            self.suite_cancel_requested = True
            self.suite_status_label.configure(text="Cancelling...")

        def _generate_suite_report(self):
            """Generate TXT, JSON, and DOCX reports for the last suite run."""
            from docsearch.reporter import (write_suite_report_txt,
                                            write_suite_report_json,
                                            write_suite_report_docx)
            from docsearch import __version__
            folder = self.folder_entry.get().strip()
            if not folder or not self._suite_results_data:
                return
            report_dir = getattr(self, '_suite_output_dir', folder)
            safe_name = self._suite_name.replace(" ", "_").replace("/", "_")
            ts = f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            txt_path = os.path.join(report_dir, f"DO_NOT_SEARCH_docsearch_suite_{safe_name}{ts}.txt")
            json_path = os.path.join(report_dir, f"DO_NOT_SEARCH_docsearch_suite_{safe_name}{ts}.json")
            docx_path = os.path.join(report_dir, f"DO_NOT_SEARCH_docsearch_suite_{safe_name}{ts}.docx")
            write_suite_report_txt(
                txt_path, self._suite_name, folder,
                self._suite_results_data,
                self._suite_start_time, self._suite_end_time,
            )
            write_suite_report_json(
                json_path, self._suite_name, folder,
                self._suite_results_data,
                self._suite_start_time, self._suite_end_time,
            )
            write_suite_report_docx(
                docx_path, self._suite_name, folder,
                self._suite_results_data,
                self._suite_start_time, self._suite_end_time,
                version=__version__,
                source_files=getattr(self, '_suite_source_files', None),
            )
            self._suite_report_path = docx_path
            suite_open = self._suite_window_open()
            if suite_open:
                self.suite_status_label.configure(
                    text=f"Reports saved: {os.path.basename(docx_path)} (+txt, json)"
                )

        def _open_suite_report(self):
            """Open the .docx suite report from the last run."""
            path = self._suite_report_path
            if not path or not os.path.exists(path):
                self.suite_status_label.configure(text="No suite report found.")
                return
            system = platform.system()
            if system == "Darwin":
                subprocess.Popen(["open", path])
            elif system == "Windows":
                os.startfile(path)
            else:
                subprocess.Popen(["xdg-open", path])

        def _configure_email_alerts(self):
            """Open a dialog to configure email alert settings."""
            from docsearch.cli import _load_config, _save_config

            dialog = ctk.CTkToplevel(self)
            dialog.title("Email Alert Settings")
            dialog.geometry("500x420")
            dialog.transient(self)
            dialog.grab_set()

            cfg = _load_config()

            ctk.CTkLabel(dialog, text="Email Alert Settings", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))
            ctk.CTkLabel(dialog, text="Send email notifications when scheduled suite runs complete.",
                         font=ctk.CTkFont(size=11), text_color="gray50").pack(pady=(0, 10))

            form = ctk.CTkFrame(dialog, fg_color="transparent")
            form.pack(fill="x", padx=20)

            fields = {}
            row = 0
            for label, key, default, tooltip in [
                ("SMTP Server:", "smtp_host", "", "e.g., smtp.gmail.com or smtp.office365.com"),
                ("SMTP Port:", "smtp_port", "587", "587 for STARTTLS (Gmail, Outlook), 465 for SSL, 25 for plain"),
                ("Username:", "smtp_user", "", "Your email login (often your full email address)"),
                ("Password:", "smtp_password", "", "App password (Gmail) or account password"),
                ("From Address:", "email_from", "", "Sender address (defaults to username if blank)"),
                ("To Address:", "email_to", "", "Recipient email address for alerts"),
            ]:
                ctk.CTkLabel(form, text=label, font=ctk.CTkFont(size=12)).grid(row=row, column=0, padx=(0, 10), pady=4, sticky="e")
                entry = ctk.CTkEntry(form, width=300,
                                     show="*" if "password" in key.lower() else "")
                entry.grid(row=row, column=1, pady=4, sticky="w")
                val = cfg.get(key, default)
                if val:
                    entry.insert(0, str(val))
                Tooltip(entry, tooltip)
                fields[key] = entry
                row += 1

            # Email on: failure only vs always
            ctk.CTkLabel(form, text="Send alerts:", font=ctk.CTkFont(size=12)).grid(row=row, column=0, padx=(0, 10), pady=4, sticky="e")
            email_on_var = ctk.StringVar(value=cfg.get("email_on", "failure"))
            email_on_menu = ctk.CTkOptionMenu(form, variable=email_on_var,
                                               values=["failure", "always", "off"], width=150)
            email_on_menu.grid(row=row, column=1, pady=4, sticky="w")
            Tooltip(email_on_menu, "failure = only when a suite has FAIL results. always = every auto-run. off = no emails")
            row += 1

            status_label = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=11))
            status_label.pack(pady=(10, 0))

            btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            btn_frame.pack(pady=(10, 15))

            def _save():
                cfg_update = _load_config()
                for key, entry in fields.items():
                    cfg_update[key] = entry.get().strip()
                cfg_update["email_on"] = email_on_var.get()
                _save_config(cfg_update)
                status_label.configure(text="Settings saved to ~/.docsearchrc", text_color="green")

            def _test():
                from docsearch.email_alert import send_suite_alert
                test_cfg = {}
                for key, entry in fields.items():
                    test_cfg[key] = entry.get().strip()
                test_cfg["email_on"] = "always"  # Force send for test
                status_label.configure(text="Sending test email...", text_color="gray50")
                dialog.update()
                err = send_suite_alert(
                    test_cfg, "Test Suite", "/test/folder",
                    [{"name": "test_check", "passed": True, "match_count": 5,
                      "pass_criteria": {"op": ">=", "n": 1}}],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    1, 1, "PASSED",
                )
                if err:
                    status_label.configure(text=err, text_color="red")
                else:
                    status_label.configure(text="Test email sent successfully!", text_color="green")

            ctk.CTkButton(btn_frame, text="Save", width=100, command=_save).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Send Test Email", width=140, command=_test).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Close", width=100, fg_color="transparent",
                          text_color=("gray30", "gray70"), hover_color=("gray90", "gray25"),
                          command=dialog.destroy).pack(side="left", padx=5)

        def _build_bottom_row(self):
            self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
            self.bottom_frame.grid(
                row=10, column=0, columnspan=3, padx=15, pady=(0, 15), sticky="sew"
            )

            ctk.CTkLabel(
                self.bottom_frame, text="Toolbar",
                font=ctk.CTkFont(size=10), text_color=("gray50", "gray50"),
            ).pack(side="left", padx=(5, 2))

            self.help_button = ctk.CTkButton(
                self.bottom_frame,
                text="Open Readme.md",
                width=110,
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self.open_help,
                font=ctk.CTkFont(size=13),
            )
            self.help_button.pack(side="left")

            self.about_button = ctk.CTkButton(
                self.bottom_frame,
                text="About",
                width=70,
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self.show_about,
                font=ctk.CTkFont(size=13),
            )
            self.about_button.pack(side="right", padx=5)

            text_size_menu = ctk.CTkOptionMenu(
                self.bottom_frame, variable=self._text_size_var,
                values=["Small", "Normal", "Large", "Extra Large"],
                width=110, font=ctk.CTkFont(size=11),
                command=self._on_text_size_changed,
            )
            text_size_menu.pack(side="right", padx=5)
            ctk.CTkLabel(self.bottom_frame, text="Text Size:", font=ctk.CTkFont(size=11)).pack(side="right")

            self.tooltip_toggle_btn = ctk.CTkButton(
                self.bottom_frame,
                text="Disable Hover Text",
                width=130,
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self._toggle_tooltips,
                font=ctk.CTkFont(size=13),
            )
            self.tooltip_toggle_btn.pack(side="right", padx=5)

            self.clear_error_log_btn = ctk.CTkButton(
                self.bottom_frame,
                text="Clear Error Log",
                width=115,
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self._clear_error_log,
                font=ctk.CTkFont(size=13),
            )
            self.clear_error_log_btn.pack(side="right", padx=5)

            self.view_error_log_bottom = ctk.CTkButton(
                self.bottom_frame,
                text="View Error Log",
                width=110,
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self.open_error_log,
                font=ctk.CTkFont(size=13),
            )
            self.view_error_log_bottom.pack(side="right", padx=5)
            Tooltip(self.view_error_log_bottom, "Open docsearch_errors.log to see details about files that could not be read")


        # ── Actions ──────────────────────────────────────────────

        def _toggle_tooltips(self):
            Tooltip.enabled = not Tooltip.enabled
            if Tooltip.enabled:
                self.tooltip_toggle_btn.configure(text="Disable Hover Text")
            else:
                self.tooltip_toggle_btn.configure(text="Enable Hover Text")

        def toggle_advanced(self):
            if self.advanced_visible:
                self._close_advanced_window()
            else:
                self.advanced_window.deiconify()
                self.advanced_window.lift()
                self.advanced_toggle.configure(text="\u25bc Advanced Options")
                self.advanced_visible = True

        def _close_advanced_window(self):
            self.advanced_window.withdraw()
            self.advanced_toggle.configure(text="\u25b6 Advanced Options")
            self.advanced_visible = False

        def _toggle_index_options(self):
            if self.index_visible:
                self.index_frame.grid_remove()
                self.index_toggle_btn.configure(text="\u25b6 Index Options")
            else:
                if not self.index_contents.winfo_ismapped():
                    self.index_contents.pack(fill="x", expand=True, padx=5, pady=5)
                self.index_frame.grid(
                    row=5, column=0, columnspan=3, padx=15, pady=(5, 0), sticky="ew"
                )
                self.index_toggle_btn.configure(text="\u25bc Index Options")
            self.index_visible = not self.index_visible

        def browse_folder(self):
            initial = self.folder_entry.get() or os.path.expanduser("~")
            folder = filedialog.askdirectory(initialdir=initial)
            if folder:
                self.folder_entry.delete(0, "end")
                self.folder_entry.insert(0, folder)
                self._update_index_button_color()
                self._on_refresh_interval_changed(self.refresh_interval_var.get())
                # Resume suite schedule from new folder's collection
                if self.suite_visible:
                    self._refresh_suite_panel()
                self._refresh_load_search_menu()
                self._resume_suite_schedule()

        def _browse_output_dir(self):
            initial = self.output_dir_entry.get().strip() or self.folder_entry.get().strip() or os.path.expanduser("~")
            folder = filedialog.askdirectory(initialdir=initial)
            if folder:
                self.output_dir_entry.delete(0, "end")
                self.output_dir_entry.insert(0, folder)

        def _browse_suite_output_dir(self):
            initial = self.suite_output_dir_entry.get().strip() or self.folder_entry.get().strip() or os.path.expanduser("~")
            folder = filedialog.askdirectory(initialdir=initial)
            if folder:
                self.suite_output_dir_entry.delete(0, "end")
                self.suite_output_dir_entry.insert(0, folder)

        def start_search(self):
            if self.suite_running:
                return
            if self.process is not None:
                self.process.terminate()
                return

            # Wait for any in-progress auto-refresh to finish
            if self._refresh_running:
                self._show_error("Index refresh in progress — please wait a moment.")
                return

            # Pause scheduled auto-refresh while search runs
            if self._refresh_timer_id is not None:
                self.after_cancel(self._refresh_timer_id)
                self._refresh_timer_id = None

            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a valid folder.")
                return

            search_text = self.search_entry.get().strip()
            range_text = self.range_entry.get().strip()
            if not search_text and not range_text:
                self._show_error("Please enter search terms or a range filter.")
                return

            if self.index_search_var.get() == "on":
                index_path = os.path.join(folder, ".docsearch.db")
                if not os.path.exists(index_path):
                    self._show_error(
                        "No search index found in this folder. "
                        "First use Browse to navigate to the folder where your files are, "
                        "then click Build Index(es) to create one."
                    )
                    return

            if self.timestamp_var.get() == "on":
                self._last_ts_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
            else:
                self._last_ts_suffix = ""

            cmd = _build_command_from_values(
                search_text=search_text,
                folder=folder,
                and_mode=self.and_mode_var.get() == "on",
                recursive=self.recursive_var.get() == "on",
                fuzzy=self.fuzzy_var.get() == "on",
                wildcard=self.wildcard_var.get() == "on",
                ocr=self.ocr_var.get() == "on",
                regex=self.regex_var.get() == "on",
                exclude=self.exclude_entry.get(),
                file_types=self.file_types_entry.get(),
                proximity=self.proximity_entry.get(),
                context_before=self.context_before_entry.get(),
                context_after=self.context_after_entry.get(),
                cores=self.cores_entry.get(),
                specific_files=self.specific_files_entry.get(),
                append_name=self.append_name_entry.get(),
                output_csv=self.output_csv_var.get() == "on",
                output_json=self.output_json_var.get() == "on",
                index_search=self.index_search_var.get() == "on",
                inverse=self.inverse_var.get() == "on",
                expression=self.expression_var.get() == "on",
                whole_word=self.whole_word_var.get() == "on",
                max_matches=self.max_matches_entry.get(),
                timestamp_suffix=self._last_ts_suffix,
                output_dir=self.output_dir_entry.get(),
                range_filters=self.range_entry.get(),
            )
            if cmd == "FLAGS_IN_SEARCH":
                self._show_error("Flags go in Advanced Options, not the search box.")
                return
            if cmd is None:
                # Debug: show what values were passed
                dbg = f"folder='{folder}' search='{search_text}' isdir={os.path.isdir(folder)}"
                self._show_error(f"Invalid input. Debug: {dbg}")
                return

            od = self.output_dir_entry.get().strip()
            self.results_dir = od if od else folder
            # Remove stale output files for formats not requested (skip when timestamps are on)
            if not self._last_ts_suffix:
                if self.output_csv_var.get() != "on":
                    stale = os.path.join(self.results_dir, "docsearch_results.csv")
                    if os.path.exists(stale):
                        os.remove(stale)
                if self.output_json_var.get() != "on":
                    stale = os.path.join(self.results_dir, "docsearch_results.json")
                    if os.path.exists(stale):
                        os.remove(stale)
            self.search_button.configure(text="Cancel")
            self.search_entry.configure(state="disabled")
            self._clear_action_buttons()
            self._hide_files_list()
            self._hide_preview()
            # Use indeterminate for indexed searches (no file-by-file progress),
            # determinate for direct file scanning
            is_indexed = self.index_search_var.get() == "on"
            if is_indexed:
                self.progress_bar.configure(mode="indeterminate")
                self.progress_bar.start()
            else:
                self.progress_bar.configure(mode="determinate")
                self.progress_bar.set(0)
            self.progress_bar.grid(
                row=7, column=0, columnspan=3, padx=15, pady=(10, 0), sticky="ew"
            )
            self.status_label.configure(text="Searching...", text_color=("gray30", "gray70"))
            self.search_start_time = time.time()
            self._start_elapsed_timer()

            self.search_thread = threading.Thread(
                target=self._run_search, args=(cmd, folder), daemon=True
            )
            self.search_thread.start()

        def _start_elapsed_timer(self):
            self._update_elapsed()

        def _update_elapsed(self):
            if self.process is None and self.search_start_time is None:
                return
            if self.search_start_time is not None:
                elapsed = time.time() - self.search_start_time
                self.status_label.configure(text=f"Searching... ({elapsed:.0f}s)")
            self.elapsed_timer_id = self.after(1000, self._update_elapsed)

        def _run_search(self, cmd, folder):
            import re as _re
            try:
                self.process = subprocess.Popen(
                    cmd,
                    cwd=folder,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
                stdout_lines = []
                current_line = []
                progress_re = _re.compile(r'(\d+)/(\d+)\s')
                while True:
                    byte = self.process.stdout.read(1)
                    if not byte:
                        break
                    if byte == b'\r':
                        # Carriage return — parse progress from current line
                        line = b''.join(current_line).decode('utf-8', errors='replace')
                        m = progress_re.search(line)
                        if m:
                            done = int(m.group(1))
                            total = int(m.group(2))
                            if total > 0:
                                self.after(0, self._update_search_progress, done, total)
                        current_line = []
                    elif byte == b'\n':
                        stdout_lines.append(b''.join(current_line).decode('utf-8', errors='replace'))
                        current_line = []
                    else:
                        current_line.append(byte)
                if current_line:
                    stdout_lines.append(b''.join(current_line).decode('utf-8', errors='replace'))
                stdout = '\n'.join(stdout_lines)
                self.process.wait()
                returncode = self.process.returncode
            except Exception:
                stdout = ""
                returncode = -1
            finally:
                self.process = None

            self.after(0, self._search_finished, stdout, returncode)

        def _show_preview(self, stdout):
            """Populate the results preview pane from search output."""
            import re as _re
            self.preview_text.configure(state="normal")
            self.preview_text.delete("1.0", "end")

            # Parse the results file for cleaner output
            results_path = None
            if self.results_dir:
                suffix = f"_{self._last_ts_suffix}" if getattr(self, '_last_ts_suffix', '') else ""
                results_path = os.path.join(self.results_dir, f"docsearch_results{suffix}.txt")

            lines_added = 0
            max_preview_lines = 500  # Cap to keep the GUI responsive

            if results_path and os.path.exists(results_path):
                in_results = False
                with open(results_path, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.rstrip("\n")
                        if line == "Results:":
                            in_results = True
                            continue
                        if not in_results:
                            continue
                        if lines_added >= max_preview_lines:
                            self.preview_text.insert("end", f"\n... (showing first {max_preview_lines} lines — open the report for full results)\n")
                            break
                        if line.startswith("Document:"):
                            self.preview_text.insert("end", "\n")
                            self.preview_text.insert("end", line + "\n", "filename")
                        elif line.startswith("(") and line.endswith(")"):
                            # Directory path
                            self.preview_text.insert("end", line + "\n", "line_num")
                        elif line.startswith("Files WITHOUT matches:"):
                            self.preview_text.insert("end", line + "\n", "filename")
                        elif "**" in line:
                            # Line with highlighted matches — render highlights
                            parts = _re.split(r'(\*\*.*?\*\*)', line)
                            for part in parts:
                                if part.startswith("**") and part.endswith("**"):
                                    self.preview_text.insert("end", part[2:-2], "match")
                                else:
                                    self.preview_text.insert("end", part)
                            self.preview_text.insert("end", "\n")
                        else:
                            self.preview_text.insert("end", line + "\n")
                        lines_added += 1

            if lines_added == 0:
                self.preview_text.insert("end", "(No results to preview)")

            self.preview_text.configure(state="disabled")
            self.preview_text.see("1.0")

            # Update count label
            match_count = len(self.matched_files)
            if self._inverse_results:
                self._preview_count_label.configure(text=f"{match_count} file(s) without matches")
            else:
                total_matches = sum(c for _, _, c in self.matched_files)
                self._preview_count_label.configure(text=f"{total_matches} match(es) in {match_count} file(s)")

            # Show the preview frame
            self.preview_frame.grid(
                row=8, column=0, columnspan=3, padx=15, pady=(5, 0), sticky="nsew"
            )

        def _hide_preview(self):
            """Hide the results preview pane."""
            self.preview_frame.grid_remove()

        def _update_search_progress(self, done, total):
            """Update the determinate progress bar during search."""
            pct = done / total if total > 0 else 0
            self.progress_bar.set(pct)
            if self.search_start_time is not None:
                elapsed = time.time() - self.search_start_time
                self.status_label.configure(
                    text=f"Searching... {done}/{total} files ({elapsed:.0f}s)"
                )

        def _search_finished(self, stdout, returncode):
            try:
                self.progress_bar.stop()
            except Exception:
                pass
            self.progress_bar.grid_remove()
            self.search_start_time = None
            if self.elapsed_timer_id:
                self.after_cancel(self.elapsed_timer_id)
                self.elapsed_timer_id = None

            self.search_button.configure(text="Search")
            self.search_entry.configure(state="normal")

            if returncode == -1:
                self._show_error("Search process failed to start.")
                return

            summary = _parse_summary_text(stdout)

            if returncode == 0:
                self.status_label.configure(
                    text=summary or "Search complete. Matches found.",
                    text_color=("gray30", "gray70"),
                    font=ctk.CTkFont(size=13),
                )
                # Post-search save (-s) if user filled in "Save as" field
                save_name = self.save_name_entry.get().strip()
                if save_name:
                    save_cmd = [sys.executable, "-m", "docsearch", "-s", save_name]
                    try:
                        result = subprocess.run(save_cmd, cwd=self.results_dir, capture_output=True, text=True)
                        if result.returncode != 0:
                            self._show_error(f"Save failed: {result.stdout.strip() or 'unknown error'}")
                            return
                    except Exception as e:
                        self._show_error(f"Save failed: {e}")
                        return
                # Populate file list for the popup button
                ts = getattr(self, '_last_ts_suffix', '')
                results_fn = f"docsearch_results_{ts}.txt" if ts else "docsearch_results.txt"
                self._inverse_results = self.inverse_var.get() == "on"
                if self._inverse_results:
                    self.matched_files = _parse_inverse_files(self.results_dir, results_fn)
                else:
                    self.matched_files = _parse_matched_files(self.results_dir, results_fn)
                self._show_action_buttons(inverse=self._inverse_results)
                self._show_preview(stdout)
            elif returncode == 1:
                self.status_label.configure(
                    text=summary or "Search complete. No matches found.",
                    text_color=("gray30", "gray70"),
                    font=ctk.CTkFont(size=13),
                )
                self._show_action_buttons()
            elif returncode == 2:
                error_msg = stdout.strip().split("\n")[-1] if stdout.strip() else "Invalid input."
                self._show_error(error_msg)
                self._show_action_buttons()
            else:
                self.status_label.configure(
                    text="Search was cancelled.", text_color=("gray30", "gray70"),
                    font=ctk.CTkFont(size=13),
                )

            # Resume auto-refresh schedule if active
            self._reschedule_refresh()

        def _show_action_buttons(self, inverse=False):
            """Show Matched Files and View Report buttons."""
            self._clear_action_buttons()

            has_matched = bool(self.matched_files)

            # Check which report formats exist
            report_formats = {}
            if self.results_dir:
                suffix = f"_{self._last_ts_suffix}" if getattr(self, '_last_ts_suffix', '') else ""
                for fmt in ("txt", "docx", "csv", "json"):
                    path = os.path.join(self.results_dir, f"docsearch_results{suffix}.{fmt}")
                    report_formats[fmt] = os.path.exists(path)

            has_any_report = any(report_formats.values())

            if not has_any_report and not has_matched:
                return

            col = 0
            if has_matched:
                if inverse:
                    label = f"Files Without Matches ({len(self.matched_files)})"
                else:
                    label = f"Matched Files ({len(self.matched_files)})"
                self.matched_files_button.configure(text=label)
                self.matched_files_button.grid(
                    row=9, column=col, padx=(15, 5), pady=(5, 45), sticky="w"
                )
                col += 1
            if has_any_report:
                # Pack only the buttons for formats that exist
                for fmt, btn in [
                    ("txt", self.report_btn_txt),
                    ("docx", self.report_btn_docx),
                    ("csv", self.report_btn_csv),
                    ("json", self.report_btn_json),
                ]:
                    btn.pack(side="left", padx=(0, 2))
                    if report_formats.get(fmt):
                        btn.configure(
                            fg_color=("#3B8ED0", "#1F6AA5"),
                            hover_color=("#36719F", "#144870"),
                        )
                    else:
                        btn.configure(
                            fg_color="#CC3333",
                            hover_color="#AA2222",
                        )
                self.report_frame.grid(
                    row=9, column=col, padx=(10, 5), pady=(5, 45), sticky="w"
                )
                col += 1
        def open_error_log(self):
            folder = self.results_dir or self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a folder first.")
                return
            error_log_path = os.path.join(folder, "docsearch_errors.log")
            if not os.path.exists(error_log_path):
                self._show_error("No error log found in the selected folder.")
                return
            system = platform.system()
            if system == "Darwin":
                subprocess.Popen(["open", error_log_path])
            elif system == "Windows":
                os.startfile(error_log_path)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", error_log_path])

        def _clear_error_log(self):
            folder = self.results_dir or self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a folder first.")
                return
            error_log_path = os.path.join(folder, "docsearch_errors.log")
            if not os.path.exists(error_log_path):
                self.status_label.configure(text="No error log to clear.")
                return
            from tkinter import messagebox
            if messagebox.askyesno("Clear Error Log",
                                   f"Delete {os.path.basename(error_log_path)}?\n\nThis cannot be undone."):
                try:
                    os.remove(error_log_path)
                    self.status_label.configure(text="Error log cleared.")
                except OSError as e:
                    self._show_error(f"Could not delete error log: {e}")

        def _open_report_format(self, fmt):
            """Open the report file for the given format (txt, docx, csv, json)."""
            suffix = f"_{self._last_ts_suffix}" if getattr(self, '_last_ts_suffix', '') else ""
            path = os.path.join(self.results_dir, f"docsearch_results{suffix}.{fmt}")
            if not os.path.exists(path):
                self._show_error(f"Report file not found: {os.path.basename(path)}")
                return
            system = platform.system()
            if system == "Darwin":
                subprocess.Popen(["open", path])
            elif system == "Windows":
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", path])

        def _update_index_button_color(self):
            """Set Build Index(es) button blue if index exists, red if not.
            Also enable/disable the Search Using Index(es) checkbox and show last_updated.
            """
            folder = self.folder_entry.get().strip()
            if folder and os.path.isdir(folder):
                index_path = os.path.join(folder, ".docsearch.db")
                if os.path.exists(index_path):
                    self.build_index_button.configure(fg_color=("#3B8ED0", "#1F6AA5"), hover_color=("#36719F", "#144870"))
                    self.cb_index_search.configure(state="normal")
                    if self.index_search_var.get() == "off":
                        self.index_search_var.set("on")
                    # Show last_updated if no active refresh status
                    if hasattr(self, 'refresh_status_label') and not self._refresh_running:
                        self._show_last_updated(folder)
                    return
            self.build_index_button.configure(fg_color="#CC3333", hover_color="#AA2222")
            self.cb_index_search.configure(state="disabled")
            self.index_search_var.set("off")

        def _show_last_updated(self, folder):
            """Display the index last_updated timestamp on the refresh status label."""
            from docsearch.indexer import index_status
            try:
                status = index_status(folder)
                if status:
                    last = status.get("last_updated", status.get("created_at"))
                    if last:
                        self.refresh_status_label.configure(
                            text=f"Index last updated: {last}",
                            text_color=("gray50", "gray50"),
                        )
                        return
            except Exception:
                pass

        # ── Auto-Refresh Scheduler ────────────────────────────

        _REFRESH_INTERVALS = {"Off": 0, "5 min": 5, "15 min": 15, "30 min": 30, "1 hour": 60}

        def _on_refresh_interval_changed(self, value):
            """Handle auto-refresh interval selection change."""
            # Cancel any existing timer
            if self._refresh_timer_id is not None:
                self.after_cancel(self._refresh_timer_id)
                self._refresh_timer_id = None

            minutes = self._REFRESH_INTERVALS.get(value, 0)

            if minutes > 0:
                ms = minutes * 60 * 1000
                self._refresh_timer_id = self.after(ms, self._auto_refresh_tick)
                self.refresh_status_label.configure(
                    text=f"Next refresh in {minutes} min",
                    text_color=("gray50", "gray50"),
                )
            else:
                self.refresh_status_label.configure(text="")

        def _auto_refresh_tick(self):
            """Timer callback for auto-refresh."""
            self._refresh_timer_id = None

            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._reschedule_refresh()
                return
            if not os.path.exists(os.path.join(folder, ".docsearch.db")):
                self._reschedule_refresh()
                return
            if self.process is not None or self.search_start_time is not None:
                self._reschedule_refresh()
                return
            if self.build_index_button.cget("text") == "Building...":
                self._reschedule_refresh()
                return
            if self.suite_running:
                self._reschedule_refresh()
                return
            if self._refresh_running:
                self._reschedule_refresh()
                return

            self._refresh_running = True
            self.refresh_status_label.configure(
                text="Refreshing...", text_color=("gray50", "gray50"),
            )
            threading.Thread(target=self._run_auto_refresh, args=(folder,), daemon=True).start()

        def _run_auto_refresh(self, folder):
            """Background thread: run refresh_index and post result to main thread."""
            from docsearch.indexer import refresh_index
            try:
                result = refresh_index(folder, recursive=True, use_ocr=False)
            except Exception:
                result = None
            self.after(0, self._auto_refresh_finished, result)

        def _auto_refresh_finished(self, result):
            """Main-thread callback after auto-refresh completes."""
            self._refresh_running = False

            if result is not None:
                time_str = datetime.now().strftime("%H:%M")
                changes = result["added"] + result["updated"] + result["removed"]
                if changes > 0:
                    self.refresh_status_label.configure(
                        text=f"Refreshed at {time_str}: {result['added']} added, "
                             f"{result['updated']} updated, {result['removed']} removed",
                        text_color=("gray50", "gray50"),
                    )
                else:
                    self.refresh_status_label.configure(
                        text=f"Refreshed at {time_str}: no changes",
                        text_color=("gray50", "gray50"),
                    )
                self._update_index_button_color()
            else:
                self.refresh_status_label.configure(
                    text="Auto-refresh failed", text_color="red",
                )

            self._reschedule_refresh()

        def _reschedule_refresh(self):
            """Schedule the next auto-refresh tick based on current interval."""
            if self._refresh_timer_id is not None:
                return
            minutes = self._REFRESH_INTERVALS.get(self.refresh_interval_var.get(), 0)
            if minutes > 0:
                self._refresh_timer_id = self.after(minutes * 60 * 1000, self._auto_refresh_tick)

        # ── Suite Scheduling ───────────────────────────────────

        _SUITE_SCHEDULE_INTERVALS = {
            "Off": 0, "30 min": 30, "1 hour": 60,
            "4 hours": 240, "12 hours": 720, "24 hours": 1440,
        }

        def _on_suite_schedule_changed(self, value):
            """Handle suite schedule interval change."""
            if getattr(self, '_restoring_schedule', False):
                return
            from docsearch.collection import update_suite_field
            # Cancel any existing timer
            if self._suite_schedule_timer_id is not None:
                self.after_cancel(self._suite_schedule_timer_id)
                self._suite_schedule_timer_id = None

            minutes = self._SUITE_SCHEDULE_INTERVALS.get(value, 0)

            # Persist schedule to collection for selected suite
            suite_name = None
            folder = self.folder_entry.get().strip()
            if folder and hasattr(self, 'suite_selector'):
                sel = self.suite_selector.curselection()
                if sel:
                    suite_name = self.suite_selector.get(sel[0])
                    update_suite_field(folder, suite_name, "schedule", value)

            if minutes > 0 and suite_name:
                self._scheduled_suite_name = suite_name
                self._scheduled_suite_interval = value
                self._scheduled_next_run_time = time.time() + minutes * 60
                ms = minutes * 60 * 1000
                self._suite_schedule_timer_id = self.after(ms, self._suite_schedule_tick)
                self._start_countdown()
                self._update_autorun_name_label()
                self._update_last_run_label()
            else:
                # Clear schedule but preserve last run info for the suite
                prev_name = self._scheduled_suite_name or suite_name
                self._scheduled_suite_name = None
                self._scheduled_suite_interval = None
                self._scheduled_next_run_time = None
                self._stop_countdown()
                self._update_autorun_name_label()
                self._update_last_run_label(for_suite=prev_name)

        def _update_autorun_name_label(self):
            """Update the Auto-Run Suite label with the scheduled suite name."""
            if self._suite_label_available() and hasattr(self, 'suite_autorun_name_label'):
                name = self._scheduled_suite_name or "None"
                self.suite_autorun_name_label.configure(text=name)

        def _start_countdown(self):
            """Start the 1-minute countdown display timer."""
            self._stop_countdown()
            self._update_countdown()

        def _suite_label_available(self):
            """Check if suite schedule labels are visible (window is open)."""
            return (self._suite_window_open()
                    and hasattr(self, 'suite_next_run_label'))

        def _stop_countdown(self):
            """Stop the countdown display timer."""
            if self._countdown_timer_id is not None:
                self.after_cancel(self._countdown_timer_id)
                self._countdown_timer_id = None
            if self._suite_label_available():
                self.suite_next_run_label.configure(text="—")

        def _update_countdown(self):
            """Update the countdown label and reschedule in 1 minute."""
            self._countdown_timer_id = None
            if not self._scheduled_next_run_time:
                if self._suite_label_available():
                    self.suite_next_run_label.configure(text="—")
                return
            remaining = self._scheduled_next_run_time - time.time()
            if remaining <= 0:
                if self._suite_label_available():
                    self.suite_next_run_label.configure(text="Running...")
                return
            hours = int(remaining // 3600)
            mins = int((remaining % 3600) // 60)
            if hours > 0:
                text = f"{hours}h {mins}m"
            else:
                text = f"{mins}m" if mins > 0 else "<1m"
            if self._suite_label_available():
                self.suite_next_run_label.configure(text=text)
            # Keep ticking even if window is closed so it's correct when reopened
            self._countdown_timer_id = self.after(60000, self._update_countdown)

        def _suite_schedule_tick(self):
            """Timer callback for scheduled suite run."""
            self._suite_schedule_timer_id = None

            suite_name = self._scheduled_suite_name
            if not suite_name:
                return

            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._reschedule_suite()
                return
            if self.suite_running:
                self._reschedule_suite()
                return
            if self.process is not None or self.search_start_time is not None:
                self._reschedule_suite()
                return
            if self._refresh_running:
                self._reschedule_suite()
                return
            if self._suite_schedule_running:
                self._reschedule_suite()
                return

            self._suite_schedule_running = True
            self._suite_scheduled_run = True
            self._run_suite_by_name(folder, suite_name)

        def _log_autorun(self, folder, results, run_time, passed, total, verdict):
            """Log auto-run results to a persistent log file and auto-generate report."""
            if not folder:
                return
            report_dir = getattr(self, '_suite_output_dir', folder)
            suite_name = getattr(self, '_suite_name', 'unknown')

            # Auto-generate suite report
            if results:
                from docsearch.reporter import (write_suite_report_txt,
                                                write_suite_report_json,
                                                write_suite_report_docx)
                from docsearch import __version__
                safe_name = suite_name.replace(" ", "_").replace("/", "_")
                ts = f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                txt_path = os.path.join(report_dir, f"DO_NOT_SEARCH_docsearch_suite_{safe_name}{ts}.txt")
                json_path = os.path.join(report_dir, f"DO_NOT_SEARCH_docsearch_suite_{safe_name}{ts}.json")
                docx_path = os.path.join(report_dir, f"DO_NOT_SEARCH_docsearch_suite_{safe_name}{ts}.docx")
                write_suite_report_txt(
                    txt_path, suite_name, folder,
                    results, self._suite_start_time, self._suite_end_time,
                )
                write_suite_report_json(
                    json_path, suite_name, folder,
                    results, self._suite_start_time, self._suite_end_time,
                )
                write_suite_report_docx(
                    docx_path, suite_name, folder,
                    results, self._suite_start_time, self._suite_end_time,
                    version=__version__,
                    source_files=getattr(self, '_suite_source_files', None),
                )

            # Append to auto-run log
            log_path = os.path.join(report_dir, "DO_NOT_SEARCH_autorun_log.txt")
            try:
                new_file = not os.path.exists(log_path)
                empty_file = not new_file and os.path.getsize(log_path) == 0
                with open(log_path, "a", encoding="utf-8") as f:
                    if new_file:
                        f.write(f"Auto-Run History: {log_path}\n")
                        f.write("=" * len(f"Auto-Run History: {log_path}") + "\n")
                        f.write(f"(Recreated on {run_time} — previous history file was missing)\n\n")
                    elif empty_file:
                        f.write(f"Auto-Run History: {log_path}\n")
                        f.write("=" * len(f"Auto-Run History: {log_path}") + "\n\n")
                    f.write(f"[{run_time}] Suite: {suite_name} — {passed}/{total} passed — {verdict}\n")
                    for r in results:
                        status = "PASS" if r["passed"] else "FAIL"
                        pc = r.get("pass_criteria", {"op": ">=", "n": 1})
                        f.write(f"  [{status}] {r['name']} — {r['match_count']} match(es) (need {pc['op']} {pc['n']})\n")
                    f.write("\n")
            except OSError:
                pass

            # Send email alert if configured
            try:
                from docsearch.cli import _load_config
                from docsearch.email_alert import send_suite_alert
                cfg = _load_config()
                if cfg.get("smtp_host") and cfg.get("email_to"):
                    docx_report = docx_path if results else None
                    err = send_suite_alert(
                        cfg, suite_name, folder, results, run_time,
                        passed, total, verdict, report_path=docx_report,
                    )
                    if err:
                        # Log email failure to auto-run log
                        try:
                            with open(log_path, "a", encoding="utf-8") as f:
                                f.write(f"  [EMAIL ALERT] {err}\n\n")
                        except OSError:
                            pass
            except Exception:
                pass  # Never let email failure break the auto-run

        def _reschedule_suite(self):
            """Schedule the next suite run tick based on stored interval."""
            if self._suite_schedule_timer_id is not None:
                return
            if not self._scheduled_suite_interval:
                return
            minutes = self._SUITE_SCHEDULE_INTERVALS.get(self._scheduled_suite_interval, 0)
            if minutes > 0:
                self._scheduled_next_run_time = time.time() + minutes * 60
                self._suite_schedule_timer_id = self.after(minutes * 60 * 1000, self._suite_schedule_tick)
                self._start_countdown()

        def _resume_suite_schedule(self):
            """On startup or folder change, resume auto-run for any scheduled suite."""
            from docsearch.collection import load_collection
            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                return

            # Cancel any existing schedule
            if self._suite_schedule_timer_id is not None:
                self.after_cancel(self._suite_schedule_timer_id)
                self._suite_schedule_timer_id = None
            self._stop_countdown()

            data = load_collection(folder)
            for suite_name, suite in data.get("test_suites", {}).items():
                schedule = suite.get("schedule", "Off")
                minutes = self._SUITE_SCHEDULE_INTERVALS.get(schedule, 0)
                if minutes <= 0:
                    continue

                # Found a scheduled suite — calculate when next run is due
                last_run = suite.get("last_run_time")
                if last_run:
                    try:
                        last_dt = datetime.strptime(last_run, "%Y-%m-%d %H:%M:%S")
                        elapsed_since = (datetime.now() - last_dt).total_seconds()
                        remaining = (minutes * 60) - elapsed_since
                    except (ValueError, TypeError):
                        remaining = 0
                else:
                    remaining = 0

                # If overdue, run soon (10 seconds); otherwise schedule the remainder
                if remaining <= 0:
                    delay_ms = 10000
                    self._scheduled_next_run_time = time.time() + 10
                else:
                    delay_ms = int(remaining * 1000)
                    self._scheduled_next_run_time = time.time() + remaining

                self._scheduled_suite_name = suite_name
                self._scheduled_suite_interval = schedule
                self._suite_schedule_timer_id = self.after(delay_ms, self._suite_schedule_tick)
                self._start_countdown()

                # Update the schedule dropdown if suite window is open
                if hasattr(self, 'suite_schedule_var'):
                    self._restoring_schedule = True
                    self.suite_schedule_var.set(schedule)
                    self._restoring_schedule = False
                break  # Only one schedule at a time

        def _update_last_run_label(self, for_suite=None):
            """Update the last run label from the selected or scheduled suite."""
            if not self._suite_label_available():
                return
            from docsearch.collection import get_suite
            folder = self.folder_entry.get().strip()
            if not folder:
                self.suite_last_run_label.configure(text="Never")
                return

            # Try explicit name, then selected suite, then scheduled suite
            suite_name = for_suite
            if not suite_name and self._suite_window_open() and hasattr(self, 'suite_selector'):
                sel = self.suite_selector.curselection()
                if sel:
                    suite_name = self.suite_selector.get(sel[0])
            if not suite_name:
                suite_name = self._scheduled_suite_name

            if not suite_name:
                self.suite_last_run_label.configure(text="Never")
                return
            suite = get_suite(folder, suite_name)
            if suite and suite.get("last_run_time"):
                self.suite_last_run_label.configure(
                    text=f"{suite_name} \u2014 {suite['last_run_time']}"
                )
            else:
                self.suite_last_run_label.configure(text="Never")

        def build_index_action(self):
            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a valid folder.")
                return

            cmd = [sys.executable, "-m", "docsearch", "-q", "--index", "-r"]

            self.build_index_button.configure(state="disabled", text="Building...", width=120)
            self.status_label.configure(text="Building index...", text_color=("gray30", "gray70"))

            def _run():
                try:
                    result = subprocess.run(
                        cmd, cwd=folder, capture_output=True, text=True,
                    )
                    stdout = result.stdout
                    returncode = result.returncode
                except Exception:
                    stdout = ""
                    returncode = -1
                self.after(0, _finished, stdout, returncode)

            def _finished(stdout, returncode):
                self.build_index_button.configure(state="normal", text="Build Index(es)")
                self._update_index_button_color()
                if returncode == 0:
                    summary = ""
                    elapsed = ""
                    index_file = ""
                    for line in stdout.strip().split("\n"):
                        if line.startswith("Index built:"):
                            summary = line
                        elif line.startswith("Elapsed:"):
                            elapsed = line.strip().replace("Elapsed:", "").strip()
                        elif line.startswith("Index file:"):
                            index_file = line.strip()
                    display = summary or "Index built successfully."
                    if elapsed:
                        display += f", {elapsed}"
                    if index_file:
                        display += f"  ({index_file.replace('Index file:', '').strip()})"
                    self.status_label.configure(
                        text=display,
                        text_color=("gray30", "gray70"),
                    )
                else:
                    self._show_error("Index build failed. Check the error log.")

            threading.Thread(target=_run, daemon=True).start()

        def delete_index_action(self):
            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a valid folder.")
                return

            cmd = [sys.executable, "-m", "docsearch", "-q", "--index-clear"]
            try:
                result = subprocess.run(cmd, cwd=folder, capture_output=True, text=True)
                msg = result.stdout.strip()
                self.status_label.configure(
                    text=msg or "Index removed.",
                    text_color=("gray30", "gray70"),
                )
                self._update_index_button_color()
                self.refresh_interval_var.set("Off")
                self._on_refresh_interval_changed("Off")
            except Exception:
                self._show_error("Failed to delete index.")

        def index_status_action(self):
            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a valid folder.")
                return

            cmd = [sys.executable, "-m", "docsearch", "-q", "--index-status"]
            try:
                result = subprocess.run(cmd, cwd=folder, capture_output=True, text=True)
                stdout = result.stdout.strip()
            except Exception:
                self._show_error("Failed to get index status.")
                return

            if not stdout or "No index found" in stdout:
                self.status_label.configure(
                    text="No index found. Click Build Index(es) to create one.",
                    text_color=("gray30", "gray70"),
                )
                return

            import tkinter as tk
            status_win = tk.Toplevel(self)
            status_win.title("Index Status")
            status_win.resizable(True, True)
            line_count = stdout.count("\n") + 1
            max_line_len = max((len(line) for line in stdout.split("\n")), default=30)
            win_w = max(380, min(550, max_line_len * 9 + 40))
            win_h = max(220, min(400, line_count * 26 + 60))
            status_win.geometry(f"{win_w}x{win_h}")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - win_w) // 2
            y = self.winfo_rooty() + (self.winfo_height() - win_h) // 2
            status_win.geometry(f"+{x}+{y}")
            tk.Label(
                status_win, text=stdout, font=("TkDefaultFont", 12),
                justify="left", anchor="nw", padx=15, pady=15,
            ).pack(fill="both", expand=True)

        def about_index_action(self):
            import tkinter as tk
            about_win = tk.Toplevel(self)
            about_win.title("About Index")
            about_win.resizable(True, True)
            about_win.geometry("540x420")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 540) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 420) // 2
            about_win.geometry(f"+{x}+{y}")

            scrollbar = tk.Scrollbar(about_win)
            scrollbar.pack(side="right", fill="y")

            text = tk.Text(
                about_win, font=("TkDefaultFont", 12), wrap="word",
                padx=15, pady=15, borderwidth=0, highlightthickness=0,
                yscrollcommand=scrollbar.set,
            )
            text.tag_configure("bold", font=("TkDefaultFont", 12, "bold"))
            text.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=text.yview)

            sections = [
                ("Index Overview\n",
                 "docsearch can build an optional search index to speed up "
                 "repeated searches. Instead of opening and parsing every file "
                 "each time, the index stores extracted text in a small SQLite "
                 "database (.docsearch.db) so searches skip file I/O entirely.\n\n"),
                ("How It Works\n",
                 "When you click Build Index(es), docsearch reads every supported "
                 "file in the selected folder and all subfolders, extracts the "
                 "text, and stores it in a single .docsearch.db file in that "
                 "folder.\n\n"),
                ("Automatic Refresh\n",
                 "Each time you search with the index, docsearch automatically "
                 "checks for new, changed, or deleted files and updates the index "
                 "before returning results. You never need to manually rebuild.\n\n"),
                ("Identical Results\n",
                 "Indexed searches produce the exact same results as direct "
                 "searches. You can verify this by unchecking Search Using "
                 "Index(es) and comparing. Both methods use the same matching "
                 "logic \u2014 the index just skips the file-parsing step.\n\n"),
                ("The Index File\n",
                 "A single .docsearch.db file is created in the top-level "
                 "folder you selected. It contains text from that folder and "
                 "all subfolders. It is a hidden file (starts with a dot). "
                 "Use Cmd+Shift+. in Finder or 'ls -a' in Terminal to see it. "
                 "The index is typically 10\u201320% the size of your original "
                 "files.\n\n"),
                ("Managing Indexes\n",
                 "Use Delete Index(es) to remove the database at any time. "
                 "Use Index Status to see how many files and lines are indexed, "
                 "the database size, and when it was created."),
            ]
            for heading, body in sections:
                text.insert("end", heading, "bold")
                text.insert("end", body)
            text.configure(state="disabled")

        def _open_selected_file(self):
            selection = self.files_listbox.curselection()
            if not selection:
                return
            filepath, _, _ = self.matched_files[selection[0]]
            if not os.path.exists(filepath):
                self._show_error(f"File not found: {filepath}")
                return
            system = platform.system()
            if system == "Darwin":
                subprocess.Popen(["open", filepath])
            elif system == "Windows":
                os.startfile(filepath)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", filepath])

        def _hide_files_list(self):
            self.matched_files = []

        def _show_matched_files_popup(self):
            """Show a popup listing all matched files. Click a file to open it."""
            if not self.matched_files:
                return
            import tkinter as tk

            popup = tk.Toplevel(self)
            count = len(self.matched_files)
            if self._inverse_results:
                heading = f"Files Without Matches ({count})"
            else:
                heading = f"Matched Files ({count})"
            popup.title(heading)
            popup.resizable(True, True)
            win_h = max(200, min(500, count * 28 + 80))
            popup.geometry(f"500x{win_h}")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 500) // 2
            y = self.winfo_rooty() + (self.winfo_height() - win_h) // 2
            popup.geometry(f"+{x}+{y}")

            tk.Label(
                popup, text=heading,
                font=("TkDefaultFont", 13, "bold"),
            ).pack(pady=(10, 2))
            tk.Label(
                popup, text="Click a file to open it",
                font=("TkDefaultFont", 10), fg="gray",
            ).pack(pady=(0, 8))

            list_frame = tk.Frame(popup)
            list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side="right", fill="y")

            listbox = tk.Listbox(
                list_frame, font=("TkDefaultFont", 12),
                selectmode=tk.SINGLE, activestyle="none",
                bg="#2b2b2b", fg="white", selectbackground="#1f6aa5",
                highlightthickness=0, borderwidth=1, relief="sunken",
                yscrollcommand=scrollbar.set,
            )
            listbox.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=listbox.yview)

            for filepath, filename, match_count in self.matched_files:
                listbox.insert("end", f"{filename} ({match_count} match{'es' if match_count != 1 else ''})")

            def _on_click(event):
                selection = listbox.curselection()
                if not selection:
                    return
                filepath, _, _ = self.matched_files[selection[0]]
                if not os.path.exists(filepath):
                    self._show_error(f"File not found: {filepath}")
                    return
                system = platform.system()
                if system == "Darwin":
                    subprocess.Popen(["open", filepath])
                elif system == "Windows":
                    os.startfile(filepath)  # type: ignore[attr-defined]
                else:
                    subprocess.Popen(["xdg-open", filepath])

            listbox.bind("<Double-1>", _on_click)

            tk.Button(popup, text="Close", width=10, command=popup.destroy).pack(pady=(0, 10))

        def open_help(self):
            webbrowser.open("https://github.com/exbuf/docsearch#readme")

        def show_about(self):
            import tkinter as tk
            about_win = tk.Toplevel(self)
            about_win.title("About docsearch")
            about_win.resizable(False, False)
            about_win.geometry("300x140")
            # Center on parent
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 300) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 120) // 2
            about_win.geometry(f"+{x}+{y}")
            try:
                ver = pkg_version("docsearch")
            except Exception:
                ver = "unknown"
            tk.Label(about_win, text="docsearch", font=("TkDefaultFont", 16, "bold")).pack(pady=(15, 2))
            tk.Label(about_win, text=f"Version {ver}", font=("TkDefaultFont", 12)).pack()
            tk.Label(about_win, text="by Robert D. Schoening", font=("TkDefaultFont", 12)).pack(pady=(2, 2))
            tk.Label(about_win, text="MIT License", font=("TkDefaultFont", 11)).pack(pady=(0, 15))

        _TEXT_SIZE_SCALES = {
            "Small": 0.85,
            "Normal": 1.0,
            "Large": 1.2,
            "Extra Large": 1.4,
        }

        def _on_text_size_changed(self, value):
            """Scale all GUI widgets and auto-save the setting."""
            scale = self._TEXT_SIZE_SCALES.get(value, 1.0)
            ctk.set_widget_scaling(scale)
            # Auto-save so it persists between app invocations
            try:
                from docsearch.cli import _load_config, _save_config
                cfg = _load_config()
                if value == "Normal":
                    cfg.pop("text_size", None)
                else:
                    cfg["text_size"] = value
                _save_config(cfg)
            except Exception:
                pass

        def _inspect_settings(self):
            """Show the current saved settings from ~/.docsearchrc in a read-only popup."""
            from docsearch.cli import _config_path
            import tkinter as tk

            path = _config_path()
            if os.path.exists(path):
                with open(path, "r") as f:
                    content = f.read().strip()
            else:
                content = "(No settings file found)"

            win = tk.Toplevel(self)
            win.title("Saved Settings")
            win.resizable(True, True)
            line_count = content.count("\n") + 1
            max_line_len = max((len(line) for line in content.split("\n")), default=30)
            win_w = max(380, min(550, max_line_len * 9 + 40))
            win_h = max(200, min(500, line_count * 26 + 80))
            win.geometry(f"{win_w}x{win_h}")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - win_w) // 2
            y = self.winfo_rooty() + (self.winfo_height() - win_h) // 2
            win.geometry(f"+{x}+{y}")

            tk.Label(
                win, text="Saved Settings (read-only)",
                font=("TkDefaultFont", 13, "bold"),
            ).pack(pady=(10, 2))
            tk.Label(
                win, text=path,
                font=("TkDefaultFont", 10), fg="gray",
            ).pack(pady=(0, 8))
            tk.Label(
                win, text=content, font=("TkDefaultFont", 12),
                justify="left", anchor="nw", padx=15, pady=10,
            ).pack(fill="both", expand=True)
            tk.Button(win, text="Close", width=10, command=win.destroy).pack(pady=(0, 10))

        def _save_current_settings(self):
            """Save current Advanced Options state to ~/.docsearchrc."""
            from docsearch.cli import _save_config, _config_path

            settings = {}
            # Boolean settings
            if self.recursive_var.get() == "on":
                settings["recursive"] = True
            if self.and_mode_var.get() == "on":
                settings["match_all"] = True
            if self.fuzzy_var.get() == "on":
                settings["fuzzy"] = True
            if self.wildcard_var.get() == "on":
                settings["wildcard"] = True
            if self.regex_var.get() == "on":
                settings["regex"] = True
            if self.ocr_var.get() == "on":
                settings["ocr"] = True
            if self.index_search_var.get() == "on":
                settings["index_search"] = True
            if self.output_csv_var.get() == "on":
                settings["output_csv"] = True
            if self.output_json_var.get() == "on":
                settings["output_json"] = True
            if self.inverse_var.get() == "on":
                settings["inverse"] = True
            if self.expression_var.get() == "on":
                settings["expression"] = True
            if self.whole_word_var.get() == "on":
                settings["whole_word"] = True
            settings["timestamp"] = (self.timestamp_var.get() == "on")
            # Integer settings
            cores_val = self.cores_entry.get().strip()
            if cores_val:
                try:
                    n = int(cores_val)
                    if n >= 1:
                        settings["cores"] = n
                except ValueError:
                    pass
            cb = self.context_before_entry.get().strip()
            if cb:
                try:
                    n = int(cb)
                    if n >= 1:
                        settings["context_before"] = n
                except ValueError:
                    pass
            ca = self.context_after_entry.get().strip()
            if ca:
                try:
                    n = int(ca)
                    if n >= 1:
                        settings["context_after"] = n
                except ValueError:
                    pass
            prox = self.proximity_entry.get().strip()
            if prox:
                try:
                    n = int(prox)
                    if n >= 1:
                        settings["proximity"] = n
                except ValueError:
                    pass
            mm = self.max_matches_entry.get().strip()
            if mm:
                try:
                    n = int(mm)
                    if n >= 0:
                        settings["max_matches"] = n
                except ValueError:
                    pass
            # String settings
            ft = self.file_types_entry.get().strip()
            if ft:
                settings["file_types"] = ft
            search = self.search_entry.get().strip()
            if search:
                settings["search_terms"] = search
            folder = self.folder_entry.get().strip()
            if folder:
                settings["folder"] = folder
            exclude = self.exclude_entry.get().strip()
            if exclude:
                settings["exclude"] = exclude
            specific = self.specific_files_entry.get().strip()
            if specific:
                settings["specific_files"] = specific
            save_name = self.save_name_entry.get().strip()
            if save_name:
                settings["save_name"] = save_name
            append_name = self.append_name_entry.get().strip()
            if append_name:
                settings["append_name"] = append_name
            output_dir = self.output_dir_entry.get().strip()
            if output_dir:
                settings["output_dir"] = output_dir
            suite_od = ""
            if hasattr(self, 'suite_output_dir_entry'):
                try:
                    suite_od = self.suite_output_dir_entry.get().strip()
                except Exception:
                    pass
            if not suite_od:
                suite_od = getattr(self, '_saved_suite_output_dir', '')
            if suite_od:
                settings["suite_output_dir"] = suite_od
            range_val = self.range_entry.get().strip()
            if range_val:
                settings["range"] = range_val
            refresh_val = self.refresh_interval_var.get()
            if refresh_val != "Off":
                settings["refresh_interval"] = refresh_val
            text_size_val = self._text_size_var.get()
            if text_size_val != "Normal":
                settings["text_size"] = text_size_val

            if settings:
                _save_config(settings)
            else:
                path = _config_path()
                if os.path.exists(path):
                    os.remove(path)
            self.status_label.configure(
                text="Settings saved to ~/.docsearchrc",
                text_color=("gray30", "gray70"),
                font=ctk.CTkFont(size=13),
            )

        def _load_saved_settings(self):
            """Load saved settings from ~/.docsearchrc and apply to GUI."""
            from docsearch.cli import _load_config

            config = _load_config()
            # Set booleans — reset to off if not in config
            self.recursive_var.set("on" if config.get("recursive") else "off")
            self.and_mode_var.set("on" if config.get("match_all") else "off")
            self.fuzzy_var.set("on" if config.get("fuzzy") else "off")
            self.wildcard_var.set("on" if config.get("wildcard") else "off")
            self.regex_var.set("on" if config.get("regex") else "off")
            self.ocr_var.set("on" if config.get("ocr") else "off")
            self.index_search_var.set("on" if config.get("index_search") else "off")
            self.output_csv_var.set("on" if config.get("output_csv") else "off")
            self.output_json_var.set("on" if config.get("output_json") else "off")
            self.inverse_var.set("on" if config.get("inverse") else "off")
            self.expression_var.set("on" if config.get("expression") else "off")
            self.whole_word_var.set("on" if config.get("whole_word") else "off")
            self.timestamp_var.set("on" if config.get("timestamp", True) else "off")
            # Clear and set entry fields
            self.cores_entry.delete(0, "end")
            if "cores" in config:
                self.cores_entry.insert(0, str(config["cores"]))
            self.context_before_entry.delete(0, "end")
            if "context_before" in config:
                self.context_before_entry.insert(0, str(config["context_before"]))
            self.context_after_entry.delete(0, "end")
            if "context_after" in config:
                self.context_after_entry.insert(0, str(config["context_after"]))
            self.proximity_entry.delete(0, "end")
            if "proximity" in config:
                self.proximity_entry.insert(0, str(config["proximity"]))
            self.max_matches_entry.delete(0, "end")
            if "max_matches" in config:
                self.max_matches_entry.insert(0, str(config["max_matches"]))
            else:
                self.max_matches_entry.insert(0, "1000")
            self.file_types_entry.delete(0, "end")
            if "file_types" in config:
                self.file_types_entry.insert(0, config["file_types"])
            self.search_entry.delete(0, "end")
            if "search_terms" in config:
                self.search_entry.insert(0, config["search_terms"])
            self.folder_entry.delete(0, "end")
            if "folder" in config:
                self.folder_entry.insert(0, config["folder"])
            self.exclude_entry.delete(0, "end")
            if "exclude" in config:
                self.exclude_entry.insert(0, config["exclude"])
            self.specific_files_entry.delete(0, "end")
            if "specific_files" in config:
                self.specific_files_entry.insert(0, config["specific_files"])
            self.save_name_entry.delete(0, "end")
            if "save_name" in config:
                self.save_name_entry.insert(0, config["save_name"])
            self.append_name_entry.delete(0, "end")
            if "append_name" in config:
                self.append_name_entry.insert(0, config["append_name"])
            self.output_dir_entry.delete(0, "end")
            if "output_dir" in config:
                self.output_dir_entry.insert(0, config["output_dir"])
            self._saved_suite_output_dir = config.get("suite_output_dir", "")
            self.range_entry.delete(0, "end")
            if "range" in config:
                self.range_entry.insert(0, config["range"])
            self._update_index_button_color()
            # Restore auto-refresh interval
            refresh_interval = config.get("refresh_interval", "Off")
            if refresh_interval not in self._REFRESH_INTERVALS:
                refresh_interval = "Off"
            self.refresh_interval_var.set(refresh_interval)
            self._on_refresh_interval_changed(refresh_interval)
            # Restore text size
            text_size = config.get("text_size", "Normal")
            if text_size not in self._TEXT_SIZE_SCALES:
                text_size = "Normal"
            self._text_size_var.set(text_size)
            self._on_text_size_changed(text_size)

        def reset_form(self):
            """Reset all fields to their defaults."""
            self.search_entry.delete(0, "end")
            self.and_mode_var.set("off")
            self.recursive_var.set("off")
            self.fuzzy_var.set("off")
            self.wildcard_var.set("off")
            self.ocr_var.set("off")
            self.regex_var.set("off")
            self.exclude_entry.delete(0, "end")
            self.file_types_entry.delete(0, "end")
            self.proximity_entry.delete(0, "end")
            self.context_before_entry.delete(0, "end")
            self.context_after_entry.delete(0, "end")
            self.cores_entry.delete(0, "end")
            self.cores_entry.insert(0, str(self._default_cores))
            self.max_matches_entry.delete(0, "end")
            self.max_matches_entry.insert(0, "1000")
            self.specific_files_entry.delete(0, "end")
            self.save_name_entry.delete(0, "end")
            self.append_name_entry.delete(0, "end")
            self.output_csv_var.set("off")
            self.output_json_var.set("off")
            self.index_search_var.set("off")
            self.inverse_var.set("off")
            self.expression_var.set("off")
            self.whole_word_var.set("off")
            self.timestamp_var.set("off")
            self.output_dir_entry.delete(0, "end")
            self.range_entry.delete(0, "end")
            self.refresh_interval_var.set("Off")
            self._on_refresh_interval_changed("Off")
            if hasattr(self, 'suite_schedule_var'):
                self.suite_schedule_var.set("Off")
                self._on_suite_schedule_changed("Off")
                self._on_suite_schedule_changed("Off")
            self.search_entry.configure(placeholder_text="Enter search terms...")
            self.status_label.configure(
                text="", font=ctk.CTkFont(size=13), text_color=("gray30", "gray70")
            )
            self._clear_action_buttons()
            self._hide_files_list()

        def _clear_action_buttons(self):
            """Hide all action buttons."""
            self.matched_files_button.grid_remove()
            self.report_frame.grid_remove()
            self.report_btn_txt.pack_forget()
            self.report_btn_docx.pack_forget()
            self.report_btn_csv.pack_forget()
            self.report_btn_json.pack_forget()

        def _show_error(self, message):
            self.status_label.configure(
                text=message, text_color="red", font=ctk.CTkFont(size=13, weight="bold")
            )
            self.bell()
            messagebox.showerror("Error", message)

        # ── Search Collections ─────────────────────────────────

        def _collect_gui_params(self):
            """Collect current search parameters from GUI widgets into a dict."""
            return {
                "search_text": self.search_entry.get().strip(),
                "and_mode": self.and_mode_var.get() == "on",
                "recursive": self.recursive_var.get() == "on",
                "fuzzy": self.fuzzy_var.get() == "on",
                "wildcard": self.wildcard_var.get() == "on",
                "ocr": self.ocr_var.get() == "on",
                "regex": self.regex_var.get() == "on",
                "exclude": self.exclude_entry.get().strip(),
                "file_types": self.file_types_entry.get().strip(),
                "proximity": self.proximity_entry.get().strip(),
                "context_before": self.context_before_entry.get().strip(),
                "context_after": self.context_after_entry.get().strip(),
                "cores": self.cores_entry.get().strip(),
                "max_matches": self.max_matches_entry.get().strip(),
                "specific_files": self.specific_files_entry.get().strip(),
                "index_search": self.index_search_var.get() == "on",
                "inverse": self.inverse_var.get() == "on",
                "expression": self.expression_var.get() == "on",
                "whole_word": self.whole_word_var.get() == "on",
                "output_csv": self.output_csv_var.get() == "on",
                "output_json": self.output_json_var.get() == "on",
                "range_filters": self.range_entry.get().strip(),
                "append_name": self.append_name_entry.get().strip(),
                "save_name": self.save_name_entry.get().strip(),
                "timestamp": self.timestamp_var.get() == "on",
            }

        def _apply_params_to_gui(self, params):
            """Set GUI widgets to match a saved search's parameter dict."""
            self.search_entry.delete(0, "end")
            self.search_entry.insert(0, params.get("search_text", ""))
            self.and_mode_var.set("on" if params.get("and_mode") else "off")
            self.recursive_var.set("on" if params.get("recursive") else "off")
            self.fuzzy_var.set("on" if params.get("fuzzy") else "off")
            self.wildcard_var.set("on" if params.get("wildcard") else "off")
            self.ocr_var.set("on" if params.get("ocr") else "off")
            self.regex_var.set("on" if params.get("regex") else "off")
            self.exclude_entry.delete(0, "end")
            self.exclude_entry.insert(0, params.get("exclude", ""))
            self.file_types_entry.delete(0, "end")
            self.file_types_entry.insert(0, params.get("file_types", ""))
            self.proximity_entry.delete(0, "end")
            self.proximity_entry.insert(0, params.get("proximity", ""))
            self.context_before_entry.delete(0, "end")
            self.context_before_entry.insert(0, params.get("context_before", ""))
            self.context_after_entry.delete(0, "end")
            self.context_after_entry.insert(0, params.get("context_after", ""))
            self.cores_entry.delete(0, "end")
            self.cores_entry.insert(0, params.get("cores", "") or str(self._default_cores))
            self.max_matches_entry.delete(0, "end")
            self.max_matches_entry.insert(0, params.get("max_matches", "") or "1000")
            self.specific_files_entry.delete(0, "end")
            self.specific_files_entry.insert(0, params.get("specific_files", ""))
            self.index_search_var.set("on" if params.get("index_search") else "off")
            self.inverse_var.set("on" if params.get("inverse") else "off")
            self.expression_var.set("on" if params.get("expression") else "off")
            self.whole_word_var.set("on" if params.get("whole_word") else "off")
            if params.get("expression"):
                self.search_entry.configure(placeholder_text='e.g. (budget OR revenue) AND NOT draft')
            else:
                self.search_entry.configure(placeholder_text="Enter search terms...")
            self.output_csv_var.set("on" if params.get("output_csv") else "off")
            self.output_json_var.set("on" if params.get("output_json") else "off")
            self.range_entry.delete(0, "end")
            self.range_entry.insert(0, params.get("range_filters", ""))
            self.append_name_entry.delete(0, "end")
            self.append_name_entry.insert(0, params.get("append_name", ""))
            self.save_name_entry.delete(0, "end")
            self.save_name_entry.insert(0, params.get("save_name", ""))
            self.timestamp_var.set("on" if params.get("timestamp") else "off")

        def _save_to_collection(self):
            """Save current search config to the folder's collection file."""
            import tkinter as tk
            from docsearch.collection import add_saved_search, load_collection

            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Select a valid folder before saving.")
                return
            search_text = self.search_entry.get().strip()
            if not search_text:
                self._show_error("Enter search terms before saving.")
                return

            # Prompt for a name
            dialog = tk.Toplevel(self)
            dialog.title("Save to Collection")
            dialog.resizable(False, False)
            w, h = 350, 120
            x = self.winfo_rootx() + (self.winfo_width() - w) // 2
            y = self.winfo_rooty() + (self.winfo_height() - h) // 2
            dialog.geometry(f"{w}x{h}+{x}+{y}")
            dialog.transient(self)
            dialog.grab_set()

            tk.Label(dialog, text="Search name:", font=("TkDefaultFont", 13)).pack(
                padx=15, pady=(15, 5), anchor="w"
            )
            name_entry = tk.Entry(dialog, font=("TkDefaultFont", 13))
            name_entry.pack(padx=15, fill="x")
            name_entry.focus_set()

            def do_save(_event=None):
                name = name_entry.get().strip()
                print(f"[DEBUG] do_save called, name='{name}', folder='{folder}'")
                if not name:
                    return
                try:
                    existing = load_collection(folder)
                    if name in existing["saved_searches"]:
                        from tkinter import messagebox as mb
                        if not mb.askyesno("Overwrite?", f"'{name}' already exists. Overwrite?", parent=dialog):
                            return
                    params = self._collect_gui_params()
                    add_saved_search(folder, name, params)
                    dialog.destroy()
                    self.status_label.configure(
                        text=f"Search '{name}' saved to collection.",
                        text_color=("gray30", "gray70"), font=ctk.CTkFont(size=13),
                    )
                    if self.suite_window is not None and self.suite_visible:
                        self._refresh_suite_panel()
                    self._refresh_load_search_menu()
                except Exception as exc:
                    self._show_error(f"Failed to save search: {exc}")

            name_entry.bind("<Return>", do_save)
            btn_frame = tk.Frame(dialog)
            btn_frame.pack(pady=(10, 10))
            tk.Button(btn_frame, text="Save", width=10, command=do_save).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Cancel", width=10, command=dialog.destroy).pack(side="left", padx=5)

        # ── Search Wizard ────────────────────────────────────────

        def _open_search_wizard(self):
            """Open the Search Wizard popup for building regex patterns."""
            import tkinter as tk
            from tkinter import ttk
            from docsearch.wizard_patterns import WIZARD_PATTERNS, WIZARD_CATEGORY_ORDER

            # Initialize persistent state on first open
            if not hasattr(self, "_wizard_state"):
                self._wizard_state = {
                    "category": WIZARD_CATEGORY_ORDER[0],
                    "mode": "OR",
                    "custom": "",
                    "checked": {},  # category -> set of checked labels
                }

            wiz = tk.Toplevel(self)
            wiz.title("Search Wizard")
            wiz.resizable(True, True)
            wiz.geometry("560x640")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 560) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 640) // 2
            wiz.geometry(f"+{x}+{y}")

            tk.Label(
                wiz, text="Search Wizard",
                font=("TkDefaultFont", 15, "bold"),
            ).pack(pady=(10, 2))
            tk.Label(
                wiz, text="Select a category and check the patterns to include.",
                font=("TkDefaultFont", 11), fg="gray",
            ).pack(pady=(0, 2))
            tk.Label(
                wiz,
                text="Note: The wizard enables regex mode. If you manually type terms with\n"
                     "special characters ( . + ( ) [ ] etc.), escape them with \\ (e.g., cost\\+fees).\n"
                     "Plain words like \"budget\" need no escaping.",
                font=("TkDefaultFont", 10), fg="gray", justify="left",
            ).pack(padx=15, pady=(0, 8), anchor="w")

            # Category dropdown — restore previous selection
            cat_frame = tk.Frame(wiz)
            cat_frame.pack(fill="x", padx=15, pady=(0, 5))
            tk.Label(cat_frame, text="Category:", font=("TkDefaultFont", 12)).pack(side="left")
            cat_var = tk.StringVar(value=self._wizard_state["category"])
            cat_combo = ttk.Combobox(
                cat_frame, textvariable=cat_var, values=WIZARD_CATEGORY_ORDER,
                state="readonly", width=28, font=("TkDefaultFont", 12),
            )
            cat_combo.pack(side="left", padx=(8, 0))

            # Match mode selector (OR / AND) — restore previous selection
            mode_frame = tk.Frame(wiz)
            mode_frame.pack(fill="x", padx=15, pady=(0, 5))
            tk.Label(mode_frame, text="Match mode:", font=("TkDefaultFont", 12)).pack(side="left")
            mode_var = tk.StringVar(value=self._wizard_state["mode"])
            tk.Radiobutton(
                mode_frame, text="OR  (match any pattern)",
                variable=mode_var, value="OR", font=("TkDefaultFont", 11),
                command=lambda: _update_preview(),
            ).pack(side="left", padx=(10, 5))
            tk.Radiobutton(
                mode_frame, text="AND  (match all patterns)",
                variable=mode_var, value="AND", font=("TkDefaultFont", 11),
                command=lambda: _update_preview(),
            ).pack(side="left", padx=(5, 0))

            # Checkbox area
            check_frame = tk.Frame(wiz)
            check_frame.pack(fill="both", expand=True, padx=15, pady=(0, 5))

            canvas = tk.Canvas(check_frame, highlightthickness=0)
            scrollbar = tk.Scrollbar(check_frame, orient="vertical", command=canvas.yview)
            inner_frame = tk.Frame(canvas)

            inner_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
            )
            canvas.create_window((0, 0), window=inner_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # State: list of (BooleanVar, label, regex) for current category
            check_vars = []

            def _save_checked():
                """Save which labels are checked for the current category."""
                category = cat_var.get()
                checked = {label for var, label, _ in check_vars if var.get()}
                self._wizard_state["checked"][category] = checked

            def _update_preview(*_args):
                _save_checked()
                self._wizard_state["mode"] = mode_var.get()
                self._wizard_state["custom"] = custom_entry.get().strip()
                selected = [(label, regex) for var, label, regex in check_vars if var.get()]
                # Include custom regex if any
                custom = custom_entry.get().strip()
                if custom:
                    selected.append(("Custom", custom))
                if mode_var.get() == "AND":
                    # Each pattern as a separate quoted term
                    parts = [f'"{regex}"' for _, regex in selected]
                    combined = " ".join(parts)
                else:
                    combined = _build_wizard_regex(selected)
                preview_text.configure(state="normal")
                preview_text.delete("1.0", "end")
                preview_text.insert("1.0", combined)
                preview_text.configure(state="disabled")

            def _load_category(*_args):
                # Save state of outgoing category before switching
                if check_vars:
                    _save_checked()

                # Clear existing checkboxes
                for widget in inner_frame.winfo_children():
                    widget.destroy()
                check_vars.clear()

                category = cat_var.get()
                self._wizard_state["category"] = category
                patterns = WIZARD_PATTERNS.get(category, [])
                saved_checked = self._wizard_state["checked"].get(category, set())

                for i, (label, regex) in enumerate(patterns):
                    var = tk.BooleanVar(value=label in saved_checked)
                    cb = tk.Checkbutton(
                        inner_frame, text=label, variable=var,
                        font=("TkDefaultFont", 12), anchor="w",
                        command=_update_preview,
                    )
                    cb.grid(row=i, column=0, sticky="w", padx=(5, 10), pady=2)
                    Tooltip(cb, f"Regex: {regex}")
                    check_vars.append((var, label, regex))

                _update_preview()

            cat_combo.bind("<<ComboboxSelected>>", _load_category)

            # Custom regex entry — restore previous value
            custom_frame = tk.Frame(wiz)
            custom_frame.pack(fill="x", padx=15, pady=(0, 5))
            tk.Label(custom_frame, text="Custom regex:", font=("TkDefaultFont", 12)).pack(side="left")
            custom_entry = tk.Entry(custom_frame, font=("TkDefaultFont", 12), width=35)
            custom_entry.pack(side="left", padx=(8, 0), fill="x", expand=True)
            custom_entry.insert(0, self._wizard_state["custom"])
            custom_entry.bind("<KeyRelease>", _update_preview)

            # Preview area
            preview_label = tk.Label(wiz, text="Preview:", font=("TkDefaultFont", 12), anchor="w")
            preview_label.pack(fill="x", padx=15, pady=(0, 2))
            preview_text = tk.Text(
                wiz, font=("TkDefaultFont", 11), height=3, wrap="word",
                borderwidth=1, relief="sunken", state="disabled",
            )
            preview_text.pack(fill="x", padx=15, pady=(0, 8))

            # Buttons
            btn_frame = tk.Frame(wiz)
            btn_frame.pack(fill="x", padx=15, pady=(0, 12))

            def _select_all():
                for var, _, _ in check_vars:
                    var.set(True)
                _update_preview()

            def _clear_all():
                for var, _, _ in check_vars:
                    var.set(False)
                custom_entry.delete(0, "end")
                _update_preview()

            def _apply():
                preview_text.configure(state="normal")
                combined = preview_text.get("1.0", "end").strip()
                preview_text.configure(state="disabled")
                if not combined:
                    return

                current_text = self.search_entry.get().strip()
                if current_text:
                    answer = messagebox.askyesnocancel(
                        "Search Bar Has Text",
                        "The search bar already has text.\n\n"
                        "Yes = Replace existing text\n"
                        "No = Append to existing text\n"
                        "Cancel = Do nothing",
                        parent=wiz,
                    )
                    if answer is None:  # Cancel
                        return
                    elif answer:  # Yes = Replace
                        self.search_entry.delete(0, "end")
                        self.search_entry.insert(0, combined)
                    else:  # No = Append
                        if mode_var.get() == "AND":
                            self.search_entry.insert("end", " " + combined)
                        else:
                            self.search_entry.insert("end", "|" + combined)
                        messagebox.showinfo(
                            "Note",
                            "The AND mode checkbox in Advanced Options applies "
                            "to ALL terms in the search bar — not just the "
                            "wizard's patterns. Check or uncheck it to control "
                            "whether all terms must match (AND) or any term "
                            "can match (OR).",
                            parent=wiz,
                        )
                else:
                    self.search_entry.insert(0, combined)

                # Auto-enable regex mode and disable conflicting modes
                self.regex_var.set("on")
                self.fuzzy_var.set("off")
                self.wildcard_var.set("off")
                # Enable AND mode if selected in wizard
                if mode_var.get() == "AND":
                    self.and_mode_var.set("on")
                wiz.destroy()

            tk.Button(btn_frame, text="Select All", width=10, command=_select_all).pack(side="left", padx=(0, 5))
            tk.Button(btn_frame, text="Clear All", width=10, command=_clear_all).pack(side="left", padx=(0, 5))
            tk.Button(btn_frame, text="Apply", width=10, command=_apply).pack(side="right", padx=(5, 0))
            tk.Button(btn_frame, text="Cancel", width=10, command=wiz.destroy).pack(side="right", padx=(5, 0))

            # Load initial category
            _load_category()

        # ── Mutual exclusion for search modes ────────────────────

        def _on_fuzzy_toggle(self):
            if self.fuzzy_var.get() == "on":
                self.regex_var.set("off")
                self.wildcard_var.set("off")

        def _on_regex_toggle(self):
            if self.regex_var.get() == "on":
                self.fuzzy_var.set("off")
                self.wildcard_var.set("off")

        def _on_wildcard_toggle(self):
            if self.wildcard_var.get() == "on":
                self.fuzzy_var.set("off")
                self.regex_var.set("off")

        def _on_expression_toggle(self):
            if self.expression_var.get() == "on":
                self.and_mode_var.set("off")
                self.exclude_entry.delete(0, "end")
                self.proximity_entry.delete(0, "end")
                self.search_entry.configure(placeholder_text='e.g. (budget OR revenue) AND NOT draft')
            else:
                self.search_entry.configure(placeholder_text="Enter search terms...")

        def _on_and_toggle(self):
            if self.and_mode_var.get() == "on":
                self.expression_var.set("off")
                self.search_entry.configure(placeholder_text="Enter search terms...")

    app = DocSearchApp()
    app.mainloop()


def main():
    _launch_gui()


if __name__ == "__main__":
    main()
