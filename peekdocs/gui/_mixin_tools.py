"""PeekDocs GUI — ToolsMixin."""

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
from peekdocs.scanner import RESULT_FILE_PREFIXES
from peekdocs.gui._helpers import (
    _build_command_from_values,
    _parse_summary_text,
    _parse_matched_files,
    _parse_inverse_files,
    _build_wizard_regex,
)
import json
import webbrowser
from tkinter import filedialog, messagebox

class ToolsMixin:
    def _show_search_options_help(self):
        # NOTE: Currently unreachable from the UI. Originally bound to
        # the `?` button on the options-row blue bar (AND/OR / Recursive
        # / Whole Word / Use Index) — that bar was removed in 1.2.0 when
        # those controls were consolidated into Advanced Search Options.
        # The body still describes the pre-1.2.0 layout where these
        # controls lived on the main screen; if you ever re-wire this
        # help, rewrite the body to reflect the inline Advanced panel.
        """Show help for the search options group: AND/OR, Recursive, Whole Word."""
        import tkinter as tk
        win, _dark = self._themed_toplevel()
        win.title("Search Options \u2014 Help")
        win.geometry("740x680")
        win.resizable(True, True)
        win.transient(self)

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
                          foreground="#999999" if ctk.get_appearance_mode() == "Dark" else "gray40")

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
        b("Finds lines where ALL search terms appear. Fewer results,")
        b("but every result contains every term. Useful when searching for")
        b("a combination of words.")
        blank()
        e("  Search: Smith invoice 2024")
        e("  Finds lines with 'Smith' AND 'invoice' AND '2024'")
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
        b("Search Options and click 'Save As Defaults'. Your choices are")
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
        self._apply_dark_theme(win)



    def _show_search_help(self):
        """Show a quick-start guide with search examples by category."""
        import tkinter as tk
        help_win, _dark = self._themed_toplevel()
        help_win.title("Search Examples & Quick-Start Guide")
        help_win.geometry("750x700")
        help_win.resizable(True, True)
        help_win.transient(self)
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
                          foreground="#999999" if ctk.get_appearance_mode() == "Dark" else "gray40")

        txt.insert("end", "TABLE OF CONTENTS\n", "toc_title")
        for section in [
            "What Is peekdocs?", "Who Is It For?", "Getting Started",
            "Standard Search (blue button) vs Regex Search",
            "Regex Search vs Search Suites",
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
        b("archives, and 100+ file types \u2014 all at once, all offline. Your")
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
        txt.insert("end", "\u2022 Researchers", "body_bold_who")
        txt.insert("end", " \u2014 search journal articles (PDF), interview\n", "body")
        b("  transcripts, survey responses, field notes, grant proposals,")
        b("  and historical documents (OCR).")
        blank()
        txt.insert("end", "\u2022 Engineers", "body_bold_who")
        txt.insert("end", " \u2014 search specifications, manuals, design notes,\n", "body")
        b("  vendor PDFs, test reports, datasheets, SPICE netlists,")
        b("  Verilog/VHDL, and maintenance records.")
        blank()
        txt.insert("end", "\u2022 Legal", "body_bold_who")
        txt.insert("end", " \u2014 search contracts, court filings, NDAs,\n", "body")
        b("  briefs, memos, and other case-related documents.")
        blank()
        txt.insert("end", "\u2022 IT / Operations", "body_bold_who")
        txt.insert("end", " \u2014 search procedures, runbooks, exported\n", "body")
        b("  tickets, deployment notes, email archives (.pst, .mbox),")
        b("  error logs, and server configs.")
        blank()
        txt.insert("end", "\u2022 Developers", "body_bold_who")
        txt.insert("end", " \u2014 search code, technical docs, markdown, logs,\n", "body")
        b("  config files, API references, .env files, Dockerfiles,")
        b("  and archived project folders. CLI with --stdout for JSON")
        b("  piping, Python API for integration, and scripting with")
        b("  exit codes (0/1/2) for workflow automation.")
        blank()
        b("You don't need to use every feature. Start with a simple")
        b("keyword search and explore from there.")
        blank()

        h("GETTING STARTED")
        b("All searches are case-insensitive. Type your terms in the Search Bar,")
        b("pick a folder with Browse, and click Run Search. Use the checkboxes")
        b("under Advanced Search Options to change search modes \u2014 do not type flags in")
        b("the search box. Results are saved to peekdocs_standard_results.txt and .docx.")
        blank()
        b("Quick tips: Click the \u25bc button next to the search bar to reuse one of")
        b("your last 10 searches. While a search is running, the status line shows")
        b("how many terms are being searched. In the Results Preview, right-click")
        b("to copy text and double-click a filename to open it in your default app.")
        blank()
        b("After a search, click the green Matched Files button on the status")
        b("line to see every file that matched, with match counts and line numbers.")
        b("This is the fastest way to locate all matches in each file:")
        b("\u2022 Single-click a file, then click View Text (with line numbers) \u2014")
        b("  peekdocs displays the file's full extracted text with every match")
        b("  highlighted in yellow, so you can see exactly where they appear")
        b("\u2022 Double-click a file to open it in its default app (Word, Adobe, etc.)")
        b("\u2022 Right-click a file to bookmark it for quick access later")
        blank()
        blank()

        h("STANDARD SEARCH (GREEN BUTTON) vs REGEX SEARCH")
        b("The orange Regex Search button and the main search bar overlap")
        b("in capability. Here's the difference:")
        blank()
        b("Standard Search (blue button, main search bar \u2014 next to Step 2):")
        b("\u2022 Supports all 11 search modes: keywords, AND/OR, Boolean,")
        b("  regex, fuzzy, wildcard, whole-word, proximity, inverse, range")
        b("\u2022 Single regex via the Regex checkbox in Advanced Search Options")
        b("\u2022 Uses the index when available for faster results")
        blank()
        b("Regex Search popup:")
        b("\u2022 Edit up to 10 named regex patterns at a time; collections")
        b("  on disk are unbounded")
        b("\u2022 Run all enabled patterns one at a time with per-pattern results")
        b("\u2022 Run two or more saved collections together via Run Multiple")
        b("  Collections\u2026 (no row cap \u2014 patterns come straight off disk)")
        b("\u2022 Optional screen-only mode (no report files written)")
        b("\u2022 Always scans files directly (index is bypassed)")
        b("\u2022 Does not support AND, Boolean, fuzzy, wildcard, whole-word,")
        b("  proximity, inverse, or range queries")
        blank()
        b("Use Regex Search when you have a recurring set of regex patterns")
        b("you want to save and reuse. Use the main search bar for everything")
        b("else \u2014 including single regex searches with the Regex checkbox.")
        blank()

        h("REGEX SEARCH vs SEARCH SUITES")
        b("Regex Search and Search Suites are related but serve different")
        b("purposes:")
        blank()
        b("Regex Search popup:")
        b("\u2022 Up to 10 named regex patterns visible at a time (collections")
        b("  on disk are unbounded; Run Multiple Collections\u2026 runs more)")
        b("\u2022 Each pattern runs separately with per-pattern match counts")
        b("\u2022 Screen-only mode available (no reports written)")
        b("\u2022 Regex patterns only")
        b("\u2022 One folder per search")
        blank()
        b("Search Suites:")
        b("\u2022 Group any number of saved searches into a named suite")
        b("\u2022 Each search runs independently with its own settings")
        b("  (AND, regex, fuzzy, wildcard, etc.)")
        b("\u2022 Results organized by search in a combined report")
        b("\u2022 Per-folder collections")
        b("\u2022 No screen-only mode")
        blank()
        b("When to use each:")
        blank()
        e("  I want to...                          Use")
        e("  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
        e("  Search for a word or phrase            Standard Search (blue button)")
        e("  Use AND, Boolean, fuzzy, proximity     Standard Search (blue button)")
        e("  Search with one regex pattern           Standard Search (blue button)")
        e("  Run multiple regex patterns at once     Regex Search")
        e("  Save and reuse named regex patterns     Regex Search")
        e("  Hide results from report files          Regex Search")
        e("  Run different search modes together     Search Suites")
        e("  Repeat the same set of searches later   Search Suites")
        e("  Combine results into one report         Search Suites")
        blank()
        s("Why the different result surfaces?")
        b("Search Suites populate the main page's Results Preview pane,")
        b("Matched Files link, and count label. Regex Search shows its")
        b("results in a separate popup window. Three reasons:")
        blank()
        b("1. Engine reuse. A suite is a sequence of standard searches —")
        b("   every saved search in the suite goes through the same")
        b("   standard-search pipeline the green Run Standard Search")
        b("   button uses. That pipeline already wires its output to the")
        b("   main page, so the suite inherits the preview pane, the")
        b("   Matched Files link, and the count label for free. Regex")
        b("   Search calls the in-process API directly per pattern and")
        b("   never goes through the standard-search code path, so the")
        b("   main-page wiring would have to be re-plumbed by hand.")
        blank()
        b("2. Shape of the result. Regex Search wants to show per-")
        b("   pattern hit counts side by side (\"Pattern A: 17 hits in")
        b("   4 files\", \"Pattern B: 42 hits in 11 files\", …) with a")
        b("   View Files / View Text button on each row. That card-")
        b("   per-pattern layout doesn't fit the main page's single")
        b("   linear preview stream. A suite, by contrast, produces a")
        b("   single combined match list that maps naturally onto the")
        b("   preview pane.")
        blank()
        b("3. Screen-only mode. Regex Search has a 'Do not save regex")
        b("   match contents to reports' checkbox for sensitive scans.")
        b("   A popup that disappears on Close is the natural surface")
        b("   for that — putting sensitive matches into the persistent")
        b("   main-page preview defeats the privacy intent. Search")
        b("   Suites have no equivalent screen-only mode, so there's no")
        b("   privacy reason to keep their output off the main page.")
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
        b("settings. Tools \u2192 Clear Files and Tools \u2192 Indexes \u2192 Delete")
        b("only remove files that peekdocs created \u2014 never your documents.")
        b("All peekdocs files are safe to delete manually too \u2014")
        b("peekdocs recreates them as needed.")
        blank()
        s("Standard search reports (overwritten each Standard Search)")
        e("peekdocs_standard_results.txt       \u2014 text report")
        e("peekdocs_standard_results.docx      \u2014 Word report with highlights")
        e("peekdocs_standard_results.csv       \u2014 optional (-o csv)")
        e("peekdocs_standard_results.json      \u2014 optional (-o json)")
        blank()
        s("Regex search reports (overwritten each Regex Search)")
        e("peekdocs_regex_results.txt          \u2014 text report")
        e("peekdocs_regex_results.docx         \u2014 Word report with highlights")
        blank()
        s("Suite reports (overwritten each suite run)")
        e("peekdocs_suite_results.txt          \u2014 combined text report")
        e("peekdocs_suite_results.docx         \u2014 combined Word report")
        blank()
        s("Saved/archived reports")
        e("peekdocs_report_{name}.txt/docx         \u2014 saved with -s")
        e("peekdocs_accumulated_{name}.*          \u2014 appended with -sa")
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
        b("\u2022 All peekdocs_ report files are automatically excluded from searches")
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
        b("\u2022 Use Tools \u2192 Clear Files, Tools \u2192 Error Log, or Tools \u2192")
        b("  Indexes \u2192 Delete to manage files from the GUI")
        blank()
        s("Building a search index")
        b("1. Browse to the folder you want to index")
        b("2. Open Tools → Indexes")
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
        self._apply_dark_theme(help_win)



    def _show_advanced_help(self):
        """Show help for all Advanced Search Options with examples."""
        import tkinter as tk
        # Advanced is now inline, not a popup — parent the help window
        # to the main window directly.
        help_win, _dark = self._themed_toplevel(self)
        help_win.title("Advanced Search Options — Help")
        help_win.geometry("750x620")
        help_win.resizable(True, True)

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
                          foreground="#999999" if ctk.get_appearance_mode() == "Dark" else "gray40")

        txt.insert("end", "TABLE OF CONTENTS\n", "toc_title")
        for section in [
            "What Is This Panel?",
            "Search Mode Checkboxes", "Text Fields",
            "Combining Modes", "Settings Buttons", "Troubleshooting",
        ]:
            txt.insert("end", f"\u2022 {section}\n", "toc_item")
        txt.insert("end", "\n")

        h("WHAT IS THIS PANEL?")
        b("All searches are based on this panel and the Search Terms on the")
        b("main page. Your selections take effect immediately on the next")
        b("search — no need to press Save Defaults. That button saves")
        b("your current settings as permanent defaults for future sessions.")
        blank()
        b("Advanced Search Options is where you configure every search setting")
        b("that isn't on the main page \u2014 the additional search modes (AND, fuzzy,")
        b("wildcard, regex, OCR, expression, inverse), text filters (excluded")
        b("terms, file type list, range filters), output controls (CSV, JSON,")
        b("PDF, HTML, timestamped filenames, output directory), session")
        b("options (Delete on Close, Clear History on Close, Restrict File")
        b("Permissions), and the Notify on Search Complete desktop-notification")
        b("toggle. Every CLI flag")
        b("peekdocs supports has a matching control on this panel. Selections")
        b("take effect on the next search; use Save Defaults to make them")
        b("persistent. Hover any control for a brief tooltip.")
        blank()

        h("SEARCH MODE CHECKBOXES")
        blank()

        s("AND Mode")
        b("All search terms must appear in the same line. For PDF and Word")
        b("documents, a 'line' is typically a paragraph since each paragraph")
        b("is extracted as one line. For plain text files, a line is a literal line.")
        b("Tip: if your terms might span multiple lines (e.g., a multi-line function")
        b("call or SQL query), use Proximity (-p N) instead to find terms within N")
        b("words of each other, or use Lines Before/After (-B/-A) to capture")
        b("surrounding context.")
        b("Without AND mode, any single term matching is enough (OR mode).")
        e("budget revenue        \u2192  line must contain BOTH words")
        blank()

        s("Match counting in OR mode (why the numbers don't add up)")
        b("In OR mode each matching line is counted ONCE, even when more")
        b("than one of your terms appears on it. So OR totals can look")
        b("smaller than you'd expect by adding the per-term counts. Example:")
        e("bowling           \u2192 342 matches")
        e("tunick            \u2192  23 matches")
        e("bowling tunick    \u2192 350 matches  (in OR mode)")
        b("If OR added the counts you'd see 342 + 23 = 365. You actually")
        b("see 350, because 15 lines contain BOTH bowling AND tunick \u2014")
        b("inclusion-exclusion: |A \u222a B| = |A| + |B| \u2212 |A \u2229 B|.")
        b("To find those 15 overlap lines, run the same search with AND")
        b("mode on \u2014 it returns exactly the intersection.")
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
        e("\\d{3}-\\d{2}-\\d{4}     \u2192  9-digit ID with dashes (123-45-6789)")
        e("\\$[\\d,]+\\.\\d{2}       \u2192  dollar amounts ($1,234.56)")
        e("[A-Z]{2}-\\d{4,}       \u2192  ID codes (AB-12345)")
        e("\\d{2}/\\d{2}/\\d{4}     \u2192  dates (03/15/2026)")
        b("Tip: Tools → Search Wizard has pre-built regex patterns for")
        b("phone numbers, emails, dates, and other common formats.")
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

        s("Word Proximity")
        b("Find terms that appear within N words of each other on the same line.")
        b("Requires 2 or more search terms. AND mode is applied automatically.")
        e("Terms: breach contract    Word Proximity: 5")
        e("\u2192  both words must appear within 5 words of each other")
        blank()
        b("Line Proximity (-P) is available in the CLI only. It finds terms")
        b("within N lines of each other, even if they are on different lines.")
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
        b("Cap the number of matches written to report files. Default: 5000")
        b("(raised from 1000 in 1.2.7 to handle more real-world searches without")
        b("truncation). The total count is always accurate in the summary line —")
        b("only the report files are capped. The Matched Files list is also")
        b("affected: when capped, only files with matches within the cap appear.")
        b("Set to 0 for unlimited.")
        blank()
        b("Why a cap exists, and the tradeoff:")
        b("• DOCX is the bottleneck. python-docx is slow at inserting tens of")
        b("  thousands of highlighted runs — a 50,000-match DOCX takes several")
        b("  minutes and produces a very large file.")
        b("• TXT report size scales linearly with match count and can hit")
        b("  100+ MB on >100K matches.")
        b("• The default 5,000 covers most 'find every X' workflows. Common")
        b("  business-document searches hit a few hundred to a few thousand")
        b("  matches; tokens like TODO/FIXME in a typical repo come in")
        b("  under 5,000.")
        b("• Raise it or set 0 (unlimited) for genuinely huge result sets —")
        b("  typical use of 0 is jq-pipeline scenarios where the output is")
        b("  --stdout JSON or -o json, so the DOCX render cost doesn't apply.")
        b("• Pre-1.2.7, the default was 1,000. After real-world demo runs")
        b("  showed common searches getting truncated, we raised it to 5,000")
        b("  as a better balance between completeness and report-write speed.")
        b("  Unlimited as the default was considered and rejected: it")
        b("  surprises first-time users with minutes-long DOCX renders.")
        blank()

        s("Max File Size (MB)")
        b("Skip files larger than this size. Default: 100 MB. Very large files")
        b("(huge PDFs, massive spreadsheets) can cause slow searches or exhaust")
        b("memory. Skipped files are shown in the Excluded Files list after each")
        b("search. Set to 0 for no limit if you need to search large files.")
        b("Changing this value automatically rebuilds the index on the next")
        b("indexed search, so results stay consistent.")
        blank()
        b("Note: Raising Max File Size can sometimes result in fewer matched")
        b("files, not more. This happens when a very large file contains")
        b("thousands of matches that consume most of the Max Matches budget,")
        b("leaving fewer slots for matches from other files. If you see this,")
        b("try raising Max Matches too (or set it to 0 for unlimited).")
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
        b("Both use a peekdocs_ prefix so they are never re-searched.")
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
        b("Build the index first using Indexes in the Tools menu.")
        b("Note: The index always includes ALL subfolders. If you")
        b("check Use Index, your results will include files from")
        b("subfolders even if Recursive is unchecked. To search only")
        b("the top folder without subfolder results, uncheck both")
        b("Use Index and Recursive.")
        blank()

        h("COMBINING MODES")
        b("You can mix multiple options for more powerful searches.")
        blank()
        s("Regex + AND + Recursive")
        b("Find files with both a 9-digit ID pattern and a dollar amount in subfolders:")
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
        s("Whole Word + Word Proximity")
        b("'breach' and 'contract' as whole words within 5 words:")
        e("      Terms:  breach contract")
        e("Checkboxes:  Whole Word     Word Proximity: 5")
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
        b("Save all current options as permanent defaults to ~/.peekdocsrc.")
        b("This includes every setting on this Advanced Search Options")
        b("panel (AND/OR mode, recursive, whole word, regex, file types,")
        b("output formats, and the rest) plus the search terms and folder")
        b("from the main page. These become the defaults every time you")
        b("launch the app.")
        blank()
        b("Not required for the current search \u2014 your selections take")
        b("effect immediately on the next Search. Save As Defaults is")
        b("only for making your choices persist across sessions.")
        blank()
        b("This is different from Save Search on the main screen, which")
        b("saves the current search terms and settings by name so you")
        b("can reload them later. Save As Defaults sets your preferred")
        b("starting configuration. Save Search saves a specific named")
        b("search.")
        s("Restore Settings")
        b("Reload saved defaults from ~/.peekdocsrc into the GUI.")
        s("Reset All Fields")
        b("Clear all fields and reset to FACTORY defaults for the current")
        b("session — not the values you previously saved via Save")
        b("Defaults. To reload your saved defaults instead, use Restore")
        b("Settings (above). Reset All Fields does not modify ~/.peekdocsrc;")
        b("your saved preferences come back the next time you launch peekdocs.")
        b("Use this when you want a clean slate for one search without losing")
        b("your usual preferences. (Compare to Restore Factory Settings below,")
        b("which deletes ~/.peekdocsrc on disk.)")
        blank()

        s("Restore Factory Settings")
        b("Delete ~/.peekdocsrc entirely and return all settings to factory")
        b("defaults. The app will start fresh next time as if newly installed.")
        b("Your documents, search history, and personal files are not affected.")
        b("Use this when you want to wipe your saved preferences and start over.")
        b("(Compare to Reset All Fields above, which only clears the live GUI")
        b("for the current session and leaves ~/.peekdocsrc untouched.)")
        b("CLI equivalent: peekdocs --config --reset")
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
        b("\u2022 OCR unchecked \u2014 if the file-type count is lower than")
        b("  expected, image files (.jpg, .jpeg, .png, .tif, .tiff,")
        b("  .bmp) are skipped entirely when OCR is off, and image-only")
        b("  / scanned PDFs return zero text. Regular PDFs with a text")
        b("  layer are always searched regardless of this setting \u2014")
        b("  OCR is only needed for PDFs that are just pictures of")
        b("  pages (scans, faxes). Check OCR (and confirm Tesseract")
        b("  is installed) so those formats join the corpus. OCR is")
        b("  non-persisting by design \u2014 it resets to OFF each launch;")
        b("  click Save Defaults if you want it on by default.")
        blank()
        b("  First OCR run on a folder is dramatically slower than")
        b("  subsequent runs. Tesseract has to invoke once per image")
        b("  and once per scanned PDF page \u2014 a 300-scanned-PDF folder")
        b("  can take 20-30+ seconds the first time. peekdocs caches")
        b("  the OCR-extracted text in the search index after that, so")
        b("  the second and subsequent searches return at normal")
        b("  indexed-search speed (~sub-second). Deleting the index")
        b("  (.peekdocs.db) or moving the corpus to a fresh machine")
        b("  forces the OCR cost to be paid again next time.")
        blank()
        b("Click Reset All Fields (the red button at the bottom) to")
        b("clear everything and start fresh.")
        blank()
        b("If Use Index is checked inside Advanced Search Options, try")
        b("unchecking it and searching directly. A stale index may not contain")
        b("recently added or changed files. Use Auto-Refresh in Manage")
        b("Indexes to keep the index current automatically:")
        blank()
        b("\u2022 5\u201315 min \u2014 folders where files change frequently")
        b("\u2022 30 min\u20131 hour \u2014 folders that change occasionally")
        b("\u2022 4\u201324 hours \u2014 stable folders checked periodically")
        b("\u2022 Off \u2014 rebuild manually with Build Index(es) when needed")

        txt.configure(state="disabled")
        self._apply_dark_theme(help_win)



    def _show_save_load_help(self):
        """Show help for the \u25b6 Save and \u25b6 Reload buttons on the Step 2 row."""
        import tkinter as tk
        help_win, _dark = self._themed_toplevel()
        help_win.title("Save & Reload \u2014 Help")
        help_win.geometry("740x680")
        help_win.resizable(True, True)
        help_win.transient(self)

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
                          foreground="#999999" if ctk.get_appearance_mode() == "Dark" else "gray40")

        def h(s): txt.insert("end", s + "\n", "heading")
        def b(s): txt.insert("end", s + "\n", "body")
        def e(s): txt.insert("end", s + "\n", "example")
        def blank(): txt.insert("end", "\n")

        txt.insert("end", "TABLE OF CONTENTS\n", "toc_title")
        for section in [
            "What Save Does",
            "What Reload Does",
            "Where Saved Searches Are Stored",
            "Editing a Saved Search",
            "Deleting a Saved Search",
            "Sharing Saved Searches",
            "Tips",
        ]:
            txt.insert("end", f"\u2022 {section}\n", "toc_item")
        txt.insert("end", "\n")

        h("WHAT SAVE DOES")
        b("\u25b6 Save (the button between \u25bc Recent and \u25b6 Reload on the search")
        b("bar row) takes everything you currently have configured \u2014 search")
        b("terms and folder on the main page, plus every option inside")
        b("Advanced Search Options (mode AND/OR/Boolean/regex/fuzzy/wildcard/")
        b("whole word, inverse, file type filters, exclude terms, proximity,")
        b("range filters, context lines, recursive, OCR, max file size, and")
        b("Use Index) \u2014 and stores it under a name you choose.")
        blank()
        b("Once saved, you can reload the exact same configuration")
        b("later with one click from \u25b6 Reload. Nothing is \"locked")
        b("in\" \u2014 you can always edit and re-save it.")
        blank()
        b("Saving does NOT run the search. If you want to verify that")
        b("the search works the way you expect, click Run Standard Search")
        b("first, check the results, then click ▶ Save.")
        blank()

        h("WHAT RELOAD DOES")
        b("\u25b6 Reload (the button next to \u25bc Recent and \u25b6 Save on the search")
        b("bar row) opens a popup listing every saved search in the")
        b("current folder's collection. Click one to load it back into")
        b("the main page \u2014 the search terms, folder, and every Advanced")
        b("Search Options field are restored exactly as they were when")
        b("you saved.")
        blank()
        b("After loading, you can:")
        b("\u2022 Click Run Standard Search to execute it as-is")
        b("\u2022 Modify any field and click Run Standard Search to try a variation")
        b("\u2022 Click \u25b6 Save to overwrite the saved version (use the same")
        b("  name) or save it as a new one (use a new name)")
        b("\u2022 Delete the saved search from the Reload popup")
        blank()
        b("Saving does NOT run the search. To verify a search works")
        b("the way you expect, click Run Standard Search first, check the")
        b("results, then click \u25b6 Save.")
        blank()

        h("WHERE SAVED SEARCHES ARE STORED")
        b("Saved searches live in a file called .peekdocs_collection.json")
        b("inside the search folder itself. Each folder has its own")
        b("collection \u2014 the saved searches for ~/Documents/Contracts are")
        b("separate from those in ~/Documents/HR_Files. When you switch")
        b("folders on the main page, the Reload popup")
        b("automatically shows that folder's collection.")
        blank()
        h("WHY PER FOLDER?")
        b("Most people organize documents by topic \u2014 tax returns in one")
        b("folder, insurance in another, work projects in a third.")
        b("The searches you need for tax documents (W-2, 1099, deduction)")
        b("are completely different from the searches you need for an")
        b("insurance folder (policy number, claim, agent). Keeping them")
        b("separate means you only see what's relevant to the folder")
        b("you're working in \u2014 no clutter from unrelated searches.")
        blank()
        b("It also means your searches travel with your documents. Copy")
        b("a folder to a USB drive, another computer, or a backup \u2014 the")
        b("saved searches and suites come with it automatically. Nothing")
        b("to export, nothing to reconfigure.")
        blank()
        b("If you need to find a search you saved in a different folder,")
        b("use All Collections in the Tools menu \u2014 it shows every saved")
        b("search across all your folders in one view.")
        blank()
        b("Tip: If your files aren't organized into separate folders \u2014")
        b("everything is in one big Documents folder \u2014 that's fine too.")
        b("All your saved searches and suites will be in one collection.")
        b("Or point peekdocs at a parent folder with Recursive checked")
        b("to search everything underneath it at once.")
        blank()

        h("EDITING A SAVED SEARCH")
        b("1. Click \u25b6 Reload and pick the one you want to edit")
        b("2. The search bar and Advanced Search Options are filled in")
        b("   with the saved values")
        b("3. Change whatever you need to (terms, filters, options)")
        b("4. Click Run Standard Search to verify the new version works")
        b("5. Click \u25b6 Save and give it the SAME name \u2014 you'll")
        b("   be asked to confirm overwriting the existing entry")
        blank()
        b("If you give it a new name instead, you'll end up with two")
        b("saved searches: the original and your modified version.")
        blank()

        h("DELETING A SAVED SEARCH")
        b("Open \u25b6 Reload. Each entry in the popup has a Delete")
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
        self._apply_dark_theme(help_win)



    def _show_matched_files_help(self, parent):
        """Show help for the Matched Files popup."""
        import tkinter as tk
        help_win, _dark = self._themed_toplevel(parent)
        help_win.title("Matched Files \u2014 Help")
        help_win.geometry("720x640")
        help_win.resizable(True, True)
        help_win.transient(parent)

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
                          foreground="#999999" if ctk.get_appearance_mode() == "Dark" else "gray40")

        def h(s): txt.insert("end", s + "\n", "heading")
        def b(s): txt.insert("end", s + "\n", "body")
        def e(s): txt.insert("end", s + "\n", "example")
        def blank(): txt.insert("end", "\n")

        txt.insert("end", "TABLE OF CONTENTS\n", "toc_title")
        for section in [
            "What This Popup Shows",
            "How to Use It",
            "Bookmarks",
            "View Text vs Open File",
            "Heatmap",
            "Line Numbers",
            "Why Some Files May Be Missing",
        ]:
            txt.insert("end", f"\u2022 {section}\n", "toc_item")
        txt.insert("end", "\n")

        h("WHAT THIS POPUP SHOWS")
        b("You opened this popup by clicking the green Matched Files")
        b("button in the right pane, just below the results headline.")
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
        b("\u2022 Right-click a row to add it to your Bookmarks")
        b("\u2022 Click Close when you're done")
        blank()

        h("BOOKMARKS")
        b("Right-click any file in this list and choose 'Add Bookmark'")
        b("to pin it for quick access later. Bookmarked files can be")
        b("opened any time from Tools \u2192 Bookmarks without re-running")
        b("a search. This is useful for files you refer to often \u2014")
        b("contracts, reference documents, or important results you")
        b("don't want to lose track of.")
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

        h("HEATMAP")
        b("Select a row and click the Heatmap button to open a")
        b("matplotlib chart showing where the matches sit INSIDE that")
        b("file, plotted by line number. The x-axis is line number")
        b("(1 → end of file); the y-axis is how many matches fall in")
        b("each bin. Tall bars at the LEFT mean the matches cluster")
        b("near the start of the document; tall bars at the RIGHT")
        b("mean they cluster near the end; an even spread means the")
        b("term recurs throughout. A faint blue tick is drawn for")
        b("every individual match line so single hits are still")
        b("visible even when no histogram bin is tall.")
        blank()
        b("Why it's useful: it lets you triage WHICH matching file to")
        b("open first. A 200-page report where every match clusters in")
        b("Chapter 3 is a different read than one where matches are")
        b("scattered across every chapter.")
        blank()
        b("Heatmap needs per-match line numbers, which the search")
        b("captures by default. If you see \"No line-number data\",")
        b("re-run the search — some legacy search paths didn't")
        b("populate them.")
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
        self._apply_dark_theme(help_win)



    def _show_excluded_files_help(self, parent):
        """Show help for the Excluded Files popup."""
        import tkinter as tk
        help_win, _dark = self._themed_toplevel(parent)
        help_win.title("Excluded Files \u2014 Help")
        help_win.geometry("720x680")
        help_win.resizable(True, True)
        help_win.transient(parent)

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
                          foreground="#999999" if ctk.get_appearance_mode() == "Dark" else "gray40")

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
        b("button in the right pane, just below the results headline.")
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
        b("  such as peekdocs_report_*.docx reports, index databases,")
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
        e("      peekdocs_report_results.docx")
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
        self._apply_dark_theme(help_win)



    def _show_index_help(self):
        """Show help explaining what indexes are and when to use them."""
        import tkinter as tk
        help_win, _dark = self._themed_toplevel(self.index_window or self)
        help_win.title("Indexes — Help")
        help_win.geometry("650x560")
        help_win.resizable(True, True)
        if self.index_window:
            help_win.transient(self.index_window)

        # Close button anchored to bottom row
        ctk.CTkButton(
            help_win, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=help_win.destroy,
            font=ctk.CTkFont(size=12),
        ).pack(side="bottom", pady=(5, 10))

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
                          foreground="#999999" if ctk.get_appearance_mode() == "Dark" else "gray40")

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
            "What Is an Index?",
            "Quick Start",
            "Buttons on This Panel",
            "Use Index Checkbox (Main Screen)",
            "Do I Need an Index?",
            "Good to Know",
        ]:
            txt.insert("end", f"\u2022 {section}\n", "toc_item")
        txt.insert("end", "\n")

        h("WHAT IS AN INDEX?")
        b("An index is a pre-built database of every word in every file in")
        b("the search folder. Instead of re-reading each file on every search,")
        b("peekdocs looks up matches in the index \u2014 much faster, especially")
        b("for large folders. The index is optional: leave Use Index unchecked")
        b("to search files directly each time. The index lives in a hidden")
        b("file called .peekdocs.db inside the search folder; you can delete")
        b("it any time without losing your documents.")
        blank()

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
        b("inside Advanced Search Options is automatically unchecked")
        b("and grayed out.")
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
        b("\u2022 One index covers the folder and ALL subfolders \u2014 there")
        b("  is no way to build an index for just the top folder.")
        b("  This means if you check Use Index, your search results")
        b("  will include files from subfolders even if Recursive is")
        b("  unchecked. To search only the top folder without subfolder")
        b("  results, uncheck Use Index and uncheck Recursive.")
        b("\u2022 Safe to delete \u2014 rebuild with Build Index(es) anytime")
        b("\u2022 If Use Index is checked but no index exists, peekdocs")
        b("  falls back to direct scanning automatically")
        b("\u2022 Changing Max File Size (in Advanced Search Options) triggers")
        b("  an automatic rebuild on the next indexed search")
        b("\u2022 Search Suites honor each saved search's Use Index setting")
        b("  (saved at the time the search was saved), so one suite run")
        b("  can mix indexed and direct-scan sections")
        b("\u2022 Regex Search collections never use the index \u2014 every")
        b("  pattern is evaluated directly against the extracted text")

        txt.configure(state="disabled")
        self._apply_dark_theme(help_win)

    # ── Search Suites ──────────────────────────────────────────────

    def _show_search_modes_compare(self):
        """Show a short side-by-side comparison of the three search modes."""
        import tkinter as tk
        win, _dark = self._themed_toplevel()
        win.title("Search Modes — What’s the Difference?")
        win.geometry("820x560")
        win.resizable(True, True)
        win.transient(self)

        # Bottom Close button — matches the muted "transparent / gray text"
        # style every other help popup in peekdocs uses (Advanced, Indexes,
        # Recent Changes help, etc.). Packed FIRST with side="bottom" so it
        # reserves its space before the scrollable Text takes the rest.
        ctk.CTkButton(
            win, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            font=ctk.CTkFont(size=12),
            command=win.destroy,
        ).pack(side="bottom", pady=(5, 10))

        txt = tk.Text(win, wrap="word", font=("TkDefaultFont", 12),
                      padx=18, pady=12, borderwidth=0, highlightthickness=0)
        scroll = tk.Scrollbar(win, command=txt.yview)
        txt.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True)

        txt.tag_configure("title", font=("TkDefaultFont", 15, "bold"),
                          spacing1=4, spacing3=8)
        txt.tag_configure("std", font=("TkDefaultFont", 13, "bold"),
                          foreground="#1976D2", spacing1=10, spacing3=4)
        txt.tag_configure("suite", font=("TkDefaultFont", 13, "bold"),
                          foreground="#5E9516", spacing1=10, spacing3=4)
        txt.tag_configure("regex", font=("TkDefaultFont", 13, "bold"),
                          foreground="#F57C00", spacing1=10, spacing3=4)
        txt.tag_configure("body", font=("TkDefaultFont", 12),
                          lmargin1=18, lmargin2=18, spacing1=2, spacing3=4)
        txt.tag_configure("foot", font=("TkDefaultFont", 11, "italic"),
                          foreground="#666666", spacing1=14)

        txt.insert("end", "Three ways to search\n", "title")
        txt.insert("end",
                   "peekdocs has three Search buttons on the main page. "
                   "They share the same folder (Step 1) and same file types but "
                   "differ in what they do and what report they produce.\n",
                   "body")

        txt.insert("end", "Run Standard Search (blue)\n", "std")
        txt.insert("end",
                   "Type one or more terms in the search bar and click Run. "
                   "Supports AND/OR, whole-word, fuzzy, wildcard, and regex "
                   "(one or more patterns). Produces one report with every match.\n"
                   "Click the Advanced link above the search-buttons row to open "
                   "Advanced Search Options — file types, exclude terms, "
                   "range filters, proximity, context lines, OCR, and more "
                   "all live there and apply to the standard search.\n"
                   "Best for: most everyday searches.\n", "body")

        txt.insert("end", "Search Suites (green)\n", "suite")
        txt.insert("end",
                   "Group several saved searches into a named suite, then run "
                   "them all with one click. Produces one combined report with "
                   "a separate section per saved search.\n"
                   "Best for: recurring multi-topic reviews where you want all "
                   "the results in a single document.\n", "body")

        txt.insert("end", "Regex Search (orange)\n", "regex")
        txt.insert("end",
                   "Open the Regex workflow to build or run a named collection "
                   "of regex patterns (up to 10 visible in the popup at a time; "
                   "collections on disk are unbounded). Each pattern runs separately, "
                   "with per-pattern results.\n"
                   "Best for: pattern-based work — structured strings, IDs, "
                   "URLs, code tokens — where regular search terms aren’t "
                   "expressive enough.\n", "body")

        txt.insert("end",
                   "Both Search Suites and Regex Search collections can be run "
                   "automatically on a schedule — open Tools → Schedule Search "
                   "to generate a ready-to-paste cron (Mac / Linux) or Task "
                   "Scheduler (Windows) command for your OS.\n", "body")

        txt.insert("end",
                   "Tip: not sure which to use? Start with Run Standard Search. "
                   "Move up to Suites when you find yourself running the same "
                   "two or three searches together, or Regex when you need "
                   "pattern matching.",
                   "foot")
        txt.configure(state="disabled")

    def _run_system_check(self):
        """Show the GUI equivalent of CLI `peekdocs --check` — installation health probe."""
        import tkinter as tk
        from peekdocs.cli import run_system_check

        try:
            info = run_system_check()
        except Exception as e:
            self._show_error(f"System check failed: {e}")
            return

        popup, _dark = self._themed_toplevel()


        popup.withdraw()  # hidden during widget setup; centered + shown at end
        popup.title("System Check")
        popup.resizable(True, True)
        self._center_popup_on_main(popup, 740, 600)

        # Header — overall status
        if info["all_ok"]:
            header_text = "✓  Everything looks healthy."
            header_color = "#2E7D32"
        else:
            header_text = "⚠  Issues found — see below."
            header_color = "#C62828"
        tk.Label(
            popup, text=header_text, font=self._scaled_font(14, "bold"),
            fg=header_color, bg=("white" if not _dark else "#2B2B2B"),
        ).pack(anchor="w", padx=12, pady=(12, 4))

        # Scrollable text widget with color tags
        text_frame = tk.Frame(popup, bg=("white" if not _dark else "#2B2B2B"))
        text_frame.pack(fill="both", expand=True, padx=12, pady=(4, 8))
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        text = tk.Text(
            text_frame, wrap="word", yscrollcommand=scrollbar.set,
            font=("Courier", 11),
            bg=("#F9F9F9" if not _dark else "#1E1E1E"),
            fg=("#222" if not _dark else "#DDD"),
            relief="flat", borderwidth=1,
        )
        text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text.yview)

        # Color tags
        text.tag_configure("ok", foreground=("#2E7D32" if not _dark else "#81C784"))
        text.tag_configure("bad", foreground=("#C62828" if not _dark else "#EF5350"))
        text.tag_configure("warn", foreground=("#E65100" if not _dark else "#FFB74D"))
        text.tag_configure("section", font=("Courier", 11, "bold"))
        text.tag_configure("dim", foreground=("#777" if not _dark else "#999"))

        # Build the report — also accumulate plain-text version for Copy to Clipboard
        plain_lines = []
        def add(line, tag=None):
            text.insert("end", line + "\n", tag if tag else ())
            plain_lines.append(line)

        add(f"peekdocs {info['peekdocs_version']}")
        add(f"Python {info['python_version_full']}")
        add(f"OS: {info['os_system']} {info['os_release']}")
        add("")

        v = info["python_version_tuple"]
        py_min = info["tested_python_min"]
        py_max = info["tested_python_max"]
        if info["python_status"] == "below_min":
            add(f"Python version:  {v[0]}.{v[1]} (BELOW minimum {py_min[0]}.{py_min[1]}) — upgrade Python to {py_min[0]}.{py_min[1]} or later", "bad")
        elif info["python_status"] == "above_max":
            add(f"Python version:  {v[0]}.{v[1]} (above maximum tested {py_max[0]}.{py_max[1]}) — should work, but not yet verified", "warn")
        else:
            add(f"Python version:  {v[0]}.{v[1]} (ok)", "ok")
        add("")

        add("Required dependencies:", "section")
        for desc, pkg, status, ver in info["required_deps"]:
            if status == "ok":
                add(f"  {desc} ({pkg}): ok ({ver})", "ok")
            else:
                add(f"  {desc} ({pkg}): MISSING — install with: pip install {pkg}", "bad")
        add("")

        add("Optional dependencies:", "section")
        for desc, pkg, status, ver in info["optional_deps"]:
            if status == "ok":
                add(f"  {desc} ({pkg}): ok ({ver})", "ok")
            else:
                add(f"  {desc} ({pkg}): not installed — install with: pip install {pkg}", "dim")
        add("")

        if info["tesseract_installed"]:
            add("Tesseract OCR:   installed (OCR available with -O flag)", "ok")
        else:
            add("Tesseract OCR:   not installed (optional — needed only for OCR)", "dim")

        add(f"SQLite version:  {info['sqlite_version']}")
        add("")

        if info["disk_low"]:
            add(f"Disk space:      {info['disk_free_human']} free — LOW; reports may fail to write", "bad")
        else:
            add(f"Disk space:      {info['disk_free_human']} free", "ok")
        add("")

        if not info["all_ok"]:
            add("Fix missing dependencies with: pipx upgrade peekdocs  (or see https://github.com/exbuf/peekdocs#installation)", "warn")

        text.config(state="disabled")

        # Copy to Clipboard — packed directly on popup, left-anchored.
        # (Previous intermediate tk.Frame had an explicit white background
        # that rendered as a visible full-width bar in light mode.)
        def _copy_to_clipboard():
            popup.clipboard_clear()
            popup.clipboard_append("\n".join(plain_lines))
            popup.update()
            copy_btn.configure(text="Copied!")
            popup.after(1500, lambda: copy_btn.configure(text="Copy to Clipboard"))

        copy_btn = ctk.CTkButton(
            popup, text="Copy to Clipboard", width=160,
            font=ctk.CTkFont(size=12),
            command=_copy_to_clipboard,
        )
        copy_btn.pack(anchor="w", padx=12, pady=(4, 0))

        # Close — centered, on its own row below Copy to Clipboard.
        close_row = tk.Frame(popup, bg=("white" if not _dark else "#2B2B2B"))
        close_row.pack(pady=(5, 12))
        ctk.CTkButton(
            close_row, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            font=ctk.CTkFont(size=12),
            command=popup.destroy,
        ).pack()

        self._apply_dark_theme(popup)


    # ── Schedule Search ───────────────────────────────────────────────

    def _open_diff_snapshots(self):
        """Open the Diff Snapshots dialog — compares two peekdocs JSON snapshots."""
        import tkinter as tk

        win, _dark = self._themed_toplevel()
        win.withdraw()  # hidden during widget setup; centered + shown at end
        win.title("Diff Snapshots")
        win.resizable(True, True)
        # NOTE: deliberately NOT calling win.transient(self) or binding
        # <FocusIn> -> win.lift() — both cause the popup to disappear when
        # dragged across monitors on macOS. See Regex Search popup for fix.

        # ── Header ──
        header = tk.Frame(win)
        header.pack(fill="x", padx=15, pady=(10, 0))
        tk.Label(
            header, text="Diff Snapshots",
            font=("TkDefaultFont", 14, "bold"),
        ).pack(side="left")
        ctk.CTkButton(
            header, text="?", width=30, height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#1565C0", text_color="white",
            hover_color="#0D47A1",
            corner_radius=15,
            command=lambda: self._show_diff_snapshots_help(win),
        ).pack(side="right")

        tk.Label(
            win,
            text="Compare two peekdocs JSON snapshots and see what changed: NEW files now "
                 "matching, REMOVED files no longer matching, CHANGED match counts, and "
                 "MODIFIED file content (when both snapshots were captured with --hash). "
                 "Produce a snapshot first with:  peekdocs <terms> --stdout > peekdocs_snapshot.json. "
                 "Name your snapshots peekdocs_snapshot_<label>.json for consistency with other peekdocs output files.",
            font=("TkDefaultFont", 10), fg="gray", wraplength=780, justify="left",
        ).pack(fill="x", padx=15, pady=(2, 10))

        # ── Snapshot picker rows ──
        old_var = tk.StringVar(value="")
        new_var = tk.StringVar(value="")

        def _picker_row(parent, label_text, var, tooltip):
            row = tk.Frame(parent)
            row.pack(fill="x", padx=15, pady=(0, 6))
            tk.Label(row, text=label_text, font=("TkDefaultFont", 11, "bold"),
                     width=12, anchor="w").pack(side="left")
            entry = tk.Entry(row, textvariable=var, font=("TkDefaultFont", 11))
            entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

            def _browse():
                p = filedialog.askopenfilename(
                    parent=win,
                    title=f"Pick {label_text.rstrip(':')} snapshot",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                )
                if p:
                    var.set(p)

            btn = ctk.CTkButton(
                row, text="Browse", width=80,
                font=ctk.CTkFont(size=11), command=_browse,
            )
            btn.pack(side="left")
            Tooltip(btn, tooltip)
            return entry

        _picker_row(win, "Old snapshot:", old_var,
                    "Earlier snapshot — the baseline you are comparing against")
        _picker_row(win, "New snapshot:", new_var,
                    "Later snapshot — the one being checked for changes")

        # ── Action row ──
        action_row = tk.Frame(win)
        action_row.pack(fill="x", padx=15, pady=(6, 6))

        status_var = tk.StringVar(value="")
        status_label = tk.Label(
            action_row, textvariable=status_var,
            font=("TkDefaultFont", 11), fg="gray",
        )

        # Results text widget — created here so _compare() can clear/populate it.
        results_frame = tk.Frame(win)
        results_frame.pack(fill="both", expand=True, padx=15, pady=(4, 10))
        scroll = tk.Scrollbar(results_frame)
        scroll.pack(side="right", fill="y")
        results = tk.Text(
            results_frame, wrap="word",
            font=("Courier", 11), padx=10, pady=8,
            yscrollcommand=scroll.set,
            borderwidth=1, relief="solid", highlightthickness=0,
        )
        results.pack(side="left", fill="both", expand=True)
        scroll.config(command=results.yview)

        if ctk.get_appearance_mode() == "Dark":
            results.configure(bg="#1e1e1e", fg="#e0e0e0",
                              insertbackground="#e0e0e0")

        results.tag_configure("hdr", font=("Courier", 11, "bold"))
        results.tag_configure("new", foreground="#2E7D32",
                              font=("Courier", 11, "bold"))
        results.tag_configure("removed", foreground="#C62828",
                              font=("Courier", 11, "bold"))
        results.tag_configure("changed", foreground="#EF6C00",
                              font=("Courier", 11, "bold"))
        results.tag_configure("modified", foreground="#6A1B9A",
                              font=("Courier", 11, "bold"))
        results.tag_configure("muted", foreground="#777777")

        def _compare():
            from peekdocs.diff import (
                load_json, compute_diff, format_human, is_actionable,
            )
            old_path = old_var.get().strip()
            new_path = new_var.get().strip()
            if not old_path or not new_path:
                messagebox.showerror(
                    "Diff Snapshots",
                    "Please pick both an old and a new snapshot file.",
                    parent=win,
                )
                return

            old_data, err = load_json(old_path)
            if err:
                messagebox.showerror(
                    "Diff Snapshots",
                    f"Could not read old snapshot:\n{err}\n\n"
                    "Snapshots are JSON files produced by\n"
                    "  peekdocs <terms> --stdout > peekdocs_snapshot.json",
                    parent=win,
                )
                return
            new_data, err = load_json(new_path)
            if err:
                messagebox.showerror(
                    "Diff Snapshots",
                    f"Could not read new snapshot:\n{err}\n\n"
                    "Snapshots are JSON files produced by\n"
                    "  peekdocs <terms> --stdout > peekdocs_snapshot.json",
                    parent=win,
                )
                return

            diff = compute_diff(old_data, new_data)
            text = format_human(diff, old_path, new_path)

            results.configure(state="normal")
            results.delete("1.0", "end")
            # Render with per-section coloring so the eye can scan the deltas.
            for line in text.splitlines(True):
                lstrip = line.lstrip()
                if lstrip.startswith("NEW:"):
                    tag = "new"
                elif lstrip.startswith("REMOVED:"):
                    tag = "removed"
                elif lstrip.startswith("CHANGED:"):
                    tag = "changed"
                elif lstrip.startswith("MODIFIED:"):
                    tag = "modified"
                elif lstrip.startswith("+ "):
                    tag = "new"
                elif lstrip.startswith("- "):
                    tag = "removed"
                elif lstrip.startswith("~ "):
                    tag = "changed"
                elif lstrip.startswith("UNCHANGED:") or lstrip.startswith("Net "):
                    tag = "muted"
                elif lstrip.startswith("Diff:") or lstrip.startswith("Old:") or lstrip.startswith("New:"):
                    tag = "hdr"
                else:
                    tag = None
                if tag:
                    results.insert("end", line, tag)
                else:
                    results.insert("end", line)
            results.configure(state="disabled")

            actionable = is_actionable(diff)
            n_new = len(diff.get("new", []))
            n_chg = len(diff.get("changed", []))
            n_mod = len(diff.get("modified", []))
            n_rem = len(diff.get("removed", []))
            if actionable:
                status_var.set(
                    f"Actionable changes: {n_new} new, {n_chg} changed, "
                    f"{n_mod} modified  (removed: {n_rem})"
                )
                status_label.configure(fg="#C62828")
            else:
                status_var.set(
                    f"No actionable changes  (removed: {n_rem})"
                )
                status_label.configure(fg="#2E7D32")

        compare_btn = ctk.CTkButton(
            action_row, text="Compare", width=120, height=34,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2196F3", hover_color="#1976D2",
            text_color="white",
            command=_compare,
        )
        compare_btn.pack(side="left")
        Tooltip(compare_btn, "Run the diff and show what changed between the two snapshots")

        status_label.pack(side="left", padx=(12, 0))

        # Bottom Close button — matches the standard muted style used by
        # every other peekdocs help / info popup.
        ctk.CTkButton(
            win, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            font=ctk.CTkFont(size=12),
            command=win.destroy,
        ).pack(side="bottom", pady=(5, 10))

        self._center_popup_on_main(win, 820, 680)

    def _show_diff_snapshots_help(self, parent):
        """Help popup for Diff Snapshots."""
        import tkinter as tk
        help_win, _dark = self._themed_toplevel(parent)
        help_win.title("Diff Snapshots — Help")
        help_win.geometry("680x600")
        help_win.resizable(True, True)
        help_win.transient(parent)

        txt = tk.Text(help_win, wrap="word", font=("TkDefaultFont", 12),
                      padx=18, pady=12, borderwidth=0, highlightthickness=0)
        scroll = tk.Scrollbar(help_win, command=txt.yview)
        txt.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True)

        txt.tag_configure("h", font=("TkDefaultFont", 14, "bold"),
                          spacing1=10, spacing3=4)
        txt.tag_configure("b", font=("TkDefaultFont", 12), spacing1=2)
        txt.tag_configure("code", font=("Courier", 11),
                          lmargin1=24, lmargin2=24, spacing1=2)

        def h(t): txt.insert("end", t + "\n", "h")
        def b(t): txt.insert("end", t + "\n", "b")
        def c(t): txt.insert("end", t + "\n", "code")
        def blank(): txt.insert("end", "\n")

        h("What does Diff Snapshots do?")
        b("It compares two peekdocs JSON snapshots and shows what changed: ")
        b("new files matching, files that gained or lost matches, and (when")
        b("both snapshots were captured with --hash) files whose content")
        b("changed under a steady match count.")
        b("Typical use: scheduled scans where the question is not “what")
        b("matches?” but “what is new since last week?”")
        blank()

        h("What is a snapshot?")
        b("A snapshot is a JSON file produced by peekdocs --stdout (or by")
        b("running a search with -o json). It captures the matched files and,")
        b("with --hash, a sha256 of each file. Example:")
        c("peekdocs <terms> -r --hash --stdout > peekdocs_snapshot_2026-05-25.json")
        blank()
        b("Capture two snapshots at different points in time, then compare")
        b("them here.")
        blank()

        h("Reading the result")
        b("• NEW       — files matching now that were not matching before")
        b("• REMOVED   — files that were matching but no longer match")
        b("• CHANGED   — same file, different match count")
        b("• MODIFIED  — same path and same match count, but the file content")
        b("              changed (sha256 differs). Requires --hash on both")
        b("              snapshots; otherwise this section is silently empty.")
        b("• UNCHANGED — summarized as a count only")
        blank()

        h("Same feature on the CLI")
        b("Diff Snapshots is the GUI front for the peekdocs --diff command.")
        b("From a terminal:")
        c("peekdocs --diff peekdocs_snapshot_old.json peekdocs_snapshot_new.json")
        c("peekdocs --diff peekdocs_snapshot_old.json peekdocs_snapshot_new.json --json")
        blank()
        b("The CLI is the right surface for cron and CI pipelines because it")
        b("returns diff-flavored exit codes (0 = no change, 1 = new findings,")
        b("2 = error) — see the User Guide → Automation and IT Use for the")
        b("full pattern.")
        blank()

        h("What it does not do")
        b("Diff Snapshots compares scan results, not source documents.")
        b("To compare two Word or LibreOffice documents directly, use the")
        b("application's built-in Compare Document feature.")

        txt.configure(state="disabled")

    def _open_schedule_search(self):
        """Open the Schedule Search dialog — generates cron or schtasks commands."""
        import tkinter as tk

        win, _dark = self._themed_toplevel()
        win.withdraw()  # hidden during widget setup; centered + shown at end
        win.title("Schedule Search")
        win.resizable(True, True)
        # NOTE: deliberately NOT calling win.transient(self) or binding
        # <FocusIn> -> win.lift() — both cause the popup to disappear when
        # dragged across monitors on macOS. See Regex Search popup for fix.

        # No outer scrollable wrapper — earlier attempts (CTkScrollableFrame
        # and a manual Canvas+Scrollbar) both produced layouts that hid
        # widgets or scrolled only the first inch. Packing widgets directly
        # to `win` is simpler and works on every platform; long content
        # (the instructions Text widget) gets its own scrollbar below.
        # `body` is just an alias for `win` so the earlier sweep's
        # `body`-parented widgets keep working without further edits.
        body = win

        # Close button packed FIRST with side="bottom" so it's always
        # anchored at the bottom of the popup regardless of content height.
        ctk.CTkButton(
            win, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=win.destroy, font=ctk.CTkFont(size=12),
        ).pack(side="bottom", pady=(0, 10))

        # ── Title & subtitle ──
        tk.Label(
            body, text="Schedule Search",
            font=("TkDefaultFont", 13, "bold"),
        ).pack(anchor="w", padx=15, pady=(10, 0))
        tk.Label(
            body,
            text="Generate a command to run a peekdocs search automatically on a schedule. "
                 "This dialog creates the command for you \u2014 you paste it into your "
                 "system's scheduler. Step-by-step instructions are shown below.",
            font=("TkDefaultFont", 10), fg="gray", wraplength=640, justify="left",
        ).pack(fill="x", padx=15, pady=(2, 8))

        # ── What to run ──
        tk.Label(
            body, text="What to run:",
            font=("TkDefaultFont", 11, "bold"),
        ).pack(anchor="w", padx=15, pady=(4, 2))

        search_type_var = tk.StringVar(value="regex_collection")
        choice_frame = tk.Frame(body)
        choice_frame.pack(fill="x", padx=15, pady=(0, 4))
        tk.Radiobutton(
            choice_frame, text="Search Suite", variable=search_type_var,
            value="suite", font=("TkDefaultFont", 11),
            command=lambda: _refresh_names(),
        ).pack(side="left", padx=(0, 15))
        tk.Radiobutton(
            choice_frame, text="Regex Collection", variable=search_type_var,
            value="regex_collection", font=("TkDefaultFont", 11),
            command=lambda: _refresh_names(),
        ).pack(side="left")

        name_var = tk.StringVar(value="")
        name_dropdown = ctk.CTkOptionMenu(
            body, variable=name_var, values=["(none found)"],
            width=400, font=ctk.CTkFont(size=11),
            command=lambda _: _regenerate(),
        )
        name_dropdown.pack(anchor="w", padx=15, pady=(0, 6))

        # ── Folder ──
        tk.Label(
            body, text="Search folder:",
            font=("TkDefaultFont", 11, "bold"),
        ).pack(anchor="w", padx=15, pady=(4, 2))
        folder_frame = tk.Frame(body)
        folder_frame.pack(fill="x", padx=15, pady=(0, 2))
        folder_var = tk.StringVar(value=self.folder_entry.get().strip() or os.path.expanduser("~"))
        folder_entry = tk.Entry(folder_frame, textvariable=folder_var, font=("TkDefaultFont", 11))
        folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        def _browse_folder():
            d = filedialog.askdirectory(parent=win, initialdir=folder_var.get())
            if d:
                folder_var.set(d)
                _refresh_names()
                _regenerate()

        ctk.CTkButton(
            folder_frame, text="Browse", width=70,
            font=ctk.CTkFont(size=11), command=_browse_folder,
        ).pack(side="left")

        recursive_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            win, text="Recursive (-r) \u2014 include subfolders",
            variable=recursive_var, font=("TkDefaultFont", 11),
            command=lambda: _regenerate(),
        ).pack(anchor="w", padx=15, pady=(0, 6))

        # ── Schedule ──
        tk.Label(
            win, text="How often:",
            font=("TkDefaultFont", 11, "bold"),
        ).pack(anchor="w", padx=15, pady=(4, 2))

        sched_frame = tk.Frame(body)
        sched_frame.pack(fill="x", padx=15, pady=(0, 2))

        freq_var = tk.StringVar(value="Weekly")
        freq_menu = ctk.CTkOptionMenu(
            sched_frame, variable=freq_var,
            values=["Daily", "Weekly", "Monthly"],
            width=120, font=ctk.CTkFont(size=11),
            command=lambda _: (_toggle_day_pickers(), _regenerate()),
        )
        freq_menu.pack(side="left", padx=(0, 10))

        day_of_week_var = tk.StringVar(value="Monday")
        day_of_week_menu = ctk.CTkOptionMenu(
            sched_frame, variable=day_of_week_var,
            values=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            width=130, font=ctk.CTkFont(size=11),
            command=lambda _: _regenerate(),
        )
        day_of_week_menu.pack(side="left", padx=(0, 10))

        day_of_month_var = tk.StringVar(value="1")
        day_of_month_menu = ctk.CTkOptionMenu(
            sched_frame, variable=day_of_month_var,
            values=[str(i) for i in range(1, 29)],
            width=70, font=ctk.CTkFont(size=11),
            command=lambda _: _regenerate(),
        )

        def _toggle_day_pickers():
            freq = freq_var.get()
            day_of_week_menu.pack_forget()
            day_of_month_menu.pack_forget()
            if freq == "Weekly":
                day_of_week_menu.pack(side="left", padx=(0, 10), after=freq_menu)
            elif freq == "Monthly":
                day_of_month_menu.pack(side="left", padx=(0, 10), after=freq_menu)

        # Time widgets packed into the same row as the How often dropdowns
        # so the popup is one row shorter. Left-padding on "At:" separates
        # the time picker from the day-of-week / day-of-month pickers.
        tk.Label(sched_frame, text="At:", font=("TkDefaultFont", 11)).pack(side="left", padx=(15, 5))
        hour_var = tk.StringVar(value="08")
        ctk.CTkOptionMenu(
            sched_frame, variable=hour_var,
            values=[f"{h:02d}" for h in range(24)],
            width=70, font=ctk.CTkFont(size=11),
            command=lambda _: _regenerate(),
        ).pack(side="left", padx=(0, 3))
        tk.Label(sched_frame, text=":", font=("TkDefaultFont", 11)).pack(side="left")
        minute_var = tk.StringVar(value="00")
        ctk.CTkOptionMenu(
            sched_frame, variable=minute_var,
            values=["00", "15", "30", "45"],
            width=70, font=ctk.CTkFont(size=11),
            command=lambda _: _regenerate(),
        ).pack(side="left", padx=(3, 0))

        # ── Options ──
        tk.Label(
            win, text="Options:",
            font=("TkDefaultFont", 11, "bold"),
        ).pack(anchor="w", padx=15, pady=(4, 2))
        timestamp_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            win, text="Add timestamp to report filenames (--timestamp)",
            variable=timestamp_var, font=("TkDefaultFont", 11),
            command=lambda: _regenerate(),
        ).pack(anchor="w", padx=15)
        stdout_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            win, text="Also save JSON output to a file (--stdout)",
            variable=stdout_var, font=("TkDefaultFont", 11),
            command=lambda: _regenerate(),
        ).pack(anchor="w", padx=15, pady=(0, 6))

        # ── Generated command ──
        tk.Label(
            win, text="Your scheduling command:",
            font=("TkDefaultFont", 11, "bold"),
        ).pack(anchor="w", padx=15, pady=(4, 2))
        cmd_text = tk.Text(
            win, height=4, wrap="word", font=("Courier", 11),
            relief="solid", borderwidth=1,
        )
        cmd_text.pack(fill="x", padx=15, pady=(0, 4))

        cmd_btn_frame = tk.Frame(body)
        cmd_btn_frame.pack(fill="x", padx=15, pady=(0, 6))
        ctk.CTkButton(
            cmd_btn_frame, text="Copy to Clipboard", width=140,
            font=ctk.CTkFont(size=11),
            fg_color="#2E7D32", hover_color="#1B5E20",
            command=lambda: _copy_command(),
        ).pack(side="left")

        # ── Instructions ──
        tk.Label(
            body, text="Step-by-step instructions:",
            font=("TkDefaultFont", 11, "bold"),
        ).pack(anchor="w", padx=15, pady=(4, 2))
        # Text widget with its own scrollbar so both Mac/Linux and Windows
        # instruction blocks fit in a fixed-height window. Close is already
        # packed with side="bottom" above, anchored at the bottom of `win`.
        instr_frame = tk.Frame(body)
        instr_frame.pack(fill="both", expand=True, padx=15, pady=(0, 6))
        instr_vbar = tk.Scrollbar(instr_frame, orient="vertical")
        instr_vbar.pack(side="right", fill="y")
        instr_text = tk.Text(
            instr_frame, height=4, wrap="word", font=("TkDefaultFont", 11),
            relief="solid", borderwidth=1,
            yscrollcommand=instr_vbar.set,
        )
        instr_vbar.config(command=instr_text.yview)
        instr_text.pack(side="left", fill="both", expand=True)

        # ── Helper functions ──

        def _get_suite_names():
            """Return list of suite names for the selected folder."""
            from peekdocs.collection import load_collection
            folder = folder_var.get().strip()
            if not folder or not os.path.isdir(folder):
                return []
            data = load_collection(folder)
            return sorted(data.get("suites", {}).keys())

        def _get_collection_names():
            """Return list of regex collection names."""
            rc_path = os.path.join(os.path.expanduser("~"), ".peekdocs_regex_collections.json")
            if not os.path.exists(rc_path):
                return []
            try:
                with open(rc_path, "r", encoding="utf-8") as f:
                    return sorted(json.load(f).keys())
            except Exception:
                return []

        def _refresh_names():
            """Repopulate the name dropdown based on search type."""
            if search_type_var.get() == "suite":
                names = _get_suite_names()
            else:
                names = _get_collection_names()
            if names:
                name_dropdown.configure(values=names)
                name_var.set(names[0])
            else:
                label = "No suites found" if search_type_var.get() == "suite" else "No collections found"
                name_dropdown.configure(values=[label])
                name_var.set(label)
            _regenerate()

        def _build_peekdocs_cmd():
            """Build the peekdocs CLI command string."""
            python = sys.executable
            stype = search_type_var.get()
            name = name_var.get()
            parts = [python, "-m", "peekdocs"]
            if stype == "suite":
                parts += ["--suite", f'"{name}"']
            else:
                parts += ["--regex-collection", f'"{name}"']
            if recursive_var.get():
                parts.append("-r")
            if timestamp_var.get():
                parts.append("--timestamp")
            parts.append("-qq")  # suppress terminal output for background jobs
            return " ".join(parts)

        def _regenerate():
            """Regenerate the command and instructions."""
            folder = folder_var.get().strip()
            peekdocs_cmd = _build_peekdocs_cmd()
            is_win = platform.system() == "Windows"
            minute = minute_var.get()
            hour = hour_var.get()
            freq = freq_var.get()

            if is_win:
                # schtasks command
                task_name = "peekdocs_scheduled_search"
                # Build the /tr argument
                tr_cmd = f'cmd /c "cd /d \\"{folder}\\" && {peekdocs_cmd}'
                if stdout_var.get():
                    tr_cmd += f' --stdout >> \\"{folder}\\peekdocs_scheduled.json\\"'
                tr_cmd += '"'
                sched = f"/sc {freq.upper()} /st {hour}:{minute}"
                if freq == "Weekly":
                    day_abbr = {"Monday": "MON", "Tuesday": "TUE", "Wednesday": "WED",
                                "Thursday": "THU", "Friday": "FRI", "Saturday": "SAT",
                                "Sunday": "SUN"}
                    sched += f" /d {day_abbr[day_of_week_var.get()]}"
                elif freq == "Monthly":
                    sched += f" /d {day_of_month_var.get()}"
                full_cmd = f'schtasks /create /tn "{task_name}" /tr "{tr_cmd}" {sched} /f'
            else:
                # cron entry
                dow_map = {"Sunday": "0", "Monday": "1", "Tuesday": "2",
                           "Wednesday": "3", "Thursday": "4", "Friday": "5",
                           "Saturday": "6"}
                if freq == "Daily":
                    cron_time = f"{minute} {hour} * * *"
                elif freq == "Weekly":
                    cron_time = f"{minute} {hour} * * {dow_map[day_of_week_var.get()]}"
                else:  # Monthly
                    cron_time = f"{minute} {hour} {day_of_month_var.get()} * *"

                shell_cmd = f'cd "{folder}" && {peekdocs_cmd}'
                if stdout_var.get():
                    shell_cmd += f' --stdout >> "{folder}/peekdocs_scheduled.json"'
                full_cmd = f"{cron_time} {shell_cmd}"

            # Update command box
            cmd_text.configure(state="normal")
            cmd_text.delete("1.0", "end")
            cmd_text.insert("1.0", full_cmd)
            cmd_text.configure(state="disabled")

            # Update instructions — always show both platforms so cross-
            # platform users see the full picture. The user's current OS
            # is shown first.
            instr_text.configure(state="normal")
            instr_text.delete("1.0", "end")
            if is_win:
                instr_text.insert("end", _windows_instructions(folder))
                instr_text.insert("end", "\n\n")
                instr_text.insert("end", _mac_linux_instructions(folder))
            else:
                instr_text.insert("end", _mac_linux_instructions(folder))
                instr_text.insert("end", "\n\n")
                instr_text.insert("end", _windows_instructions(folder))
            instr_text.configure(state="disabled")

        def _mac_linux_instructions(folder):
            return (
                "How to set up this scheduled search (Mac / Linux):\n\n"
                "1. Copy the command above (click Copy to Clipboard).\n\n"
                "2. Open Terminal.\n"
                "   Mac: press Cmd+Space, type \"Terminal\", press Enter.\n"
                "   Linux: press Ctrl+Alt+T, or find Terminal in your applications menu.\n\n"
                "3. Type this and press Enter:\n"
                "   crontab -e\n\n"
                "4. Your crontab file opens in a text editor (usually nano).\n"
                "   Use arrow keys to move to the bottom of the file.\n\n"
                "5. Paste the command on a new line at the bottom.\n"
                "   Mac Terminal: press Cmd+V to paste.\n"
                "   Linux Terminal: press Ctrl+Shift+V to paste.\n\n"
                "6. Save and exit:\n"
                "   In nano: press Ctrl+O, then Enter to save, then Ctrl+X to exit.\n"
                "   In vi: press Escape, then type :wq and press Enter.\n\n"
                "7. Verify it was saved by running:\n"
                "   crontab -l\n"
                "   You should see your new line in the output.\n\n"
                f"Reports will be saved in:\n{folder}\n\n"
                "To stop the scheduled search later:\n"
                "Run \"crontab -e\" again and delete the line, then save.\n"
            )

        def _windows_instructions(folder):
            return (
                "How to set up this scheduled search (Windows):\n\n"
                "1. Copy the command above (click Copy to Clipboard).\n\n"
                "2. Open Command Prompt as Administrator.\n"
                "   Press the Windows key, type \"cmd\".\n"
                "   Right-click \"Command Prompt\" and select\n"
                "   \"Run as administrator\".\n"
                "   Click \"Yes\" when asked for permission.\n\n"
                "3. Paste the command and press Enter.\n"
                "   Right-click in the Command Prompt window to paste.\n\n"
                "4. You should see:\n"
                "   SUCCESS: The scheduled task has been successfully created.\n\n"
                f"Reports will be saved in:\n{folder}\n\n"
                "To see your scheduled tasks:\n"
                "Open Task Scheduler (press Windows key, type \"Task Scheduler\").\n"
                "Look under Task Scheduler Library for\n"
                "\"peekdocs_scheduled_search\".\n\n"
                "To stop the scheduled search later:\n"
                "Open Command Prompt as Administrator and run:\n"
                "schtasks /delete /tn \"peekdocs_scheduled_search\" /f\n"
            )

        def _copy_command():
            cmd = cmd_text.get("1.0", "end").strip()
            self.clipboard_clear()
            self.clipboard_append(cmd)
            self.status_label.configure(
                text="Scheduling command copied to clipboard.",
                text_color="green",
            )

        # Initial population
        _toggle_day_pickers()
        _refresh_names()
        self._apply_dark_theme(win)

        self._center_popup_on_main(win, 680, 720)

    # ── Regex Search ─────────────────────────────────────────────────

