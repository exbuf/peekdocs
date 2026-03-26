"""Graphical interface for DocSearch."""

import os
import platform
import re
import shlex
import subprocess
import sys
import threading
import time


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
):
    """Build a docsearch CLI command list from GUI values.

    Returns None on validation error, or "FLAGS_IN_SEARCH" if flags are
    detected in the search text.
    """
    if not search_text.strip():
        return None

    if not folder or not os.path.isdir(folder):
        return None

    # Block flags typed into the search box
    _CLI_FLAGS = {"-a", "-A", "-B", "-c", "-f", "-h", "-n", "-o", "-O", "-p", "-q", "-r", "-s", "-sa", "-t", "-v", "-w", "-x", "-z", "--config"}
    tokens = search_text.strip().split()
    if any(token in _CLI_FLAGS for token in tokens):
        return "FLAGS_IN_SEARCH"

    cmd = [sys.executable, "-m", "docsearch", "-q"]

    if not index_search:
        cmd.append("--no-index")

    if and_mode:
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

    if exclude.strip():
        cmd.extend(["-n", exclude.strip()])

    if file_types.strip():
        cmd.extend(["-t", file_types.strip()])

    if proximity.strip():
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

    if regex:
        # Preserve backslashes for regex patterns (shlex.split eats them)
        lex = shlex.shlex(search_text.strip(), posix=True)
        lex.escape = ""
        lex.commenters = ""
        lex.whitespace_split = True
        try:
            terms = list(lex)
        except ValueError:
            terms = search_text.strip().split()
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
    elapsed_match = re.search(r"Elapsed time:\s*([\d.]+)\s*seconds", clean)

    parts = []
    if found_match:
        count = found_match.group(1)
        parts.append(f"Found {count} match(es)")
    if files_match:
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


