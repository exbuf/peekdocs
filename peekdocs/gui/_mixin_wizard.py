"""PeekDocs GUI — WizardMixin.

Extracted from ``_mixin_tools.py`` in commit-history-continuity terms:
Search Wizard functionality that grew alongside the Tools menu became
its own mixin as of the mixin-tools-split refactor.

The mixin owns two related-but-distinct user surfaces:

* **Search Wizard** (``_open_search_wizard_guide``) — main-screen Search
  Wizard button opens a category-cards popup with 20 pre-built
  search-type forms (keyword OR/AND, exclude, phone/email regex, dollar
  ranges, fuzzy, proximity, Boolean expression, date range, OCR, and
  context-lines). Each form has fields and an Apply callable that calls
  ``_apply_wizard`` to populate the main screen's Search Bar +
  Advanced Search Options.

* **Regex Wizard** (``_open_search_wizard``) — separate popup with a
  categorized regex-pattern picker (35 patterns across 6 categories:
  Common/General, Business/Finance, Legal, Engineering/Technical,
  Real Estate, HR/Admin). Opened both from the Search Wizard guide's
  "Regex Wizard" row and from the Regex Search / Regex Tester popups
  (via the ``on_apply`` callback).

The method name ``_open_search_wizard`` — despite the Regex Wizard
title — stays as-is for git-history continuity.

Methods:
    _open_search_wizard_guide  Main "Search Wizard" category-cards popup
    _apply_wizard              Push wizard settings into the main GUI
    _show_search_wizard_help   "?" help panel for the wizard guide
    _open_search_wizard        Regex Wizard picker + preview + Apply
"""

import sys

import customtkinter as ctk
from tkinter import messagebox

from peekdocs.gui._tooltip import Tooltip
from peekdocs.gui._helpers import _build_wizard_regex


