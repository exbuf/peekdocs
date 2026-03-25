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
    try:
        tokens = shlex.split(search_text.strip())
    except ValueError:
        tokens = search_text.strip().split()
    if any(token in _CLI_FLAGS for token in tokens):
        return "FLAGS_IN_SEARCH"

    cmd = [sys.executable, "-m", "docsearch", "-q"]

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

    return " ".join(parts) if parts else ""


def _parse_matched_files(results_dir):
    """Parse docsearch_results.txt and return a list of unique (filepath, filename) tuples."""
    results_path = os.path.join(results_dir, "docsearch_results.txt")
    if not os.path.exists(results_path):
        return []
    files = []
    seen = set()
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
                    filename = line.split("Document: ")[1].split(", Line: ")[0]
                    filepath = os.path.join(file_dir, filename)
                    if filepath not in seen:
                        seen.add(filepath)
                        files.append((filepath, filename))
        i += 1
    return files


def _launch_gui():
    """Import customtkinter and build the GUI. Separated to keep module importable without tkinter."""
    try:
        import customtkinter as ctk
    except ImportError:
        print("GUI mode requires customtkinter. Install it with: pip install customtkinter")
        sys.exit(1)

    import webbrowser
    from tkinter import filedialog
    from importlib.metadata import version as pkg_version

    class Tooltip:
        """Simple hover tooltip for any widget."""

        def __init__(self, widget, text):
            self.widget = widget
            self.text = text
            self.tip_window = None
            widget.bind("<Enter>", self._show)
            widget.bind("<Leave>", self._hide)

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
            self.geometry("700x520")
            self.minsize(600, 400)
            self._center_window(700, 520)

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
            self._build_bottom_row()

        def _center_window(self, width, height):
            self.update_idletasks()
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            x = (screen_w - width) // 2
            y = (screen_h - height) // 2
            self.geometry(f"{width}x{height}+{x}+{y}")

        # ── Layout builders ──────────────────────────────────────

        def _build_search_row(self):
            row = 0
            label = ctk.CTkLabel(self, text="Search:", font=ctk.CTkFont(size=14))
            label.grid(row=row, column=0, padx=(15, 5), pady=(15, 5), sticky="w")

            self.search_entry = ctk.CTkEntry(
                self, placeholder_text="Enter search terms...", font=ctk.CTkFont(size=14)
            )
            self.search_entry.grid(row=row, column=1, padx=5, pady=(15, 5), sticky="ew")
            self.search_entry.bind("<Return>", lambda e: self.start_search())

            self.search_button = ctk.CTkButton(
                self, text="Search", width=90, command=self.start_search,
                font=ctk.CTkFont(size=14),
            )
            self.search_button.grid(row=row, column=2, padx=(5, 15), pady=(15, 5))

            Tooltip(self.search_entry, "Type one or more search terms separated by spaces — there is no limit to the number of terms. Use quotes for phrases (e.g., \"annual report\"). Do not use commas. Do not enter flags here — the checkboxes under Advanced Options handle that.")

        def _build_folder_row(self):
            row = 1
            label = ctk.CTkLabel(self, text="Folder:", font=ctk.CTkFont(size=14))
            label.grid(row=row, column=0, padx=(15, 5), pady=5, sticky="w")

            self.folder_entry = ctk.CTkEntry(self, font=ctk.CTkFont(size=14))
            self.folder_entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
            self.folder_entry.insert(0, os.path.expanduser("~"))

            self.browse_button = ctk.CTkButton(
                self, text="Browse", width=90, command=self.browse_folder,
                font=ctk.CTkFont(size=14),
            )
            self.browse_button.grid(row=row, column=2, padx=(5, 15), pady=5)

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

            self.advanced_frame.grid_columnconfigure(1, weight=1)

            # Tooltips
            Tooltip(cb_and, "All search terms must appear in the same paragraph")
            Tooltip(cb_rec, "Search subfolders inside the selected folder")
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

            # Matched files list — starts hidden, shown after search with matches
            import tkinter as tk
            self.files_frame = ctk.CTkFrame(self)
            self.files_label = ctk.CTkLabel(
                self.files_frame, text="Matched Files (double-click to open):",
                font=ctk.CTkFont(size=12), anchor="w",
            )
            self.files_label.pack(fill="x", padx=5, pady=(4, 0))
            self.files_listbox = tk.Listbox(
                self.files_frame, font=("TkDefaultFont", 12),
                selectmode=tk.SINGLE, activestyle="none",
                bg="#2b2b2b", fg="white", selectbackground="#1f6aa5",
                highlightthickness=0, borderwidth=0, height=6,
            )
            self.files_listbox.pack(fill="both", expand=True, padx=5, pady=(2, 5))
            self.files_listbox.bind("<Double-1>", lambda e: self._open_selected_file())
            self.matched_files = []
            Tooltip(self.files_listbox, "Double-click a file to open it")

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

        def _build_bottom_row(self):
            self.help_button = ctk.CTkButton(
                self,
                text="GitHub-Readme",
                width=110,
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self.open_help,
                font=ctk.CTkFont(size=13),
            )
            self.help_button.grid(
                row=6, column=0, padx=15, pady=(0, 15), sticky="sw"
            )

            self.reset_button = ctk.CTkButton(
                self,
                text="Reset",
                width=90,
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self.reset_form,
                font=ctk.CTkFont(size=13),
            )
            self.reset_button.grid(
                row=6, column=1, padx=5, pady=(0, 15), sticky="s"
            )

            self.about_button = ctk.CTkButton(
                self,
                text="About",
                width=70,
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self.show_about,
                font=ctk.CTkFont(size=13),
            )
            self.about_button.grid(
                row=6, column=2, padx=(5, 15), pady=(0, 15), sticky="se"
            )

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
                self._show_action_buttons()
                # Populate matched files list
                self.matched_files = _parse_matched_files(self.results_dir)
                self.files_listbox.delete(0, "end")
                if self.matched_files:
                    for filepath, filename in self.matched_files:
                        self.files_listbox.insert("end", filename)
                    self.files_frame.grid(
                        row=6, column=0, columnspan=3, padx=15, pady=(5, 5), sticky="nsew"
                    )
                    self.grid_rowconfigure(6, weight=1, minsize=150)
                    self.grid_rowconfigure(5, weight=0)
                    # Move bottom row down
                    self.help_button.grid(row=7, column=0, padx=15, pady=(0, 15), sticky="sw")
                    self.reset_button.grid(row=7, column=1, padx=5, pady=(0, 15), sticky="s")
                    self.about_button.grid(row=7, column=2, padx=(5, 15), pady=(0, 15), sticky="se")
                    # Expand window to fit files list
                    current_height = self.winfo_height()
                    if current_height < 720:
                        self.geometry(f"{self.winfo_width()}x720")
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
            self.action_buttons_frame.grid_remove()

            has_report = False
            has_error_log = False

            if self.results_dir:
                docx_path = os.path.join(self.results_dir, "docsearch_results.docx")
                has_report = os.path.exists(docx_path)
                error_log_path = os.path.join(self.results_dir, "docsearch_errors.log")
                has_error_log = os.path.exists(error_log_path)

            if not has_report and not has_error_log:
                return

            if has_report:
                self.open_report_button.pack(pady=(0, 2))
            if has_error_log:
                self.error_log_button.pack(pady=(0, 2))

            self.action_buttons_frame.grid(
                row=5, column=2, padx=(5, 15), pady=(5, 0), sticky="ne"
            )

        def open_error_log(self):
            error_log_path = os.path.join(self.results_dir, "docsearch_errors.log")
            if not os.path.exists(error_log_path):
                self._show_error("Error log not found.")
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

        def _open_selected_file(self):
            selection = self.files_listbox.curselection()
            if not selection:
                return
            filepath, _ = self.matched_files[selection[0]]
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
            self.files_frame.grid_remove()
            self.files_listbox.delete(0, "end")
            self.matched_files = []
            self.grid_rowconfigure(6, weight=0, minsize=0)
            self.grid_rowconfigure(5, weight=1)
            # Restore bottom row position
            self.help_button.grid(row=6, column=0, padx=15, pady=(0, 15), sticky="sw")
            self.reset_button.grid(row=6, column=1, padx=5, pady=(0, 15), sticky="s")
            self.about_button.grid(row=6, column=2, padx=(5, 15), pady=(0, 15), sticky="se")
            # Restore window size
            self.geometry(f"{self.winfo_width()}x520")

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
            self.status_label.configure(
                text="", font=ctk.CTkFont(size=13), text_color=("gray30", "gray70")
            )
            self.action_buttons_frame.grid_remove()
            self._hide_files_list()

        def _show_error(self, message):
            self.status_label.configure(
                text=message, text_color="red", font=ctk.CTkFont(size=13, weight="bold")
            )

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
