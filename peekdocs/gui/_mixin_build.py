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


class _UpwardOptionMenu(ctk.CTkOptionMenu):
    """CTkOptionMenu that opens its dropdown ABOVE the button instead
    of below — used for the App Size + Language pickers in the bottom
    toolbar, where a downward menu would overflow the window edge.

    CTk's stock _open_dropdown_menu positions the dropdown at
    (rootx, rooty + current_height). We override to position at
    (rootx, rooty - estimated_dropdown_height) so it grows upward."""

    def _open_dropdown_menu(self):
        n = len(self._values) if self._values else 1
        # 26 px per item matches CTk's default dropdown row height
        # (24 px content + 2 px gap); +6 px chrome at top + bottom.
        dropdown_h = n * 26 + 6
        self._dropdown_menu.open(
            self.winfo_rootx(),
            self.winfo_rooty() - dropdown_h,
        )


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
        tk.Label(inner, text="Search across 100+ file types — Word docs, PDFs, spreadsheets, emails, source code, archives, and more. All offline.",
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
        _step(2, "Type what you're looking for", "Enter your search terms in the '2. Search Terms' field. Example: budget revenue. By default, finding any of the terms is enough; to fine-tune behavior (AND vs OR matching, whole-word, regex, fuzzy, file-type filters, and the rest) expand Advanced Search Options below and adjust there.\n\nFour small buttons sit just to the right of the search bar on the same row:\n\n  • ▼ Recent — your last 10 searches. Each entry captures the FULL search context (terms + folder + every Advanced Search Options setting), so selecting one from the popup restores all of those in one click. ↑ / ↓ in the search bar walk through the same list but only copy the terms text into the bar, leaving your current Advanced options untouched.\n  • ▶ Save — save the current search to the folder's collection under a name so you can reload it later. Saved searches survive across sessions and can be grouped into Search Suites.\n  • ▶ Reload — open the popup to load (or delete) a saved search by name.\n  • ? — quick help describing the Save / Reload workflow.")
        _step(3, "Use Advanced Search Options below to configure search parameters", "Step 3 on the main page is a pointer to the inline Advanced Search Options panel — click the ▶ Advanced Search Options header in the left pane to expand it. Inside you'll find: AND/OR mode, Recursive, Whole Word, Regex, Fuzzy, Wildcard, OCR, Inverse, Expression mode, Use Index, file-type filters, exclude terms, proximity, context lines, CPU cores, max matches, max file size, range filters, specific-file list, output directory, the optional output formats CSV / JSON / PDF / HTML (under 'Also ==>'), timestamp filenames, Delete on Close, Clear history on close, Restrict permissions, and Notify on Search Complete.\n\nTXT and DOCX reports are always generated. The Open Report row in the left pane lights its buttons green for each format the most recent search produced — click any green button to open that format. Reports stay on your computer; peekdocs avoids opening them in Google Docs, Apple Pages, or any cloud-based application that may upload your data.\n\nWhich output formats apply where: the CSV / JSON / PDF / HTML checkboxes apply to Standard Search only. Search Suites have their own HTML / CSV / JSON / PDF picker inside the Search Suites popup. Regex Search always writes just TXT and DOCX. After any Suite or Regex run, the Open Report buttons re-point to whatever that run produced, so a button colored red just means that format wasn't generated by the most recent search — not that anything is broken.")
        _step(4, "Click Run Standard Search (or Search Suites / Regex Search)", "Three Run buttons share the Step 4 row:\n\n  • 🔍 Run Standard Search (blue, large) — runs your typed terms against the current Advanced Search Options settings (AND/OR, Recursive, Whole Word, Use Index, regex, fuzzy, file-type filters, output formats, and the rest). This is the everyday button.\n  • Search Suites (green, square) — opens a popup of named suites (groups of saved searches) that run together as a single combined report. Each saved search inside a suite carries its own settings, so the Advanced Search Options on the main page do NOT apply to suite runs. The suite popup has its own HTML / CSV / JSON / PDF picker.\n  • Regex Search (orange, square) — opens the multi-pattern regex collections popup. Each pattern in a collection is independent and runs as its own regex, with TXT and DOCX as the only output formats. Use this when you need several regex patterns at once; the Standard Search Regex checkbox is for a single pattern only.\n\nAfter the search, results appear with matches highlighted in yellow. The right pane shows a results headline (files searched · matches · elapsed time), Matched Files / Excluded Files count buttons, a Chart button (top files by match count), and the matches themselves. On the left pane, click any green button in the Open Report row to open the highlighted DOCX, TXT, CSV, JSON, PDF, or HTML report (DOCX opens in Microsoft Word or LibreOffice; HTML in your browser).")

        # Tip about tooltips — safety-net hint so users know how to discover button behavior.
        # Body uses tk.Text (not tk.Label) so the "?" can be colored blue inline to match
        # the actual help-button color — tk.Label is single-color-only.
        tip_frame = tk.Frame(inner)
        tip_frame.pack(fill="x", padx=30, pady=(15, 0))
        tk.Label(tip_frame, text="\U0001f4a1  Tip:", font=("TkDefaultFont", 13, "bold"), fg="#E65100").pack(side="left", anchor="n", padx=(0, 8))
        tip_body = tk.Text(
            tip_frame, font=("TkDefaultFont", 12), wrap="word",
            borderwidth=0, highlightthickness=0, height=5, width=80,
            cursor="arrow", bg=tip_frame.cget("bg"),
        )
        tip_body.tag_configure("gray", foreground="gray")
        tip_body.tag_configure("blue", foreground="#1565C0", font=("TkDefaultFont", 12, "bold"))
        tip_body.insert("end", "Hover over any button, checkbox, or field on the main page or any popup to see a tooltip explaining what it does. Most screens also have a ", "gray")
        tip_body.insert("end", "?", "blue")
        tip_body.insert("end", " button that opens a detailed help page. If tooltips feel noisy, use the Tooltips: ON/OFF button at the bottom-right to switch them off; turn them back on anytime.", "gray")
        tip_body.configure(state="disabled")
        tip_body.pack(side="left", fill="both", expand=True)

        tk.Label(inner, text="", font=("TkDefaultFont", 6)).pack()  # spacer

        tk.Label(inner, text="Want to do more?", font=("TkDefaultFont", 16, "bold")).pack(pady=(15, 5), **pad)

        features = [
            ("\U0001f9ea  Search Wizard", "Tools → Search Wizard. Pick a search type (phone, email, dollar range, date, etc.) and the wizard configures it for you.", "#8B5CF6"),
            ("\U0001f50e  Save and Reload Searches", "▶ Save the current search by name; ▶ Reload to recall the full configuration later.", "#2196F3"),
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
        b("peekdocs lets you search across 100+ file types \u2014 Word docs,")
        b("PDFs, spreadsheets, emails, calendars, contacts, source code,")
        b("archives, and more \u2014 all at once, all offline.")
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
        st("Step 3: Use Advanced Search Options below to configure search parameters")
        b("Step 3 on the main page is a pointer to the inline")
        b("Advanced Search Options panel. Click the ▶ Advanced Search")
        b("Options header in the left pane to expand it. Inside you'll")
        b("find AND/OR mode, Recursive, Whole Word, Regex, Fuzzy,")
        b("Wildcard, OCR, Inverse, Expression, Use Index, file-type")
        b("filters, exclude terms, proximity, context lines, CPU cores,")
        b("max matches, max file size, range filters, specific-file")
        b("list, output directory, the optional output formats")
        b("(DOCX / CSV / JSON / PDF / HTML under 'Also ==>'),")
        b("timestamp filenames, Delete on Close, Clear history on close,")
        b("Restrict permissions, and Notify on Search Complete.")
        blank()
        b("TXT is always written and feeds the in-pane preview. DOCX")
        b("defaults ON; uncheck it (or pass --no-docx on the CLI) to")
        b("skip the .docx report. CSV / JSON / PDF / HTML default OFF —")
        b("check the ones you want. Search Suites have their own format")
        b("picker inside the Suites popup; Regex Search always writes")
        b("just TXT and DOCX. After a Suite or Regex run, the Open")
        b("Report buttons (on the left pane below the status row) re-")
        b("point to whatever that run produced — a red button just")
        b("means that format wasn't generated by the most recent search.")
        blank()
        st("Step 4: Click Run Standard Search (or Search Suites / Regex Search)")
        b("Three Run buttons share the Step 4 row:")
        b("• 🔍 Run Standard Search (blue) — runs the typed terms with")
        b("  the current Advanced Search Options settings.")
        b("• Search Suites (green square) — runs a named suite of saved")
        b("  searches together as one combined report; each saved search")
        b("  inside the suite carries its own settings, so Advanced")
        b("  Search Options on the main page do NOT apply to suite runs.")
        b("• Regex Search (orange square) — runs a saved regex collection")
        b("  where each pattern is independent. Always writes just")
        b("  TXT and DOCX.")
        blank()
        b("peekdocs scans every supported file in the folder and shows")
        b("a results headline (files searched · matches · elapsed time)")
        b("at the top of the right pane. Matches appear with yellow")
        b("highlighting in the preview below, and are saved to:")
        e("peekdocs_standard_results.txt   (always written)")
        e("peekdocs_standard_results.docx  (Word, with highlights — optional)")
        blank()
        b("Click any green button in the Open Report row on the LEFT")
        b("pane to open the corresponding report. TXT sits leftmost")
        b("(it's the always-written report); DOCX next; then CSV / JSON")
        b("/ PDF / HTML if they were enabled.")
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
        b("Once you've configured a search you'll want to reuse, click")
        b("the ▶ Save button on the Step 2 row to store it by name.")
        b("Click ▶ Reload later to recall it with one click — terms,")
        b("folder, and every Advanced Search Options setting come back.")
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
        from peekdocs.i18n import t as _t
        # Page-header row — "Main page" on the left; App Size + Language
        # dropdowns are added on the right in _build_progress_area.
        self._page_header_row = ctk.CTkFrame(self._search_parent, fg_color="transparent")
        self._page_header_row.grid(
            row=0, column=0, columnspan=3,
            padx=(15, 15), pady=(2, 0), sticky="ew"
        )
        self._page_header_lbl = ctk.CTkLabel(
            self._page_header_row,
            text=_t("page_header_label"),
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray45", "gray60"),
        )
        self._page_header_lbl.pack(side="left")

        # Combined frame for both input rows — shared grid columns
        # guarantee the labels, entries, and button frames align.
        # Parented to the scrollable container inside the left pane
        # (built in _app.py) so the whole controls column scrolls.
        self._input_frame = ctk.CTkFrame(self._left_scroll, fg_color="transparent")
        self._input_frame.pack(fill="both", expand=True, padx=10, pady=(5, 2))
        self._input_frame.grid_columnconfigure(0)
        self._input_frame.grid_columnconfigure(1, weight=1)
        self._input_frame.grid_columnconfigure(2, minsize=185)

        # Create recursive_var early so both the folder row checkbox
        # and Advanced Search Options can share it.
        self.recursive_var = ctk.StringVar(value="on")
        # AND/OR mode, whole-word, and use-index vars — the matching
        # checkboxes live only inside Advanced Search Options now. Vars
        # stay at this scope so saved settings still load correctly.
        self.and_mode_var = ctk.StringVar(value="off")
        self.whole_word_var = ctk.StringVar(value="on")
        self.index_search_var = ctk.StringVar(value="off")

        import tkinter as _tk_step2
        from peekdocs.i18n import t as _t
        self._step_lbl_2 = _tk_step2.Label(self._input_frame, text=_t("step_2_label"), font=("TkDefaultFont", 14, "bold"),
                                       fg="white", bg="#2196F3")
        self._step_lbl_2.grid(row=1, column=0, padx=(10, 2), pady=(4, 8), sticky="w")
        self._step_2_tooltip = Tooltip(self._step_lbl_2, _t("step_2_tooltip"))

        self._assistant_label = ctk.CTkLabel(
            self._input_frame, text="", font=ctk.CTkFont(size=12),
            text_color=("#8B5CF6", "#A78BFA"), anchor="w",
        )
        # Hidden until Search Assistant sets a query

        self.search_entry = ctk.CTkEntry(
            self._input_frame, placeholder_text="Enter search terms...", font=ctk.CTkFont(size=14)
        )
        self.search_entry.grid(row=1, column=1, padx=(5, 5), pady=(4, 8), sticky="ew")
        self.search_entry.bind("<Key>", self._on_search_key)
        self.search_entry.bind("<Return>", lambda e: self.start_search())
        self.search_entry.bind("<Up>", self._search_history_prev)
        self.search_entry.bind("<Down>", self._search_history_next)

        self._search_btn_frame = ctk.CTkFrame(self._input_frame, corner_radius=6,
                                               border_width=2, border_color=("gray50", "gray50"))
        self._search_btn_frame.grid(row=1, column=2, padx=(5, 10), pady=(4, 8), sticky="w")

        from peekdocs.i18n import t as _t
        # Clear button removed — users can select-all + delete in the
        # search bar, or just retype. The Recent dropdown is what most
        # users were reaching for after Clear anyway.

        self._recent_btn = ctk.CTkButton(
            self._search_btn_frame, text="\u25bc " + __import__("peekdocs.i18n", fromlist=["t"]).t("recent_searches_label"), width=80,
            command=self._show_recent_searches,
            font=ctk.CTkFont(size=11),
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
        )
        self._recent_btn.pack(side="left", padx=(2, 2), pady=4)
        self._recent_btn_tooltip = Tooltip(self._recent_btn, __import__("peekdocs.i18n", fromlist=["t"]).t("recent_searches_tooltip"), anchor="left")

        # Row 2 used to host a tinted "options bar" (Wizard + save_group);
        # both moved out — Wizard to the Tools menu, save_group up next
        # to Recent in the Step 2 button row — leaving the bar empty,
        # so it's gone now. Row 2 of _input_frame is unused.
        from peekdocs.i18n import t as _t

        # Row 4: "Step 4" label + Run Standard Search button.
        # Step 3 (output report buttons) now sits above this row at grid row=3 —
        # users select / view output format BEFORE running a search.
        import tkinter as _tk_step3
        from peekdocs.i18n import t as _t
        self._step_lbl_4 = _tk_step3.Label(self._input_frame, text=_t("step_4_label"), font=("TkDefaultFont", 14, "bold"),
                                       fg="white", bg="#2196F3")
        self._step_lbl_4.grid(row=4, column=0, padx=(10, 2), pady=(6, 8), sticky="nw")
        self._step_4_tooltip = Tooltip(self._step_lbl_4, _t("step_4_tooltip"))

        # Run-buttons row is a vertical stack: top sub-row holds the three
        # Run buttons; bottom sub-row holds the "What's the difference?" link.
        _run_outer = ctk.CTkFrame(self._input_frame, fg_color="transparent")
        _run_outer.grid(row=4, column=1, columnspan=2, padx=(5, 5), pady=(0, 8), sticky="ew")

        btn_frame = ctk.CTkFrame(_run_outer, fg_color="transparent")
        btn_frame.pack(side="top", fill="x", anchor="w")
        self._run_search_frame = btn_frame
        self._run_search_outer = _run_outer

        # Run Standard Search button — standalone
        from peekdocs.i18n import t as _t
        self.search_button = ctk.CTkButton(
            btn_frame, text=_t("run_standard_search_label"), width=200, height=44, command=self.start_search,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#2196F3", hover_color="#1976D2", text_color="white",
        )
        self.search_button.pack(side="left", padx=(0, 10))
        self._run_search_tooltip = Tooltip(self.search_button, _t("run_standard_search_tooltip"))



        # AND/OR, Recursive, Whole Word, and the Advanced toggle used to
        # sit here as a duplicate of their Advanced-panel counterparts.
        # They now live only inside the inline Advanced Search Options
        # section below; this row keeps Wizard, Save, Reload.
        from peekdocs.i18n import t as _t

        # Search Wizard moved to the Tools menu (see _show_tools_menu in
        # _build_bottom_row). It no longer sits in this options bar.

        # Save, Reload, and ? grouped together
        # Transparent — sits inside the now-tinted options_row.
        # Save / Reload / ? — moved out of an options_row save_group
        # into _search_btn_frame so they sit next to Recent on Step 2.
        save_group = self._search_btn_frame

        self.save_to_collection_btn = ctk.CTkButton(
            save_group, text="\u25b6 " + __import__("peekdocs.i18n", fromlist=["t"]).t("save_label"), width=60,
            fg_color="transparent",
            text_color=("black", "black"),
            hover_color=("gray90", "gray25"),
            command=self._save_to_collection,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.save_to_collection_btn.pack(side="left", padx=(0, 0), pady=3)
        self._save_to_collection_btn_tooltip = Tooltip(self.save_to_collection_btn, __import__("peekdocs.i18n", fromlist=["t"]).t("save_tooltip"))

        self.load_search_btn = ctk.CTkButton(
            save_group, text="\u25b6 " + __import__("peekdocs.i18n", fromlist=["t"]).t("reload_label"), width=70,
            fg_color="transparent",
            text_color=("black", "black"),
            hover_color=("gray90", "gray25"),
            command=self._open_load_search_popup,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.load_search_btn.pack(side="left", padx=(0, 0), pady=3)
        self._load_search_btn_tooltip = Tooltip(self.load_search_btn, __import__("peekdocs.i18n", fromlist=["t"]).t("reload_tooltip"))
        self._load_search_popup = None

        self.save_load_help_btn = ctk.CTkButton(
            save_group, text="?", width=30, height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#1565C0",
            text_color="white",
            hover_color="#0D47A1",
            corner_radius=15,
            command=self._show_save_load_help,
        )
        self.save_load_help_btn.pack(side="left", padx=(2, 2), pady=3)
        Tooltip(self.save_load_help_btn, "Help for ▶ Save and ▶ Reload")


        Tooltip(self.search_entry, "Search Bar: Type one or more search terms separated by spaces — there is no limit to the number of terms. Use quotes for phrases (e.g., \"annual report\"). All searches are case-insensitive. Do not use commas. Do not enter flags here — the checkboxes under Advanced Search Options handle that. When Expression is checked, enter a boolean expression instead (e.g., \"(bob AND amy) OR fred NOT draft\"). Press ↑ / ↓ to recall recent searches without opening the popup.")



    def _build_folder_row(self):
        """Build the folder selection row in the shared _input_frame at row 0."""
        import tkinter as _tk_step
        from peekdocs.i18n import t as _t
        self._step_lbl_1 = _tk_step.Label(self._input_frame, text=_t("step_1_label"), font=("TkDefaultFont", 14, "bold"),
                                      fg="white", bg="#2196F3")
        self._step_lbl_1.grid(row=0, column=0, padx=(10, 2), pady=(4, 8), sticky="w")
        self._step_1_tooltip = Tooltip(self._step_lbl_1, _t("step_1_tooltip"))

        self.folder_entry = ctk.CTkEntry(self._input_frame, font=ctk.CTkFont(size=14))
        self.folder_entry.grid(row=0, column=1, padx=(5, 5), pady=(4, 8), sticky="ew")
        self.folder_entry.insert(0, os.path.expanduser("~"))

        self._browse_frame = ctk.CTkFrame(self._input_frame, corner_radius=6,
                                          border_width=2, border_color=("gray50", "gray50"))
        self._browse_frame.grid(row=0, column=2, padx=(5, 10), pady=(4, 8), sticky="w")

        from peekdocs.i18n import t as _t
        self.browse_button = ctk.CTkButton(
            self._browse_frame, text=_t("browse_button_label"), width=60, command=self.browse_folder,
            font=ctk.CTkFont(size=11),
        )
        self.browse_button.pack(side="left", padx=(6, 3), pady=4)
        self._browse_button_tooltip = Tooltip(self.browse_button, _t("browse_button_tooltip"), anchor="left")

        self._multi_folder_btn = ctk.CTkButton(
            self._browse_frame, text=_t("multi_folder_button_label"), width=65, command=self._add_folder,
            font=ctk.CTkFont(size=11),
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
        )
        self._multi_folder_btn.pack(side="left", padx=(3, 0))
        self._multi_folder_btn_tooltip = Tooltip(self._multi_folder_btn, _t("multi_folder_button_tooltip"), anchor="left")

        self.browse_file_button = ctk.CTkButton(
            self._browse_frame, text=_t("single_file_button_label"), width=80, command=self._browse_file,
            font=ctk.CTkFont(size=11),
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
        )
        self.browse_file_button.pack(side="left", padx=(3, 6), pady=4)
        self._browse_file_button_tooltip = Tooltip(self.browse_file_button, _t("single_file_button_tooltip"), anchor="left")

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

        # Top-right ? — same blue chip styling as the help affordances on
        # the options bar so the help vocabulary is consistent everywhere.
        search_help_btn = ctk.CTkButton(
            self, text="?", width=30, height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#1565C0", text_color="white",
            hover_color="#0D47A1",
            corner_radius=15,
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
        # Search Suites button — square, with the two-word label stacked
        # vertically. Same height as Run Standard Search (44px) so the
        # row baseline is preserved; width matches the height.
        from peekdocs.i18n import t as _t
        self._suites_btn = ctk.CTkButton(
            self._run_search_frame,
            text=self._stack_label(_t("search_suites_label")), width=44, height=44,
            fg_color="#76BA1B", hover_color="#76BA1B",
            text_color="white",
            command=self._show_search_suites,
            font=ctk.CTkFont(size=10, weight="bold"),
        )
        self._suites_btn.pack(side="left", padx=(12, 0))
        self._suites_tooltip = Tooltip(self._suites_btn, _t("search_suites_tooltip"))

        # Regex Search button — orange, third color in the run-buttons
        # row so the three search modes are visually distinct
        # (blue=Standard, green=Suites, orange=Regex). Same square shape
        # and stacked text as Suites; height matches Run Standard Search.
        from peekdocs.i18n import t as _t
        self._regex_search_btn = ctk.CTkButton(
            self._run_search_frame,
            text=self._stack_label(_t("regex_search_label")), width=44, height=44,
            fg_color="#FF9800", hover_color="#FF9800",
            text_color="white",
            command=self._start_regex_search,
            font=ctk.CTkFont(size=10, weight="bold"),
        )
        self._regex_search_btn.pack(side="left", padx=(12, 0))
        self._regex_search_tooltip = Tooltip(self._regex_search_btn, _t("regex_search_tooltip"))

        # "What's the difference?" hyperlink removed — the Search Suites
        # and Regex Search buttons now stand on their own; users who
        # want the breakdown can hover the tooltips or read the docs.



    @staticmethod
    def _stack_label(text):
        """Insert a single newline at the first space so a two-word
        label renders stacked on the square Suites / Regex buttons.
        For single-token labels (e.g. Japanese, Chinese) returns the
        text unchanged."""
        return text.replace(" ", "\n", 1) if " " in text else text

    def _build_advanced_panel(self):
        """Build the Advanced Search Options panel inline in the left
        pane (below the status row). Hidden until the Advanced toggle
        in the options row is clicked. Replaces a former CTkToplevel
        popup so the panel scrolls with the rest of the left pane."""
        from peekdocs.i18n import t as _t

        # Always-visible inline container in the left pane at row 7.
        # Holds a clickable header (always shown) and a collapsible body
        # (the controls + Save/Close/Restore/Inspect buttons). Row 6 is
        # the open-report buttons row (DOCX/TXT/CSV/JSON/PDF/HTML).
        self._advanced_container = ctk.CTkFrame(self._input_frame, fg_color=("gray92", "gray18"))
        self._advanced_container.grid(
            row=7, column=0, columnspan=3, padx=10, pady=(8, 5), sticky="ew"
        )

        # Header — clickable; chevron + label. Click to toggle body.
        self._advanced_header_btn = ctk.CTkButton(
            self._advanced_container,
            text="▶ " + _t("advanced_label"),
            fg_color="transparent",
            text_color=("#1565C0", "#90CAF9"),
            hover_color=("gray85", "gray22"),
            anchor="w",
            command=self.toggle_advanced,
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self._advanced_header_btn.pack(fill="x", padx=10, pady=(8, 4))
        self._advanced_header_tooltip = Tooltip(self._advanced_header_btn, _t("advanced_tooltip"))

        # Body — collapsible. Hidden initially; toggle_advanced packs it.
        self._advanced_body = ctk.CTkFrame(self._advanced_container, fg_color="transparent")
        # Not packed yet — collapsed by default.

        self.advanced_frame = ctk.CTkFrame(self._advanced_body, fg_color="transparent")
        self.advanced_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

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
            wraplength=380,
        ).grid(row=0, column=0, sticky="w")
        # Advanced help — same blue chip vocabulary as every other ? on the app.
        adv_help_btn = ctk.CTkButton(
            adv_header_frame, text="?", width=30, height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#1565C0", text_color="white",
            hover_color="#0D47A1",
            corner_radius=15,
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

        self._adv_cb_and = ctk.CTkCheckBox(
            cb_frame, text=_t("adv_and_mode_label"), variable=self.and_mode_var,
            onvalue="on", offvalue="off", command=self._on_and_toggle,
        )
        self._adv_cb_and.grid(row=0, column=0, padx=(0, 15), pady=(0, 5), sticky="w")
        self._adv_cb_rec = ctk.CTkCheckBox(
            cb_frame, text=_t("recursive_label"), variable=self.recursive_var,
            onvalue="on", offvalue="off",
            command=lambda: self._save_ui_preference("recursive", self.recursive_var.get() == "on"),
        )
        self._adv_cb_rec.grid(row=0, column=1, padx=(0, 15), pady=(0, 5), sticky="w")
        self._adv_cb_fuz = ctk.CTkCheckBox(
            cb_frame, text=_t("adv_fuzzy_label"), variable=self.fuzzy_var,
            onvalue="on", offvalue="off", command=self._on_fuzzy_toggle,
        )
        self._adv_cb_fuz.grid(row=0, column=2, padx=(0, 15), pady=(0, 5), sticky="w")

        self.wildcard_var = ctk.StringVar(value="off")
        self.ocr_var = ctk.StringVar(value="off")
        self.regex_var = ctk.StringVar(value="off")

        self._adv_cb_wild = ctk.CTkCheckBox(
            cb_frame, text=_t("adv_wildcard_label"), variable=self.wildcard_var,
            onvalue="on", offvalue="off", command=self._on_wildcard_toggle,
        )
        self._adv_cb_wild.grid(row=1, column=0, padx=(0, 15), pady=0, sticky="w")
        self._adv_cb_ocr = ctk.CTkCheckBox(
            cb_frame, text=_t("adv_ocr_label"), variable=self.ocr_var,
            onvalue="on", offvalue="off",
        )
        self._adv_cb_ocr.grid(row=1, column=1, padx=(0, 15), pady=0, sticky="w")
        self._adv_cb_regex = ctk.CTkCheckBox(
            cb_frame, text=_t("adv_regex_label"), variable=self.regex_var,
            onvalue="on", offvalue="off", command=self._on_regex_toggle,
        )
        self._adv_cb_regex.grid(row=1, column=2, padx=(0, 15), pady=0, sticky="w")

        # Row 2 of the checkbox grid: Inverse, Expression, Whole Word.
        # Moved out of rows 0/1 so the first two rows group naturally
        # by category (mode toggles → search-term modifiers).
        # whole_word_var already created in _build_search_row.
        self.expression_var = ctk.StringVar(value="off")
        self.inverse_var = ctk.StringVar(value="off")

        self._adv_cb_inverse = ctk.CTkCheckBox(
            cb_frame, text=_t("adv_inverse_label"), variable=self.inverse_var,
            onvalue="on", offvalue="off",
        )
        self._adv_cb_inverse.grid(row=2, column=0, padx=(0, 15), pady=(5, 0), sticky="w")
        Tooltip(self._adv_cb_inverse, "Show files that do NOT contain the search terms — useful for finding missing content")

        self._adv_cb_expr = ctk.CTkCheckBox(
            cb_frame, text=_t("adv_expression_label"), variable=self.expression_var,
            onvalue="on", offvalue="off", command=self._on_expression_toggle,
        )
        self._adv_cb_expr.grid(row=2, column=1, padx=(0, 15), pady=(5, 0), sticky="w")

        self._adv_cb_whole_word = ctk.CTkCheckBox(
            cb_frame, text=_t("whole_word_label"), variable=self.whole_word_var,
            onvalue="on", offvalue="off",
            command=lambda: self._save_ui_preference("whole_word", self.whole_word_var.get() == "on"),
        )
        self._adv_cb_whole_word.grid(row=2, column=2, padx=(0, 15), pady=(5, 0), sticky="w")
        Tooltip(self._adv_cb_whole_word, "Matches complete words only. 'bob' matches 'bob' but not 'bobcat'.")

        # Use Index used to sit at row 1 / col 4 of this grid. It now
        # lives below the Output Dir entry — see the cb_index_search
        # creation after that row.

        # Row 2: exclude
        self._adv_lbl_exclude = ctk.CTkLabel(self.advanced_frame, text=_t("adv_exclude_label"))
        self._adv_lbl_exclude.grid(
            row=2, column=0, padx=(15, 5), pady=5, sticky="e"
        )
        self.exclude_entry = ctk.CTkEntry(
            self.advanced_frame, placeholder_text="Ex: draft,obsolete"
        )
        self.exclude_entry.grid(row=2, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="ew")

        # Row 3: file types
        self._adv_lbl_file_types = ctk.CTkLabel(self.advanced_frame, text=_t("adv_file_types_label"))
        self._adv_lbl_file_types.grid(
            row=3, column=0, padx=(15, 5), pady=5, sticky="e"
        )
        self.file_types_entry = ctk.CTkEntry(
            self.advanced_frame, placeholder_text="Ex: pdf,docx,txt"
        )
        self.file_types_entry.grid(row=3, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="ew")

        # Row 3: proximity + context lines
        self._adv_lbl_word_proximity = ctk.CTkLabel(self.advanced_frame, text=_t("adv_word_proximity_label"))
        self._adv_lbl_word_proximity.grid(
            row=4, column=0, padx=(15, 5), pady=5, sticky="e"
        )
        num_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
        num_frame.grid(row=4, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="w")

        self.proximity_entry = ctk.CTkEntry(num_frame, width=60)
        self.proximity_entry.grid(row=0, column=0)

        num_frame.grid_columnconfigure(1, minsize=110)
        self._adv_lbl_lines_before = ctk.CTkLabel(num_frame, text=_t("adv_lines_before_label"))
        self._adv_lbl_lines_before.grid(row=0, column=1, padx=(20, 5), sticky="e")
        self.context_before_entry = ctk.CTkEntry(num_frame, width=60)
        self.context_before_entry.grid(row=0, column=2)

        self._adv_lbl_lines_after = ctk.CTkLabel(num_frame, text=_t("adv_lines_after_label"))
        self._adv_lbl_lines_after.grid(row=0, column=3, padx=(20, 5))
        self.context_after_entry = ctk.CTkEntry(num_frame, width=60)
        self.context_after_entry.grid(row=0, column=4)

        # Row 5: Cores to use (entry alone, gridded directly on
        # advanced_frame col 1 — same column the other input fields
        # use, so left edges line up across all rows).
        self._default_cores = max(1, (os.cpu_count() or 1) // 2)
        self._adv_lbl_cores = ctk.CTkLabel(self.advanced_frame, text=_t("adv_cores_to_use_label"))
        self._adv_lbl_cores.grid(row=5, column=0, padx=(15, 5), pady=5, sticky="e")
        self.cores_entry = ctk.CTkEntry(self.advanced_frame, width=60)
        self.cores_entry.insert(0, str(self._default_cores))
        self.cores_entry.grid(row=5, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="w")

        # Row 6: Max Matches + Max File Size pair on their own row.
        # Both entries align with cores_entry above (all at advanced_frame col 1).
        self._adv_lbl_max_matches = ctk.CTkLabel(self.advanced_frame, text=_t("adv_max_matches_label"))
        self._adv_lbl_max_matches.grid(row=6, column=0, padx=(15, 5), pady=5, sticky="e")
        max_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
        max_frame.grid(row=6, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="w")
        self.max_matches_entry = ctk.CTkEntry(max_frame, width=60)
        self.max_matches_entry.insert(0, "1000")
        self.max_matches_entry.grid(row=0, column=0, sticky="w")
        self._adv_lbl_max_file_size = ctk.CTkLabel(max_frame, text=_t("adv_max_file_size_label"))
        self._adv_lbl_max_file_size.grid(row=0, column=1, padx=(20, 5), sticky="w")
        self.max_file_size_entry = ctk.CTkEntry(max_frame, width=60)
        self.max_file_size_entry.insert(0, "100")
        self.max_file_size_entry.grid(row=0, column=2, sticky="w")

        # Row 7: range filters
        self._adv_lbl_range = ctk.CTkLabel(self.advanced_frame, text=_t("adv_range_label"))
        self._adv_lbl_range.grid(
            row=7, column=0, padx=(15, 5), pady=5, sticky="e"
        )
        self.range_entry = ctk.CTkEntry(
            self.advanced_frame, placeholder_text="Ex: amount:1000..5000, date:2024-01-01..2024-12-31"
        )
        self.range_entry.grid(row=7, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="ew")
        Tooltip(self.range_entry, "Range filter: field:min..max (comma-separated for multiple). Fields: date, amount, number, percent, age, time, filesize, filedate. Use fn: prefix for filename ranges (e.g. fn:date:2024-01-01..2024-12-31). Open-ended ranges: amount:1000.. or amount:..5000")

        # Row 8: specific files
        self._adv_lbl_specific_files = ctk.CTkLabel(self.advanced_frame, text=_t("adv_specific_files_label"))
        self._adv_lbl_specific_files.grid(
            row=8, column=0, padx=(15, 5), pady=5, sticky="e"
        )
        self.specific_files_entry = ctk.CTkEntry(
            self.advanced_frame, placeholder_text="Ex: report.pdf,notes.txt"
        )
        self.specific_files_entry.grid(row=8, column=1, columnspan=2, padx=(0, 15), pady=5, sticky="ew")

        # Row 9: Save Report As (save_name entry alone — directly on
        # advanced_frame so its left edge aligns with the other inputs).
        self._adv_lbl_save_as = ctk.CTkLabel(self.advanced_frame, text=_t("adv_save_report_as_label"))
        self._adv_lbl_save_as.grid(
            row=9, column=0, padx=(15, 5), pady=(5, 5), sticky="e"
        )
        self.save_name_entry = ctk.CTkEntry(self.advanced_frame, width=140, placeholder_text="Ex: my_report")
        self.save_name_entry.grid(row=9, column=1, columnspan=2, padx=(0, 15), pady=(5, 5), sticky="w")

        # Row 10: Append Report To — its own row.
        self._adv_lbl_append_to = ctk.CTkLabel(self.advanced_frame, text=_t("adv_append_report_to_label"))
        self._adv_lbl_append_to.grid(
            row=10, column=0, padx=(15, 5), pady=(0, 10), sticky="e"
        )
        self.append_name_entry = ctk.CTkEntry(self.advanced_frame, width=140, placeholder_text="Ex: combined_report")
        self.append_name_entry.grid(row=10, column=1, columnspan=2, padx=(0, 15), pady=(0, 10), sticky="w")

        # Row 11: output directory
        self._adv_lbl_output_dir = ctk.CTkLabel(self.advanced_frame, text=_t("adv_output_dir_label"))
        self._adv_lbl_output_dir.grid(
            row=11, column=0, padx=(15, 5), pady=(0, 5), sticky="e"
        )
        outdir_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
        outdir_frame.grid(row=11, column=1, columnspan=2, padx=(0, 15), pady=(0, 5), sticky="ew")

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

        # Row 12: Use Index — left-aligned to the panel's left margin
        # (col 0, no label) so it sits flush with the other label-left
        # positions instead of indented under the entry column.
        self.cb_index_search = ctk.CTkCheckBox(
            self.advanced_frame, text=_t("use_index_label"),
            variable=self.index_search_var,
            onvalue="on", offvalue="off",
            command=lambda: self._save_ui_preference("index_search", self.index_search_var.get() == "on"),
        )
        self.cb_index_search.grid(row=12, column=0, columnspan=3, padx=(15, 15), pady=(2, 6), sticky="w")
        self._cb_index_search_tooltip = Tooltip(self.cb_index_search, _t("use_index_tooltip"))

        # Row 11: additional output formats
        output_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
        output_frame.grid(row=13, column=0, columnspan=3, padx=15, pady=(0, 5), sticky="w")

        # The "Also ==>" leading label was removed — DOCX now occupies
        # column 0 and all five checkboxes share one line. DOCX defaults
        # ON (the existing always-written behaviour); unchecking it adds
        # the --no-docx CLI flag, which skips writing the DOCX report.
        # Tooltip on each format checkbox documents the same scope note.
        _output_scope_note = (
            "Applies to Standard Search only (the green Run button). "
            "Search Suites have their own DOCX / HTML / CSV / JSON / PDF picker "
            "inside the Search Suites popup. Regex Search always writes "
            "just TXT and DOCX, regardless of these checkboxes."
        )
        self.output_docx_var = ctk.StringVar(value="on")
        self.output_csv_var = ctk.StringVar(value="off")
        self.output_json_var = ctk.StringVar(value="off")
        self.output_pdf_var = ctk.StringVar(value="off")
        self.output_html_var = ctk.StringVar(value="off")
        def _save_output_format(key, var):
            self._save_ui_preference(key, var.get() == "on")

        cb_docx = ctk.CTkCheckBox(
            output_frame, text="DOCX", variable=self.output_docx_var,
            onvalue="on", offvalue="off",
            command=lambda: _save_output_format("output_docx", self.output_docx_var),
        )
        cb_docx.grid(row=0, column=0, padx=(0, 15))
        Tooltip(cb_docx,
                "Write the highlighted Word report (.docx). Default ON. "
                "Uncheck to skip the .docx report and only keep the .txt "
                "report on disk (the GUI's preview pane reads from the .txt, "
                "so it still works). " + _output_scope_note,
                anchor="above")
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
        # PDF and HTML wrap onto a second row so the format row only
        # spans 3 columns. This keeps the output_frame width bounded
        # by 3 checkboxes (~250-280 px) instead of 5, which matters on
        # Windows where font widths push the 5-across layout past the
        # left pane's right edge in tight sash positions.
        cb_pdf.grid(row=1, column=0, padx=(0, 15), pady=(4, 0))
        cb_html = ctk.CTkCheckBox(
            output_frame, text="HTML", variable=self.output_html_var,
            onvalue="on", offvalue="off",
            command=lambda: _save_output_format("output_html", self.output_html_var),
        )
        cb_html.grid(row=1, column=1, padx=(0, 15), pady=(4, 0))
        # Tooltips on the four output checkboxes are attached below in
        # the bulk-tooltip section near the bottom of this method — this
        # file's convention is to declare every widget first, then attach
        # all tooltips together. Inline Tooltip calls here get shadowed
        # by the later ones; the bottom calls carry the
        # _output_scope_note disclaimer.
        self.timestamp_var = ctk.StringVar(value="off")
        self._adv_cb_ts = ctk.CTkCheckBox(
            output_frame, text=_t("adv_timestamp_filename_label"), variable=self.timestamp_var,
            onvalue="on", offvalue="off",
        )
        # Each cleanup checkbox gets its own row. Pairing two long
        # labels at cols 0-2 / 3-5 used to push the frame wider than
        # narrow left-pane widths could fit (notably on Windows where
        # font metrics widen these by ~15-20%), clipping the rightmost
        # widget without exposing a horizontal scrollbar. One per row
        # keeps the frame width bounded by the longest single label.
        self._adv_cb_ts.grid(row=2, column=0, columnspan=3, padx=(0, 15), pady=(4, 0), sticky="w")
        cb_ts = self._adv_cb_ts
        Tooltip(cb_ts, "Keep every search result by appending date+time to filenames (e.g., peekdocs_standard_results_20260327_143022.txt). Without this, each search overwrites the previous results. Useful when you want to compare searches or keep a record. Files accumulate over time — use Delete on Close or Tools → Clear Files → Wipe Session to clean up", anchor="above")
        self.delete_reports_var = ctk.StringVar(value="off")
        from peekdocs.i18n import t as _t
        self._cb_delete_adv = ctk.CTkCheckBox(
            output_frame, text=_t("delete_on_close_label"), variable=self.delete_reports_var,
            onvalue="on", offvalue="off",
            command=lambda: _save_output_format("delete_reports_on_close", self.delete_reports_var),
        )
        self._cb_delete_adv.grid(row=3, column=0, columnspan=3, padx=(0, 15), pady=(4, 0), sticky="w")
        self.clear_history_var = ctk.StringVar(value="off")
        self._adv_cb_clear_hist = ctk.CTkCheckBox(
            output_frame, text=_t("adv_clear_history_label"), variable=self.clear_history_var,
            onvalue="on", offvalue="off",
            command=lambda: _save_output_format("clear_history_on_close", self.clear_history_var),
        )
        cb_clear_hist = self._adv_cb_clear_hist
        cb_clear_hist.grid(row=4, column=0, columnspan=3, padx=(0, 15), pady=(4, 0), sticky="w")

        self.restrict_permissions_var = ctk.StringVar(value="off")
        self._adv_cb_restrict = ctk.CTkCheckBox(
            output_frame, text=_t("adv_restrict_perms_label"), variable=self.restrict_permissions_var,
            onvalue="on", offvalue="off",
            command=lambda: _save_output_format("restrict_permissions", self.restrict_permissions_var),
        )
        cb_restrict = self._adv_cb_restrict
        cb_restrict.grid(row=5, column=0, columnspan=3, padx=(0, 0), pady=(4, 0), sticky="w")
        self.notify_on_complete_var = ctk.StringVar(value="off")
        self._adv_cb_notify_complete = ctk.CTkCheckBox(
            output_frame, text=_t("adv_notify_complete_label"), variable=self.notify_on_complete_var,
            onvalue="on", offvalue="off",
            command=lambda: _save_output_format("notify_on_complete", self.notify_on_complete_var),
        )
        cb_notify_complete = self._adv_cb_notify_complete
        cb_notify_complete.grid(row=6, column=0, columnspan=3, padx=(0, 15), pady=(4, 0), sticky="w")
        Tooltip(cb_notify_complete, "Fire a native desktop notification (macOS Notification Center / Windows toast / Linux libnotify) when a Standard / Suite / Regex search finishes. Suppressed when the peekdocs window is focused — if you can already see the result, no notification fires. Useful for long scans where you start the search, switch to another app, and want a ping when it's done. Notification carries the match count, file count, and elapsed time. No data leaves the machine — the notification is delivered by the local OS notification daemon. macOS users: install terminal-notifier (`brew install terminal-notifier`) for reliable notifications — the built-in AppleScript path is silently dropped on macOS Sequoia (15+) unless Script Editor is explicitly approved in System Settings → Notifications", anchor="above")

        # Separator line below output options
        import tkinter as _tk_sep
        _tk_sep.Frame(self.advanced_frame, height=2, bg="gray60").grid(
            row=14, column=0, columnspan=3, padx=15, pady=(10, 10), sticky="ew")

        # Reset All Fields and Restore Factory Settings moved to a
        # dedicated row in the bottom-button stack below — see
        # adv_bottom_row2.

        self.advanced_frame.grid_columnconfigure(0, minsize=130)
        self.advanced_frame.grid_columnconfigure(1, weight=1)

        # Tooltips
        Tooltip(self._adv_cb_and, "All search terms must appear in the same line. For PDF/Word documents, a line is typically a paragraph")
        Tooltip(self._adv_cb_rec, "Search subfolders inside the Search Folder")
        Tooltip(self._adv_cb_fuz, "Find approximate matches for typos, misspellings, and for scans (e.g., 'budgt' matches 'budget').\nFuzzy and Regex are mutually exclusive.")
        Tooltip(self._adv_cb_wild, "Use * for any characters and ? for one character (e.g., budg* matches budget, budgets)")
        Tooltip(self._adv_cb_ocr, "Extract text from scanned PDFs and image files (bmp, jpg, jpeg, png, tif, tiff). Requires Tesseract to be installed (see Readme.md)")
        Tooltip(self._adv_cb_expr, (
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
        Tooltip(self._adv_cb_regex, "Treat the search bar as a single regular expression for advanced pattern matching (e.g., \\d{3}-\\d{4} for phone numbers). The whole search bar is ONE pattern — spaces are part of the pattern, not separators between terms. Fuzzy and Regex are mutually exclusive. To run multiple regex patterns at once, use the orange Regex Search button (Step 4) instead — it runs a saved regex collection where each pattern is independent.", anchor="above")
        Tooltip(self.exclude_entry, "Comma-separated terms to skip (e.g., draft,obsolete)")
        Tooltip(self.file_types_entry, "Comma-separated file extensions to search. Leave blank to search ALL 100+ supported file types (not every file on disk — unsupported formats like .DS_Store, .exe, random binaries are always skipped). Supported types: 7z, asm, bat, bz2, c, cfg, cir, cmake, conf, cpp, cs, css, csv, doc, dockerfile, docx, dxf, eml, env, epub, f, f90, go, gql, gradle, graphql, gz, h, hpp, html, ics, ini, ipynb, java, js, json, jsonl, key, kt, log, lua, m, makefile, mbox, md, msg, ndjson, numbers, odp, ods, odt, pages, pdf, pl, ppt, pptx, properties, proto, ps1, pst, py, r, rar, rb, rs, rst, rtf, s, scala, scss, sh, sp, spice, sql, sv, swift, tar, tcl, tex, tf, tgz, toml, ts, tsv, txt, v, vb, vcf, vhd, vhdl, vsdx, xls, xlsx, xml, yaml, yml, zip. With OCR enabled: bmp, jpg, jpeg, png, tif, tiff")
        Tooltip(self.proximity_entry, "Word Proximity (-p): find terms within this many words of each other on the same line. Line Proximity (-P) is available in the CLI only — it finds terms within N lines of each other")
        Tooltip(self.context_before_entry, "Number of lines to show before each match. The unit of a 'line' matches what peekdocs indexes per format: a literal line for plain text and source code, a paragraph for Word and PDF, a row for Excel. On paragraph-heavy files, even a small N can include several sentences.")
        Tooltip(self.context_after_entry, "Number of lines to show after each match. The unit of a 'line' matches what peekdocs indexes per format: a literal line for plain text and source code, a paragraph for Word and PDF, a row for Excel. On paragraph-heavy files, even a small N can include several sentences.")
        Tooltip(self.cores_entry, f"Number of CPU cores to use. This machine has {os.cpu_count()}, default is {self._default_cores}")
        Tooltip(self.max_matches_entry, "Maximum matches included in reports. Default 1000. Set to 0 for no limit. See \u2753 help for possible counterintuitive results when this interacts with Max File Size.")
        Tooltip(self.max_file_size_entry, "Skip files larger than this (in MB). Default 100. Set to 0 for no limit. See \u2753 help for possible counterintuitive results when this interacts with Max Matches.")
        Tooltip(self.specific_files_entry, "Comma-separated filenames to search — no limit to the number of files (e.g., report.pdf,notes.txt)")
        Tooltip(self.save_name_entry, "Save an extra copy of the report with a custom name after search completes. peekdocs_report_ will be added to the front of your file name. This is in addition to the regular results files (peekdocs_standard_results.txt and .docx) reachable through the Open Report row in the left pane. Important: without this, your regular reports are overwritten every time you run a new search. Fill in this field to keep a permanent copy. To open it later, navigate to your Search Folder using File Explorer (Windows), Finder (macOS), or your file manager (Linux) and double-click the peekdocs_report_ file")
        Tooltip(self.append_name_entry, "Append results to a named report file (creates or extends it). peekdocs_accumulated_ will be added to the front of your file name")
        Tooltip(cb_csv, "Also save results as a CSV file (peekdocs_standard_results.csv) — open in Excel or Google Sheets to sort, filter, and analyze. " + _output_scope_note)
        Tooltip(cb_json, "Also save results as a JSON file (peekdocs_standard_results.json) — machine-readable format for automation and integration. " + _output_scope_note)
        Tooltip(cb_pdf, "Also save results as a PDF file (peekdocs_standard_results.pdf) — matches highlighted in yellow, portable format for sharing and printing. " + _output_scope_note)
        Tooltip(cb_html, "Also save results as an HTML file (peekdocs_standard_results.html) — opens in any web browser with highlighted matches. The file is stored locally on your computer, not on the internet — nothing is uploaded or made public. " + _output_scope_note)
        self._cb_delete_adv_tooltip = Tooltip(self._cb_delete_adv, __import__("peekdocs.i18n", fromlist=["t"]).t("delete_on_close_tooltip"), anchor="above")
        Tooltip(cb_clear_hist, "Automatically clear your search history and recent searches when you close peekdocs. Search terms, folder paths, and recent searches are stored in plaintext on disk (~/.peekdocs_history.json and ~/.peekdocsrc). If a search term you'd rather not leave on disk has been typed, that exact text is sitting in these files. This checkbox deletes the history file and clears search terms, folder path, and recent searches from your settings. Saved searches, bookmarks, and the rest of your settings are not affected", anchor="above")
        Tooltip(cb_restrict, "Set report files to owner-only read/write (chmod 600) on Unix/macOS. Prevents other users on shared machines from reading your search results. Leave unchecked if colleagues need to access reports in a shared folder. No effect on Windows (NTFS permissions are managed differently). Applies to all report formats: TXT, DOCX, CSV, JSON, PDF, HTML", anchor="above")

        # Bottom buttons — three stacked rows inside the collapsible body:
        #   row 1: Save Defaults / Restore Saved Defaults / Inspect
        #   row 2: Reset All Fields + Restore Factory Settings (the
        #          destructive pair, kept together)
        #   row 3: Close (alone)
        import tkinter as _tk_adv

        # ── Row 1 ────────────────────────────────────────────────────
        adv_bottom_row1 = ctk.CTkFrame(self._advanced_body, fg_color="transparent")
        adv_bottom_row1.pack(fill="x", padx=10, pady=(0, 5))

        self._adv_save_btn = ctk.CTkButton(
            adv_bottom_row1, text=_t("adv_save_defaults_label"), width=110,
            command=self._save_current_settings,
            font=ctk.CTkFont(size=13),
        )
        self._adv_save_btn.pack(side="left", padx=(5, 0))
        Tooltip(self._adv_save_btn, "Save all current options as permanent defaults to ~/.peekdocsrc. This includes every setting on this Advanced Search Options panel (AND/OR mode, recursive, whole word, regex, file types, output formats, and the rest) plus the search terms and folder from the main page. These become the defaults every time you launch the app", anchor="above")

        self._adv_restore_btn = ctk.CTkButton(
            adv_bottom_row1, text=_t("adv_restore_defaults_label"), width=170,
            command=self._load_saved_settings,
            font=ctk.CTkFont(size=13),
        )
        self._adv_restore_btn.pack(side="left", padx=(5, 0))
        Tooltip(self._adv_restore_btn, "Load saved defaults from ~/.peekdocsrc into the GUI", anchor="above")

        adv_inspect_btn = ctk.CTkButton(
            adv_bottom_row1, text="Inspect .peekdocsrc", width=130,
            command=self._inspect_settings,
            font=ctk.CTkFont(size=13),
        )
        adv_inspect_btn.pack(side="right", padx=(0, 5))
        Tooltip(adv_inspect_btn, "View the current saved settings in ~/.peekdocsrc (read-only). These settings are saved by 'Save As Defaults' and apply to: search mode (AND/OR), recursive, regex, fuzzy, wildcard, whole word, OCR, inverse, file types, exclude terms, word proximity, context lines, max matches, max file size, CPU cores, output formats, output directory, timestamp, quiet mode, and appearance. They persist across sessions and are used as defaults when the app starts", anchor="above")

        # ── Row 2: Reset All Fields + Restore Factory Settings ───────
        adv_bottom_row2 = ctk.CTkFrame(self._advanced_body, fg_color="transparent")
        adv_bottom_row2.pack(fill="x", padx=10, pady=(0, 5))

        self._adv_reset_btn = ctk.CTkButton(
            adv_bottom_row2, text=_t("adv_reset_all_label"), width=140,
            fg_color="#CC3333", hover_color="#AA2222",
            command=self.reset_form,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._adv_reset_btn.pack(side="left", padx=(5, 0))
        Tooltip(self._adv_reset_btn, "Clear all fields and reset the GUI to its default state. This does not change the config file — only Save Defaults writes to it", anchor="above")

        self._adv_reset_defaults_btn = ctk.CTkButton(
            adv_bottom_row2, text=_t("adv_restore_factory_label"), width=200,
            fg_color="#DC2626", hover_color="#B91C1C",
            command=self._reset_saved_defaults,
            font=ctk.CTkFont(size=13),
        )
        self._adv_reset_defaults_btn.pack(side="left", padx=(10, 0))
        Tooltip(self._adv_reset_defaults_btn, "Delete ~/.peekdocsrc and return all settings to factory defaults. This erases all saved preferences — search mode, file types, output formats, and everything else. The app will start fresh next time as if newly installed. Your documents and search history are not affected", anchor="above")

        # The "↑ Collapse" link that used to sit here was removed —
        # on Windows, collapsing the body while the user was scrolled
        # deep into it left the scrollable left pane parked past the
        # new (shorter) content, making the top of the pane look like
        # it had vanished. Users now collapse by scrolling back up to
        # the ▶/▼ Advanced Search Options header at the top of the
        # panel — that path doesn't trigger the layout glitch because
        # the user is already at the top of the scroll when they
        # click it.

        # No popup window — sizing is handled by the inline container's
        # natural grid height inside the scrollable left pane.

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
        # row=5: shifted down by 1 to make room for report_frame at row=3 and Run row at row=4
        status_row.grid(row=5, column=0, columnspan=3, padx=(10, 15), pady=(0, 4), sticky="ew")

        # status_row holds the label + wrapping message. The Matched /
        # Excluded file buttons moved out to the right pane below the
        # results headline — see the _results_button_row block in the
        # preview_frame area further down.
        _status_top = ctk.CTkFrame(status_row, fg_color="transparent")
        _status_top.pack(fill="x", side="top", anchor="w")

        _status_label_size = 16 if sys.platform == "win32" else 14
        from peekdocs.i18n import t as _t
        self._status_label_left = ctk.CTkLabel(
            _status_top, text=_t("status_label"), font=ctk.CTkFont(size=_status_label_size, weight="bold"),
        )
        self._status_label_left.pack(side="left", padx=(0, 5))
        self._status_label_tooltip = Tooltip(self._status_label_left, _t("status_tooltip"))

        _status_font_size = 16 if sys.platform == "win32" else 14
        # wraplength sized to comfortably fit the left pane at 50/50
        # split on a 1280-wide default window; updated dynamically
        # below in _on_status_row_resize so it tracks pane resizes.
        self.status_label = ctk.CTkLabel(
            _status_top, text="", font=ctk.CTkFont(size=_status_font_size), anchor="w",
            wraplength=400, text_color=("blue", "#66BBFF"), justify="left",
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        def _on_status_row_resize(event):
            # Reserve ~70 px for the "Status:" prefix + padding.
            new_wrap = max(120, event.width - 70)
            try:
                self.status_label.configure(wraplength=new_wrap)
            except Exception:
                pass
        _status_top.bind("<Configure>", _on_status_row_resize)

        # Matched / Excluded file buttons are created further down as
        # children of _results_button_row in the right pane.

        self.matched_files = []
        self._inverse_results = False

        # Results preview pane — lives in the right pane of the
        # horizontal split (created in _app.py). Shown on launch with
        # empty content.
        # Transparent + zero padding so the preview text fills the
        # entire right pane edge-to-edge with no surrounding box.
        self.preview_frame = ctk.CTkFrame(self._right_pane, fg_color="transparent", corner_radius=0)
        self.preview_frame.pack(fill="both", expand=True, padx=0, pady=0)

        import tkinter as tk
        from peekdocs.i18n import t as _t

        # App Size + Language pickers moved to the bottom toolbar —
        # see the middle group built in _build_bottom_row. The page
        # header row is now just the "Main page" label on the left.
        # `_TEXT_SIZE_KEYS` is created in _build_bottom_row alongside
        # the picker that uses it.

        # ── Results summary — sits at the very top of the right pane.
        # Empty until a search completes, then carries the headline
        # numbers (files searched, match count, elapsed time). Status
        # progress (Searching… / Cancelling… / Search complete) stays on
        # the left pane's status_label.
        self._results_summary_label = ctk.CTkLabel(
            self.preview_frame, text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#1565C0", "#90CAF9"),
            anchor="w", justify="left", wraplength=600,
        )
        self._results_summary_label.pack(fill="x", padx=10, pady=(8, 2))
        # Track the pane width so the headline wraps cleanly even when
        # the user drags the sash narrower.
        def _on_summary_resize(event):
            try:
                self._results_summary_label.configure(wraplength=max(200, event.width - 20))
            except Exception:
                pass
        self.preview_frame.bind("<Configure>", _on_summary_resize, add="+")

        # ── Results button row: Matched / Excluded file count chips ──
        # Sits right under the headline, on the right pane. Both buttons
        # start hidden (pack_forget) and the search-completion paths in
        # _mixin_search.py re-pack them once the counts are known.
        _results_button_row = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        _results_button_row.pack(fill="x", padx=10, pady=(0, 4))

        self._matched_files_link = ctk.CTkButton(
            _results_button_row, text="", font=ctk.CTkFont(size=10),
            fg_color="#FF6B35", hover_color="#E55A2B", text_color="white",
            cursor="hand2", height=22, width=120,
            command=self._show_matched_files_popup,
        )
        self._matched_files_link.pack(side="left", padx=(0, 0))
        self._matched_files_link.pack_forget()  # Hidden until matches found
        from peekdocs.i18n import t as _t_mf
        self._matched_files_link_tooltip = Tooltip(self._matched_files_link, _t_mf("matched_files_tooltip"))

        self._excluded_files_btn = ctk.CTkButton(
            _results_button_row, text="", font=ctk.CTkFont(size=10),
            fg_color="#666666", hover_color="#555555", text_color="white",
            cursor="hand2", height=22, width=120,
            command=self._show_excluded_files_popup,
        )
        self._excluded_files_btn.pack(side="left", padx=(5, 0))
        self._excluded_files_btn.pack_forget()  # Hidden until search completes
        self._excluded_files_btn_tooltip = Tooltip(self._excluded_files_btn, _t_mf("excluded_files_tooltip"))

        # ── Middle row: Preview Size + Preview cap dropdowns ─────────
        preview_header_mid = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        preview_header_mid.pack(fill="x", padx=5, pady=(5, 0))

        # Results Preview label + count + Clear were moved down one row
        # (into preview_label_row, built after the dropdowns below) so
        # the dropdowns sit alone on this row.

        # Right-side group on this row (right→left pack order):
        # cap_dropdown, cap_label, preview_size_menu, preview_size_lbl.
        # Cap picker — anchored to the right edge of this row. Status
        # text describing the cap sits on its own row just below.
        self._preview_cap_var = ctk.StringVar(value="500")
        self._PREVIEW_CAP_VALUES = ["100", "500", "1000", "5000", "No cap"]
        self._preview_cap_dropdown = ctk.CTkOptionMenu(
            preview_header_mid, variable=self._preview_cap_var,
            values=self._PREVIEW_CAP_VALUES,
            width=85, font=ctk.CTkFont(size=11),
            command=self._on_preview_cap_changed,
        )
        self._preview_cap_dropdown.pack(side="right")
        Tooltip(self._preview_cap_dropdown,
                "Preview cap — max matches rendered in this pane. The full result is always in the report files. Default 500.",
                anchor="left")
        self._preview_cap_lbl = ctk.CTkLabel(
            preview_header_mid, text="Preview cap:",
            font=ctk.CTkFont(size=11),
        )
        self._preview_cap_lbl.pack(side="right", padx=(10, 3))

        # Preview Size — moved here from the (now-removed) top header row.
        self._preview_font_size = 11
        self._preview_size_var = ctk.StringVar(value="11")
        preview_size_menu = ctk.CTkOptionMenu(
            preview_header_mid, variable=self._preview_size_var,
            values=["8", "9", "10", "11", "12", "13", "14", "16", "18", "20"],
            width=65, font=ctk.CTkFont(size=11),
            command=self._on_preview_size_changed,
        )
        preview_size_menu.pack(side="right")
        self._preview_size_menu_tooltip = Tooltip(preview_size_menu, __import__("peekdocs.i18n", fromlist=["t"]).t("preview_size_tooltip"), anchor="left")
        self._preview_size_lbl = ctk.CTkLabel(preview_header_mid, text=__import__("peekdocs.i18n", fromlist=["t"]).t("preview_size_label"), font=ctk.CTkFont(size=11))
        self._preview_size_lbl.pack(side="right", padx=(0, 3))

        # ── Label row: Results Preview + count + Clear ───────────────
        # Pushed down one row from the dropdown row above for breathing
        # room and to give the label/Clear pair a clean baseline.
        preview_label_row = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        preview_label_row.pack(fill="x", padx=5, pady=(2, 0))

        self._preview_label = ctk.CTkLabel(preview_label_row, text=_t("results_preview_label"),
                                      font=ctk.CTkFont(size=12, weight="bold"))
        self._preview_label.pack(side="left")
        self._preview_label_tooltip = Tooltip(self._preview_label, _t("results_preview_tooltip"))
        # _preview_count_label removed — the same numbers now live in
        # the search-results headline below this row, so showing them
        # twice was redundant. Configure-call sites are guarded with
        # hasattr to keep working unchanged.
        self._clear_preview_btn = ctk.CTkButton(
            preview_label_row, text=_t("clear_preview_label"), width=100,
            font=ctk.CTkFont(size=11),
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=self._clear_preview,
        )
        self._clear_preview_btn.pack(side="left", padx=(8, 0))
        self._clear_preview_tooltip = Tooltip(self._clear_preview_btn, _t("clear_preview_tooltip"))

        # Chart — opens a matplotlib popup with the "Top 10 files by
        # match count" bar chart (mirrors the browser GUI's Chart tab).
        self._chart_btn = ctk.CTkButton(
            preview_label_row, text="Chart", width=70,
            font=ctk.CTkFont(size=11),
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=self._show_match_chart,
        )
        self._chart_btn.pack(side="left", padx=(4, 0))
        Tooltip(self._chart_btn,
                "Open a bar chart of the top 10 files by match count for the most recent search. "
                "Matplotlib renders in a separate window.",
                anchor="left")

        # Reorder: move the search-results headline and the Matched /
        # Excluded buttons row to sit below the Results Preview label
        # row. They were created earlier (and packed at the top of
        # preview_frame) so the buttons could be referenced by their
        # later pack/forget call sites; now we slide them down to the
        # spot the user wants them in.
        self._results_summary_label.pack_configure(after=preview_label_row)
        _results_button_row.pack_configure(after=self._results_summary_label)

        # Cap-status row — sits below the middle row, full width, with
        # the browser-style "All N matches rendered…" / "Preview shows
        # the first M of N matches…" wording. The dropdown itself lives
        # in the middle row above; this is just the explanatory text.
        cap_status_row = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        cap_status_row.pack(fill="x", padx=8, pady=(2, 2))

        self._preview_cap_status = ctk.CTkLabel(
            cap_status_row, text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray60"),
            anchor="w", justify="left", wraplength=500,
        )
        self._preview_cap_status.pack(side="left", fill="x", expand=True)

        preview_text_frame = tk.Frame(self.preview_frame)
        preview_text_frame.pack(fill="both", expand=True, padx=0, pady=(2, 0))

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
                self.status_label.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("status_copied_to_clipboard"),
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
        """Build the Step 3 label row and the report-format buttons row.

        Step 3 is just a pointer to Advanced Search Options below — no
        controls. The DOCX/TXT/CSV/JSON/PDF/HTML "open report" buttons
        plus Delete-on-Close live in a separate frame placed below the
        status line (gridded by _app.py)."""
        self.matched_files_button = ctk.CTkButton(
            self._input_frame,
            text="Matched Files",
            width=140,
            command=self._show_matched_files_popup,
            font=ctk.CTkFont(size=13),
        )
        Tooltip(self.matched_files_button, "View the list of files that contained matches (click a file to open it). The number of files shown here may be affected by the Max Matches setting in Advanced Search Options — if the report is capped, only files with matches within the cap are listed")

        # ── Step 3 row: Step badge + pointer to Advanced ─────────────
        self.report_frame = ctk.CTkFrame(self._input_frame, fg_color="transparent")
        import tkinter as _tk_step4
        from peekdocs.i18n import t as _t
        self._step_lbl_3 = _tk_step4.Label(self.report_frame, text=_t("step_3_label"), font=("TkDefaultFont", 14, "bold"),
                                       fg="white", bg="#2196F3")
        self._step_lbl_3.pack(side="left", padx=(0, 8))

        self._step_3_msg = ctk.CTkLabel(
            self.report_frame,
            text="Use 'Advanced Search Options' below to configure search parameters",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray70"),
            anchor="w",
        )
        self._step_3_msg.pack(side="left", padx=(0, 0))

        # ── Open-report buttons row (sits below status_row at row 6) ──
        self.report_btn_frame = ctk.CTkFrame(self._input_frame, fg_color="transparent")

        # "Open Report:" label — packed first so it sits to the left of
        # the DOCX button. The format buttons are packed by _app.py
        # using side="left" so they line up to the right of this label.
        self._open_report_lbl = ctk.CTkLabel(
            self.report_btn_frame, text="Open Report:",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray70"),
        )
        self._open_report_lbl.pack(side="left", padx=(0, 8))

        btn_font = ctk.CTkFont(size=12)
        btn_w = 60
        _report_color_note = "Green = report file exists and is ready to open. Red = not generated (enable in Advanced Search Options under Output Formats)."
        self.report_btn_docx = ctk.CTkButton(
            self.report_btn_frame, text="DOCX", width=btn_w, font=btn_font,
            command=lambda: self._open_report_format("docx"),
        )
        Tooltip(self.report_btn_docx, f"Open the highlighted Word report (.docx) — every match in yellow with context. Default ON; uncheck the DOCX box in Advanced Search Options under Output formats to skip it. {_report_color_note}", anchor="above")
        self.report_btn_txt = ctk.CTkButton(
            self.report_btn_frame, text="TXT", width=btn_w, font=btn_font,
            command=lambda: self._open_report_format("txt"),
        )
        Tooltip(self.report_btn_txt, f"Open the plain-text report (.txt). The .txt report is ALWAYS written — it cannot be disabled, because the GUI's Results Preview pane and Matched Files popup both parse it. So this button is always green after a search. {_report_color_note.replace(' Red = not generated (enable in Advanced Search Options under Output Formats).', '')}", anchor="above")
        self.report_btn_csv = ctk.CTkButton(
            self.report_btn_frame, text="CSV", width=btn_w, font=btn_font,
            command=lambda: self._open_report_format("csv"),
        )
        Tooltip(self.report_btn_csv, f"Open the CSV report — one row per match, importable into Excel or Google Sheets. {_report_color_note}", anchor="above")
        self.report_btn_json = ctk.CTkButton(
            self.report_btn_frame, text="JSON", width=btn_w, font=btn_font,
            command=lambda: self._open_report_format("json"),
        )
        Tooltip(self.report_btn_json, f"Open the JSON report — structured data for scripting or further processing. {_report_color_note}", anchor="above")
        self.report_btn_pdf = ctk.CTkButton(
            self.report_btn_frame, text="PDF", width=btn_w, font=btn_font,
            command=lambda: self._open_report_format("pdf"),
        )
        Tooltip(self.report_btn_pdf, f"Open the PDF report — highlighted matches, portable format. {_report_color_note}", anchor="above")
        self.report_btn_html = ctk.CTkButton(
            self.report_btn_frame, text="HTML", width=btn_w, font=btn_font,
            command=lambda: self._open_report_format("html"),
        )
        Tooltip(self.report_btn_html, f"Open the HTML report — view in any web browser. The file is stored locally on your computer, not on the internet — nothing is uploaded or made public. {_report_color_note}", anchor="above")

        # Delete on Close checkbox removed from the main page — the
        # equivalent control lives inside Advanced Search Options
        # (_cb_delete_adv) and shares the same delete_reports_var, so
        # the cleanup behavior on app close is unchanged.



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
        # Manage Indexes help — unified blue chip styling.
        idx_help_btn = ctk.CTkButton(
            idx_header, text="?", width=30, height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#1565C0", text_color="white",
            hover_color="#0D47A1",
            corner_radius=15,
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
            fg_color="#D32F2F", hover_color="#B71C1C",
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
        # Lives in the footer area (created in _app.py) so the toolbar
        # spans the full window width below the left/right split.
        self.bottom_frame = ctk.CTkFrame(self._footer_area, fg_color="transparent")
        self.bottom_frame.pack(fill="x", padx=15, pady=(0, 8))

        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=1)
        self.bottom_frame.grid_columnconfigure(2, weight=1)

        # Left group
        left_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="w")

        from peekdocs.i18n import t as _t
        self._readme_button = ctk.CTkButton(
            left_frame,
            text=_t("readme_button_label"),
            width=70,
            fg_color="transparent",
            text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=lambda: webbrowser.open("https://github.com/exbuf/peekdocs/tree/main"),
            font=ctk.CTkFont(size=13),
        )
        self._readme_button.pack(side="left")
        self._readme_tooltip = Tooltip(self._readme_button, _t("readme_button_tooltip"), anchor="above")

        self.help_button = ctk.CTkButton(
            left_frame,
            text=_t("user_guide_button_label"),
            width=90,
            fg_color="transparent",
            text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=self.open_help,
            font=ctk.CTkFont(size=13),
        )
        self.help_button.pack(side="left")
        self._user_guide_tooltip = Tooltip(self.help_button, _t("user_guide_button_tooltip"), anchor="above")

        # Close button packed into the left group (after README and User
        # Guide). Previously gridded at column=1 of bottom_frame, which
        # placed it at the visual horizontal center of the main page —
        # exactly where popup Close buttons sit when popups are centered,
        # making it easy to misclick when dismissing a popup. Now it lives
        # with the other navigation buttons on the left.
        self._close_main_btn = ctk.CTkButton(
            left_frame,
            text=_t("close_button_label"),
            width=70,
            fg_color="transparent",
            text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=self.destroy,
            font=ctk.CTkFont(size=13),
        )
        self._close_main_btn.pack(side="left")
        self._close_main_tooltip = Tooltip(self._close_main_btn, _t("close_button_tooltip"), anchor="above")

        # Middle group — App Size + Language pickers, centered in the
        # bottom toolbar. The pickers use _UpwardOptionMenu so their
        # dropdowns grow UP from the toolbar instead of off the bottom
        # edge of the window.
        middle_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        middle_frame.grid(row=0, column=1, sticky="")

        self._TEXT_SIZE_KEYS = ["Small", "Normal", "Large", "Extra Large", "Huge"]
        self._app_size_lbl = ctk.CTkLabel(
            middle_frame,
            text=__import__("peekdocs.i18n", fromlist=["t"]).t("app_size_label"),
            font=ctk.CTkFont(size=11),
        )
        self._app_size_lbl.pack(side="left", padx=(0, 3))
        self._app_size_menu = _UpwardOptionMenu(
            middle_frame,
            values=[self._text_size_localized(k) for k in self._TEXT_SIZE_KEYS],
            width=110, font=ctk.CTkFont(size=11),
            command=self._app_size_menu_pick,
        )
        self._app_size_menu.set(self._text_size_localized(self._text_size_var.get() or "Normal"))
        self._app_size_menu.pack(side="left", padx=(0, 14))
        self._app_size_menu_tooltip = Tooltip(
            self._app_size_menu,
            __import__("peekdocs.i18n", fromlist=["t"]).t("app_size_tooltip"),
            anchor="above",
        )

        from peekdocs.i18n import LANGUAGES as _LANGS, current_language as _curlang
        from peekdocs.i18n import t as _t_lang_bot
        self._lang_label = ctk.CTkLabel(
            middle_frame, text=_t_lang_bot("language_picker_label"),
            font=ctk.CTkFont(size=11),
        )
        self._lang_label.pack(side="left", padx=(0, 3))
        self._lang_picker = _UpwardOptionMenu(
            middle_frame,
            values=list(_LANGS.values()),
            command=self._on_lang_picker_change,
            width=130, font=ctk.CTkFont(size=11),
        )
        self._lang_picker.set(_LANGS.get(_curlang(), "English"))
        self._lang_picker.pack(side="left")
        Tooltip(self._lang_picker,
                "Language (experiment scope — currently translates the four main-page Step badges and tooltips, plus the Run Standard Search / Search Suites / Regex Search buttons + their tooltips. Everything else stays English).",
                anchor="above")

        # Right group
        right_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        right_frame.grid(row=0, column=2, sticky="e")

        from peekdocs.i18n import t as _t
        self.about_button = ctk.CTkButton(
            right_frame,
            text=_t("about_button_label"),
            width=70,
            fg_color="transparent",
            text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=self.show_about,
            font=ctk.CTkFont(size=13),
        )
        self.about_button.pack(side="right", padx=5)
        self._about_tooltip = Tooltip(self.about_button, _t("about_button_tooltip"), anchor="above-left")

        # Tools menu — consolidates utilities, settings, and maintenance
        def _show_tools_menu():
            import tkinter as tk
            menu = tk.Menu(self, tearoff=0, font=("TkDefaultFont", 12))
            def _dark_sep():
                menu.add_command(label="─" * 50, state="disabled",
                                 font=("TkDefaultFont", 2),
                                 foreground="#999999" if ctk.get_appearance_mode() == "Dark" else "gray40")
            # Folder analysis (alphabetical)
            menu.add_command(label="Collection Summary — one-page overview combining all file-analysis insights", command=self._run_collection_summary)
            menu.add_command(label="Duplicate Finder — find identical files in the folder", command=self._run_duplicate_scan)
            menu.add_command(label="Empty Files — find zero-length or blank files", command=self._run_empty_file_scan)
            menu.add_command(label="File Age Distribution — histogram of files by modification age", command=self._run_file_age_distribution)
            menu.add_command(label="File Inventory — summary of all files by type, size, and date", command=self._run_file_inventory)
            menu.add_command(label="Large Files — find the biggest files in the folder", command=self._run_large_file_scan)
            menu.add_command(label="Protected Files — find password-protected or encrypted files", command=self._run_protected_scan)
            menu.add_command(label="Recent Changes — files modified in the last 7 / 30 / 90 days", command=self._run_recent_changes)
            menu.add_command(label="Unsearchable Files — files peekdocs cannot search and why", command=self._run_unsearchable_files)
            _dark_sep()
            # User tools (alphabetical)
            menu.add_command(label="Bookmarks — pinned files for quick access", command=self._show_bookmarks)
            menu.add_command(label="Diff Snapshots — compare two saved scans to see what changed", command=self._open_diff_snapshots)
            menu.add_command(label="Indexes — build, delete, and refresh search indexes", command=self._toggle_index_options)
            menu.add_command(label="Regex Tester — paste sample text and watch matches highlight in real time", command=lambda: self._show_regex_tester())
            menu.add_command(label="Schedule Search — generate a command to run searches on a schedule (cron / Task Scheduler)", command=self._open_schedule_search)
            menu.add_command(label="Search History — log of past searches and results", command=self._show_search_history)
            menu.add_command(label="Search Wizard — pick a search type (phone, email, dollar range, date, etc.) and the wizard configures it for you", command=self._open_search_wizard_guide)
            # Search Suites moved to main screen next to Wizard
            _dark_sep()
            # App management (alphabetical)
            menu.add_command(label="All Collections — find saved searches across all folders", command=self._show_all_collections)
            menu.add_command(label="View All peekdocs Files — list every peekdocs-created file in the Search Folder", command=self._show_app_files)
            menu.add_command(label="Error Log — see which files couldn't be read", command=self.open_error_log)
            menu.add_command(label="System Check — verify Python, dependencies, and disk space", command=self._run_system_check)
            _dark_sep()
            # Cleanup
            menu.add_command(label="Clear Files — wipe session files or choose specific files to delete", command=self._clear_files)
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
            # Language picker is now in the main page header row
            # (top-left); no longer duplicated as a Tools-menu cascade.
            btn = self._tools_btn
            x = btn.winfo_rootx() - 400
            y = btn.winfo_rooty() - 350
            menu.tk_popup(x, y)

        self._tools_btn = ctk.CTkButton(
            right_frame,
            text=__import__("peekdocs.i18n", fromlist=["t"]).t("tools_button_label") + " \u25b2",
            width=70,
            fg_color="transparent",
            text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=_show_tools_menu,
            font=ctk.CTkFont(size=13),
        )
        self._tools_btn.pack(side="right", padx=5)
        self._tools_tooltip = Tooltip(self._tools_btn, __import__("peekdocs.i18n", fromlist=["t"]).t("tools_button_tooltip"), anchor="above-left")

        _t_h = __import__("peekdocs.i18n", fromlist=["t"]).t
        hover_label = _t_h("tooltips_on_label") if Tooltip.enabled else _t_h("tooltips_off_label")
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
        self._tooltips_toggle_tooltip = Tooltip(self._hover_toggle_btn, __import__("peekdocs.i18n", fromlist=["t"]).t("tooltips_button_tooltip"), anchor="above-left")

        # Keep references for tooltip toggle (used by _toggle_tooltips)
        self.tooltip_toggle_btn = None
        self.view_error_log_bottom = None


    # ── Actions ──────────────────────────────────────────────



    def toggle_advanced(self):
        """Expand or collapse the inline Advanced Search Options body."""
        from peekdocs.i18n import t as _t
        if self.advanced_visible:
            self._close_advanced_window()
        else:
            self._advanced_body.pack(fill="both", expand=True)
            self._advanced_header_btn.configure(text="▼ " + _t("advanced_label"))
            self.advanced_visible = True

    def _close_advanced_window(self):
        """Collapse the inline Advanced Search Options body."""
        from peekdocs.i18n import t as _t
        self._advanced_body.pack_forget()
        self._advanced_header_btn.configure(text="▶ " + _t("advanced_label"))
        self.advanced_visible = False



    def _toggle_index_options(self):
        """Toggle the Manage Indexes window open or closed."""
        if self.index_visible:
            self._close_index_window()
        else:
            # Center on main window before showing so the popup opens on the
            # same monitor as the main page in multi-monitor setups.
            self._center_popup_on_main(self.index_window, 580, 310)
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
        # Recent Searches help — unified blue chip styling.
        ctk.CTkButton(
            _recent_header, text="?", width=30, height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#1565C0", text_color="white",
            hover_color="#0D47A1",
            corner_radius=15,
            command=lambda: self._show_recent_searches_help(popup),
        ).pack(side="right")

        listbox = tk.Listbox(popup, font=("TkDefaultFont", 12),
                             selectmode=tk.SINGLE, activestyle="none",
                             bg="#2b2b2b", fg="white", selectbackground="#1f6aa5",
                             highlightthickness=0, borderwidth=1, relief="sunken",
                             width=60, height=min(len(self._recent_searches), 10))
        listbox.pack(padx=10, pady=(0, 8))
        # Each entry is a config dict (or legacy plain string). The
        # listbox shows just the search-terms portion so the user can
        # identify entries; selection restores the full config.
        for entry in self._recent_searches:
            listbox.insert("end", self._recent_entry_terms(entry))

        def _select(event=None):
            sel = listbox.curselection()
            if not sel:
                return
            entry = self._recent_searches[sel[0]]
            self._apply_search_config(entry)
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
            self.status_label.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("status_recent_searches_cleared"), text_color=("blue", "#66BBFF"))

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
        n("The last 10 searches you ran are remembered here so you can")
        n("re-run them without rebuilding the configuration. Each entry")
        n("captures the FULL search context — not just the words you")
        n("typed:")
        n("  • the search terms")
        n("  • the search folder")
        n("  • every Advanced Search Options setting (AND/OR mode,")
        n("    recursive, whole word, regex, fuzzy, wildcard, OCR,")
        n("    expression, inverse, file types, exclude terms,")
        n("    proximity / context lines, max matches, max file size,")
        n("    cores, range, specific files, output formats, output")
        n("    directory, timestamp, delete-on-close, and the rest).")
        n("Select an entry and click Use (or double-click) to restore")
        n("all of those settings in one shot.\n")

        b("How this differs from the ↑ / ↓ arrows in the search bar")
        n("The arrow-key shortcut next to Step 2 cycles through the")
        n("same recent list, but only the search-terms text is copied")
        n("back into the search bar — your current Advanced Search")
        n("Options are left as you have them. Use the arrows when you")
        n("want to reuse just the wording with the current settings;")
        n("use this popup when you want the whole configuration back.\n")

        b("How they're stored")
        n("Recent searches are saved to ~/.peekdocsrc and persist")
        n("across sessions. They're available every time you open")
        n("the app.\n")

        b("Recent Searches vs Search History")
        n("\u2022 Recent Searches (this popup) \u2014 last 10 full configs,")
        n("  persists across sessions. For one-click re-run.")
        n("\u2022 Search History (Tools menu) \u2014 saved to disk in")
        n("  ~/.peekdocs_history.json, persists across sessions,")
        n("  includes date, match count, file count, and elapsed time.")
        n("  For reviewing past searches.\n")

        b("Clear button")
        n("Clears the recent searches list from memory and disk.")
        n("Does NOT affect Search History.")

        b("\nSaved Searches")
        n("To save a search permanently under a name so you can reload")
        n("it later, use the Save button on the main screen. Saved")
        n("searches persist across sessions and can be grouped into")
        n("suites — useful for configurations you want to keep beyond")
        n("the 10-entry Recent rolling window.")

        txt.configure(state="disabled")
        self._apply_dark_theme(help_win)

    # ── Search-bar history navigation (Up / Down arrows) ─────────────
    # Keysyms that should NOT reset the history-navigation cursor.
    # Pure cursor / modifier / focus keys leave the recalled entry
    # editable in place; anything else (typing, Backspace, paste,
    # Delete, etc.) signals the user has started a fresh draft and
    # the cursor is reset.
    _SEARCH_HISTORY_SAFE_KEYS = (
        "Up", "Down", "Left", "Right", "Home", "End",
        "Shift_L", "Shift_R", "Control_L", "Control_R",
        "Alt_L", "Alt_R", "Meta_L", "Meta_R",
        "Super_L", "Super_R", "Caps_Lock", "Num_Lock",
        "Return", "Tab", "Escape",
    )

    def _on_search_key(self, event):
        """Search-bar <Key> handler: hide the assistant label on any
        non-Return/Tab key, and reset the history-navigation cursor
        whenever the user types something that changes the entry."""
        if event.keysym not in ("Return", "Tab"):
            try:
                self._assistant_label.grid_remove()
            except Exception:
                pass
        if event.keysym not in self._SEARCH_HISTORY_SAFE_KEYS:
            self._search_history_idx = -1
            self._search_history_draft = ""

    def _search_history_prev(self, event=None):
        """Up arrow in the search bar — recall an older entry from
        the recent-searches list. First press snapshots whatever
        the user had typed so Down can restore it later."""
        recents = getattr(self, "_recent_searches", None) or []
        if not recents:
            return "break"
        idx = getattr(self, "_search_history_idx", -1)
        if idx == -1:
            self._search_history_draft = self.search_entry.get()
        if idx + 1 >= len(recents):
            try:
                self.bell()
            except Exception:
                pass
            return "break"
        self._search_history_idx = idx + 1
        # Arrow keys only restore the search-terms text, not the full
        # config — that's the popup's job. Pull the terms out of either
        # the dict or the legacy plain-string entry.
        self._replace_search_text(self._recent_entry_terms(recents[self._search_history_idx]))
        return "break"

    def _search_history_next(self, event=None):
        """Down arrow in the search bar — recall a newer entry, or
        restore the snapshot draft once past the most-recent entry."""
        idx = getattr(self, "_search_history_idx", -1)
        if idx == -1:
            return "break"
        recents = getattr(self, "_recent_searches", None) or []
        new_idx = idx - 1
        if new_idx == -1:
            self._replace_search_text(getattr(self, "_search_history_draft", ""))
            self._search_history_idx = -1
            return "break"
        self._search_history_idx = new_idx
        self._replace_search_text(self._recent_entry_terms(recents[new_idx]))
        return "break"

    def _replace_search_text(self, text):
        """Replace the search bar contents and move the cursor to
        the end. Shared by Up / Down arrow navigation."""
        self.search_entry.delete(0, "end")
        if text:
            self.search_entry.insert(0, text)
        try:
            self.search_entry.icursor("end")
        except Exception:
            pass

    def _save_ui_preference(self, key, value):
        """Auto-save a single UI preference to ~/.peekdocsrc."""
        try:
            from peekdocs.cli import _load_config, _save_config
            config = _load_config()
            config[key] = value
            _save_config(config)
        except Exception:
            pass

    def _on_lang_picker_change(self, display_name):
        """CTkOptionMenu callback — receives the display name (e.g.
        ``'Español'``), reverse-looks-it-up to the language code, and
        routes through ``_set_language`` so the label re-render and
        config-persist flow is shared between the picker and any
        future menu/keyboard entry points."""
        from peekdocs.i18n import LANGUAGES
        code = next((c for c, n in LANGUAGES.items() if n == display_name), None)
        if code:
            self._set_language(code)

    def _text_size_localized(self, canonical_key):
        """Translate a canonical English text-size key (one of
        ``Small`` / ``Normal`` / ``Large`` / ``Extra Large`` /
        ``Huge``) into the active language's display string. Used to
        build the App Size dropdown's `values` list."""
        from peekdocs.i18n import t
        key = "text_size_" + canonical_key.lower().replace(" ", "_") + "_label"
        return t(key)

    def _text_size_canonical(self, display_value):
        """Reverse lookup — given a localized display string from the
        App Size dropdown, return the canonical English key (or
        ``"Normal"`` if no match). Lets the dropdown callback
        translate the user's pick back to the stable internal value
        before calling the scales-dict logic."""
        for k in getattr(self, "_TEXT_SIZE_KEYS", ["Small", "Normal", "Large", "Extra Large", "Huge"]):
            if self._text_size_localized(k) == display_value:
                return k
        return "Normal"

    def _app_size_menu_pick(self, display_value):
        """CTkOptionMenu callback for the App Size dropdown. Receives
        the user's localized pick, maps it back to the canonical
        English key, syncs `_text_size_var`, and calls the existing
        `_on_text_size_changed` so the scales-dict lookup keeps
        working unchanged."""
        canonical = self._text_size_canonical(display_value)
        self._text_size_var.set(canonical)
        self._on_text_size_changed(canonical)

    def _set_language(self, code):
        """Switch the UI language for the four main-page Step labels +
        their tooltips. Experiment scope — only those eight strings are
        translatable today; the rest of the UI stays English.

        Mechanics: update the module-level current-language pointer,
        re-`configure(text=…)` each Step label widget, rewrite each
        Tooltip's `text` attribute (the Tooltip class reads the
        attribute lazily on each hover, so no widget recreation is
        needed), and persist the selection to ~/.peekdocsrc so the
        next launch picks the same language."""
        from peekdocs.i18n import set_language, t
        set_language(code)
        # Re-render the four Step labels. Each was stashed on self in
        # the corresponding _build_* method so we can find them here.
        try:
            self._step_lbl_1.configure(text=t("step_1_label"))
            self._step_lbl_2.configure(text=t("step_2_label"))
            self._step_lbl_3.configure(text=t("step_3_label"))
            self._step_lbl_4.configure(text=t("step_4_label"))
        except Exception:
            pass
        # Re-render the three main-screen action buttons. Each writes
        # the idle-state label (Run Standard Search / Search Suites /
        # Regex Search). If the user happens to change language while
        # a search is mid-flight, the button text will flip from
        # "Cancel" back to the idle label — minor UX wobble, accepted
        # for experiment scope. The buttons also have their own reset
        # sites scattered across _mixin_search.py, _mixin_tools.py,
        # and _mixin_data.py that have been routed through t() so the
        # active language sticks across search-finish transitions.
        try:
            self.search_button.configure(text=t("run_standard_search_label"))
            self._suites_btn.configure(text=self._stack_label(t("search_suites_label")))
            self._regex_search_btn.configure(text=self._stack_label(t("regex_search_label")))
            # Status / Results Preview / Clear Preview static labels.
            self._status_label_left.configure(text=t("status_label"))
            self._preview_label.configure(text=t("results_preview_label"))
            self._clear_preview_btn.configure(text=t("clear_preview_label"))
            # Bottom-row navigation buttons (left + right groups).
            self._readme_button.configure(text=t("readme_button_label"))
            self.help_button.configure(text=t("user_guide_button_label"))
            self._close_main_btn.configure(text=t("close_button_label"))
            self.about_button.configure(text=t("about_button_label"))
            # Tools button — preserve the trailing "▲" arrow indicator
            # since it's a universal dropdown affordance, not English.
            self._tools_btn.configure(text=t("tools_button_label") + " ▲")
            # Tooltips toggle — pick the right state-dependent key.
            from peekdocs.gui._tooltip import Tooltip as _TT
            self._hover_toggle_btn.configure(
                text=t("tooltips_on_label") if _TT.enabled else t("tooltips_off_label")
            )
            # Page header + both Delete-on-Close checkboxes (Advanced
            # Search Options + main-page report row). The Search Options
            # label was removed from the row above.
            self._page_header_lbl.configure(text=t("page_header_label"))
            self._cb_delete_adv.configure(text=t("delete_on_close_label"))
            # Main-page Delete-on-Close checkbox was removed.
            # Folder row buttons: Browse / +Folder / Single File.
            self.browse_button.configure(text=t("browse_button_label"))
            self._multi_folder_btn.configure(text=t("multi_folder_button_label"))
            self.browse_file_button.configure(text=t("single_file_button_label"))
            # Getting Started tab — re-configure the segmented_button
            # button's visible text. The internal CTk tab name stays
            # "Getting Started" so callers like _tabview.set(...) still
            # work; only the user-visible label flips.
            if getattr(self, "_gs_tab_btn", None) is not None:
                self._gs_tab_btn.configure(text=t("getting_started_tab_label"))
            # Search-bar row: Recent button (literal "▼ " prefix kept as
            # the universal dropdown affordance). The Clear button was
            # removed from this row.
            self._recent_btn.configure(text="▼ " + t("recent_searches_label"))
            # "Language:" label next to the picker.
            self._lang_label.configure(text=t("language_picker_label"))
            # Preview-header size labels.
            self._app_size_lbl.configure(text=t("app_size_label"))
            self._preview_size_lbl.configure(text=t("preview_size_label"))
            # App Size dropdown — rebuild values in the new language,
            # then re-select the localized variant of the canonical
            # English key currently held in _text_size_var.
            try:
                new_values = [self._text_size_localized(k) for k in self._TEXT_SIZE_KEYS]
                self._app_size_menu.configure(values=new_values)
                self._app_size_menu.set(self._text_size_localized(self._text_size_var.get() or "Normal"))
            except Exception:
                pass
            # "What's the difference?" hyperlink was removed.
            # Options row: AND / OR / Recursive / Whole Word / Advanced
            # / Use Index / Wizard / Save / Reload. Save and Reload both
            # carry a static ▶ prefix.
            # AND/OR, Recursive, Whole Word, and the Advanced hyperlink
            # were removed from the options row — their labels live only
            # on the corresponding Advanced-panel checkboxes now.
            if hasattr(self, "_advanced_header_btn"):
                # Refresh the inline Advanced header label (prefix preserved).
                arrow = "▼ " if self.advanced_visible else "▶ "
                self._advanced_header_btn.configure(text=arrow + t("advanced_label"))
            self.cb_index_search.configure(text=t("use_index_label"))
            # Search Wizard hyperlink removed — entry lives in the Tools
            # menu now and is rebuilt each time that menu opens.
            self.save_to_collection_btn.configure(text="▶ " + t("save_label"))
            self.load_search_btn.configure(text="▶ " + t("reload_label"))
            # ─── Advanced Search Options panel ───
            try:
                self.advanced_window.title(t("adv_window_title"))
            except Exception:
                pass
            self._adv_cb_and.configure(text=t("adv_and_mode_label"))
            self._adv_cb_rec.configure(text=t("recursive_label"))
            self._adv_cb_fuz.configure(text=t("adv_fuzzy_label"))
            self._adv_cb_wild.configure(text=t("adv_wildcard_label"))
            self._adv_cb_ocr.configure(text=t("adv_ocr_label"))
            self._adv_cb_regex.configure(text=t("adv_regex_label"))
            self._adv_cb_whole_word.configure(text=t("whole_word_label"))
            self._adv_cb_expr.configure(text=t("adv_expression_label"))
            self._adv_cb_inverse.configure(text=t("adv_inverse_label"))
            self._adv_lbl_exclude.configure(text=t("adv_exclude_label"))
            self._adv_lbl_file_types.configure(text=t("adv_file_types_label"))
            self._adv_lbl_word_proximity.configure(text=t("adv_word_proximity_label"))
            self._adv_lbl_lines_before.configure(text=t("adv_lines_before_label"))
            self._adv_lbl_lines_after.configure(text=t("adv_lines_after_label"))
            self._adv_lbl_cores.configure(text=t("adv_cores_to_use_label"))
            self._adv_lbl_max_matches.configure(text=t("adv_max_matches_label"))
            self._adv_lbl_max_file_size.configure(text=t("adv_max_file_size_label"))
            self._adv_lbl_range.configure(text=t("adv_range_label"))
            self._adv_lbl_specific_files.configure(text=t("adv_specific_files_label"))
            self._adv_lbl_save_as.configure(text=t("adv_save_report_as_label"))
            self._adv_lbl_append_to.configure(text=t("adv_append_report_to_label"))
            self._adv_lbl_output_dir.configure(text=t("adv_output_dir_label"))
            # "Also ==>" label was removed; no widget to refresh.
            self._adv_cb_ts.configure(text=t("adv_timestamp_filename_label"))
            self._adv_cb_clear_hist.configure(text=t("adv_clear_history_label"))
            self._adv_cb_restrict.configure(text=t("adv_restrict_perms_label"))
            self._adv_cb_notify_complete.configure(text=t("adv_notify_complete_label"))
            self._adv_reset_btn.configure(text=t("adv_reset_all_label"))
            self._adv_save_btn.configure(text=t("adv_save_defaults_label"))
            # "↑ Collapse" link is hardcoded (navigation marker, not a
            # translatable button label) — no refresh needed.
            self._adv_restore_btn.configure(text=t("adv_restore_defaults_label"))
            self._adv_reset_defaults_btn.configure(text=t("adv_restore_factory_label"))
        except Exception:
            pass
        try:
            self._step_1_tooltip.text = t("step_1_tooltip")
            self._step_2_tooltip.text = t("step_2_tooltip")
            # Step 3 no longer carries a tooltip — it's now a pointer label.
            self._step_4_tooltip.text = t("step_4_tooltip")
            self._run_search_tooltip.text = t("run_standard_search_tooltip")
            self._suites_tooltip.text = t("search_suites_tooltip")
            self._regex_search_tooltip.text = t("regex_search_tooltip")
            # Status / Results Preview / Clear Preview tooltips.
            self._status_label_tooltip.text = t("status_tooltip")
            self._preview_label_tooltip.text = t("results_preview_tooltip")
            self._clear_preview_tooltip.text = t("clear_preview_tooltip")
            # Bottom-row tooltips.
            self._readme_tooltip.text = t("readme_button_tooltip")
            self._user_guide_tooltip.text = t("user_guide_button_tooltip")
            self._close_main_tooltip.text = t("close_button_tooltip")
            self._about_tooltip.text = t("about_button_tooltip")
            self._tools_tooltip.text = t("tools_button_tooltip")
            self._tooltips_toggle_tooltip.text = t("tooltips_button_tooltip")
            # Delete on Close tooltips (page header and the gone
            # Search Options label have no tooltip to refresh).
            self._cb_delete_adv_tooltip.text = t("delete_on_close_tooltip")
            # Main-page Delete-on-Close checkbox tooltip removed.
            # Folder row + Getting Started tab tooltips.
            self._browse_button_tooltip.text = t("browse_button_tooltip")
            self._multi_folder_btn_tooltip.text = t("multi_folder_button_tooltip")
            self._browse_file_button_tooltip.text = t("single_file_button_tooltip")
            if getattr(self, "_gs_tab_tooltip", None) is not None:
                self._gs_tab_tooltip.text = t("getting_started_tab_tooltip")
            # Clear button removed — no tooltip to refresh.
            self._recent_btn_tooltip.text = t("recent_searches_tooltip")
            # Options-row tooltips.
            # The Advanced hyperlink was replaced by the inline header
            # button — that's where the wording lives now.
            if hasattr(self, "_advanced_header_btn"):
                arrow = "▼ " if getattr(self, "advanced_visible", False) else "▶ "
                self._advanced_header_btn.configure(text=arrow + t("advanced_label"))
            self._cb_index_search_tooltip.text = t("use_index_tooltip")
            # Wizard tooltip lived on the deleted hyperlink button —
            # the Tools menu entry doesn't carry a refreshable tooltip.
            self._save_to_collection_btn_tooltip.text = t("save_tooltip")
            self._load_search_btn_tooltip.text = t("reload_tooltip")
            # Status-row count-button tooltips + preview-header size
            # tooltips. The buttons' dynamic count text doesn't
            # auto-update on language change — same caveat as the
            # status label's dynamic messages.
            self._matched_files_link_tooltip.text = t("matched_files_tooltip")
            self._excluded_files_btn_tooltip.text = t("excluded_files_tooltip")
            self._app_size_menu_tooltip.text = t("app_size_tooltip")
            self._preview_size_menu_tooltip.text = t("preview_size_tooltip")
        except Exception:
            pass
        self._save_ui_preference("language", code)

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

    def _center_popup_on_main(self, win, width, height):
        """Center a popup on the main window's monitor and deiconify it.

        Use after all widgets in the popup have been packed/gridded.
        The popup must have been win.withdraw()'n immediately after
        creation so widget setup happened invisibly — otherwise the
        user sees the popup briefly open at the system primary monitor
        and jump to the main window's monitor.

        Centering math uses self.winfo_rootx/y, which return the main
        window's screen coordinates — so the popup lands on whichever
        monitor the main window currently lives on. Fixes the recurring
        multi-monitor bug where popups opened on the laptop screen even
        when the main window was on an external display.
        """
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - width) // 2
        y = self.winfo_rooty() + (self.winfo_height() - height) // 2
        win.geometry(f"{width}x{height}+{x}+{y}")
        win.deiconify()

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
        if _sys_tt.platform != "win32":
            # macOS/Linux: tk's `option add` writes to the application-wide
            # option database, not per-window — so option_add values set
            # during a dark-mode popup persist after that popup is
            # destroyed. If we only set them in dark mode and skip light
            # mode, a subsequent light-mode popup inherits the stale dark
            # values for its plain tk widgets (Text, Listbox, Canvas,
            # etc.) and visually stays dark. Always set mode-appropriate
            # values so each popup overwrites whatever the previous one
            # left in the option DB.
            if _is_dark:
                _bg = "#2b2b2b"
                _fg = "#e0e0e0"
                _entry_bg = "#3a3a3a"
                _btn_bg = "#555555"
                _btn_fg = "white"
                _listbox_bg = "#2b2b2b"
                _listbox_fg = "white"
                # Place offscreen while building widgets to reduce the
                # white flash on macOS dark mode startup. The popup's
                # own geometry() call moves it onscreen after setup.
                win.geometry("+99999+99999")
            else:
                _bg = "#f0f0f0"
                _fg = "black"
                _entry_bg = "white"
                _btn_bg = "#e1e1e1"
                _btn_fg = "black"
                _listbox_bg = "white"
                _listbox_fg = "black"
            win.configure(bg=_bg)
            win.option_add("*Background", _bg)
            win.option_add("*Foreground", _fg)
            win.option_add("*Entry.Background", _entry_bg)
            win.option_add("*Entry.Foreground", _fg)
            win.option_add("*Entry.insertBackground", _fg)
            win.option_add("*Listbox.Background", _listbox_bg)
            win.option_add("*Listbox.Foreground", _listbox_fg)
            win.option_add("*Text.Background", _entry_bg)
            win.option_add("*Text.Foreground", _fg)
            win.option_add("*Text.insertBackground", _fg)
            win.option_add("*Button.Background", _btn_bg)
            win.option_add("*Button.Foreground", _btn_fg)
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

        if _is_dark and _sys_tt.platform != "win32":
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
        from peekdocs.i18n import t
        Tooltip.enabled = not Tooltip.enabled
        self._save_ui_preference("hover_text", Tooltip.enabled)
        if hasattr(self, "_hover_toggle_btn"):
            self._hover_toggle_btn.configure(
                text=t("tooltips_on_label") if Tooltip.enabled else t("tooltips_off_label")
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
        self._save_ui_preference("match_all", self.and_mode_var.get() == "on")



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