class WizardMixin:
    def _open_search_wizard_guide(self):
        """Open a guided Search Wizard with predefined search patterns."""
        import tkinter as tk

        win = ctk.CTkToplevel(self)
        win.withdraw()  # invisible during widget setup; repositioned + shown at end
        win.title("Search Wizard")
        win.geometry("920x750")
        win.resizable(True, True)
        win.after(50, win.lift)
        win.after(100, win.focus_force)
        win.after(200, lambda: win.title("Search Wizard"))

        header_frame = ctk.CTkFrame(win, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(10, 5))
        ctk.CTkLabel(
            header_frame,
            text="Select one search type (click its radio button \u2014 only one can be active at a time), "
                 "fill in your values, then click Apply. Apply configures the search bar (Step 2) and Advanced Search Options (Step 3) for you \u2014 "
                 "then click Run Standard Search on the Main page. Close this window at any time to cancel \u2014 nothing changes until you click Apply.",
            font=ctk.CTkFont(size=13),
            wraplength=650, justify="center",
        ).pack(expand=True)
        ctk.CTkButton(
            header_frame, text="?", width=30, height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#1565C0", text_color="white",
            hover_color="#0D47A1",
            corner_radius=15,
            command=lambda: self._show_search_wizard_help(win),
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

            ("Regex Wizard", "Opens the Regex Wizard — a categorized regex pattern picker (dates, money, identifiers, contacts, code patterns, networking).\n"
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
             "full paragraph without opening the file. Especially useful for programmers —\n"
             "capture not just the matching line, but the function or block it belongs to.\n"
             "Default is OR mode — after clicking Apply, you can check AND mode or Expression\n"
             "in Advanced Search Options to change how the terms are combined. You can also\n"
             "use a boolean expression directly in the Keywords field (e.g., \"(breach OR violation) AND contract\").",
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
        Tooltip(apply_btn, "Apply the selected row's settings to the main screen — fills the Search Bar and enables matching options (regex, AND, OCR, etc.)", anchor="above")

        clear_sel_btn = ctk.CTkButton(
            apply_group, text="Clear Selection", width=120, height=36,
            command=_clear_selection,
            font=ctk.CTkFont(size=12),
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
        )
        clear_sel_btn.pack(side="left", padx=6, pady=6)
        Tooltip(clear_sel_btn, "Unpick the currently selected row so nothing is chosen — click a different radio button to pick a new one", anchor="above")

        ctk.CTkButton(
            win, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=win.destroy,
            font=ctk.CTkFont(size=12),
        ).pack(pady=(0, 10))

        # Apply dark theme to the plain tk widgets inside this CTkToplevel
        self._apply_dark_theme(win)

        # Center on the main window and show. Withdraw + final geometry +
        # deiconify ensures the popup opens on the same monitor as the main
        # page in multi-monitor setups, with no visible jump. Matches the
        # pattern used by Search Suites and Regex Search popups.
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 920) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 750) // 2
        win.geometry(f"920x750+{x}+{y}")
        win.deiconify()

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
        help_win, _dark = self._themed_toplevel(parent)
        help_win.title("Search Wizard — Help")
        help_win.geometry("700x580")
        help_win.resizable(True, True)
        help_win.transient(parent)

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
                          foreground="#999999" if ctk.get_appearance_mode() == "Dark" else "gray40")

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
        b("Word Proximity — find two terms within N words of each other")
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
        b("Regex Wizard — opens the categorized regex picker with 35")
        b("named patterns across 6 categories (dates, money, identifiers,")
        b("contacts, code patterns, networking). Pick one or more, combine")
        b("with OR or AND, optionally add your own custom regex.")
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
        b("  sudo apt install tesseract-ocr. If you check the OCR box")
        b("  in Advanced Search Options without Tesseract installed,")
        b("  peekdocs shows a modal with the platform-specific install")
        b("  command (as of 1.2.71). See the User Guide 'Prerequisites'")
        b("  section for full details.")
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
        self._apply_dark_theme(help_win)

    def _open_search_wizard(self, on_apply=None):
        """Open the Regex Wizard popup for building regex patterns.

        (The method name stays ``_open_search_wizard`` for git-history
        continuity, but the popup is user-titled "Regex Wizard" so
        it's distinguishable from the main-screen "Search Wizard"
        button — which opens the category-cards search-type wizard,
        not this picker.)

        When ``on_apply`` is provided, the Apply button calls that
        callback with the combined regex string instead of routing it
        into the main search bar + flipping the global regex-mode
        flag. Used by the Regex Tester popup and the Regex Search
        popup's "Pick from Wizard…" buttons to reuse this picker's
        category dropdown + checkbox-list + OR/AND combiner without
        duplicating the UI."""
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

        wiz, _dark = self._themed_toplevel()


        wiz.withdraw()  # hidden during widget setup; centered + shown at end
        wiz.title("Regex Wizard")
        wiz.resizable(True, True)
        self._center_popup_on_main(wiz, 560, 700)

        # Header frame: title centered, ? help button right-aligned.
        wiz_header = tk.Frame(wiz)
        wiz_header.pack(fill="x", padx=15, pady=(10, 2))
        tk.Label(
            wiz_header, text="Regex Wizard",
            font=("TkDefaultFont", 15, "bold"),
        ).pack(side="left", expand=True)
        ctk.CTkButton(
            wiz_header, text="?", width=30, height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#1565C0", text_color="white",
            hover_color="#0D47A1",
            corner_radius=15,
            command=lambda: self._show_regex_builder_help(wiz),
        ).pack(side="right")
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

            # Custom apply path — Regex Tester (and any other future
            # caller that wants the composed regex without the main-
            # screen side effects) routes through the callback. Skip
            # all of the search_entry / regex_var / fuzzy_var / etc.
            # mutations below; the caller decides what to do with the
            # combined string.
            if on_apply is not None:
                try:
                    on_apply(combined)
                finally:
                    wiz.destroy()
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

        ctk.CTkButton(btn_frame, text="Select All", width=80, font=ctk.CTkFont(size=12), command=_select_all).pack(side="left", padx=(0, 5))
        ctk.CTkButton(btn_frame, text="Clear All", width=80, font=ctk.CTkFont(size=12), command=_clear_all).pack(side="left", padx=(0, 5))
        ctk.CTkButton(btn_frame, text="Apply", width=80, font=ctk.CTkFont(size=12), command=_apply).pack(side="right", padx=(5, 0))
        ctk.CTkButton(
            close_frame, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=wiz.destroy,
            font=ctk.CTkFont(size=12),
        ).pack()

        # Load initial category
        _load_category()
        self._apply_dark_theme(wiz)