def _parse_matched_files(results_dir):
    """Parse docsearch_results.txt and return a list of (filepath, filename, count) tuples."""
    results_path = os.path.join(results_dir, "docsearch_results.txt")
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
            if self.tip_window:
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
            self.elapsed_timer_id = None
            self.search_start_time = None

            self.grid_columnconfigure(1, weight=1)
            self.grid_rowconfigure(5, weight=1)

            self._build_search_row()
            self._build_folder_row()
            self._build_advanced_toggle()
            self._build_advanced_panel()
            self._build_progress_area()
            self._build_open_report()
            self._build_index_panel()
            self._build_bottom_row()
            self._load_saved_settings()

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
            self.search_bar_frame.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                self.search_bar_frame, text="Search Bar",
                font=ctk.CTkFont(size=10), text_color=("gray50", "gray50"),
            ).grid(row=0, column=0, columnspan=4, padx=10, pady=(4, 0), sticky="w")

            label = ctk.CTkLabel(self.search_bar_frame, text="Search Terms:", font=ctk.CTkFont(size=14))
            label.grid(row=1, column=0, padx=(10, 5), pady=(0, 8), sticky="w")

            self.search_entry = ctk.CTkEntry(
                self.search_bar_frame, placeholder_text="Enter search terms...", font=ctk.CTkFont(size=14)
            )
            self.search_entry.grid(row=1, column=1, padx=5, pady=(0, 8), sticky="ew")
            self.search_entry.bind("<Return>", lambda e: self.start_search())

            self.search_button = ctk.CTkButton(
                self.search_bar_frame, text="Search", width=90, command=self.start_search,
                font=ctk.CTkFont(size=14),
            )
            self.search_button.grid(row=1, column=2, padx=(5, 5), pady=(0, 8))

            self.wizard_button = ctk.CTkButton(
                self.search_bar_frame, text="Wizard", width=80, command=self._open_search_wizard,
                font=ctk.CTkFont(size=14),
            )
            self.wizard_button.grid(row=1, column=3, padx=(0, 10), pady=(0, 8))
            Tooltip(self.wizard_button, "Open the Search Wizard to build regex patterns from presets")

            Tooltip(self.search_entry, "Type one or more search terms separated by spaces — there is no limit to the number of terms. Use quotes for phrases (e.g., \"annual report\"). Do not use commas. Do not enter flags here — the checkboxes under Advanced Options handle that.")

        def _build_folder_row(self):
            self.folder_bar_frame = ctk.CTkFrame(self)
            self.folder_bar_frame.grid(
                row=1, column=0, columnspan=3, padx=10, pady=2, sticky="ew"
            )
            self.folder_bar_frame.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                self.folder_bar_frame, text="Folder Bar",
                font=ctk.CTkFont(size=10), text_color=("gray50", "gray50"),
            ).grid(row=0, column=0, columnspan=3, padx=10, pady=(4, 0), sticky="w")

            label = ctk.CTkLabel(self.folder_bar_frame, text="Search Folder:", font=ctk.CTkFont(size=14))
            label.grid(row=1, column=0, padx=(10, 5), pady=(0, 8), sticky="w")

            self.folder_entry = ctk.CTkEntry(self.folder_bar_frame, font=ctk.CTkFont(size=14))
            self.folder_entry.grid(row=1, column=1, padx=5, pady=(0, 8), sticky="ew")
            self.folder_entry.insert(0, os.path.expanduser("~"))

            self.browse_button = ctk.CTkButton(
                self.folder_bar_frame, text="Browse", width=90, command=self.browse_folder,
                font=ctk.CTkFont(size=14),
            )
            self.browse_button.grid(row=1, column=2, padx=(5, 10), pady=(0, 8))

            Tooltip(self.folder_entry, "The folder to search. Click Browse to choose a different folder")

        def _build_advanced_toggle(self):
            self.advanced_toggle = ctk.CTkButton(
                self,
                text="\u25b6 Advanced Options",
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                anchor="w",
                command=self.toggle_advanced,
                font=ctk.CTkFont(size=13),
            )
            self.advanced_toggle.grid(
                row=2, column=0, columnspan=3, padx=15, pady=(10, 0), sticky="w"
            )

        def _build_advanced_panel(self):
            self.advanced_frame = ctk.CTkFrame(self)
            # Don't grid it yet — starts collapsed

            # Row 0: checkboxes row 1
            self.and_mode_var = ctk.StringVar(value="off")
            self.recursive_var = ctk.StringVar(value="off")
            self.fuzzy_var = ctk.StringVar(value="off")

            cb_and = ctk.CTkCheckBox(
                self.advanced_frame, text="AND mode", variable=self.and_mode_var,
                onvalue="on", offvalue="off",
            )
            cb_and.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")
            cb_rec = ctk.CTkCheckBox(
                self.advanced_frame, text="Recursive", variable=self.recursive_var,
                onvalue="on", offvalue="off",
            )
            cb_rec.grid(row=0, column=1, padx=15, pady=(10, 5), sticky="w")
            cb_fuz = ctk.CTkCheckBox(
                self.advanced_frame, text="Fuzzy", variable=self.fuzzy_var,
                onvalue="on", offvalue="off", command=self._on_fuzzy_toggle,
            )
            cb_fuz.grid(row=0, column=2, padx=15, pady=(10, 5), sticky="w")

            # Row 1: checkboxes row 2
            self.wildcard_var = ctk.StringVar(value="off")
            self.ocr_var = ctk.StringVar(value="off")
            self.regex_var = ctk.StringVar(value="off")

            cb_wild = ctk.CTkCheckBox(
                self.advanced_frame, text="Wildcard", variable=self.wildcard_var,
                onvalue="on", offvalue="off", command=self._on_wildcard_toggle,
            )
            cb_wild.grid(row=1, column=0, padx=15, pady=5, sticky="w")
            cb_ocr = ctk.CTkCheckBox(
                self.advanced_frame, text="OCR", variable=self.ocr_var,
                onvalue="on", offvalue="off",
            )
            cb_ocr.grid(row=1, column=1, padx=15, pady=5, sticky="w")
            cb_regex = ctk.CTkCheckBox(
                self.advanced_frame, text="Regex", variable=self.regex_var,
                onvalue="on", offvalue="off", command=self._on_regex_toggle,
            )
            cb_regex.grid(row=1, column=2, padx=15, pady=5, sticky="w")

            # Row 2: exclude
            ctk.CTkLabel(self.advanced_frame, text="Exclude:").grid(
                row=2, column=0, padx=(15, 5), pady=5, sticky="e"
            )
            self.exclude_entry = ctk.CTkEntry(
                self.advanced_frame, placeholder_text="Ex: draft,obsolete"
            )
            self.exclude_entry.grid(row=2, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="ew")

            # Row 3: file types
            ctk.CTkLabel(self.advanced_frame, text="File types:").grid(
                row=3, column=0, padx=(15, 5), pady=5, sticky="e"
            )
            self.file_types_entry = ctk.CTkEntry(
                self.advanced_frame, placeholder_text="Ex: pdf,docx,txt"
            )
            self.file_types_entry.grid(row=3, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="ew")

            # Row 4: proximity + context lines
            num_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
            num_frame.grid(row=4, column=0, columnspan=3, padx=15, pady=(5, 5), sticky="w")

            ctk.CTkLabel(num_frame, text="Proximity:").grid(row=0, column=0, padx=(0, 5))
            self.proximity_entry = ctk.CTkEntry(num_frame, width=60)
            self.proximity_entry.grid(row=0, column=1, padx=(0, 20))

            ctk.CTkLabel(num_frame, text="Lines Before:").grid(row=0, column=2, padx=(0, 5))
            self.context_before_entry = ctk.CTkEntry(num_frame, width=60)
            self.context_before_entry.grid(row=0, column=3, padx=(0, 20))

            ctk.CTkLabel(num_frame, text="Lines After:").grid(row=0, column=4, padx=(0, 5))
            self.context_after_entry = ctk.CTkEntry(num_frame, width=60)
            self.context_after_entry.grid(row=0, column=5)

            # Row 5: cores
            self._default_cores = max(1, (os.cpu_count() or 1) // 2)
            cores_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
            cores_frame.grid(row=5, column=0, columnspan=3, padx=15, pady=(0, 5), sticky="w")

            ctk.CTkLabel(cores_frame, text="Cores to Use:").grid(row=0, column=0, padx=(0, 5))
            self.cores_entry = ctk.CTkEntry(cores_frame, width=60)
            self.cores_entry.insert(0, str(self._default_cores))
            self.cores_entry.grid(row=0, column=1)

            # Row 6: specific files
            ctk.CTkLabel(self.advanced_frame, text="Specific files:").grid(
                row=6, column=0, padx=(15, 5), pady=5, sticky="e"
            )
            self.specific_files_entry = ctk.CTkEntry(
                self.advanced_frame, placeholder_text="Ex: report.pdf,notes.txt"
            )
            self.specific_files_entry.grid(row=6, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="ew")

            # Row 7: save as + append to
            save_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
            save_frame.grid(row=7, column=0, columnspan=3, padx=15, pady=(5, 10), sticky="w")

            ctk.CTkLabel(save_frame, text="Save as:").grid(row=0, column=0, padx=(0, 5))
            self.save_name_entry = ctk.CTkEntry(save_frame, width=140, placeholder_text="Ex: my_report")
            self.save_name_entry.grid(row=0, column=1, padx=(0, 20))

            ctk.CTkLabel(save_frame, text="Append to:").grid(row=0, column=2, padx=(0, 5))
            self.append_name_entry = ctk.CTkEntry(save_frame, width=140, placeholder_text="Ex: combined_report")
            self.append_name_entry.grid(row=0, column=3)

            # Row 8: additional output formats
            output_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
            output_frame.grid(row=8, column=0, columnspan=3, padx=15, pady=(0, 10), sticky="w")

            ctk.CTkLabel(output_frame, text="Also output report in ==>").grid(row=0, column=0, padx=(0, 10))
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

            # Row 9: Save Settings + Restore Settings buttons
            settings_btn_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
            settings_btn_frame.grid(row=9, column=0, columnspan=3, padx=(0, 15), pady=(0, 10), sticky="e")

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
                settings_btn_frame, text="Save Settings", width=120,
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
            Tooltip(reset_btn, "Clear all fields and reset the GUI to its default state. This does not change the config file — only Save Settings writes to it")

            self.advanced_frame.grid_columnconfigure(1, weight=1)

            # Tooltips
            Tooltip(cb_and, "All search terms must appear in the same paragraph")
            Tooltip(cb_rec, "Search subfolders inside the Search Folder")
            Tooltip(cb_fuz, "Find approximate matches for typos, misspellings, and for scans (e.g., 'budgt' matches 'budget')")
            Tooltip(cb_wild, "Use * for any characters and ? for one character (e.g., budg* matches budget, budgets)")
            Tooltip(cb_ocr, "Extract text from scanned PDFs and image files (bmp, jpg, jpeg, png, tif, tiff). Requires Tesseract to be installed (see GitHub-Readme)")
            Tooltip(cb_regex, "Use regular expressions for advanced pattern matching (e.g., \\d{3}-\\d{4} for phone numbers)")
            Tooltip(self.exclude_entry, "Comma-separated terms to skip (e.g., draft,obsolete)")
            Tooltip(self.file_types_entry, "Comma-separated file extensions to search — no limit to the number of types. Supported types: cfg, csv, docx, epub, html, ini, json, log, md, odp, ods, odt, pdf, pptx, rst, rtf, sql, tex, toml, tsv, txt, xlsx, xml, yaml, yml. With OCR enabled: bmp, jpg, jpeg, png, tif, tiff")
            Tooltip(self.proximity_entry, "Find terms within this many words of each other")
            Tooltip(self.context_before_entry, "Number of lines to show before each match")
            Tooltip(self.context_after_entry, "Number of lines to show after each match")
            Tooltip(self.cores_entry, f"Number of CPU cores to use. This machine has {os.cpu_count()}, default is {self._default_cores}")
            Tooltip(self.specific_files_entry, "Comma-separated filenames to search — no limit to the number of files (e.g., report.pdf,notes.txt)")
            Tooltip(self.save_name_entry, "Save the report with a custom name after search completes. DO_NOT_SEARCH_ will be added to the front of your file name")
            Tooltip(self.append_name_entry, "Append results to a named report file (creates or extends it). DO_NOT_SEARCH_ will be added to the front of your file name")
            Tooltip(cb_csv, "Also save results as a CSV file (docsearch_results.csv) — open in Excel or Google Sheets to sort, filter, and analyze")
            Tooltip(cb_json, "Also save results as a JSON file (docsearch_results.json) — machine-readable format for automation and integration")

        def _build_progress_area(self):
            self.progress_bar = ctk.CTkProgressBar(self, mode="indeterminate")
            # Starts hidden — shown only during search

            self.status_label = ctk.CTkLabel(
                self, text="", font=ctk.CTkFont(size=13), anchor="w"
            )
            self.status_label.grid(
                row=5, column=0, columnspan=2, padx=15, pady=(5, 0), sticky="ew"
            )

            self.matched_files = []

        def _build_open_report(self):
            self.action_buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
            # Starts hidden — shown after search when buttons are needed

            self.open_report_button = ctk.CTkButton(
                self.action_buttons_frame,
                text="Open Report",
                width=130,
                command=self.open_report,
                font=ctk.CTkFont(size=14),
            )

            self.error_log_button = ctk.CTkButton(
                self.action_buttons_frame,
                text="View Error Log",
                width=130,
                command=self.open_error_log,
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
            )
            Tooltip(self.error_log_button, "Open docsearch_errors.log to see details about files that could not be read")

            self.matched_files_button = ctk.CTkButton(
                self.action_buttons_frame,
                text="Matched Files",
                width=130,
                command=self._show_matched_files_popup,
                font=ctk.CTkFont(size=13),
            )
            Tooltip(self.matched_files_button, "View the list of files that contained matches (click a file to open it)")

        def _build_index_panel(self):
            self.index_frame = ctk.CTkFrame(self)
            self.index_frame.grid(
                row=6, column=0, columnspan=3, padx=15, pady=(5, 5), sticky="ew"
            )
            self.index_frame.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                self.index_frame, text="Index Bar",
                font=ctk.CTkFont(size=10), text_color=("gray50", "gray50"),
            ).grid(row=0, column=0, columnspan=6, padx=10, pady=(4, 0), sticky="w")

            self.index_search_var = ctk.StringVar(value="off")
            cb_index_search = ctk.CTkCheckBox(
                self.index_frame, text="Search Using Index(es)", variable=self.index_search_var,
                onvalue="on", offvalue="off", font=ctk.CTkFont(size=12),
            )
            cb_index_search.grid(row=1, column=0, padx=(10, 5), pady=(0, 5), sticky="w")
            Tooltip(cb_index_search, "Use the search index for faster searches. Uncheck to search files directly — useful for verifying that both methods find identical results")

            self.build_index_button = ctk.CTkButton(
                self.index_frame, text="Build Index(es)", width=120,
                command=self.build_index_action, font=ctk.CTkFont(size=12),
            )
            self.build_index_button.grid(row=1, column=2, padx=5, pady=(0, 5), sticky="e")
            Tooltip(self.build_index_button, "Build a search index for faster repeated searches. Indexes all subfolders automatically. Warning: Navigate to the right folder (Browse button) before Building Index(es)")

            self.delete_index_button = ctk.CTkButton(
                self.index_frame, text="Delete Index(es)", width=120,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self.delete_index_action, font=ctk.CTkFont(size=12),
            )
            self.delete_index_button.grid(row=1, column=3, padx=5, pady=(0, 5), sticky="e")
            Tooltip(self.delete_index_button, "Delete the search index from the selected folder")

            self.index_status_button = ctk.CTkButton(
                self.index_frame, text="Index Status", width=100,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self.index_status_action, font=ctk.CTkFont(size=12),
            )
            self.index_status_button.grid(row=1, column=4, padx=5, pady=(0, 5), sticky="e")
            Tooltip(self.index_status_button, "Show index info — file count, size, and settings")

            self.about_index_button = ctk.CTkButton(
                self.index_frame, text="About Index", width=100,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self.about_index_action, font=ctk.CTkFont(size=12),
            )
            self.about_index_button.grid(row=1, column=5, padx=(5, 10), pady=(0, 5), sticky="e")
            Tooltip(self.about_index_button, "Overview of how indexes work in docsearch")

        def _build_bottom_row(self):
            self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
            self.bottom_frame.grid(
                row=7, column=0, columnspan=3, padx=15, pady=(0, 15), sticky="sew"
            )

            ctk.CTkLabel(
                self.bottom_frame, text="Toolbar",
                font=ctk.CTkFont(size=10), text_color=("gray50", "gray50"),
            ).pack(side="left", padx=(5, 2))

            self.help_button = ctk.CTkButton(
                self.bottom_frame,
                text="GitHub-Readme",
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
            self.about_button.pack(side="right")

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

        def toggle_advanced(self):
            if self.advanced_visible:
                self.advanced_frame.grid_remove()
                self.advanced_toggle.configure(text="\u25b6 Advanced Options")
            else:
                self.advanced_frame.grid(
                    row=3, column=0, columnspan=3, padx=15, pady=(0, 5), sticky="ew"
                )
                self.advanced_toggle.configure(text="\u25bc Advanced Options")
            self.advanced_visible = not self.advanced_visible

        def browse_folder(self):
            initial = self.folder_entry.get() or os.path.expanduser("~")
            folder = filedialog.askdirectory(initialdir=initial)
            if folder:
                self.folder_entry.delete(0, "end")
                self.folder_entry.insert(0, folder)

        def start_search(self):
            if self.process is not None:
                self.process.terminate()
                return

            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a valid folder.")
                return

            search_text = self.search_entry.get().strip()
            if not search_text:
                self._show_error("Please enter one or more search terms.")
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
            )
            if cmd == "FLAGS_IN_SEARCH":
                self._show_error("Flags go in Advanced Options, not the search box.")
                return
            if cmd is None:
                self._show_error("Invalid input. Check your search terms and options.")
                return

            self.results_dir = folder
            self.search_button.configure(text="Cancel")
            self.search_entry.configure(state="disabled")
            self.action_buttons_frame.grid_remove()
            self._hide_files_list()
            self.progress_bar.grid(
                row=4, column=0, columnspan=3, padx=15, pady=(10, 0), sticky="ew"
            )
            self.progress_bar.start()
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
            try:
                self.process = subprocess.Popen(
                    cmd,
                    cwd=folder,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                stdout, _ = self.process.communicate()
                returncode = self.process.returncode
            except Exception:
                stdout = ""
                returncode = -1
            finally:
                self.process = None

            self.after(0, self._search_finished, stdout, returncode)

        def _search_finished(self, stdout, returncode):
            self.progress_bar.stop()
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
                # Populate matched files for the popup button
                self.matched_files = _parse_matched_files(self.results_dir)
                self._show_action_buttons()
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

        def _show_action_buttons(self):
            """Show Open Report and/or View Error Log buttons as appropriate."""
            # Clear any previous buttons
            self.open_report_button.pack_forget()
            self.error_log_button.pack_forget()
            self.matched_files_button.pack_forget()
            if hasattr(self, "top_action_row"):
                self.top_action_row.destroy()
            self.action_buttons_frame.grid_remove()

            has_report = False
            has_error_log = False
            has_matched = bool(self.matched_files)

            if self.results_dir:
                docx_path = os.path.join(self.results_dir, "docsearch_results.docx")
                has_report = os.path.exists(docx_path)
                error_log_path = os.path.join(self.results_dir, "docsearch_errors.log")
                has_error_log = os.path.exists(error_log_path)

            if not has_report and not has_error_log and not has_matched:
                return

            # Top row: Matched Files + Open Report side by side
            if has_matched or has_report:
                self.top_action_row = ctk.CTkFrame(self.action_buttons_frame, fg_color="transparent")
                self.top_action_row.pack(pady=(0, 2))
                if has_matched:
                    self.matched_files_button.configure(
                        text=f"Matched Files ({len(self.matched_files)})"
                    )
                    self.matched_files_button.pack(in_=self.top_action_row, side="left", padx=(0, 5))
                if has_report:
                    self.open_report_button.pack(in_=self.top_action_row, side="left")
            if has_error_log:
                self.error_log_button.pack(pady=(0, 2))

            self.action_buttons_frame.grid(
                row=5, column=2, padx=(5, 15), pady=(5, 0), sticky="ne"
            )

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

        def open_report(self):
            docx_path = os.path.join(self.results_dir, "docsearch_results.docx")
            if not os.path.exists(docx_path):
                self._show_error("Report file not found.")
                return
            system = platform.system()
            if system == "Darwin":
                subprocess.Popen(["open", docx_path])
            elif system == "Windows":
                os.startfile(docx_path)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", docx_path])

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
                if returncode == 0:
                    summary = ""
                    index_file = ""
                    for line in stdout.strip().split("\n"):
                        if line.startswith("Index built:"):
                            summary = line
                        elif line.startswith("Index file:"):
                            index_file = line.strip()
                    display = summary or "Index built successfully."
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
            popup.title("Matched Files")
            popup.resizable(True, True)
            count = len(self.matched_files)
            win_h = max(200, min(500, count * 28 + 80))
            popup.geometry(f"500x{win_h}")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 500) // 2
            y = self.winfo_rooty() + (self.winfo_height() - win_h) // 2
            popup.geometry(f"+{x}+{y}")

            tk.Label(
                popup, text=f"Matched Files ({count})",
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
            self.specific_files_entry.delete(0, "end")
            self.save_name_entry.delete(0, "end")
            self.append_name_entry.delete(0, "end")
            self.output_csv_var.set("off")
            self.output_json_var.set("off")
            self.index_search_var.set("off")
            self.status_label.configure(
                text="", font=ctk.CTkFont(size=13), text_color=("gray30", "gray70")
            )
            self.action_buttons_frame.grid_remove()
            self._hide_files_list()

        def _show_error(self, message):
            self.status_label.configure(
                text=message, text_color="red", font=ctk.CTkFont(size=13, weight="bold")
            )
            self.bell()
            messagebox.showerror("Error", message)

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

    app = DocSearchApp()
    app.mainloop()


def main():
    _launch_gui()


if __name__ == "__main__":
    main()
