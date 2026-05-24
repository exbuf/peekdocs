"""PeekDocs GUI — BuildMixin."""

import os
import platform
import re
import subprocess
import sys
import threading
import time
from datetime import datetime

import customtkinter as ctk

from peekdocs.gui._tooltip import Tooltip
from peekdocs.gui._helpers import (
    _build_command_from_values,
    _parse_summary_text,
    _parse_matched_files,
    _parse_inverse_files,
    _build_wizard_regex,
)
import webbrowser
from tkinter import filedialog, messagebox

class BuildMixin:
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
        _step(3, "Click Run Standard Search", "peekdocs scans every supported file and shows results with matches highlighted in yellow.")
        _step(4, "View your results", "Scan matches in the Results Preview pane, or click DOCX / TXT next to View Report for a highlighted report. No Microsoft Word? The DOCX opens in any word processor — LibreOffice (free) is recommended. Prefer your browser? Enable HTML in Advanced Search Options and click the HTML button. All reports stay on your computer — peekdocs avoids opening them in Google Docs, Apple Pages, or any cloud-based application that may upload your data. Check Delete on Close to automatically remove result files when you close the app.")

        tk.Label(inner, text="", font=("TkDefaultFont", 6)).pack()  # spacer

        tk.Label(inner, text="Want to do more?", font=("TkDefaultFont", 16, "bold")).pack(pady=(15, 5), **pad)

        features = [
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

        tk.Label(inner, text="You've got this! Click the Done tab above and discover what's hiding in your documents.",
                 font=("TkDefaultFont", 14, "bold"), fg="#2196F3").pack(pady=(15, 30), **pad)



    def _show_welcome(self):
        """Show a getting-started guide for first-time users."""
        import tkinter as tk
        win, _dark = self._themed_toplevel()
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
        st("Step 3: Click Run Standard Search")
        b("peekdocs scans every supported file in the folder and")
        b("shows a summary when finished. Your results appear in")
        b("a preview below, and are saved to two report files:")
        e("peekdocs_standard_results.txt   (plain text)")
        e("peekdocs_standard_results.docx  (Word, with highlights)")
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
        self._apply_dark_theme(win)



    def _build_search_row(self):
        """Build the search bar with entry field, action buttons, and tooltips.

        Both the folder row and search row share a single combined frame
        (_input_frame) so their columns align perfectly.  The folder row
        is built later by _build_folder_row at row 0; this method builds
        the search row at rows 1-2.
        """
        # Page header — small "Main page" label at the very top so users
        # know which screen they're on. Subordinate to tab/Step labels.
        self._page_header_lbl = ctk.CTkLabel(
            self._search_parent,
            text="Main page",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray45", "gray60"),
        )
        self._page_header_lbl.grid(
            row=0, column=0, columnspan=3,
            padx=(15, 5), pady=(2, 0), sticky="w"
        )

        # Combined frame for both input rows — shared grid columns
        # guarantee the labels, entries, and button frames align.
        self._input_frame = ctk.CTkFrame(self._search_parent, fg_color="transparent")
        self._input_frame.grid(
            row=1, column=0, columnspan=3,
            padx=10, pady=(5, 2), sticky="nsew"
        )
        self._input_frame.grid_columnconfigure(0)
        self._input_frame.grid_columnconfigure(1, weight=1)
        self._input_frame.grid_columnconfigure(2, minsize=185)
        self._input_frame.grid_rowconfigure(7, weight=1)  # preview row expands

        # Create recursive_var early so both the folder row checkbox
        # and Advanced Search Options can share it.
        self.recursive_var = ctk.StringVar(value="on")

        import tkinter as _tk_step2
        _step_lbl_2 = _tk_step2.Label(self._input_frame, text=" Step 2 ", font=("TkDefaultFont", 14, "bold"),
                                       fg="white", bg="#2196F3")
        _step_lbl_2.grid(row=1, column=0, padx=(10, 2), pady=(4, 8), sticky="w")
        Tooltip(_step_lbl_2, "Search Terms — type what you're looking for, then select AND/OR, Recursive (include subfolders), or Whole Word. For advanced options click Advanced")

        self._assistant_label = ctk.CTkLabel(
            self._input_frame, text="", font=ctk.CTkFont(size=12),
            text_color=("#8B5CF6", "#A78BFA"), anchor="w",
        )
        # Hidden until Search Assistant sets a query

        self.search_entry = ctk.CTkEntry(
            self._input_frame, placeholder_text="Enter search terms...", font=ctk.CTkFont(size=14)
        )
        self.search_entry.grid(row=1, column=1, padx=(5, 5), pady=(4, 8), sticky="ew")
        self.search_entry.bind("<Key>", lambda e: self._assistant_label.grid_remove() if e.keysym not in ("Return", "Tab") else None)
        self.search_entry.bind("<Return>", lambda e: self.start_search())

        self._search_btn_frame = ctk.CTkFrame(self._input_frame, corner_radius=6,
                                               border_width=2, border_color=("gray50", "gray50"))
        self._search_btn_frame.grid(row=1, column=2, padx=(5, 10), pady=(4, 8), sticky="w")

        clear_button = ctk.CTkButton(
            self._search_btn_frame, text="Clear", width=70,
            command=lambda: self.search_entry.delete(0, "end"),
            font=ctk.CTkFont(size=14),
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
        )
        clear_button.pack(side="left", padx=(6, 3), pady=4)
        Tooltip(clear_button, "Clear the search bar", anchor="left")

        recent_btn = ctk.CTkButton(
            self._search_btn_frame, text="\u25bc Recent Searches", width=130,
            command=self._show_recent_searches,
            font=ctk.CTkFont(size=14),
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
        )
        recent_btn.pack(side="left", padx=(0, 6), pady=4)
        Tooltip(recent_btn, "Show recent searches — click to re-use a previous search", anchor="left")

        # Row 2: options row (AND/OR, Save/Reload, Use Index)
        # Small "Options" label in column 0, under the Step 2 tag, for visual cue.
        # Faded color + small font so it doesn't compete with the Step labels.
        self._options_lbl = ctk.CTkLabel(
            self._input_frame,
            text="Options",
            font=ctk.CTkFont(size=16),
            text_color=("gray55", "gray55"),
        )
        self._options_lbl.grid(row=2, column=0, padx=(10, 2), pady=(0, 8), sticky="nw")

        self._options_row = ctk.CTkFrame(self._input_frame, fg_color="transparent")
        self._options_row.grid(row=2, column=1, columnspan=2, padx=(5, 5), pady=(0, 8), sticky="w")
        options_row = self._options_row  # local alias for convenience

        # Row 3: "Step 3" label + Run Standard Search button
        import tkinter as _tk_step3
        _step_lbl_3 = _tk_step3.Label(self._input_frame, text=" Step 3 ", font=("TkDefaultFont", 14, "bold"),
                                       fg="white", bg="#2196F3")
        _step_lbl_3.grid(row=3, column=0, padx=(10, 2), pady=(0, 8), sticky="w")
        Tooltip(_step_lbl_3, "Run Standard Search — click to search all files in the folder")

        btn_frame = ctk.CTkFrame(self._input_frame, fg_color="transparent")
        self._run_search_frame = btn_frame
        btn_frame.grid(row=3, column=1, columnspan=2, padx=(5, 5), pady=(0, 8), sticky="ew")

        # Run Standard Search button — standalone
        self.search_button = ctk.CTkButton(
            btn_frame, text="\U0001f50d Run Standard Search", width=270, height=44, command=self.start_search,
            font=ctk.CTkFont(size=24, weight="bold"),
            fg_color="#76BA1B", hover_color="#5E9516", text_color="white",
        )
        self.search_button.pack(side="left", padx=(0, 10))
        Tooltip(self.search_button, "Run a standard search using the current search terms and all settings in Advanced Search Options (checkboxes, file types, exclude terms, range filters, proximity, etc.). For pattern-based searches (regex collections, screen-only mode), use Run Regex Search instead. This button turns red and is temporarily disabled while an index is being built to avoid conflicts")



        # Search options group: AND/OR, Recursive, Whole Word, ?
        options_group = ctk.CTkFrame(
            options_row, border_width=2, border_color=("gray40", "gray60"),
            corner_radius=8, fg_color=("gray85", "gray20"),
        )
        options_group.pack(side="left", padx=(0, 10))

        # AND/OR toggle buttons — the active mode is highlighted blue (matches checkboxes)
        self.and_mode_var = ctk.StringVar(value="off")
        _and_on_fg = ("#3B8ED0", "#3B8ED0")
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
            hover_color=("#1f6aa5", "#1f6aa5"),
            command=_on_and_click,
        )
        self._and_btn.pack(side="left", padx=(4, 0), pady=3)
        Tooltip(self._and_btn, "AND mode — all search terms must appear in the same line. For PDF/Word documents, a line is typically a paragraph. Synced with AND mode in Advanced Search Options")

        self._or_btn = ctk.CTkButton(
            options_group, text="OR", width=35,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=_and_on_fg, text_color=_and_on_text,
            hover_color=("#1f6aa5", "#1f6aa5"),
            command=_on_or_click,
        )
        self._or_btn.pack(side="left", padx=(2, 4), pady=3)
        Tooltip(self._or_btn, "OR mode (default) — find lines containing any of the search terms. Synced with AND mode in Advanced Search Options")
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
        Tooltip(self._folder_recursive_cb, "Include all subfolders when searching. Synced with Recursive in Advanced Search Options. Without this checked and without using the index, peekdocs searches only the one folder shown — no subfolders. With the index checked, searches are always recursive regardless of this setting")

        self.whole_word_var = ctk.StringVar(value="on")
        self._search_whole_word_cb = ctk.CTkCheckBox(
            options_group, text="Whole Word", variable=self.whole_word_var,
            onvalue="on", offvalue="off", font=ctk.CTkFont(size=12),
        )
        self._search_whole_word_cb.pack(side="left", padx=(0, 4), pady=3)
        Tooltip(self._search_whole_word_cb, "Matches complete words only. 'bob' matches 'bob' but not 'bobcat'. Synced with Whole Word in Advanced Search Options")

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

        # Advanced Search Options toggle — between options group and save group
        self.advanced_toggle = ctk.CTkButton(
            options_row,
            text="Advanced", width=0,
            fg_color="transparent",
            text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            anchor="w",
            command=self.toggle_advanced,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.advanced_toggle.pack(side="left", padx=(10, 0))
        Tooltip(self.advanced_toggle, "Open the Advanced Search Options panel — AND mode, regex, fuzzy, file types, exclude terms, range filters, and all other search settings")

        self.index_search_var = ctk.StringVar(value="off")
        self.cb_index_search = ctk.CTkCheckBox(
            options_row, text="Use Index", variable=self.index_search_var,
            onvalue="on", offvalue="off", font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.cb_index_search.pack(side="left", padx=(10, 0))
        Tooltip(self.cb_index_search, "Use the search index for faster searches. Uncheck to search files directly. Build an index first using Indexes in the Tools menu. When checked, searches are always recursive (all subfolders) regardless of the Recursive checkbox. Indexes persist between sessions unless Delete on Close is checked, which deletes them when you close the app", anchor="left")

        # Search Wizard — sits before the Save / Reload group
        self._search_wiz_btn = ctk.CTkButton(
            options_row,
            text="Search Wizard", width=0,
            fg_color="transparent",
            text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            anchor="w",
            command=self._open_search_wizard_guide,
            font=ctk.CTkFont(size=13),
        )
        self._search_wiz_btn.pack(side="left", padx=(20, 0))
        Tooltip(self._search_wiz_btn, "Search Wizard — guided search builder with 20+ pre-built patterns. Pick a search type, fill in values, and apply. No flags or regex knowledge needed", anchor="left")

        # Save, Reload, and ? grouped together
        save_group = ctk.CTkFrame(
            options_row, border_width=2, border_color=("gray40", "gray60"),
            corner_radius=8, fg_color=("gray85", "gray20"),
        )
        save_group.pack(side="left", padx=(15, 0))

        self.save_to_collection_btn = ctk.CTkButton(
            save_group, text="\u25b6 Save", width=120,
            fg_color="transparent",
            text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=self._save_to_collection,
            font=ctk.CTkFont(size=13),
        )
        self.save_to_collection_btn.pack(side="left", padx=(10, 6), pady=3)
        Tooltip(self.save_to_collection_btn, "Save the current search settings by name so you can reload it later. You can click this before or after running a search — it saves the settings (search terms and options), not the results. Saves: search terms, AND/OR mode, Recursive, Whole Word, Fuzzy, Wildcard, Regex, Expression, Inverse, OCR, Use Index, file types, exclude terms, proximity, context lines, max matches, max file size, specific files, output formats (CSV/JSON/PDF/HTML), range filters, output directory, save name, and append name")

        self.load_search_btn = ctk.CTkButton(
            save_group, text="\u25b6 Reload", width=120,
            fg_color="transparent",
            text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=self._open_load_search_popup,
            font=ctk.CTkFont(size=13),
        )
        self.load_search_btn.pack(side="left", padx=(6, 6), pady=3)
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


        Tooltip(self.search_entry, "Search Bar: Type one or more search terms separated by spaces — there is no limit to the number of terms. Use quotes for phrases (e.g., \"annual report\"). All searches are case-insensitive. Do not use commas. Do not enter flags here — the checkboxes under Advanced Search Options handle that. When Expression is checked, enter a boolean expression instead (e.g., \"(bob AND amy) OR fred NOT draft\").")



    def _build_folder_row(self):
        """Build the folder selection row in the shared _input_frame at row 0."""
        import tkinter as _tk_step
        _step_lbl_1 = _tk_step.Label(self._input_frame, text=" Step 1 ", font=("TkDefaultFont", 14, "bold"),
                                      fg="white", bg="#2196F3")
        _step_lbl_1.grid(row=0, column=0, padx=(10, 2), pady=(4, 8), sticky="w")
        Tooltip(_step_lbl_1, "Search Folder — point peekdocs at the folder containing your documents")

        self.folder_entry = ctk.CTkEntry(self._input_frame, font=ctk.CTkFont(size=14))
        self.folder_entry.grid(row=0, column=1, padx=(5, 5), pady=(4, 8), sticky="ew")
        self.folder_entry.insert(0, os.path.expanduser("~"))

        self._browse_frame = ctk.CTkFrame(self._input_frame, corner_radius=6,
                                          border_width=2, border_color=("gray50", "gray50"))
        self._browse_frame.grid(row=0, column=2, padx=(5, 10), pady=(4, 8), sticky="w")

        self.browse_button = ctk.CTkButton(
            self._browse_frame, text="Browse", width=60, command=self.browse_folder,
            font=ctk.CTkFont(size=14),
        )
        self.browse_button.pack(side="left", padx=(6, 3), pady=4)
        Tooltip(self.browse_button, "Browse for a folder to search. Linux: double-click to select a folder in the dialog", anchor="left")

        self._multi_folder_btn = ctk.CTkButton(
            self._browse_frame, text="+Folder", width=65, command=self._add_folder,
            font=ctk.CTkFont(size=14),
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
        )
        self._multi_folder_btn.pack(side="left", padx=(3, 0))
        Tooltip(self._multi_folder_btn, "Search multiple top-level folders at once (e.g., Documents and Desktop). Different from Recursive, which searches subfolders within a single folder. Folders are separated by semicolons (;)", anchor="left")

        self.browse_file_button = ctk.CTkButton(
            self._browse_frame, text="Single File", width=80, command=self._browse_file,
            font=ctk.CTkFont(size=14),
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
        )
        self.browse_file_button.pack(side="left", padx=(3, 6), pady=4)
        Tooltip(self.browse_file_button, "Browse for a specific file to search", anchor="left")

        # Clear button — inside the browse frame, shown when a file is selected
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

        Tooltip(self.folder_entry, "Search Folder: The folder or file to search. Use Browse to pick a folder, Single File to pick a specific file")



    def _build_advanced_toggle(self):
        """Build the Advanced Search Options panel and remaining options_row buttons.

        Note: the Advanced toggle button itself is created in _build_search_row
        so it appears between the options group and the save group.
        """
        # Run Search Suites button — sits next to Run Standard Search in the run-buttons row
        self._suites_btn = ctk.CTkButton(
            self._run_search_frame,
            text="Run Search Suites", width=260, height=44,
            fg_color="#2196F3", hover_color="#1976D2",
            text_color="white",
            command=self._show_search_suites,
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self._suites_btn.pack(side="left", padx=(12, 0))
        Tooltip(self._suites_btn, "Run Search Suites — group saved searches into a named suite and run them all at once with a single click", anchor="above")

        # Run Regex Search button — gray, font matches Run Standard Search
        self._regex_search_btn = ctk.CTkButton(
            self._run_search_frame,
            text="Run Regex Search", width=240, height=44,
            fg_color="#6B7280", hover_color="#5B6270",
            text_color="white",
            command=self._start_regex_search,
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self._regex_search_btn.pack(side="left", padx=(12, 0))
        Tooltip(self._regex_search_btn, "Open the Regex Search workflow — create or run a named collection of up to 10 regex patterns, each executed separately with per-pattern results. Results depend on the report checkbox setting in the popup.")



    def _build_advanced_panel(self):
        """Build the Advanced Search Options popup window with all search mode checkboxes and fields."""
        # Create popup window for Advanced Search Options
        self.advanced_window = ctk.CTkToplevel(self)
        self.advanced_window.title("Advanced Search Options")
        self.advanced_window.after(100, lambda: self.advanced_window.title("Advanced Search Options"))
        self.advanced_window.geometry("900x760")
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
            text="All searches are based on this screen and the Search Terms on the main screen. Your selections take effect immediately on the next search \u2014 no need to press Save As Defaults. That button saves your settings as permanent defaults for future sessions.",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray50"),
            justify="left",
            wraplength=700,
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
        ctk.CTkLabel(self.advanced_frame, text="Word Proximity:").grid(
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
        output_frame.grid(row=10, column=0, columnspan=3, padx=15, pady=(0, 5), sticky="w")

        ctk.CTkLabel(output_frame, text="Also output report as ==>").grid(row=0, column=0, padx=(0, 10))
        self.output_csv_var = ctk.StringVar(value="off")
        self.output_json_var = ctk.StringVar(value="off")
        self.output_pdf_var = ctk.StringVar(value="off")
        self.output_html_var = ctk.StringVar(value="off")
        def _save_output_format(key, var):
            self._save_ui_preference(key, var.get() == "on")

        cb_csv = ctk.CTkCheckBox(
            output_frame, text="CSV", variable=self.output_csv_var,
            onvalue="on", offvalue="off",
            command=lambda: _save_output_format("output_csv", self.output_csv_var),
        )
        cb_csv.grid(row=0, column=1, padx=(0, 15))
        cb_json = ctk.CTkCheckBox(
            output_frame, text="JSON", variable=self.output_json_var,
            onvalue="on", offvalue="off",
            command=lambda: _save_output_format("output_json", self.output_json_var),
        )
        cb_json.grid(row=0, column=2, padx=(0, 15))
        cb_pdf = ctk.CTkCheckBox(
            output_frame, text="PDF", variable=self.output_pdf_var,
            onvalue="on", offvalue="off",
            command=lambda: _save_output_format("output_pdf", self.output_pdf_var),
        )
        cb_pdf.grid(row=0, column=3, padx=(0, 15))
        cb_html = ctk.CTkCheckBox(
            output_frame, text="HTML", variable=self.output_html_var,
            onvalue="on", offvalue="off",
            command=lambda: _save_output_format("output_html", self.output_html_var),
        )
        cb_html.grid(row=0, column=4, padx=(0, 0))
        self.timestamp_var = ctk.StringVar(value="off")
        cb_ts = ctk.CTkCheckBox(
            output_frame, text="Timestamp Filename", variable=self.timestamp_var,
            onvalue="on", offvalue="off",
        )
        cb_ts.grid(row=1, column=0, columnspan=2, padx=(0, 15), pady=(4, 0), sticky="w")
        Tooltip(cb_ts, "Keep every search result by appending date+time to filenames (e.g., peekdocs_standard_results_20260327_143022.txt). Without this, each search overwrites the previous results. Useful when you want to compare searches or keep a record. Files accumulate over time — use Delete on Close or Delete Everything Now to clean up")
        self.delete_reports_var = ctk.StringVar(value="off")
        cb_delete_adv = ctk.CTkCheckBox(
            output_frame, text="Delete on Close", variable=self.delete_reports_var,
            onvalue="on", offvalue="off",
            command=lambda: _save_output_format("delete_reports_on_close", self.delete_reports_var),
        )
        cb_delete_adv.grid(row=1, column=2, columnspan=2, padx=(0, 15), pady=(4, 0), sticky="w")
        self.clear_history_var = ctk.StringVar(value="off")
        cb_clear_hist = ctk.CTkCheckBox(
            output_frame, text="Clear History on Close", variable=self.clear_history_var,
            onvalue="on", offvalue="off",
            command=lambda: _save_output_format("clear_history_on_close", self.clear_history_var),
        )
        cb_clear_hist.grid(row=1, column=4, columnspan=2, padx=(0, 15), pady=(4, 0), sticky="w")
        self.restrict_permissions_var = ctk.StringVar(value="off")
        cb_restrict = ctk.CTkCheckBox(
            output_frame, text="Restrict File Permissions", variable=self.restrict_permissions_var,
            onvalue="on", offvalue="off",
            command=lambda: _save_output_format("restrict_permissions", self.restrict_permissions_var),
        )
        cb_restrict.grid(row=2, column=0, columnspan=3, padx=(0, 0), pady=(4, 0), sticky="w")

        # Separator line below output options
        import tkinter as _tk_sep
        _tk_sep.Frame(self.advanced_frame, height=2, bg="gray60").grid(
            row=11, column=0, columnspan=3, padx=15, pady=(10, 10), sticky="ew")

        # Row 12: Save Defaults + Restore Settings buttons
        settings_btn_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
        settings_btn_frame.grid(row=12, column=0, columnspan=3, padx=(0, 15), pady=(0, 0), sticky="e")




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
        Tooltip(cb_and, "All search terms must appear in the same line. For PDF/Word documents, a line is typically a paragraph")
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
        Tooltip(self.file_types_entry, "Comma-separated file extensions to search. Leave blank to search ALL 100+ supported file types (not every file on disk — unsupported formats like .DS_Store, .exe, random binaries are always skipped). Supported types: 7z, asm, bat, bz2, c, cfg, cir, cmake, conf, cpp, cs, css, csv, doc, dockerfile, docx, dxf, eml, env, epub, f, f90, go, gql, gradle, graphql, gz, h, hpp, html, ics, ini, ipynb, java, js, json, jsonl, key, kt, log, lua, m, makefile, mbox, md, msg, ndjson, numbers, odp, ods, odt, pages, pdf, pl, ppt, pptx, properties, proto, ps1, pst, py, r, rar, rb, rs, rst, rtf, s, scala, scss, sh, sp, spice, sql, sv, swift, tar, tcl, tex, tf, tgz, toml, ts, tsv, txt, v, vb, vcf, vhd, vhdl, vsdx, xls, xlsx, xml, yaml, yml, zip. With OCR enabled: bmp, jpg, jpeg, png, tif, tiff")
        Tooltip(self.proximity_entry, "Word Proximity (-p): find terms within this many words of each other on the same line. Line Proximity (-P) is available in the CLI only — it finds terms within N lines of each other")
        Tooltip(self.context_before_entry, "Number of lines to show before each match")
        Tooltip(self.context_after_entry, "Number of lines to show after each match")
        Tooltip(self.cores_entry, f"Number of CPU cores to use. This machine has {os.cpu_count()}, default is {self._default_cores}")
        Tooltip(self.max_matches_entry, "Maximum matches included in reports. Default 1000. Set to 0 for no limit. See \u2753 help for possible counterintuitive results when this interacts with Max File Size.")
        Tooltip(self.max_file_size_entry, "Skip files larger than this (in MB). Default 100. Set to 0 for no limit. See \u2753 help for possible counterintuitive results when this interacts with Max Matches.")
        Tooltip(self.specific_files_entry, "Comma-separated filenames to search — no limit to the number of files (e.g., report.pdf,notes.txt)")
        Tooltip(self.save_name_entry, "Save an extra copy of the report with a custom name after search completes. peekdocs_report_ will be added to the front of your file name. This is in addition to the regular results files (peekdocs_standard_results.txt and .docx) shown in View Report. Important: without this, your regular reports are overwritten every time you run a new search. Fill in this field to keep a permanent copy. To open it later, navigate to your Search Folder using File Explorer (Windows), Finder (macOS), or your file manager (Linux) and double-click the peekdocs_report_ file")
        Tooltip(self.append_name_entry, "Append results to a named report file (creates or extends it). peekdocs_accumulated_ will be added to the front of your file name")
        Tooltip(cb_csv, "Also save results as a CSV file (peekdocs_standard_results.csv) — open in Excel or Google Sheets to sort, filter, and analyze")
        Tooltip(cb_json, "Also save results as a JSON file (peekdocs_standard_results.json) — machine-readable format for automation and integration")
        Tooltip(cb_pdf, "Also save results as a PDF file (peekdocs_standard_results.pdf) — matches highlighted in yellow, portable format for sharing and printing")
        Tooltip(cb_html, "Also save results as an HTML file (peekdocs_standard_results.html) — opens in any web browser with highlighted matches. The file is stored locally on your computer, not on the internet — nothing is uploaded or made public")
        Tooltip(cb_delete_adv, "Automatically delete all search result files (peekdocs_standard_results.*, peekdocs_regex_results.*, peekdocs_suite_results.*) and the search index (.peekdocs.db) in every folder searched during the session when you close peekdocs. The index is included because it contains extracted text from every indexed file. You can check or uncheck this at any time — it only matters at the moment you close the app. Saved reports (peekdocs_report_*) and accumulated reports (peekdocs_accumulated_*) are never deleted — those are reports you explicitly chose to keep")
        Tooltip(cb_clear_hist, "Automatically clear your search history and recent searches when you close peekdocs. Search terms, folder paths, and recent searches are stored in plaintext on disk (~/.peekdocs_history.json and ~/.peekdocsrc). If you searched for a specific name, SSN, account number, or any sensitive term, that exact text is sitting in these files. This checkbox deletes the history file and clears search terms, folder path, and recent searches from your settings")
        Tooltip(cb_restrict, "Set report files to owner-only read/write (chmod 600) on Unix/macOS. Prevents other users on shared machines from reading your search results. Leave unchecked if colleagues need to access reports in a shared folder. No effect on Windows (NTFS permissions are managed differently). Applies to all report formats: TXT, DOCX, CSV, JSON, PDF, HTML")

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
        Tooltip(adv_save_btn, "Save all current options as permanent defaults to ~/.peekdocsrc. This includes all settings on this Advanced Search Options screen and on the main screen (search terms, folder, recursive, AND/OR mode, whole word, etc.). These become the defaults every time you launch the app", anchor="above")

        adv_close_btn = ctk.CTkButton(
            adv_bottom_frame, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=self._close_advanced_window,
            font=ctk.CTkFont(size=13),
        )
        adv_close_btn.place(relx=0.5, rely=0.5, anchor="center")
        Tooltip(adv_close_btn, "Close this panel. Your settings are preserved — they take effect on the next search. To make them permanent across sessions, click Save Defaults first", anchor="above")

        adv_restore_btn = ctk.CTkButton(
            adv_bottom_frame, text="Restore Saved Defaults", width=130,
            command=self._load_saved_settings,
            font=ctk.CTkFont(size=13),
        )
        adv_restore_btn.pack(side="left", padx=(5, 0))
        Tooltip(adv_restore_btn, "Load saved defaults from ~/.peekdocsrc into the GUI", anchor="above")

        adv_reset_defaults_btn = ctk.CTkButton(
            adv_bottom_frame, text="Restore Factory Settings", width=130,
            fg_color="#DC2626", hover_color="#B91C1C",
            command=self._reset_saved_defaults,
            font=ctk.CTkFont(size=13),
        )
        adv_reset_defaults_btn.pack(side="right", padx=(0, 5))
        Tooltip(adv_reset_defaults_btn, "Delete ~/.peekdocsrc and return all settings to factory defaults. This erases all saved preferences — search mode, file types, output formats, and everything else. The app will start fresh next time as if newly installed. Your documents and search history are not affected", anchor="above")

        adv_inspect_btn = ctk.CTkButton(
            adv_bottom_frame, text="Inspect .peekdocsrc", width=130,
            command=self._inspect_settings,
            font=ctk.CTkFont(size=13),
        )
        adv_inspect_btn.pack(side="right", padx=(0, 5))
        Tooltip(adv_inspect_btn, "View the current saved settings in ~/.peekdocsrc (read-only). These settings are saved by 'Save As Defaults' and apply to: search mode (AND/OR), recursive, regex, fuzzy, wildcard, whole word, OCR, inverse, file types, exclude terms, word proximity, context lines, max matches, max file size, CPU cores, output formats, output directory, timestamp, quiet mode, and appearance. They persist across sessions and are used as defaults when the app starts", anchor="above")



    def _build_progress_area(self):
        """Build the progress bar, status label, and results preview pane."""
        self.progress_bar = ctk.CTkProgressBar(
            self._input_frame, mode="indeterminate", height=18,
            progress_color=("#2196F3", "#1976D2"),
            fg_color=("#E0E0E0", "#3A3A3A"),
            corner_radius=5,
            indeterminate_speed=1.2,
        )
        self.progress_bar.set(0)
        # Starts hidden — shown only during search

        import tkinter as _tk_status
        status_row = ctk.CTkFrame(self._input_frame, fg_color="transparent")
        status_row.grid(row=4, column=0, columnspan=3, padx=(10, 15), pady=(0, 4), sticky="ew")

        _status_label_size = 16 if sys.platform == "win32" else 14
        status_label_left = ctk.CTkLabel(
            status_row, text="Status:", font=ctk.CTkFont(size=_status_label_size, weight="bold"),
        )
        status_label_left.pack(side="left", padx=(0, 5))
        Tooltip(status_label_left, "Search status — shows progress during search and results summary when complete")

        _status_font_size = 16 if sys.platform == "win32" else 14
        self.status_label = ctk.CTkLabel(
            status_row, text="", font=ctk.CTkFont(size=_status_font_size), anchor="w",
            wraplength=550, text_color=("blue", "#66BBFF"), justify="left",
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
        Tooltip(self._matched_files_link, "Click to see the list of files that matched — double-click a filename to open it, or use View Text to see the extracted content with highlighted matches. The number of files shown may be affected by the Max Matches setting in Advanced Search Options")

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
        self.preview_frame = ctk.CTkFrame(self._input_frame)
        self.preview_frame.grid(
            row=7, column=0, columnspan=3, padx=5, pady=(5, 0), sticky="nsew"
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
        self._clear_preview_btn = ctk.CTkButton(
            preview_header, text="Clear Preview", width=100,
            font=ctk.CTkFont(size=11),
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=self._clear_preview,
        )
        self._clear_preview_btn.pack(side="left", padx=(8, 0))
        Tooltip(self._clear_preview_btn, "Clear the Results Preview pane — removes all visible match data from the screen. Useful if you've finished reviewing and don't want results visible. Does not delete report files on disk")

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
            padx=8, pady=5, height=8,
        )
        self.preview_text.pack(side="left", fill="both", expand=True)
        preview_scroll.config(command=self.preview_text.yview)
        Tooltip(self.preview_text, "Results Preview: Shows search matches with highlighted terms. Right-click to copy text. Double-click a filename to open it in its default application.")

        # Apply dark theme to preview area if in dark mode
        if ctk.get_appearance_mode() == "Dark":
            preview_text_frame.configure(bg="#2b2b2b")
            self.preview_text.configure(bg="#1e1e1e", fg="#e0e0e0", insertbackground="#e0e0e0")
            preview_scroll.configure(bg="#404040", troughcolor="#2b2b2b")

        # Configure tags for highlighting
        _is_dark = ctk.get_appearance_mode() == "Dark"
        self.preview_text.tag_configure("filename", font=("Courier", 11, "bold"),
                                        foreground="#66BBFF" if _is_dark else "#1a73e8")
        self.preview_text.tag_configure("match", background="#FFFF00", foreground="#000000")
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
                                            text_color=("blue", "#66BBFF"))
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
                        from peekdocs.gui._helpers import safe_open_file
                        warning = safe_open_file(filepath)
                        if warning:
                            self._show_error(warning)
                    return
        self.preview_text.bind("<Double-1>", _preview_open_file)



    def _build_open_report(self):
        """Build the Matched Files and View Report buttons."""
        # Buttons are children of the search tab, gridded directly at row 6
        self.matched_files_button = ctk.CTkButton(
            self._input_frame,
            text="Matched Files",
            width=140,
            command=self._show_matched_files_popup,
            font=ctk.CTkFont(size=13),
        )
        Tooltip(self.matched_files_button, "View the list of files that contained matches (click a file to open it). The number of files shown here may be affected by the Max Matches setting in Advanced Search Options — if the report is capped, only files with matches within the cap are listed")

        self.report_frame = ctk.CTkFrame(self._input_frame, fg_color="transparent")
        import tkinter as _tk_step4
        _step_lbl_4 = _tk_step4.Label(self.report_frame, text=" Step 4 ", font=("TkDefaultFont", 14, "bold"),
                                       fg="white", bg="#2196F3")
        _step_lbl_4.pack(side="left", padx=(0, 8))
        Tooltip(_step_lbl_4, "View Report — open the highlighted results report. Additional formats (CSV, JSON, PDF, HTML) can be enabled in Advanced Search Options", anchor="above")

        btn_font = ctk.CTkFont(size=12)
        btn_w = 60
        _report_color_note = "Green = report file exists and is ready to open. Red = not generated (enable in Advanced Search Options under Output Formats)."
        self.report_btn_docx = ctk.CTkButton(
            self.report_frame, text="DOCX", width=btn_w, font=btn_font,
            command=lambda: self._open_report_format("docx"),
        )
        Tooltip(self.report_btn_docx, f"Open the highlighted Word report (.docx) — every match in yellow with context. {_report_color_note}", anchor="above")
        self.report_btn_txt = ctk.CTkButton(
            self.report_frame, text="TXT", width=btn_w, font=btn_font,
            command=lambda: self._open_report_format("txt"),
        )
        Tooltip(self.report_btn_txt, f"Open the plain-text report (.txt). {_report_color_note}", anchor="above")
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
        self.report_btn_html = ctk.CTkButton(
            self.report_frame, text="HTML", width=btn_w, font=btn_font,
            command=lambda: self._open_report_format("html"),
        )
        Tooltip(self.report_btn_html, f"Open the HTML report — view in any web browser. The file is stored locally on your computer, not on the internet — nothing is uploaded or made public. {_report_color_note}", anchor="above")

        self.report_delete_cb = ctk.CTkCheckBox(
            self.report_frame, text="Delete on Close",
            variable=self.delete_reports_var,
            onvalue="on", offvalue="off",
            command=lambda: self._save_ui_preference("delete_reports_on_close", self.delete_reports_var.get() == "on"),
            font=ctk.CTkFont(size=12),
        )
        Tooltip(self.report_delete_cb, "Automatically delete all search result files (peekdocs_standard_results.*, peekdocs_regex_results.*, peekdocs_suite_results.*) and the search index (.peekdocs.db) in every folder searched during the session when you close peekdocs. The index is included because it contains extracted text from every indexed file. You can check or uncheck this at any time — it only matters at the moment you close the app. Saved reports (peekdocs_report_*) and accumulated reports (peekdocs_accumulated_*) are never deleted", anchor="above")

        self._delete_everything_btn = ctk.CTkButton(
            self.report_frame, text="Delete Everything Now", width=170,
            font=ctk.CTkFont(size=12),
            fg_color="#0D9488", hover_color="#0B7A70", text_color="white",
            command=self._delete_everything_now,
        )
        Tooltip(self._delete_everything_btn, "Immediately delete all peekdocs result files and search indexes in every folder searched during the session, clear the Results Preview, clear search history, and blank out search terms and folder fields. Deletes report files from the most recent search and clears displayed results to reduce leftover local artifacts. The search index (.peekdocs.db) is included because it contains extracted text from every indexed file. Saved reports, accumulated reports, saved searches, and settings are not affected. Your documents and personal files are never touched", anchor="above")



    def _build_index_panel(self):
        """Build the Manage Indexes popup window with build, delete, status, and auto-refresh controls."""
        # Manage Indexes button moved to Tools menu

        # Create popup window for Manage Indexes
        self.index_window = ctk.CTkToplevel(self)
        self.index_window.title("Indexes")
        self.index_window.after(100, lambda: self.index_window.title("Indexes"))
        self.index_window.geometry("580x310")
        self.index_window.resizable(True, True)
        self.index_window.protocol("WM_DELETE_WINDOW", self._close_index_window)
        self.index_window.withdraw()
        self.after(10, self.index_window.withdraw)
        self.index_visible = False

        idx_frame = ctk.CTkFrame(self.index_window)
        idx_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header with description and ? help
        idx_header = ctk.CTkFrame(idx_frame, fg_color="transparent")
        idx_header.pack(fill="x", padx=5, pady=(0, 5))
        ctk.CTkLabel(
            idx_header,
            text="Build a search index for faster repeated searches.\nAll indexes are recursive — every subfolder is included automatically,\nregardless of the Recursive checkbox setting.\nThe status line on the main screen shows index build progress.",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray50"),
        ).pack(side="left")

        # Show which folder the index applies to
        self._index_folder_label = ctk.CTkLabel(
            idx_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray50"),
        )
        self._index_folder_label.pack(anchor="w", padx=5, pady=(0, 5))
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



    def _build_bottom_row(self):
        """Build the bottom toolbar with help, about, tools, and close."""
        self.bottom_frame = ctk.CTkFrame(self._input_frame, fg_color="transparent")
        self.bottom_frame.grid(
            row=9, column=0, columnspan=3, padx=15, pady=(0, 8), sticky="sew"
        )

        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=1)
        self.bottom_frame.grid_columnconfigure(2, weight=1)

        # Left group
        left_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="w")

        self._readme_button = ctk.CTkButton(
            left_frame,
            text="README",
            width=70,
            fg_color="transparent",
            text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=lambda: webbrowser.open("https://github.com/exbuf/peekdocs/tree/main"),
            font=ctk.CTkFont(size=13),
        )
        self._readme_button.pack(side="left")
        Tooltip(self._readme_button, "Open the peekdocs README on GitHub — features, installation, security, and more", anchor="above")

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
                                 foreground="#999999" if ctk.get_appearance_mode() == "Dark" else "gray40")
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
            menu.add_command(label="Indexes — build, delete, and refresh search indexes", command=self._toggle_index_options)
            menu.add_command(label="Schedule Search — generate a cron or Task Scheduler command", command=self._open_schedule_search)
            menu.add_command(label="Search History — log of past searches and results", command=self._show_search_history)
            # Search Suites moved to main screen next to Wizard
            _dark_sep()
            # App management (alphabetical)
            menu.add_command(label="All Collections — find saved searches across all folders", command=self._show_all_collections)
            menu.add_command(label="View All peekdocs Files — list every peekdocs-created file in the Search Folder", command=self._show_app_files)
            menu.add_command(label="Error Log — open peekdocs_errors.log", command=self.open_error_log)
            _dark_sep()
            # Cleanup
            menu.add_command(label="Clear Files — choose which peekdocs files to delete", command=self._clear_files)
            menu.add_command(label="Clean Folder — delete peekdocs files in any folder", command=self._clean_folder)
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
            # Appearance mode (Dark / Light / System)
            current_mode = ctk.get_appearance_mode()
            for mode in ["System", "Light", "Dark"]:
                marker = " \u2713" if mode == current_mode else ""
                menu.add_command(
                    label=f"Appearance: {mode}{marker}",
                    command=lambda m=mode: self._set_appearance_mode(m),
                )
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
        Tooltip(self._tools_btn, "File Inventory, Duplicates, Large Files, Empty Files, Recent Changes, Protected Files, Search History, Bookmarks, App Files, and more. Linux: hold mouse button and drag to select — click-to-open is a known Linux/tkinter limitation", anchor="above-left")

        hover_label = "Hover: ON" if Tooltip.enabled else "Hover: OFF"
        self._hover_toggle_btn = ctk.CTkButton(
            right_frame,
            text=hover_label,
            width=80,
            fg_color="transparent",
            text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=self._toggle_tooltips,
            font=ctk.CTkFont(size=13),
        )
        self._hover_toggle_btn.pack(side="right", padx=5)
        Tooltip(self._hover_toggle_btn, "Enable or disable hover text (tooltips) on all buttons and controls", anchor="above-left")

        # Keep references for tooltip toggle (used by _toggle_tooltips)
        self.tooltip_toggle_btn = None
        self.view_error_log_bottom = None


    # ── Actions ──────────────────────────────────────────────



    def toggle_advanced(self):
        """Toggle the Advanced Search Options window open or closed."""
        if self.advanced_visible:
            self._close_advanced_window()
        else:
            self.advanced_window.deiconify()
            self.advanced_window.lift()
            self.advanced_toggle.configure(text="Advanced")
            self.advanced_visible = True



    def _close_advanced_window(self):
        """Hide the Advanced Search Options window and update the toggle button."""
        self.advanced_window.withdraw()
        self.advanced_toggle.configure(text="Advanced")
        self.advanced_visible = False



    def _toggle_index_options(self):
        """Toggle the Manage Indexes window open or closed."""
        if self.index_visible:
            self._close_index_window()
        else:
            self.index_window.deiconify()
            self.index_window.lift()
            if hasattr(self, "index_toggle_btn"):
                self.index_toggle_btn.configure(text="\u25bc Indexes")
            # Show current search folder
            if hasattr(self, "_index_folder_label"):
                folder = self.folder_entry.get().strip() or "(none)"
                self._index_folder_label.configure(text=f"Index for Search Folder: {folder}")
            self.index_visible = True
            self._update_index_button_color()



    def _close_index_window(self):
        """Hide the Indexes window and update the toggle button."""
        self.index_window.withdraw()
        if hasattr(self, "index_toggle_btn"):
            self.index_toggle_btn.configure(text="\u25b6 Indexes")
        self.index_visible = False



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
            self._close_suite_popup_if_open()



    def _add_folder(self):
        """Add another folder to the search folder field (multi-folder search)."""
        current = self.folder_entry.get().strip()
        # Use the last folder in the list as the initial dir for the picker
        parts = [p.strip() for p in current.split(";") if p.strip()]
        initial = parts[-1] if parts else os.path.expanduser("~")
        folder = filedialog.askdirectory(initialdir=initial)
        if folder:
            folder = os.path.normpath(folder)
            if folder not in parts:
                parts.append(folder)
                self.folder_entry.delete(0, "end")
                self.folder_entry.insert(0, "; ".join(parts))
                self._clear_specific_file()
                self._close_suite_popup_if_open()

    def _close_suite_popup_if_open(self):
        """Close the Search Suites popup if it's open — folder changed."""
        if hasattr(self, "_suite_popup") and self._suite_popup and self._suite_popup.winfo_exists():
            self._suite_popup.destroy()
            self._suite_popup = None

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
                text_color=("blue", "#66BBFF"),
            )
            self._clear_file_btn.pack(side="left", padx=(2, 6), pady=4)



    def _clear_specific_file(self):
        """Clear the specific file selection and revert to full folder search."""
        self.specific_files_entry.delete(0, "end")
        self._clear_file_btn.pack_forget()
        self.status_label.configure(
            text="File selection cleared — searching entire folder.",
            text_color=("blue", "#66BBFF"),
        )



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
            self.bell()
            self._show_error("No recent searches yet. Run a search first — your last 10 searches will appear here.")
            return
        popup, _dark = self._themed_toplevel()
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

        _recent_header = tk.Frame(popup)
        _recent_header.pack(fill="x", padx=10, pady=(8, 4))
        tk.Label(_recent_header, text="Click a search to re-use it:",
                 font=("TkDefaultFont", 11), fg="gray").pack(side="left")
        ctk.CTkButton(
            _recent_header, text="?", width=28, height=24,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=lambda: self._show_recent_searches_help(popup),
        ).pack(side="right")

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

        import tkinter as _tk_recent
        top_btn_row = _tk_recent.Frame(popup)
        top_btn_row.pack(fill="x", padx=10, pady=(0, 4))
        ctk.CTkButton(top_btn_row, text="Use", width=70, font=ctk.CTkFont(size=12), command=_select).pack(side="left")

        def _clear_recent():
            from tkinter import messagebox
            if not messagebox.askyesno("Clear Recent Searches",
                                       "Clear all recent searches?\n\nThis cannot be undone.",
                                       parent=popup):
                return
            self._recent_searches.clear()
            self._save_ui_preference("recent_searches", [])
            popup.destroy()
            self.status_label.configure(text="Recent searches cleared.", text_color=("blue", "#66BBFF"))

        ctk.CTkButton(top_btn_row, text="Clear", width=70, font=ctk.CTkFont(size=12),
                       fg_color="#CC3333", hover_color="#AA2222",
                       command=_clear_recent).pack(side="right")

        cancel_row = _tk_recent.Frame(popup)
        cancel_row.pack(pady=(0, 8))
        ctk.CTkButton(cancel_row, text="Cancel", width=70, font=ctk.CTkFont(size=12),
                       fg_color="transparent", text_color=("gray30", "gray70"),
                       hover_color=("gray90", "gray25"), command=popup.destroy).pack()

        self._apply_dark_theme(popup)

    def _show_recent_searches_help(self, parent):
        """Show help for the Recent Searches popup."""
        import tkinter as tk
        help_win, _dark = self._themed_toplevel(parent)
        help_win.title("Recent Searches — Help")
        help_win.geometry("580x400")
        help_win.resizable(True, True)
        help_win.transient(parent)
        try:
            help_win.grab_set()
        except Exception:
            help_win.after(150, lambda: help_win.grab_set() if help_win.winfo_exists() else None)

        # Pack Close first so it anchors to the bottom
        _close_btn_recent = ctk.CTkButton(
            help_win, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=help_win.destroy, font=ctk.CTkFont(size=12),
        )
        _close_btn_recent.pack(side="bottom", pady=(5, 10))

        txt_frame = tk.Frame(help_win)
        txt_frame.pack(fill="both", expand=True)
        txt = tk.Text(txt_frame, wrap="word", font=("TkDefaultFont", 12),
                      padx=15, pady=10, spacing3=4)
        txt.pack(fill="both", expand=True)

        def b(text):
            txt.insert("end", text + "\n", "bold")
        def n(text):
            txt.insert("end", text + "\n")

        txt.tag_configure("bold", font=("TkDefaultFont", 12, "bold"))

        b("What are Recent Searches?")
        n("The last 10 search terms you typed are remembered here so")
        n("you can quickly re-use them without retyping. Select one")
        n("and click Use (or double-click) to fill the search bar.\n")

        b("How they're stored")
        n("Recent searches are saved to ~/.peekdocsrc and persist")
        n("across sessions. They're available every time you open")
        n("the app.\n")

        b("Recent Searches vs Search History")
        n("\u2022 Recent Searches (this popup) \u2014 last 10 search terms,")
        n("  persists across sessions. For quick re-use.")
        n("\u2022 Search History (Tools menu) \u2014 saved to disk in")
        n("  ~/.peekdocs_history.json, persists across sessions,")
        n("  includes date, match count, file count, and elapsed time.")
        n("  For reviewing past searches.\n")

        b("Clear button")
        n("Clears the recent searches list from memory and disk.")
        n("Does NOT affect Search History.")

        b("\nSaved Searches")
        n("To save a search permanently so you can reload it later,")
        n("use the Save button on the main screen. Saved searches")
        n("persist across sessions and can be grouped into suites.")

        txt.configure(state="disabled")
        self._apply_dark_theme(help_win)

    def _save_ui_preference(self, key, value):
        """Auto-save a single UI preference to ~/.peekdocsrc."""
        try:
            from peekdocs.cli import _load_config, _save_config
            config = _load_config()
            config[key] = value
            _save_config(config)
        except Exception:
            pass

    def _set_appearance_mode(self, mode):
        """Switch between Dark, Light, and System appearance modes."""
        ctk.set_appearance_mode(mode)
        self._appearance_mode = mode
        self._save_ui_preference("appearance_mode", mode)
        # Close ephemeral tool popups — they were themed at creation
        # time and cannot be reliably re-themed in place.  Skip
        # persistent windows (advanced_window, index_window) that
        # are part of the main UI.
        import tkinter as tk
        _keep = set()
        for attr in ("advanced_window", "index_window"):
            w = getattr(self, attr, None)
            if w is not None:
                _keep.add(str(w))
        for child in self.winfo_children():
            if isinstance(child, tk.Toplevel) and child.winfo_exists():
                if str(child) not in _keep:
                    child.destroy()
        # Update the Results Preview pane colors
        if hasattr(self, "preview_text"):
            _dark = ctk.get_appearance_mode() == "Dark"
            self.preview_text.configure(
                bg="#1e1e1e" if _dark else "white",
                fg="#e0e0e0" if _dark else "black",
                insertbackground="#e0e0e0" if _dark else "black",
            )
            self.preview_text.tag_configure(
                "filename", foreground="#66BBFF" if _dark else "#1a73e8")
            try:
                self.preview_text.master.configure(bg="#2b2b2b" if _dark else "white")
            except Exception:
                pass

    def _themed_toplevel(self, parent=None):
        """Create a themed Toplevel window.

        Returns (window, is_dark).

        Uses CTkToplevel for compatibility with customtkinter's event
        system (plain tk.Toplevel crashes on Windows because CTk
        expects the block_update_dimensions_event attribute).

        On macOS in dark mode, also sets the tk option database so
        plain tk child widgets are created with dark colors from the
        start and places the window offscreen until the caller
        repositions it.
        """
        import sys as _sys_tt
        win = ctk.CTkToplevel(parent or self)
        # Windows: popups appear behind the main window without these
        if _sys_tt.platform == "win32":
            win.transient(parent or self)
            win.lift()
            win.after(50, win.lift)
            win.after(100, win.focus_force)
        _is_dark = ctk.get_appearance_mode() == "Dark"
        if _is_dark and _sys_tt.platform != "win32":
            # macOS/Linux: place offscreen while building widgets to
            # reduce white flash.  The popup's own geometry() call
            # moves it onscreen after setup is complete.
            win.geometry("+99999+99999")
            _bg = "#2b2b2b"
            _fg = "#e0e0e0"
            _entry_bg = "#3a3a3a"
            _btn_bg = "#555555"
            win.configure(bg=_bg)
            win.option_add("*Background", _bg)
            win.option_add("*Foreground", _fg)
            win.option_add("*Entry.Background", _entry_bg)
            win.option_add("*Entry.Foreground", _fg)
            win.option_add("*Entry.insertBackground", _fg)
            win.option_add("*Listbox.Background", "#2b2b2b")
            win.option_add("*Listbox.Foreground", "white")
            win.option_add("*Text.Background", _entry_bg)
            win.option_add("*Text.Foreground", _fg)
            win.option_add("*Text.insertBackground", _fg)
            win.option_add("*Button.Background", _btn_bg)
            win.option_add("*Button.Foreground", "white")
            win.option_add("*Checkbutton.Background", _bg)
            win.option_add("*Checkbutton.Foreground", _fg)
            win.option_add("*Checkbutton.selectColor", _entry_bg)
            win.option_add("*Radiobutton.Background", _bg)
            win.option_add("*Radiobutton.Foreground", _fg)
            win.option_add("*Radiobutton.selectColor", _entry_bg)
            win.option_add("*Label.Background", _bg)
            win.option_add("*Label.Foreground", _fg)
            win.option_add("*Scrollbar.Background", _btn_bg)
            win.option_add("*Scrollbar.troughColor", _bg)
            win.option_add("*Canvas.Background", _bg)

            def _ensure_onscreen(_w=win, _self=self):
                """If the popup is still offscreen, center it over the main window."""
                try:
                    if not _w.winfo_exists():
                        return
                    _w.update_idletasks()
                    if _w.winfo_x() >= 99000 or _w.winfo_y() >= 99000:
                        w = _w.winfo_reqwidth()
                        h = _w.winfo_reqheight()
                        x = _self.winfo_rootx() + (_self.winfo_width() - w) // 2
                        y = _self.winfo_rooty() + (_self.winfo_height() - h) // 2
                        _w.geometry(f"+{max(0, x)}+{max(0, y)}")
                except Exception:
                    pass

            # Use a short delay so the caller has time to build widgets
            # and optionally set its own geometry before the safety net fires.
            win.after(200, _ensure_onscreen)
        if _is_dark:
            return win, True
        return win, False

    @staticmethod
    def _is_dark_mode():
        """Return True if the current appearance is Dark."""
        return ctk.get_appearance_mode() == "Dark"

    @staticmethod



    def _apply_dark_theme(widget):
        """Recursively apply dark colors to plain tk widgets if Dark mode is active."""
        if ctk.get_appearance_mode() != "Dark":
            return
        import tkinter as tk
        _bg = "#2b2b2b"
        _fg = "#e0e0e0"
        _entry_bg = "#3a3a3a"
        _btn_bg = "#404040"
        # Backgrounds that are intentionally colored (severity badges, etc.)
        # — don't override these with the dark background
        _keep_bg = {"#FF4444", "#ff4444", "#FFB800", "#ffb800", "#4488FF",
                     "#4488ff", "#FF6B35", "#ff6b35", "#CC3333", "#cc3333",
                     "#CC0000", "#cc0000", "#2196F3", "#888888", "#666666"}

        def _apply(w):
            cls = w.winfo_class()
            try:
                if cls in ("Frame", "Labelframe"):
                    w.configure(bg=_bg)
                elif cls == "Label":
                    cur_bg = str(w.cget("bg"))
                    if cur_bg.upper() in {c.upper() for c in _keep_bg}:
                        pass  # Intentionally colored — leave it alone
                    else:
                        w.configure(bg=_bg)
                        # Set fg to light unless it's intentionally colored
                        cur_fg = str(w.cget("fg"))
                        if cur_fg.lower() not in ("red", "#cc0000", "#cc3333",
                                                   "green", "#008000", "blue"):
                            w.configure(fg=_fg)
                elif cls == "Entry":
                    w.configure(bg=_entry_bg, fg=_fg, insertbackground=_fg)
                elif cls == "Checkbutton":
                    w.configure(bg=_bg, fg=_fg, selectcolor=_entry_bg,
                                activebackground=_bg, activeforeground=_fg)
                elif cls == "Button":
                    # macOS ignores bg/fg on native buttons; set
                    # highlightbackground to control the border color only
                    import sys as _sys_dt
                    if _sys_dt.platform == "darwin":
                        w.configure(highlightbackground=_bg)
                    else:
                        w.configure(bg="#555555", fg="white",
                                    activebackground="#666666", activeforeground="white")
                elif cls == "Radiobutton":
                    w.configure(bg=_bg, fg=_fg, selectcolor=_entry_bg,
                                activebackground=_bg, activeforeground=_fg)
                elif cls == "Text":
                    w.configure(bg=_entry_bg, fg=_fg, insertbackground=_fg)
                elif cls == "Toplevel":
                    w.configure(bg=_bg)
                elif cls == "Canvas":
                    w.configure(bg=_bg)
                elif cls == "Scrollbar":
                    w.configure(bg=_btn_bg, troughcolor=_bg)
                elif cls == "TCombobox":
                    # ttk.Combobox uses ttk styling
                    from tkinter import ttk as _ttk_dt
                    style = _ttk_dt.Style()
                    style.configure("Dark.TCombobox",
                                    fieldbackground=_entry_bg,
                                    background=_btn_bg,
                                    foreground=_fg,
                                    selectbackground="#555555",
                                    selectforeground=_fg)
                    style.map("Dark.TCombobox",
                              fieldbackground=[("readonly", _entry_bg)],
                              foreground=[("readonly", _fg)])
                    w.configure(style="Dark.TCombobox")
            except Exception:
                pass
            for child in w.winfo_children():
                _apply(child)

        _apply(widget)



    def _toggle_tooltips(self):
        """Toggle hover tooltip visibility on or off."""
        Tooltip.enabled = not Tooltip.enabled
        self._save_ui_preference("hover_text", Tooltip.enabled)
        if hasattr(self, "_hover_toggle_btn"):
            self._hover_toggle_btn.configure(
                text="Hover: ON" if Tooltip.enabled else "Hover: OFF"
            )



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

        popup, _dark = self._themed_toplevel()
        popup.title("Load Settings")
        popup.resizable(False, False)
        popup.transient(self)
        self._load_search_popup = popup

        # Center on the main window (matches the Save popup's positioning).
        # Width is approximate — the listbox sizes itself once packed; the
        # popup re-centers cleanly even if the actual width differs slightly.
        approx_w = 320
        x = self.winfo_rootx() + (self.winfo_width() - approx_w) // 2
        y = self.winfo_rooty() + 120
        popup.geometry(f"+{x}+{y}")

        frame = ctk.CTkFrame(popup)
        frame.pack(fill="both", expand=True)

        ctk.CTkLabel(frame, text=f"Saved searches in: {os.path.basename(folder) or folder}",
                     font=ctk.CTkFont(size=10), text_color="gray").pack(
            padx=4, pady=(4, 0), anchor="w"
        )

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
                    text_color=("blue", "#66BBFF"),
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
                text_color=("blue", "#66BBFF"),
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
        self._apply_dark_theme(popup)



    def _refresh_load_search_menu(self):
        """No-op — popup rebuilds its list each time it opens."""
        pass


