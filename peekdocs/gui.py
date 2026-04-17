"""Graphical interface for PeekDocs."""

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
    output_pdf=False,
    index_search=False,
    inverse=False,
    expression=False,
    whole_word=False,
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
    if output_pdf:
        output_parts.append("pdf")
    if output_parts:
        cmd.extend(["-o", ",".join(output_parts)])

    if str(max_matches).strip() and str(max_matches).strip() != "1000":
        cmd.extend(["-m", str(max_matches).strip()])

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
    capped_match = re.search(r"Reports capped at ([\d,]+)", clean)
    inverse_match = re.search(r"Found\s+(\d+)\s+file\(s\)\s+WITHOUT\s+matches", clean)
    elapsed_match = re.search(r"Elapsed time:\s*([\d.]+)\s*seconds", clean)

    parts = []
    # Lead with files searched count
    if files_match:
        file_part = f"{files_match.group(1)} file(s) searched"
        if size_match:
            file_part += f" ({size_match.group(1)})"
        parts.append(file_part)
    if inverse_match:
        parts.append(f"— Found {inverse_match.group(1)} file(s) WITHOUT matches")
    elif found_match:
        count = found_match.group(1)
        if capped_match:
            parts.append(f"— Found {count} match(es) — reports capped at {capped_match.group(1)}")
        else:
            parts.append(f"— Found {count} match(es)")
    if elapsed_match:
        parts.append(f"in {elapsed_match.group(1)}s")

    errors_match = re.search(r"(\d+)\s+error\(s\)", clean)
    if errors_match:
        err_count = errors_match.group(1)
        parts.append(f"— {err_count} file(s) could not be read")

    return " ".join(parts) if parts else ""


def _parse_matched_files(results_dir, results_filename="peekdocs_results.txt"):
    """Parse peekdocs_results.txt and return a list of (filepath, filename, count, line_nums) tuples.

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


def _parse_inverse_files(results_dir, results_filename="peekdocs_results.txt"):
    """Parse peekdocs_results.txt for inverse search and return (filepath, filename, 0, []) tuples."""
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

        def __init__(self, widget, text, anchor="right"):
            """Bind hover tooltip with the given text to a widget."""
            self.widget = widget
            self.text = text
            self.anchor = anchor
            self.tip_window = None
            widget.bind("<Enter>", self._show)
            widget.bind("<Leave>", self._hide)
            # Bind to internal children (needed for CTk composite widgets)
            for child in widget.winfo_children():
                child.bind("<Enter>", self._show)
                child.bind("<Leave>", self._hide)

        def _show(self, event=None):
            """Display the tooltip window near the widget on mouse enter."""
            if self.tip_window or not Tooltip.enabled:
                return
            try:
                import tkinter as tk

                # Initial x position; y for above-* is computed after the
                # tooltip is rendered so it never overlaps the widget.
                if self.anchor == "left":
                    x = self.widget.winfo_rootx() + self.widget.winfo_width() - 310
                    y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
                elif self.anchor in ("above", "above-left", "above-mid", "above-high"):
                    x = self.widget.winfo_rootx()
                    if self.anchor == "above-left":
                        x = self.widget.winfo_rootx() + self.widget.winfo_width() - 310
                    # Placeholder y; will be corrected after tooltip is laid out
                    y = self.widget.winfo_rooty() - 200
                else:
                    x = self.widget.winfo_rootx() + 20
                    y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

                self.tip_window = tw = tk.Toplevel(self.widget)
                tw.wm_overrideredirect(True)
                tw.wm_geometry(f"+{x}+{y}")
                display_text = (
                    f"{self.text}\n\n"
                    "Turn hover text on/off from Tools \u25b2 \u2192 "
                    "Disable/Enable Hover Text."
                )
                label = tk.Label(
                    tw, text=display_text, background="#333333", foreground="white",
                    relief="solid", borderwidth=1, font=("TkDefaultFont", 12),
                    padx=6, pady=4, wraplength=300, justify="left",
                )
                label.pack()

                # For "above" variants, measure the rendered tooltip height
                # and place it so its bottom edge sits just above the widget.
                # This guarantees the tooltip never covers the widget itself,
                # regardless of how much text it contains.
                if self.anchor in ("above", "above-left", "above-mid", "above-high"):
                    tw.update_idletasks()
                    tip_h = tw.winfo_height()
                    y = self.widget.winfo_rooty() - tip_h - 6
                    tw.wm_geometry(f"+{x}+{y}")
            except Exception:
                self.tip_window = None

        def _hide(self, event=None):
            """Destroy the tooltip window on mouse leave."""
            if self.tip_window:
                try:
                    self.tip_window.destroy()
                except Exception:
                    pass
                self.tip_window = None

    class PeekDocsApp(ctk.CTk):
        def __init__(self):
            """Initialize the main application window, widgets, and saved settings."""
            super().__init__()

            try:
                version = pkg_version("peekdocs")
            except Exception:
                version = ""
            self.title(f"peekdocs {version}".strip())
            self.withdraw()  # Hide until setup is complete to prevent flicker
            self.geometry("1280x800")
            self.minsize(1280, 700)
            self._center_window(1050, 720)

            ctk.set_appearance_mode("System")
            ctk.set_default_color_theme("blue")

            self.process = None
            self.search_thread = None
            self.results_dir = None
            self._recent_searches = []
            self._excluded_files = []
            self.advanced_visible = False
            self.elapsed_timer_id = None
            self.search_start_time = None
            self._refresh_timer_id = None
            self._refresh_running = False
            self._text_size_var = ctk.StringVar(value="Normal")

            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(0, weight=1)

            # Tab view: Getting Started + Search
            self._tabview = ctk.CTkTabview(self, anchor="nw", command=self._on_tab_changed)
            self._tabview.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5, 0))

            self._tab_started = self._tabview.add("Getting Started")
            self._tab_search = self._tabview.add("Search")

            # Add tooltip to the Getting Started tab button
            try:
                gs_btn = self._tabview._segmented_button._buttons_dict.get("Getting Started")
                if gs_btn:
                    Tooltip(gs_btn, "A quick introduction to peekdocs — what it does, how to use it, and what features are available")
            except Exception:
                pass

            # Build Getting Started tab
            self._build_getting_started_tab()

            # Use an inner frame with grid layout inside the Search tab
            self._search_parent = ctk.CTkFrame(self._tab_search, fg_color="transparent")
            self._search_parent.pack(fill="both", expand=True)
            self._search_parent.grid_columnconfigure(0, weight=0)
            self._search_parent.grid_columnconfigure(1, weight=1)
            self._search_parent.grid_rowconfigure(8, weight=1)

            # Shared toggle row for Advanced Search Options and Manage Indexes
            self._toggle_row = ctk.CTkFrame(self._search_parent, fg_color="transparent")
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
            self._build_bottom_row()

            # Show the View Report row on startup (buttons grayed out until a search runs)
            for btn in (self.report_btn_txt, self.report_btn_docx, self.report_btn_csv,
                        self.report_btn_json, self.report_btn_pdf):
                btn.pack(side="left", padx=(0, 2))
                btn.configure(state="disabled", fg_color="gray60", hover_color="gray60")
            self.report_frame.grid(
                row=9, column=0, padx=(15, 5), pady=(5, 5), sticky="w"
            )

            # Check for first run before loading settings (which creates the config file)
            from peekdocs.cli import _config_path
            self._is_first_run = not os.path.exists(_config_path())
            self._load_saved_settings()
            self._update_index_button_color()
            self._refresh_load_search_menu()
            # Re-apply settings after event loop starts (CTkToplevel widgets may
            # reset their variables during initialization on Windows)
            self.after(200, self._load_saved_settings)
            self.after(1000, self._load_saved_settings)
            # Show the window after all settings reloads are done
            self.after(1100, self.deiconify)
            if self._is_first_run:
                self._tabview.set("Getting Started")
            else:
                self._tabview.set("Search")
            # Apply the Search-tab-visibility rules to the initial tab
            # (fire after deiconify so the segmented button is fully laid out)
            self.after(1200, self._on_tab_changed)
            # Sync entry field widths after layout is complete
            self.after(1300, self._sync_input_widths)

        def _on_tab_changed(self):
            """Hide the Search tab button when on Search (redundant), and
            rename it to 'Return' when on Getting Started so clicking it
            returns the user to where they started."""
            try:
                current = self._tabview.get()
                seg = self._tabview._segmented_button
                search_btn = seg._buttons_dict.get("Search")
                if search_btn is None:
                    return
                if current == "Search":
                    # User is already on Search — hide the redundant tab button
                    search_btn.grid_remove()
                else:
                    # On Getting Started — show the button labeled "Return"
                    search_btn.grid()
                    search_btn.configure(text="Return")
            except Exception:
                pass

        def _sync_input_widths(self):
            """No-op — kept for compatibility.  Entry alignment is now handled
            by the shared _input_frame grid (both rows share the same columns).
            """
            pass

        def _center_window(self, width, height):
            """Center the application window on screen with the given dimensions."""
            self.update_idletasks()
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            x = (screen_w - width) // 2
            y = (screen_h - height) // 2
            self.geometry(f"{width}x{height}+{x}+{y}")

        # ── Layout builders ──────────────────────────────────────

        def _build_getting_started_tab(self):
            """Build the Getting Started tab with a friendly guided introduction."""
            import tkinter as tk
            tab = self._tab_started

            canvas = tk.Canvas(tab, highlightthickness=0)
            scrollbar = tk.Scrollbar(tab, command=canvas.yview)
            inner = tk.Frame(canvas)
            inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=inner, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set, yscrollincrement=10)
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)

            def _on_mousewheel(event):
                delta = 1 if event.delta > 0 else -1
                canvas.yview_scroll(-delta, "units")
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

            pad = {"padx": 30, "anchor": "w"}

            tk.Label(inner, text="Welcome to peekdocs!", font=("TkDefaultFont", 22, "bold")).pack(pady=(20, 5), **pad)
            tk.Label(inner, text="Search Word docs, PDFs, spreadsheets, emails, and 42 other file types — all offline.",
                     font=("TkDefaultFont", 13), fg="gray").pack(pady=(0, 15), **pad)

            def _step(number, title, desc):
                frame = tk.Frame(inner)
                frame.pack(fill="x", padx=30, pady=(10, 0))
                tk.Label(frame, text=f"Step {number}", font=("TkDefaultFont", 14, "bold"),
                         fg="white", bg="#2196F3", width=7).pack(side="left", padx=(0, 12))
                text_frame = tk.Frame(frame)
                text_frame.pack(side="left", fill="x")
                tk.Label(text_frame, text=title, font=("TkDefaultFont", 14, "bold"),
                         anchor="w", justify="left").pack(anchor="w", fill="x")
                tk.Label(text_frame, text=desc, font=("TkDefaultFont", 12), fg="gray",
                         anchor="w", justify="left", wraplength=800).pack(anchor="w", fill="x")

            _step(1, "Choose a folder", "On the main page, click Browse next to '1. Search Folder' to select the folder containing your documents.")
            _step(2, "Type what you're looking for", "Enter your search terms in the '2. Search Terms' field. Example: budget revenue. Then choose OR if any terms are matched, or AND if all terms must be matched.")
            _step(3, "Click Run Search", "peekdocs scans every supported file and shows results with matches highlighted in yellow.")
            _step(4, "View your results", "You can view results two ways: inline in the Results Preview pane below the search bar, or in a full report. Click DOCX or TXT next to View Report to open the highlighted Word or plain text report. DOCX requires a word processor on your computer (Microsoft Word, LibreOffice, Google Docs, or Apple Pages). TXT opens in any text editor.")

            tk.Label(inner, text="", font=("TkDefaultFont", 6)).pack()  # spacer

            tk.Label(inner, text="Want to do more?", font=("TkDefaultFont", 16, "bold")).pack(pady=(15, 5), **pad)

            features = [
                ("\U0001f50d  PII Scan", "One click finds SSNs, credit cards, passwords, and other sensitive data hiding in your files. Advanced users can add their own custom regex.", "#0D9488"),
                ("\U0001f9ea  Search Wizard", "Pick a search type (SSN, phone, email, dollar range, etc.) and the wizard configures it for you.", "#8B5CF6"),
                ("\U0001f50e  Save Search", "Save a configured search by name and load it later to run it again.", "#2196F3"),
                ("\U0001f4c4  Highlighted Reports", "Every search produces a Word report with matches highlighted in yellow.", "#E65100"),
                ("\U0001f30d  Any Language", "Search documents in English, Spanish, Chinese, Arabic, Hindi, Japanese, Greek, or any other language. All text handling is Unicode-based. Documentation and GUI are in English only.", "#6B7280"),
            ]

            for emoji_title, desc, color in features:
                frame = tk.Frame(inner)
                frame.pack(fill="x", padx=30, pady=(8, 0))
                tk.Label(frame, text=emoji_title, font=("TkDefaultFont", 13, "bold"), fg=color, anchor="w").pack(anchor="w")
                tk.Label(frame, text=desc, font=("TkDefaultFont", 12), fg="gray", anchor="w", justify="left", wraplength=900).pack(anchor="w", padx=(24, 0))

            tk.Label(inner, text="", font=("TkDefaultFont", 6)).pack()  # spacer

            tk.Label(inner, text="You've got this! Click the Return tab above and discover what's hiding in your documents.",
                     font=("TkDefaultFont", 14, "bold"), fg="#2196F3").pack(pady=(15, 30), **pad)

        def _build_search_row(self):
            """Build the search bar with entry field, action buttons, and tooltips.

            Both the folder row and search row share a single combined frame
            (_input_frame) so their columns align perfectly.  The folder row
            is built later by _build_folder_row at row 0; this method builds
            the search row at rows 1-2.
            """
            # Combined frame for both input rows — shared grid columns
            # guarantee the labels, entries, and button frames align.
            self._input_frame = ctk.CTkFrame(self._search_parent, fg_color="transparent")
            self._input_frame.grid(
                row=0, column=0, columnspan=3, rowspan=2,
                padx=10, pady=(5, 2), sticky="nsew"
            )
            self._input_frame.grid_columnconfigure(0)
            self._input_frame.grid_columnconfigure(1, weight=1)
            self._input_frame.grid_columnconfigure(2, minsize=185)

            # Create recursive_var early so both the folder row checkbox
            # and Advanced Search Options can share it.
            self.recursive_var = ctk.StringVar(value="on")

            label = ctk.CTkLabel(self._input_frame, text="2. Search Terms:", font=ctk.CTkFont(size=18, weight="bold"), width=200, anchor="w")
            label.grid(row=1, column=0, padx=(10, 2), pady=(4, 8), sticky="w")

            self._assistant_label = ctk.CTkLabel(
                self._input_frame, text="", font=ctk.CTkFont(size=12),
                text_color=("#8B5CF6", "#A78BFA"), anchor="w",
            )
            # Hidden until Search Assistant sets a query

            self.search_entry = ctk.CTkEntry(
                self._input_frame, placeholder_text="Enter search terms...", font=ctk.CTkFont(size=14)
            )
            self.search_entry.grid(row=1, column=1, padx=(5, 25), pady=(4, 8), sticky="ew")
            self.search_entry.bind("<Key>", lambda e: self._assistant_label.grid_remove() if e.keysym not in ("Return", "Tab") else None)
            self.search_entry.bind("<Return>", lambda e: self.start_search())

            self._search_btn_frame = ctk.CTkFrame(self._input_frame, fg_color="transparent")
            self._search_btn_frame.grid(row=1, column=2, padx=(5, 10), pady=(4, 8), sticky="w")

            clear_button = ctk.CTkButton(
                self._search_btn_frame, text="Clear", width=70,
                command=lambda: self.search_entry.delete(0, "end"),
                font=ctk.CTkFont(size=14),
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
            )
            clear_button.pack(side="left", padx=(0, 3))
            Tooltip(clear_button, "Clear the search bar", anchor="left")

            recent_btn = ctk.CTkButton(
                self._search_btn_frame, text="\u25bc", width=30,
                command=self._show_recent_searches,
                font=ctk.CTkFont(size=14),
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
            )
            recent_btn.pack(side="left")
            Tooltip(recent_btn, "Show recent searches — click to re-use a previous search", anchor="left")

            # Row 2: "3." label + action buttons
            ctk.CTkLabel(
                self._input_frame, text="3. Run Search:",
                font=ctk.CTkFont(size=18, weight="bold"),
            ).grid(row=2, column=0, padx=(10, 2), pady=(0, 8), sticky="w")

            btn_frame = ctk.CTkFrame(self._input_frame, fg_color="transparent")
            btn_frame.grid(row=2, column=1, columnspan=2, padx=(5, 5), pady=(0, 8), sticky="ew")

            # Run Search button — standalone
            self.search_button = ctk.CTkButton(
                btn_frame, text="Run Search", width=100, height=32, command=self.start_search,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="green", hover_color="darkgreen",
            )
            self.search_button.pack(side="left", padx=(0, 10))
            Tooltip(self.search_button, "Run the search using the current search terms and all settings in Advanced Search Options (checkboxes, file types, exclude terms, range filters, proximity, etc.). This button turns red and is temporarily disabled while an index is being built to avoid conflicts")

            # Search options group: AND/OR, Recursive, Whole Word, ?
            options_group = ctk.CTkFrame(
                btn_frame, border_width=2, border_color=("gray40", "gray60"),
                corner_radius=8, fg_color=("gray85", "gray20"),
            )
            options_group.pack(side="left", padx=(0, 10))

            # AND/OR toggle buttons — the active mode is highlighted green
            self.and_mode_var = ctk.StringVar(value="off")
            _and_on_fg = ("#4CAF50", "#43A047")
            _and_off_fg = ("gray78", "gray45")
            _and_on_text = ("white", "white")
            _and_off_text = ("gray30", "gray70")

            def _sync_and_or_colors():
                is_and = self.and_mode_var.get() == "on"
                self._and_btn.configure(
                    fg_color=_and_on_fg if is_and else _and_off_fg,
                    text_color=_and_on_text if is_and else _and_off_text,
                )
                self._or_btn.configure(
                    fg_color=_and_on_fg if not is_and else _and_off_fg,
                    text_color=_and_on_text if not is_and else _and_off_text,
                )

            def _on_and_click():
                self.and_mode_var.set("on")
                if hasattr(self, "expression_var"):
                    self.expression_var.set("off")
                if hasattr(self, "search_entry"):
                    self.search_entry.configure(placeholder_text="Enter search terms...")
                _sync_and_or_colors()

            def _on_or_click():
                self.and_mode_var.set("off")
                if hasattr(self, "search_entry"):
                    self.search_entry.configure(placeholder_text="Enter search terms...")
                _sync_and_or_colors()

            self._and_btn = ctk.CTkButton(
                options_group, text="AND", width=40,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=_and_off_fg, text_color=_and_off_text,
                hover_color=("gray60", "gray50"),
                command=_on_and_click,
            )
            self._and_btn.pack(side="left", padx=(4, 0), pady=3)
            Tooltip(self._and_btn, "AND mode — all search terms must appear in the same paragraph")

            self._or_btn = ctk.CTkButton(
                options_group, text="OR", width=35,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=_and_on_fg, text_color=_and_on_text,
                hover_color=("gray60", "gray50"),
                command=_on_or_click,
            )
            self._or_btn.pack(side="left", padx=(2, 4), pady=3)
            Tooltip(self._or_btn, "OR mode (default) — find lines containing any of the search terms")
            self._sync_and_or_colors = _sync_and_or_colors

            # Separator
            _sep = ctk.CTkFrame(options_group, width=2, height=20,
                                fg_color=("gray55", "gray55"))
            _sep.pack(side="left", padx=(14, 14), pady=3)

            self._folder_recursive_cb = ctk.CTkCheckBox(
                options_group, text="Recursive", variable=self.recursive_var,
                onvalue="on", offvalue="off", font=ctk.CTkFont(size=12),
            )
            self._folder_recursive_cb.pack(side="left", padx=(2, 5), pady=3)
            Tooltip(self._folder_recursive_cb, "Include all subfolders when searching")

            self.whole_word_var = ctk.StringVar(value="on")
            self._search_whole_word_cb = ctk.CTkCheckBox(
                options_group, text="Whole Word", variable=self.whole_word_var,
                onvalue="on", offvalue="off", font=ctk.CTkFont(size=12),
            )
            self._search_whole_word_cb.pack(side="left", padx=(0, 4), pady=3)
            Tooltip(self._search_whole_word_cb, "Matches complete words only. 'bob' matches 'bob' but not 'bobcat'")

            # ? help for this options group
            options_help_btn = ctk.CTkButton(
                options_group, text="?", width=0, height=22,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self._show_search_options_help,
            )
            options_help_btn.pack(side="left", padx=(0, 4), pady=3)
            Tooltip(options_help_btn, "Help — explains AND/OR, Recursive, and Whole Word")

            # Save, Reload, and ? grouped together
            save_group = ctk.CTkFrame(
                btn_frame, border_width=2, border_color=("gray40", "gray60"),
                corner_radius=8, fg_color=("gray85", "gray20"),
            )
            save_group.pack(side="left", padx=(15, 0))

            self.save_to_collection_btn = ctk.CTkButton(
                save_group, text="\u25b6 Save", width=0,
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self._save_to_collection,
                font=ctk.CTkFont(size=13),
            )
            self.save_to_collection_btn.pack(side="left", padx=(4, 2), pady=3)
            Tooltip(self.save_to_collection_btn, "Save the current search settings to the folder's collection by name so you can load and reuse it later")

            self.load_search_btn = ctk.CTkButton(
                save_group, text="\u25b6 Reload", width=0,
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self._open_load_search_popup,
                font=ctk.CTkFont(size=13),
            )
            self.load_search_btn.pack(side="left", padx=(2, 2), pady=3)
            Tooltip(self.load_search_btn, "Load a saved search from the folder's collection into the GUI to review, edit, or re-run it")
            self._load_search_popup = None

            self.save_load_help_btn = ctk.CTkButton(
                save_group, text="?", width=0, height=22,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self._show_save_load_help,
            )
            self.save_load_help_btn.pack(side="left", padx=(2, 4), pady=3)
            Tooltip(self.save_load_help_btn, "Help for Save Search and Load Search")

            self.index_search_var = ctk.StringVar(value="off")
            self.cb_index_search = ctk.CTkCheckBox(
                btn_frame, text="Use Index", variable=self.index_search_var,
                onvalue="on", offvalue="off", font=ctk.CTkFont(size=12, weight="bold"),
            )
            self.cb_index_search.pack(side="left", padx=(20, 20))
            Tooltip(self.cb_index_search, "Use the search index for faster searches. Uncheck to search files directly. Build an index first using Manage Indexes", anchor="left")


            Tooltip(self.search_entry, "Type one or more search terms separated by spaces — there is no limit to the number of terms. Use quotes for phrases (e.g., \"annual report\"). All searches are case-insensitive. Do not use commas. Do not enter flags here — the checkboxes under Advanced Search Options handle that. When Expression is checked, enter a boolean expression instead (e.g., \"(bob AND amy) OR fred NOT draft\").")

        def _show_welcome(self):
            """Show a getting-started guide for first-time users."""
            import tkinter as tk
            win = tk.Toplevel(self)
            win.title("Welcome to peekdocs")
            win.geometry("620x480")
            win.resizable(True, True)
            win.transient(self)
            try:
                win.grab_set()
            except Exception:
                win.after(150, lambda: win.grab_set() if win.winfo_exists() else None)

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

            h("Welcome to peekdocs!")
            b("peekdocs lets you search Word docs, PDFs, spreadsheets,")
            b("emails, calendars, contacts, and 40 other file types \u2014 all at once, all offline.")
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
            b("peekdocs scans every supported file in the folder and")
            b("shows a summary when finished. Your results appear in")
            b("a preview below, and are saved to two report files:")
            e("peekdocs_results.txt   (plain text)")
            e("peekdocs_results.docx  (Word, with highlights)")
            blank()
            st("Step 4: View your results")
            b("Click the DOCX button next to View Report to open the")
            b("Word report with your matches highlighted in yellow.")
            blank()

            h("What's Next?")
            blank()
            s("Search subfolders")
            b("Open Advanced Search Options and check Recursive to search")
            b("all subfolders, not just the selected folder.")
            blank()
            s("Use advanced search modes")
            b("Open Advanced Search Options for regex, fuzzy matching,")
            b("wildcards, Boolean expressions, range queries, and more.")
            b("Click the ? button inside Advanced Search Options for help.")
            blank()
            s("Scan for sensitive data")
            b("Click the red Sensitive Data Scan button to check your")
            b("documents for SSNs, credit cards, tax IDs, emails, phone")
            b("numbers, passwords, and more \u2014 one click, no setup needed.")
            blank()
            s("Save your searches")
            b("Once you've configured a search you'll want to reuse,")
            b("click Save Search to store it by name. Click Load Search")
            b("later to recall it with one click.")
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

        def _open_search_wizard_guide(self):
            """Open a guided Search Wizard with predefined search patterns."""
            import tkinter as tk

            win = ctk.CTkToplevel(self)
            win.title("Search Wizard")
            win.geometry("920x680")
            win.resizable(True, True)
            win.after(50, win.lift)
            win.after(100, win.focus_force)
            win.after(200, lambda: win.title("Search Wizard"))

            header_frame = ctk.CTkFrame(win, fg_color="transparent")
            header_frame.pack(fill="x", padx=15, pady=(10, 5))
            ctk.CTkLabel(
                header_frame,
                text="Select a search type (click its radio button), fill in your values, "
                     "then click Apply. Close this window at any time to cancel \u2014 nothing changes until you click Apply.",
                font=ctk.CTkFont(size=13),
                wraplength=650, justify="center",
            ).pack(expand=True)
            ctk.CTkButton(
                header_frame, text="?", width=30,
                command=lambda: self._show_search_wizard_help(win),
                font=ctk.CTkFont(size=14, weight="bold"),
            ).pack(side="right")

            self._sw_folder_label = self._add_folder_bar(win, "Search will run against this folder.")

            import tkinter as _tk_wiz
            tip_frame = _tk_wiz.Frame(win, bg="#FFF3CD", highlightbackground="#FFD700", highlightthickness=1)
            tip_frame.pack(fill="x", padx=15, pady=(0, 5))
            _tk_wiz.Label(
                tip_frame,
                text="\u2191 Tip: After clicking Apply, visit Advanced Search Options for additional settings: "
                     "File Types, Exclude Terms, Proximity, Context Lines, Range Filters, and more.",
                font=("TkDefaultFont", 11, "bold"), fg="#856404", bg="#FFF3CD",
                wraplength=860, justify="left",
            ).pack(padx=10, pady=6)

            # Common settings — Recursive and OCR
            _sf = self._scaled_font
            settings_frame = tk.Frame(win)
            settings_frame.pack(fill="x", padx=15, pady=(0, 0))
            tk.Frame(win, height=24).pack()  # spacer for readability
            tk.Label(settings_frame, text="Also apply:", font=_sf(13, "bold"),
                     ).pack(side="left", padx=(0, 8))
            wiz_recursive_var = tk.BooleanVar(value=self.recursive_var.get() == "on")
            wiz_recursive_cb = tk.Checkbutton(
                settings_frame, text="Include subfolders (Recursive)",
                variable=wiz_recursive_var, font=_sf(13),
            )
            wiz_recursive_cb.pack(side="left", padx=(0, 15))
            wiz_ocr_var = tk.BooleanVar(value=self.ocr_var.get() == "on")
            wiz_ocr_cb = tk.Checkbutton(
                settings_frame, text="Search scanned PDFs/images (OCR)",
                variable=wiz_ocr_var, font=_sf(13),
            )
            wiz_ocr_cb.pack(side="left")

            # Scrollable frame for patterns
            canvas_frame = tk.Frame(win)
            canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))
            canvas = tk.Canvas(canvas_frame)
            scrollbar = tk.Scrollbar(canvas_frame, command=canvas.yview)
            scroll_inner = tk.Frame(canvas)
            scroll_inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scroll_inner, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)

            # Enable mousewheel scrolling (cross-platform)
            def _bind_mousewheel(c, parent_win):
                def _scroll(event):
                    if sys.platform == "darwin":
                        direction = -1 if event.delta > 0 else 1
                        c.yview_scroll(direction, "units")
                    elif sys.platform == "linux":
                        pass  # handled by Button-4/5
                    else:
                        c.yview_scroll(int(-event.delta / 40), "units")
                c.configure(yscrollincrement=10)
                parent_win.bind("<MouseWheel>", _scroll)
                if sys.platform == "linux":
                    parent_win.bind("<Button-4>", lambda e: c.yview_scroll(-1, "units"))
                    parent_win.bind("<Button-5>", lambda e: c.yview_scroll(1, "units"))
            _bind_mousewheel(canvas, win)

            patterns = [
                ("Find keywords (OR — any match)", "Lines containing any of the terms. For AND+OR combos use Boolean below",
                 [("Keywords:", "keyword", "budget revenue expenses")],
                 lambda v: self._apply_wizard(search_text=v["keyword"])),

                ("Find keywords (AND — all must match)", "Lines containing ALL terms. For AND+OR combos use Boolean below",
                 [("Keywords:", "keyword", "budget approved Q1")],
                 lambda v: self._apply_wizard(search_text=v["keyword"], and_mode=True)),

                ("Find keywords OR (exclude terms)", "Lines with any keyword, skipping lines with excluded terms",
                 [("Keywords:", "keyword", "budget revenue"), ("Exclude:", "exclude", "draft,preliminary")],
                 lambda v: self._apply_wizard(search_text=v["keyword"], exclude=v["exclude"])),

                ("Find keywords AND (exclude terms)", "Lines with ALL keywords, skipping lines with excluded terms",
                 [("Keywords:", "keyword", "budget approved"), ("Exclude:", "exclude", "draft,pending,obsolete")],
                 lambda v: self._apply_wizard(search_text=v["keyword"], and_mode=True, exclude=v["exclude"])),

                ("Find files MISSING terms", "List files that do NOT contain ANY of these terms",
                 [("Required terms:", "term", "Authorized Signature")],
                 lambda v: self._apply_wizard(search_text=v["term"], inverse=True)),

                ("Find SSNs", "Social Security numbers (XXX-XX-XXXX)",
                 [],
                 lambda v: self._apply_wizard(search_text=r"\d{3}-\d{2}-\d{4}", regex=True)),

                ("Find phone numbers", "US phone numbers with formatting (requires dashes, dots, spaces, or parentheses)",
                 [],
                 lambda v: self._apply_wizard(search_text=r"(?<!\d)(?:\(\d{3}\)\s?\d{3}[-.\s]\d{4}|\d{3}[-.\s]\d{3}[-.\s]\d{4})(?!\d)", regex=True)),

                ("Find email addresses", "Email addresses in any format",
                 [],
                 lambda v: self._apply_wizard(search_text=r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}", regex=True)),

                ("Find dollar amounts in range", "Lines containing a dollar amount in range.\n"
                 "Note: all dollar amounts on matching lines are highlighted, but only lines\n"
                 "with at least one amount in range are included in results.",
                 [("Min ($):", "lo", "10000"), ("Max ($):", "hi", "50000")],
                 lambda v: self._apply_wizard(search_text=r"\$[\d,.]+", regex=True, range_filters=f"amount:{v['lo']}..{v['hi']}")),

                ("Find vendor with dollar amounts in range", "Lines with a vendor name AND a dollar amount in range.\n"
                 "Example: find lines mentioning 'Acme' with amounts between $5,000 and $25,000",
                 [("Vendor:", "vendor", "Acme"), ("Min ($):", "lo", "5000"), ("Max ($):", "hi", "25000")],
                 lambda v: self._apply_wizard(search_text=rf"{v['vendor']} \$[\d,.]+", regex=True, and_mode=True, range_filters=f"amount:{v['lo']}..{v['hi']}")),

                ("Find vendor with any dollar amount", "Lines with a vendor name AND any dollar amount on the same line",
                 [("Vendor:", "vendor", "Acme")],
                 lambda v: self._apply_wizard(search_text=rf"{v['vendor']} \$[\d,.]+", regex=True, and_mode=True)),

                ("Find keywords with dollar amounts", "Lines with both keywords AND a dollar sign",
                 [("Keywords:", "keyword", "cloudnine hosting")],
                 lambda v: self._apply_wizard(search_text=f"{v['keyword']} $", and_mode=True)),

                ("Find keywords in file types", "Search only certain file formats",
                 [("Keywords:", "keyword", "budget revenue"), ("Types:", "types", "pdf,docx,xlsx")],
                 lambda v: self._apply_wizard(search_text=v["keyword"], file_types=v["types"])),

                ("Find keywords in subfolders", "Search the folder and all subfolders",
                 [("Keywords:", "keyword", "budget revenue 2025")],
                 lambda v: self._apply_wizard(search_text=v["keyword"], recursive=True)),

                ("Find misspelled terms (fuzzy)", "Fuzzy match for typos or OCR errors",
                 [("Terms:", "term", "accommodation receipt")],
                 lambda v: self._apply_wizard(search_text=v["term"], fuzzy=True)),

                ("Find words near each other", "Two terms within N words of each other",
                 [("Term 1:", "t1", "breach"), ("Term 2:", "t2", "contract"), ("N words:", "n", "5")],
                 lambda v: self._apply_wizard(search_text=f"{v['t1']} {v['t2']}", proximity=v["n"])),

                ("Boolean expression (AND + OR + NOT)", "Combine AND, OR, NOT with parentheses. No limit on terms or nesting depth.\n"
                 "AND/OR/NOT must be UPPERCASE. Examples:\n"
                 "(budget OR revenue) AND approved\n"
                 "(budget OR revenue OR limit OR expenses) AND approved\n"
                 "(salary OR bonus) AND NOT confidential\n"
                 "((budget OR revenue) AND (approved OR signed)) OR (draft AND NOT confidential)\n"
                 "budget AND revenue AND NOT (draft OR preliminary)",
                 [("Expression:", "expr", "(budget OR revenue) AND NOT draft")],
                 lambda v: self._apply_wizard(search_text=v["expr"], expression=True)),

                ("Find dates in range", "Lines with dates in a specific range.\n"
                 "Use YYYY-MM-DD format. Dates must be valid (e.g., use 06-30 not 06-31).\n"
                 "Invalid dates will cause no results to be found.",
                 [("From:", "lo", "2026-01-01"), ("To:", "hi", "2026-12-31")],
                 lambda v: self._apply_wizard(search_text=r"\d{2}/\d{2}/\d{4}", regex=True, range_filters=f"date:{v['lo']}..{v['hi']}")),

                ("Regex pattern builder", "Opens a separate window with categorized regex presets (SSNs, invoices, part numbers, etc.).\n"
                 "Select a category, check the patterns you need, combine with OR or AND,\n"
                 "and optionally add your own custom regex. When you click Apply, the regex is\n"
                 "placed in the Search Terms field and Regex is checked in Advanced Search Options.",
                 [],
                 lambda v: self._open_search_wizard()),

                ("Search scanned PDFs and images (OCR)", "Enable OCR to extract text from scanned PDFs and image files.\n"
                 "Requires Tesseract to be installed. When you click Apply, the keywords are placed\n"
                 "in the Search Terms field and OCR is checked in Advanced Search Options.\n"
                 "Searches .bmp, .jpg, .jpeg, .png, .tif, .tiff in addition to normal file types.",
                 [("Keywords:", "keyword", "budget revenue")],
                 lambda v: (self._apply_wizard(search_text=v["keyword"]), self.ocr_var.set("on"))),

                ("Find keywords with surrounding context", "Show lines before and after each match so you can read the\n"
                 "full paragraph without opening the file. Default is OR mode — after clicking\n"
                 "Apply, you can check AND mode or Expression in Advanced Search Options to\n"
                 "change how the terms are combined. You can also use a boolean expression\n"
                 "directly in the Keywords field (e.g., \"(breach OR violation) AND contract\").",
                 [("Keywords:", "keyword", "breach liability"), ("Lines before:", "before", "3"), ("Lines after:", "after", "3")],
                 lambda v: self._apply_wizard(search_text=v["keyword"], context_before=v["before"], context_after=v["after"])),
            ]

            # Track which row the user has selected via its radio button.
            # 0 = nothing selected; radio values start at 1.
            selected_row = tk.IntVar(value=0)
            row_applies = {}  # idx -> callable that applies the row's settings

            for idx, (title, desc, fields, apply_fn) in enumerate(patterns, 1):
                frame = tk.LabelFrame(scroll_inner, text="", padx=8, pady=5)
                frame.pack(fill="x", padx=5, pady=(0, 8))

                # Radio button + title in a header row (replaces the LabelFrame's built-in title)
                rb = tk.Radiobutton(
                    frame, text=f"{idx}. {title}",
                    variable=selected_row, value=idx,
                    font=_sf(12, "bold"), anchor="w", justify="left",
                )
                rb.pack(anchor="w")

                tk.Label(frame, text=desc, font=_sf(10), fg="gray",
                         anchor="w", justify="left").pack(anchor="w", padx=(22, 0))

                entries = {}
                if fields:
                    field_frame = tk.Frame(frame)
                    field_frame.pack(fill="x", pady=(3, 0), padx=(22, 0))
                    for i, (label, key, placeholder) in enumerate(fields):
                        tk.Label(field_frame, text=label, font=_sf(11)).grid(row=0, column=i*2, padx=(0, 3), sticky="e")
                        entry_width = max(15, len(placeholder) + 3)
                        e = tk.Entry(field_frame, font=_sf(11), width=entry_width)
                        e.insert(0, placeholder)
                        e.grid(row=0, column=i*2+1, padx=(0, 10))
                        # Selecting the entry also selects this row's radio button
                        e.bind("<FocusIn>", lambda ev, i=idx: selected_row.set(i))
                        entries[key] = e

                def _make_apply(fn, ents, t):
                    def _click():
                        vals = {k: e.get().strip() for k, e in ents.items()}
                        fn(vals)
                        # Sync Recursive and OCR checkboxes to main screen
                        self.recursive_var.set("on" if wiz_recursive_var.get() else "off")
                        self.ocr_var.set("on" if wiz_ocr_var.get() else "off")
                        self._assistant_label.configure(text=f"Search Wizard: {t}")
                        self._assistant_label.grid(row=0, column=1, columnspan=2, padx=(5, 105), pady=(0, 0), sticky="sw")
                    return _click

                row_applies[idx] = _make_apply(apply_fn, entries, title)

            def _on_apply_clicked():
                idx = selected_row.get()
                apply_fn = row_applies.get(idx)
                if apply_fn:
                    apply_fn()
                else:
                    from tkinter import messagebox
                    messagebox.showinfo(
                        "No Selection",
                        "Please click the radio button next to the search type you want, "
                        "then click Apply.",
                        parent=win,
                    )

            def _clear_selection():
                selected_row.set(0)

            # Prominent bottom-center Apply button in a bordered group
            # (matches the Run Search button's look on the main screen)
            apply_group = ctk.CTkFrame(
                win, border_width=2, border_color=("gray40", "gray60"),
                corner_radius=8, fg_color=("gray85", "gray20"),
            )
            apply_group.pack(pady=(8, 4))

            apply_btn = ctk.CTkButton(
                apply_group, text="Apply", width=160, height=36,
                command=_on_apply_clicked,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="green", hover_color="darkgreen",
            )
            apply_btn.pack(side="left", padx=6, pady=6)
            Tooltip(apply_btn, "Apply the selected row's settings to the main screen — fills the Search Bar and enables matching options (regex, AND, OCR, etc.)")

            clear_sel_btn = ctk.CTkButton(
                apply_group, text="Clear Selection", width=120, height=36,
                command=_clear_selection,
                font=ctk.CTkFont(size=12),
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
            )
            clear_sel_btn.pack(side="left", padx=6, pady=6)
            Tooltip(clear_sel_btn, "Unpick the currently selected row so nothing is chosen — click a different radio button to pick a new one")

            ctk.CTkButton(
                win, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=win.destroy,
                font=ctk.CTkFont(size=12),
            ).pack(pady=(0, 10))

        def _apply_wizard(self, search_text="", regex=False, fuzzy=False,
                          wildcard=False, inverse=False, whole_word=False,
                          expression=False, and_mode=False, recursive=False,
                          file_types="", exclude="", proximity="",
                          range_filters="", context_before="", context_after=""):
            """Apply Search Wizard settings to the GUI fields."""
            # Sync folder from wizard to main screen
            if hasattr(self, "_sw_folder_label"):
                try:
                    sw_folder = self._sw_folder_label.cget("text")
                    if sw_folder and sw_folder != "(none)" and sw_folder != self.folder_entry.get().strip():
                        self.folder_entry.delete(0, "end")
                        self.folder_entry.insert(0, sw_folder)
                except Exception:
                    pass
            self.search_entry.delete(0, "end")
            if search_text:
                self.search_entry.insert(0, search_text)
            self.and_mode_var.set("on" if and_mode else "off")
            if hasattr(self, "_sync_and_or_colors"):
                self._sync_and_or_colors()
            self.recursive_var.set("on" if recursive else "off")
            self.regex_var.set("on" if regex else "off")
            self.fuzzy_var.set("on" if fuzzy else "off")
            self.wildcard_var.set("on" if wildcard else "off")
            self.inverse_var.set("on" if inverse else "off")
            self.whole_word_var.set("on" if whole_word else "off")
            self.expression_var.set("on" if expression else "off")
            self.file_types_entry.delete(0, "end")
            if file_types:
                self.file_types_entry.insert(0, file_types)
            self.exclude_entry.delete(0, "end")
            if exclude:
                self.exclude_entry.insert(0, exclude)
            self.proximity_entry.delete(0, "end")
            if proximity:
                self.proximity_entry.insert(0, proximity)
            self.range_entry.delete(0, "end")
            if range_filters:
                self.range_entry.insert(0, range_filters)
            self.context_before_entry.delete(0, "end")
            if context_before:
                self.context_before_entry.insert(0, context_before)
            self.context_after_entry.delete(0, "end")
            if context_after:
                self.context_after_entry.insert(0, context_after)

        def _show_search_wizard_help(self, parent):
            """Show help for the Search Wizard."""
            import tkinter as tk
            help_win = tk.Toplevel(parent)
            help_win.title("Search Wizard — Help")
            help_win.geometry("700x580")
            help_win.resizable(True, True)
            help_win.transient(parent)
            try:
                help_win.grab_set()
            except Exception:
                help_win.after(150, lambda: help_win.grab_set() if help_win.winfo_exists() else None)

            txt = tk.Text(help_win, wrap="word", font=("TkDefaultFont", 12),
                          padx=15, pady=10, borderwidth=0, highlightthickness=0)
            scroll = tk.Scrollbar(help_win, command=txt.yview)
            txt.configure(yscrollcommand=scroll.set)
            scroll.pack(side="right", fill="y")
            txt.pack(fill="both", expand=True)

            txt.tag_configure("heading", font=("TkDefaultFont", 14, "bold"),
                              spacing1=10, spacing3=5)
            txt.tag_configure("body", font=("TkDefaultFont", 12), spacing1=2)
            txt.tag_configure("example", font=("Courier", 11), lmargin1=30,
                              lmargin2=30, spacing1=2)

            def h(text):
                txt.insert("end", text + "\n", "heading")

            def b(text):
                txt.insert("end", text + "\n", "body")

            def e(text):
                txt.insert("end", text + "\n", "example")

            def blank():
                txt.insert("end", "\n")

            # Table of contents
            txt.tag_configure("toc_title", font=("TkDefaultFont", 14, "bold"), spacing1=5, spacing3=8)
            txt.tag_configure("toc_item", font=("TkDefaultFont", 11), lmargin1=20, lmargin2=20,
                              foreground="gray40")

            txt.insert("end", "TABLE OF CONTENTS\n", "toc_title")
            for section in [
                "What Is the Search Wizard?", "How to Use It",
                "Available Search Types", "Saving Your Search", "Tips",
            ]:
                txt.insert("end", f"\u2022 {section}\n", "toc_item")
            txt.insert("end", "\n")

            b("The Search Wizard helps you configure searches without memorizing")
            b("flags or regex syntax. Pick a type, fill in values, click Apply.")
            blank()

            h("WHAT IS THE SEARCH WIZARD?")
            b("The Search Wizard helps you configure searches without memorizing")
            b("flags, regex syntax, or advanced options. Pick a search type, fill")
            b("in your values, and click Apply \u2014 the wizard sets everything up.")
            b("For example, make selections in the Search Wizard and watch the")
            b("Search Terms field on the main screen and inputs on the Advanced")
            b("Search Options screen change accordingly.")
            blank()

            h("HOW TO USE IT")
            b("1. Scroll through the search types to find what you need")
            b("2. Fill in the input fields (placeholders show example values)")
            b("3. Click Apply \u2014 the wizard fills the search bar and enables")
            b("   the correct checkboxes in Advanced Search Options")
            b("4. Close the wizard \u2014 everything has been updated on the")
            b("   main screen. You're done with the wizard.")
            b("5. Click Run Search to execute, or click Save Search to")
            b("   save it for reuse later")
            blank()
            b("Once you click Apply, the wizard's job is done. All changes")
            b("are on the main screen and in Advanced Search Options. You")
            b("can close the wizard and edit anything further from there.")
            blank()
            b("The wizard configures the search type, terms, Recursive,")
            b("and OCR. You may still want to visit Advanced Search Options")
            b("to set other options before running:")
            blank()
            b("\u2022 File types \u2014 fill this in to limit to specific formats")
            b("\u2022 Exclude terms \u2014 fill this in to skip unwanted results")
            b("\u2022 Max Matches, Cores, Output Dir \u2014 adjust as needed")
            blank()
            b("The wizard isn't doing anything you can't do manually using")
            b("the search bar and Advanced Search Options. It just fills in")
            b("the fields for you. Using the wizard when you're starting out")
            b("is a good way to learn how Advanced Search Options works \u2014")
            b("watch what changes after each Apply and you'll quickly")
            b("understand how to configure searches on your own.")
            blank()

            h("AVAILABLE SEARCH TYPES")
            blank()
            b("Keywords (OR) — find lines with any of the terms")
            e("  budget revenue expenses")
            blank()
            b("Keywords (AND) — find lines with ALL terms")
            e("  budget approved Q1")
            blank()
            b("Multi-word phrases — enclose in double quotes to match as one unit")
            e('  "annual report"                 (exact phrase)')
            e('  "Q4 2025" budget                (phrase AND word with AND mode)')
            blank()
            b("Keywords with exclude — skip lines containing certain terms")
            e("  Keywords: budget revenue  Exclude: draft,preliminary")
            blank()
            b("Files missing terms (inverse) — find files that do NOT")
            b("contain specific required text")
            e("  Required terms: Authorized Signature")
            blank()
            b("SSNs, phone numbers, email addresses — pre-built regex")
            b("patterns, no typing needed. Just click Apply.")
            blank()
            b("Dollar amounts in range — find lines with dollar amounts")
            b("within a min/max range")
            e("  Min: 10000  Max: 50000")
            blank()
            b("Vendor with dollar amounts — find lines with a vendor name")
            b("AND a dollar amount (optionally in a range)")
            e("  Vendor: Acme  Min: 5000  Max: 25000")
            blank()
            b("Keywords in file types — search only certain formats")
            e("  Keywords: budget  Types: pdf,docx,xlsx")
            blank()
            b("Fuzzy matching — find misspelled terms or OCR errors")
            e("  Terms: accommodation receipt")
            blank()
            b("Proximity — find two terms within N words of each other")
            e("  Term 1: breach  Term 2: contract  N words: 5")
            blank()
            b("Boolean expression \u2014 combine AND, OR, NOT with parentheses.")
            b("No limit on terms or nesting depth. AND/OR/NOT must be UPPERCASE.")
            e("  (budget OR revenue OR limit OR expenses) AND NOT draft")
            e("  ((budget OR revenue) AND (approved OR signed)) OR draft")
            blank()
            b("Dates in range — find lines with dates in a specific range")
            e("  From: 2026-01-01  To: 2026-12-31")
            blank()
            b("Regex pattern builder — opens the categorized regex picker")
            b("with checkboxes for SSNs, invoice numbers, part numbers,")
            b("and dozens more patterns organized by profession.")
            blank()
            b("Search scanned PDFs (OCR) — enable OCR to extract text")
            b("from scanned PDFs and image files. Requires Tesseract.*")
            blank()
            b("Keywords with context — show lines before and after each")
            b("match so you can read the full paragraph in the results.")
            blank()

            h("SAVING YOUR SEARCH")
            b("After the wizard configures your search, click Save Search on the")
            b("main screen to save it by name. Saved searches can be reused later")
            b("with Load Search. It doesn't matter whether the wizard configured")
            b("the search or you did it manually \u2014 Save Search preserves")
            b("everything.")
            blank()

            h("TIPS")
            b("\u2022 The wizard replaces whatever is in the search bar each time")
            b("  you click Apply \u2014 save your search first if you want to keep it")
            b("\u2022 Placeholder values (gray text) are examples \u2014 replace them")
            b("  with your own values before clicking Apply")
            b("\u2022 Use Save Search to store a useful configuration by name so")
            b("  you can reload it later without reconfiguring everything")
            blank()

            b("* Tesseract is a free, open-source OCR engine that extracts")
            b("  text from scanned documents and images. peekdocs uses it")
            b("  when the OCR option is enabled. It must be installed")
            b("  separately: macOS: brew install tesseract | Windows:")
            b("  download from github.com/UB-Mannheim/tesseract | Linux:")
            b("  sudo apt install tesseract-ocr. See the User Guide")
            b("  'Prerequisites' section for full details.")
            blank()

            txt.configure(state="disabled")

            close_btn = ctk.CTkButton(
                help_win, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=help_win.destroy,
                font=ctk.CTkFont(size=12),
            )
            close_btn.pack(pady=(5, 10))

        def _show_search_options_help(self):
            """Show help for the search options group: AND/OR, Recursive, Whole Word."""
            import tkinter as tk
            win = tk.Toplevel(self)
            win.title("Search Options \u2014 Help")
            win.geometry("740x680")
            win.resizable(True, True)
            win.transient(self)
            try:
                win.grab_set()
            except Exception:
                win.after(150, lambda: win.grab_set() if win.winfo_exists() else None)

            txt_frame = tk.Frame(win)
            txt_frame.pack(fill="both", expand=True, padx=10, pady=10)
            scrollbar = tk.Scrollbar(txt_frame)
            scrollbar.pack(side="right", fill="y")
            txt = tk.Text(
                txt_frame, wrap="word", font=("TkDefaultFont", 12),
                yscrollcommand=scrollbar.set, padx=10, pady=10,
                borderwidth=1, relief="sunken",
            )
            txt.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=txt.yview)

            txt.tag_configure("heading", font=("TkDefaultFont", 13, "bold"), spacing1=8, spacing3=4)
            txt.tag_configure("body", font=("TkDefaultFont", 12), lmargin1=10, lmargin2=10, spacing3=2)
            txt.tag_configure("example", font=("Courier", 11), lmargin1=20, lmargin2=20, spacing3=2)
            txt.tag_configure("toc_title", font=("TkDefaultFont", 14, "bold"), spacing1=5, spacing3=8)
            txt.tag_configure("toc_item", font=("TkDefaultFont", 11), lmargin1=20, lmargin2=20,
                              foreground="gray40")

            def h(s): txt.insert("end", s + "\n", "heading")
            def b(s): txt.insert("end", s + "\n", "body")
            def e(s): txt.insert("end", s + "\n", "example")
            def blank(): txt.insert("end", "\n")

            txt.insert("end", "TABLE OF CONTENTS\n", "toc_title")
            for section in [
                "AND / OR Mode",
                "Recursive",
                "Whole Word",
                "Defaults & Saving",
                "Advanced Search Options",
            ]:
                txt.insert("end", f"\u2022 {section}\n", "toc_item")
            txt.insert("end", "\n")

            h("AND / OR MODE")
            b("Controls how multiple search terms are combined.")
            blank()
            b("OR mode (default, highlighted green)")
            b("Finds lines containing ANY of your search terms. Each term is")
            b("searched independently. More terms = more results.")
            blank()
            e("  Search: invoice receipt")
            e("  Finds lines with 'invoice' OR 'receipt'")
            blank()
            b("AND mode")
            b("Finds paragraphs where ALL search terms appear. Fewer results,")
            b("but every result contains every term. Useful when searching for")
            b("a combination of words.")
            blank()
            e("  Search: Smith invoice 2024")
            e("  Finds paragraphs with 'Smith' AND 'invoice' AND '2024'")
            blank()
            b("The active mode is shown in green. Click the other button to")
            b("switch. This setting is synced with the AND mode checkbox in")
            b("Advanced Search Options.")
            blank()

            h("RECURSIVE")
            b("When checked, peekdocs searches all subfolders inside the")
            b("selected folder, no matter how deeply nested. When unchecked,")
            b("only files directly in the chosen folder are searched \u2014")
            b("subfolders are ignored.")
            blank()
            e("  \u2611 Recursive: /Documents and all its subfolders")
            e("  \u2610 Recursive: only files directly in /Documents")
            blank()
            b("This is checked by default. If you have a large folder tree")
            b("and want to search only the top level, uncheck it. Synced with")
            b("the Recursive checkbox in Advanced Search Options.")
            blank()

            h("WHOLE WORD")
            b("When checked, search terms must match complete words. A word")
            b("boundary is a space, punctuation, or the start/end of a line.")
            blank()
            e("  \u2611 Whole Word: 'bob' matches 'bob' but NOT 'bobcat'")
            e("  \u2610 Whole Word: 'bob' matches 'bob', 'bobcat', 'bobsled'")
            blank()
            b("This is checked by default to avoid partial matches that")
            b("clutter your results. Uncheck it when you want to find word")
            b("fragments, suffixes, or substrings. Synced with the Whole Word")
            b("checkbox in Advanced Search Options.")
            blank()

            h("DEFAULTS & SAVING")
            b("Recursive and Whole Word are checked by default on every")
            b("launch. OR mode is the default search mode.")
            blank()
            b("To save your preferred settings for next time, open Advanced")
            b("Search Options and click 'Save Settings'. Your choices are")
            b("stored in ~/.peekdocsrc and restored automatically on the")
            b("next launch.")
            blank()

            h("WHY THESE CONTROLS APPEAR ON THE MAIN SCREEN")
            b("AND/OR, Recursive, and Whole Word are the most frequently")
            b("used search options, so they are placed on the main screen")
            b("for quick access. These same controls also appear inside")
            b("the Advanced Search Options panel \u2014 they are always kept")
            b("in sync, so changing one automatically updates the other.")
            blank()
            b("The Advanced Search Options panel (click the \u25b6 Advanced")
            b("Search Options toggle to expand it) offers additional modes")
            b("like Fuzzy, Wildcard, Regex, Expression, Inverse, OCR,")
            b("file type filters, exclude terms, proximity, context lines,")
            b("and range queries.")

            txt.configure(state="disabled")

            close_btn = ctk.CTkButton(
                win, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=win.destroy,
                font=ctk.CTkFont(size=12),
            )
            close_btn.pack(pady=(5, 10))

        def _show_search_help(self):
            """Show a quick-start guide with search examples by category."""
            import tkinter as tk
            help_win = tk.Toplevel(self)
            help_win.title("Search Examples & Quick-Start Guide")
            help_win.geometry("750x700")
            help_win.resizable(True, True)
            help_win.transient(self)
            try:
                help_win.grab_set()
            except Exception:
                help_win.after(150, lambda: help_win.grab_set() if help_win.winfo_exists() else None)
            help_win.lift()
            help_win.after(50, help_win.lift)
            help_win.after(100, help_win.focus_force)

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

            # Table of contents
            txt.tag_configure("toc_title", font=("TkDefaultFont", 13, "bold"), spacing1=5, spacing3=8)
            txt.tag_configure("toc_item", font=("TkDefaultFont", 11), lmargin1=20, lmargin2=20,
                              foreground="gray40")

            txt.insert("end", "TABLE OF CONTENTS\n", "toc_title")
            for section in [
                "What Is peekdocs?", "Who Is It For?", "Getting Started",
                "Saving and Loading Searches", "Simple Search",
                "Phrase Search (Quoted Terms)", "AND Mode",
                "Boolean Expressions", "Breaking Down Complex Searches",
                "Tips", "Troubleshooting",
                "Files Created by peekdocs", "Search Mode Checkboxes",
                "Text Fields", "Combining Modes", "Settings Buttons",
            ]:
                txt.insert("end", f"\u2022 {section}\n", "toc_item")
            txt.insert("end", "\n")

            h("WHAT IS PEEKDOCS?")
            b("peekdocs searches Word docs, PDFs, spreadsheets, emails,")
            b("archives, and 46 file types \u2014 all at once, all offline. Your")
            b("files never leave your computer. Results are presented on")
            b("screen and in a Word document with every match highlighted")
            b("in yellow. peekdocs never modifies, moves, or deletes your")
            b("files.")
            blank()

            h("WHO IS IT FOR?")
            txt.tag_configure("body_bold_who", font=("TkDefaultFont", 12, "bold"), lmargin1=20, lmargin2=20)
            txt.insert("end", "\u2022 Home users", "body_bold_who")
            txt.insert("end", " \u2014 search personal documents, Google Docs\n", "body")
            b("  backups, tax records, family files. Just type a keyword")
            b("  and click Run Search. Recent searches remember your last")
            b("  10 searches so you can quickly repeat them.")
            blank()
            txt.insert("end", "\u2022 Small businesses", "body_bold_who")
            txt.insert("end", " \u2014 find information across contracts,\n", "body")
            b("  invoices, reports, and correspondence. Use AND mode,")
            b("  file type filters, and range queries to narrow results.")
            blank()
            b("You don't need to use every feature. Start with a simple")
            b("keyword search and explore from there.")
            blank()

            h("GETTING STARTED")
            b("All searches are case-insensitive. Type your terms in the Search Bar,")
            b("pick a folder with Browse, and click Run Search. Use the checkboxes")
            b("under Advanced Search Options to change search modes \u2014 do not type flags in")
            b("the search box. Results are saved to peekdocs_results.txt and .docx.")
            blank()
            b("Quick tips: Click the \u25bc button next to the search bar to reuse one of")
            b("your last 10 searches. While a search is running, the status line shows")
            b("how many terms are being searched. In the Results Preview, right-click")
            b("to copy text and double-click a filename to open it in your default app.")
            blank()
            b("After a search, click the View N matched file(s) link on the status")
            b("line to see the list of files with match counts and line numbers.")
            b("Double-click a file to open it in its default app, or click View Text")
            b("(with line numbers) to see the file's extracted content with line")
            b("numbers and matches highlighted in yellow.")
            blank()

            h("SAVING AND LOADING SEARCHES")
            b("Save Search saves your current search terms AND all settings in")
            b("Advanced Search Options (checkboxes, file types, exclude terms, range")
            b("filters, proximity, etc.) as a named search. Give it a name like")
            b("'find_ssns' or 'missing_signature'. Saved searches are stored in")
            b("the folder's .peekdocs_collection.json file.")
            blank()
            b("Load Saved Search restores a previously saved search \u2014 it loads")
            b("the search terms back into the search box AND restores all the")
            b("Advanced Search Options settings exactly as they were when you saved it.")
            b("This lets you re-run the same search later with one click.")
            blank()
            b("It doesn't matter whether you configured the search yourself or")
            b("the Search Wizard set it up for you \u2014 as long as you remember")
            b("to save the search, everything gets preserved.")
            blank()
            s("Save Search vs Save Defaults \u2014 what's the difference?")
            b("\u2022 Save Search (main screen) \u2014 saves the current search terms")
            b("  and settings by name for reuse. Stored per folder in")
            b("  .peekdocs_collection.json.")
            b("\u2022 Save Defaults (Advanced Search Options) \u2014 saves your")
            b("  preferred settings as defaults for every future session.")
            b("  Stored once in ~/.peekdocsrc. Use this to set your")
            b("  preferred starting configuration.")
            blank()

            h("SIMPLE SEARCH")
            b("Type one or more terms separated by spaces. By default, any term matches (OR mode).")
            e("budget                \u2192  finds lines containing \"budget\"")
            e("budget revenue        \u2192  finds lines with \"budget\" OR \"revenue\"")
            e("\"annual report\"       \u2192  exact phrase match (use quotes)")
            blank()

            h("PHRASE SEARCH (QUOTED TERMS)")
            b("To find a multi-word phrase as a single unit, enclose it in")
            b("double quotes. Without quotes, each space-separated word is")
            b("treated as a separate search term.")
            e('"annual report"              \u2192  exact phrase "annual report"')
            e('annual report                \u2192  "annual" OR "report" (two terms)')
            e('"Q4 2025" budget             \u2192  phrase AND word (with AND mode)')
            blank()
            b("Phrase search works in plain, AND, expression, and inverse modes.")
            b("Inside Boolean expressions, quote phrases directly:")
            e('("annual report" OR "yearly report") AND 2024')
            blank()

            h("AND MODE")
            b("Check the AND mode checkbox. All terms must appear in the same line.")
            e("budget revenue        \u2192  line must contain both words")
            e("\"Q1\" \"2024\"           \u2192  line must contain both phrases")
            blank()

            h("BOOLEAN EXPRESSIONS")
            b("Check the Expression checkbox. Combine AND, OR, NOT with parentheses.")
            b("No limit on terms or nesting depth. AND/OR/NOT must be UPPERCASE.")
            e("budget AND revenue")
            e("(bob AND amy) OR fred")
            e("(budget OR revenue OR limit OR expenses) AND approved")
            e("contract NOT draft")
            e("(salary OR bonus) AND NOT confidential")
            e("((budget OR revenue) AND (approved OR signed)) OR draft")
            blank()

            b("For help with Fuzzy, Regex, Wildcard, Whole Word, Proximity,")
            b("Range Filters, Context Lines, and other advanced options, click")
            b("the ? button inside the Advanced Search Options window.")
            blank()

            h("BREAKING DOWN COMPLEX SEARCHES")
            b("When a single search becomes too complex, break it into")
            b("several focused searches and run them one at a time, or")
            b("save each one and reload them later with Load Search.")
            blank()
            s("Why this helps")
            b("\u2022 Each search is simpler to configure and understand")
            b("\u2022 You see exactly which files matched which check")
            b("\u2022 Easy to update one check without affecting the others")
            b("\u2022 Saved searches can be reloaded and re-run later")
            blank()
            s("Example: Breaking down a document review")
            b("Instead of one giant search, save a series of focused searches:")
            e('1. "find_contracts"   \u2014 Terms: contract')
            e('2. "missing_date"     \u2014 Regex: \\d{2}/\\d{2}/\\d{4}   + Inverse')
            e('3. "no_draft_stamp"   \u2014 Terms: DRAFT')
            e('4. "amounts_in_range" \u2014 Range: amount:1000..50000')
            e('5. "has_ssn"          \u2014 Regex: \\d{3}-\\d{2}-\\d{4}')
            b("Use Load Search to reload each one when you need it.")
            blank()

            h("TIPS")
            b("\u2022 Use Save Search to save useful configurations by name for reuse.")
            b("\u2022 Click User Guide in the toolbar for full documentation on GitHub.")
            blank()

            h("TROUBLESHOOTING: SEARCH NOT FINDING EXPECTED RESULTS?")
            b("If a search returns no results (or fewer than expected) for")
            b("terms you know exist in your documents, check Advanced Search")
            b("Options for leftover settings from a previous search. Common")
            b("culprits:")
            blank()
            b("\u2022 Recursive \u2014 if unchecked, only looks in the selected folder")
            b("  and ignores subfolders")
            b("\u2022 File types \u2014 limits the search to specific formats")
            b("\u2022 Exclude terms \u2014 silently drops matching lines")
            b("\u2022 Specific files \u2014 restricts to a single file")
            b("\u2022 Range filters \u2014 filters out lines outside the range")
            b("\u2022 Inverse checked \u2014 shows files missing your terms")
            b("\u2022 Regex or Expression checked \u2014 changes how terms")
            b("  are interpreted")
            blank()
            b("Open Advanced Search Options and click Reset All Fields (the")
            b("red button) to clear everything and start fresh.")
            blank()
            b("If Use Index is checked, try unchecking it and searching")
            b("directly. A stale index may not contain recently added or")
            b("changed files. When you build an index, Auto-Refresh is")
            b("set to 1 hour automatically to keep it current. You can")
            b("change the interval in Manage Indexes:")
            blank()
            b("\u2022 5\u201315 min \u2014 folders where files change frequently")
            b("\u2022 30 min\u20131 hour \u2014 folders that change occasionally")
            b("\u2022 4\u201324 hours \u2014 stable folders checked periodically")
            b("\u2022 Off \u2014 rebuild manually with Build Index(es) when needed")
            blank()
            b("Auto-refresh runs in the background while the app is open")
            b("and does not interrupt searches.")
            blank()
            b("Files over 100 MB are automatically skipped to prevent slow")
            b("searches and memory issues. The status line shows how many")
            b("files were skipped. Click View Error Log to see which files")
            b("and why. To change the limit, set Max File Size (MB) in")
            b("Advanced Search Options. Set to 0 for no limit. When you")
            b("change the limit, the index is automatically rebuilt on")
            b("the next indexed search.")
            blank()
            b("After each search, click View N excluded file(s) on the")
            b("status line to see every file that was NOT searched, grouped")
            b("by reason (unsupported type, prior search output, oversized,")
            b("hidden file, etc.). This explains any difference between")
            b("peekdocs's file count and a manual count of the folder.")
            blank()
            b("Sanity check: searched + excluded should equal the total")
            b("number of files in the folder. Count all files with:")
            blank()
            e("  macOS/Linux:  find \"/path/to/folder\" -type f | wc -l")
            e("  Windows PS:   (Get-ChildItem -Recurse -File -Force).Count")
            blank()
            b("This shows that every file was either searched or explicitly")
            b("excluded with a documented reason.")
            blank()

            h("FILES CREATED BY PEEKDOCS")
            b("peekdocs never modifies, moves, or deletes your original")
            b("documents. It creates its own files for reports, indexes, and")
            b("settings. Buttons like Clear Results and Delete Index only")
            b("delete files that peekdocs created \u2014 never your documents.")
            b("All peekdocs files are safe to delete manually too \u2014")
            b("peekdocs recreates them as needed.")
            blank()
            s("Search reports (overwritten each search)")
            e("peekdocs_results.txt       \u2014 text report")
            e("peekdocs_results.docx      \u2014 Word report with highlights")
            e("peekdocs_results.csv       \u2014 optional (-o csv)")
            e("peekdocs_results.json      \u2014 optional (-o json)")
            blank()
            s("Saved/archived reports")
            e("DO_NOT_SEARCH_{name}.txt/docx          \u2014 saved with -s")
            e("DO_NOT_SEARCH_ACCUMULATED_{name}.*     \u2014 appended with -sa")
            blank()
            s("PII scan reports")
            e("DO_NOT_SEARCH_pii_scan_report.docx     \u2014 PII Scan report")
            blank()
            s("Error log")
            e("peekdocs_errors.log        \u2014 files that couldn't be read + crash reports")
            blank()
            s("Index (optional)")
            e(".peekdocs.db               \u2014 search index (SQLite)")
            e(".peekdocs.db-wal/-shm      \u2014 temporary SQLite files")
            blank()
            s("Settings & data")
            e(".peekdocs_collection.json  \u2014 saved searches (per folder)")
            e("~/.peekdocsrc              \u2014 user settings (home directory)")
            b("The 'rc' in .peekdocsrc stands for 'run commands' \u2014 a Unix naming")
            b("convention meaning 'config file' (same as .bashrc, .vimrc, etc.).")
            blank()
            s("Key points")
            b("\u2022 All DO_NOT_SEARCH_ files are automatically excluded from searches")
            b("\u2022 All peekdocs internal files (.db, .log, .json config) are excluded")
            b("\u2022 Most files are safe to delete \u2014 peekdocs recreates them as needed")
            blank()
            s("Upgrading peekdocs")
            b("When you upgrade to a new version, only the code is replaced.")
            b("Your saved searches, settings, indexes, and reports are stored")
            b("in your home directory and document folders \u2014 they are never")
            b("touched by an upgrade. No migration needed.")
            blank()
            s("Backing up your work")
            b("Only two files matter \u2014 everything else can be regenerated:")
            blank()
            b("\u2022 ~/.peekdocsrc \u2014 your settings")
            b("  (one file in your home directory)")
            blank()
            b("\u2022 .peekdocs_collection.json \u2014 your saved searches")
            b("  (one per search folder, hidden file)")
            blank()
            b("Copy these to a safe location before major changes. If you")
            b("search multiple folders, back up the .peekdocs_collection.json")
            b("in each one. On macOS, press Cmd+Shift+. in Finder to see")
            b("hidden files. On Windows, enable 'Show hidden items' in the")
            b("View tab of File Explorer.")
            blank()
            s("If ~/.peekdocsrc is deleted")
            b("Nothing breaks \u2014 peekdocs uses built-in defaults. To recover:")
            b("1. Open Advanced Search Options, set your preferences, click Save Defaults")
            b("2. Change Text Size dropdown if needed (auto-saves immediately)")
            b("\u2022 Use Clear Results, Clear Error Log, or Delete Index to manage")
            b("  files from the GUI")
            blank()
            s("Building a search index")
            b("1. Browse to the folder you want to index")
            b("2. Click Manage Indexes (below Advanced Search Options)")
            b("3. Click Build Index(es)")
            b("4. Check Search Using Index(es) in Advanced Search Options")
            b("The index automatically includes all subfolders \u2014 one")
            b("index in your top folder covers everything underneath it.")
            b("You don't need to build separate indexes in each subfolder.")
            b("The index speeds up repeated searches on large folders.")
            b("\u2022 See the full file reference in the README for details on each file")

            txt.configure(state="disabled")

            close_btn = ctk.CTkButton(
                help_win, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=help_win.destroy,
                font=ctk.CTkFont(size=12),
            )
            close_btn.pack(pady=(5, 10))

        def _show_advanced_help(self):
            """Show help for all Advanced Search Options with examples."""
            import tkinter as tk
            help_win = tk.Toplevel(self.advanced_window or self)
            help_win.title("Advanced Search Options — Help")
            help_win.geometry("750x620")
            help_win.resizable(True, True)
            if self.advanced_window:
                help_win.transient(self.advanced_window)

            # Pack the Close button FIRST, anchored to the bottom, so the
            # scrollable text frame below cannot push it off-screen.
            close_btn = ctk.CTkButton(
                help_win, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=help_win.destroy,
                font=ctk.CTkFont(size=12),
            )
            close_btn.pack(side="bottom", pady=(5, 10))

            text_frame = tk.Frame(help_win)
            text_frame.pack(side="top", fill="both", expand=True, padx=10, pady=(10, 5))
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

            # Table of contents
            txt.tag_configure("toc_title", font=("TkDefaultFont", 13, "bold"), spacing1=5, spacing3=8)
            txt.tag_configure("toc_item", font=("TkDefaultFont", 11), lmargin1=20, lmargin2=20,
                              foreground="gray40")

            txt.insert("end", "TABLE OF CONTENTS\n", "toc_title")
            for section in [
                "Search Mode Checkboxes", "Text Fields",
                "Combining Modes", "Settings Buttons", "Troubleshooting",
            ]:
                txt.insert("end", f"\u2022 {section}\n", "toc_item")
            txt.insert("end", "\n")

            h("SEARCH MODE CHECKBOXES")
            blank()

            s("AND Mode")
            b("All search terms must appear in the same line (paragraph).")
            b("Without AND mode, any single term matching is enough (OR mode).")
            e("budget revenue        \u2192  line must contain BOTH words")
            blank()

            s("Phrase Search (Quoted Terms)")
            b("To search for a multi-word phrase as a single unit, enclose it")
            b("in double quotes. Without quotes, each space-separated word is")
            b("treated as a separate search term.")
            e('"annual report"                   \u2192  exact phrase')
            e('"Q4 2025" budget                  \u2192  phrase AND word (with AND mode)')
            e('insecure core                     \u2192  two separate terms')
            blank()
            b("Phrase search works in plain, regex, expression, and inverse")
            b("modes. In Boolean expressions, quote phrases inside the")
            b("expression: (\"annual report\" OR \"yearly report\") AND 2024")
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
            e("rec1pe                \u2192  finds \"recipe\" (OCR error)")
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
            b("Useful when you want to find files that are missing something")
            b("they should contain.")
            e("Terms: confidentiality    Inverse: ON")
            e("\u2192  lists files WITHOUT the word \"confidentiality\"")
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

            s("Max File Size (MB)")
            b("Skip files larger than this size. Default: 100 MB. Very large files")
            b("(huge PDFs, massive spreadsheets) can cause slow searches or exhaust")
            b("memory. Skipped files are logged to peekdocs_errors.log with a message")
            b("explaining why. Set to 0 for no limit if you need to search large files.")
            b("Changing this value automatically rebuilds the index on the next")
            b("indexed search, so results stay consistent.")
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
            b("Check CSV, JSON, and/or PDF to generate additional report files.")
            b("PDF highlights matches in yellow, like the DOCX report.")
            b("Check Timestamp to add a timestamp to report filenames.")
            blank()

            s("Search Using Index(es)")
            b("Use the search index for faster repeated searches.")
            b("Build the index first using Manage Indexes on the main screen.")
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
            s("Inspect .peekdocsrc")
            b("View the current saved settings file (read-only).")
            s("Save As Defaults")
            b("Save all current Advanced Search Options as defaults to ~/.peekdocsrc.")
            b("These are restored automatically when peekdocs starts.")
            b("Not required for the current search \u2014 your selections take")
            b("effect immediately on the next Run Search. Save Defaults is")
            b("only for making your choices persist across sessions.")
            blank()
            b("This is different from Save Search on the main screen, which")
            b("saves the current search terms and settings by name so you")
            b("can reload them later. Save Defaults sets your preferred")
            b("starting configuration. Save Search saves a specific named")
            b("search.")
            s("Restore Settings")
            b("Reload saved defaults from ~/.peekdocsrc into the GUI.")
            s("Reset All Fields")
            b("Clear all fields and reset to defaults. Does not modify the config file.")
            blank()

            h("TROUBLESHOOTING: SEARCH NOT FINDING EXPECTED RESULTS?")
            b("If a search returns no results (or fewer than expected) for")
            b("terms you know exist in your documents, check the fields")
            b("above for leftover settings from a previous search. Common")
            b("culprits:")
            blank()
            b("\u2022 Recursive \u2014 if unchecked, only looks in the selected folder")
            b("  and ignores subfolders")
            b("\u2022 File types \u2014 limits the search to specific formats")
            b("\u2022 Exclude terms \u2014 silently drops matching lines")
            b("\u2022 Specific files \u2014 restricts to a single file")
            b("\u2022 Range filters \u2014 filters out lines outside the range")
            b("\u2022 Inverse checked \u2014 shows files missing your terms")
            b("\u2022 Regex or Expression checked \u2014 changes how terms")
            b("  are interpreted")
            blank()
            b("Click Reset All Fields (the red button at the bottom) to")
            b("clear everything and start fresh.")
            blank()
            b("If Use Index is checked on the main screen, try unchecking")
            b("it and searching directly. A stale index may not contain")
            b("recently added or changed files. Use Auto-Refresh in Manage")
            b("Indexes to keep the index current automatically:")
            blank()
            b("\u2022 5\u201315 min \u2014 folders where files change frequently")
            b("\u2022 30 min\u20131 hour \u2014 folders that change occasionally")
            b("\u2022 4\u201324 hours \u2014 stable folders checked periodically")
            b("\u2022 Off \u2014 rebuild manually with Build Index(es) when needed")

            txt.configure(state="disabled")

        def _build_folder_row(self):
            """Build the folder selection row in the shared _input_frame at row 0."""
            label = ctk.CTkLabel(self._input_frame, text="1. Search Folder:", font=ctk.CTkFont(size=18, weight="bold"), width=200, anchor="w")
            label.grid(row=0, column=0, padx=(10, 2), pady=(4, 8), sticky="w")

            self.folder_entry = ctk.CTkEntry(self._input_frame, font=ctk.CTkFont(size=14))
            self.folder_entry.grid(row=0, column=1, padx=(5, 25), pady=(4, 8), sticky="ew")
            self.folder_entry.insert(0, os.path.expanduser("~"))

            self._browse_frame = ctk.CTkFrame(self._input_frame, fg_color="transparent")
            self._browse_frame.grid(row=0, column=2, padx=(5, 10), pady=(4, 8), sticky="w")

            self.browse_button = ctk.CTkButton(
                self._browse_frame, text="Browse", width=60, command=self.browse_folder,
                font=ctk.CTkFont(size=14),
            )
            self.browse_button.pack(side="left", padx=(0, 3))
            Tooltip(self.browse_button, "Browse for a folder to search", anchor="left")

            self.browse_file_button = ctk.CTkButton(
                self._browse_frame, text="Single File", width=80, command=self._browse_file,
                font=ctk.CTkFont(size=14),
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
            )
            self.browse_file_button.pack(side="left")
            Tooltip(self.browse_file_button, "Browse for a specific file to search", anchor="left")

            self._clear_file_btn = ctk.CTkButton(
                self._browse_frame, text="\u2715", width=24, height=24,
                font=ctk.CTkFont(size=12),
                fg_color="transparent", text_color=("gray50", "gray50"),
                hover_color=("gray90", "gray25"),
                command=self._clear_specific_file,
            )
            # Hidden until a file is selected
            Tooltip(self._clear_file_btn, "Clear the selected file and search the entire folder", anchor="left")

            search_help_btn = ctk.CTkButton(
                self, text="?", width=28, height=28,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self._show_search_help,
            )
            search_help_btn.place(relx=1.0, y=8, anchor="ne", x=-15)
            Tooltip(search_help_btn, "Search examples and quick-start guide", anchor="left")

            Tooltip(self.folder_entry, "The folder or file to search. Use Browse to pick a folder, Single File to pick a specific file")

        def _build_advanced_toggle(self):
            """Build the toggle button for Advanced Search Options."""
            self.advanced_toggle = ctk.CTkButton(
                self._toggle_row,
                text="\u25b6 Advanced Search Options", width=0,
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                anchor="w",
                command=self.toggle_advanced,
                font=ctk.CTkFont(size=13),
            )
            self.advanced_toggle.pack(side="left", padx=(0, 20))
            Tooltip(self.advanced_toggle, "Open the Advanced Search Options panel — AND mode, regex, fuzzy, file types, exclude terms, range filters, and all other search settings")

            self._search_wiz_btn = ctk.CTkButton(
                self._toggle_row,
                text="\u25b6 Search Wizard", width=0,
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                anchor="w",
                command=self._open_search_wizard_guide,
                font=ctk.CTkFont(size=13),
            )
            self._search_wiz_btn.pack(side="left", padx=(20, 20))
            Tooltip(self._search_wiz_btn, "Search Wizard — guided search builder with 20+ pre-built patterns. Pick a search type, fill in values, and apply. No flags or regex knowledge needed")

            self.sensitive_scan_btn = ctk.CTkButton(
                self._toggle_row,
                text="\u25b6 PII Scan", width=0,
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                anchor="w",
                command=self._start_sensitive_scan,
                font=ctk.CTkFont(size=13),
            )
            self.sensitive_scan_btn.pack(side="left", padx=(20, 20))
            Tooltip(self.sensitive_scan_btn, "PII Scan — one-click scan for SSNs, credit cards, tax IDs, emails, phone numbers, passwords, dates of birth, and user-configurable dollar-amount ranges. Advanced users can also add their own custom regex pattern")

        def _build_advanced_panel(self):
            """Build the Advanced Search Options popup window with all search mode checkboxes and fields."""
            # Create popup window for Advanced Search Options
            self.advanced_window = ctk.CTkToplevel(self)
            self.advanced_window.title("Advanced Search Options")
            self.advanced_window.after(100, lambda: self.advanced_window.title("Advanced Search Options"))
            self.advanced_window.geometry("900x720")
            self.advanced_window.resizable(True, True)
            self.advanced_window.protocol("WM_DELETE_WINDOW", self._close_advanced_window)
            # Withdraw after event loop starts to avoid flash
            self.advanced_window.withdraw()
            self.after(10, self.advanced_window.withdraw)

            self.advanced_frame = ctk.CTkFrame(self.advanced_window)
            self.advanced_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Header with description and ? help button
            adv_header_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
            adv_header_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=(0, 5), sticky="ew")
            adv_header_frame.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                adv_header_frame,
                text="All searches are based on this screen and the Search Terms on the main screen. Your selections take effect immediately on the next Run Search \u2014 no need to press Save As Defaults. That button saves your settings as permanent defaults for future sessions.",
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray50"),
                justify="left",
                wraplength=600,
            ).grid(row=0, column=0, sticky="w")
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

            # and_mode_var and recursive_var are already created in _build_search_row
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

            # whole_word_var already created in _build_search_row
            cb_whole_word = ctk.CTkCheckBox(
                cb_frame, text="Whole Word", variable=self.whole_word_var,
                onvalue="on", offvalue="off",
            )
            cb_whole_word.grid(row=1, column=3, padx=(0, 15), pady=0, sticky="w")
            Tooltip(cb_whole_word, "Matches complete words only. 'bob' matches 'bob' but not 'bobcat'. Synced with the Whole Word checkbox on the search row")

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

            # Row 3: proximity + context lines
            ctk.CTkLabel(self.advanced_frame, text="Proximity:").grid(
                row=4, column=0, padx=(15, 5), pady=5, sticky="e"
            )
            num_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
            num_frame.grid(row=4, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="w")

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
                row=5, column=0, padx=(15, 5), pady=5, sticky="e"
            )
            cores_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
            cores_frame.grid(row=5, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="w")

            self.cores_entry = ctk.CTkEntry(cores_frame, width=60)
            self.cores_entry.insert(0, str(self._default_cores))
            self.cores_entry.grid(row=0, column=0)

            cores_frame.grid_columnconfigure(1, minsize=110)
            ctk.CTkLabel(cores_frame, text="Max Matches:").grid(row=0, column=1, padx=(20, 5), sticky="e")
            self.max_matches_entry = ctk.CTkEntry(cores_frame, width=60)
            self.max_matches_entry.insert(0, "1000")
            self.max_matches_entry.grid(row=0, column=2)

            ctk.CTkLabel(cores_frame, text="Max File Size (MB):").grid(row=0, column=3, padx=(20, 5), sticky="e")
            self.max_file_size_entry = ctk.CTkEntry(cores_frame, width=60)
            self.max_file_size_entry.insert(0, "100")
            self.max_file_size_entry.grid(row=0, column=4)

            # Row 6: range filters
            ctk.CTkLabel(self.advanced_frame, text="Range:").grid(
                row=6, column=0, padx=(15, 5), pady=5, sticky="e"
            )
            self.range_entry = ctk.CTkEntry(
                self.advanced_frame, placeholder_text="Ex: amount:1000..5000, date:2024-01-01..2024-12-31"
            )
            self.range_entry.grid(row=6, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="ew")
            Tooltip(self.range_entry, "Range filter: field:min..max (comma-separated for multiple). Fields: date, amount, number, percent, age, time, filesize, filedate. Use fn: prefix for filename ranges (e.g. fn:date:2024-01-01..2024-12-31). Open-ended ranges: amount:1000.. or amount:..5000")

            # Row 7: specific files
            ctk.CTkLabel(self.advanced_frame, text="Specific files:").grid(
                row=7, column=0, padx=(15, 5), pady=5, sticky="e"
            )
            self.specific_files_entry = ctk.CTkEntry(
                self.advanced_frame, placeholder_text="Ex: report.pdf,notes.txt"
            )
            self.specific_files_entry.grid(row=7, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="ew")

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
            Tooltip(outdir_browse_btn, "Pick a folder where peekdocs should write its reports, error log, and other output files", anchor="left")
            Tooltip(self.output_dir_entry, "Directory for search output files (reports, error log, CSV, JSON). Leave empty to write to the search folder.")

            # Row 9: additional output formats
            output_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
            output_frame.grid(row=10, column=0, columnspan=3, padx=15, pady=(0, 10), sticky="w")

            ctk.CTkLabel(output_frame, text="Also output report as ==>").grid(row=0, column=0, padx=(0, 10))
            self.output_csv_var = ctk.StringVar(value="off")
            self.output_json_var = ctk.StringVar(value="off")
            self.output_pdf_var = ctk.StringVar(value="off")
            cb_csv = ctk.CTkCheckBox(
                output_frame, text="CSV", variable=self.output_csv_var,
                onvalue="on", offvalue="off",
            )
            cb_csv.grid(row=0, column=1, padx=(0, 15))
            cb_json = ctk.CTkCheckBox(
                output_frame, text="JSON", variable=self.output_json_var,
                onvalue="on", offvalue="off",
            )
            cb_json.grid(row=0, column=2, padx=(0, 15))
            cb_pdf = ctk.CTkCheckBox(
                output_frame, text="PDF", variable=self.output_pdf_var,
                onvalue="on", offvalue="off",
            )
            cb_pdf.grid(row=0, column=3, padx=(0, 15))
            self.timestamp_var = ctk.StringVar(value="off")
            cb_ts = ctk.CTkCheckBox(
                output_frame, text="Timestamp Filename", variable=self.timestamp_var,
                onvalue="on", offvalue="off",
            )
            cb_ts.grid(row=0, column=4, padx=(0, 0))
            Tooltip(cb_ts, "Add timestamp to report filenames (e.g., peekdocs_results_20260327_143022.txt)")

            # Row 10: Save Defaults + Restore Settings buttons
            settings_btn_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
            settings_btn_frame.grid(row=11, column=0, columnspan=3, padx=(0, 15), pady=(0, 10), sticky="e")




            reset_btn = ctk.CTkButton(
                settings_btn_frame, text="Reset All Fields", width=120,
                fg_color="#CC3333", hover_color="#AA2222",
                command=self.reset_form,
                font=ctk.CTkFont(size=13, weight="bold"),
            )
            reset_btn.pack(side="left", padx=5)
            Tooltip(reset_btn, "Clear all fields and reset the GUI to its default state. This does not change the config file — only Save Defaults writes to it")


            # Row 11: Search Using Index(es)
            # Index checkbox moved to main panel (next to Load Settings)

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
            Tooltip(self.file_types_entry, "Comma-separated file extensions to search. Leave blank to search ALL 46 supported file types (not every file on disk — unsupported formats like .DS_Store, .exe, random binaries are always skipped). Supported types: 7z, bz2, cfg, csv, doc, docx, eml, epub, gz, html, ics, ini, json, log, mbox, md, msg, odp, ods, odt, pages, pdf, ppt, pptx, pst, rar, rst, rtf, sql, tar, tex, tgz, toml, tsv, txt, vcf, xls, xlsx, xml, yaml, yml, zip. With OCR enabled: bmp, jpg, jpeg, png, tif, tiff")
            Tooltip(self.proximity_entry, "Find terms within this many words of each other")
            Tooltip(self.context_before_entry, "Number of lines to show before each match")
            Tooltip(self.context_after_entry, "Number of lines to show after each match")
            Tooltip(self.cores_entry, f"Number of CPU cores to use. This machine has {os.cpu_count()}, default is {self._default_cores}")
            Tooltip(self.max_matches_entry, "Maximum matches included in reports. Default 1000. Set to 0 for no limit.")
            Tooltip(self.max_file_size_entry, "Skip files larger than this (in MB). Default 100. Set to 0 for no limit. Large files can cause slow searches or memory issues.")
            Tooltip(self.specific_files_entry, "Comma-separated filenames to search — no limit to the number of files (e.g., report.pdf,notes.txt)")
            Tooltip(self.save_name_entry, "Save the report with a custom name after search completes. DO_NOT_SEARCH_ will be added to the front of your file name")
            Tooltip(self.append_name_entry, "Append results to a named report file (creates or extends it). DO_NOT_SEARCH_ will be added to the front of your file name")
            Tooltip(cb_csv, "Also save results as a CSV file (peekdocs_results.csv) — open in Excel or Google Sheets to sort, filter, and analyze")
            Tooltip(cb_json, "Also save results as a JSON file (peekdocs_results.json) — machine-readable format for automation and integration")
            Tooltip(cb_pdf, "Also save results as a PDF file (peekdocs_results.pdf) — matches highlighted in yellow, portable format for sharing and printing")

            # Note about saving
            # Note above bottom buttons
            import tkinter as _tk_adv
            # Bottom buttons for the Advanced Search Options window
            adv_bottom_frame = ctk.CTkFrame(self.advanced_window, fg_color="transparent")
            adv_bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

            adv_save_btn = ctk.CTkButton(
                adv_bottom_frame, text="Save As Defaults", width=110,
                command=self._save_current_settings,
                font=ctk.CTkFont(size=13),
            )
            adv_save_btn.pack(side="left", padx=(5, 0))
            Tooltip(adv_save_btn, "Save all current options as permanent defaults to ~/.peekdocsrc")

            ctk.CTkButton(
                adv_bottom_frame, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self._close_advanced_window,
                font=ctk.CTkFont(size=13),
            ).place(relx=0.5, rely=0.5, anchor="center")

            adv_restore_btn = ctk.CTkButton(
                adv_bottom_frame, text="Restore Saved Defaults", width=130,
                command=self._load_saved_settings,
                font=ctk.CTkFont(size=13),
            )
            adv_restore_btn.pack(side="right", padx=(0, 5))
            Tooltip(adv_restore_btn, "Load saved defaults from ~/.peekdocsrc into the GUI")

            adv_inspect_link = ctk.CTkLabel(
                adv_bottom_frame, text="Inspect .peekdocsrc",
                font=ctk.CTkFont(size=12, underline=True),
                text_color=("dodgerblue", "deepskyblue"), cursor="hand2",
            )
            adv_inspect_link.pack(side="left", padx=(5, 0))
            adv_inspect_link.bind("<Button-1>", lambda e: self._inspect_settings())
            Tooltip(adv_inspect_link, "View the current saved settings in ~/.peekdocsrc (read-only)")

        def _build_progress_area(self):
            """Build the progress bar, status label, and results preview pane."""
            self.progress_bar = ctk.CTkProgressBar(
                self._search_parent, mode="indeterminate", height=18,
                progress_color=("#2196F3", "#1976D2"),
                fg_color=("#E0E0E0", "#3A3A3A"),
                corner_radius=5,
                indeterminate_speed=1.2,
            )
            self.progress_bar.set(0)
            # Starts hidden — shown only during search

            import tkinter as _tk_status
            status_row = ctk.CTkFrame(self._input_frame, fg_color="transparent")
            status_row.grid(row=3, column=0, columnspan=3, padx=(10, 15), pady=(0, 4), sticky="ew")

            _status_label_size = 16 if sys.platform == "win32" else 14
            status_label_left = ctk.CTkLabel(
                status_row, text="Status:", font=ctk.CTkFont(size=_status_label_size, weight="bold"),
            )
            status_label_left.pack(side="left", padx=(0, 5))
            Tooltip(status_label_left, "Search status — shows progress during search and results summary when complete")

            _status_font_size = 16 if sys.platform == "win32" else 14
            self.status_label = ctk.CTkLabel(
                status_row, text="", font=ctk.CTkFont(size=_status_font_size), anchor="w",
                wraplength=550, text_color="blue", justify="left",
            )
            self.status_label.pack(side="left")

            self._matched_files_link = ctk.CTkButton(
                status_row, text="", font=ctk.CTkFont(size=10),
                fg_color="#FF6B35", hover_color="#E55A2B", text_color="white",
                cursor="hand2", height=22, width=120,
                command=self._show_matched_files_popup,
            )
            self._matched_files_link.pack(side="left", padx=(5, 0))
            self._matched_files_link.pack_forget()  # Hidden until matches found
            Tooltip(self._matched_files_link, "Click to see the list of files that matched — double-click a filename to open it, or use View Text to see the extracted content with highlighted matches")

            self._excluded_files_btn = ctk.CTkButton(
                status_row, text="", font=ctk.CTkFont(size=10),
                fg_color="#666666", hover_color="#555555", text_color="white",
                cursor="hand2", height=22, width=120,
                command=self._show_excluded_files_popup,
            )
            self._excluded_files_btn.pack(side="left", padx=(5, 0))
            self._excluded_files_btn.pack_forget()  # Hidden until search completes
            Tooltip(self._excluded_files_btn, "Click to see which files in the folder were skipped and why (unsupported type, prior peekdocs output, oversized, hidden, etc.) — explains any difference between your folder's file count and the number peekdocs searched")

            self.matched_files = []
            self._inverse_results = False

            # Results preview pane — shown on launch with empty content
            self.preview_frame = ctk.CTkFrame(self._search_parent)
            self.preview_frame.grid(
                row=8, column=0, columnspan=3, padx=10, pady=(5, 0), sticky="nsew"
            )

            import tkinter as tk
            preview_header = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
            preview_header.pack(fill="x", padx=5, pady=(5, 0))
            ctk.CTkLabel(preview_header, text="Results Preview:",
                         font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            self._preview_count_label = ctk.CTkLabel(
                preview_header, text="", font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray50"))
            self._preview_count_label.pack(side="left", padx=(8, 0))

            # App-wide text size dropdown
            self._app_size_menu = ctk.CTkOptionMenu(
                preview_header, variable=self._text_size_var,
                values=["Small", "Normal", "Large", "Extra Large", "Huge"],
                width=110, font=ctk.CTkFont(size=11),
                command=self._on_text_size_changed,
            )
            self._app_size_menu.pack(side="right")
            Tooltip(self._app_size_menu, "Adjust the overall app text size — changes all labels, buttons, and fields", anchor="left")
            ctk.CTkLabel(preview_header, text="App Size:", font=ctk.CTkFont(size=11)).pack(side="right", padx=(10, 3))

            # Preview-only font size dropdown
            self._preview_font_size = 11
            self._preview_size_var = ctk.StringVar(value="11")
            preview_size_menu = ctk.CTkOptionMenu(
                preview_header, variable=self._preview_size_var,
                values=["8", "9", "10", "11", "12", "13", "14", "16", "18", "20"],
                width=65, font=ctk.CTkFont(size=11),
                command=self._on_preview_size_changed,
            )
            preview_size_menu.pack(side="right")
            Tooltip(preview_size_menu, "Adjust the font size of the Results Preview text only", anchor="left")
            ctk.CTkLabel(preview_header, text="Preview Size:", font=ctk.CTkFont(size=11)).pack(side="right", padx=(0, 3))

            preview_text_frame = tk.Frame(self.preview_frame)
            preview_text_frame.pack(fill="both", expand=True, padx=5, pady=(2, 5))

            preview_scroll = tk.Scrollbar(preview_text_frame)
            preview_scroll.pack(side="right", fill="y")

            self.preview_text = tk.Text(
                preview_text_frame, wrap="word", font=("Courier", 11),
                state="disabled", yscrollcommand=preview_scroll.set,
                padx=8, pady=5, height=15,
            )
            self.preview_text.pack(side="left", fill="both", expand=True)
            preview_scroll.config(command=self.preview_text.yview)

            # Configure tags for highlighting
            self.preview_text.tag_configure("filename", font=("Courier", 11, "bold"),
                                            foreground="#1a73e8")
            self.preview_text.tag_configure("match", background="#FFFF00")
            self.preview_text.tag_configure("line_num", foreground="#888888")

            # Right-click to copy selected text or current line
            def _preview_copy(event):
                try:
                    sel = self.preview_text.get("sel.first", "sel.last")
                except tk.TclError:
                    # No selection — copy current line
                    sel = self.preview_text.get("current linestart", "current lineend")
                if sel.strip():
                    self.clipboard_clear()
                    self.clipboard_append(sel.strip())
                    self.status_label.configure(text="Copied to clipboard.",
                                                text_color="blue")
            self.preview_text.bind("<Button-3>", _preview_copy)  # Windows/Linux
            self.preview_text.bind("<Button-2>", _preview_copy)  # macOS right-click

            # Double-click filename to open the file
            def _preview_open_file(event):
                idx = self.preview_text.index("current")
                line = self.preview_text.get(f"{idx} linestart", f"{idx} lineend").strip()
                # Filename lines are tagged with "filename" — check if clicked line has it
                tags = self.preview_text.tag_names(f"{idx} linestart")
                if "filename" not in tags:
                    return
                # Extract path from the line (format: "── filename (dir) ──" or just a path)
                # Try matched_files list first
                for _item in getattr(self, 'matched_files', []):
                    filepath, fname = _item[0], _item[1]
                    if fname in line:
                        if os.path.exists(filepath):
                            system = platform.system()
                            if system == "Darwin":
                                subprocess.Popen(["open", filepath])
                            elif system == "Windows":
                                os.startfile(filepath)
                            else:
                                subprocess.Popen(["xdg-open", filepath])
                        return
            self.preview_text.bind("<Double-1>", _preview_open_file)

        def _build_open_report(self):
            """Build the Matched Files and View Report buttons."""
            # Buttons are children of the search tab, gridded directly at row 6
            self.matched_files_button = ctk.CTkButton(
                self._search_parent,
                text="Matched Files",
                width=140,
                command=self._show_matched_files_popup,
                font=ctk.CTkFont(size=13),
            )
            Tooltip(self.matched_files_button, "View the list of files that contained matches (click a file to open it)")

            self.report_frame = ctk.CTkFrame(self._search_parent, fg_color=self._search_parent.cget("fg_color"))
            ctk.CTkLabel(
                self.report_frame, text="4.",
                font=ctk.CTkFont(size=18, weight="bold"),
            ).pack(side="left", padx=(0, 4))
            report_lbl = ctk.CTkLabel(
                self.report_frame, text="View Report:", font=ctk.CTkFont(size=18, weight="bold"),
            )
            report_lbl.pack(side="left", padx=(0, 4))

            btn_font = ctk.CTkFont(size=12)
            btn_w = 60
            _report_color_note = "Green = report file exists and is ready to open. Red = not generated (enable in Advanced Search Options under Output Formats)."
            self.report_btn_txt = ctk.CTkButton(
                self.report_frame, text="TXT", width=btn_w, font=btn_font,
                command=lambda: self._open_report_format("txt"),
            )
            Tooltip(self.report_btn_txt, f"Open the plain-text report (.txt). {_report_color_note}", anchor="above")
            self.report_btn_docx = ctk.CTkButton(
                self.report_frame, text="DOCX", width=btn_w, font=btn_font,
                command=lambda: self._open_report_format("docx"),
            )
            Tooltip(self.report_btn_docx, f"Open the highlighted Word report (.docx) — every match in yellow with context. {_report_color_note}", anchor="above")
            self.report_btn_csv = ctk.CTkButton(
                self.report_frame, text="CSV", width=btn_w, font=btn_font,
                command=lambda: self._open_report_format("csv"),
            )
            Tooltip(self.report_btn_csv, f"Open the CSV report — one row per match, importable into Excel or Google Sheets. {_report_color_note}", anchor="above")
            self.report_btn_json = ctk.CTkButton(
                self.report_frame, text="JSON", width=btn_w, font=btn_font,
                command=lambda: self._open_report_format("json"),
            )
            Tooltip(self.report_btn_json, f"Open the JSON report — structured data for scripting or further processing. {_report_color_note}", anchor="above")
            self.report_btn_pdf = ctk.CTkButton(
                self.report_frame, text="PDF", width=btn_w, font=btn_font,
                command=lambda: self._open_report_format("pdf"),
            )
            Tooltip(self.report_btn_pdf, f"Open the PDF report — highlighted matches, portable format. {_report_color_note}", anchor="above")

        def _build_index_panel(self):
            """Build the Manage Indexes popup window with build, delete, status, and auto-refresh controls."""
            # Index toggle button — in the shared toggle row
            self.index_toggle_btn = ctk.CTkButton(
                self._toggle_row,
                text="\u25b6 Manage Indexes", width=0,
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                anchor="w",
                command=self._toggle_index_options,
                font=ctk.CTkFont(size=13),
            )
            self.index_toggle_btn.pack(side="left", padx=(20, 20))
            Tooltip(self.index_toggle_btn, "Open the Manage Indexes panel — build, delete, and refresh search indexes for faster repeated searches")

            # Create popup window for Manage Indexes
            self.index_window = ctk.CTkToplevel(self)
            self.index_window.title("Manage Indexes")
            self.index_window.after(100, lambda: self.index_window.title("Manage Indexes"))
            self.index_window.geometry("650x240")
            self.index_window.resizable(True, True)
            self.index_window.protocol("WM_DELETE_WINDOW", self._close_index_window)
            self.index_window.withdraw()
            self.after(10, self.index_window.withdraw)
            self.index_visible = False

            idx_frame = ctk.CTkFrame(self.index_window)
            idx_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Header with description and ? help
            idx_header = ctk.CTkFrame(idx_frame, fg_color="transparent")
            idx_header.pack(fill="x", padx=5, pady=(0, 10))
            ctk.CTkLabel(
                idx_header,
                text="Build a search index for faster repeated searches. The index includes all subfolders.",
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray50"),
            ).pack(side="left")
            idx_help_btn = ctk.CTkButton(
                idx_header, text="?", width=28, height=28,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self._show_index_help,
            )
            idx_help_btn.pack(side="right")
            Tooltip(idx_help_btn, "Help — explains what indexes are and when to use them")

            # Buttons row
            btn_frame = ctk.CTkFrame(idx_frame, fg_color="transparent")
            btn_frame.pack(fill="x", padx=5)

            self.build_index_button = ctk.CTkButton(
                btn_frame, text="Build Index(es)", width=120,
                command=self.build_index_action, font=ctk.CTkFont(size=12),
            )
            self.build_index_button.pack(side="left", padx=(0, 5))
            Tooltip(self.build_index_button, "Build a search index for faster repeated searches. Indexes all subfolders automatically")

            self.cancel_index_button = ctk.CTkButton(
                btn_frame, text="Cancel Build", width=100,
                fg_color="red", hover_color="darkred",
                command=self._cancel_index_build, font=ctk.CTkFont(size=12),
            )
            # Hidden by default — shown during build
            Tooltip(self.cancel_index_button, "Cancel the index build in progress")

            self.delete_index_button = ctk.CTkButton(
                btn_frame, text="Delete Index(es)", width=120,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self.delete_index_action, font=ctk.CTkFont(size=12),
            )
            self.delete_index_button.pack(side="left", padx=5)
            Tooltip(self.delete_index_button, "Delete the search index from the selected folder")

            self.index_status_button = ctk.CTkButton(
                btn_frame, text="Index Status", width=100,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self.index_status_action, font=ctk.CTkFont(size=12),
            )
            self.index_status_button.pack(side="left", padx=5)
            Tooltip(self.index_status_button, "Show index info — file count, size, and settings")

            # Auto-refresh row
            refresh_frame = ctk.CTkFrame(idx_frame, fg_color="transparent")
            refresh_frame.pack(fill="x", padx=5, pady=(10, 0))

            ctk.CTkLabel(
                refresh_frame, text="Auto-Refresh Index:",
                font=ctk.CTkFont(size=12),
            ).pack(side="left", padx=(0, 5))

            self.refresh_interval_var = ctk.StringVar(value="Off")
            self.refresh_interval_menu = ctk.CTkOptionMenu(
                refresh_frame,
                values=["Off", "5 min", "15 min", "30 min", "1 hour", "4 hours", "8 hours", "24 hours"],
                variable=self.refresh_interval_var,
                command=self._on_refresh_interval_changed,
                width=100,
                font=ctk.CTkFont(size=12),
            )
            self.refresh_interval_menu.pack(side="left")
            Tooltip(self.refresh_interval_menu,
                    "Automatically refresh the index at this interval while the app is open. "
                    "Adds new files, re-indexes changed files, removes deleted files.")

            # Status label
            self.refresh_status_label = ctk.CTkLabel(
                idx_frame, text="", font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray50"), anchor="w",
            )
            self.refresh_status_label.pack(anchor="w", padx=5, pady=(5, 0))

            # Close button
            ctk.CTkButton(
                idx_frame, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self._close_index_window,
                font=ctk.CTkFont(size=12),
            ).pack(side="bottom", pady=(10, 10))

            # For index_frame compatibility with _update_index_button_color
            self.index_frame = idx_frame

        def _open_load_search_popup(self):
            """Open a popup with saved searches listbox and Select/Delete buttons."""
            import tkinter as tk
            from peekdocs.collection import load_collection
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
            btn_frame.pack(side="top", fill="x", padx=4, pady=(2, 2))
            cancel_frame = ctk.CTkFrame(frame, fg_color="transparent")
            cancel_frame.pack(side="top", fill="x", padx=4, pady=(0, 4))

            def on_select():
                sel = listbox.curselection()
                if not sel:
                    return
                name = listbox.get(sel[0])
                if name == "(no saved searches)":
                    return
                from peekdocs.collection import get_search_params
                params = get_search_params(folder, name)
                if params:
                    self._apply_params_to_gui(params)
                    self.status_label.configure(
                        text=f"Loaded search '{name}' from collection.",
                        text_color="blue",
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
                from peekdocs.collection import remove_saved_search
                if not messagebox.askyesno("Delete Saved Search",
                                           f"Delete saved search '{name}'?",
                                           parent=popup):
                    return
                remove_saved_search(folder, name)
                listbox.delete(sel[0])
                self.status_label.configure(
                    text=f"Deleted saved search '{name}'.",
                    text_color="blue",
                )
                if listbox.size() == 0:
                    listbox.insert("end", "(no saved searches)")

            def close_popup(event=None):
                if self._load_search_popup and self._load_search_popup.winfo_exists():
                    self._load_search_popup.destroy()
                    self._load_search_popup = None

            ctk.CTkButton(btn_frame, text="Select", width=70, font=ctk.CTkFont(size=12),
                          command=on_select).pack(side="left")
            ctk.CTkButton(btn_frame, text="Delete", width=70, font=ctk.CTkFont(size=12),
                          fg_color="firebrick", hover_color="darkred",
                          command=on_delete).pack(side="right")
            ctk.CTkButton(cancel_frame, text="Cancel", width=80,
                          fg_color="transparent", text_color=("gray30", "gray70"),
                          hover_color=("gray90", "gray25"),
                          font=ctk.CTkFont(size=12),
                          command=close_popup).pack()

            listbox.bind("<Double-1>", lambda e: on_select())
            popup.bind("<Escape>", close_popup)
            popup.protocol("WM_DELETE_WINDOW", close_popup)
            listbox.focus_set()

        def _refresh_load_search_menu(self):
            """No-op — popup rebuilds its list each time it opens."""
            pass

        def _build_bottom_row(self):
            """Build the bottom toolbar with help, about, tools, and close."""
            self.bottom_frame = ctk.CTkFrame(self._search_parent, fg_color="transparent")
            self.bottom_frame.grid(
                row=10, column=0, columnspan=3, padx=15, pady=(0, 8), sticky="sew"
            )

            self.bottom_frame.grid_columnconfigure(0, weight=1)
            self.bottom_frame.grid_columnconfigure(1, weight=1)
            self.bottom_frame.grid_columnconfigure(2, weight=1)

            # Left group
            left_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
            left_frame.grid(row=0, column=0, sticky="w")

            self.help_button = ctk.CTkButton(
                left_frame,
                text="User Guide",
                width=90,
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self.open_help,
                font=ctk.CTkFont(size=13),
            )
            self.help_button.pack(side="left")
            Tooltip(self.help_button, "The USER_GUIDE.md, TROUBLESHOOTING.md, and API.md are under 'docs' on GitHub", anchor="above")

            # Center: Close button
            close_main_btn = ctk.CTkButton(
                self.bottom_frame,
                text="Close",
                width=70,
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self.destroy,
                font=ctk.CTkFont(size=13),
            )
            close_main_btn.grid(row=0, column=1)
            Tooltip(close_main_btn, "Close peekdocs", anchor="above")

            # Right group
            right_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
            right_frame.grid(row=0, column=2, sticky="e")

            self.about_button = ctk.CTkButton(
                right_frame,
                text="About",
                width=70,
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=self.show_about,
                font=ctk.CTkFont(size=13),
            )
            self.about_button.pack(side="right", padx=5)
            Tooltip(self.about_button, "About peekdocs — version, author, and license information", anchor="above-left")

            # Tools menu — consolidates utilities, settings, and maintenance
            def _show_tools_menu():
                import tkinter as tk
                menu = tk.Menu(self, tearoff=0, font=("TkDefaultFont", 12))
                def _dark_sep():
                    menu.add_command(label="─" * 50, state="disabled",
                                     font=("TkDefaultFont", 2),
                                     foreground="gray40")
                # Folder analysis (alphabetical)
                menu.add_command(label="Duplicate Finder — find identical files in the folder", command=self._run_duplicate_scan)
                menu.add_command(label="Empty Files — find zero-length or blank files", command=self._run_empty_file_scan)
                menu.add_command(label="File Inventory — summary of all files by type, size, and date", command=self._run_file_inventory)
                menu.add_command(label="Large Files — find the biggest files in the folder", command=self._run_large_file_scan)
                menu.add_command(label="Protected Files — find password-protected or encrypted files", command=self._run_protected_scan)
                menu.add_command(label="Recent Changes — files modified in the last 7 / 30 / 90 days", command=self._run_recent_changes)
                _dark_sep()
                # User tools (alphabetical)
                menu.add_command(label="Bookmarks — pinned files for quick access", command=self._show_bookmarks)
                menu.add_command(label="Search History — log of past searches and results", command=self._show_search_history)
                _dark_sep()
                # App management (alphabetical)
                menu.add_command(label="All Collections — find saved searches across all folders", command=self._show_all_collections)
                menu.add_command(label="App Files — list peekdocs-created files in the Search Folder", command=self._show_app_files)
                menu.add_command(label="Error Log — open peekdocs_errors.log", command=self.open_error_log)
                _dark_sep()
                # Cleanup (alphabetical)
                menu.add_command(label="Clean Up Practice Files — remove all except saved searches", command=self._clean_up_practice_files)
                menu.add_command(label="Clear Error Log — delete peekdocs_errors.log", command=self._clear_error_log)
                menu.add_command(label="Clear Search Results — delete peekdocs_results files", command=self._clear_results_files)
                _dark_sep()
                # Text Size — direct items instead of a cascade submenu
                # (cascades open to the right and go off-screen on small displays)
                current_size = self._text_size_var.get()
                for size in ["Small", "Normal", "Large", "Extra Large", "Huge"]:
                    marker = " \u2713" if size == current_size else ""
                    menu.add_command(
                        label=f"Text Size: {size}{marker}",
                        command=lambda s=size: (self._text_size_var.set(s), self._on_text_size_changed(s)),
                    )
                # Hover text toggle
                hover_label = (
                    "Disable Hover Text — hide tooltip popups when hovering over buttons and fields"
                    if Tooltip.enabled else
                    "Enable Hover Text — show tooltip popups when hovering over buttons and fields"
                )
                menu.add_command(label=hover_label, command=self._toggle_tooltips)
                btn = self._tools_btn
                x = btn.winfo_rootx() - 400
                y = btn.winfo_rooty() - 350
                menu.tk_popup(x, y)

            self._tools_btn = ctk.CTkButton(
                right_frame,
                text="Tools \u25b2",
                width=70,
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=_show_tools_menu,
                font=ctk.CTkFont(size=13),
            )
            self._tools_btn.pack(side="right", padx=5)
            Tooltip(self._tools_btn, "File Inventory, Duplicates, Large Files, Empty Files, Recent Changes, Protected Files, Search History, Bookmarks, App Files, and more", anchor="above-left")

            # Keep references for tooltip toggle (used by _toggle_tooltips)
            self.tooltip_toggle_btn = None
            self.view_error_log_bottom = None


        # ── Actions ──────────────────────────────────────────────

        def _toggle_tooltips(self):
            """Toggle hover tooltip visibility on or off."""
            Tooltip.enabled = not Tooltip.enabled

        def toggle_advanced(self):
            """Toggle the Advanced Search Options window open or closed."""
            if self.advanced_visible:
                self._close_advanced_window()
            else:
                self.advanced_window.deiconify()
                self.advanced_window.lift()
                self.advanced_toggle.configure(text="\u25bc Advanced Search Options")
                self.advanced_visible = True

        def _close_advanced_window(self):
            """Hide the Advanced Search Options window and update the toggle button."""
            self.advanced_window.withdraw()
            self.advanced_toggle.configure(text="\u25b6 Advanced Search Options")
            self.advanced_visible = False

        def _toggle_index_options(self):
            """Toggle the Manage Indexes window open or closed."""
            if self.index_visible:
                self._close_index_window()
            else:
                self.index_window.deiconify()
                self.index_window.lift()
                self.index_toggle_btn.configure(text="\u25bc Manage Indexes")
                self.index_visible = True
                self._update_index_button_color()

        def _close_index_window(self):
            """Hide the Manage Indexes window and update the toggle button."""
            self.index_window.withdraw()
            self.index_toggle_btn.configure(text="\u25b6 Manage Indexes")
            self.index_visible = False

        def _cancel_index_build(self):
            """Cancel an in-progress index build."""
            self._index_cancelled = True
            # For older subprocess-based builds (safety), also try terminate
            if hasattr(self, '_index_process') and self._index_process is not None:
                if hasattr(self._index_process, 'terminate'):
                    try:
                        self._index_process.terminate()
                    except Exception:
                        pass
            self.status_label.configure(text="Cancelling index build...", text_color="blue")

        def _browse_file(self):
            """Open a file picker, set the folder to the file's directory and specific file to search."""
            if getattr(self, '_file_dialog_open', False):
                return
            self._file_dialog_open = True
            try:
                self._browse_file_inner()
            finally:
                self.after(500, lambda: setattr(self, '_file_dialog_open', False))

        def _browse_file_inner(self):
            initial = self.folder_entry.get().strip()
            if not initial or not os.path.isdir(initial):
                initial = os.path.expanduser("~")
            filepath = filedialog.askopenfilename(
                parent=self,
                initialdir=initial,
                title="Select a file to search",
            )
            if filepath:
                filepath = os.path.normpath(filepath)
                folder = os.path.dirname(filepath)
                filename = os.path.basename(filepath)
                self.folder_entry.delete(0, "end")
                self.folder_entry.insert(0, folder)
                self.specific_files_entry.delete(0, "end")
                self.specific_files_entry.insert(0, filename)
                self.recursive_var.set("off")
                self._update_index_button_color()
                self._refresh_load_search_menu()
                self.status_label.configure(
                    text=f"File selected: {filename} in {folder}",
                    text_color="blue",
                )
                self._clear_file_btn.pack(side="left", padx=(2, 0))

        def _clear_specific_file(self):
            """Clear the specific file selection and revert to full folder search."""
            self.specific_files_entry.delete(0, "end")
            self._clear_file_btn.pack_forget()
            self.status_label.configure(
                text="File selection cleared — searching entire folder.",
                text_color="blue",
            )

        def browse_folder(self):
            """Open a folder picker and update the search folder entry."""
            initial = self.folder_entry.get() or os.path.expanduser("~")
            folder = filedialog.askdirectory(initialdir=initial)
            if folder:
                folder = os.path.normpath(folder)
                self.folder_entry.delete(0, "end")
                self.folder_entry.insert(0, folder)
                # Clear any single-file selection so the search covers
                # the entire folder, not the previously selected file.
                self._clear_specific_file()
                self._update_index_button_color()
                self._on_refresh_interval_changed(self.refresh_interval_var.get())
                self._refresh_load_search_menu()

        def _browse_output_dir(self):
            """Open a folder picker for the search output directory."""
            initial = self.output_dir_entry.get().strip() or self.folder_entry.get().strip() or os.path.expanduser("~")
            folder = filedialog.askdirectory(initialdir=initial)
            if folder:
                self.output_dir_entry.delete(0, "end")
                self.output_dir_entry.insert(0, folder)

        def _show_recent_searches(self):
            """Show a popup with recent searches to re-use."""
            import tkinter as tk
            if not self._recent_searches:
                self.status_label.configure(
                    text="No recent searches yet.",
                    text_color="blue",
                    font=ctk.CTkFont(size=13),
                )
                return
            popup = tk.Toplevel(self)
            popup.title("Recent Searches")
            popup.resizable(False, False)
            popup.transient(self)
            try:
                popup.grab_set()
            except Exception:
                popup.after(150, lambda: popup.grab_set() if popup.winfo_exists() else None)
            self.update_idletasks()
            x = self.winfo_rootx() + 50
            y = self.winfo_rooty() + 80
            popup.geometry(f"+{x}+{y}")

            tk.Label(popup, text="Click a search to re-use it:",
                     font=("TkDefaultFont", 11), fg="gray").pack(padx=10, pady=(8, 4))

            listbox = tk.Listbox(popup, font=("TkDefaultFont", 12),
                                 selectmode=tk.SINGLE, activestyle="none",
                                 bg="#2b2b2b", fg="white", selectbackground="#1f6aa5",
                                 highlightthickness=0, borderwidth=1, relief="sunken",
                                 width=60, height=min(len(self._recent_searches), 10))
            listbox.pack(padx=10, pady=(0, 8))
            for s in self._recent_searches:
                listbox.insert("end", s)

            def _select(event=None):
                sel = listbox.curselection()
                if not sel:
                    return
                text = listbox.get(sel[0])
                self.search_entry.delete(0, "end")
                self.search_entry.insert(0, text)
                popup.destroy()

            listbox.bind("<Double-1>", _select)
            tk.Button(popup, text="Use", width=8, command=_select).pack(side="left", padx=(10, 5), pady=(0, 8))
            tk.Button(popup, text="Cancel", width=8, command=popup.destroy).pack(side="left", padx=5, pady=(0, 8))

        def _start_sensitive_scan(self):
            """Show a configuration popup for the sensitive data scan."""
            import tkinter as tk
            from peekdocs.sensitive_patterns import SENSITIVE_PATTERNS, SEVERITY_COLORS

            if self.process is not None:
                self._show_error("A search is already running.")
                return

            win = tk.Toplevel(self)
            win.title("PII Scan — Select Categories")
            win.resizable(False, False)
            win.transient(self)
            # No grab_set() — the help window (?) must remain interactive
            # alongside this popup so users can copy regex examples and
            # paste them into the Custom Pattern fields.
            # Raise on focus so this window comes to front when clicked
            # anywhere (macOS doesn't auto-reorder transient siblings).
            win.bind("<FocusIn>", lambda e: win.lift())

            header = tk.Frame(win)
            header.pack(fill="x", padx=15, pady=(12, 4))
            tk.Label(
                header, text="Select which categories to scan for:",
                font=("TkDefaultFont", 13, "bold"),
            ).pack(side="left")
            tk.Button(
                header, text="?", width=3, font=("TkDefaultFont", 12, "bold"),
                command=lambda: self._show_pii_scan_help(win),
            ).pack(side="right")

            _pii_folder_label = self._add_folder_bar(win, "Scan will check files in this folder.")

            # Load saved selections (default: all enabled)
            if not hasattr(self, "_pii_scan_enabled"):
                from peekdocs.cli import _load_config
                config = _load_config()
                saved = config.get("pii_scan_categories")
                if isinstance(saved, list):
                    self._pii_scan_enabled = set(saved)
                else:
                    self._pii_scan_enabled = {cat for cat, _, _, _ in SENSITIVE_PATTERNS}

            # Load saved dollar amount range (defaults to $10,000 – $999,999,999)
            from peekdocs.cli import _load_config
            _cfg = _load_config()
            saved_min = _cfg.get("pii_scan_dollar_min", "10000")
            saved_max = _cfg.get("pii_scan_dollar_max", "999999999")

            # Checkboxes for each pattern
            check_vars = []
            dollar_min_entry = None
            dollar_max_entry = None
            checks_frame = tk.Frame(win)
            checks_frame.pack(fill="x", padx=20)

            for i, (category, _regex, severity, description) in enumerate(SENSITIVE_PATTERNS):
                var = tk.BooleanVar(value=(category in self._pii_scan_enabled))
                check_vars.append(var)
                row = tk.Frame(checks_frame)
                row.pack(fill="x", pady=2)

                sev = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["info"])
                tk.Label(
                    row, text=f" {sev['label']} ", font=("TkDefaultFont", 9, "bold"),
                    bg=sev["bg"], fg=sev["fg"], width=10,
                ).pack(side="left", padx=(0, 8))

                cb = tk.Checkbutton(row, variable=var, text=category, font=("TkDefaultFont", 12))
                cb.pack(side="left")

                if category == "Dollar Amounts":
                    # Inline Min/Max entries for the dollar amount range
                    tk.Label(
                        row, text="  Min $", font=("TkDefaultFont", 11),
                    ).pack(side="left", padx=(10, 2))
                    dollar_min_entry = tk.Entry(row, width=12, font=("TkDefaultFont", 11))
                    dollar_min_entry.insert(0, str(saved_min))
                    dollar_min_entry.pack(side="left")
                    tk.Label(
                        row, text="  Max $", font=("TkDefaultFont", 11),
                    ).pack(side="left", padx=(10, 2))
                    dollar_max_entry = tk.Entry(row, width=12, font=("TkDefaultFont", 11))
                    dollar_max_entry.insert(0, str(saved_max))
                    dollar_max_entry.pack(side="left")
                else:
                    tk.Label(
                        row, text=f"  {description}", font=("TkDefaultFont", 10), fg="gray",
                    ).pack(side="left")

            # Select All / Deselect All
            toggle_frame = tk.Frame(win)
            toggle_frame.pack(pady=(8, 4))

            def _select_all():
                for v in check_vars:
                    v.set(True)

            def _deselect_all():
                for v in check_vars:
                    v.set(False)

            tk.Button(toggle_frame, text="Select All", width=10, command=_select_all).pack(side="left", padx=5)
            tk.Button(toggle_frame, text="Deselect All", width=10, command=_deselect_all).pack(side="left", padx=5)

            # ── Advanced: user-supplied custom regex patterns (2 rows) ──
            from tkinter import ttk as _ttk
            _ttk.Separator(win, orient="horizontal").pack(fill="x", padx=15, pady=(10, 4))

            custom_outer = tk.Frame(win)
            custom_outer.pack(fill="x", padx=20, pady=(0, 2))
            tk.Label(
                custom_outer,
                text="Advanced \u2014 Custom Patterns (optional)",
                font=("TkDefaultFont", 11, "bold"),
            ).pack(anchor="w")
            tk.Label(
                custom_outer,
                text="Add up to two of your own regex patterns to the scan. Requires regex knowledge. "
                     "See the ? help for examples and disclaimers.",
                font=("TkDefaultFont", 9), fg="gray",
            ).pack(anchor="w")

            # Build two custom-pattern rows with shared structure.
            # Config keys use "" for the first row and "2" for the second,
            # so existing configs with pii_scan_custom_* still work.
            _custom_suffixes = ["", "2"]
            custom_rows = []  # list of (enabled_var, name_entry, regex_entry, severity_var)
            for suffix in _custom_suffixes:
                saved_enabled = bool(_cfg.get(f"pii_scan_custom{suffix}_enabled", False))
                saved_name = _cfg.get(f"pii_scan_custom{suffix}_name", "")
                saved_regex = _cfg.get(f"pii_scan_custom{suffix}_regex", "")
                saved_severity = _cfg.get(f"pii_scan_custom{suffix}_severity", "moderate")
                if saved_severity not in ("high", "moderate", "info"):
                    saved_severity = "moderate"

                row = tk.Frame(custom_outer)
                row.pack(fill="x", pady=(4, 0))

                enabled_var = tk.BooleanVar(value=saved_enabled)
                tk.Checkbutton(
                    row, variable=enabled_var, font=("TkDefaultFont", 11),
                ).pack(side="left")

                tk.Label(row, text="Name:", font=("TkDefaultFont", 11)).pack(side="left", padx=(0, 2))
                name_entry = tk.Entry(row, width=16, font=("TkDefaultFont", 11))
                name_entry.insert(0, saved_name)
                name_entry.pack(side="left", padx=(0, 6))

                tk.Label(row, text="Regex:", font=("TkDefaultFont", 11)).pack(side="left", padx=(0, 2))
                regex_entry = tk.Entry(row, width=26, font=("TkDefaultFont", 11))
                regex_entry.insert(0, saved_regex)
                regex_entry.pack(side="left", padx=(0, 6))
                Tooltip(
                    regex_entry,
                    "Your custom regex. peekdocs does NOT validate that it "
                    "correctly identifies the data you intend to find \u2014 you "
                    "own the outcome. Syntax errors are caught before the scan "
                    "runs, and obviously too-broad patterns will trigger a "
                    "warning. Findings from your pattern are marked '(custom)' "
                    "in the results and report. See the ? help for details.",
                )

                tk.Label(row, text="Severity:", font=("TkDefaultFont", 11)).pack(side="left", padx=(0, 2))
                severity_var = tk.StringVar(value=saved_severity)
                _ttk.Combobox(
                    row, textvariable=severity_var,
                    values=["high", "moderate", "info"],
                    state="readonly", width=10,
                    font=("TkDefaultFont", 11),
                ).pack(side="left")

                custom_rows.append((enabled_var, name_entry, regex_entry, severity_var))

            # Persistent amber warning below the custom-pattern rows
            tk.Label(
                custom_outer,
                text=(
                    "\u26a0  peekdocs does NOT validate your regex. You own the outcome. "
                    "Findings from your patterns are marked '(custom)' in the results and report."
                ),
                font=("TkDefaultFont", 9, "italic"),
                fg="#996600",
                wraplength=820,
                justify="left",
            ).pack(anchor="w", pady=(4, 0))

            # Run button on its own row; Close button on a separate row below
            btn_frame = tk.Frame(win)
            btn_frame.pack(pady=(8, 2))
            close_frame = tk.Frame(win)
            close_frame.pack(pady=(0, 12))

            def _run():
                from tkinter import messagebox as _mb
                import re as _re
                # 5-tuples: (category, regex, severity, description, is_custom)
                # Built-in patterns get is_custom=False explicitly.
                selected = [(*SENSITIVE_PATTERNS[i], False) for i, v in enumerate(check_vars) if v.get()]

                # Validate Dollar Amounts min/max if that category is selected
                dollar_min = dollar_max = None
                dollar_selected = any(
                    SENSITIVE_PATTERNS[i][0] == "Dollar Amounts"
                    for i, v in enumerate(check_vars) if v.get()
                )
                if dollar_selected and dollar_min_entry is not None:
                    min_str = dollar_min_entry.get().strip().replace(",", "").replace("$", "")
                    max_str = dollar_max_entry.get().strip().replace(",", "").replace("$", "")
                    try:
                        dollar_min = float(min_str) if min_str else 0.0
                        dollar_max = float(max_str) if max_str else 999999999.0
                    except ValueError:
                        self._show_error("Dollar amount Min and Max must be numbers.")
                        return
                    if dollar_min < 0 or dollar_max < 0:
                        self._show_error("Dollar amount Min and Max must be non-negative.")
                        return
                    if dollar_min > dollar_max:
                        self._show_error("Dollar amount Min must be less than or equal to Max.")
                        return

                # Validate and include custom patterns if enabled
                for row_idx, (c_enabled_var, c_name_entry, c_regex_entry, c_sev_var) in enumerate(custom_rows):
                    c_enabled = c_enabled_var.get()
                    c_name = c_name_entry.get().strip()
                    c_regex = c_regex_entry.get().strip()
                    c_severity = c_sev_var.get()
                    if c_severity not in ("high", "moderate", "info"):
                        c_severity = "moderate"
                    label = f"Custom Pattern {row_idx + 1}"
                    if c_enabled:
                        if not c_name:
                            self._show_error(f"{label}: please enter a Name.")
                            return
                        if not c_regex:
                            self._show_error(f"{label}: please enter a Regex.")
                            return
                        try:
                            _re.compile(c_regex)
                        except _re.error as exc:
                            self._show_error(
                                f"{label} regex is invalid:\n\n{exc}\n\n"
                                "Fix the pattern and try again."
                            )
                            return
                        stripped = c_regex.strip()
                        looks_too_broad = (
                            len(stripped) < 3
                            or stripped in (".", ".*", ".+", "\\w", "\\w+", "\\w*",
                                            "\\S", "\\S+", "\\S*", "\\d", "\\d+",
                                            "\\d*", "[^ ]", "[^ ]*", "[^ ]+")
                        )
                        if looks_too_broad:
                            if not _mb.askyesno(
                                f"Very Broad {label}",
                                f"Your custom regex is {repr(stripped)}, which is likely to "
                                "match almost every file in the folder and produce a huge "
                                "number of findings.\n\nRun the scan anyway?",
                                parent=win,
                            ):
                                return
                        description = f"Custom user pattern: {c_regex}"
                        selected.append((c_name, c_regex, c_severity, description, True))

                if not selected:
                    self._show_error("Select at least one category or add a custom pattern.")
                    return

                # Remember selections for next time
                self._pii_scan_enabled = {SENSITIVE_PATTERNS[i][0] for i, v in enumerate(check_vars) if v.get()}
                try:
                    from peekdocs.cli import _load_config, _save_config
                    config = _load_config()
                    config["pii_scan_categories"] = sorted(self._pii_scan_enabled)
                    if dollar_selected and dollar_min is not None:
                        config["pii_scan_dollar_min"] = str(int(dollar_min)) if dollar_min.is_integer() else str(dollar_min)
                        config["pii_scan_dollar_max"] = str(int(dollar_max)) if dollar_max.is_integer() else str(dollar_max)
                    # Always persist the custom-pattern fields so the popup
                    # restores them next time, even if the checkbox is off.
                    for row_idx, (c_ev, c_ne, c_re, c_sv) in enumerate(custom_rows):
                        suffix = _custom_suffixes[row_idx]
                        config[f"pii_scan_custom{suffix}_enabled"] = c_ev.get()
                        config[f"pii_scan_custom{suffix}_name"] = c_ne.get().strip()
                        config[f"pii_scan_custom{suffix}_regex"] = c_re.get().strip()
                        config[f"pii_scan_custom{suffix}_severity"] = c_sv.get()
                    _save_config(config)
                except Exception:
                    pass
                pii_folder = _pii_folder_label.cget("text")
                win.destroy()
                self._run_sensitive_scan(selected, pii_folder, dollar_range=(dollar_min, dollar_max) if dollar_selected else None)

            tk.Button(btn_frame, text="Run Scan", width=12, font=("TkDefaultFont", 12, "bold"), command=_run).pack()
            ctk.CTkButton(
                close_frame, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=win.destroy,
                font=ctk.CTkFont(size=12),
            ).pack()

        def _show_pii_scan_help(self, parent):
            """Show help for the PII Scan.

            Non-modal (no grab_set) so the user can copy regex examples
            from this window and paste them into the Custom Pattern fields
            on the categories popup without closing the help first.
            """
            import tkinter as tk
            # Both this help window and the categories popup are
            # transient(self) so they stay above the main window as a
            # group.  macOS doesn't auto-reorder transient siblings on
            # click, so we add a <Button-1> → lift() binding on both
            # windows — whichever you click comes to front.
            help_win = tk.Toplevel(self)
            help_win.title("PII Scan — Help")
            help_win.geometry("750x700")
            help_win.resizable(True, True)
            help_win.transient(self)
            help_win.bind("<FocusIn>", lambda e: help_win.lift())
            # Ensure the window is visible on Linux (X11 window managers
            # can silently open new windows behind existing ones).
            help_win.lift()
            help_win.after(50, help_win.lift)
            help_win.after(100, help_win.focus_force)

            txt = tk.Text(help_win, wrap="word", font=("TkDefaultFont", 12),
                          padx=15, pady=10, borderwidth=0, highlightthickness=0)
            scroll = tk.Scrollbar(help_win, command=txt.yview)
            txt.configure(yscrollcommand=scroll.set)
            scroll.pack(side="right", fill="y")
            txt.pack(fill="both", expand=True)

            # Right-click context menu for copying selected text
            _copy_menu = tk.Menu(txt, tearoff=0)
            _copy_menu.add_command(
                label="Copy",
                command=lambda: (
                    help_win.clipboard_clear(),
                    help_win.clipboard_append(txt.get("sel.first", "sel.last")),
                ) if txt.tag_ranges("sel") else None,
            )

            def _show_copy_menu(event):
                try:
                    _copy_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    _copy_menu.grab_release()

            # Bind right-click on all platforms
            txt.bind("<Button-3>", _show_copy_menu)          # Windows / Linux
            txt.bind("<Button-2>", _show_copy_menu)          # macOS
            txt.bind("<Control-Button-1>", _show_copy_menu)  # macOS ctrl+click

            txt.tag_configure("heading", font=("TkDefaultFont", 14, "bold"),
                              spacing1=10, spacing3=5)
            txt.tag_configure("body", font=("TkDefaultFont", 12), spacing1=2)
            txt.tag_configure("example", font=("Courier", 11), lmargin1=30,
                              lmargin2=30, spacing1=2)
            txt.tag_configure("toc_title", font=("TkDefaultFont", 14, "bold"),
                              spacing1=5, spacing3=8)
            txt.tag_configure("toc_item", font=("TkDefaultFont", 11), lmargin1=20,
                              lmargin2=20, foreground="gray40")
            txt.tag_configure("heading_red", font=("TkDefaultFont", 14, "bold"),
                              spacing1=10, spacing3=5, foreground="red")

            def h(text):
                txt.insert("end", text + "\n", "heading")

            def h_red(text):
                txt.insert("end", text + "\n", "heading_red")

            def b(text):
                txt.insert("end", text + "\n", "body")

            def e(text):
                txt.insert("end", text + "\n", "example")

            def blank():
                txt.insert("end", "\n")

            txt.tag_configure("toc_item_red", font=("TkDefaultFont", 11, "bold"), lmargin1=20,
                              lmargin2=20, foreground="red")
            txt.insert("end", "TABLE OF CONTENTS\n", "toc_title")
            for section in [
                "What Is the PII Scan?",
                "How to Use It",
                "Scan Categories",
                "Severity Levels",
                "Custom Pattern (Advanced)",
                "Understanding Results",
                "The Highlighted Report",
                "Saving Your Selections",
                "Search Folder",
                "How It Differs from Regular Search",
            ]:
                txt.insert("end", f"\u2022 {section}\n", "toc_item")
            txt.insert("end", "\u2022 Think Before You Print\n", "toc_item_red")
            for section in [
                "Disclaimer",
                "MIT License",
            ]:
                txt.insert("end", f"\u2022 {section}\n", "toc_item")
            txt.insert("end", "\n")

            b("The PII Scan checks your documents for sensitive data \u2014 SSNs,")
            b("credit cards, tax IDs, passwords, and more \u2014 with one click.")
            blank()

            h("WHAT IS THE PII SCAN?")
            b("The PII Scan checks your documents for personally identifiable")
            b("information (PII) and other sensitive data with one click. It")
            b("runs a battery of regex pattern searches \u2014 SSNs, credit cards,")
            b("tax IDs, emails, phone numbers, passwords, dates of birth, and")
            b("large dollar amounts \u2014 and shows you exactly where they are.")
            blank()
            b("Use it to discover sensitive data hiding in your files before")
            b("someone else finds it. Check years of personal documents for")
            b("exposed SSNs, scan an old laptop before you sell it, or review")
            b("files in a shared drive to see what might need to be cleaned up.")
            blank()

            h("HOW TO USE IT")
            b("1. Make sure the Search Folder points to the folder you want")
            b("   to check (use Change Folder if needed)")
            b("2. Check the categories you want to scan for (all are checked")
            b("   by default)")
            b("3. Click Run Scan")
            b("4. Results appear in a popup with color-coded severity badges")
            b("5. Click View Files on any category to see affected files")
            b("6. Click Open Report to view the highlighted .docx report")
            blank()

            h("SCAN CATEGORIES")
            blank()
            b("Social Security Numbers (HIGH)")
            e("  Pattern: XXX-XX-XXXX (e.g., 123-45-6789)")
            blank()
            b("Credit Card Numbers (HIGH)")
            e("  Visa, Mastercard, Amex, Discover patterns")
            e("  (e.g., 4111-1111-1111-1111)")
            blank()
            b("Tax ID / EIN (HIGH)")
            e("  Employer Identification Numbers: XX-XXXXXXX")
            e("  (e.g., 12-3456789)")
            blank()
            b("Email Addresses (MODERATE)")
            e("  Standard email patterns (e.g., name@example.com)")
            blank()
            b("Phone Numbers (MODERATE)")
            e("  US phone patterns with separators")
            e("  (e.g., 555-123-4567 or (555) 123-4567)")
            blank()
            b("Passwords / Secrets (MODERATE)")
            e("  Lines containing password=, secret=, api_key=,")
            e("  token=, or similar assignments")
            blank()
            b("Dates of Birth (MODERATE)")
            e("  Date patterns near keywords like DOB, date of birth,")
            e("  or born (e.g., DOB: 03/15/1990)")
            blank()
            b("Dollar Amounts Over $10,000 (INFO)")
            e("  Dollar amounts $10,000 and above")
            e("  (e.g., $15,000 or $250,000.00)")
            blank()

            h("SEVERITY LEVELS")
            b("HIGH (red) \u2014 Data that could cause serious harm if exposed:")
            b("SSNs, credit cards, tax IDs. These should be investigated")
            b("immediately.")
            blank()
            b("MODERATE (yellow) \u2014 Data that may be sensitive depending on")
            b("context: emails, phone numbers, passwords, dates of birth.")
            b("Review to determine if exposure is a concern.")
            blank()
            b("INFO (blue) \u2014 Data that is noteworthy but not necessarily")
            b("sensitive: large dollar amounts. Useful for financial review")
            b("but unlikely to be a privacy risk on its own.")
            blank()

            h("CUSTOM PATTERN (ADVANCED)")
            b("The eight built-in categories cover common US PII. If you")
            b("need to scan for something else \u2014 an international ID, a")
            b("company-specific account number, an internal reference code")
            b("\u2014 the Custom Pattern section at the bottom of the category")
            b("selection popup lets you add your own regex to the scan.")
            blank()

            b("WHAT IS REGEX?")
            blank()
            b("Regex (short for 'regular expression') is a mini-language")
            b("for describing text patterns. Instead of searching for an")
            b("exact word like 'budget', a regex lets you describe a")
            b("shape \u2014 for example, 'three digits, a dash, two digits,")
            b("a dash, four digits' matches the SSN format 123-45-6789.")
            blank()
            b("You don't need to be a programmer to use basic regex.")
            b("Most useful patterns are built from a handful of building")
            b("blocks described below. If you can read a pattern like")
            b("\\d{3}-\\d{2}-\\d{4} and understand that \\d means 'any digit'")
            b("and {3} means 'exactly three,' you know enough to write")
            b("your own custom patterns for the PII Scan.")
            blank()
            b("If you've never used regex before, these free resources")
            b("can help you get started in 15\u201330 minutes:")
            blank()
            b("\u2022 regex101.com \u2014 an interactive regex tester where you can")
            b("  type a pattern, paste some sample text, and see what")
            b("  matches in real time. Choose the 'Python' flavor on the")
            b("  left sidebar. This is the single best way to learn.")
            b("\u2022 regexone.com \u2014 a free, step-by-step tutorial that teaches")
            b("  one concept at a time with interactive exercises.")
            b("\u2022 rexegg.com/regex-quickstart.html \u2014 a one-page cheat")
            b("  sheet with every regex symbol and what it does.")
            blank()

            b("HOW TO USE THE CUSTOM PATTERN")
            blank()
            b("1. Check the box next to 'Advanced \u2014 Custom Pattern'")
            b("2. Enter a short Name (e.g., 'UK NINO' or 'Client ID')")
            b("3. Enter the Regex pattern")
            b("4. Pick a Severity (HIGH / MODERATE / INFO)")
            b("5. Click Run Scan")
            blank()
            b("The custom pattern runs alongside the built-in categories")
            b("you have checked. Findings appear in the results popup and")
            b("report as a separate category with the name you entered,")
            b("marked with '(custom)' so you can tell it apart from the")
            b("built-in categories.")
            blank()

            b("REGEX BASICS")
            blank()
            b("Characters and digits:")
            e("  \\d              any single digit (0\u20139)")
            e("  \\D              any character that is NOT a digit")
            e("  \\w              any letter, digit, or underscore")
            e("  \\W              any character that is NOT a letter/digit/_")
            e("  \\s              any whitespace (space, tab, newline)")
            e("  \\S              any character that is NOT whitespace")
            e("  .               any single character except newline")
            e("  \\.              a literal dot (the backslash 'escapes' it)")
            blank()
            b("Repetition (how many times to match):")
            e("  \\d{3}           exactly 3 digits")
            e("  \\d{3,5}         3 to 5 digits")
            e("  \\d{3,}          3 or more digits")
            e("  \\d+             one or more digits (same as \\d{1,})")
            e("  \\d*             zero or more digits")
            e("  \\d?             zero or one digit (the digit is optional)")
            blank()
            b("Character classes (match one of a set):")
            e("  [A-Z]           any uppercase letter A\u2013Z")
            e("  [a-z]           any lowercase letter a\u2013z")
            e("  [A-Za-z]        any letter (upper or lower)")
            e("  [0-9]           any digit (same as \\d)")
            e("  [A-Z0-9]        any uppercase letter or digit")
            e("  [- ]            a dash or a space")
            e("  [^0-9]          any character EXCEPT a digit")
            blank()
            b("Anchors and grouping:")
            e("  ^               start of line")
            e("  $               end of line")
            e("  ( )             group characters together")
            e("  |               OR  (e.g., cat|dog matches 'cat' or 'dog')")
            e("  (?:  )          group without capturing (more efficient)")
            blank()
            b("Escaping special characters:")
            b("These characters have special meaning in regex:")
            e("  . * + ? [ ] ( ) { } ^ $ \\ |")
            b("To search for one of them literally, put a backslash")
            b("in front of it. For example:")
            e("  \\.              matches a literal dot")
            e("  \\$              matches a literal dollar sign")
            e("  \\(              matches a literal opening parenthesis")
            blank()
            b("Putting it together \u2014 reading a pattern:")
            e("  \\d{3}-\\d{2}-\\d{4}")
            b("  means: 3 digits, a dash, 2 digits, a dash, 4 digits")
            b("  matches: 123-45-6789 (SSN format)")
            blank()
            e("  [A-Z]{2}\\d{6}[A-Z]")
            b("  means: 2 uppercase letters, 6 digits, 1 uppercase letter")
            b("  matches: AB123456C (UK National Insurance Number)")
            blank()
            e("  \\$[\\d,]+\\.\\d{2}")
            b("  means: a dollar sign, one or more digits/commas, a dot,")
            b("  exactly 2 digits")
            b("  matches: $1,234.56  $99.00  $1,000,000.00")
            blank()

            b("EXAMPLE PATTERNS FOR COMMON FORMATS")
            blank()
            b("National ID numbers:")
            e("  US SSN:            \\d{3}-\\d{2}-\\d{4}")
            e("  UK NINO:           [A-Z]{2}\\d{6}[A-Z]")
            e("  Canadian SIN:      \\d{3}[- ]?\\d{3}[- ]?\\d{3}")
            e("  Australian TFN:    \\d{3}[ ]?\\d{3}[ ]?\\d{3}")
            e("  Indian PAN:        [A-Z]{5}\\d{4}[A-Z]")
            e("  Indian Aadhaar:    \\d{4}[ ]?\\d{4}[ ]?\\d{4}")
            e("  German Steuer-ID:  \\d{2}[ ]?\\d{3}[ ]?\\d{3}[ ]?\\d{3}")
            e("  French INSEE/NIR:  [12]\\d{2}[01]\\d{9}([ ]?\\d{2})?")
            e("  South Korean RRN:  \\d{6}-\\d{7}")
            e("  Brazilian CPF:     \\d{3}\\.\\d{3}\\.\\d{3}-\\d{2}")
            e("  Mexican CURP:      [A-Z]{4}\\d{6}[A-Z]{6}\\d{2}")
            blank()
            b("Tax and business numbers:")
            e("  US EIN:            \\d{2}-\\d{7}")
            e("  UK VAT:            GB\\d{9}")
            e("  EU VAT (generic):  [A-Z]{2}\\d{8,12}")
            e("  Australian ABN:    \\d{2}[ ]?\\d{3}[ ]?\\d{3}[ ]?\\d{3}")
            blank()
            b("Financial:")
            e("  IBAN (generic):    [A-Z]{2}\\d{2}[A-Z0-9]{4,30}")
            e("  SWIFT/BIC:         [A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?")
            e("  Dollar amounts:    \\$[\\d,]+\\.\\d{2}")
            e("  Euro amounts:      \\d+[,.]\\d{2}[ ]?\u20ac")
            blank()
            b("Technology:")
            e("  AWS access key:    AKIA[0-9A-Z]{16}")
            e("  Generic API key:   [A-Za-z0-9_]{20,}")
            e("  IPv4 address:      \\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}")
            e("  Email address:     [A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}")
            blank()
            b("Other:")
            e("  US passport:       [A-Z]\\d{8}")
            e("  UK passport:       \\d{9}")
            e("  US license plate:  [A-Z0-9]{2,7}")
            e("  Dates (YYYY-MM-DD): \\d{4}-\\d{2}-\\d{2}")
            e("  Dates (DD/MM/YYYY): \\d{2}/\\d{2}/\\d{4}")
            e("  Phone (intl):      \\+\\d{1,3}[- ]?\\d{4,14}")
            blank()
            b("Tip: copy a pattern from above, paste it into the Regex")
            b("field, give it a Name, and click Run Scan. You can also")
            b("test patterns at regex101.com (choose the Python flavor)")
            b("before running the scan.")
            blank()

            b("IMPORTANT NOTES")
            blank()
            b("\u2022 Don't worry about getting your regex wrong. peekdocs")
            b("  never modifies, moves, or deletes the files it searches")
            b("  \u2014 it only reads them and writes a summary report. The")
            b("  worst thing a bad regex can do is produce a useless or")
            b("  confusing report, which you can fix by running the scan")
            b("  again with a better pattern.")
            b("\u2022 Syntax errors in your regex are caught before the scan")
            b("  runs, so an invalid pattern will produce a friendly error")
            b("  message and not start the scan.")
            b("\u2022 Very broad patterns (like . or \\d) will match almost")
            b("  everything and produce a flood of findings. peekdocs")
            b("  warns you before running the scan if it detects one.")
            b("\u2022 Your Custom Pattern is saved between sessions. Uncheck")
            b("  the box to skip it for a scan without losing the pattern.")
            b("\u2022 Read the Disclaimer section below for the full list of")
            b("  what peekdocs does and does not promise about regex-based")
            b("  detection. Custom patterns are your responsibility.")
            blank()

            h("UNDERSTANDING RESULTS")
            b("The results popup shows each category with:")
            b("\u2022 A color-coded severity badge (HIGH/MODERATE/INFO)")
            b("\u2022 The number of matches and files affected")
            b("\u2022 'Clean' (green) if no matches were found")
            b("\u2022 A View Files button to see per-file details")
            blank()
            b("Click View Files to see which files contain that type of data,")
            b("with match counts and line numbers. Double-click a file to")
            b("open it in its default application.")
            blank()

            h("THE HIGHLIGHTED REPORT")
            b("When the scan detects findings, a Word report is automatically")
            b("generated and saved:")
            blank()
            e("  File:     DO_NOT_SEARCH_pii_scan_report.docx")
            e("  Location: Your search folder (or Output Dir if set)")
            blank()
            b("The report includes:")
            b("\u2022 Summary table of all categories with match counts")
            b("\u2022 Detail sections for each category with findings")
            b("\u2022 Every affected file with match count and line numbers")
            b("\u2022 The actual matched text with sensitive data highlighted")
            b("  in yellow")
            b("\u2022 A disclaimer about false positives")
            blank()
            b("Click Open Report in the results popup to view it directly.")
            b("The DO_NOT_SEARCH prefix ensures the report is never included")
            b("in future search results. The report is overwritten each time")
            b("you run a new PII scan.")
            blank()
            b("To save the report to a different folder, set Output Dir in")
            b("Advanced Search Options on the main screen before running the")
            b("scan. This is useful if you want to keep reports separate from")
            b("your documents \u2014 for example, a dedicated 'reports' folder.")
            blank()

            h("SAVING YOUR SELECTIONS")
            b("Your checkbox selections are saved to ~/.peekdocsrc and")
            b("remembered between sessions. The next time you open the PII")
            b("Scan, the same categories will be checked. Use Select All")
            b("or Deselect All for quick toggling.")
            blank()

            h("SEARCH FOLDER")
            b("The scan runs against whatever folder is shown at the top")
            b("of this window. Use Change Folder to switch without closing")
            b("the window. If Recursive is checked in Advanced Search")
            b("Options, all subfolders are included.")
            blank()
            b("The scan always searches files directly \u2014 it does not use")
            b("the search index, because regex pattern matching requires")
            b("scanning every line of text. The Use Index checkbox is")
            b("temporarily unchecked during the scan and restored afterward.")
            blank()

            h("HOW IT DIFFERS FROM REGULAR SEARCH")
            b("A regular search looks for terms you type. The PII Scan")
            b("runs 8 pre-built regex patterns designed to detect specific")
            b("types of sensitive data. You don't need to know regex \u2014")
            b("the patterns are built in.")
            blank()
            b("The PII Scan is a standalone one-click scan with its own")
            b("report. It does not save anything to your collection. If")
            b("you want to reuse the same regex patterns as normal searches,")
            b("use the Search Wizard to build an equivalent search and then")
            b("click Save Search to store it by name.")
            blank()

            h_red("THINK BEFORE YOU PRINT")
            b("The PII Scan report contains the actual sensitive data it")
            b("found \u2014 real SSNs, real credit card numbers, real passwords,")
            b("highlighted in yellow. Before printing or sharing the report,")
            b("consider whether you want that information on paper or in")
            b("someone else's hands. A printed report left on a desk or in")
            b("a recycling bin is itself a data exposure. If you need to")
            b("share findings with someone, consider describing the results")
            b("(e.g., '3 SSNs found in tax_return.docx') rather than")
            b("sending the report with the actual data visible.")
            blank()

            h("DISCLAIMER")
            b("The PII Scan is a pattern-matching discovery aid, not a")
            b("security product or a compliance certification. Please read")
            b("the following before relying on it.")
            blank()
            b("\u2022 False positives happen. A 9-digit account number can")
            b("  look like an SSN. A tracking number can match the credit")
            b("  card pattern. The word 'password' can appear in a help")
            b("  document that contains no actual passwords. Always review")
            b("  findings in context before taking action \u2014 the report")
            b("  shows the matched text with surrounding context precisely")
            b("  so you can judge whether each finding is real.")
            blank()
            b("\u2022 False negatives happen. The PII Scan cannot find PII")
            b("  that does not match its built-in regex patterns. An SSN")
            b("  written as '123 45 6789' (spaces instead of dashes) may")
            b("  not be detected. A credit card number without separators")
            b("  may be missed. A foreign tax ID in a format peekdocs")
            b("  does not know will not be flagged. A clean report does")
            b("  NOT prove that a file is free of sensitive data \u2014 it")
            b("  proves only that peekdocs's specific regex patterns did")
            b("  not match anything in the file's extracted text.")
            blank()
            b("\u2022 Some file formats may not be fully extracted. peekdocs")
            b("  searches 46 file types, but extraction quality varies. A")
            b("  scanned PDF without OCR enabled will not surface any")
            b("  text. An image file is ignored unless OCR is on. Complex")
            b("  binary formats may yield partial text. Files that")
            b("  peekdocs could not read will not produce findings even")
            b("  if they contain PII. Check View N excluded file(s) after")
            b("  each scan to see which files were skipped.")
            blank()
            b("\u2022 Not a breach prevention tool. The PII Scan finds and")
            b("  reports only. It does not block, encrypt, move, delete,")
            b("  or otherwise secure any data. Any action taken based on")
            b("  this report is the reader's decision and responsibility.")
            blank()
            b("\u2022 Not compliance software. A clean scan does not certify")
            b("  HIPAA, GDPR, PCI-DSS, SOX, or any other regulatory")
            b("  compliance. The PII Scan can be one input to a review")
            b("  process, but it is not a substitute for professional")
            b("  compliance expertise or a formal audit.")
            blank()
            b("\u2022 Custom user-supplied patterns are your responsibility.")
            b("  When you enter your own regex in the Custom Pattern section,")
            b("  peekdocs does not validate that your pattern correctly")
            b("  identifies the data you intend to find, and makes no")
            b("  representation about whether a custom pattern will match")
            b("  all instances of the data you are looking for. If you type")
            b("  your own regex, you own the outcome. peekdocs never")
            b("  modifies, moves, or deletes the files it searches, so a")
            b("  bad pattern cannot harm your documents \u2014 the worst outcome")
            b("  is a useless report, which you can fix by editing the")
            b("  pattern and re-running the scan.")
            blank()
            b("\u2022 Provided as-is under the MIT License. peekdocs comes")
            b("  with no warranty of any kind, express or implied. Users")
            b("  are solely responsible for how they interpret and act on")
            b("  these results. The full MIT License text is reproduced")
            b("  below.")
            blank()
            b("In short: the PII Scan is a helpful set of eyes on your own")
            b("files. It is not a guarantee, a certification, or a security")
            b("system. Use the results as a starting point for your own")
            b("review, not as a final answer.")
            blank()

            h("MIT LICENSE")
            b("Copyright (c) 2026 Robert D. Schoening")
            blank()
            b("Permission is hereby granted, free of charge, to any person")
            b("obtaining a copy of this software and associated documentation")
            b("files (the \"Software\"), to deal in the Software without")
            b("restriction, including without limitation the rights to use,")
            b("copy, modify, merge, publish, distribute, sublicense, and/or")
            b("sell copies of the Software, and to permit persons to whom")
            b("the Software is furnished to do so, subject to the following")
            b("conditions:")
            blank()
            b("The above copyright notice and this permission notice shall")
            b("be included in all copies or substantial portions of the")
            b("Software.")
            blank()
            b("THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY")
            b("KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE")
            b("WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR")
            b("PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS")
            b("OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR")
            b("OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR")
            b("OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE")
            b("SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.")
            blank()

            txt.configure(state="disabled")

            # Ensure Cmd+C (macOS) and Ctrl+C (Windows/Linux) copy the
            # selected text even though the widget is in disabled state.
            def _keyboard_copy(event):
                try:
                    sel = txt.get("sel.first", "sel.last")
                    if sel:
                        help_win.clipboard_clear()
                        help_win.clipboard_append(sel)
                except tk.TclError:
                    pass  # No selection
                return "break"

            txt.bind("<Command-c>", _keyboard_copy)   # macOS
            txt.bind("<Control-c>", _keyboard_copy)    # Windows / Linux

            close_btn = ctk.CTkButton(
                help_win, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=help_win.destroy,
                font=ctk.CTkFont(size=12),
            )
            close_btn.pack(pady=(5, 10))

        def _run_sensitive_scan(self, selected_patterns, folder=None, dollar_range=None):
            """Launch the sensitive data scan with the selected patterns."""
            if not folder:
                folder = self.folder_entry.get().strip()
            if not folder or folder == "(none)" or not os.path.isdir(folder):
                self._show_error("Please select a valid folder first.")
                return
            recursive = self.recursive_var.get() == "on"
            file_types_str = self.file_types_entry.get().strip() if hasattr(self, "file_types_entry") else ""
            file_types = None
            if file_types_str:
                file_types = ["." + t.strip().lstrip(".") for t in file_types_str.split(",") if t.strip()]

            # Save and uncheck Use Index — regex scans don't benefit from the index
            self._sensitive_scan_saved_index = self.index_search_var.get()
            self.index_search_var.set("off")

            self.sensitive_scan_btn.configure(state="disabled", text="\u25b6 Scanning...")
            self.status_label.configure(text="Scanning for sensitive data (index not used — regex scans files directly)...", text_color="blue")
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
            self.progress_bar.grid(row=7, column=0, columnspan=3, padx=15, pady=(10, 0), sticky="ew")

            thread = threading.Thread(
                target=self._sensitive_scan_thread,
                args=(folder, recursive, file_types, selected_patterns, dollar_range),
                daemon=True,
            )
            thread.start()

        def _sensitive_scan_thread(self, folder, recursive, file_types, selected_patterns=None, dollar_range=None):
            """Run selected sensitive data patterns in a background thread."""
            from peekdocs.api import search
            from peekdocs.sensitive_patterns import SENSITIVE_PATTERNS

            patterns = selected_patterns if selected_patterns else SENSITIVE_PATTERNS
            total_patterns = len(patterns)
            scan_results = []
            start = time.time()
            files_searched = 0

            for pat_idx, pattern_tuple in enumerate(patterns, 1):
                # 5-tuple: (category, regex, severity, description, is_custom)
                # Fall back to 4-tuple with is_custom=False for safety.
                if len(pattern_tuple) >= 5:
                    category, regex, severity, description, is_custom = pattern_tuple[:5]
                else:
                    category, regex, severity, description = pattern_tuple[:4]
                    is_custom = False
                self.after(0, lambda i=pat_idx, t=total_patterns, c=category:
                    self.status_label.configure(
                        text=f"Scanning for sensitive data... ({i}/{t}) {c}",
                        text_color="blue",
                    )
                )
                # For the Dollar Amounts category, inject a range filter and
                # update the display name/description to reflect the user's range
                range_filters = None
                if category == "Dollar Amounts" and dollar_range is not None:
                    lo, hi = dollar_range
                    range_filters = [f"amount:{lo}..{hi}"]
                    lo_label = f"${int(lo):,}" if float(lo).is_integer() else f"${lo:,}"
                    hi_label = f"${int(hi):,}" if float(hi).is_integer() else f"${hi:,}"
                    category = f"Dollar Amounts ({lo_label} \u2013 {hi_label})"
                    description = f"Dollar amounts between {lo_label} and {hi_label}"
                try:
                    result = search(
                        [regex],
                        directory=folder,
                        recursive=recursive,
                        use_regex=True,
                        use_index=False,
                        file_types=file_types,
                        range_filters=range_filters,
                    )
                    files_searched = max(files_searched, len(result.files_searched))
                    # Build per-file breakdown
                    file_matches = {}
                    for match in result.matches:
                        key = match.filename
                        if key not in file_matches:
                            file_matches[key] = {
                                "path": os.path.join(match.file_dir, match.filename),
                                "count": 0,
                                "lines": [],
                                "match_texts": [],
                            }
                        file_matches[key]["count"] += 1
                        file_matches[key]["lines"].append(match.line_num)
                        file_matches[key]["match_texts"].append(match.text)
                    scan_results.append({
                        "category": category,
                        "severity": severity,
                        "description": description,
                        "regex": regex,
                        "match_count": len(result.matches),
                        "file_count": len(file_matches),
                        "files": file_matches,
                        "is_custom": is_custom,
                    })
                except Exception:
                    scan_results.append({
                        "category": category,
                        "severity": severity,
                        "description": description,
                        "match_count": 0,
                        "file_count": 0,
                        "files": {},
                        "is_custom": is_custom,
                    })

            elapsed = time.time() - start
            self.after(0, self._sensitive_scan_finished, scan_results, elapsed, files_searched)

        def _sensitive_scan_finished(self, scan_results, elapsed, files_searched):
            """Restore UI and show results popup after sensitive data scan."""
            self.progress_bar.stop()
            self.progress_bar.grid_remove()
            self.sensitive_scan_btn.configure(state="normal", text="\u25b6 PII Scan")

            # Restore Use Index checkbox
            if hasattr(self, "_sensitive_scan_saved_index"):
                self.index_search_var.set(self._sensitive_scan_saved_index)

            total = sum(r["match_count"] for r in scan_results)
            high = sum(r["match_count"] for r in scan_results if r["severity"] == "high")

            if total == 0:
                self.status_label.configure(
                    text=f"Sensitive data scan complete ({elapsed:.1f}s, {files_searched} files) — no findings.",
                    text_color="green",
                )
            else:
                self.status_label.configure(
                    text=f"Sensitive data scan complete ({elapsed:.1f}s, {files_searched} files) — {total} finding(s) ({high} high severity).",
                    text_color="red" if high > 0 else "black",
                )
            # Generate .docx report
            folder = self.folder_entry.get().strip()
            self._pii_report_path = None
            if total > 0:
                try:
                    from peekdocs.reporter import write_pii_scan_report
                    report_name = "DO_NOT_SEARCH_pii_scan_report.docx"
                    output_dir = folder
                    # Use output dir if set in Advanced Search Options
                    if hasattr(self, "output_dir_entry"):
                        od = self.output_dir_entry.get().strip()
                        if od and os.path.isdir(od):
                            output_dir = od
                    report_path = os.path.join(output_dir, report_name)
                    write_pii_scan_report(report_path, scan_results, folder, elapsed, files_searched)
                    self._pii_report_path = report_path
                except Exception as _pii_err:
                    import traceback
                    traceback.print_exc()
                    self.status_label.configure(
                        text=f"PII report generation failed: {_pii_err}",
                        text_color="red",
                    )

            self._show_sensitive_scan_results(scan_results, elapsed, files_searched)

        def _show_sensitive_scan_results(self, scan_results, elapsed, files_searched):
            """Show a popup with categorized sensitive data scan results."""
            import tkinter as tk
            from peekdocs.sensitive_patterns import SEVERITY_COLORS, SEVERITY_ORDER

            popup = tk.Toplevel(self)
            popup.title("Sensitive Data Scan Results")
            popup.resizable(True, True)
            popup.geometry("800x520")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 800) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 520) // 2
            popup.geometry(f"+{x}+{y}")

            total = sum(r["match_count"] for r in scan_results)
            high = sum(r["match_count"] for r in scan_results if r["severity"] == "high")

            # Header
            if total == 0:
                header_text = f"No sensitive data found — {files_searched} files scanned in {elapsed:.1f}s"
                header_color = "green"
            else:
                header_text = f"{total} finding(s) across {files_searched} files ({elapsed:.1f}s)"
                header_color = "#CC0000" if high > 0 else "black"

            header_frame = tk.Frame(popup)
            header_frame.pack(fill="x", padx=15, pady=(10, 2))
            tk.Label(
                header_frame, text="Sensitive Data Scan Results",
                font=("TkDefaultFont", 14, "bold"),
            ).pack(side="left", expand=True)
            tk.Button(
                header_frame, text="?", width=3,
                font=("TkDefaultFont", 12, "bold"),
                command=lambda: self._show_pii_scan_results_help(popup),
            ).pack(side="right")
            tk.Label(
                popup, text=header_text,
                font=("TkDefaultFont", 12), fg=header_color,
            ).pack(pady=(0, 8))

            # Scrollable results frame
            canvas_frame = tk.Frame(popup)
            canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

            canvas = tk.Canvas(canvas_frame, highlightthickness=0)
            scrollbar = tk.Scrollbar(canvas_frame, command=canvas.yview)
            inner = tk.Frame(canvas)

            inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=inner, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # Sort built-in categories by severity, then custom patterns
            # at the bottom where the user expects to find them.
            severity_rank = {s: i for i, s in enumerate(SEVERITY_ORDER)}
            builtin = [r for r in scan_results if not r.get("is_custom")]
            custom = [r for r in scan_results if r.get("is_custom")]
            sorted_results = sorted(
                builtin,
                key=lambda r: (severity_rank.get(r["severity"], 99), -r["match_count"]),
            ) + sorted(
                custom,
                key=lambda r: (severity_rank.get(r["severity"], 99), -r["match_count"]),
            )

            for result in sorted_results:
                sev = SEVERITY_COLORS.get(result["severity"], SEVERITY_COLORS["info"])
                row = tk.Frame(inner, pady=3)
                row.pack(fill="x", padx=5, pady=2)

                # Severity badge
                badge = tk.Label(
                    row, text=f" {sev['label']} ", font=("TkDefaultFont", 10, "bold"),
                    bg=sev["bg"], fg=sev["fg"], width=10,
                )
                badge.pack(side="left", padx=(0, 8))

                # Category name
                tk.Label(
                    row, text=result["category"],
                    font=("TkDefaultFont", 12, "bold"), anchor="w",
                ).pack(side="left", padx=(0, 4))

                # Custom pattern marker — visually distinguish user-supplied
                # pattern findings from peekdocs's built-in categories
                if result.get("is_custom"):
                    tk.Label(
                        row, text="(custom)",
                        font=("TkDefaultFont", 10, "italic"),
                        fg="#996600",
                    ).pack(side="left", padx=(0, 8))

                if result["match_count"] == 0:
                    tk.Label(
                        row, text="Clean",
                        font=("TkDefaultFont", 11), fg="green",
                    ).pack(side="left")
                else:
                    count_text = f"{result['match_count']} match(es) in {result['file_count']} file(s)"
                    tk.Label(
                        row, text=count_text,
                        font=("TkDefaultFont", 11), fg="#CC0000" if result["severity"] == "high" else "black",
                    ).pack(side="left", padx=(0, 8))

                    files_data = result["files"]
                    cat_name = result["category"]
                    cat_regex = result.get("regex")
                    view_btn = tk.Button(
                        row, text="View Files",
                        font=("TkDefaultFont", 10),
                        command=lambda f=files_data, c=cat_name, p=popup, r=cat_regex: self._show_sensitive_category_files(f, c, p, regex=r),
                    )
                    view_btn.pack(side="right", padx=(0, 5))

                # Description
                desc_row = tk.Frame(inner)
                desc_row.pack(fill="x", padx=5)
                tk.Label(
                    desc_row, text=f"    {result['description']}",
                    font=("TkDefaultFont", 10), fg="gray",
                ).pack(side="left")

            # Mousewheel scrolling
            def _on_mousewheel(event):
                delta = event.delta
                if abs(delta) > 10:
                    delta = 1 if delta > 0 else -1
                else:
                    delta = max(-1, min(1, delta))
                canvas.yview_scroll(-delta, "units")

            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            popup.protocol("WM_DELETE_WINDOW", lambda: (canvas.unbind_all("<MouseWheel>"), popup.destroy()))

            if self._pii_report_path and os.path.exists(self._pii_report_path):
                def _open_report():
                    import subprocess, sys
                    try:
                        if sys.platform == "darwin":
                            subprocess.Popen(["open", self._pii_report_path])
                        elif sys.platform == "win32":
                            os.startfile(self._pii_report_path)
                        else:
                            subprocess.Popen(["xdg-open", self._pii_report_path])
                    except Exception:
                        pass
                open_btn = ctk.CTkButton(
                    popup, text="\u2b50 Open Highlighted Report \u2b50",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    fg_color="#2196F3", hover_color="#1976D2",
                    text_color="white",
                    width=260, height=36,
                    command=_open_report,
                )
                open_btn.pack(pady=(8, 4))

            tk.Button(
                popup, text="Close", width=10,
                command=lambda: (canvas.unbind_all("<MouseWheel>"), popup.destroy()),
            ).pack(pady=(0, 10))

        def _show_pii_scan_results_help(self, parent):
            """Show help for interpreting the PII Scan Results window."""
            import tkinter as tk
            help_win = tk.Toplevel(parent)
            help_win.title("PII Scan Results — Help")
            help_win.geometry("700x580")
            help_win.resizable(True, True)
            help_win.transient(parent)
            try:
                help_win.grab_set()
            except Exception:
                help_win.after(150, lambda: help_win.grab_set() if help_win.winfo_exists() else None)

            txt = tk.Text(help_win, wrap="word", font=("TkDefaultFont", 12),
                          padx=15, pady=10, borderwidth=0, highlightthickness=0)
            scroll = tk.Scrollbar(help_win, command=txt.yview)
            txt.configure(yscrollcommand=scroll.set)
            scroll.pack(side="right", fill="y")
            txt.pack(fill="both", expand=True)

            txt.tag_configure("heading", font=("TkDefaultFont", 14, "bold"),
                              spacing1=10, spacing3=5)
            txt.tag_configure("body", font=("TkDefaultFont", 12), spacing1=2)
            txt.tag_configure("example", font=("Courier", 11), lmargin1=30,
                              lmargin2=30, spacing1=2)
            txt.tag_configure("toc_title", font=("TkDefaultFont", 14, "bold"),
                              spacing1=5, spacing3=8)
            txt.tag_configure("toc_item", font=("TkDefaultFont", 11), lmargin1=20,
                              lmargin2=20, foreground="gray40")
            txt.tag_configure("heading_red", font=("TkDefaultFont", 13, "bold"),
                              spacing1=8, spacing3=4, foreground="red")

            def h(text):
                txt.insert("end", text + "\n", "heading")
            def h_red(text):
                txt.insert("end", text + "\n", "heading_red")
            def b(text):
                txt.insert("end", text + "\n", "body")
            def e(text):
                txt.insert("end", text + "\n", "example")
            def blank():
                txt.insert("end", "\n")

            txt.tag_configure("toc_item_red", font=("TkDefaultFont", 11, "bold"), lmargin1=20,
                              lmargin2=20, foreground="red")
            txt.insert("end", "TABLE OF CONTENTS\n", "toc_title")
            for section in [
                "What This Window Shows",
                "Severity Badges",
                "Reading the Match Counts",
                "View Files Button",
                "Open Report Button",
                "The Highlighted Report",
                "What to Do Next",
            ]:
                txt.insert("end", f"\u2022 {section}\n", "toc_item")
            txt.insert("end", "\u2022 Think Before You Print\n", "toc_item_red")
            txt.insert("end", "\u2022 False Positives\n", "toc_item")
            txt.insert("end", "\n")

            b("This window shows the results of the PII Scan \u2014 each")
            b("category the scan checked, with counts of matches found.")
            blank()

            h("WHAT THIS WINDOW SHOWS")
            b("Each row represents one of the 8 scan categories you ran.")
            b("The categories are sorted by severity (HIGH first, then")
            b("MODERATE, then INFO). Categories with no matches show a")
            b("green 'Clean' label \u2014 nothing to worry about.")
            blank()

            h("SEVERITY BADGES")
            b("HIGH (red) \u2014 Data that could cause serious harm if exposed:")
            b("Social Security numbers, credit card numbers, tax IDs.")
            b("Investigate these immediately.")
            blank()
            b("MODERATE (yellow) \u2014 Data that may be sensitive depending on")
            b("context: emails, phone numbers, passwords, dates of birth.")
            b("Review to determine if exposure is a concern.")
            blank()
            b("INFO (blue) \u2014 Noteworthy but not necessarily sensitive:")
            b("large dollar amounts. Useful for financial review.")
            blank()

            h("READING THE MATCH COUNTS")
            b("Each category with findings shows:")
            e("  12 match(es) in 3 file(s)")
            blank()
            b("This means peekdocs found 12 instances of that pattern across")
            b("3 different files. Some files may contain multiple matches.")
            blank()

            h("VIEW FILES BUTTON")
            b("Click View Files on any category to see exactly which files")
            b("contain that type of data. The sub-popup shows:")
            b("\u2022 Each affected file with its match count")
            b("\u2022 Line numbers where matches appear (up to 20 per file)")
            b("\u2022 Double-click a file to open it in its default application")
            blank()
            b("This is how you drill into a specific finding \u2014 start at")
            b("the category, find the file, open it, and look at the line.")
            blank()

            h("OPEN REPORT BUTTON")
            b("Click Open Report (at the bottom) to open the full highlighted")
            b("Word report: DO_NOT_SEARCH_pii_scan_report.docx")
            blank()
            b("The report is saved in your search folder (or in the Output Dir")
            b("if set in Advanced Search Options). It is overwritten each")
            b("time you run a new PII scan.")
            blank()

            h("THE HIGHLIGHTED REPORT")
            b("File name and location:")
            e("  File:     DO_NOT_SEARCH_pii_scan_report.docx")
            e("  Saved in: Your search folder (or in the Output Dir if set")
            e("            in Advanced Search Options)")
            blank()
            b("The report is overwritten each time you run a new PII scan.")
            b("To keep a copy, rename it or move it before running the next")
            b("scan.")
            blank()
            b("The .docx report contains:")
            b("\u2022 Summary table of all 8 categories with match counts")
            b("\u2022 Detail sections for each category with findings")
            b("\u2022 Every affected file listed with match count and line numbers")
            b("\u2022 The actual matched text with the sensitive data")
            b("  highlighted in yellow \u2014 so you can see exactly what")
            b("  was detected and in what context")
            b("\u2022 A disclaimer about false positives")
            blank()
            b("Example entry in the report:")
            e("  contract.docx  (2 match(es) \u2014 lines 47, 89)")
            e("  Line 47: Employee SSN: [123-45-6789]  \u2190 highlighted yellow")
            e("  Line 89: Contact SSN: [987-65-4321]  \u2190 highlighted yellow")
            blank()

            h("WHAT TO DO NEXT")
            b("For HIGH severity findings:")
            b("1. Click View Files to see which files are affected")
            b("2. Open each file and go to the listed line numbers")
            b("3. Determine whether the data should be there or not")
            b("4. If it shouldn't: redact, move to a secured location, or delete")
            b("5. Re-run the scan to verify the finding is gone")
            blank()
            b("For MODERATE/INFO findings: review to determine if any action")
            b("is needed based on your context. Some findings may be")
            b("legitimate (e.g., your own email address in a template).")
            blank()

            h_red("THINK BEFORE YOU PRINT")
            b("The PII Scan report contains the actual sensitive data it")
            b("found \u2014 real SSNs, real credit card numbers, real passwords,")
            b("highlighted in yellow. Before printing or sharing the report,")
            b("consider whether you want that information on paper or in")
            b("someone else's hands. A printed report left on a desk or in")
            b("a recycling bin is itself a data exposure. If you need to")
            b("share findings with someone, consider describing the results")
            b("(e.g., '3 SSNs found in tax_return.docx') rather than")
            b("sending the report with the actual data visible.")
            blank()

            h("FALSE POSITIVES")
            b("Pattern-based detection produces false positives. For example:")
            b("\u2022 A 9-digit account number that looks like an SSN")
            b("\u2022 A tracking number that matches the credit card pattern")
            b("\u2022 The word 'password' in a help document")
            blank()
            b("Always review findings in context before taking action.")
            b("The report shows the matched text with surrounding context")
            b("so you can quickly judge whether a finding is real.")
            blank()

            txt.configure(state="disabled")

            close_btn = ctk.CTkButton(
                help_win, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=help_win.destroy,
                font=ctk.CTkFont(size=12),
            )
            close_btn.pack(pady=(5, 10))

        def _show_sensitive_category_files(self, files_data, category, parent, regex=None):
            """Show files for a specific sensitive data category.

            If regex is provided, the View Text button opens the extracted-text
            view with that regex highlighted (so the user sees the actual PII
            matches for this category, not whatever is in the main search bar).
            """
            import tkinter as tk
            import subprocess, sys

            popup = tk.Toplevel(parent)
            popup.title(f"Files containing: {category}")
            popup.resizable(True, True)
            popup.geometry("750x400")
            parent.update_idletasks()
            x = parent.winfo_rootx() + 25
            y = parent.winfo_rooty() + 25
            popup.geometry(f"+{x}+{y}")

            tk.Label(
                popup, text=f"{category} — {len(files_data)} file(s)",
                font=("TkDefaultFont", 13, "bold"),
            ).pack(pady=(10, 5))

            list_frame = tk.Frame(popup)
            list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side="right", fill="y")

            listbox = tk.Listbox(
                list_frame, font=("TkDefaultFont", 11),
                selectmode=tk.SINGLE, activestyle="none",
                bg="#2b2b2b", fg="white", selectbackground="#1f6aa5",
                highlightthickness=0, borderwidth=1, relief="sunken",
                yscrollcommand=scrollbar.set,
            )
            listbox.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=listbox.yview)

            file_paths = {}
            for fname, info in sorted(files_data.items()):
                line_nums = sorted(set(info["lines"]))[:20]
                lines_str = ", ".join(str(ln) for ln in line_nums)
                if len(info["lines"]) > 20:
                    lines_str += "..."
                entry = f"{fname}  ({info['count']} match(es) — lines {lines_str})"
                idx = listbox.size()
                listbox.insert("end", entry)
                file_paths[idx] = info["path"]

            def _on_double_click(event):
                sel = listbox.curselection()
                if not sel or sel[0] not in file_paths:
                    return
                path = file_paths[sel[0]]
                try:
                    if sys.platform == "darwin":
                        subprocess.Popen(["open", path])
                    elif sys.platform == "win32":
                        os.startfile(path)
                    else:
                        subprocess.Popen(["xdg-open", path])
                except Exception:
                    pass

            listbox.bind("<Double-1>", _on_double_click)

            tk.Label(
                popup, text="Double-click a file to open it in its default application, "
                            "or select a file and click View Text below to see the "
                            "extracted text with line numbers and matches highlighted.",
                font=("TkDefaultFont", 10), fg="gray", wraplength=700, justify="center",
            ).pack(padx=10)

            def _view_text():
                sel = listbox.curselection()
                if not sel or sel[0] not in file_paths:
                    return
                path = file_paths[sel[0]]
                if not os.path.exists(path):
                    self._show_error(f"File not found: {path}")
                    return
                self._show_file_text_view(
                    path, os.path.basename(path),
                    highlight_regex_pattern=regex,
                )

            btn_frame = tk.Frame(popup)
            btn_frame.pack(pady=(5, 10))

            view_btn = tk.Label(
                btn_frame, text="View Text (with line numbers)",
                font=("TkDefaultFont", 13, "bold"),
                bg="#FF6B35", fg="white",
                relief="raised", borderwidth=2,
                padx=20, pady=8, cursor="hand2",
            )
            view_btn.pack(side="left", padx=5)
            view_btn.bind("<Button-1>", lambda e: _view_text())
            view_btn.bind("<Enter>", lambda e: view_btn.configure(bg="#E55A2B"))
            view_btn.bind("<Leave>", lambda e: view_btn.configure(bg="#FF6B35"))

            close_btn = tk.Label(
                btn_frame, text="Close",
                font=("TkDefaultFont", 13, "bold"),
                bg="#888888", fg="white",
                relief="raised", borderwidth=2,
                padx=20, pady=8, cursor="hand2",
            )
            close_btn.pack(side="left", padx=5)
            close_btn.bind("<Button-1>", lambda e: popup.destroy())
            close_btn.bind("<Enter>", lambda e: close_btn.configure(bg="#666666"))
            close_btn.bind("<Leave>", lambda e: close_btn.configure(bg="#888888"))

        def start_search(self):
            """Validate inputs, build the CLI command, and launch a search thread."""
            if self.process is not None:
                self.process.terminate()
                return

            # Wait for any in-progress index build or auto-refresh to finish
            if hasattr(self, '_index_process') and self._index_process is not None:
                self._show_error("Index build in progress — please wait for it to finish, or cancel it in Manage Indexes.")
                return
            if self._refresh_running:
                self._show_error("Index refresh in progress — please wait a moment.")
                return

            # Pause scheduled auto-refresh while search runs
            if self._refresh_timer_id is not None:
                self.after_cancel(self._refresh_timer_id)
                self._refresh_timer_id = None

            folder = os.path.normpath(self.folder_entry.get().strip())
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a valid folder.")
                return

            search_text = self.search_entry.get().strip()
            range_text = self.range_entry.get().strip()
            if not search_text and not range_text:
                self._show_error("Please enter search terms or a range filter.")
                return

            # Auto-save search terms, folder, and max file size for next launch
            # (max_file_size_mb must be saved here so the CLI subprocess picks it up)
            try:
                from peekdocs.cli import _load_config, _save_config
                cfg = _load_config()
                cfg["search_terms"] = search_text
                cfg["folder"] = folder
                try:
                    mfs = int(self.max_file_size_entry.get().strip() or "100")
                    cfg["max_file_size_mb"] = mfs
                except ValueError:
                    pass
                _save_config(cfg)
            except Exception:
                pass

            # Record in recent searches (max 10, no duplicates)
            if search_text and search_text not in self._recent_searches:
                self._recent_searches.insert(0, search_text)
                self._recent_searches = self._recent_searches[:10]
            elif search_text in self._recent_searches:
                self._recent_searches.remove(search_text)
                self._recent_searches.insert(0, search_text)

            if self.index_search_var.get() == "on":
                index_path = os.path.join(folder, ".peekdocs.db")
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
                output_pdf=self.output_pdf_var.get() == "on",
                index_search=self.index_search_var.get() == "on",
                inverse=self.inverse_var.get() == "on",
                expression=self.expression_var.get() == "on",
                whole_word=self.whole_word_var.get() == "on",
                max_matches=self.max_matches_entry.get(),
                max_file_size_mb=self.max_file_size_entry.get(),
                timestamp_suffix=self._last_ts_suffix,
                output_dir=self.output_dir_entry.get(),
                range_filters=self.range_entry.get(),
            )
            if cmd == "FLAGS_IN_SEARCH":
                self._show_error("Flags go in Advanced Search Options, not the search box.")
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
                    stale = os.path.join(self.results_dir, "peekdocs_results.csv")
                    if os.path.exists(stale):
                        os.remove(stale)
                if self.output_json_var.get() != "on":
                    stale = os.path.join(self.results_dir, "peekdocs_results.json")
                    if os.path.exists(stale):
                        os.remove(stale)
                if self.output_pdf_var.get() != "on":
                    stale = os.path.join(self.results_dir, "peekdocs_results.pdf")
                    if os.path.exists(stale):
                        os.remove(stale)
            self.search_button.configure(text="Cancel", fg_color="red", hover_color="darkred")
            self.search_entry.configure(state="disabled")
            self._clear_action_buttons()
            self._hide_files_list()
            self._hide_preview()
            self._matched_files_link.pack_forget()
            self._excluded_files_btn.pack_forget()
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
            self.progress_bar.grid(
                row=7, column=0, columnspan=3, padx=15, pady=(10, 0), sticky="ew"
            )
            # Count search terms for status display
            import shlex as _shlex
            try:
                _term_count = len(_shlex.split(search_text))
            except ValueError:
                _term_count = len(search_text.split())
            _term_label = f"{_term_count} term{'s' if _term_count != 1 else ''}"

            # If Use Index is on and the index was built with a different max file
            # size, warn the user that the index will be rebuilt during this search
            _will_rebuild = False
            if self.index_search_var.get() == "on":
                try:
                    from peekdocs.indexer import index_status as _istatus
                    status = _istatus(folder)
                    if status:
                        stored = status.get("max_file_size_mb")
                        try:
                            current_mfs = int(self.max_file_size_entry.get().strip() or "100")
                        except ValueError:
                            current_mfs = 100
                        if stored is None:
                            # Old index from before this feature — will rebuild
                            _will_rebuild = True
                        else:
                            try:
                                if int(stored) != current_mfs:
                                    _will_rebuild = True
                            except (ValueError, TypeError):
                                _will_rebuild = True
                except Exception:
                    pass

            if _will_rebuild:
                self.status_label.configure(
                    text=f"Rebuilding index with new Max File Size, then searching ({_term_label})...",
                    text_color="blue",
                )
            else:
                self.status_label.configure(text=f"Searching ({_term_label})...", text_color="blue")
            self.search_start_time = time.time()
            self._start_elapsed_timer()

            self.search_thread = threading.Thread(
                target=self._run_search, args=(cmd, folder), daemon=True
            )
            self.search_thread.start()

        def _start_elapsed_timer(self):
            """Start the repeating timer that updates the elapsed-time display."""
            self._update_elapsed()

        def _update_elapsed(self):
            """Update the status label with the current elapsed search time."""
            if self.process is None and self.search_start_time is None:
                return
            if self.search_start_time is not None:
                elapsed = time.time() - self.search_start_time
                dots = "." * (int(elapsed) % 4)
                # Preserve a "Rebuilding index..." prefix if set, append elapsed time
                current = self.status_label.cget("text") or ""
                if current.startswith("Rebuilding index"):
                    import re as _re
                    new_text = _re.sub(r"\s*\(\d+s\)\s*$", "", current)
                    new_text = f"{new_text} ({elapsed:.0f}s)"
                    self.status_label.configure(text=new_text, text_color="blue")
                else:
                    self.status_label.configure(
                        text=f"Searching{dots.ljust(3)}  ({elapsed:.0f}s elapsed)",
                        text_color="blue",
                    )
            self.elapsed_timer_id = self.after(1000, self._update_elapsed)

        def _run_search(self, cmd, folder):
            """Run the peekdocs subprocess in a background thread and post results."""
            import re as _re
            try:
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                self.process = subprocess.Popen(
                    cmd,
                    cwd=folder,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=env,
                )
                stdout, stderr = self.process.communicate()
                returncode = self.process.returncode
                # Include stderr in output if stdout is empty
                if not stdout.strip() and stderr.strip():
                    stdout = stderr
            except Exception as e:
                stdout = str(e)
                returncode = -1
            finally:
                self.process = None

            self.after(0, self._search_finished, stdout, returncode)

        def _show_preview(self, stdout):
            """Populate the results preview pane from search output."""
            import re as _re
            self.preview_text.configure(state="normal")
            self.preview_text.delete("1.0", "end")

            # If inverse search, show the list of files missing the term
            if self._inverse_results and self.matched_files:
                self.preview_text.tag_configure("inverse_header",
                    font=("TkDefaultFont", 12, "bold"), foreground="#FF6B35")
                self.preview_text.tag_configure("inverse_file",
                    font=("TkDefaultFont", 11))
                self.preview_text.insert("end",
                    f"Files WITHOUT your search term ({len(self.matched_files)} file(s)) \u2014 Inverse box checked:\n\n",
                    "inverse_header")
                for item in self.matched_files:
                    filepath, filename = item[0], item[1]
                    dirname = os.path.dirname(filepath)
                    self.preview_text.insert("end", f"  {filename}\n", "inverse_file")
                    self.preview_text.insert("end", f"  ({dirname})\n\n", "inverse_file")
                self.preview_text.configure(state="disabled")
                self.preview_text.see("1.0")
                self.preview_frame.grid(
                    row=8, column=0, columnspan=3, padx=15, pady=(5, 0), sticky="nsew"
                )
                return

            # Build highlight pattern from current search settings
            highlight_pattern = None
            search_text = self.search_entry.get().strip()
            use_regex = self.regex_var.get() == "on"
            use_wildcard = self.wildcard_var.get() == "on"
            use_whole_word = self.whole_word_var.get() == "on"
            use_fuzzy = self.fuzzy_var.get() == "on"
            is_expression = self.expression_var.get() == "on"

            if search_text and use_fuzzy:
                # For fuzzy, build patterns that match approximate words
                from rapidfuzz import fuzz
                import shlex as _shlex_fz
                try:
                    _fuzzy_terms = _shlex_fz.split(search_text)
                except ValueError:
                    _fuzzy_terms = search_text.split()
                _fuzzy_highlight = True
            else:
                _fuzzy_highlight = False

            if search_text and not use_fuzzy:
                patterns = []
                if is_expression:
                    from peekdocs.expr_parser import parse_expression, extract_positive_terms
                    terms = extract_positive_terms(parse_expression(search_text))
                else:
                    # Use shlex.split to respect quoted phrases (e.g., "insecure core")
                    import shlex as _shlex_hl
                    try:
                        terms = _shlex_hl.split(search_text)
                    except ValueError:
                        terms = search_text.split()
                for term in terms:
                    if use_wildcard:
                        from peekdocs.scanner import _wildcard_to_regex
                        patterns.append(_wildcard_to_regex(term))
                    elif use_regex:
                        patterns.append(term)
                    elif use_whole_word:
                        patterns.append(r'\b' + _re.escape(term) + r'\b')
                    else:
                        patterns.append(_re.escape(term))
                if patterns:
                    try:
                        highlight_pattern = _re.compile("|".join(patterns), _re.IGNORECASE)
                    except _re.error:
                        highlight_pattern = None

            def _insert_highlighted(line):
                """Insert a line with yellow highlighting on matched terms."""
                if highlight_pattern:
                    parts = highlight_pattern.split(line)
                    matches = highlight_pattern.findall(line)
                    for i, part in enumerate(parts):
                        if part:
                            self.preview_text.insert("end", part)
                        if i < len(matches):
                            self.preview_text.insert("end", matches[i], "match")
                elif _fuzzy_highlight:
                    # Highlight words that fuzzy-match the search terms
                    import re as _re_fz
                    from peekdocs.constants import FUZZY_THRESHOLD
                    words = _re_fz.split(r'(\s+)', line)
                    for word in words:
                        if word.strip() and any(
                            fuzz.ratio(term.lower(), word.lower()) >= FUZZY_THRESHOLD
                            for term in _fuzzy_terms
                        ):
                            self.preview_text.insert("end", word, "match")
                        else:
                            self.preview_text.insert("end", word)
                else:
                    self.preview_text.insert("end", line)
                self.preview_text.insert("end", "\n")

            # Parse the results file for cleaner output
            results_path = None
            if self.results_dir:
                suffix = f"_{self._last_ts_suffix}" if getattr(self, '_last_ts_suffix', '') else ""
                results_path = os.path.join(self.results_dir, f"peekdocs_results{suffix}.txt")

            lines_added = 0
            max_preview_lines = 500  # Cap to keep the GUI responsive

            if results_path and os.path.exists(results_path):
                in_results = False
                in_match_text = False
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
                            in_match_text = False
                            self.preview_text.insert("end", "\n")
                            self.preview_text.insert("end", line + "\n", "filename")
                        elif line.startswith("(") and not in_match_text:
                            self.preview_text.insert("end", line + "\n", "line_num")
                        elif line.startswith("Files WITHOUT matches:"):
                            self.preview_text.insert("end", line + "\n", "filename")
                        elif line.startswith('"') or in_match_text:
                            # Match text block — may span multiple wrapped lines
                            in_match_text = True
                            # Strip leading/trailing quotes
                            display = line
                            if display.startswith('"'):
                                display = display[1:]
                            if display.endswith('"'):
                                display = display[:-1]
                                in_match_text = False
                            _insert_highlighted(display)
                        elif line == "---":
                            self.preview_text.insert("end", "---\n")
                        elif line.strip() == "":
                            if not in_match_text:
                                continue  # Skip blank lines between matches
                        else:
                            _insert_highlighted(line)
                        lines_added += 1

            if lines_added == 0:
                self.preview_text.insert("end", "(No results to preview)")

            self.preview_text.configure(state="disabled")
            self.preview_text.see("1.0")

            # Update count label
            match_count = len(self.matched_files)
            if self._inverse_results:
                self._preview_count_label.configure(
                    text=f"{match_count} file(s) without matches")
            else:
                total_matches = sum(item[2] for item in self.matched_files)
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
                pct_display = int(pct * 100)
                self.status_label.configure(
                    text=f"Searching... {done}/{total} files  ({pct_display}%)  ({elapsed:.0f}s)",
                    text_color="blue",
                )

        def _search_finished(self, stdout, returncode):
            """Handle search completion by updating status, reports, and preview."""
            try:
                self.progress_bar.stop()
            except Exception:
                pass
            self.progress_bar.grid_remove()
            self.search_start_time = None
            if self.elapsed_timer_id:
                self.after_cancel(self.elapsed_timer_id)
                self.elapsed_timer_id = None

            self.search_button.configure(text="Search", fg_color="green", hover_color="darkgreen")
            self.search_entry.configure(state="normal")

            if returncode == -1:
                self._show_error("Search process failed to start.")
                return

            summary = _parse_summary_text(stdout)

            # Log to search history
            try:
                import re as _re_hist
                _clean = _re_hist.sub(r"\033\[[0-9;]*m", "", stdout or "")
                _h_matches = _re_hist.search(r"Found\s+(\d+)\s+match", _clean)
                _h_files = _re_hist.search(r"Files searched:\s*(\d+)", _clean)
                _h_elapsed = _re_hist.search(r"Elapsed time:\s*([\d.]+)", _clean)
                _h_search = self.search_entry.get().strip()
                if _h_search:
                    self._log_search_history(
                        _h_search,
                        int(_h_matches.group(1)) if _h_matches else 0,
                        int(_h_files.group(1)) if _h_files else 0,
                        _h_elapsed.group(1) if _h_elapsed else "",
                    )
            except Exception:
                pass

            # Check if any files were skipped (appears in subprocess output)
            import re as _re_fin
            _skip_match = _re_fin.search(r"Errors logged to peekdocs_errors\.log \((\d+) error", stdout or "")
            _skip_count = int(_skip_match.group(1)) if _skip_match else 0

            # Compute excluded files list (unsupported types, peekdocs outputs, etc.)
            folder = self.folder_entry.get().strip()
            recursive = self.recursive_var.get() == "on"
            try:
                self._excluded_files = self._compute_excluded_files(folder, recursive=recursive)
            except Exception:
                self._excluded_files = []
            _excl_count = len(self._excluded_files)
            if _excl_count > 0:
                self._excluded_files_btn.configure(text=f"{_excl_count} Excluded Files")
                self._excluded_files_btn.pack(side="left", padx=(5, 0))
            else:
                self._excluded_files_btn.pack_forget()

            # Error log tooltip removed — Error Log is now in Tools menu

            if returncode == 0:
                status_text = summary or "Search complete. Matches found."
                specific = self.specific_files_entry.get().strip()
                if specific:
                    status_text += f"  [{specific}]"
                if _skip_count:
                    status_text += f"  ({_skip_count} file(s) skipped — see Error Log)"
                self.status_label.configure(
                    text=status_text,
                    text_color="blue",
                )
                # Post-search save (-s) if user filled in "Save as" field
                save_name = self.save_name_entry.get().strip()
                if save_name:
                    save_cmd = [sys.executable, "-m", "peekdocs", "-s", save_name]
                    try:
                        result = subprocess.run(save_cmd, cwd=self.results_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
                        if result.returncode != 0:
                            self._show_error(f"Save failed: {result.stdout.strip() or 'unknown error'}")
                            return
                    except Exception as e:
                        self._show_error(f"Save failed: {e}")
                        return
                # Populate file list for the popup button
                ts = getattr(self, '_last_ts_suffix', '')
                results_fn = f"peekdocs_results_{ts}.txt" if ts else "peekdocs_results.txt"
                self._inverse_results = self.inverse_var.get() == "on"
                if self._inverse_results:
                    self.matched_files = _parse_inverse_files(self.results_dir, results_fn)
                else:
                    self.matched_files = _parse_matched_files(self.results_dir, results_fn)
                self._show_action_buttons(inverse=self._inverse_results)
                self._show_preview(stdout)
                # Show matched files link on status line
                if self.matched_files:
                    if self._inverse_results:
                        link_text = f"{len(self.matched_files)} File(s) Without Matches"
                        self._matched_files_link.configure(text=link_text, fg_color="#CC3333", hover_color="#AA2222")
                    else:
                        link_text = f"{len(self.matched_files)} Matched File(s)"
                        self._matched_files_link.configure(text=link_text, fg_color="#FF6B35", hover_color="#E55A2B")
                    self._matched_files_link.pack(side="left", padx=(5, 0))
            elif returncode == 1:
                no_match_text = summary or "Search complete. No matches found."
                specific = self.specific_files_entry.get().strip()
                if specific:
                    no_match_text += f"  [{specific}]"
                if _skip_count:
                    no_match_text += f"  ({_skip_count} file(s) skipped — see Error Log)"
                self.status_label.configure(
                    text=no_match_text,
                    text_color="blue",
                )
                self._matched_files_link.configure(
                    text="0 Matched File(s)",
                    fg_color="#CC3333", hover_color="#AA2222",
                )
                self._matched_files_link.pack(side="left", padx=(5, 0))
                self._show_action_buttons()
            elif returncode == 2:
                # Check if results were produced despite the error (e.g., .docx generation failed)
                ts = getattr(self, '_last_ts_suffix', '')
                results_fn = f"peekdocs_results_{ts}.txt" if ts else "peekdocs_results.txt"
                results_path = os.path.join(self.results_dir or folder, results_fn)
                if os.path.exists(results_path):
                    # Search succeeded but something else failed (likely report generation)
                    self.status_label.configure(
                        text=summary or "Search complete (with warnings — check error log).",
                        text_color="blue",
                    )
                    self._inverse_results = self.inverse_var.get() == "on"
                    if self._inverse_results:
                        self.matched_files = _parse_inverse_files(self.results_dir or folder, results_fn)
                    else:
                        self.matched_files = _parse_matched_files(self.results_dir or folder, results_fn)
                    self._show_action_buttons(inverse=self._inverse_results)
                    self._show_preview(stdout)
                else:
                    error_msg = stdout.strip() if stdout.strip() else "Search failed (exit code 2). No output captured."
                    self._show_error(error_msg)
                    self._show_action_buttons()
            else:
                self.status_label.configure(
                    text="Search was cancelled.", text_color="blue",
                )

            # Resume auto-refresh schedule if active
            self._reschedule_refresh()

            # Suggest indexing for large folders without an index
            if returncode in (0, 1) and self.index_search_var.get() != "on":
                _files_match = _re_fin.search(r"Files searched:\s*(\d+)", stdout or "")
                if _files_match:
                    _file_count = int(_files_match.group(1))
                    if _file_count >= 100:
                        from peekdocs.indexer import index_exists
                        if not index_exists(folder):
                            current = self.status_label.cget("text")
                            self.status_label.configure(
                                text=current + "  |  Tip: Build an index for faster searches — click Manage Indexes",
                            )

        def _show_action_buttons(self, inverse=False):
            """Show Matched Files and View Report buttons."""
            self._clear_action_buttons()

            has_matched = bool(self.matched_files)

            # Check which report formats exist
            report_formats = {}
            if self.results_dir:
                suffix = f"_{self._last_ts_suffix}" if getattr(self, '_last_ts_suffix', '') else ""
                for fmt in ("txt", "docx", "csv", "json", "pdf"):
                    path = os.path.join(self.results_dir, f"peekdocs_results{suffix}.{fmt}")
                    report_formats[fmt] = os.path.exists(path)

            has_any_report = any(report_formats.values())

            if not has_any_report:
                return

            # Pack report format buttons
            for fmt, btn in [
                ("txt", self.report_btn_txt),
                ("docx", self.report_btn_docx),
                ("csv", self.report_btn_csv),
                ("json", self.report_btn_json),
                ("pdf", self.report_btn_pdf),
            ]:
                btn.pack(side="left", padx=(0, 2))
                btn.configure(state="normal")
                if report_formats.get(fmt):
                    btn.configure(
                        fg_color="green",
                        hover_color="darkgreen",
                    )
                else:
                    btn.configure(
                        fg_color="#CC3333",
                        hover_color="#AA2222",
                    )
            self.report_frame.grid(
                row=9, column=0, padx=(15, 5), pady=(5, 5), sticky="w"
            )
        def _show_simple_popup(self, title, heading, message):
            """Show a simple informational popup with a consistent look and Close button."""
            import tkinter as tk
            popup = tk.Toplevel(self)
            popup.title(title)
            popup.resizable(False, False)
            popup.geometry("520x280")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 520) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 280) // 2
            popup.geometry(f"+{x}+{y}")
            try:
                popup.transient(self)
            except Exception:
                pass

            # Close button anchored to the bottom row
            ctk.CTkButton(
                popup, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=popup.destroy,
                font=ctk.CTkFont(size=12),
            ).pack(side="bottom", pady=(5, 15))

            tk.Label(
                popup, text=heading,
                font=("TkDefaultFont", 14, "bold"),
            ).pack(pady=(18, 8))

            tk.Label(
                popup, text=message,
                font=("TkDefaultFont", 12),
                wraplength=470, justify="left",
            ).pack(padx=20, pady=(0, 10), fill="both", expand=True)

        def open_error_log(self):
            """Open the peekdocs error log file in the default text editor."""
            # Check results dir first (output dir if set), then search folder
            candidates = []
            if self.results_dir:
                candidates.append(self.results_dir)
            folder = self.folder_entry.get().strip()
            if folder and folder not in candidates:
                candidates.append(folder)
            if not candidates:
                self._show_error("Please select a folder first.")
                return
            error_log_path = None
            for d in candidates:
                p = os.path.join(d, "peekdocs_errors.log")
                if os.path.exists(p):
                    error_log_path = p
                    break
            if not error_log_path:
                self._show_simple_popup(
                    title="Error Log",
                    heading="No Error Log Found",
                    message=(
                        "No error log was found.\n\n"
                        "This is good news — the log file is only created when a file error "
                        "occurs during a search (e.g., a file couldn't be read). If you haven't "
                        "had any errors, no log exists."
                    ),
                )
                self.status_label.configure(
                    text="No error log found — no file errors have occurred.",
                    text_color="green",
                )
                return
            system = platform.system()
            if system == "Darwin":
                subprocess.Popen(["open", error_log_path])
            elif system == "Windows":
                os.startfile(error_log_path)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", error_log_path])

        def _clear_results_files(self):
            """Delete all peekdocs_results* files from the search folder."""
            folder = self.results_dir or self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a folder first.")
                return
            # Find all peekdocs_results* files
            results_files = [
                f for f in os.listdir(folder)
                if f.startswith("peekdocs_results") and not f.startswith("peekdocs_results_dir")
            ]
            if not results_files:
                self.status_label.configure(text="No results files to clear.")
                return
            from tkinter import messagebox
            msg = f"Delete {len(results_files)} results file(s)?\n\n"
            if len(results_files) <= 10:
                msg += "\n".join(results_files)
            else:
                msg += "\n".join(results_files[:10]) + f"\n... and {len(results_files) - 10} more"
            msg += "\n\nThis cannot be undone."
            if messagebox.askyesno("Clear Search Results", msg):
                deleted = 0
                for fname in results_files:
                    try:
                        os.remove(os.path.join(folder, fname))
                        deleted += 1
                    except OSError:
                        pass
                self.status_label.configure(text=f"Deleted {deleted} results file(s).")
                self._hide_preview()
                self._clear_action_buttons()

        def _clear_error_log(self):
            """Delete the peekdocs error log file after confirmation."""
            folder = self.results_dir or self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a folder first.")
                return
            error_log_path = os.path.join(folder, "peekdocs_errors.log")
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

        def _clean_up_practice_files(self):
            """Delete all peekdocs-generated artifacts from the search folder
            (and all subfolders), preserving saved searches and settings.

            For users who have been experimenting with the app and want to
            start fresh before serious work.
            """
            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a folder first.")
                return

            # Files to delete — anything peekdocs created during searches
            # Preserved: .peekdocs_collection.json (saved searches)
            #           .peekdocsrc (in home dir, not search folder anyway)
            to_delete = []  # list of (path, reason)

            for root, dirs, files in os.walk(folder):
                for fname in files:
                    filepath = os.path.join(root, fname)
                    # Search result files
                    if fname.startswith("peekdocs_results"):
                        to_delete.append((filepath, "search results"))
                    # peekdocs-generated reports (e.g., PII scan report)
                    elif fname.startswith("DO_NOT_SEARCH"):
                        to_delete.append((filepath, "peekdocs report"))
                    # Error log
                    elif fname == "peekdocs_errors.log":
                        to_delete.append((filepath, "error log"))
                    # Index database
                    elif fname in (".peekdocs.db", ".peekdocs.db-wal", ".peekdocs.db-shm"):
                        to_delete.append((filepath, "index database"))

            if not to_delete:
                self.status_label.configure(
                    text="Nothing to clean up — no practice files found.",
                    text_color="blue",
                )
                return

            from tkinter import messagebox
            # Build confirmation message
            from collections import Counter
            reasons = Counter(r for _, r in to_delete)
            reason_lines = "\n".join(f"  \u2022 {count} {reason}" for reason, count in sorted(reasons.items()))
            msg = (
                f"Delete {len(to_delete)} practice file(s) from\n"
                f"{folder}\n\n"
                f"{reason_lines}\n\n"
                f"PRESERVED:\n"
                f"  \u2022 Your saved searches (.peekdocs_collection.json)\n"
                f"  \u2022 Your settings (~/.peekdocsrc)\n"
                f"  \u2022 Your original documents\n\n"
                f"This cannot be undone."
            )
            if not messagebox.askyesno("Clean Up Practice Files", msg):
                return

            deleted = 0
            failed = 0
            for path, _ in to_delete:
                try:
                    os.remove(path)
                    deleted += 1
                except OSError:
                    failed += 1

            # Refresh index button color since we may have deleted the index
            self._update_index_button_color()
            self._hide_preview()
            self._clear_action_buttons()

            if failed:
                self.status_label.configure(
                    text=f"Cleaned up {deleted} file(s). {failed} could not be deleted.",
                    text_color="blue",
                )
            else:
                self.status_label.configure(
                    text=f"Cleaned up {deleted} practice file(s). Saved searches preserved.",
                    text_color="blue",
                )

        def _open_report_format(self, fmt):
            """Open the report file for the given format (txt, docx, csv, json)."""
            suffix = f"_{self._last_ts_suffix}" if getattr(self, '_last_ts_suffix', '') else ""
            path = os.path.join(self.results_dir, f"peekdocs_results{suffix}.{fmt}")
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
                index_path = os.path.join(folder, ".peekdocs.db")
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
            from peekdocs.indexer import index_status
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

        _REFRESH_INTERVALS = {"Off": 0, "5 min": 5, "15 min": 15, "30 min": 30, "1 hour": 60, "4 hours": 240, "8 hours": 480, "24 hours": 1440}

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
            if not os.path.exists(os.path.join(folder, ".peekdocs.db")):
                self._reschedule_refresh()
                return
            if self.process is not None or self.search_start_time is not None:
                self._reschedule_refresh()
                return
            if self.build_index_button.cget("text") == "Building...":
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
            from peekdocs.indexer import refresh_index
            try:
                mfs = int(self.max_file_size_entry.get().strip() or "100")
            except (ValueError, AttributeError):
                mfs = 100
            try:
                result = refresh_index(folder, recursive=True, use_ocr=False, max_file_size_mb=mfs)
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

        def build_index_action(self):
            """Build a search index for the selected folder in a background thread."""
            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a valid folder.")
                return

            self.build_index_button.configure(state="disabled", text="Building...", width=120)
            self.cancel_index_button.pack(side="left", padx=5)
            self.search_button.configure(state="disabled", fg_color="#CC3333", hover_color="#AA2222")
            self.status_label.configure(
                text="Building index... this may take a few minutes for large folders. Please wait.",
                text_color="blue",
            )

            self._index_cancelled = False
            # Shared progress state (thread writes, main thread polls)
            self._index_progress = {"done": 0, "total": 0, "filename": "", "finished": False, "result": None, "returncode": None}

            def _progress_callback(done, total_count, filename):
                if self._index_cancelled:
                    raise InterruptedError("Index build cancelled by user")
                self._index_progress["done"] = done + 1
                self._index_progress["total"] = total_count
                self._index_progress["filename"] = filename or ""

            def _poll_progress():
                if self._index_progress["finished"]:
                    _finished(self._index_progress["result"], self._index_progress["returncode"])
                    return
                done = self._index_progress["done"]
                total = self._index_progress["total"]
                fname = self._index_progress["filename"]
                if total > 0:
                    short_name = os.path.basename(fname) if fname else ""
                    if len(short_name) > 50:
                        short_name = short_name[:47] + "..."
                    self.status_label.configure(
                        text=f"Building index... {done}/{total} files: {short_name}",
                        text_color="blue",
                    )
                self.after(300, _poll_progress)

            def _run():
                build_result = None
                try:
                    from peekdocs.indexer import build_index
                    self._index_process = "running"  # sentinel so start_search knows
                    try:
                        mfs = int(self.max_file_size_entry.get().strip() or "100")
                    except ValueError:
                        mfs = 100
                    build_result = build_index(folder, recursive=True, use_ocr=False,
                                               progress_callback=_progress_callback,
                                               max_file_size_mb=mfs)
                    returncode = 0
                except InterruptedError:
                    returncode = 2
                except Exception as e:
                    build_result = {"error": str(e)}
                    returncode = -1
                finally:
                    self._index_process = None
                self._index_progress["result"] = build_result
                self._index_progress["returncode"] = returncode
                self._index_progress["finished"] = True

            def _finished(result, returncode):
                self.build_index_button.configure(state="normal", text="Build Index(es)")
                self.cancel_index_button.pack_forget()
                self.search_button.configure(state="normal", fg_color="green", hover_color="darkgreen")
                self._update_index_button_color()
                if returncode == 0 and result:
                    fc = result.get("file_count", 0)
                    lc = result.get("line_count", 0)
                    el = result.get("elapsed", 0)
                    display = f"Index built: {fc} files, {lc:,} lines in {el:.1f}s"
                    self.status_label.configure(text=display, text_color="blue")
                    # Default auto-refresh to 1 hour if currently Off
                    if self.refresh_interval_var.get() == "Off":
                        self.refresh_interval_var.set("1 hour")
                        self._on_refresh_interval_changed("1 hour")
                elif returncode == 2:
                    self.status_label.configure(text="Index build cancelled.", text_color="blue")
                else:
                    err_msg = (result or {}).get("error", "Unknown error")
                    self.status_label.configure(text=f"Index build failed: {err_msg}", text_color="red")

            threading.Thread(target=_run, daemon=True).start()
            self.after(300, _poll_progress)

        def delete_index_action(self):
            """Delete the search index from the selected folder."""
            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a valid folder.")
                return

            cmd = [sys.executable, "-m", "peekdocs", "-q", "--index-clear"]
            try:
                result = subprocess.run(cmd, cwd=folder, capture_output=True, text=True, encoding="utf-8", errors="replace")
                msg = result.stdout.strip()
            except Exception:
                self._show_error("Failed to delete index.")
                return
            self.status_label.configure(
                text=msg or "Index removed.",
                text_color="blue",
            )
            self._update_index_button_color()
            self.refresh_interval_var.set("Off")
            self._on_refresh_interval_changed("Off")

        def index_status_action(self):
            """Display index status information in a popup window."""
            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a valid folder.")
                return

            # Read index status directly — no subprocess needed
            try:
                from peekdocs.indexer import index_status as _idx_status
                from peekdocs.constants import INDEX_FILENAME as _IDX_FILE
                status = _idx_status(folder)
            except Exception as e:
                self._show_error(f"Failed to get index status: {e}")
                return

            if status is None:
                self.status_label.configure(
                    text="No index found. Click Build Index(es) to create one.",
                    text_color="blue",
                )
                return

            # Build status text
            from peekdocs.reporter import fmt_size as _fmt_size
            db_path = os.path.join(folder, _IDX_FILE)
            stdout = (
                "Index status:\n"
                f"  Index file:     {_IDX_FILE}\n"
                f"  Folder:         {folder}\n"
                f"  Full path:      {db_path}\n"
                f"  Files indexed:  {status.get('file_count', '?')}\n"
                f"  Lines indexed:  {status.get('line_count', '?')}\n"
                f"  Database size:  {_fmt_size(status.get('db_size', 0))}\n"
                f"  Created:        {status.get('created_at', '?')}\n"
                f"  Last updated:   {status.get('last_updated', status.get('created_at', '?'))}\n"
                f"  Recursive:      {status.get('recursive', '?')}\n"
                f"  OCR:            {status.get('use_ocr', '?')}\n"
                f"  peekdocs ver:  {status.get('peekdocs_version', '?')}"
            )

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

        def _show_index_help(self):
            """Show help explaining what indexes are and when to use them."""
            import tkinter as tk
            help_win = tk.Toplevel(self.index_window or self)
            help_win.title("Manage Indexes — Help")
            help_win.geometry("650x560")
            help_win.resizable(True, True)
            if self.index_window:
                help_win.transient(self.index_window)

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
            txt.tag_configure("body", font=("TkDefaultFont", 12), lmargin1=20, lmargin2=20)
            txt.tag_configure("example", font=("Courier", 12), lmargin1=30, lmargin2=30)
            txt.tag_configure("toc_title", font=("TkDefaultFont", 14, "bold"), spacing1=5, spacing3=8)
            txt.tag_configure("toc_item", font=("TkDefaultFont", 11), lmargin1=20, lmargin2=20,
                              foreground="gray40")

            def h(text):
                txt.insert("end", text + "\n", "heading")
            def s(text):
                txt.insert("end", text + "\n", "subhead")
            def b(text):
                txt.insert("end", text + "\n", "body")
            def e(text):
                txt.insert("end", text + "\n", "example")
            def blank():
                txt.insert("end", "\n")

            txt.insert("end", "TABLE OF CONTENTS\n", "toc_title")
            for section in [
                "Quick Start",
                "Buttons on This Panel",
                "Use Index Checkbox (Main Screen)",
                "Do I Need an Index?",
                "Good to Know",
            ]:
                txt.insert("end", f"\u2022 {section}\n", "toc_item")
            txt.insert("end", "\n")

            h("QUICK START")
            b("Click Build Index(es) and you're done. peekdocs reads")
            b("your files once, enables Use Index, and sets Auto-Refresh")
            b("to 1 hour. All future searches are faster and the index")
            b("stays current automatically.")
            blank()

            h("BUTTONS ON THIS PANEL")
            blank()
            s("Build Index(es)")
            b("Reads every file in the search folder (and all subfolders)")
            b("and stores the extracted text in a database. Run Search is")
            b("disabled while this runs. May take a few minutes for large")
            b("folders. This button is red when no index exists and blue")
            b("when one does. When no index exists, the Use Index checkbox")
            b("on the main screen is automatically unchecked and grayed out.")
            blank()
            s("Delete Index(es)")
            b("Removes the index database. Searches go back to reading")
            b("files directly. You can rebuild anytime.")
            blank()
            s("Index Status")
            b("Shows how many files are indexed, the database size, and")
            b("when it was last updated.")
            blank()
            s("Auto-Refresh")
            b("Keeps the index current by checking for new, changed, and")
            b("deleted files at the interval you choose. Set automatically")
            b("to 1 hour when you first build an index. Change it anytime:")
            blank()
            b("\u2022 5\u201315 min \u2014 files change frequently")
            b("\u2022 30 min\u20131 hour \u2014 files change occasionally")
            b("\u2022 4\u201324 hours \u2014 stable folders")
            b("\u2022 Off \u2014 rebuild manually when needed")
            blank()

            h("USE INDEX CHECKBOX (MAIN SCREEN)")
            b("Controls whether searches use the index or read files")
            b("directly. Enabled automatically when an index exists.")
            b("Grayed out when no index exists. Uncheck it to compare")
            b("indexed vs direct results, or if indexed search feels")
            b("slower for your particular folder.")
            blank()

            h("DO I NEED AN INDEX?")
            b("Yes, if you search the same folder often (100+ files).")
            b("No, if your folder is small or you rarely re-search it.")
            b("peekdocs suggests building one when it would help.")
            blank()
            b("If indexed search feels slower than direct search,")
            b("uncheck Use Index. This can happen with folders that")
            b("have a few very large files instead of many small ones.")
            blank()

            h("GOOD TO KNOW")
            b("\u2022 Results are identical with or without an index")
            b("\u2022 The index is one file (.peekdocs.db) in your search folder")
            b("\u2022 One index covers the folder and all subfolders")
            b("\u2022 Safe to delete \u2014 rebuild with Build Index(es) anytime")
            b("\u2022 If Use Index is checked but no index exists, peekdocs")
            b("  falls back to direct scanning automatically")
            b("\u2022 Changing Max File Size (in Advanced Search Options) triggers")
            b("  an automatic rebuild on the next indexed search")

            txt.configure(state="disabled")

            close_btn = ctk.CTkButton(
                help_win, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=help_win.destroy,
                font=ctk.CTkFont(size=12),
            )
            close_btn.pack(pady=(5, 10))

        def _open_selected_file(self):
            """Open the selected file from the matched files list in the default app."""
            selection = self.files_listbox.curselection()
            if not selection:
                return
            filepath = self.matched_files[selection[0]][0]
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
            """Clear the matched files list."""
            self.matched_files = []
            self._excluded_files = []

        def _compute_excluded_files(self, folder, recursive=True):
            """Walk the search folder and return a list of (filepath, reason) tuples
            for files that peekdocs did NOT include in its search pool.

            Files that were discovered but skipped at process time (e.g., oversized)
            are reported in the error log, not here — that avoids double-counting.
            """
            from peekdocs.constants import SUPPORTED_TYPES, OCR_IMAGE_TYPES
            from peekdocs.scanner import discover_files as _discover
            excluded = []
            use_ocr = self.ocr_var.get() == "on"
            supported = SUPPORTED_TYPES | (OCR_IMAGE_TYPES if use_ocr else set())

            # Get the set of files peekdocs would include in its search pool
            try:
                disc = _discover(folder, recursive=recursive, use_ocr=use_ocr)
                if isinstance(disc, tuple):
                    searched_set = set()
                else:
                    searched_set = {os.path.normcase(os.path.normpath(p)) for p in disc}
            except Exception:
                searched_set = set()

            _PEEKDOCS_INTERNAL = {
                ".peekdocs.db", ".peekdocs.db-wal", ".peekdocs.db-shm",
                ".peekdocs_collection.json", ".peekdocsrc",
                "peekdocs_errors.log",
            }

            walker = os.walk(folder) if recursive else [(folder, [], os.listdir(folder))]
            for root, dirs, files in walker:
                for fname in files:
                    filepath = os.path.join(root, fname)
                    # Skip files that discover_files already includes
                    if os.path.normcase(os.path.normpath(filepath)) in searched_set:
                        continue
                    ext = os.path.splitext(fname)[1].lower()

                    # Hidden file
                    if fname.startswith("."):
                        if fname in _PEEKDOCS_INTERNAL:
                            excluded.append((filepath, "peekdocs internal file (hidden)"))
                        else:
                            excluded.append((filepath, "hidden file (starts with .)"))
                        continue

                    # peekdocs output files
                    if fname.startswith("peekdocs_results") or fname.startswith("DO_NOT_SEARCH"):
                        excluded.append((filepath, "peekdocs output file (prior search results)"))
                        continue
                    if fname in _PEEKDOCS_INTERNAL:
                        excluded.append((filepath, "peekdocs internal file"))
                        continue

                    # Unsupported file type
                    if ext not in supported:
                        if ext in OCR_IMAGE_TYPES and not use_ocr:
                            excluded.append((filepath, f"image file ({ext}) — enable OCR to search"))
                        else:
                            excluded.append((filepath, f"unsupported file type ({ext or 'no extension'})"))
                        continue

                    # Supported type but not in searched set — unknown reason
                    excluded.append((filepath, "not included in search (unknown reason)"))
                if not recursive:
                    break
            return excluded

        # ── File Inventory ────────────────────────────────────────

        def _run_file_inventory(self):
            """Launch a background scan to inventory all files in the search folder."""
            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a search folder first.")
                return
            recursive = self.recursive_var.get() == "on"
            self.status_label.configure(
                text="Scanning folder for file inventory...", text_color="blue")
            self.progress_bar.grid(
                row=7, column=0, columnspan=3, padx=10, pady=(2, 2), sticky="ew")
            self.progress_bar.start()
            import threading
            t = threading.Thread(
                target=self._file_inventory_thread,
                args=(folder, recursive), daemon=True)
            t.start()

        def _file_inventory_thread(self, folder, recursive):
            """Worker thread: walk the folder tree and collect file stats."""
            from collections import Counter
            from datetime import datetime

            type_counts = Counter()
            type_sizes = Counter()
            total_size = 0
            total_files = 0
            total_dirs = 0
            oldest_date = None
            oldest_file = None
            newest_date = None
            newest_file = None
            skipped = 0

            try:
                if recursive:
                    walker = os.walk(folder)
                else:
                    # Single level only
                    top_entries = []
                    try:
                        top_entries = os.listdir(folder)
                    except PermissionError:
                        skipped += 1
                    walker = [(folder, [], top_entries)]

                for root, dirs, files in walker:
                    total_dirs += len(dirs)
                    for fname in files:
                        filepath = os.path.join(root, fname)
                        try:
                            stat = os.stat(filepath)
                            fsize = stat.st_size
                            mtime = stat.st_mtime
                        except (OSError, PermissionError):
                            skipped += 1
                            continue

                        total_files += 1
                        total_size += fsize

                        ext = os.path.splitext(fname)[1].lower()
                        if not ext:
                            ext = "(no extension)"
                        type_counts[ext] += 1
                        type_sizes[ext] += fsize

                        mdt = datetime.fromtimestamp(mtime)
                        if oldest_date is None or mdt < oldest_date:
                            oldest_date = mdt
                            oldest_file = filepath
                        if newest_date is None or mdt > newest_date:
                            newest_date = mdt
                            newest_file = filepath
            except Exception:
                pass

            results = {
                "folder": folder,
                "recursive": recursive,
                "total_files": total_files,
                "total_dirs": total_dirs,
                "total_size": total_size,
                "type_counts": type_counts,
                "type_sizes": type_sizes,
                "oldest_date": oldest_date,
                "oldest_file": oldest_file,
                "newest_date": newest_date,
                "newest_file": newest_file,
                "skipped": skipped,
            }
            self.after(0, self._file_inventory_finished, results)

        def _file_inventory_finished(self, results):
            """Handle inventory completion — stop progress and show popup."""
            try:
                self.progress_bar.stop()
            except Exception:
                pass
            self.progress_bar.grid_remove()
            self.status_label.configure(
                text=f"File inventory complete — {results['total_files']} file(s) found.",
                text_color="blue")
            self._show_file_inventory_popup(results)

        @staticmethod
        def _format_file_size(size_bytes):
            """Format bytes as a human-readable string."""
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

        def _show_file_inventory_popup(self, results):
            """Display the file inventory results in a popup window."""
            import tkinter as tk
            fmt = self._format_file_size

            popup = tk.Toplevel(self)
            popup.title("File Inventory")
            popup.resizable(True, True)
            popup.geometry("780x580")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 780) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 580) // 2
            popup.geometry(f"+{x}+{y}")

            # Header
            header_frame = tk.Frame(popup)
            header_frame.pack(fill="x", padx=10, pady=(10, 2))
            tk.Label(
                header_frame,
                text=f"File Inventory — {results['total_files']} file(s)",
                font=("TkDefaultFont", 13, "bold"),
            ).pack(side="left", expand=True)

            # Folder path
            tk.Label(
                popup, text=results["folder"],
                font=("TkDefaultFont", 10), fg="gray",
            ).pack(pady=(0, 5))

            # Summary frame
            summary_frame = tk.Frame(popup)
            summary_frame.pack(fill="x", padx=15, pady=(0, 5))

            lines = []
            lines.append(f"Total files:     {results['total_files']}")
            lines.append(f"Total size:      {fmt(results['total_size'])}")
            if results["recursive"]:
                lines.append(f"Subfolders:      {results['total_dirs']}")
            lines.append(f"File types:      {len(results['type_counts'])}")
            if results["oldest_date"] and results["oldest_file"]:
                lines.append(f"Oldest file:     {os.path.basename(results['oldest_file'])}  ({results['oldest_date'].strftime('%Y-%m-%d')})")
            if results["newest_date"] and results["newest_file"]:
                lines.append(f"Newest file:     {os.path.basename(results['newest_file'])}  ({results['newest_date'].strftime('%Y-%m-%d')})")
            if results["skipped"]:
                lines.append(f"Skipped:         {results['skipped']} file(s) (permission denied)")

            tk.Label(
                summary_frame, text="\n".join(lines),
                font=("Courier", 11), justify="left", anchor="nw",
            ).pack(anchor="w")

            # Separator
            tk.Frame(popup, height=1, bg="gray60").pack(fill="x", padx=10, pady=(5, 5))

            # File type breakdown label
            tk.Label(
                popup, text="Breakdown by File Type",
                font=("TkDefaultFont", 12, "bold"),
            ).pack(pady=(2, 4))

            # Listbox with type breakdown
            list_frame = tk.Frame(popup)
            list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side="right", fill="y")

            listbox = tk.Listbox(
                list_frame, font=("Courier", 11),
                selectmode=tk.SINGLE, activestyle="none",
                bg="#2b2b2b", fg="white", selectbackground="#1f6aa5",
                highlightthickness=0, borderwidth=1, relief="sunken",
                yscrollcommand=scrollbar.set,
            )
            listbox.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=listbox.yview)

            # Header row
            listbox.insert("end", f"{'Extension':<20}{'Files':>8}{'Size':>14}")
            listbox.insert("end", f"{'─' * 20}{'─' * 8}{'─' * 14}")

            # Sort by count descending
            sorted_types = sorted(
                results["type_counts"].items(),
                key=lambda x: x[1], reverse=True)

            for ext, count in sorted_types:
                size_str = fmt(results["type_sizes"][ext])
                listbox.insert("end", f"{ext:<20}{count:>8}{size_str:>14}")

            # Total row
            listbox.insert("end", f"{'─' * 20}{'─' * 8}{'─' * 14}")
            listbox.insert("end", f"{'TOTAL':<20}{results['total_files']:>8}{fmt(results['total_size']):>14}")

            # Buttons
            btn_frame = tk.Frame(popup)
            btn_frame.pack(pady=(5, 10))

            save_btn = ctk.CTkButton(
                btn_frame, text="Save Report", width=100,
                command=lambda: self._save_inventory_report(results),
                font=ctk.CTkFont(size=12),
            )
            save_btn.pack(side="left", padx=5)
            Tooltip(save_btn, "Save this inventory as a plain text file")

            close_btn = ctk.CTkButton(
                btn_frame, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=popup.destroy,
                font=ctk.CTkFont(size=12),
            )
            close_btn.pack(side="left", padx=5)

        def _save_inventory_report(self, results):
            """Save the file inventory as a plain text report."""
            from tkinter import filedialog
            from datetime import datetime
            fmt = self._format_file_size

            default_name = f"file_inventory_{datetime.now().strftime('%Y-%m-%d')}.txt"
            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")],
                initialfile=default_name,
                title="Save File Inventory Report",
            )
            if not filepath:
                return

            lines = []
            lines.append("=" * 60)
            lines.append("FILE INVENTORY REPORT")
            lines.append("=" * 60)
            lines.append(f"Folder:      {results['folder']}")
            lines.append(f"Recursive:   {'Yes' if results['recursive'] else 'No'}")
            lines.append(f"Generated:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")
            lines.append(f"Total files:     {results['total_files']}")
            lines.append(f"Total size:      {fmt(results['total_size'])}")
            if results["recursive"]:
                lines.append(f"Subfolders:      {results['total_dirs']}")
            lines.append(f"File types:      {len(results['type_counts'])}")
            if results["oldest_date"] and results["oldest_file"]:
                lines.append(f"Oldest file:     {os.path.basename(results['oldest_file'])}  ({results['oldest_date'].strftime('%Y-%m-%d')})")
            if results["newest_date"] and results["newest_file"]:
                lines.append(f"Newest file:     {os.path.basename(results['newest_file'])}  ({results['newest_date'].strftime('%Y-%m-%d')})")
            if results["skipped"]:
                lines.append(f"Skipped:         {results['skipped']} file(s) (permission denied)")
            lines.append("")
            lines.append("-" * 60)
            lines.append(f"{'Extension':<20}{'Files':>8}{'Size':>14}")
            lines.append("-" * 60)

            sorted_types = sorted(
                results["type_counts"].items(),
                key=lambda x: x[1], reverse=True)
            for ext, count in sorted_types:
                size_str = fmt(results["type_sizes"][ext])
                lines.append(f"{ext:<20}{count:>8}{size_str:>14}")

            lines.append("-" * 60)
            lines.append(f"{'TOTAL':<20}{results['total_files']:>8}{fmt(results['total_size']):>14}")
            lines.append("")
            lines.append("Generated by peekdocs")

            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines) + "\n")
                self.status_label.configure(
                    text=f"Inventory report saved: {os.path.basename(filepath)}",
                    text_color="blue")
            except Exception as e:
                self._show_error(f"Failed to save report: {e}")

        # ── Password-Protected File Detector ─────────────────────

        def _run_protected_scan(self):
            """Launch a background scan for password-protected / encrypted files."""
            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a search folder first.")
                return
            recursive = self.recursive_var.get() == "on"
            self.status_label.configure(
                text="Scanning for password-protected files...", text_color="blue")
            self.progress_bar.grid(
                row=7, column=0, columnspan=3, padx=10, pady=(2, 2), sticky="ew")
            self.progress_bar.start()
            import threading
            t = threading.Thread(
                target=self._protected_scan_thread,
                args=(folder, recursive), daemon=True)
            t.start()

        def _protected_scan_thread(self, folder, recursive):
            """Worker thread: check each file for password protection."""
            import fitz
            import olefile
            import zipfile

            protected = []  # list of (filepath, file_type, reason)
            scanned = 0

            # Extensions worth checking — only formats that support encryption
            _check_exts = {
                ".pdf", ".docx", ".xlsx", ".pptx",
                ".doc", ".xls", ".ppt",
                ".odt", ".ods", ".odp",
                ".zip", ".7z", ".rar",
            }

            try:
                if recursive:
                    walker = os.walk(folder)
                else:
                    try:
                        entries = os.listdir(folder)
                    except PermissionError:
                        entries = []
                    walker = [(folder, [], entries)]

                for root, dirs, files in walker:
                    for fname in files:
                        ext = os.path.splitext(fname)[1].lower()
                        if ext not in _check_exts:
                            continue
                        filepath = os.path.join(root, fname)
                        scanned += 1
                        try:
                            if ext == ".pdf":
                                doc = fitz.open(filepath)
                                if doc.is_encrypted:
                                    protected.append((filepath, "PDF", "Encrypted PDF — requires a password to open"))
                                doc.close()

                            elif ext in (".docx", ".xlsx", ".pptx"):
                                # Modern Office files are ZIP archives.
                                # Encrypted ones are wrapped in an OLE container instead.
                                try:
                                    if olefile.isOleFile(filepath):
                                        ole = olefile.OleFileIO(filepath)
                                        if ole.exists("EncryptedPackage"):
                                            label = {".docx": "Word", ".xlsx": "Excel", ".pptx": "PowerPoint"}[ext]
                                            protected.append((filepath, label, f"Encrypted {label} document — requires a password to open"))
                                        ole.close()
                                    else:
                                        # Try opening as ZIP — if it fails, file may be corrupt
                                        try:
                                            zf = zipfile.ZipFile(filepath)
                                            zf.close()
                                        except Exception:
                                            pass
                                except Exception:
                                    pass

                            elif ext in (".doc", ".xls", ".ppt"):
                                # Old Office binary formats — check OLE encryption
                                try:
                                    if olefile.isOleFile(filepath):
                                        ole = olefile.OleFileIO(filepath)
                                        if ole.exists("EncryptedPackage") or ole.exists("encryption"):
                                            label = {".doc": "Word (legacy)", ".xls": "Excel (legacy)", ".ppt": "PowerPoint (legacy)"}[ext]
                                            protected.append((filepath, label, f"Encrypted {label} document"))
                                        ole.close()
                                except Exception:
                                    pass

                            elif ext in (".odt", ".ods", ".odp"):
                                # ODF files are ZIPs; encrypted ones fail to open as ZIP
                                try:
                                    zf = zipfile.ZipFile(filepath)
                                    # Check for encryption-data.xml (ODF encryption marker)
                                    names = zf.namelist()
                                    if "META-INF/encryption.xml" in names:
                                        label = {".odt": "ODF Text", ".ods": "ODF Spreadsheet", ".odp": "ODF Presentation"}[ext]
                                        protected.append((filepath, label, f"Encrypted {label} document"))
                                    zf.close()
                                except zipfile.BadZipFile:
                                    pass

                            elif ext == ".zip":
                                try:
                                    zf = zipfile.ZipFile(filepath)
                                    for info in zf.infolist():
                                        if info.flag_bits & 0x1:  # encryption bit
                                            protected.append((filepath, "ZIP", "Encrypted ZIP archive — one or more files require a password"))
                                            break
                                    zf.close()
                                except Exception:
                                    pass

                            elif ext == ".7z":
                                try:
                                    import py7zr
                                    with py7zr.SevenZipFile(filepath, mode='r') as z:
                                        if z.needs_password():
                                            protected.append((filepath, "7-Zip", "Encrypted 7z archive — requires a password"))
                                except py7zr.exceptions.PasswordRequired:
                                    protected.append((filepath, "7-Zip", "Encrypted 7z archive — requires a password"))
                                except Exception:
                                    pass

                            elif ext == ".rar":
                                try:
                                    import rarfile
                                    rf = rarfile.RarFile(filepath)
                                    if rf.needs_password():
                                        protected.append((filepath, "RAR", "Encrypted RAR archive — requires a password"))
                                    rf.close()
                                except Exception:
                                    pass

                        except (OSError, PermissionError):
                            pass
            except Exception:
                pass

            results = {
                "folder": folder,
                "recursive": recursive,
                "scanned": scanned,
                "protected": protected,
            }
            self.after(0, self._protected_scan_finished, results)

        def _protected_scan_finished(self, results):
            """Handle protected-file scan completion."""
            try:
                self.progress_bar.stop()
            except Exception:
                pass
            self.progress_bar.grid_remove()
            count = len(results["protected"])
            if count == 0:
                self.status_label.configure(
                    text=f"No password-protected files found ({results['scanned']} file(s) checked).",
                    text_color="blue")
            else:
                self.status_label.configure(
                    text=f"Found {count} password-protected file(s) ({results['scanned']} checked).",
                    text_color="blue")
            self._show_protected_popup(results)

        def _show_protected_popup(self, results):
            """Display the password-protected file scan results."""
            import tkinter as tk
            count = len(results["protected"])

            popup = tk.Toplevel(self)
            popup.title("Password-Protected Files")
            popup.resizable(True, True)
            popup.geometry("800x500")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 800) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 500) // 2
            popup.geometry(f"+{x}+{y}")

            # Header
            header_frame = tk.Frame(popup)
            header_frame.pack(fill="x", padx=10, pady=(10, 2))
            tk.Label(
                header_frame,
                text=f"Password-Protected Files — {count} found",
                font=("TkDefaultFont", 13, "bold"),
            ).pack(side="left", expand=True)

            # Subtitle
            tk.Label(
                popup,
                text=f"Checked {results['scanned']} file(s) in {results['folder']}",
                font=("TkDefaultFont", 10), fg="gray",
            ).pack(pady=(0, 5))

            if count == 0:
                tk.Label(
                    popup,
                    text="\nNo password-protected files were found.\n\n"
                         "All files in this folder can be searched and scanned by peekdocs.",
                    font=("TkDefaultFont", 12), justify="center",
                ).pack(expand=True)
            else:
                # Warning
                tk.Label(
                    popup,
                    text="These files cannot be searched or scanned for sensitive data by peekdocs.\n"
                         "To include them, remove the password protection and search again.",
                    font=("TkDefaultFont", 11), fg="#CC3333", justify="center",
                ).pack(pady=(0, 5))

                # Listbox
                list_frame = tk.Frame(popup)
                list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

                scrollbar = tk.Scrollbar(list_frame)
                scrollbar.pack(side="right", fill="y")

                listbox = tk.Listbox(
                    list_frame, font=("TkDefaultFont", 11),
                    selectmode=tk.SINGLE, activestyle="none",
                    bg="#2b2b2b", fg="white", selectbackground="#1f6aa5",
                    highlightthickness=0, borderwidth=1, relief="sunken",
                    yscrollcommand=scrollbar.set,
                )
                listbox.pack(side="left", fill="both", expand=True)
                scrollbar.config(command=listbox.yview)

                # Group by file type
                from collections import defaultdict
                by_type = defaultdict(list)
                for filepath, ftype, reason in results["protected"]:
                    by_type[ftype].append((filepath, reason))

                for ftype in sorted(by_type.keys()):
                    files = by_type[ftype]
                    listbox.insert("end", f"── {ftype} ({len(files)} file(s)) ──")
                    for filepath, reason in sorted(files, key=lambda x: os.path.basename(x[0]).lower()):
                        listbox.insert("end", f"    {os.path.basename(filepath)}")
                        rel = os.path.relpath(os.path.dirname(filepath), results["folder"])
                        if rel != ".":
                            listbox.insert("end", f"        in {rel}")
                    listbox.insert("end", "")

            # Buttons
            btn_frame = tk.Frame(popup)
            btn_frame.pack(pady=(5, 10))

            if count > 0:
                save_btn = ctk.CTkButton(
                    btn_frame, text="Save Report", width=100,
                    command=lambda: self._save_protected_report(results),
                    font=ctk.CTkFont(size=12),
                )
                save_btn.pack(side="left", padx=5)
                Tooltip(save_btn, "Save this list as a plain text file")

            close_btn = ctk.CTkButton(
                btn_frame, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=popup.destroy,
                font=ctk.CTkFont(size=12),
            )
            close_btn.pack(side="left", padx=5)

        def _save_protected_report(self, results):
            """Save the protected files list as a plain text report."""
            from tkinter import filedialog
            from datetime import datetime

            default_name = f"protected_files_{datetime.now().strftime('%Y-%m-%d')}.txt"
            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")],
                initialfile=default_name,
                title="Save Protected Files Report",
            )
            if not filepath:
                return

            lines = []
            lines.append("=" * 60)
            lines.append("PASSWORD-PROTECTED FILES REPORT")
            lines.append("=" * 60)
            lines.append(f"Folder:      {results['folder']}")
            lines.append(f"Recursive:   {'Yes' if results['recursive'] else 'No'}")
            lines.append(f"Generated:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Files checked: {results['scanned']}")
            lines.append(f"Protected:     {len(results['protected'])}")
            lines.append("")
            lines.append("These files cannot be searched or scanned for sensitive")
            lines.append("data by peekdocs. To include them, remove the password")
            lines.append("protection and search again.")
            lines.append("")
            lines.append("-" * 60)

            from collections import defaultdict
            by_type = defaultdict(list)
            for fpath, ftype, reason in results["protected"]:
                by_type[ftype].append((fpath, reason))

            for ftype in sorted(by_type.keys()):
                files = by_type[ftype]
                lines.append(f"\n{ftype} ({len(files)} file(s))")
                lines.append("-" * 40)
                for fpath, reason in sorted(files, key=lambda x: os.path.basename(x[0]).lower()):
                    lines.append(f"  {os.path.basename(fpath)}")
                    lines.append(f"    Location: {os.path.dirname(fpath)}")
                    lines.append(f"    {reason}")

            lines.append("")
            lines.append("Generated by peekdocs")

            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines) + "\n")
                self.status_label.configure(
                    text=f"Protected files report saved: {os.path.basename(filepath)}",
                    text_color="blue")
            except Exception as e:
                self._show_error(f"Failed to save report: {e}")

        # ── Duplicate File Finder ─────────────────────────────────

        def _run_duplicate_scan(self):
            """Launch a background scan for duplicate files."""
            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a search folder first.")
                return
            recursive = self.recursive_var.get() == "on"
            self.status_label.configure(
                text="Scanning for duplicate files...", text_color="blue")
            self.progress_bar.grid(
                row=7, column=0, columnspan=3, padx=10, pady=(2, 2), sticky="ew")
            self.progress_bar.start()
            import threading
            t = threading.Thread(
                target=self._duplicate_scan_thread,
                args=(folder, recursive), daemon=True)
            t.start()

        def _duplicate_scan_thread(self, folder, recursive):
            """Worker thread: find files with identical content via hashing."""
            import hashlib
            from collections import defaultdict

            # Phase 1: group files by size (fast pre-filter)
            size_groups = defaultdict(list)
            total_files = 0
            try:
                if recursive:
                    walker = os.walk(folder)
                else:
                    try:
                        entries = os.listdir(folder)
                    except PermissionError:
                        entries = []
                    walker = [(folder, [], entries)]

                for root, dirs, files in walker:
                    for fname in files:
                        filepath = os.path.join(root, fname)
                        try:
                            fsize = os.path.getsize(filepath)
                            if fsize == 0:
                                continue  # skip empty files
                            total_files += 1
                            size_groups[fsize].append(filepath)
                        except (OSError, PermissionError):
                            pass
            except Exception:
                pass

            # Phase 2: hash only files that share a size
            hash_groups = defaultdict(list)
            for fsize, paths in size_groups.items():
                if len(paths) < 2:
                    continue
                for filepath in paths:
                    try:
                        h = hashlib.md5()
                        with open(filepath, "rb") as f:
                            while True:
                                chunk = f.read(65536)
                                if not chunk:
                                    break
                                h.update(chunk)
                        hash_groups[h.hexdigest()].append(filepath)
                    except (OSError, PermissionError):
                        pass

            # Keep only groups with 2+ files
            duplicates = []
            wasted = 0
            for digest, paths in hash_groups.items():
                if len(paths) >= 2:
                    fsize = 0
                    try:
                        fsize = os.path.getsize(paths[0])
                    except OSError:
                        pass
                    duplicates.append((paths, fsize))
                    wasted += fsize * (len(paths) - 1)

            # Sort by wasted space descending
            duplicates.sort(key=lambda x: x[1] * (len(x[0]) - 1), reverse=True)

            results = {
                "folder": folder,
                "recursive": recursive,
                "total_files": total_files,
                "groups": duplicates,
                "wasted": wasted,
            }
            self.after(0, self._duplicate_scan_finished, results)

        def _duplicate_scan_finished(self, results):
            """Handle duplicate scan completion."""
            try:
                self.progress_bar.stop()
            except Exception:
                pass
            self.progress_bar.grid_remove()
            groups = results["groups"]
            total_dupes = sum(len(g[0]) - 1 for g in groups)
            if groups:
                self.status_label.configure(
                    text=f"Found {len(groups)} group(s) of duplicates ({total_dupes} extra copies, "
                         f"{self._format_file_size(results['wasted'])} wasted).",
                    text_color="blue")
            else:
                self.status_label.configure(
                    text=f"No duplicate files found ({results['total_files']} file(s) checked).",
                    text_color="blue")
            self._show_duplicate_popup(results)

        def _show_duplicate_popup(self, results):
            """Display the duplicate file scan results."""
            import tkinter as tk
            fmt = self._format_file_size
            groups = results["groups"]
            total_dupes = sum(len(g[0]) - 1 for g in groups)

            popup = tk.Toplevel(self)
            popup.title("Duplicate Files")
            popup.resizable(True, True)
            popup.geometry("820x550")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 820) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 550) // 2
            popup.geometry(f"+{x}+{y}")

            header_frame = tk.Frame(popup)
            header_frame.pack(fill="x", padx=10, pady=(10, 2))
            tk.Label(
                header_frame,
                text=f"Duplicate Files — {len(groups)} group(s), {total_dupes} extra copy(ies)",
                font=("TkDefaultFont", 13, "bold"),
            ).pack(side="left", expand=True)

            tk.Label(
                popup,
                text=f"Checked {results['total_files']} file(s) in {results['folder']}"
                     + (f"  —  {fmt(results['wasted'])} wasted by duplicates" if results['wasted'] else ""),
                font=("TkDefaultFont", 10), fg="gray",
            ).pack(pady=(0, 5))

            if not groups:
                tk.Label(
                    popup,
                    text="\nNo duplicate files were found.\n\nEvery file in this folder is unique.",
                    font=("TkDefaultFont", 12), justify="center",
                ).pack(expand=True)
            else:
                list_frame = tk.Frame(popup)
                list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

                scrollbar = tk.Scrollbar(list_frame)
                scrollbar.pack(side="right", fill="y")

                listbox = tk.Listbox(
                    list_frame, font=("TkDefaultFont", 11),
                    selectmode=tk.SINGLE, activestyle="none",
                    bg="#2b2b2b", fg="white", selectbackground="#1f6aa5",
                    highlightthickness=0, borderwidth=1, relief="sunken",
                    yscrollcommand=scrollbar.set,
                )
                listbox.pack(side="left", fill="both", expand=True)
                scrollbar.config(command=listbox.yview)

                for i, (paths, fsize) in enumerate(groups, 1):
                    listbox.insert("end",
                        f"── Group {i}: {len(paths)} copies, {fmt(fsize)} each ──")
                    for filepath in sorted(paths, key=lambda p: p.lower()):
                        rel = os.path.relpath(filepath, results["folder"])
                        listbox.insert("end", f"    {rel}")
                    listbox.insert("end", "")

            btn_frame = tk.Frame(popup)
            btn_frame.pack(pady=(5, 10))

            if groups:
                save_btn = ctk.CTkButton(
                    btn_frame, text="Save Report", width=100,
                    command=lambda: self._save_duplicate_report(results),
                    font=ctk.CTkFont(size=12),
                )
                save_btn.pack(side="left", padx=5)

            ctk.CTkButton(
                btn_frame, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=popup.destroy, font=ctk.CTkFont(size=12),
            ).pack(side="left", padx=5)

        def _save_duplicate_report(self, results):
            """Save the duplicate files report as plain text."""
            from tkinter import filedialog
            from datetime import datetime
            fmt = self._format_file_size

            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")],
                initialfile=f"duplicate_files_{datetime.now().strftime('%Y-%m-%d')}.txt",
                title="Save Duplicate Files Report",
            )
            if not filepath:
                return

            groups = results["groups"]
            total_dupes = sum(len(g[0]) - 1 for g in groups)
            lines = []
            lines.append("=" * 60)
            lines.append("DUPLICATE FILES REPORT")
            lines.append("=" * 60)
            lines.append(f"Folder:        {results['folder']}")
            lines.append(f"Recursive:     {'Yes' if results['recursive'] else 'No'}")
            lines.append(f"Generated:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Files checked: {results['total_files']}")
            lines.append(f"Duplicate groups: {len(groups)}")
            lines.append(f"Extra copies:  {total_dupes}")
            lines.append(f"Wasted space:  {fmt(results['wasted'])}")
            lines.append("")

            for i, (paths, fsize) in enumerate(groups, 1):
                lines.append(f"Group {i}: {len(paths)} copies, {fmt(fsize)} each")
                lines.append("-" * 40)
                for p in sorted(paths, key=lambda p: p.lower()):
                    lines.append(f"  {os.path.relpath(p, results['folder'])}")
                lines.append("")

            lines.append("Generated by peekdocs")

            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines) + "\n")
                self.status_label.configure(
                    text=f"Duplicate report saved: {os.path.basename(filepath)}",
                    text_color="blue")
            except Exception as e:
                self._show_error(f"Failed to save report: {e}")

        # ── Large File Finder ────────────────────────────────────

        def _run_large_file_scan(self):
            """Find the largest files in the search folder."""
            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a search folder first.")
                return
            recursive = self.recursive_var.get() == "on"
            self.status_label.configure(
                text="Scanning for large files...", text_color="blue")

            import threading
            t = threading.Thread(
                target=self._large_file_thread,
                args=(folder, recursive), daemon=True)
            t.start()

        def _large_file_thread(self, folder, recursive):
            """Worker thread: collect all files sorted by size."""
            import heapq
            top_n = 50  # Show top 50 largest files
            heap = []  # min-heap of (size, filepath)
            total_files = 0
            total_size = 0

            try:
                if recursive:
                    walker = os.walk(folder)
                else:
                    try:
                        entries = os.listdir(folder)
                    except PermissionError:
                        entries = []
                    walker = [(folder, [], entries)]

                for root, dirs, files in walker:
                    for fname in files:
                        filepath = os.path.join(root, fname)
                        try:
                            fsize = os.path.getsize(filepath)
                            total_files += 1
                            total_size += fsize
                            if len(heap) < top_n:
                                heapq.heappush(heap, (fsize, filepath))
                            elif fsize > heap[0][0]:
                                heapq.heapreplace(heap, (fsize, filepath))
                        except (OSError, PermissionError):
                            pass
            except Exception:
                pass

            # Sort largest first
            largest = sorted(heap, key=lambda x: x[0], reverse=True)

            results = {
                "folder": folder,
                "recursive": recursive,
                "total_files": total_files,
                "total_size": total_size,
                "largest": largest,
            }
            self.after(0, self._large_file_finished, results)

        def _large_file_finished(self, results):
            """Handle large file scan completion."""
            self.status_label.configure(
                text=f"Found {len(results['largest'])} largest file(s) out of {results['total_files']}.",
                text_color="blue")
            self._show_large_file_popup(results)

        def _show_large_file_popup(self, results):
            """Display the largest files in a popup."""
            import tkinter as tk
            fmt = self._format_file_size

            popup = tk.Toplevel(self)
            popup.title("Largest Files")
            popup.resizable(True, True)
            popup.geometry("800x500")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 800) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 500) // 2
            popup.geometry(f"+{x}+{y}")

            tk.Label(
                popup,
                text=f"Largest Files — top {len(results['largest'])} of {results['total_files']}",
                font=("TkDefaultFont", 13, "bold"),
            ).pack(pady=(10, 2))

            tk.Label(
                popup,
                text=f"Total folder size: {fmt(results['total_size'])}  —  {results['folder']}",
                font=("TkDefaultFont", 10), fg="gray",
            ).pack(pady=(0, 5))

            list_frame = tk.Frame(popup)
            list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side="right", fill="y")

            listbox = tk.Listbox(
                list_frame, font=("Courier", 11),
                selectmode=tk.SINGLE, activestyle="none",
                bg="#2b2b2b", fg="white", selectbackground="#1f6aa5",
                highlightthickness=0, borderwidth=1, relief="sunken",
                yscrollcommand=scrollbar.set,
            )
            listbox.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=listbox.yview)

            listbox.insert("end", f"{'#':>4}  {'Size':>12}  {'File'}")
            listbox.insert("end", f"{'─' * 4}  {'─' * 12}  {'─' * 50}")

            for i, (fsize, filepath) in enumerate(results["largest"], 1):
                rel = os.path.relpath(filepath, results["folder"])
                listbox.insert("end", f"{i:>4}  {fmt(fsize):>12}  {rel}")

            btn_frame = tk.Frame(popup)
            btn_frame.pack(pady=(5, 10))
            ctk.CTkButton(
                btn_frame, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=popup.destroy, font=ctk.CTkFont(size=12),
            ).pack()

        # ── Empty File Detector ──────────────────────────────────

        def _run_empty_file_scan(self):
            """Find zero-length or blank files in the search folder."""
            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a search folder first.")
                return
            recursive = self.recursive_var.get() == "on"
            self.status_label.configure(
                text="Scanning for empty files...", text_color="blue")

            import threading
            t = threading.Thread(
                target=self._empty_file_thread,
                args=(folder, recursive), daemon=True)
            t.start()

        def _empty_file_thread(self, folder, recursive):
            """Worker thread: find zero-byte files."""
            empty_files = []
            total_files = 0

            try:
                if recursive:
                    walker = os.walk(folder)
                else:
                    try:
                        entries = os.listdir(folder)
                    except PermissionError:
                        entries = []
                    walker = [(folder, [], entries)]

                for root, dirs, files in walker:
                    for fname in files:
                        filepath = os.path.join(root, fname)
                        try:
                            fsize = os.path.getsize(filepath)
                            total_files += 1
                            if fsize == 0:
                                empty_files.append(filepath)
                        except (OSError, PermissionError):
                            pass
            except Exception:
                pass

            results = {
                "folder": folder,
                "recursive": recursive,
                "total_files": total_files,
                "empty": empty_files,
            }
            self.after(0, self._empty_file_finished, results)

        def _empty_file_finished(self, results):
            """Handle empty file scan completion."""
            count = len(results["empty"])
            self.status_label.configure(
                text=f"Found {count} empty file(s) out of {results['total_files']}.",
                text_color="blue")
            self._show_empty_file_popup(results)

        def _show_empty_file_popup(self, results):
            """Display empty files in a popup."""
            import tkinter as tk
            count = len(results["empty"])

            popup = tk.Toplevel(self)
            popup.title("Empty Files")
            popup.resizable(True, True)
            popup.geometry("750x450")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 750) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 450) // 2
            popup.geometry(f"+{x}+{y}")

            tk.Label(
                popup,
                text=f"Empty Files — {count} found",
                font=("TkDefaultFont", 13, "bold"),
            ).pack(pady=(10, 2))

            tk.Label(
                popup,
                text=f"Checked {results['total_files']} file(s) in {results['folder']}",
                font=("TkDefaultFont", 10), fg="gray",
            ).pack(pady=(0, 5))

            if count == 0:
                tk.Label(
                    popup,
                    text="\nNo empty files found.\n\nAll files in this folder contain data.",
                    font=("TkDefaultFont", 12), justify="center",
                ).pack(expand=True)
            else:
                tk.Label(
                    popup,
                    text="These files are zero bytes (completely empty). They may be"
                         " placeholders, failed downloads, or leftover junk.",
                    font=("TkDefaultFont", 11), fg="#CC3333",
                ).pack(pady=(0, 5))

                list_frame = tk.Frame(popup)
                list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

                scrollbar = tk.Scrollbar(list_frame)
                scrollbar.pack(side="right", fill="y")

                listbox = tk.Listbox(
                    list_frame, font=("TkDefaultFont", 11),
                    selectmode=tk.SINGLE, activestyle="none",
                    bg="#2b2b2b", fg="white", selectbackground="#1f6aa5",
                    highlightthickness=0, borderwidth=1, relief="sunken",
                    yscrollcommand=scrollbar.set,
                )
                listbox.pack(side="left", fill="both", expand=True)
                scrollbar.config(command=listbox.yview)

                for filepath in sorted(results["empty"], key=lambda p: p.lower()):
                    rel = os.path.relpath(filepath, results["folder"])
                    listbox.insert("end", f"  {rel}")

            btn_frame = tk.Frame(popup)
            btn_frame.pack(pady=(5, 10))
            ctk.CTkButton(
                btn_frame, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=popup.destroy, font=ctk.CTkFont(size=12),
            ).pack()

        # ── Recent Changes Dashboard ─────────────────────────────

        def _run_recent_changes(self):
            """Show files modified recently in the search folder."""
            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a search folder first.")
                return
            recursive = self.recursive_var.get() == "on"
            self.status_label.configure(
                text="Scanning for recently modified files...", text_color="blue")

            import threading
            t = threading.Thread(
                target=self._recent_changes_thread,
                args=(folder, recursive), daemon=True)
            t.start()

        def _recent_changes_thread(self, folder, recursive):
            """Worker thread: collect files and their modification times."""
            from datetime import datetime, timedelta
            import time

            now = time.time()
            cutoffs = {
                "7 days": now - 7 * 86400,
                "30 days": now - 30 * 86400,
                "90 days": now - 90 * 86400,
            }
            buckets = {"7 days": [], "30 days": [], "90 days": [], "older": []}
            total_files = 0

            try:
                if recursive:
                    walker = os.walk(folder)
                else:
                    try:
                        entries = os.listdir(folder)
                    except PermissionError:
                        entries = []
                    walker = [(folder, [], entries)]

                for root, dirs, files in walker:
                    for fname in files:
                        filepath = os.path.join(root, fname)
                        try:
                            mtime = os.path.getmtime(filepath)
                            fsize = os.path.getsize(filepath)
                            total_files += 1
                            entry = (filepath, mtime, fsize)
                            if mtime >= cutoffs["7 days"]:
                                buckets["7 days"].append(entry)
                            elif mtime >= cutoffs["30 days"]:
                                buckets["30 days"].append(entry)
                            elif mtime >= cutoffs["90 days"]:
                                buckets["90 days"].append(entry)
                            else:
                                buckets["older"].append(entry)
                        except (OSError, PermissionError):
                            pass
            except Exception:
                pass

            # Sort each bucket by mtime descending (most recent first)
            for key in buckets:
                buckets[key].sort(key=lambda x: x[1], reverse=True)

            results = {
                "folder": folder,
                "recursive": recursive,
                "total_files": total_files,
                "buckets": buckets,
            }
            self.after(0, self._recent_changes_finished, results)

        def _recent_changes_finished(self, results):
            """Handle recent changes scan completion."""
            b = results["buckets"]
            recent = len(b["7 days"]) + len(b["30 days"]) + len(b["90 days"])
            self.status_label.configure(
                text=f"{recent} file(s) modified in the last 90 days ({results['total_files']} total).",
                text_color="blue")
            self._show_recent_changes_popup(results)

        def _show_recent_changes_popup(self, results):
            """Display recently modified files grouped by time period."""
            import tkinter as tk
            from datetime import datetime
            fmt = self._format_file_size
            b = results["buckets"]

            popup = tk.Toplevel(self)
            popup.title("Recent Changes")
            popup.resizable(True, True)
            popup.geometry("820x550")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 820) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 550) // 2
            popup.geometry(f"+{x}+{y}")

            recent = len(b["7 days"]) + len(b["30 days"]) + len(b["90 days"])
            tk.Label(
                popup,
                text=f"Recent Changes — {recent} file(s) modified in the last 90 days",
                font=("TkDefaultFont", 13, "bold"),
            ).pack(pady=(10, 2))

            tk.Label(
                popup,
                text=f"{results['total_files']} total file(s) in {results['folder']}",
                font=("TkDefaultFont", 10), fg="gray",
            ).pack(pady=(0, 5))

            list_frame = tk.Frame(popup)
            list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side="right", fill="y")

            listbox = tk.Listbox(
                list_frame, font=("TkDefaultFont", 11),
                selectmode=tk.SINGLE, activestyle="none",
                bg="#2b2b2b", fg="white", selectbackground="#1f6aa5",
                highlightthickness=0, borderwidth=1, relief="sunken",
                yscrollcommand=scrollbar.set,
            )
            listbox.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=listbox.yview)

            for period in ["7 days", "30 days", "90 days"]:
                files = b[period]
                listbox.insert("end",
                    f"── Last {period} ({len(files)} file(s)) ──")
                if not files:
                    listbox.insert("end", "    (none)")
                for filepath, mtime, fsize in files:
                    date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                    rel = os.path.relpath(filepath, results["folder"])
                    listbox.insert("end", f"    {date_str}  {fmt(fsize):>10}  {rel}")
                listbox.insert("end", "")

            older_count = len(b["older"])
            listbox.insert("end", f"── Older than 90 days ({older_count} file(s)) ──")

            btn_frame = tk.Frame(popup)
            btn_frame.pack(pady=(5, 10))
            ctk.CTkButton(
                btn_frame, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=popup.destroy, font=ctk.CTkFont(size=12),
            ).pack()

        # ── Search History ───────────────────────────────────────

        def _log_search_history(self, search_text, match_count, file_count, elapsed):
            """Append a search entry to the history file."""
            from datetime import datetime
            folder = self.folder_entry.get().strip()
            history_path = os.path.join(os.path.expanduser("~"), ".peekdocs_history.json")
            try:
                import json
                history = []
                if os.path.exists(history_path):
                    with open(history_path, "r", encoding="utf-8") as f:
                        history = json.load(f)
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "search_text": search_text,
                    "folder": folder,
                    "matches": match_count,
                    "files": file_count,
                    "elapsed": elapsed,
                }
                history.append(entry)
                # Keep last 200 entries
                history = history[-200:]
                with open(history_path, "w", encoding="utf-8") as f:
                    json.dump(history, f, indent=2)
            except Exception:
                pass

        def _show_search_history(self):
            """Display the search history log."""
            import tkinter as tk

            history_path = os.path.join(os.path.expanduser("~"), ".peekdocs_history.json")
            history = []
            if os.path.exists(history_path):
                try:
                    import json
                    with open(history_path, "r", encoding="utf-8") as f:
                        history = json.load(f)
                except Exception:
                    pass

            popup = tk.Toplevel(self)
            popup.title("Search History")
            popup.resizable(True, True)
            popup.geometry("850x500")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 850) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 500) // 2
            popup.geometry(f"+{x}+{y}")

            tk.Label(
                popup,
                text=f"Search History — {len(history)} search(es)",
                font=("TkDefaultFont", 13, "bold"),
            ).pack(pady=(10, 2))

            tk.Label(
                popup,
                text="Your past searches with results — most recent first",
                font=("TkDefaultFont", 10), fg="gray",
            ).pack(pady=(0, 5))

            if not history:
                tk.Label(
                    popup,
                    text="\nNo search history yet.\n\nRun a search and it will be logged here automatically.",
                    font=("TkDefaultFont", 12), justify="center",
                ).pack(expand=True)
            else:
                list_frame = tk.Frame(popup)
                list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

                scrollbar = tk.Scrollbar(list_frame)
                scrollbar.pack(side="right", fill="y")

                listbox = tk.Listbox(
                    list_frame, font=("Courier", 11),
                    selectmode=tk.SINGLE, activestyle="none",
                    bg="#2b2b2b", fg="white", selectbackground="#1f6aa5",
                    highlightthickness=0, borderwidth=1, relief="sunken",
                    yscrollcommand=scrollbar.set,
                )
                listbox.pack(side="left", fill="both", expand=True)
                scrollbar.config(command=listbox.yview)

                listbox.insert("end", f"{'Date':>19}  {'Matches':>8}  {'Files':>6}  {'Time':>6}  Search Terms")
                listbox.insert("end", f"{'─' * 19}  {'─' * 8}  {'─' * 6}  {'─' * 6}  {'─' * 30}")

                for entry in reversed(history):
                    ts = entry.get("timestamp", "")[:19].replace("T", " ")
                    matches = entry.get("matches", "?")
                    files = entry.get("files", "?")
                    elapsed = entry.get("elapsed", "")
                    elapsed_str = f"{float(elapsed):.1f}s" if elapsed else "—"
                    terms = entry.get("search_text", "")
                    if len(terms) > 40:
                        terms = terms[:37] + "..."
                    listbox.insert("end", f"{ts}  {matches:>8}  {files:>6}  {elapsed_str:>6}  {terms}")

            btn_frame = tk.Frame(popup)
            btn_frame.pack(pady=(5, 10))

            if history:
                clear_btn = ctk.CTkButton(
                    btn_frame, text="Clear History", width=100,
                    fg_color="#CC3333", hover_color="#AA2222",
                    command=lambda: self._clear_search_history(popup),
                    font=ctk.CTkFont(size=12),
                )
                clear_btn.pack(side="left", padx=5)

            ctk.CTkButton(
                btn_frame, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=popup.destroy, font=ctk.CTkFont(size=12),
            ).pack(side="left", padx=5)

        def _clear_search_history(self, popup):
            """Clear all search history after confirmation."""
            from tkinter import messagebox
            if messagebox.askyesno("Clear History",
                                   "Delete all search history? This cannot be undone.",
                                   parent=popup):
                history_path = os.path.join(os.path.expanduser("~"), ".peekdocs_history.json")
                try:
                    if os.path.exists(history_path):
                        os.remove(history_path)
                except Exception:
                    pass
                popup.destroy()
                self.status_label.configure(
                    text="Search history cleared.", text_color="blue")

        # ── Bookmarks ────────────────────────────────────────────

        def _get_bookmarks_path(self):
            """Return the path to the bookmarks file."""
            return os.path.join(os.path.expanduser("~"), ".peekdocs_bookmarks.json")

        def _load_bookmarks(self):
            """Load bookmarks from disk."""
            import json
            path = self._get_bookmarks_path()
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
            return []

        def _save_bookmarks_list(self, bookmarks):
            """Save bookmarks to disk."""
            import json
            path = self._get_bookmarks_path()
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(bookmarks, f, indent=2)
            except Exception:
                pass

        def add_bookmark(self, filepath, note=""):
            """Add a file to bookmarks."""
            from datetime import datetime
            bookmarks = self._load_bookmarks()
            # Don't add duplicates
            for bm in bookmarks:
                if bm.get("filepath") == filepath:
                    self.status_label.configure(
                        text=f"Already bookmarked: {os.path.basename(filepath)}",
                        text_color="blue")
                    return
            bookmarks.append({
                "filepath": filepath,
                "filename": os.path.basename(filepath),
                "note": note,
                "added": datetime.now().isoformat(),
            })
            self._save_bookmarks_list(bookmarks)
            self.status_label.configure(
                text=f"Bookmarked: {os.path.basename(filepath)}",
                text_color="blue")

        def _show_bookmarks(self):
            """Display bookmarked files."""
            import tkinter as tk

            bookmarks = self._load_bookmarks()

            popup = tk.Toplevel(self)
            popup.title("Bookmarks")
            popup.resizable(True, True)
            popup.geometry("800x480")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 800) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 480) // 2
            popup.geometry(f"+{x}+{y}")

            tk.Label(
                popup,
                text=f"Bookmarks — {len(bookmarks)} file(s)",
                font=("TkDefaultFont", 13, "bold"),
            ).pack(pady=(10, 2))

            tk.Label(
                popup,
                text="Double-click a file to open it. Use the Matched Files popup to add bookmarks.",
                font=("TkDefaultFont", 10), fg="gray",
            ).pack(pady=(0, 5))

            if not bookmarks:
                tk.Label(
                    popup,
                    text="\nNo bookmarks yet.\n\nIn the Matched Files popup after a search,\n"
                         "right-click a file and choose 'Add Bookmark' to pin it here.",
                    font=("TkDefaultFont", 12), justify="center",
                ).pack(expand=True)
            else:
                list_frame = tk.Frame(popup)
                list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

                scrollbar = tk.Scrollbar(list_frame)
                scrollbar.pack(side="right", fill="y")

                listbox = tk.Listbox(
                    list_frame, font=("TkDefaultFont", 11),
                    selectmode=tk.SINGLE, activestyle="none",
                    bg="#2b2b2b", fg="white", selectbackground="#1f6aa5",
                    highlightthickness=0, borderwidth=1, relief="sunken",
                    yscrollcommand=scrollbar.set,
                )
                listbox.pack(side="left", fill="both", expand=True)
                scrollbar.config(command=listbox.yview)

                _bm_paths = []
                for bm in bookmarks:
                    fp = bm.get("filepath", "")
                    fname = bm.get("filename", os.path.basename(fp))
                    added = bm.get("added", "")[:10]
                    note = bm.get("note", "")
                    exists = os.path.exists(fp)
                    marker = "" if exists else " [MISSING]"
                    line = f"  {fname}{marker}"
                    if note:
                        line += f"  — {note}"
                    line += f"  ({added})"
                    listbox.insert("end", line)
                    _bm_paths.append(fp)

                def _on_double_click(event):
                    sel = listbox.curselection()
                    if not sel:
                        return
                    fp = _bm_paths[sel[0]]
                    if os.path.exists(fp):
                        import subprocess, sys
                        if sys.platform == "darwin":
                            subprocess.Popen(["open", fp])
                        elif sys.platform == "win32":
                            os.startfile(fp)
                        else:
                            subprocess.Popen(["xdg-open", fp])

                listbox.bind("<Double-1>", _on_double_click)

                def _remove_selected():
                    sel = listbox.curselection()
                    if not sel:
                        return
                    idx = sel[0]
                    bookmarks.pop(idx)
                    self._save_bookmarks_list(bookmarks)
                    listbox.delete(idx)
                    _bm_paths.pop(idx)

                # Right-click context menu
                ctx_menu = tk.Menu(popup, tearoff=0)
                ctx_menu.add_command(label="Remove Bookmark", command=_remove_selected)

                def _show_ctx(event):
                    idx = listbox.nearest(event.y)
                    if idx >= 0:
                        listbox.selection_clear(0, "end")
                        listbox.selection_set(idx)
                    ctx_menu.tk_popup(event.x_root, event.y_root)

                listbox.bind("<Button-3>", _show_ctx)
                if sys.platform == "darwin":
                    listbox.bind("<Button-2>", _show_ctx)

            btn_frame = tk.Frame(popup)
            btn_frame.pack(pady=(5, 10))

            if bookmarks:
                remove_btn = ctk.CTkButton(
                    btn_frame, text="Remove Selected", width=120,
                    fg_color="#CC3333", hover_color="#AA2222",
                    command=lambda: _remove_selected() if bookmarks else None,
                    font=ctk.CTkFont(size=12),
                )
                remove_btn.pack(side="left", padx=5)

            ctk.CTkButton(
                btn_frame, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=popup.destroy, font=ctk.CTkFont(size=12),
            ).pack(side="left", padx=5)

        def _show_app_files(self):
            """List all peekdocs-created files in the search folder and subfolders."""
            import tkinter as tk
            folder = self.folder_entry.get().strip()
            if not folder or not os.path.isdir(folder):
                self._show_error("Please select a search folder first.")
                return

            # Categorize peekdocs-generated files
            app_files = []  # list of (filepath, category)
            _INTERNAL_NAMES = {
                ".peekdocs.db", ".peekdocs.db-wal", ".peekdocs.db-shm",
                ".peekdocs_collection.json", "peekdocs_errors.log",
            }

            for root, dirs, files in os.walk(folder):
                for fname in files:
                    filepath = os.path.join(root, fname)

                    if fname.startswith("peekdocs_results"):
                        app_files.append((filepath, "Search results"))
                    elif fname.startswith("DO_NOT_SEARCH_pii_scan_report"):
                        app_files.append((filepath, "PII scan reports"))
                    elif fname.startswith("DO_NOT_SEARCH_ACCUMULATED"):
                        app_files.append((filepath, "Accumulated results"))
                    elif fname.startswith("DO_NOT_SEARCH"):
                        app_files.append((filepath, "peekdocs reports"))
                    elif fname == "peekdocs_errors.log":
                        app_files.append((filepath, "Error log"))
                    elif fname == ".peekdocs.db":
                        app_files.append((filepath, "Search index"))
                    elif fname in (".peekdocs.db-wal", ".peekdocs.db-shm"):
                        app_files.append((filepath, "Index temp files"))
                    elif fname == ".peekdocs_collection.json":
                        app_files.append((filepath, "Saved searches \u2014 DO NOT DELETE"))

            # Also check home directory for .peekdocsrc
            rc_path = os.path.expanduser("~/.peekdocsrc")
            if os.path.exists(rc_path):
                app_files.append((rc_path, "Settings \u2014 DO NOT DELETE"))

            if not app_files:
                self.status_label.configure(
                    text="No peekdocs files found in this folder.",
                    text_color="blue",
                )
                return

            popup = tk.Toplevel(self)
            popup.title(f"peekdocs App Files ({len(app_files)})")
            popup.resizable(True, True)
            popup.geometry("1000x500")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 1000) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 500) // 2
            popup.geometry(f"+{x}+{y}")

            tk.Label(
                popup, text=f"peekdocs Files ({len(app_files)} file(s) in {folder})",
                font=("TkDefaultFont", 13, "bold"),
            ).pack(pady=(10, 2))
            tk.Label(
                popup, text="Files created by peekdocs in this folder and subfolders. "
                            "Items marked DO NOT DELETE contain your saved work. "
                            ".peekdocs_collection.json holds all saved searches for that "
                            "folder \u2014 back it up before major changes.",
                font=("TkDefaultFont", 11), fg="gray", wraplength=960, justify="left",
            ).pack(pady=(0, 8), padx=15)

            list_frame = tk.Frame(popup)
            list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side="right", fill="y")

            listbox = tk.Listbox(
                list_frame, font=("TkDefaultFont", 11),
                selectmode=tk.SINGLE, activestyle="none",
                bg="#2b2b2b", fg="white", selectbackground="#1f6aa5",
                highlightthickness=0, borderwidth=1, relief="sunken",
                yscrollcommand=scrollbar.set,
            )
            listbox.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=listbox.yview)

            # Group by category
            from collections import defaultdict
            by_category = defaultdict(list)
            for display, category in app_files:
                by_category[category].append(display)

            _CATEGORY_DESCRIPTIONS = {
                "Saved searches \u2014 DO NOT DELETE":
                    "    These .peekdocs_collection.json files store your saved searches.\n"
                    "    One per folder. Back these up \u2014 they represent all your saved\n"
                    "    search configurations.",
                "Settings \u2014 DO NOT DELETE":
                    "    Your ~/.peekdocsrc file stores your Advanced Search Options\n"
                    "    settings and other saved defaults.\n"
                    "    Back this up \u2014 it contains your personalized configuration.",
                "Search index":
                    "    SQLite database storing extracted text for faster repeated searches.\n"
                    "    Safe to delete \u2014 rebuild anytime with Build Index(es).",
                "Search results":
                    "    Output files from previous searches. Safe to delete.",
                "PII scan reports":
                    "    Reports generated by the PII Scan feature. Safe to delete.",
                "Error log":
                    "    Log of files that could not be read. Safe to delete.",
            }

            for category in sorted(by_category.keys()):
                files = by_category[category]
                idx = listbox.size()
                listbox.insert("end", f"\u2500\u2500 {category} ({len(files)} file(s)) \u2500\u2500")
                listbox.itemconfig(idx, fg="#FFD700")
                desc = _CATEGORY_DESCRIPTIONS.get(category)
                if desc:
                    for desc_line in desc.split("\n"):
                        desc_idx = listbox.size()
                        listbox.insert("end", desc_line)
                        listbox.itemconfig(desc_idx, fg="#FFD700")
                for fp in sorted(files):
                    listbox.insert("end", f"    {fp}")
                listbox.insert("end", "")

            tk.Button(popup, text="Close", width=10, command=popup.destroy).pack(pady=(5, 10))

        def _show_all_collections(self):
            """Scan home directory for all .peekdocs_collection.json files and display a summary."""
            import tkinter as tk
            from collections import defaultdict
            from peekdocs.collection import COLLECTION_FILENAME, load_collection

            home = os.path.expanduser("~")
            self.status_label.configure(text="Scanning for saved collections…", text_color="blue")
            self.update_idletasks()

            # Walk home directory to find all collection files
            collections = []  # list of (folder_path, n_searches, search_names)
            try:
                for root, dirs, files in os.walk(home):
                    # Skip hidden dirs (except those containing collection files),
                    # common large dirs, and virtual environments
                    dirs[:] = [
                        d for d in dirs
                        if not d.startswith(".")
                        and d not in ("node_modules", "__pycache__", "venv", ".venv",
                                      "Library", "Applications", "AppData")
                    ]
                    if COLLECTION_FILENAME in files:
                        folder = root
                        data = load_collection(folder)
                        searches = sorted(data.get("saved_searches", {}).keys())
                        if searches:
                            collections.append((folder, len(searches), searches))
            except (OSError, PermissionError):
                pass

            if not collections:
                self.status_label.configure(
                    text="No saved collections found.",
                    text_color="blue",
                )
                self._show_simple_popup(
                    title="All Collections",
                    heading="No Saved Collections Found",
                    message=(
                        "No .peekdocs_collection.json files were found under your home directory.\n\n"
                        "Collections are created the first time you click Save on the main screen. "
                        "Each folder gets its own collection of saved searches."
                    ),
                )
                return

            self.status_label.configure(
                text=f"Found {len(collections)} collection(s).",
                text_color="blue",
            )

            popup = tk.Toplevel(self)
            popup.title(f"All Saved Collections ({len(collections)} folder(s))")
            popup.resizable(True, True)
            popup.geometry("1050x550")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 1050) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 550) // 2
            popup.geometry(f"+{x}+{y}")

            total_searches = sum(c[1] for c in collections)
            tk.Label(
                popup,
                text=f"Saved Collections — {len(collections)} folder(s), "
                     f"{total_searches} search(es)",
                font=("TkDefaultFont", 13, "bold"),
            ).pack(pady=(10, 2))
            tk.Label(
                popup,
                text="All .peekdocs_collection.json files found under your home directory. "
                     "Double-click a folder path to switch to it.",
                font=("TkDefaultFont", 11), fg="gray",
            ).pack(pady=(0, 8))

            list_frame = tk.Frame(popup)
            list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side="right", fill="y")

            listbox = tk.Listbox(
                list_frame, font=("TkDefaultFont", 11),
                selectmode=tk.SINGLE, activestyle="none",
                bg="#2b2b2b", fg="white", selectbackground="#1f6aa5",
                highlightthickness=0, borderwidth=1, relief="sunken",
                yscrollcommand=scrollbar.set,
            )
            listbox.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=listbox.yview)

            # Track which folder each listbox index belongs to (for double-click-to-switch)
            folder_indices = {}  # index -> folder_path

            for folder, n_searches, searches in sorted(collections, key=lambda c: c[0]):
                idx = listbox.size()
                listbox.insert("end", f"\u2500\u2500 {folder} \u2500\u2500")
                listbox.itemconfig(idx, fg="#FFD700")
                folder_indices[idx] = folder

                summary = f"    {n_searches} saved search(es)"
                idx = listbox.size()
                listbox.insert("end", summary)
                folder_indices[idx] = folder

                for s in searches:
                    idx = listbox.size()
                    listbox.insert("end", f"        {s}")
                    folder_indices[idx] = folder
                listbox.insert("end", "")

            def _on_double_click(event):
                sel = listbox.curselection()
                if not sel:
                    return
                idx = sel[0]
                if idx in folder_indices:
                    folder = folder_indices[idx]
                    self.folder_entry.delete(0, "end")
                    self.folder_entry.insert(0, folder)
                    self._refresh_load_search_menu()
                    self.status_label.configure(
                        text=f"Switched to: {folder}",
                        text_color="blue",
                    )
                    popup.destroy()

            listbox.bind("<Double-1>", _on_double_click)

            ctk.CTkButton(
                popup, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=popup.destroy, font=ctk.CTkFont(size=12),
            ).pack(pady=(5, 10))

        def _show_excluded_files_popup(self):
            """Show a popup listing files excluded from the search with reasons."""
            import tkinter as tk
            if not self._excluded_files:
                return
            popup = tk.Toplevel(self)
            popup.title(f"Excluded Files ({len(self._excluded_files)})")
            popup.resizable(True, True)
            popup.geometry("800x500")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 800) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 500) // 2
            popup.geometry(f"+{x}+{y}")

            header_frame = tk.Frame(popup)
            header_frame.pack(fill="x", padx=10, pady=(10, 2))
            tk.Label(
                header_frame, text=f"Files Excluded from Search ({len(self._excluded_files)})",
                font=("TkDefaultFont", 13, "bold"),
            ).pack(side="left", expand=True)
            help_btn = ctk.CTkButton(
                header_frame, text="?", width=30, height=26,
                font=ctk.CTkFont(size=14, weight="bold"),
                command=lambda: self._show_excluded_files_help(popup),
            )
            help_btn.pack(side="right")
            tk.Label(
                popup, text="These files were in your search folder but were not searched. "
                            "Each is shown with the reason why.",
                font=("TkDefaultFont", 11), fg="gray",
            ).pack(pady=(0, 8))

            list_frame = tk.Frame(popup)
            list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side="right", fill="y")

            listbox = tk.Listbox(
                list_frame, font=("TkDefaultFont", 11),
                selectmode=tk.SINGLE, activestyle="none",
                bg="#2b2b2b", fg="white", selectbackground="#1f6aa5",
                highlightthickness=0, borderwidth=1, relief="sunken",
                yscrollcommand=scrollbar.set,
            )
            listbox.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=listbox.yview)

            # Group by reason for easier scanning
            from collections import defaultdict
            by_reason = defaultdict(list)
            for filepath, reason in self._excluded_files:
                by_reason[reason].append(filepath)

            for reason in sorted(by_reason.keys()):
                files = by_reason[reason]
                listbox.insert("end", f"── {reason} ({len(files)} file(s)) ──")
                for fp in sorted(files):
                    listbox.insert("end", f"    {os.path.basename(fp)}")
                listbox.insert("end", "")

            tk.Button(popup, text="Close", width=10, command=popup.destroy).pack(pady=(5, 10))

        def _show_excluded_files_help(self, parent):
            """Show help for the Excluded Files popup."""
            import tkinter as tk
            help_win = tk.Toplevel(parent)
            help_win.title("Excluded Files \u2014 Help")
            help_win.geometry("720x680")
            help_win.resizable(True, True)
            help_win.transient(parent)
            try:
                help_win.grab_set()
            except Exception:
                help_win.after(150, lambda: help_win.grab_set() if help_win.winfo_exists() else None)

            txt_frame = tk.Frame(help_win)
            txt_frame.pack(fill="both", expand=True, padx=10, pady=10)
            scrollbar = tk.Scrollbar(txt_frame)
            scrollbar.pack(side="right", fill="y")
            txt = tk.Text(
                txt_frame, wrap="word", font=("TkDefaultFont", 12),
                yscrollcommand=scrollbar.set, padx=10, pady=10,
                borderwidth=1, relief="sunken",
            )
            txt.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=txt.yview)

            txt.tag_configure("heading", font=("TkDefaultFont", 13, "bold"), spacing1=8, spacing3=4)
            txt.tag_configure("body", font=("TkDefaultFont", 12), lmargin1=10, lmargin2=10, spacing3=2)
            txt.tag_configure("example", font=("Courier", 11), lmargin1=20, lmargin2=20, spacing3=2)
            txt.tag_configure("toc_title", font=("TkDefaultFont", 14, "bold"), spacing1=5, spacing3=8)
            txt.tag_configure("toc_item", font=("TkDefaultFont", 11), lmargin1=20, lmargin2=20,
                              foreground="gray40")

            def h(s): txt.insert("end", s + "\n", "heading")
            def b(s): txt.insert("end", s + "\n", "body")
            def e(s): txt.insert("end", s + "\n", "example")
            def blank(): txt.insert("end", "\n")

            txt.insert("end", "TABLE OF CONTENTS\n", "toc_title")
            for section in [
                "What This Popup Shows",
                "Why Files Get Excluded",
                "How the List Is Organized",
                "What to Do About Excluded Files",
                "Why This Matters",
            ]:
                txt.insert("end", f"\u2022 {section}\n", "toc_item")
            txt.insert("end", "\n")

            h("WHAT THIS POPUP SHOWS")
            b("You opened this popup by clicking the gray Excluded Files")
            b("button on the status line at the bottom of the main window.")
            b("It lists every file that was in your search folder but was")
            b("NOT searched, grouped by the reason it was skipped.")
            blank()
            b("This answers the question: \"Why did peekdocs report fewer")
            b("files searched than my file manager shows in the folder?\"")
            b("If you expected 200 files and only 180 were searched, this")
            b("popup tells you exactly which 20 were skipped and why.")
            blank()

            h("WHY FILES GET EXCLUDED")
            b("Files are excluded for several reasons:")
            blank()
            b("\u2022 Unsupported type \u2014 the file extension is not in peekdocs's")
            b("  list of 46 searchable formats (e.g., .exe, .dll, .dmg,")
            b("  .iso, .mp3, .mp4, .psd). peekdocs is a document search")
            b("  tool, not a binary/media scanner")
            b("\u2022 Prior peekdocs output \u2014 files peekdocs created itself,")
            b("  such as DO_NOT_SEARCH_*.docx reports, index databases,")
            b("  and collection files. Searching these would produce")
            b("  circular matches and pollute your results")
            b("\u2022 Oversized \u2014 files larger than your Max File Size setting")
            b("  (100 MB by default). Very large files can take minutes")
            b("  to parse and may exhaust memory. Raise the limit in")
            b("  Advanced Search Options, or set it to 0 for no limit")
            b("\u2022 Hidden \u2014 files whose names start with a dot (.DS_Store,")
            b("  .git, .venv). These are system/config files you usually")
            b("  do not want included")
            b("\u2022 Symlink \u2014 symbolic links to files outside your search")
            b("  folder, skipped to avoid searching the same file twice")
            b("\u2022 Permission denied \u2014 peekdocs does not have read")
            b("  access to the file (common on macOS for files in")
            b("  protected folders like ~/Documents without Full Disk")
            b("  Access granted)")
            b("\u2022 Archive too large \u2014 ZIP/7z/RAR files that would")
            b("  expand to more than 500 MB are skipped to prevent")
            b("  archive bombs")
            blank()

            h("HOW THE LIST IS ORGANIZED")
            b("Excluded files are grouped by reason, with a header line")
            b("showing the reason and the count in that group:")
            blank()
            e("  \u2500\u2500 Unsupported type (12 file(s)) \u2500\u2500")
            e("      photo1.jpg")
            e("      photo2.jpg")
            e("      ...")
            e("")
            e("  \u2500\u2500 Prior peekdocs output (3 file(s)) \u2500\u2500")
            e("      DO_NOT_SEARCH_results.docx")
            e("      ...")
            blank()
            b("Groups are sorted alphabetically by reason, and files")
            b("within each group are sorted alphabetically by name.")
            blank()

            h("WHAT TO DO ABOUT EXCLUDED FILES")
            b("Most exclusions are intentional and you don't need to do")
            b("anything. But here are the cases where you may want to act:")
            blank()
            b("\u2022 Unsupported type \u2014 if a format you care about is")
            b("  missing, check the Supported File Types table in the")
            b("  User Guide. If the format is genuinely unsupported,")
            b("  consider converting the file (for example, export a")
            b("  .numbers spreadsheet to .xlsx)")
            b("\u2022 Oversized \u2014 if a real document is being skipped for")
            b("  size, open Advanced Search Options, raise the Max File")
            b("  Size (MB) value, and search again. The index will")
            b("  rebuild automatically on the next search")
            b("\u2022 Permission denied (macOS) \u2014 open System Settings >")
            b("  Privacy & Security > Full Disk Access and grant access")
            b("  to your terminal application (Terminal.app, iTerm, etc.)")
            b("\u2022 Prior peekdocs output \u2014 leave these alone. They are")
            b("  supposed to be excluded")
            blank()

            h("WHY THIS MATTERS")
            b("If you ever wondered \"did peekdocs actually look at every")
            b("file in my folder?\", this popup is the answer. Every file")
            b("in your folder is either in the Matched Files popup, in")
            b("this Excluded Files popup, or in the search results with")
            b("zero matches \u2014 nothing falls through the cracks.")
            blank()

            txt.configure(state="disabled")

            close_btn = ctk.CTkButton(
                help_win, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=help_win.destroy,
                font=ctk.CTkFont(size=12),
            )
            close_btn.pack(pady=(5, 10))

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
            win_h = max(320, min(650, count * 28 + 180))
            popup.geometry(f"500x{win_h}")
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 500) // 2
            y = self.winfo_rooty() + (self.winfo_height() - win_h) // 2
            popup.geometry(f"+{x}+{y}")

            header_frame = tk.Frame(popup)
            header_frame.pack(fill="x", padx=10, pady=(10, 2))
            tk.Label(
                header_frame, text=heading,
                font=("TkDefaultFont", 13, "bold"),
            ).pack(side="left", expand=True)
            help_btn = ctk.CTkButton(
                header_frame, text="?", width=30, height=26,
                font=ctk.CTkFont(size=14, weight="bold"),
                command=lambda: self._show_matched_files_help(popup),
            )
            help_btn.pack(side="right")
            tk.Label(
                popup, text="Double-click a file to open it",
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

            for item in self.matched_files:
                filepath, filename, match_count = item[0], item[1], item[2]
                line_nums = item[3] if len(item) > 3 else []
                label = f"{filename} ({match_count} match{'es' if match_count != 1 else ''}"
                if line_nums:
                    # Show up to 10 line numbers, then ellipsis
                    shown = line_nums[:10]
                    lines_str = ", ".join(str(n) for n in shown)
                    if len(line_nums) > 10:
                        lines_str += ", ..."
                    label += f" — lines {lines_str}"
                label += ")"
                listbox.insert("end", label)

            def _on_click(event):
                selection = listbox.curselection()
                if not selection:
                    return
                filepath = self.matched_files[selection[0]][0]
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

            # Right-click context menu with Bookmark option
            _ctx = tk.Menu(popup, tearoff=0)

            def _bookmark_selected():
                sel = listbox.curselection()
                if not sel:
                    return
                fp = self.matched_files[sel[0]][0]
                self.add_bookmark(fp)

            _ctx.add_command(label="Add Bookmark", command=_bookmark_selected)

            def _show_ctx(event):
                idx = listbox.nearest(event.y)
                if idx >= 0:
                    listbox.selection_clear(0, "end")
                    listbox.selection_set(idx)
                _ctx.tk_popup(event.x_root, event.y_root)

            listbox.bind("<Button-3>", _show_ctx)
            if sys.platform == "darwin":
                listbox.bind("<Button-2>", _show_ctx)

            def _view_text():
                selection = listbox.curselection()
                if not selection:
                    return
                filepath, filename = self.matched_files[selection[0]][0], self.matched_files[selection[0]][1]
                if not os.path.exists(filepath):
                    self._show_error(f"File not found: {filepath}")
                    return
                self._show_file_text_view(filepath, filename)

            btn_frame = tk.Frame(popup)
            btn_frame.pack(pady=(5, 10))

            view_btn = tk.Label(
                btn_frame, text="View Text (with line numbers)",
                font=("TkDefaultFont", 13, "bold"),
                bg="#FF6B35", fg="white",
                relief="raised", borderwidth=2,
                padx=20, pady=8, cursor="hand2",
            )
            view_btn.pack(side="left", padx=5)
            view_btn.bind("<Button-1>", lambda e: _view_text())
            view_btn.bind("<Enter>", lambda e: view_btn.configure(bg="#E55A2B"))
            view_btn.bind("<Leave>", lambda e: view_btn.configure(bg="#FF6B35"))

            close_btn = tk.Label(
                btn_frame, text="Close",
                font=("TkDefaultFont", 13, "bold"),
                bg="#888888", fg="white",
                relief="raised", borderwidth=2,
                padx=20, pady=8, cursor="hand2",
            )
            close_btn.pack(side="left", padx=5)
            close_btn.bind("<Button-1>", lambda e: popup.destroy())
            close_btn.bind("<Enter>", lambda e: close_btn.configure(bg="#666666"))
            close_btn.bind("<Leave>", lambda e: close_btn.configure(bg="#888888"))

        def _show_matched_files_help(self, parent):
            """Show help for the Matched Files popup."""
            import tkinter as tk
            help_win = tk.Toplevel(parent)
            help_win.title("Matched Files \u2014 Help")
            help_win.geometry("720x640")
            help_win.resizable(True, True)
            help_win.transient(parent)
            try:
                help_win.grab_set()
            except Exception:
                help_win.after(150, lambda: help_win.grab_set() if help_win.winfo_exists() else None)

            txt_frame = tk.Frame(help_win)
            txt_frame.pack(fill="both", expand=True, padx=10, pady=10)
            scrollbar = tk.Scrollbar(txt_frame)
            scrollbar.pack(side="right", fill="y")
            txt = tk.Text(
                txt_frame, wrap="word", font=("TkDefaultFont", 12),
                yscrollcommand=scrollbar.set, padx=10, pady=10,
                borderwidth=1, relief="sunken",
            )
            txt.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=txt.yview)

            txt.tag_configure("heading", font=("TkDefaultFont", 13, "bold"), spacing1=8, spacing3=4)
            txt.tag_configure("body", font=("TkDefaultFont", 12), lmargin1=10, lmargin2=10, spacing3=2)
            txt.tag_configure("example", font=("Courier", 11), lmargin1=20, lmargin2=20, spacing3=2)
            txt.tag_configure("toc_title", font=("TkDefaultFont", 14, "bold"), spacing1=5, spacing3=8)
            txt.tag_configure("toc_item", font=("TkDefaultFont", 11), lmargin1=20, lmargin2=20,
                              foreground="gray40")

            def h(s): txt.insert("end", s + "\n", "heading")
            def b(s): txt.insert("end", s + "\n", "body")
            def e(s): txt.insert("end", s + "\n", "example")
            def blank(): txt.insert("end", "\n")

            txt.insert("end", "TABLE OF CONTENTS\n", "toc_title")
            for section in [
                "What This Popup Shows",
                "How to Use It",
                "View Text vs Open File",
                "Line Numbers",
                "Why Some Files May Be Missing",
            ]:
                txt.insert("end", f"\u2022 {section}\n", "toc_item")
            txt.insert("end", "\n")

            h("WHAT THIS POPUP SHOWS")
            b("You opened this popup by clicking the orange Matched Files")
            b("button on the status line at the bottom of the main window.")
            b("It lists every file that matched your search \u2014 one row per")
            b("file \u2014 along with the number of matches in that file and")
            b("the line numbers where the matches were found (up to 10 line")
            b("numbers, then \"...\").")
            blank()
            b("Example row:")
            e("  quarterly_report.docx (3 matches \u2014 lines 12, 47, 89)")
            blank()
            b("If you ran an inverse search, the popup instead lists files")
            b("that did NOT match your search \u2014 the files missing the")
            b("required content.")
            blank()

            h("HOW TO USE IT")
            b("\u2022 Single-click a row to select it")
            b("\u2022 Double-click a row to open the file in its default")
            b("  application (Word, Excel, PDF viewer, etc.)")
            b("\u2022 Select a row and click View Text to see the extracted")
            b("  text of the file with line numbers and every match")
            b("  highlighted in yellow \u2014 useful when the original")
            b("  file is a PDF, archive, or format that is awkward")
            b("  to search visually")
            b("\u2022 Click Close when you're done")
            blank()

            h("VIEW TEXT vs OPEN FILE")
            b("Double-clicking a row opens the original file \u2014 the actual")
            b(".docx, .pdf, .xlsx, or whatever format it is \u2014 in the")
            b("application your system uses for that file type.")
            blank()
            b("View Text opens peekdocs's extracted plain-text view of")
            b("the same file, with:")
            b("\u2022 Line numbers down the left side")
            b("\u2022 Every match highlighted in yellow")
            b("\u2022 A scrollable window you can read without leaving peekdocs")
            blank()
            b("Use View Text when you want to quickly scan the matches in")
            b("context. Use Open File when you want to edit, print, or")
            b("share the original document.")
            blank()

            h("LINE NUMBERS")
            b("Line numbers refer to the EXTRACTED text, not the original")
            b("page or paragraph number in the source document. For plain")
            b("text files, these are the same. For .docx, .pdf, .xlsx, and")
            b("other formats, peekdocs extracts the text content and")
            b("numbers the resulting lines \u2014 so line 47 in the popup will")
            b("match line 47 in the View Text window, but may not match")
            b("a page number or paragraph number you see when you open")
            b("the original file in Word or a PDF viewer.")
            blank()
            b("To jump directly to a match in context, click View Text")
            b("and scroll to the highlighted line.")
            blank()

            h("WHY SOME FILES MAY BE MISSING")
            b("If the popup shows fewer files than you expected, some")
            b("files in the folder may have been excluded from the search.")
            b("Close this popup and click the gray Excluded Files button")
            b("on the status line to see exactly which files were skipped")
            b("and why (unsupported type, oversized, hidden, prior")
            b("peekdocs output, etc.).")
            blank()

            txt.configure(state="disabled")

            close_btn = ctk.CTkButton(
                help_win, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=help_win.destroy,
                font=ctk.CTkFont(size=12),
            )
            close_btn.pack(pady=(5, 10))

        def _show_save_load_help(self):
            """Show help for the Save Search and Load Search buttons."""
            import tkinter as tk
            help_win = tk.Toplevel(self)
            help_win.title("Save Search & Load Search \u2014 Help")
            help_win.geometry("740x680")
            help_win.resizable(True, True)
            help_win.transient(self)
            try:
                help_win.grab_set()
            except Exception:
                help_win.after(150, lambda: help_win.grab_set() if help_win.winfo_exists() else None)

            txt_frame = tk.Frame(help_win)
            txt_frame.pack(fill="both", expand=True, padx=10, pady=10)
            scrollbar = tk.Scrollbar(txt_frame)
            scrollbar.pack(side="right", fill="y")
            txt = tk.Text(
                txt_frame, wrap="word", font=("TkDefaultFont", 12),
                yscrollcommand=scrollbar.set, padx=10, pady=10,
                borderwidth=1, relief="sunken",
            )
            txt.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=txt.yview)

            txt.tag_configure("heading", font=("TkDefaultFont", 13, "bold"), spacing1=8, spacing3=4)
            txt.tag_configure("body", font=("TkDefaultFont", 12), lmargin1=10, lmargin2=10, spacing3=2)
            txt.tag_configure("example", font=("Courier", 11), lmargin1=20, lmargin2=20, spacing3=2)
            txt.tag_configure("toc_title", font=("TkDefaultFont", 14, "bold"), spacing1=5, spacing3=8)
            txt.tag_configure("toc_item", font=("TkDefaultFont", 11), lmargin1=20, lmargin2=20,
                              foreground="gray40")

            def h(s): txt.insert("end", s + "\n", "heading")
            def b(s): txt.insert("end", s + "\n", "body")
            def e(s): txt.insert("end", s + "\n", "example")
            def blank(): txt.insert("end", "\n")

            txt.insert("end", "TABLE OF CONTENTS\n", "toc_title")
            for section in [
                "What Save Search Does",
                "What Load Search Does",
                "Where Saved Searches Are Stored",
                "Editing a Saved Search",
                "Deleting a Saved Search",
                "Sharing Saved Searches",
                "Tips",
            ]:
                txt.insert("end", f"\u2022 {section}\n", "toc_item")
            txt.insert("end", "\n")

            h("WHAT SAVE SEARCH DOES")
            b("Save Search takes everything you currently have configured")
            b("on the main screen \u2014 search terms, mode (AND/OR/Boolean/")
            b("regex/fuzzy/wildcard/whole word), inverse, file type filters,")
            b("exclude terms, proximity, range filters, context lines,")
            b("recursive, OCR, max file size, and use-index \u2014 and stores")
            b("it under a name you choose.")
            blank()
            b("Once saved, you can reload the exact same configuration")
            b("later with one click from Load Search. Nothing is \"locked")
            b("in\" \u2014 you can always edit and re-save it.")
            blank()
            b("Saving does NOT run the search. If you want to verify that")
            b("the search works the way you expect, click Run Search")
            b("first, check the results, then click Save Search.")
            blank()

            h("WHAT LOAD SEARCH DOES")
            b("Load Search \u25bc opens a popup listing every saved search in")
            b("the current folder's collection. Click one to load it back")
            b("into the main screen \u2014 the search terms and all options")
            b("are restored exactly as they were when you saved.")
            blank()
            b("After loading, you can:")
            b("\u2022 Click Run Search to execute it as-is")
            b("\u2022 Modify any field and click Run Search to try a variation")
            b("\u2022 Click Save Search to overwrite the saved version (use")
            b("  the same name) or save it as a new one (use a new name)")
            b("\u2022 Delete the saved search from the Load Search popup")
            blank()
            b("Saving does NOT run the search. To verify a search works")
            b("the way you expect, click Run Search first, check the")
            b("results, then click Save Search.")
            blank()

            h("WHERE SAVED SEARCHES ARE STORED")
            b("Saved searches live in a file called .peekdocs_collection.json")
            b("inside the search folder itself. Each folder has its own")
            b("collection \u2014 the saved searches for ~/Documents/Contracts are")
            b("separate from those in ~/Documents/HR_Files. When you switch")
            b("folders on the main screen, the Load Search dropdown")
            b("automatically shows that folder's collection.")
            blank()
            b("This is deliberate: searches that matter for contracts")
            b("probably do not apply to HR files, and storing them")
            b("alongside the documents means they travel with the folder")
            b("if you copy, move, or back it up.")
            blank()

            h("EDITING A SAVED SEARCH")
            b("1. Click Load Search \u25bc and pick the one you want to edit")
            b("2. The search bar and Advanced Search Options are filled in")
            b("   with the saved values")
            b("3. Change whatever you need to (terms, filters, options)")
            b("4. Click Run Search to verify the new version works")
            b("5. Click Save Search and give it the SAME name \u2014 you'll")
            b("   be asked to confirm overwriting the existing entry")
            blank()
            b("If you give it a new name instead, you'll end up with two")
            b("saved searches: the original and your modified version.")
            blank()

            h("DELETING A SAVED SEARCH")
            b("Open Load Search \u25bc. Each entry in the popup has a Delete")
            b("button next to it. Click Delete to remove that saved search")
            b("from the collection. You'll be asked to confirm.")
            blank()
            b("Deleting a saved search does NOT delete any files in the")
            b("folder. It only removes the entry from the")
            b(".peekdocs_collection.json file.")
            blank()

            h("SHARING SAVED SEARCHES")
            b("The .peekdocs_collection.json file is plain-text JSON. To")
            b("share a saved search with someone else, you can copy the")
            b("collection file directly, or copy the relevant entry out of")
            b("it into another folder's collection file. The file is human-")
            b("readable and easy to edit.")
            blank()

            h("TIPS")
            b("\u2022 Use descriptive names: \"contracts_missing_signature\"")
            b("  is more useful than \"search1\"")
            b("\u2022 Always Run Search to verify a search works BEFORE")
            b("  saving it. A saved search that doesn't work won't")
            b("  magically start working when you reload it later")
            b("\u2022 Saved searches remember everything on the main screen")
            b("  and in Advanced Search Options \u2014 terms, mode, filters,")
            b("  range queries, file types, everything")
            blank()

            txt.configure(state="disabled")

            close_btn = ctk.CTkButton(
                help_win, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=help_win.destroy,
                font=ctk.CTkFont(size=12),
            )
            close_btn.pack(pady=(5, 10))

        def _show_file_text_view(self, filepath, filename, highlight_regex_pattern=None):
            """Display extracted text of a file with line numbers and match highlighting.

            If highlight_regex_pattern is provided, matches for that regex are
            highlighted instead of matches for the main search bar's terms. This
            is used by the PII Scan View Files popup so the highlights reflect
            the PII category (SSN, credit card, etc.) rather than whatever is
            currently in the search bar.
            """
            import tkinter as tk
            from peekdocs.scanner import _extract_lines, _ocr_image
            import re as _re_view

            try:
                lines = _extract_lines(filepath, use_ocr=False, ocr_func=_ocr_image)
            except Exception as e:
                self._show_error(f"Could not extract text from {filename}: {e}")
                return

            win = tk.Toplevel(self)
            win.title(f"Text View — {filename}")
            win.geometry("900x600")
            win.resizable(True, True)

            tk.Label(
                win, text=f"{filename}  —  {len(lines)} line(s) extracted",
                font=("TkDefaultFont", 12, "bold"),
            ).pack(pady=(10, 2))
            tk.Label(
                win, text="Line numbers match those shown in the Results Preview. "
                          "Matches are highlighted in orange.",
                font=("TkDefaultFont", 10), fg="gray",
            ).pack(pady=(0, 2))
            matching_lines_label = tk.Label(
                win, text="", font=("TkDefaultFont", 11, "bold"),
                fg="#FF6B35", anchor="w",
            )
            matching_lines_label.pack(fill="x", padx=15, pady=(0, 8))

            text_frame = tk.Frame(win)
            text_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))
            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side="right", fill="y")

            txt = tk.Text(
                text_frame, wrap="word", font=("Courier", 11),
                yscrollcommand=scrollbar.set, padx=8, pady=5,
                bg="white", fg="black",
            )
            txt.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=txt.yview)

            txt.tag_configure("line_num", foreground="#888888")
            txt.tag_configure("match", background="#FF6B35", foreground="white")

            # Build highlight pattern — either from the caller-supplied regex
            # (PII Scan path) or from the main search bar (normal path).
            patterns = []
            if highlight_regex_pattern:
                patterns.append(highlight_regex_pattern)
            else:
                search_text = self.search_entry.get().strip()
                if search_text:
                    use_regex = self.regex_var.get() == "on"
                    use_wildcard = self.wildcard_var.get() == "on"
                    use_whole_word = self.whole_word_var.get() == "on"
                    is_expression = self.expression_var.get() == "on"
                    if is_expression:
                        try:
                            from peekdocs.expr_parser import parse_expression, extract_positive_terms
                            terms = extract_positive_terms(parse_expression(search_text))
                        except Exception:
                            terms = search_text.split()
                    else:
                        terms = search_text.split()
                    for term in terms:
                        if use_wildcard:
                            from peekdocs.scanner import _wildcard_to_regex
                            patterns.append(_wildcard_to_regex(term))
                        elif use_regex:
                            patterns.append(term)
                        elif use_whole_word:
                            patterns.append(r'\b' + _re_view.escape(term) + r'\b')
                        else:
                            patterns.append(_re_view.escape(term))

            combined_re = None
            if patterns:
                try:
                    combined_re = _re_view.compile("|".join(f"({p})" for p in patterns), _re_view.IGNORECASE)
                except _re_view.error:
                    combined_re = None

            # Calculate line number column width
            max_ln = max((ln for ln, _ in lines), default=1)
            ln_width = len(str(max_ln))

            first_match_line = None
            matched_line_nums = []
            for line_num, text in lines:
                prefix = f"{line_num:>{ln_width}}  "
                txt.insert("end", prefix, "line_num")
                line_start_idx = txt.index("end-1c")
                txt.insert("end", text + "\n")
                # Highlight matches on this line
                if combined_re:
                    found_on_line = False
                    for m in combined_re.finditer(text):
                        start_col = m.start()
                        end_col = m.end()
                        start_idx = f"{line_start_idx}+{start_col}c"
                        end_idx = f"{line_start_idx}+{end_col}c"
                        txt.tag_add("match", start_idx, end_idx)
                        if first_match_line is None:
                            first_match_line = line_num
                        found_on_line = True
                    if found_on_line:
                        matched_line_nums.append(line_num)

            # Show matching line numbers
            if matched_line_nums:
                shown = matched_line_nums[:20]
                lines_str = ", ".join(str(n) for n in shown)
                if len(matched_line_nums) > 20:
                    lines_str += f", ... ({len(matched_line_nums)} total)"
                matching_lines_label.configure(
                    text=f"Matching lines: {lines_str}"
                )
            else:
                matching_lines_label.configure(text="No matches in this file")

            txt.configure(state="disabled")

            # Scroll to first match using the match tag
            first_match_range = txt.tag_ranges("match")
            if first_match_range:
                txt.see(first_match_range[0])
                # Also highlight the first match more prominently
                txt.tag_configure("first_match", background="#FF6B35", foreground="white")
                txt.tag_add("first_match", first_match_range[0], first_match_range[1])

            tk.Button(
                win, text="Close", width=10, command=win.destroy,
            ).pack(pady=(5, 10))

        def open_help(self):
            """Open the peekdocs User Guide in the default web browser."""
            webbrowser.open("https://github.com/exbuf/peekdocs/blob/main/docs/USER_GUIDE.md")

        def show_about(self):
            """Show the About dialog with version and author information."""
            import tkinter as tk
            about_win = tk.Toplevel(self)
            about_win.title("About peekdocs")
            about_win.resizable(False, False)
            about_win.geometry("300x210")
            # Center on parent
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 300) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 120) // 2
            about_win.geometry(f"+{x}+{y}")
            try:
                ver = pkg_version("peekdocs")
            except Exception:
                ver = "unknown"
            tk.Label(about_win, text="peekdocs", font=("TkDefaultFont", 16, "bold")).pack(pady=(15, 2))
            tk.Label(about_win, text=f"Version {ver}", font=("TkDefaultFont", 12)).pack()
            tk.Label(about_win, text="by Robert D. Schoening", font=("TkDefaultFont", 12)).pack(pady=(2, 2))
            tk.Label(about_win, text="MIT License", font=("TkDefaultFont", 11)).pack()
            tk.Label(about_win, text="Provided as-is, without warranty of any kind.\n"
                     "See the LICENSE file for details.",
                     font=("TkDefaultFont", 9), fg="gray", justify="center",
                     wraplength=280).pack(pady=(5, 5))

            ctk.CTkButton(
                about_win, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=about_win.destroy,
                font=ctk.CTkFont(size=12),
            ).pack(pady=(0, 10))

        _TEXT_SIZE_SCALES = {
            "Small": 0.85,
            "Normal": 1.0,
            "Large": 1.2,
            "Extra Large": 1.4,
            "Huge": 1.7,
        }

        def _on_preview_size_changed(self, value):
            """Change the Results Preview font size."""
            try:
                size = int(value)
            except ValueError:
                return
            self._preview_font_size = size
            self._apply_preview_font(size)

        def _apply_preview_font(self, size):
            """Apply a font size to the preview text widget and its tags."""
            if hasattr(self, 'preview_text'):
                self.preview_text.configure(font=("Courier", size))
                self.preview_text.tag_configure("filename", font=("Courier", size, "bold"))
                self.preview_text.tag_configure("line_num", font=("Courier", size))

        def _scaled_font(self, base_size=12, weight="normal"):
            """Return a font tuple scaled by the current Text Size setting."""
            scale = self._TEXT_SIZE_SCALES.get(self._text_size_var.get(), 1.0)
            size = max(8, int(base_size * scale))
            if weight == "bold":
                return ("TkDefaultFont", size, "bold")
            return ("TkDefaultFont", size)

        def _on_text_size_changed(self, value):
            """Scale all GUI widgets and auto-save the setting."""
            scale = self._TEXT_SIZE_SCALES.get(value, 1.0)
            ctk.set_widget_scaling(scale)
            # Shorten row 3 button labels at Extra Large and Huge to save width
            try:
                if value in ("Extra Large", "Huge"):
                    self.search_button.configure(text="Run")
                    self.save_to_collection_btn.configure(text="\u25b6 Save")
                    self.load_search_btn.configure(text="\u25b6 Reload")
                else:
                    self.search_button.configure(text="Run Search")
                    self.save_to_collection_btn.configure(text="\u25b6 Save")
                    self.load_search_btn.configure(text="\u25b6 Reload")
            except Exception:
                pass
            # Update preview size dropdown to match the scaled size
            if hasattr(self, '_preview_size_var'):
                base_size = 11
                scaled_size = max(8, int(base_size * scale))
                self._preview_font_size = scaled_size
                self._preview_size_var.set(str(scaled_size))
                self._apply_preview_font(scaled_size)
            # Auto-save so it persists between app invocations
            try:
                from peekdocs.cli import _load_config, _save_config
                cfg = _load_config()
                if value == "Normal":
                    cfg.pop("text_size", None)
                else:
                    cfg["text_size"] = value
                _save_config(cfg)
            except Exception:
                pass
            # Re-sync input field widths after scaling change
            self.after(200, self._sync_input_widths)

        def _inspect_settings(self):
            """Show the current saved settings from ~/.peekdocsrc in a read-only popup."""
            from peekdocs.cli import _config_path
            import tkinter as tk

            path = _config_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
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
            """Save current Advanced Search Options state to ~/.peekdocsrc."""
            from peekdocs.cli import _save_config, _config_path

            settings = {}
            # Boolean settings — always save both True and False
            settings["recursive"] = (self.recursive_var.get() == "on")
            settings["match_all"] = (self.and_mode_var.get() == "on")
            settings["fuzzy"] = (self.fuzzy_var.get() == "on")
            settings["wildcard"] = (self.wildcard_var.get() == "on")
            settings["regex"] = (self.regex_var.get() == "on")
            settings["ocr"] = (self.ocr_var.get() == "on")
            settings["index_search"] = (self.index_search_var.get() == "on")
            settings["output_csv"] = (self.output_csv_var.get() == "on")
            settings["output_json"] = (self.output_json_var.get() == "on")
            settings["output_pdf"] = (self.output_pdf_var.get() == "on")
            settings["inverse"] = (self.inverse_var.get() == "on")
            settings["expression"] = (self.expression_var.get() == "on")
            settings["whole_word"] = (self.whole_word_var.get() == "on")
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
            mfs = self.max_file_size_entry.get().strip()
            if mfs:
                try:
                    n = int(mfs)
                    if n >= 0:
                        settings["max_file_size_mb"] = n
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
            range_val = self.range_entry.get().strip()
            if range_val:
                settings["range"] = range_val
            refresh_val = self.refresh_interval_var.get()
            if refresh_val != "Off":
                settings["refresh_interval"] = refresh_val
            settings["text_size"] = self._text_size_var.get()
            settings["preview_size"] = self._preview_size_var.get()

            if settings:
                _save_config(settings)
            else:
                path = _config_path()
                if os.path.exists(path):
                    os.remove(path)
            self.status_label.configure(
                text="Settings saved to ~/.peekdocsrc",
                text_color="blue",
                font=ctk.CTkFont(size=13),
            )

        def _load_saved_settings(self):
            """Load saved settings from ~/.peekdocsrc and apply to GUI."""
            from peekdocs.cli import _load_config

            config = _load_config()
            # Default Recursive and Whole Word to ON unless config explicitly says otherwise
            _recursive_default = True
            _whole_word_default = True
            # Set booleans — reset to off if not in config (except recursive/whole_word)
            self.recursive_var.set("on" if config.get("recursive", _recursive_default) else "off")
            self.and_mode_var.set("on" if config.get("match_all") else "off")
            if hasattr(self, "_sync_and_or_colors"):
                self._sync_and_or_colors()
            self.fuzzy_var.set("on" if config.get("fuzzy") else "off")
            self.wildcard_var.set("on" if config.get("wildcard") else "off")
            self.regex_var.set("on" if config.get("regex") else "off")
            self.ocr_var.set("on" if config.get("ocr") else "off")
            self.index_search_var.set("on" if config.get("index_search") else "off")
            self.output_csv_var.set("on" if config.get("output_csv") else "off")
            self.output_json_var.set("on" if config.get("output_json") else "off")
            self.output_pdf_var.set("on" if config.get("output_pdf") else "off")
            self.inverse_var.set("on" if config.get("inverse") else "off")
            self.expression_var.set("on" if config.get("expression") else "off")
            self.whole_word_var.set("on" if config.get("whole_word", _whole_word_default) else "off")
            self.timestamp_var.set("on" if config.get("timestamp", False) else "off")
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
            self.max_file_size_entry.delete(0, "end")
            if "max_file_size_mb" in config:
                self.max_file_size_entry.insert(0, str(config["max_file_size_mb"]))
            else:
                self.max_file_size_entry.insert(0, "100")
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
            # Restore preview size
            preview_size = config.get("preview_size", "11")
            if preview_size not in ("8", "9", "10", "11", "12", "13", "14", "16", "18", "20"):
                preview_size = "11"
            self._preview_size_var.set(preview_size)
            self._on_preview_size_changed(preview_size)

        def reset_form(self):
            """Reset all fields to their defaults."""
            self.search_entry.delete(0, "end")
            self.and_mode_var.set("off")
            if hasattr(self, "_sync_and_or_colors"):
                self._sync_and_or_colors()
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
            self.max_file_size_entry.delete(0, "end")
            self.max_file_size_entry.insert(0, "100")
            self.specific_files_entry.delete(0, "end")
            self.save_name_entry.delete(0, "end")
            self.append_name_entry.delete(0, "end")
            self.output_csv_var.set("off")
            self.output_json_var.set("off")
            self.output_pdf_var.set("off")
            self.index_search_var.set("off")
            self.inverse_var.set("off")
            self.expression_var.set("off")
            self.whole_word_var.set("off")
            self.timestamp_var.set("off")
            self.output_dir_entry.delete(0, "end")
            self.range_entry.delete(0, "end")
            self.refresh_interval_var.set("Off")
            self._on_refresh_interval_changed("Off")
            self.search_entry.configure(placeholder_text="Enter search terms...")
            self.status_label.configure(
                text="", text_color=("gray30", "gray70")
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
            self.report_btn_pdf.pack_forget()

        def _show_error(self, message):
            """Display an error message in the status label and a modal dialog."""
            self.status_label.configure(
                text=message, text_color="red"
            )
            self.bell()
            messagebox.showerror("Error", message)

        def _add_folder_bar(self, parent, message="Your search will run against this folder."):
            """Add a folder display bar with Change Folder button to a wizard window.

            Returns the folder label widget so callers can read the current value.
            """
            import tkinter as tk
            from tkinter import filedialog

            bar = tk.Frame(parent, bd=1, relief="groove", padx=8, pady=5)
            bar.pack(fill="x", padx=15, pady=(5, 5))

            top_row = tk.Frame(bar)
            top_row.pack(fill="x")

            tk.Label(
                top_row, text="Search Folder:",
                font=("TkDefaultFont", 11, "bold"),
            ).pack(side="left")

            folder_label = tk.Label(
                top_row, text=self.folder_entry.get().strip() or "(none)",
                font=("TkDefaultFont", 11), fg="blue",
            )
            folder_label.pack(side="left", padx=(5, 10))

            def _change_folder():
                new_folder = filedialog.askdirectory(
                    parent=parent,
                    title="Select Search Folder",
                    initialdir=folder_label.cget("text") if folder_label.cget("text") != "(none)" else os.path.expanduser("~"),
                )
                if new_folder:
                    folder_label.configure(text=new_folder)

            tk.Button(
                top_row, text="Change Folder", command=_change_folder,
                font=("TkDefaultFont", 10),
            ).pack(side="right")

            tk.Label(
                bar, text=message,
                font=("TkDefaultFont", 10), fg="gray", anchor="w",
            ).pack(fill="x", pady=(2, 0))

            return folder_label

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
                "max_file_size_mb": self.max_file_size_entry.get().strip(),
                "specific_files": self.specific_files_entry.get().strip(),
                "index_search": self.index_search_var.get() == "on",
                "inverse": self.inverse_var.get() == "on",
                "expression": self.expression_var.get() == "on",
                "whole_word": self.whole_word_var.get() == "on",
                "output_csv": self.output_csv_var.get() == "on",
                "output_json": self.output_json_var.get() == "on",
                "output_pdf": self.output_pdf_var.get() == "on",
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
            if hasattr(self, "_sync_and_or_colors"):
                self._sync_and_or_colors()
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
            self.max_file_size_entry.delete(0, "end")
            self.max_file_size_entry.insert(0, params.get("max_file_size_mb", "") or "100")
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
            self.output_pdf_var.set("on" if params.get("output_pdf") else "off")
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
            from peekdocs.collection import add_saved_search, load_collection

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
            w, h = 350, 150
            x = self.winfo_rootx() + (self.winfo_width() - w) // 2
            y = self.winfo_rooty() + (self.winfo_height() - h) // 2
            dialog.geometry(f"{w}x{h}+{x}+{y}")
            dialog.transient(self)
            try:
                dialog.grab_set()
            except Exception:
                dialog.after(150, lambda: dialog.grab_set() if dialog.winfo_exists() else None)

            frame = ctk.CTkFrame(dialog)
            frame.pack(fill="both", expand=True)

            ctk.CTkLabel(frame, text="Search name:", font=ctk.CTkFont(size=13)).pack(
                padx=15, pady=(15, 5), anchor="w"
            )
            name_entry = ctk.CTkEntry(frame, font=ctk.CTkFont(size=13))
            name_entry.pack(padx=15, fill="x")
            name_entry.focus_set()

            def do_save(_event=None):
                name = name_entry.get().strip()
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
                        text_color="blue", font=ctk.CTkFont(size=13),
                    )
                    self._refresh_load_search_menu()
                except Exception as exc:
                    self._show_error(f"Failed to save search: {exc}")

            name_entry.bind("<Return>", do_save)
            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.pack(pady=(10, 2))
            ctk.CTkButton(btn_frame, text="Save", width=70, font=ctk.CTkFont(size=12),
                          command=do_save).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Cancel", width=70, font=ctk.CTkFont(size=12),
                          command=dialog.destroy).pack(side="left", padx=5)
            close_frame = ctk.CTkFrame(frame, fg_color="transparent")
            close_frame.pack(pady=(0, 10))
            ctk.CTkButton(close_frame, text="Close", width=80,
                          fg_color="transparent", text_color=("gray30", "gray70"),
                          hover_color=("gray90", "gray25"),
                          font=ctk.CTkFont(size=12),
                          command=dialog.destroy).pack()

        # ── Search Wizard ────────────────────────────────────────

        def _open_search_wizard(self):
            """Open the Search Wizard popup for building regex patterns."""
            import tkinter as tk
            from tkinter import ttk
            from peekdocs.wizard_patterns import WIZARD_PATTERNS, WIZARD_CATEGORY_ORDER

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

            # Enable mousewheel scrolling (cross-platform)
            def _bind_mousewheel_rw(c, parent_win):
                def _scroll(event):
                    if sys.platform == "darwin":
                        c.yview_scroll(-event.delta, "units")
                    elif sys.platform == "linux":
                        pass
                    else:
                        c.yview_scroll(int(-event.delta / 40), "units")
                c.configure(yscrollincrement=5)
                parent_win.bind("<MouseWheel>", _scroll)
                if sys.platform == "linux":
                    parent_win.bind("<Button-4>", lambda e: c.yview_scroll(-1, "units"))
                    parent_win.bind("<Button-5>", lambda e: c.yview_scroll(1, "units"))
            _bind_mousewheel_rw(canvas, wiz)

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
            btn_frame.pack(fill="x", padx=15, pady=(0, 2))
            close_frame = tk.Frame(wiz)
            close_frame.pack(pady=(0, 12))

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
                            "The AND mode checkbox in Advanced Search Options applies "
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
                if hasattr(self, "_sync_and_or_colors"):
                    self._sync_and_or_colors()
                wiz.destroy()

            tk.Button(btn_frame, text="Select All", width=10, command=_select_all).pack(side="left", padx=(0, 5))
            tk.Button(btn_frame, text="Clear All", width=10, command=_clear_all).pack(side="left", padx=(0, 5))
            tk.Button(btn_frame, text="Apply", width=10, command=_apply).pack(side="right", padx=(5, 0))
            ctk.CTkButton(
                close_frame, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=wiz.destroy,
                font=ctk.CTkFont(size=12),
            ).pack()

            # Load initial category
            _load_category()

        # ── Mutual exclusion for search modes ────────────────────

        def _on_fuzzy_toggle(self):
            """Handle fuzzy toggle by disabling conflicting regex and wildcard modes."""
            if self.fuzzy_var.get() == "on":
                self.regex_var.set("off")
                self.wildcard_var.set("off")

        def _on_regex_toggle(self):
            """Handle regex toggle by disabling conflicting fuzzy and wildcard modes."""
            if self.regex_var.get() == "on":
                self.fuzzy_var.set("off")
                self.wildcard_var.set("off")

        def _on_wildcard_toggle(self):
            """Handle wildcard toggle by disabling conflicting fuzzy and regex modes."""
            if self.wildcard_var.get() == "on":
                self.fuzzy_var.set("off")
                self.regex_var.set("off")

        def _on_expression_toggle(self):
            """Handle expression toggle by disabling AND mode, exclude, and proximity."""
            if self.expression_var.get() == "on":
                self.and_mode_var.set("off")
                if hasattr(self, "_sync_and_or_colors"):
                    self._sync_and_or_colors()
                self.exclude_entry.delete(0, "end")
                self.proximity_entry.delete(0, "end")
                self.search_entry.configure(placeholder_text='e.g. (budget OR revenue) AND NOT draft')
            else:
                self.search_entry.configure(placeholder_text="Enter search terms...")

        def _on_and_toggle(self):
            """Handle AND mode toggle by disabling the expression mode."""
            if self.and_mode_var.get() == "on":
                self.expression_var.set("off")
                self.search_entry.configure(placeholder_text="Enter search terms...")
            if hasattr(self, "_sync_and_or_colors"):
                self._sync_and_or_colors()

    app = PeekDocsApp()
    app.mainloop()


def main():
    """Launch the peekdocs graphical interface."""
    _launch_gui()


if __name__ == "__main__":
    main()
