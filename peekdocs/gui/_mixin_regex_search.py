"""PeekDocs GUI — RegexSearchMixin.

Extracted from ``_mixin_tools.py`` in the mixin-tools-split refactor.
Owns the Regex Search feature end-to-end: the main-page Regex Search
button opens a per-pattern search popup; each pattern runs against the
folder as an independent regex; results are grouped by pattern with
per-pattern match counts and per-pattern report sections. Also owns the
standalone Regex Tester popup (Tools → Regex Tester) — a text-window
sandbox for developing a regex against a sample line before saving it
into a collection.

Method surface:

  Search execution:
    _start_regex_search            Kick off the per-pattern search run
    _run_regex_search_per_pattern  Background thread — one pass per pattern
    _cancel_regex_search           Cancel handler (Ctrl-C equivalent)

  Regex Tester dialog:
    _show_regex_tester             Standalone dialog for iterating on a
                                   regex against a sample text — pipes
                                   through _open_search_wizard's regex
                                   picker via on_apply callback
    _show_regex_tester_help        "?" help for Regex Tester

  Help panels:
    _show_regex_search_help        "?" help for Regex Search popup
    _show_regex_builder_help       "?" help for the Regex Wizard picker
                                   (called from _mixin_wizard.py via
                                   `self._show_regex_builder_help(wiz)` —
                                   still resolves through PeekDocsApp's MRO
                                   after this extraction)
"""

import os
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


class RegexSearchMixin:
    def _show_regex_builder_help(self, parent):
        """Help popup for the Regex Wizard (the picker invoked by
        `_open_search_wizard`).

        Distinct from `_show_search_wizard_help`, which documents the
        search-type wizard (the category-cards popup behind the
        Tools → Search Wizard menu entry). This one documents the
        picker-and-combiner popup — categories, checkbox list,
        OR/AND mode, custom regex, Apply target. The AND/OR section
        is the load-bearing part: AND mode's multi-term output is
        only valid for the main search bar (with AND mode in
        Advanced Search Options), NOT for the Regex Tester or the
        Regex Search popup's per-row pattern field."""
        import tkinter as tk

        help_win, _dark = self._themed_toplevel(parent)
        help_win.title("Regex Wizard — Help")
        help_win.geometry("720x640")
        help_win.resizable(True, True)
        try:
            help_win.transient(parent)
        except Exception:
            pass

        # Close button lives in its own bottom-anchored frame so it's
        # on a dedicated row, visually separated from the scrollable
        # text. Packing the frame FIRST with side="bottom" reserves
        # the bottom strip; the text + scrollbar then fill what's left
        # above. Matches the close_frame pattern the Wizard popup
        # itself uses for its own Close button.
        close_frame = tk.Frame(help_win)
        close_frame.pack(side="bottom", fill="x", pady=(6, 12))
        ctk.CTkButton(
            close_frame, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            font=ctk.CTkFont(size=12), command=help_win.destroy,
        ).pack()  # default anchor=center

        txt = tk.Text(
            help_win, wrap="word", font=("TkDefaultFont", 12),
            padx=15, pady=10, borderwidth=0, highlightthickness=0,
        )
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

        h("WHAT THIS POPUP IS")
        b("The Regex Wizard — a picker + combiner for regex patterns.")
        b("Choose a category, check the patterns you want, optionally")
        b("add your own custom regex, choose how to combine them, and")
        b("click Apply. The combined result lands in whichever context")
        b("opened the Regex Wizard — the main search bar, the Regex")
        b("Tester, or the Regex Search popup's first empty pattern row.")
        blank()
        b("Don't confuse it with the Tools → Search Wizard menu entry —")
        b("that one opens the category-cards search-type wizard, and")
        b("one of its cards (\"Regex Wizard\") leads here.")
        blank()
        b("Six categories ship out of the box, 35 patterns total:")
        e("  Common / General         — dates (MM/DD/YYYY and YYYY-")
        e("                              MM-DD), dollar amounts,")
        e("                              percentages, phone, email,")
        e("                              6-digit numbers")
        e("  Business / Finance       — invoice / purchase order /")
        e("                              account numbers, dollar")
        e("                              amounts, dates")
        e("  Legal                    — case numbers, statute")
        e("                              references, Bates numbers,")
        e("                              court dockets, dollar")
        e("                              amounts, dates")
        e("  Engineering / Technical  — part / drawing / serial /")
        e("                              revision numbers,")
        e("                              measurements (mm, cm, m,")
        e("                              in, ft, kg, lb, psi, MPa),")
        e("                              tolerances")
        e("  Real Estate              — parcel / APN, MLS number,")
        e("                              lot/block, square footage,")
        e("                              dollar amounts, dates")
        e("  HR / Admin               — employee IDs, phone, email,")
        e("                              dates, dollar amounts")
        blank()
        b("Some patterns (Dollar Amount, Date, Phone, Email) appear")
        b("in multiple categories on purpose — each category is")
        b("self-sufficient so you don't have to switch dropdowns to")
        b("assemble a typical search.")
        blank()

        h("HOW TO USE IT")
        b("1. Pick a Category from the dropdown.")
        b("2. Check one or more patterns.")
        b("3. Optionally type a custom regex in the Custom regex field —")
        b("   it gets combined with the checked patterns under the")
        b("   selected mode.")
        b("4. Choose OR or AND mode (see next section).")
        b("5. Watch the Preview box — it shows the exact string Apply")
        b("   will produce.")
        b("6. Click Apply to send the result to the caller.")
        blank()
        b("Selections are remembered per category — switching categories")
        b("doesn't lose your earlier checks. Use Clear All to wipe a")
        b("category's checks, or Select All to check everything in it.")
        blank()

        h("OR vs AND — THE KEY CHOICE")
        b("OR and AND mean fundamentally different things and produce")
        b("different output shapes. Get this right or the result is")
        b("either broken or just confusing.")
        blank()
        b("OR mode — combine patterns into ONE regex via alternation.")
        b("A line matches if ANY of the patterns matches. Output is")
        b("a single regex string:")
        e("  (\\d{4}-\\d{2}-\\d{2})|(\\$[\\d,]+)|([A-Z0-9._%+-]+@…)")
        b("This is a valid regex — every regex engine accepts it. Use")
        b("OR for: \"find any of these shapes\" — invoices that mention")
        b("a date OR an amount OR an email, etc.")
        blank()
        b("AND mode — keep patterns SEPARATE, joined with spaces as")
        b("quoted terms. A line matches only if ALL the patterns")
        b("appear on it. Output is multi-term search-bar syntax:")
        e('  "\\d{4}-\\d{2}-\\d{2}" "\\$[\\d,]+" "[A-Z0-9._%+-]+@…"')
        b("This is NOT a valid single regex — it's the multi-term shape")
        b("the peekdocs search bar parses when AND mode is on in")
        b("Advanced Search Options. Use AND for: \"find lines that")
        b("contain all of these shapes\" — e.g., a date AND an amount")
        b("AND a vendor name on the same line.")
        blank()

        h("WHERE OR APPLIES")
        b("OR mode works EVERYWHERE. Every place the Regex Wizard's Apply")
        b("button targets accepts a single regex string:")
        e("  Main search bar (Tools → Search Wizard)")
        e("  Regex Tester       (Tools → Regex Tester → Pick from Wizard…)")
        e("  Regex Search popup (Regex Search → Pick from Wizard…)")
        b("Pick OR if you're unsure. It's the safe default.")
        blank()

        h("WHERE AND APPLIES — AND WHERE IT DOESN'T")
        b("AND mode only works for the main search bar, because that's")
        b("the only context that parses multi-term shapes:")
        blank()
        b("✓ Main search bar (Tools → Search Wizard)")
        b("  Apply puts the multi-term string in the search bar and")
        b("  auto-enables AND mode in Advanced Search Options. The")
        b("  search engine then requires every term to match.")
        blank()
        b("✗ Regex Tester (Pick from Wizard…)")
        b("  The Tester's Pattern field expects ONE regex. AND mode's")
        b("  multi-term output gets dropped in as a literal string —")
        b("  it'll compile as \"match the literal characters \\\"date\\\"")
        b("  \\\"amount\\\"\\\" \" and produce zero matches against any normal")
        b("  text. If you used AND, switch to OR and re-Apply.")
        blank()
        b("✗ Regex Search popup (Pick from Wizard…)")
        b("  Each pattern row holds ONE regex. AND's multi-term output")
        b("  similarly doesn't parse as a single regex. Use OR, or")
        b("  alternatively, paste each individual pattern into its own")
        b("  row manually and they'll all run independently per row.")
        blank()
        b("Rule of thumb: AND mode only makes sense if your destination")
        b("is the main search bar. Otherwise stick to OR.")
        blank()

        h("CUSTOM REGEX FIELD")
        b("Type any regex into the Custom regex field and it gets")
        b("combined with the checked patterns under the selected mode.")
        b("Useful for project-specific shapes that don't fit any")
        b("built-in category — e.g. \"all our purchase orders look like")
        b("PO-\\d{6}\". Empty by default; the field's contents are")
        b("remembered across opens.")
        blank()

        h("APPLY — WHAT IT DOES PER CONTEXT")
        b("Main search bar caller (default):")
        b("  Puts the combined regex in the search bar; auto-enables")
        b("  regex mode and (if AND was selected) auto-enables AND mode")
        b("  in Advanced Search Options. Asks before overwriting any")
        b("  existing search-bar text.")
        blank()
        b("Regex Tester caller (Pick from Wizard… inside the Tester):")
        b("  Replaces the Tester's Pattern field with the combined")
        b("  regex; fires the match highlighter immediately so the")
        b("  sample area lights up without the usual 300 ms debounce.")
        blank()
        b("Regex Search popup caller (Pick from Wizard… next to the")
        b("Whole Word checkbox):")
        b("  Drops the combined regex into the first EMPTY pattern row")
        b("  above; enables that row; seeds the Name field with")
        b("  \"Wizard pattern\" if it was blank. If all 10 rows are")
        b("  already in use, surfaces a dialog telling you to clear")
        b("  one first.")
        blank()

        txt.configure(state="disabled")
        self._apply_dark_theme(help_win)

    # ── Mutual exclusion for search modes ────────────────────



    def _start_regex_search(self):
        """Open the Regex Search popup with 10 pattern rows."""
        import tkinter as tk

        if getattr(self, "search_thread", None) and self.search_thread.is_alive():
            self._show_error("A search is already running.")
            return

        win, _dark = self._themed_toplevel()
        win.withdraw()  # invisible during widget setup; repositioned + shown at end
        win.title("Regex Search")
        win.resizable(True, True)
        # NOTE: do NOT call win.transient(self) here. _themed_toplevel already
        # applies transient() on Windows (where it's needed to keep popups
        # above the main window) and intentionally skips it on macOS, where
        # transient() ties the popup to the parent's monitor and causes it
        # to disappear when dragged across displays in a multi-monitor setup.
        # The Search Suites popup also relies on the helper's default.

        tk.Label(
            win,
            text="Regex searches do not use an index. If searches take a long time it could be due to "
                 "too many results. Check your regex syntax. Results depend on your patterns "
                 "\u2014 peekdocs does not validate regex pattern correctness. Regex entries persist between invocations. "
                 "Reports list every match grouped by pattern. TXT is always written; DOCX / HTML / "
                 "CSV / JSON / PDF are opt-in via the 'Also write:' checkboxes below. DOCX and PDF "
                 "are skipped above 25,000 total matches to keep the GUI responsive \u2014 see ? for details.",
            font=("TkDefaultFont", 10), fg="gray", wraplength=600, justify="left",
        ).pack(fill="x", padx=15, pady=(10, 0))

        header = tk.Frame(win)
        header.pack(fill="x", padx=15, pady=(4, 4))
        tk.Label(
            header, text="Regex Search",
            font=("TkDefaultFont", 13, "bold"),
        ).pack(side="left")
        ctk.CTkButton(
            header, text="?", width=30, height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#1565C0", text_color="white",
            hover_color="#0D47A1",
            corner_radius=15,
            command=lambda: self._show_regex_search_help(win),
        ).pack(side="right")

        # Save/Restore collection buttons
        _collections_path = os.path.join(os.path.expanduser("~"), ".peekdocs_regex_collections.json")

        # Seed the "Examples" collection on first ever Regex Search open.
        # No-op if the user already has any collections (including ones
        # they've deleted Examples from) — peekdocs writes once, then the
        # collections file is the user's data. See peekdocs/regex_examples.py
        # for the pattern list and the design notes behind why it's flat
        # rather than audience-categorized.
        try:
            from peekdocs.regex_examples import seed_examples_if_missing
            seed_examples_if_missing(_collections_path)
        except Exception:
            pass  # If seeding fails, the popup still works with empty state

        # Load config early so the active-collection display can be seeded
        # before any widgets are built. The folder-bar block below reads
        # the same _rs_cfg.
        from peekdocs.cli import _load_config as _lc_rs
        _rs_cfg = _lc_rs()

        # Currently-loaded collection state. We track the name in a mutable
        # holder so closures can both read and write it, and bind the
        # human-readable form to a StringVar so the label updates
        # automatically when _set_active_collection is called from
        # _save_collection / _restore_collection. The window title gets
        # the same name appended.
        _active_collection_name = [(_rs_cfg.get("regex_search_active_collection") or "").strip()]
        _active_collection_display_var = tk.StringVar(value="(no collection loaded)")

        def _set_active_collection(name):
            n = (name or "").strip()
            _active_collection_name[0] = n
            if n:
                _active_collection_display_var.set(f"Currently loaded: {n}")
                try:
                    win.title(f"Regex Search — {n}")
                except Exception:
                    pass
            else:
                _active_collection_display_var.set("(no collection loaded)")
                try:
                    win.title("Regex Search")
                except Exception:
                    pass

        def _save_collection():
            """Save the enabled-and-non-empty pattern rows under a new
            or existing collection name.

            Only rows whose checkbox is ON and whose Regex field is
            non-empty are persisted, so users can curate subsets of a
            larger collection by toggling checkboxes before clicking
            Save. The popup offers two ways to choose the name: type a
            fresh name into the entry, or click a row in the existing-
            collections list to populate the entry with that name (the
            actual write still happens at Save time, with an overwrite
            prompt if the name already exists). Cancel writes nothing.
            """
            import json as _json_rc
            from tkinter import messagebox as _mb

            # Pre-flight: how many rows would we save?
            enabled_rows = []
            for en_var, nm_entry, rx_entry in pattern_rows:
                if not en_var.get():
                    continue
                rx = rx_entry.get().strip()
                if not rx:
                    continue
                enabled_rows.append((nm_entry.get(), rx_entry.get()))
            if not enabled_rows:
                self._show_error(
                    "No enabled patterns to save.\n\n"
                    "Check the box on at least one row with a non-empty "
                    "Regex field, then click Save Collection As again."
                )
                return

            # Load existing collections so we can show them in the picker
            # AND so the overwrite prompt knows what's already on disk.
            collections = {}
            if os.path.exists(_collections_path):
                try:
                    with open(_collections_path, "r", encoding="utf-8") as f:
                        collections = _json_rc.load(f)
                except Exception:
                    pass

            save_win, _ = self._themed_toplevel(win)
            save_win.title("Save Regex Collection")
            save_win.geometry("420x500")
            save_win.transient(win)
            self.update_idletasks()
            _sx = win.winfo_rootx() + (win.winfo_width() - 420) // 2
            _sy = win.winfo_rooty() + (win.winfo_height() - 500) // 2
            save_win.geometry(f"+{_sx}+{_sy}")
            save_win.update_idletasks()
            try:
                save_win.wait_visibility()
            except tk.TclError:
                pass
            try:
                save_win.grab_set()
            except tk.TclError:
                pass

            tk.Label(
                save_win,
                text=f"{len(enabled_rows)} enabled pattern row(s) will be "
                     f"saved. Disabled or empty-regex rows are skipped.",
                font=("TkDefaultFont", 11),
                wraplength=390, justify="left", anchor="w",
            ).pack(fill="x", padx=15, pady=(12, 8))

            tk.Label(
                save_win, text="New collection name:",
                font=("TkDefaultFont", 11, "bold"),
            ).pack(anchor="w", padx=15)
            name_entry = ctk.CTkEntry(
                save_win, width=390, font=ctk.CTkFont(size=11),
            )
            name_entry.pack(padx=15, pady=(2, 2))

            # Track whether the current name came from a listbox click
            # ("Or, click an existing collection to ADD the checked rows
            # to it") versus typed/pre-filled into the entry. The two
            # paths have to do different things on Save:
            #   - Listbox click on existing name  → APPEND to that
            #     collection.
            #   - Typed/pre-filled matching name  → OVERWRITE.
            #   - Typed name that doesn't exist   → CREATE new.
            # The flag flips back to False the moment the user edits the
            # entry, so a pick-then-edit sequence reverts to typed
            # semantics.
            _from_list_pick = [False]

            # Live status: tell the user whether Save will CREATE, ADD, or OVERWRITE
            # based on whether the name matches an existing collection.
            _status_var = tk.StringVar(value="")
            tk.Label(
                save_win, textvariable=_status_var,
                font=("TkDefaultFont", 10, "italic"),
                fg="blue", wraplength=390, justify="left", anchor="w",
            ).pack(fill="x", padx=15, pady=(0, 8))

            def _existing_match(n):
                """Return the existing collection key whose name matches
                *n* case-insensitively, or None. Lets the user type
                'examples' and have it resolve to a collection saved as
                'Examples'."""
                nl = n.lower()
                for k in collections:
                    if k.lower() == nl:
                        return k
                return None

            def _refresh_status(*_):
                n = name_entry.get().strip()
                if not n:
                    _status_var.set("")
                    return
                match = _existing_match(n)
                if match is not None:
                    raw = len(collections[match])
                    if _from_list_pick[0]:
                        _status_var.set(
                            f"➜ Will ADD {len(enabled_rows)} pattern(s) "
                            f"to existing '{match}' "
                            f"({raw} → {raw + len(enabled_rows)} total)."
                        )
                    else:
                        _status_var.set(
                            f"➜ Will OVERWRITE '{match}' with "
                            f"{len(enabled_rows)} pattern(s) "
                            f"({raw} existing entr"
                            f"{'y' if raw == 1 else 'ies'} discarded)."
                        )
                else:
                    _status_var.set(
                        f"➜ Will CREATE new collection '{n}' "
                        f"with {len(enabled_rows)} pattern(s)."
                    )

            # Reset the "came-from-listbox-click" flag whenever the user
            # edits the entry, so a list-pick followed by typing reverts
            # the action to OVERWRITE. <KeyRelease> covers typed input;
            # <<Paste>> and <<Cut>> cover the Cmd-V/Ctrl-V/context-menu
            # paths that don't always emit a KeyRelease the binding can
            # see. The paste/cut virtual events fire BEFORE the entry's
            # buffer is updated, so we defer through after_idle to make
            # sure _refresh_status reads the post-edit text.
            def _on_name_change(*_):
                _from_list_pick[0] = False
                _refresh_status()

            def _on_paste_or_cut(*_):
                save_win.after_idle(_on_name_change)
            try:
                name_entry.bind("<KeyRelease>", _on_name_change)
                name_entry.bind("<<Paste>>", _on_paste_or_cut)
                name_entry.bind("<<Cut>>", _on_paste_or_cut)
            except Exception:
                pass

            if _active_collection_name[0]:
                name_entry.insert(0, _active_collection_name[0])
                _refresh_status()

            if collections:
                tk.Label(
                    save_win,
                    text="Or, click an existing collection to add the checked "
                         "rows to it (populates the field above):",
                    font=("TkDefaultFont", 11, "bold"),
                    wraplength=390, justify="left", anchor="w",
                ).pack(anchor="w", padx=15)
                lb_frame = tk.Frame(save_win)
                lb_frame.pack(fill="both", expand=True, padx=15, pady=(2, 8))
                lb = tk.Listbox(
                    lb_frame, font=("TkDefaultFont", 11),
                    exportselection=False,
                )
                lb_scroll = tk.Scrollbar(
                    lb_frame, orient="vertical", command=lb.yview,
                )
                lb.configure(yscrollcommand=lb_scroll.set)
                lb_scroll.pack(side="right", fill="y")
                lb.pack(side="left", fill="both", expand=True)
                for _cname in sorted(collections.keys()):
                    lb.insert("end", _cname)

                def _on_pick(_evt=None):
                    _sel = lb.curselection()
                    if _sel:
                        name_entry.delete(0, "end")
                        name_entry.insert(0, lb.get(_sel[0]))
                        _from_list_pick[0] = True
                        _refresh_status()
                lb.bind("<<ListboxSelect>>", _on_pick)

            def _do_save():
                name = name_entry.get().strip()
                if not name:
                    _mb.showerror(
                        "Save Collection",
                        "Please enter a collection name.",
                        parent=save_win,
                    )
                    return
                new_patterns = [
                    {"enabled": True, "name": nm, "regex": rx}
                    for nm, rx in enabled_rows
                ]
                match = _existing_match(name)
                if match is not None and _from_list_pick[0]:
                    # ADD. The name came from a click in the existing-
                    # collections list, whose label is "click an
                    # existing collection to add the checked rows to
                    # it." Honor that intent by appending. Use the
                    # match's existing capitalization, not the entry's.
                    combined = list(collections[match]) + new_patterns
                    collections[match] = combined
                    status_text = (
                        f"Added {len(new_patterns)} pattern(s) to "
                        f"'{match}' (now {len(combined)} total)."
                    )
                    name = match
                elif match is not None:
                    # OVERWRITE. The name was typed or pre-filled, not
                    # picked from the list. Treat it as "save the
                    # current row state under this name," which means
                    # replacing whatever was there. Status line already
                    # warned about the discard count. Use the match's
                    # existing capitalization so typing 'examples' when
                    # 'Examples' exists doesn't fork into two keys.
                    discarded = len(collections[match])
                    collections[match] = new_patterns
                    status_text = (
                        f"Overwrote '{match}' with "
                        f"{len(new_patterns)} pattern(s) "
                        f"({discarded} discarded)."
                    )
                    name = match
                else:
                    collections[name] = new_patterns
                    status_text = (
                        f"Created collection '{name}' with "
                        f"{len(new_patterns)} pattern(s)."
                    )
                with open(_collections_path, "w", encoding="utf-8") as f:
                    _json_rc.dump(collections, f, indent=2, ensure_ascii=False)
                _set_active_collection(name)
                save_win.destroy()
                self.status_label.configure(text=status_text, text_color="green")

            btn_row = tk.Frame(save_win)
            btn_row.pack(pady=(0, 12))
            ctk.CTkButton(
                btn_row, text="Save", width=100,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=_do_save,
            ).pack(side="left", padx=5)
            ctk.CTkButton(
                btn_row, text="Cancel", width=100,
                font=ctk.CTkFont(size=12),
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=save_win.destroy,
            ).pack(side="left", padx=5)

            self._apply_dark_theme(save_win)

        def _restore_collection():
            import json as _json_rc
            if not os.path.exists(_collections_path):
                self._show_error("No saved collections found.")
                return
            try:
                with open(_collections_path, "r", encoding="utf-8") as f:
                    collections = _json_rc.load(f)
            except Exception:
                self._show_error("Could not read collections file.")
                return
            if not collections:
                self._show_error("No saved collections found.")
                return
            # Show picker popup. Same X11 pattern as the Suites
            # "Add Search" picker — wait for the toplevel to be
            # viewable before grab_set, and treat grab as best-effort.
            pick_win, _ = self._themed_toplevel(win)
            pick_win.title("Restore From Collection")
            pick_win.geometry("350x300")
            pick_win.transient(win)
            self.update_idletasks()
            px = win.winfo_rootx() + (win.winfo_width() - 350) // 2
            py = win.winfo_rooty() + (win.winfo_height() - 300) // 2
            pick_win.geometry(f"+{px}+{py}")
            pick_win.update_idletasks()
            try:
                pick_win.wait_visibility()
            except tk.TclError:
                pass
            try:
                pick_win.grab_set()
            except tk.TclError:
                pass

            tk.Label(pick_win, text="Select a collection:", font=("TkDefaultFont", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 4))
            pick_lb = tk.Listbox(pick_win, font=("TkDefaultFont", 11), exportselection=False)
            pick_lb.pack(fill="both", expand=True, padx=10, pady=(0, 5))
            for cname in sorted(collections.keys()):
                pick_lb.insert("end", cname)

            def _do_restore():
                sel = pick_lb.curselection()
                if not sel:
                    return
                chosen = pick_lb.get(sel[0])
                patterns = collections[chosen]
                for i, (en_var, nm_entry, rx_entry) in enumerate(pattern_rows):
                    if i < len(patterns):
                        p = patterns[i]
                        en_var.set(p.get("enabled", False))
                        nm_entry.delete(0, "end")
                        nm_entry.insert(0, p.get("name", ""))
                        rx_entry.delete(0, "end")
                        rx_entry.insert(0, p.get("regex", ""))
                    else:
                        en_var.set(False)
                        nm_entry.delete(0, "end")
                        rx_entry.delete(0, "end")
                pick_win.destroy()
                _set_active_collection(chosen)
                self.status_label.configure(
                    text=f"Regex collection '{chosen}' restored.",
                    text_color="green",
                )

            def _do_delete():
                sel = pick_lb.curselection()
                if not sel:
                    return
                chosen = pick_lb.get(sel[0])
                from tkinter import messagebox
                if not messagebox.askyesno("Delete Collection", f"Delete '{chosen}'?", parent=pick_win):
                    return
                del collections[chosen]
                with open(_collections_path, "w", encoding="utf-8") as f:
                    _json_rc.dump(collections, f, indent=2, ensure_ascii=False)
                pick_lb.delete(sel[0])
                # If the deleted collection was the currently-loaded one,
                # clear the label so it doesn't claim a now-missing name.
                if _active_collection_name[0] == chosen:
                    _set_active_collection("")

            btn_row = tk.Frame(pick_win)
            btn_row.pack(pady=(0, 10))
            ctk.CTkButton(btn_row, text="Restore", width=80, font=ctk.CTkFont(size=12), command=_do_restore).pack(side="left", padx=5)
            ctk.CTkButton(btn_row, text="Delete", width=80, font=ctk.CTkFont(size=12),
                          fg_color="#CC3333", hover_color="#AA2222", command=_do_delete).pack(side="left", padx=5)
            ctk.CTkButton(btn_row, text="Cancel", width=80, font=ctk.CTkFont(size=12),
                          fg_color="transparent", text_color=("gray30", "gray70"),
                          hover_color=("gray90", "gray25"), command=pick_win.destroy).pack(side="left", padx=5)
            self._apply_dark_theme(pick_win)

        def _run_multiple_collections():
            """Pick two or more saved collections and run all their
            patterns together against the popup's folder. The visible
            10-row state is left alone — the multi-run reads patterns
            straight off disk, so there's no row-count cap.

            Reuses the popup's Whole Word toggle, the screen-only
            checkbox, and the folder + Recursive settings, so users
            don't need to re-pick those for each run.
            """
            import json as _json_mc
            import re as _re_mc

            if not os.path.exists(_collections_path):
                self._show_error("No saved collections found.")
                return
            try:
                with open(_collections_path, "r", encoding="utf-8") as f:
                    _all_colls = _json_mc.load(f)
            except Exception:
                self._show_error("Could not read collections file.")
                return
            if not _all_colls:
                self._show_error("No saved collections found.")
                return

            mc_win, _ = self._themed_toplevel(win)
            mc_win.title("Run Multiple Collections")
            mc_win.geometry("420x460")
            mc_win.transient(win)
            self.update_idletasks()
            _mx = win.winfo_rootx() + (win.winfo_width() - 420) // 2
            # Anchor the picker's bottom to the parent popup's bottom so
            # it overlays the Run Regex Search button below — keeps the
            # user from misclicking the parent's Run while the picker is
            # open, and visually confirms "this is the active picker now."
            _my = win.winfo_rooty() + win.winfo_height() - 460
            mc_win.geometry(f"+{_mx}+{_my}")
            mc_win.update_idletasks()
            try:
                mc_win.wait_visibility()
            except tk.TclError:
                pass
            try:
                mc_win.grab_set()
            except tk.TclError:
                pass

            tk.Label(
                mc_win,
                text="Select two or more collections to run together. "
                     "Patterns from each are combined into one search "
                     "(folder, Recursive, Whole Word, and report mode "
                     "are taken from the Regex Search popup).",
                font=("TkDefaultFont", 11),
                wraplength=390, justify="left", anchor="w",
            ).pack(fill="x", padx=15, pady=(12, 8))

            # Scrollable checkbox list so big collection counts still fit.
            _list_frame = tk.Frame(mc_win)
            _list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 8))
            _list_canvas = tk.Canvas(_list_frame, highlightthickness=0)
            _list_scroll = tk.Scrollbar(_list_frame, orient="vertical", command=_list_canvas.yview)
            _list_inner = tk.Frame(_list_canvas)
            _list_inner.bind(
                "<Configure>",
                lambda e: _list_canvas.configure(scrollregion=_list_canvas.bbox("all")),
            )
            _list_cw_id = _list_canvas.create_window((0, 0), window=_list_inner, anchor="nw")
            _list_canvas.bind(
                "<Configure>",
                lambda e: _list_canvas.itemconfig(_list_cw_id, width=e.width),
            )
            _list_canvas.configure(yscrollcommand=_list_scroll.set)
            _list_scroll.pack(side="right", fill="y")
            _list_canvas.pack(side="left", fill="both", expand=True)

            _check_vars = {}
            for _cname in sorted(_all_colls.keys()):
                _v = tk.BooleanVar(value=False)
                _check_vars[_cname] = _v
                _n = len(_all_colls[_cname])
                tk.Checkbutton(
                    _list_inner, variable=_v,
                    text=f"{_cname}  ({_n} pattern{'' if _n == 1 else 's'})",
                    font=("TkDefaultFont", 11), anchor="w",
                ).pack(fill="x", anchor="w", padx=4, pady=1)

            def _do_run_multi():
                _picked = [n for n, v in _check_vars.items() if v.get()]
                if len(_picked) < 2:
                    self._show_error(
                        "Select at least two collections.\n\n"
                        "To run a single collection, use Restore From "
                        "Collection and then Run Regex Search."
                    )
                    return
                # Folder must already be set on the popup.
                _folder = _rs_folder_label.cget("text")
                if not _folder or _folder == "(none)" or not os.path.isdir(_folder):
                    self._show_error(
                        "Please pick a folder in the Regex Search popup first."
                    )
                    return
                # Build (display_name, regex) pairs across all picked
                # collections. Prefix each pattern name with its source
                # collection so results clearly attribute matches.
                _active = []
                for _cname in _picked:
                    for _p in _all_colls[_cname]:
                        _rx = (_p.get("regex") or "").strip()
                        if not _rx:
                            continue
                        _pname = (_p.get("name") or "").strip() or "Pattern"
                        _active.append((f"[{_cname}] {_pname}", _rx))
                if not _active:
                    self._show_error(
                        "Selected collections have no non-empty patterns to run."
                    )
                    return
                # Apply Whole Word if the popup's toggle is on.
                if whole_word_var.get():
                    _active = [(n, rf"\b(?:{rx})\b") for n, rx in _active]
                # Per-pattern regex validation — surface a clear error
                # pointing at the offending entry instead of a cryptic
                # combined-regex failure.
                _flag_re = _re_mc.compile(r'^\(\?[aiLmsux]+\)')
                _cleaned = []
                for _n, _rx in _active:
                    try:
                        _re_mc.compile(_rx)
                    except _re_mc.error as exc:
                        self._show_error(
                            f"Invalid regex in {_n}:\n\n{exc}\n\n"
                            "Fix it in the source collection and try again."
                        )
                        return
                    _cleaned.append((_n, _flag_re.sub('', _rx)))
                _combined = "|".join(f"(?:{rx})" for _n, rx in _cleaned)
                try:
                    _re_mc.compile(_combined, _re_mc.IGNORECASE)
                except _re_mc.error as exc:
                    self._show_error(f"Combined regex is invalid:\n\n{exc}")
                    return
                _recursive = _rs_recursive_var.get()
                _screen_only = no_report_var.get()
                # Friendly label for the results popup title/header —
                # listing every collection name gets unwieldy past a few.
                if len(_picked) <= 3:
                    _cn_label = " + ".join(_picked)
                else:
                    _cn_label = f"{len(_picked)} collections"
                _fmts_mc = {
                    "docx": output_docx_var.get(),
                    "html": output_html_var.get(),
                    "csv":  output_csv_var.get(),
                    "json": output_json_var.get(),
                    "pdf":  output_pdf_var.get(),
                }
                mc_win.destroy()
                win.destroy()
                self._run_regex_search_per_pattern(
                    _active, _combined, _folder, _recursive,
                    _screen_only, collection_name=_cn_label,
                    formats=_fmts_mc,
                )

            # Run Selected on its own row, Cancel on the row below it —
            # matches the Add Search to Suite popup pattern and gives
            # the user a clearly-separated "back out without running"
            # action below the primary action button.
            ctk.CTkButton(
                mc_win, text="Cancel", width=90,
                font=ctk.CTkFont(size=12),
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=mc_win.destroy,
            ).pack(side="bottom", pady=(0, 10))
            ctk.CTkButton(
                mc_win, text="Run Selected", width=130,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#FF9800", hover_color="#F57C00",
                command=_do_run_multi,
            ).pack(side="bottom", pady=(8, 4))

            self._apply_dark_theme(mc_win)

        collection_frame = tk.Frame(win)
        collection_frame.pack(fill="x", padx=15, pady=(2, 2))
        ctk.CTkButton(
            collection_frame, text="Save Collection As", width=140,
            font=ctk.CTkFont(size=11), command=_save_collection,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            collection_frame, text="Restore From Collection", width=170,
            font=ctk.CTkFont(size=11), command=_restore_collection,
        ).pack(side="left")
        # Bold + blue so the active-collection name is unmistakable next
        # to the two buttons. The dark-theme helper only overrides fg when
        # the color is generic ("gray", default, etc.), so "blue" stays in
        # both modes — readable on the popup's light-gray light-mode
        # background AND on the dark-mode #2b2b2b.
        tk.Label(
            collection_frame,
            textvariable=_active_collection_display_var,
            font=("TkDefaultFont", 11, "bold"),
            fg="blue",
        ).pack(side="left", padx=(15, 0))

        # Apply the persisted active-collection name now that the label
        # widget exists (the StringVar already has the seeded display text,
        # but this also sets the window title).
        _set_active_collection(_active_collection_name[0])

        # Folder bar with Browse and Recursive
        _saved_rs_folder = getattr(self, "_last_regex_search_folder", None)
        if not _saved_rs_folder:
            _saved_rs_folder = _rs_cfg.get("regex_search_folder")
        _rs_recursive_saved = _rs_cfg.get("regex_search_recursive", True)
        _rs_recursive_var = tk.BooleanVar(value=_rs_recursive_saved)
        _rs_folder_label = self._add_folder_bar(
            win, "",
            initial_folder=_saved_rs_folder,
            recursive_var=_rs_recursive_var,
        )

        # 10 pattern rows
        from tkinter import ttk as _ttk
        _ttk.Separator(win, orient="horizontal").pack(fill="x", padx=15, pady=(6, 4))

        patterns_frame = tk.Frame(win)
        patterns_frame.pack(fill="x", padx=20, pady=(0, 2))

        pattern_rows = []  # list of (enabled_var, name_entry, regex_entry)

        def _remove_pattern_row(idx):
            """Remove the pattern at *idx* from the displayed rows only —
            shift rows below up by one, clear the last slot. Nothing is
            written to disk; the active collection is unchanged until
            the user clicks Save Collection As. Closure binds to
            ``pattern_rows`` — the click can only happen after the loop
            has fully populated it, so the late-bound reference is safe
            even though this is defined pre-loop.
            """
            for j in range(idx, 9):
                en_dst, nm_dst, rx_dst = pattern_rows[j]
                en_src, nm_src, rx_src = pattern_rows[j + 1]
                en_dst.set(en_src.get())
                nm_dst.delete(0, "end")
                nm_dst.insert(0, nm_src.get())
                rx_dst.delete(0, "end")
                rx_dst.insert(0, rx_src.get())
            en_last, nm_last, rx_last = pattern_rows[9]
            en_last.set(False)
            nm_last.delete(0, "end")
            rx_last.delete(0, "end")

        for i in range(1, 11):
            saved_enabled = bool(_rs_cfg.get(f"regex_search_{i}_enabled", False))
            saved_name = _rs_cfg.get(f"regex_search_{i}_name", "")
            saved_regex = _rs_cfg.get(f"regex_search_{i}_regex", "")

            row = tk.Frame(patterns_frame)
            row.pack(fill="x", pady=(3, 0))

            enabled_var = tk.BooleanVar(value=saved_enabled)
            tk.Checkbutton(
                row, variable=enabled_var, font=("TkDefaultFont", 11),
            ).pack(side="left")

            tk.Label(row, text="Name:", font=("TkDefaultFont", 11)).pack(side="left", padx=(0, 2))
            name_entry = ctk.CTkEntry(row, width=130, font=ctk.CTkFont(size=11))
            name_entry.insert(0, saved_name)
            name_entry.pack(side="left", padx=(0, 6))

            tk.Label(row, text="Regex:", font=("TkDefaultFont", 11)).pack(side="left", padx=(0, 2))
            regex_entry = ctk.CTkEntry(row, width=220, font=ctk.CTkFont(size=11))
            regex_entry.insert(0, saved_regex)
            regex_entry.pack(side="left", padx=(0, 6))
            Tooltip(
                regex_entry,
                "Your regex pattern. peekdocs does NOT validate that it "
                "correctly finds what you intend \u2014 you own the outcome.",
            )

            # Per-row minus button: removes this row from the list and
            # shifts the rows below up by one. Default-argument capture
            # of `i` so each button binds to its own zero-based index;
            # lambda free-vars would all resolve to 9 by loop end.
            _minus_btn = ctk.CTkButton(
                row, text="\u2212", width=26, height=26,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="#CC3333", hover_color="#AA2222",
                command=lambda _idx=i - 1: _remove_pattern_row(_idx),
            )
            _minus_btn.pack(side="left", padx=(2, 0))
            Tooltip(
                _minus_btn,
                "Remove this row from the display. Shifts the rows below "
                "up by one and clears the last slot. Nothing is written "
                "to disk \u2014 to persist the change, click Save Collection "
                "As and save under the same name (overwrites) or a new "
                "name (creates a subset).",
            )

            # Per-row "Test" button: opens the Regex Tester pre-filled
            # with this row's regex. The tester's "Use this pattern"
            # button writes back to this row, so the loop is
            # edit-row \u2192 click Test \u2192 iterate against sample \u2192 Use \u2192 done,
            # without ever leaving the Regex Search popup.
            def _open_tester_for_row(_re=regex_entry):
                def _write_back(new_pattern):
                    _re.delete(0, "end")
                    _re.insert(0, new_pattern)
                self._show_regex_tester(
                    initial_pattern=_re.get(),
                    on_use=_write_back,
                )

            _test_btn = ctk.CTkButton(
                row, text="Test", width=44, height=26,
                font=ctk.CTkFont(size=11),
                fg_color="#555555", hover_color="#444444",
                command=_open_tester_for_row,
            )
            _test_btn.pack(side="left", padx=(4, 0))
            Tooltip(
                _test_btn,
                "Open the Regex Tester pre-filled with this row's pattern. "
                "Type sample text and watch matches highlight live; click "
                "Use this pattern to write the edited regex back to this row.",
            )

            pattern_rows.append((enabled_var, name_entry, regex_entry))

        # If no active collection was persisted (older config, or first run
        # after the active-collection feature was added), try to infer one
        # by comparing the just-populated row regexes against every saved
        # collection's regex sequence. Exact positional match wins. Names
        # are intentionally ignored — the user may have renamed a row,
        # which shouldn't break detection if the pattern set is otherwise
        # identical to a known collection.
        if not _active_collection_name[0]:
            try:
                if os.path.exists(_collections_path):
                    import json as _json_ac
                    with open(_collections_path, "r", encoding="utf-8") as f:
                        _saved_colls = _json_ac.load(f)
                    _current_rx = tuple(
                        rx.get().strip() for _e, _n, rx in pattern_rows
                    )
                    for _cname, _patterns in _saved_colls.items():
                        _saved_rx = [p.get("regex", "").strip() for p in _patterns[:10]]
                        while len(_saved_rx) < 10:
                            _saved_rx.append("")
                        if tuple(_saved_rx) == _current_rx:
                            _set_active_collection(_cname)
                            break
            except Exception:
                pass

        # "Whole Word" and "Do not save..." checkboxes
        _ttk.Separator(win, orient="horizontal").pack(fill="x", padx=15, pady=(8, 4))

        whole_word_var = tk.BooleanVar(value=bool(_rs_cfg.get("regex_search_whole_word", False)))
        whole_word_frame = tk.Frame(win)
        whole_word_frame.pack(fill="x", padx=20, pady=(0, 2))
        ww_cb = tk.Checkbutton(
            whole_word_frame, variable=whole_word_var,
            text="Whole Word (wrap each pattern with \\b at run time)",
            font=("TkDefaultFont", 11),
        )
        ww_cb.pack(side="left", anchor="w")
        Tooltip(
            ww_cb,
            "When on, each enabled pattern is wrapped with \\b...\\b before "
            "searching, so it only matches at word boundaries. Patterns that "
            "already include their own \\b, ^, or $ anchors are unaffected by "
            "the extra wrap (\\b is idempotent). Leave off if you want pure "
            "substring behavior or are using lookbehind/lookahead at the edges.",
        )

        def _pick_from_wizard_to_rows():
            """Open the Regex Wizard with Apply rewired to drop the
            combined regex into the FIRST empty pattern row (and enable
            it). If all 10 rows are full, alert the user — they can
            clear a row and click again."""
            def _apply_to_first_empty(combined):
                for en_var, nm_entry, rx_entry in pattern_rows:
                    if not rx_entry.get().strip():
                        rx_entry.delete(0, "end")
                        rx_entry.insert(0, combined)
                        if not nm_entry.get().strip():
                            nm_entry.insert(0, "Wizard pattern")
                        en_var.set(True)
                        return
                from tkinter import messagebox as _mb
                _mb.showinfo(
                    "All rows in use",
                    "All 10 pattern rows already have a regex. Clear a row "
                    "(remove the regex text or click the − button next to it), "
                    "then click Pick from Wizard… again.",
                    parent=win,
                )
            self._open_search_wizard(on_apply=_apply_to_first_empty)

        pfw_btn = ctk.CTkButton(
            whole_word_frame, text="Pick from Wizard…", width=160, height=28,
            font=ctk.CTkFont(size=12),
            command=_pick_from_wizard_to_rows,
        )
        pfw_btn.pack(side="right", padx=(0, 0))
        Tooltip(
            pfw_btn,
            "Open the Regex Wizard (categorized regex picker — 35 named "
            "patterns across 6 categories: dates, money, identifiers, "
            "contacts, code patterns, networking) and drop the combined "
            "regex into the first empty pattern row above. Enables the row "
            "automatically and seeds the Name field with 'Wizard pattern' "
            "if you hadn't named it yet — edit either field to suit. The "
            "Wizard's OR / AND combiner and custom-regex field all work the "
            "same as on the main screen; only the target changes. Note: "
            "the AND-mode output (multi-term shape) won't drop cleanly into "
            "a single regex field — click the Wizard's ? for details.",
        )

        no_report_var = tk.BooleanVar(value=bool(_rs_cfg.get("regex_search_no_report", False)))
        no_report_frame = tk.Frame(win)
        no_report_frame.pack(fill="x", padx=20, pady=(0, 4))
        tk.Checkbutton(
            no_report_frame, variable=no_report_var,
            text="Do not save regex match contents to reports",
            font=("TkDefaultFont", 11),
        ).pack(anchor="w")

        # Output format checkboxes — 1.2.6 opt-in policy mirrored here so
        # Regex Search behaves consistently with Standard Search. TXT is
        # always written; DOCX / HTML / CSV / JSON / PDF are opt-in. The
        # "Do not save..." (screen-only) checkbox above overrides all of
        # these — when on, nothing is written regardless of these
        # selections. Persisted to ~/.peekdocsrc per-key so the user's
        # preferred output set sticks across sessions.
        output_docx_var = tk.BooleanVar(value=bool(_rs_cfg.get("regex_search_output_docx", False)))
        output_html_var = tk.BooleanVar(value=bool(_rs_cfg.get("regex_search_output_html", False)))
        output_csv_var  = tk.BooleanVar(value=bool(_rs_cfg.get("regex_search_output_csv",  False)))
        output_json_var = tk.BooleanVar(value=bool(_rs_cfg.get("regex_search_output_json", False)))
        output_pdf_var  = tk.BooleanVar(value=bool(_rs_cfg.get("regex_search_output_pdf",  False)))
        fmt_frame = tk.Frame(win)
        fmt_frame.pack(fill="x", padx=20, pady=(0, 4))
        tk.Label(fmt_frame, text="Also write:", font=("TkDefaultFont", 11)).pack(side="left", padx=(0, 6))
        tk.Checkbutton(fmt_frame, variable=output_docx_var, text="DOCX", font=("TkDefaultFont", 11)).pack(side="left", padx=2)
        tk.Checkbutton(fmt_frame, variable=output_html_var, text="HTML", font=("TkDefaultFont", 11)).pack(side="left", padx=2)
        tk.Checkbutton(fmt_frame, variable=output_csv_var,  text="CSV",  font=("TkDefaultFont", 11)).pack(side="left", padx=2)
        tk.Checkbutton(fmt_frame, variable=output_json_var, text="JSON", font=("TkDefaultFont", 11)).pack(side="left", padx=2)
        tk.Checkbutton(fmt_frame, variable=output_pdf_var,  text="PDF",  font=("TkDefaultFont", 11)).pack(side="left", padx=2)
        tk.Label(fmt_frame, text="(TXT always written)", font=("TkDefaultFont", 9), fg="gray").pack(side="left", padx=(8, 0))

        def _save_regex_settings():
            """Save all pattern rows and settings to config."""
            try:
                from peekdocs.cli import _load_config, _save_config
                config = _load_config()
                for idx, (en_var, nm_entry, rx_entry) in enumerate(pattern_rows, 1):
                    config[f"regex_search_{idx}_enabled"] = en_var.get()
                    config[f"regex_search_{idx}_name"] = nm_entry.get().strip()
                    config[f"regex_search_{idx}_regex"] = rx_entry.get().strip()
                rs_folder = _rs_folder_label.cget("text")
                if rs_folder and rs_folder != "(none)":
                    config["regex_search_folder"] = rs_folder
                config["regex_search_recursive"] = _rs_recursive_var.get()
                config["regex_search_no_report"] = no_report_var.get()
                config["regex_search_whole_word"] = whole_word_var.get()
                config["regex_search_active_collection"] = _active_collection_name[0]
                config["regex_search_output_docx"] = output_docx_var.get()
                config["regex_search_output_html"] = output_html_var.get()
                config["regex_search_output_csv"]  = output_csv_var.get()
                config["regex_search_output_json"] = output_json_var.get()
                config["regex_search_output_pdf"]  = output_pdf_var.get()
                _save_config(config)
            except Exception:
                pass

        # Clear All, Run, and Close buttons
        btn_frame = tk.Frame(win)
        btn_frame.pack(fill="x", pady=(8, 2), padx=15)
        # Run Multiple Collections sits between the action row above
        # and the Close button below, so it's visually grouped with
        # other run-style actions instead of crowding the top.
        _multi_frame = tk.Frame(win)
        _multi_frame.pack(pady=(4, 0))
        _multi_btn = ctk.CTkButton(
            _multi_frame, text="Run Multiple Collections…", width=210,
            font=ctk.CTkFont(size=11),
            fg_color="#FF9800", hover_color="#F57C00", text_color="white",
            command=_run_multiple_collections,
        )
        _multi_btn.pack()
        Tooltip(
            _multi_btn,
            "Pick two or more saved collections and run all their "
            "patterns at once. Uses the folder, Recursive, Whole Word, "
            "and report-mode settings from this popup. The 10 visible "
            "rows are ignored — patterns come straight from the saved "
            "collections on disk, so there's no row-count limit.",
        )
        close_frame = tk.Frame(win)
        close_frame.pack(pady=(0, 12))

        _saved_before_clear = []  # stores snapshot for Restore All

        def _clear_all():
            # Save current state before clearing
            _saved_before_clear.clear()
            for en_var, nm_entry, rx_entry in pattern_rows:
                _saved_before_clear.append((en_var.get(), nm_entry.get(), rx_entry.get()))
                en_var.set(False)
                nm_entry.delete(0, "end")
                rx_entry.delete(0, "end")

        def _restore_all():
            if not _saved_before_clear:
                return
            for i, (en_var, nm_entry, rx_entry) in enumerate(pattern_rows):
                if i < len(_saved_before_clear):
                    saved_en, saved_nm, saved_rx = _saved_before_clear[i]
                    en_var.set(saved_en)
                    nm_entry.delete(0, "end")
                    nm_entry.insert(0, saved_nm)
                    rx_entry.delete(0, "end")
                    rx_entry.insert(0, saved_rx)

        def _run():
            import re as _re
            from tkinter import messagebox as _mb

            wrap_ww = whole_word_var.get()

            # Collect enabled patterns with non-empty regex
            active = []
            for idx, (en_var, nm_entry, rx_entry) in enumerate(pattern_rows, 1):
                if not en_var.get():
                    continue
                rx = rx_entry.get().strip()
                if not rx:
                    continue
                nm = nm_entry.get().strip() or f"Pattern {idx}"
                # Validate the user's pattern as-typed first so the error
                # message points at what they actually wrote, not the wrapped
                # form. The Whole Word wrap is a non-capturing group around
                # the original pattern, so any error in the original surfaces
                # cleanly without "\b(?:" prefix noise.
                try:
                    _re.compile(rx)
                except _re.error as exc:
                    self._show_error(
                        f"Pattern {idx} ({nm}) has invalid regex:\n\n{exc}\n\n"
                        "Fix the pattern and try again."
                    )
                    return
                if wrap_ww:
                    # \b is idempotent — wrapping a pattern that already has
                    # \b anchors at the edges (like the seeded Examples) is a
                    # no-op. The non-capturing group is essential: \bcat|dog\b
                    # parses as (\bcat)|(dog\b), but \b(?:cat|dog)\b matches
                    # "cat" or "dog" at word boundaries.
                    rx = rf"\b(?:{rx})\b"
                active.append((nm, rx))

            if not active:
                self._show_error("Enable at least one pattern with a non-empty Regex field.")
                return

            # Strip inline global flags (e.g., (?i)) — they cause errors
            # when combined with OR. We apply re.IGNORECASE to the whole pattern.
            _flag_re = _re.compile(r'^\(\?[aiLmsux]+\)')
            cleaned = []
            for _nm, rx in active:
                cleaned.append((_nm, _flag_re.sub('', rx)))
            combined = "|".join(f"(?:{rx})" for _nm, rx in cleaned)

            # Validate the combined regex
            try:
                _re.compile(combined, _re.IGNORECASE)
            except _re.error as exc:
                self._show_error(f"Combined regex is invalid:\n\n{exc}")
                return

            _save_regex_settings()

            rs_folder = _rs_folder_label.cget("text")
            rs_recursive = _rs_recursive_var.get()
            self._last_regex_search_folder = rs_folder
            if rs_folder and rs_folder != "(none)" and os.path.isdir(rs_folder):
                if not hasattr(self, "_searched_folders"):
                    self._searched_folders = set()
                self._searched_folders.add(rs_folder)

            screen_only = no_report_var.get()
            collection_name = _active_collection_name[0]
            _fmts = {
                "docx": output_docx_var.get(),
                "html": output_html_var.get(),
                "csv":  output_csv_var.get(),
                "json": output_json_var.get(),
                "pdf":  output_pdf_var.get(),
            }
            win.destroy()
            self._run_regex_search_per_pattern(
                active, combined, rs_folder, rs_recursive, screen_only,
                collection_name=collection_name,
                formats=_fmts,
            )

        ctk.CTkButton(
            btn_frame, text="Clear All", width=100,
            font=ctk.CTkFont(size=12),
            fg_color="#CC3333", hover_color="#AA2222",
            command=_clear_all,
        ).pack(side="left", padx=(15, 0))
        ctk.CTkButton(
            btn_frame, text="Restore All", width=100,
            font=ctk.CTkFont(size=12),
            fg_color="#555555", hover_color="#444444",
            command=_restore_all,
        ).pack(side="right", padx=(0, 15))
        ctk.CTkButton(
            btn_frame, text="Run Regex Search", width=170,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#FF9800", hover_color="#F57C00",
            command=_run,
        ).pack(expand=True)
        ctk.CTkButton(
            close_frame, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=lambda: (_save_regex_settings(), win.destroy()),
            font=ctk.CTkFont(size=12),
        ).pack()

        self._apply_dark_theme(win)

        # Center on the main window and show. Withdraw + final geometry +
        # deiconify ensures the popup opens on the same monitor as the main
        # page in multi-monitor setups, with no visible jump.
        self.update_idletasks()
        w = win.winfo_reqwidth()
        h = win.winfo_reqheight()
        x = self.winfo_rootx() + (self.winfo_width() - w) // 2
        y = self.winfo_rooty() + (self.winfo_height() - h) // 2
        win.geometry(f"{w}x{h}+{x}+{y}")
        win.deiconify()


    def _run_regex_search_per_pattern(self, active_patterns, combined_regex, folder, recursive, screen_only=True, collection_name="", formats=None):
        """Run regex search per-pattern via API with status updates.

        If screen_only is True, results are shown in a popup with no reports.
        If screen_only is False, results are written to report files and shown in the preview.

        ``collection_name`` is the active Regex Search collection at the time
        Run was clicked. It's surfaced in the results popup title and a
        header label so the user can tell which saved collection produced
        the result set — useful when they have several similar collections.

        Why a popup instead of the main page's Results Preview pane (the
        path Search Suites use)? Three reasons, documented in
        docs/USER_GUIDE.md → "Standard / Suite results land in the
        Preview pane; Regex Search results land in a popup":
          1. Engine reuse — suites delegate to the standard-search
             pipeline that's already wired to the main page; Regex
             Search calls the in-process API directly per pattern and
             would have to re-plumb that wiring by hand.
          2. Shape — per-pattern cards with "View Files / View Text"
             buttons don't fit the single linear preview stream.
          3. Screen-only mode — sensitive runs shouldn't leak into the
             persistent main-page preview; a popup that disappears on
             Close is the natural surface.
        """
        import tkinter as tk

        if not folder or folder == "(none)" or not os.path.isdir(folder):
            self._show_error("Please select a valid folder first.")
            return

        # Clear the right-pane preview at the start of every Regex run.
        # Regex Search itself displays results in its own popup (see the
        # popup-vs-preview rationale in the docstring above), but leaving
        # the previous Standard / Suite results visible while a new regex
        # run is in progress is misleading — the headline + matched-file
        # button advertise a result set that no longer reflects what's
        # about to run. _clear_preview also wipes the headline, the
        # Matched / Excluded buttons, and the cap-status line; the status
        # message it sets ('Preview cleared') is immediately overwritten
        # by the 'Running Regex Search...' message a few lines below.
        if hasattr(self, "_clear_preview"):
            self._clear_preview()

        mode_label = "screen only, no reports" if screen_only else "with reports"

        # Cloud-output guard runs on the main thread BEFORE the worker
        # is spawned. Tkinter modals hang on wait_window() when called
        # from a worker thread. Skip entirely for screen-only runs
        # (nothing gets written). If the user cancels the modal, abort
        # before any UI state changes.
        _rs_resolved_folder = folder
        if not screen_only:
            from peekdocs.gui._helpers import gui_cloud_guard
            from peekdocs.cli import _load_config as _load_cfg_guard
            _rs_redirect_pref = bool(
                _load_cfg_guard().get("redirect_cloud_output", False)
            )
            _rs_resolved_folder, _rs_cloud_decision = gui_cloud_guard(
                self, folder, redirect_to_safe=_rs_redirect_pref,
            )
            if _rs_resolved_folder is None:
                self.status_label.configure(
                    text="Regex Search cancelled — output folder is cloud-synced.",
                    text_color=("red", "#FF6666"),
                )
                return
        # Captured for _show_action_buttons' mtime-vs-cutoff check (see
        # the docstring there) — distinguishes report files written by
        # this run from stale leftovers in the same folder.
        self._last_search_start_time = time.time()
        self.status_label.configure(
            text=f"Running Regex Search ({mode_label})...",
            text_color=("blue", "#66BBFF"),
        )
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        self.progress_bar.grid(row=5, column=0, columnspan=3, padx=10, pady=(2, 2), sticky="ew")

        self._regex_search_cancelled = False
        if hasattr(self, "_regex_search_btn"):
            self._regex_search_btn.configure(
                fg_color="#D32F2F", hover_color="#B71C1C", text="Cancel",
                command=self._cancel_regex_search,
            )

        def _thread():
            # `nonlocal folder` — the write block below reassigns
            # `folder = _rs_resolved_folder` when the cloud-output
            # guard redirected the write target. Without nonlocal,
            # Python treats folder as local throughout _thread from
            # that reassignment, so every earlier read (including
            # `directory=folder` in the api_search loop) hits
            # UnboundLocalError, gets swallowed by the exception
            # handler, and every pattern returns zero matches.
            # Reported symptom (Regex Search "Code patterns" /
            # "Common Code Patterns" against demo folder returned 0
            # matches while the same run via CLI returned 80).
            nonlocal folder
            from peekdocs.api import search as api_search
            start = time.time()
            scan_results = []
            all_matches = []  # combined matches for report generation
            # Track which (file_dir, filename, line_num, text) tuples we
            # already saw across patterns. Multi-collection runs in
            # particular hit the same line with several patterns; without
            # this dedup, the report contains the same line N times and
            # the docx highlighter trips on the duplicate-laden
            # search_terms list, silently dropping all yellow highlights.
            _seen_match_keys = set()
            files_searched = 0
            # Collect the actual file paths each pattern scanned (union
            # across patterns — for a single folder all api_search calls
            # walk the same set, but a set-union is the defensive form
            # if that ever changes). Needed by write_txt_report so the
            # "Files searched ==> N (size)" line in the report shows
            # the real count and total bytes instead of 0 (0 bytes).
            _files_searched_set = set()
            total_patterns = len(active_patterns)

            def _respect_case_intent(rx):
                """If the pattern uses an uppercase-only or lowercase-only
                letter range, wrap the whole thing with an inline (?-i:...)
                so the otherwise-IGNORECASE search engine doesn't match
                the wrong case. \\b[A-Z][A-Z0-9_]{3,}\\b stays an
                UPPER_CASE constant detector instead of matching every
                4+ letter word, which is what was pulling header words
                like 'Document' / 'Westfield' into the report and then
                leaving the corresponding rows un-highlighted (because
                the docx highlighter correctly refused to claim those
                lines under the same case-sensitive interpretation).
                """
                has_upper = "A-Z" in rx
                has_lower = "a-z" in rx
                if has_upper != has_lower:
                    return f"(?-i:{rx})"
                return rx

            for pat_idx, (name, regex) in enumerate(active_patterns, 1):
                if getattr(self, "_regex_search_cancelled", False):
                    break
                self.after(0, lambda i=pat_idx, t=total_patterns, n=name:
                    self.status_label.configure(
                        text=f"Regex Search ({mode_label})... ({i}/{t}) {n}",
                        text_color=("blue", "#66BBFF"),
                    )
                )
                try:
                    result = api_search(
                        [_respect_case_intent(regex)],
                        directory=folder,
                        recursive=recursive,
                        use_regex=True,
                        use_index=False,
                    )
                    files_searched = max(files_searched, len(result.files_searched))
                    _files_searched_set.update(result.files_searched)
                    file_matches = {}
                    # Per-pattern flat list (file_dir, filename, line_num, text)
                    # for the new per-pattern section render in the report.
                    # No cross-pattern dedup here — each pattern's section
                    # stands on its own, so duplicates across patterns are
                    # expected and meaningful.
                    _pattern_matches = []
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
                        _pattern_matches.append(
                            (match.file_dir, match.filename, match.line_num, match.text)
                        )
                        if not screen_only and len(all_matches) < 10000:
                            _mk = (match.file_dir, match.filename, match.line_num, match.text)
                            if _mk not in _seen_match_keys:
                                _seen_match_keys.add(_mk)
                                all_matches.append(_mk)
                    scan_results.append({
                        "name": name,
                        "regex": regex,
                        "match_count": len(result.matches),
                        "file_count": len(file_matches),
                        "files": file_matches,
                        "matches": _pattern_matches,
                    })
                except Exception:
                    scan_results.append({
                        "name": name,
                        "regex": regex,
                        "match_count": 0,
                        "file_count": 0,
                        "files": {},
                    })

            # Group the deduped matches by file, then by line, so the
            # report reads naturally instead of being interleaved in
            # pattern-iteration order. Sort by filename first (case-
            # insensitive), then by folder, then by line_num — this
            # matches what users mean by "alphabetical by document":
            # apple.txt comes before banana.txt whether or not they
            # live in the same folder. Sorting by full path first
            # would cluster files by directory and then jump back to
            # earlier letters when a sibling directory starts; the
            # filename-first key produces one straight A-to-Z pass.
            all_matches.sort(key=lambda m: (
                m[1].lower(), m[0].lower(), m[2],
            ))

            elapsed = time.time() - start

            # Write reports in the background thread (not on GUI thread).
            # DOCX_MATCH_THRESHOLD: above this, skip in-memory-build
            # formats (DOCX, PDF) because python-docx and fpdf2 both
            # build the whole document in memory before saving \u2014 at
            # 100K+ matches that's enough RAM pressure to make macOS
            # swap-thrash and freeze the GUI. TXT / CSV / HTML / JSON
            # are streamed and stay affordable at any size. See
            # docs/USER_GUIDE.md \u2014 'Regex Search reports and the DOCX
            # threshold'.
            _DOCX_MATCH_THRESHOLD = 25_000
            _fmts_local = formats or {}
            if not screen_only and all_matches and not getattr(self, "_regex_search_cancelled", False):
                try:
                    from peekdocs.reporter import write_txt_report, write_docx_report, insert_file_sizes
                    # Dedupe search_terms while preserving order. Multi-
                    # collection runs commonly pick overlapping pattern
                    # sets (Examples and Common Code Patterns both have
                    # IPv4, semver, UUID...) — passing duplicates to the
                    # docx highlighter's "|".join compile makes the
                    # combined regex unnecessarily large and, in some
                    # combinations, drops highlighting entirely.
                    search_terms = list(dict.fromkeys(
                        regex for _name, regex in active_patterns
                    ))
                    # Command line as a multi-line bulleted list — comma-
                    # joining 10+ patterns turned the Command ==> line
                    # into one wall of characters. Bullets are readable.
                    _pattern_bullets = "\n".join(
                        f"  • {n} ({r})" for n, r in active_patterns
                    )
                    command_str = (
                        f"Regex Search across {len(active_patterns)} pattern(s):\n"
                        + _pattern_bullets
                    )
                    # Cloud-output guard was resolved on the main thread
                    # before this worker was spawned — _rs_resolved_folder
                    # is the write target (may be a redirected safe dir).
                    folder = _rs_resolved_folder

                    # Per-pattern section render — each pattern gets its
                    # own headed block listing every match it found, with
                    # no cross-pattern dedup or 10,000-row cap. This is
                    # the natural way to read a regex-collection result
                    # and answers the 'does the report show everything?'
                    # question with 'yes, organized by pattern'.
                    output_path = os.path.join(folder, "peekdocs_regex_results.txt")
                    docx_path = os.path.join(folder, "peekdocs_regex_results.docx")
                    _total_for_threshold = sum(s["match_count"] for s in scan_results)

                    # ── Step 1: TXT (streamed, always written) ────────
                    self.after(0, lambda: self.status_label.configure(
                        text="Regex Search — writing TXT report...",
                        text_color=("blue", "#66BBFF"),
                    ))
                    write_txt_report(
                        output_path, all_matches,
                        sorted(_files_searched_set),
                        search_terms, command_str,
                        "ANY", False, [], False, False, True, False,
                        elapsed, max(1, os.cpu_count() // 2), os.cpu_count() or 1,
                        recursive=recursive, use_index=False,
                        bulleted_terms=True,
                        pattern_sections=scan_results,
                    )

                    # Cancel check between TXT and the optional formats.
                    if getattr(self, "_regex_search_cancelled", False):
                        return

                    # ── Step 2: optional formats, each gated on its
                    #            checkbox in the Regex Search popup ──
                    # DOCX and PDF use in-memory builds → threshold-gated.
                    # CSV / JSON / HTML stream or build small, no cap.
                    result_doc = None
                    if _fmts_local.get("docx"):
                        if _total_for_threshold > _DOCX_MATCH_THRESHOLD:
                            _ts_msg = (
                                f"{_total_for_threshold:,} matches is too many "
                                f"for a Word report (threshold: "
                                f"{_DOCX_MATCH_THRESHOLD:,}). The TXT report "
                                f"has every match — open it with any text "
                                f"editor.\n\nTo get a DOCX too, narrow the "
                                f"search (fewer patterns, smaller folder, or "
                                f"more specific regexes) so the total stays "
                                f"under {_DOCX_MATCH_THRESHOLD:,}."
                            )
                            self.after(0, lambda m=_ts_msg: self._show_error(m))
                        else:
                            self.after(0, lambda: self.status_label.configure(
                                text="Regex Search — writing DOCX report...",
                                text_color=("blue", "#66BBFF"),
                            ))
                            result_doc = write_docx_report(
                                docx_path, output_path,
                                search_terms=search_terms,
                                use_regex=True,
                            )
                            if getattr(self, "_regex_search_cancelled", False):
                                return

                    if _fmts_local.get("html"):
                        self.after(0, lambda: self.status_label.configure(
                            text="Regex Search — writing HTML report...",
                            text_color=("blue", "#66BBFF"),
                        ))
                        from peekdocs.reporter import write_html_report
                        _html_path = os.path.join(folder, "peekdocs_regex_results.html")
                        try:
                            write_html_report(
                                _html_path, all_matches,
                                search_terms=search_terms, use_regex=True,
                            )
                        except Exception:
                            pass
                        if getattr(self, "_regex_search_cancelled", False):
                            return

                    if _fmts_local.get("csv"):
                        self.after(0, lambda: self.status_label.configure(
                            text="Regex Search — writing CSV report...",
                            text_color=("blue", "#66BBFF"),
                        ))
                        from peekdocs.reporter import write_csv_report
                        _csv_path = os.path.join(folder, "peekdocs_regex_results.csv")
                        try:
                            write_csv_report(_csv_path, all_matches)
                        except Exception:
                            pass
                        if getattr(self, "_regex_search_cancelled", False):
                            return

                    if _fmts_local.get("json"):
                        self.after(0, lambda: self.status_label.configure(
                            text="Regex Search — writing JSON report...",
                            text_color=("blue", "#66BBFF"),
                        ))
                        from peekdocs.reporter import write_json_report
                        _json_path = os.path.join(folder, "peekdocs_regex_results.json")
                        try:
                            write_json_report(
                                _json_path, all_matches, search_terms,
                                "ANY", len(_files_searched_set), elapsed,
                                directory=folder,
                            )
                        except Exception:
                            pass
                        if getattr(self, "_regex_search_cancelled", False):
                            return

                    if _fmts_local.get("pdf"):
                        if _total_for_threshold > _DOCX_MATCH_THRESHOLD:
                            _ts_msg = (
                                f"{_total_for_threshold:,} matches is too many "
                                f"for a PDF report (threshold: "
                                f"{_DOCX_MATCH_THRESHOLD:,}). The TXT report "
                                f"has every match.\n\nTo get a PDF too, narrow "
                                f"the search so the total stays under "
                                f"{_DOCX_MATCH_THRESHOLD:,}."
                            )
                            self.after(0, lambda m=_ts_msg: self._show_error(m))
                        else:
                            self.after(0, lambda: self.status_label.configure(
                                text="Regex Search — writing PDF report...",
                                text_color=("blue", "#66BBFF"),
                            ))
                            from peekdocs.reporter import write_pdf_report
                            _pdf_path = os.path.join(folder, "peekdocs_regex_results.pdf")
                            try:
                                write_pdf_report(
                                    _pdf_path, all_matches,
                                    search_terms=search_terms, use_regex=True,
                                )
                            except Exception:
                                pass
                            if getattr(self, "_regex_search_cancelled", False):
                                return

                    # ── Step 3: file-size insert (only when DOCX was
                    #            actually written and is non-empty). ──
                    if result_doc is not None:
                        self.after(0, lambda: self.status_label.configure(
                            text="Regex Search — finalizing...",
                            text_color=("blue", "#66BBFF"),
                        ))
                        insert_file_sizes(output_path, docx_path, result_doc)
                except Exception:
                    pass

            if getattr(self, "_regex_search_cancelled", False):
                return
            self.after(0, _finished, scan_results, elapsed, files_searched, all_matches)

        def _finished(scan_results, elapsed, files_searched, all_matches):
            self.progress_bar.stop()
            self.progress_bar.grid_remove()
            if hasattr(self, "_regex_search_btn"):
                # Restore the original stacked square layout. Previously
                # used 'run_regex_search_label' (full 'Run Regex Search'
                # text) which was wider than the button's square width
                # and forced auto-grow to a rectangle. _stack_label of
                # 'regex_search_label' + explicit 44x44 keeps the
                # button as it started.
                self._regex_search_btn.configure(
                    state="normal",
                    width=44, height=44,
                    fg_color="#FF9800", hover_color="#FF9800",
                    text_color="white",
                    text=self._stack_label(__import__("peekdocs.i18n", fromlist=["t"]).t("regex_search_label")),
                    command=self._start_regex_search,
                )

            total = sum(r["match_count"] for r in scan_results)
            # Match the Wizard-regex bypass-note phrasing in the standard-search
            # status so users see the same "index bypassed" hint regardless of
            # which Run button they pressed. Regex Search always uses
            # direct scan (use_index=False is hardcoded in the api.search call
            # above) because regex queries can't be accelerated by FTS5.
            _bypass_note = " \u2014 index bypassed (regex search uses direct scan)"
            if total == 0:
                self.status_label.configure(
                    text=f"Regex Search complete ({elapsed:.1f}s, {files_searched} files) \u2014 no matches.{_bypass_note}",
                    text_color="green",
                )
            else:
                self.status_label.configure(
                    text=f"Regex Search complete ({elapsed:.1f}s, {files_searched} files) \u2014 {total} match(es).{_bypass_note}",
                    text_color=("black", "#e0e0e0"),
                )

            # Desktop notification (opt-in, focus-suppressed).
            self._fire_completion_notification(
                "peekdocs \u2014 Regex Search complete"
                + (f": {collection_name}" if (collection_name or "").strip() else ""),
                f"{total} match(es) in {files_searched} file(s)  ({elapsed:.1f}s)"
                if total else f"No matches across {files_searched} file(s)  ({elapsed:.1f}s)",
            )

            if not screen_only and all_matches:
                self.results_dir = folder
                # Repoint the main-page Step 4 report buttons at the just-
                # written regex reports, mirroring what Suite runs do at
                # _suite_finished. Without this, after a regex run the
                # main-page DOCX / TXT / CSV / JSON / PDF / HTML buttons
                # still open peekdocs_standard_results.* from whenever
                # the user's last standard search was — silently stale
                # and actively misleading. Regex Search reads output
                # formats from its popup's own 'Also write:' checkboxes
                # (added in 1.2.25), not from Advanced Search Options;
                # any format the user didn't check will flip red. The
                # Regex Search help and the Step 4 disclaimer in
                # Getting Started both spell this out.
                self._report_file_prefix = "peekdocs_regex_results"
                self._last_ts_suffix = ""
                self._show_action_buttons()

            # Show results popup
            popup, _dark = self._themed_toplevel()

            popup.withdraw()  # hidden during widget setup; centered + shown at end
            _cn = (collection_name or "").strip()
            popup.title(
                f"Regex Search Results \u2014 {_cn}" if _cn else "Regex Search Results"
            )
            popup.resizable(True, True)
            self._center_popup_on_main(popup, 800, 520)

            header_frame = tk.Frame(popup)
            header_frame.pack(fill="x", padx=15, pady=(10, 2))
            if total == 0:
                header_text = f"No matches found \u2014 {files_searched} files scanned in {elapsed:.1f}s"
                header_color = "green"
            else:
                header_text = f"{total} match(es) across {files_searched} files ({elapsed:.1f}s)"
                header_color = "black"
            tk.Label(
                header_frame, text="Regex Search Results",
                font=("TkDefaultFont", 14, "bold"),
            ).pack(side="left", expand=True)
            # Mirror the main-popup convention: bold + blue so the
            # active collection name is unmistakable. Only render when a
            # collection was active at run time; ad-hoc runs (no
            # collection loaded) just get the bare "Regex Search Results"
            # header.
            if _cn:
                tk.Label(
                    popup,
                    text=f"Collection: {_cn}",
                    font=("TkDefaultFont", 11, "bold"),
                    fg="blue",
                ).pack(fill="x", padx=15, pady=(0, 2))
            if screen_only:
                tk.Label(
                    popup,
                    text="Screen-only results \u2014 no report files were written.",
                    font=("TkDefaultFont", 10), fg="gray",
                ).pack(fill="x", padx=15, pady=(0, 2))
            else:
                _txt_full = os.path.join(folder, "peekdocs_regex_results.txt")
                _docx_full = os.path.join(folder, "peekdocs_regex_results.docx")
                tk.Label(
                    popup,
                    text=f"Reports saved to:\n  {_txt_full}\n  {_docx_full}",
                    font=("TkDefaultFont", 10), fg="gray",
                    justify="left", anchor="w",
                ).pack(fill="x", padx=15, pady=(0, 2))

                # One-click access to the report files and the folder
                # that holds them. safe_open_file dispatches to the OS
                # default viewer (open on macOS, xdg-open on Linux,
                # os.startfile on Windows) and returns a warning
                # string only on failure.
                def _open_with_helper(path):
                    try:
                        from peekdocs.gui._helpers import safe_open_file
                        w = safe_open_file(path)
                        if w:
                            self._show_error(w)
                    except Exception as exc:
                        self._show_error(f"Could not open {path}:\n{exc}")

                _open_btn_row = tk.Frame(popup)
                _open_btn_row.pack(fill="x", padx=15, pady=(0, 6))
                ctk.CTkButton(
                    _open_btn_row, text="Open TXT", width=100,
                    font=ctk.CTkFont(size=11),
                    command=lambda p=_txt_full: _open_with_helper(p),
                ).pack(side="left", padx=(0, 6))
                ctk.CTkButton(
                    _open_btn_row, text="Open DOCX", width=100,
                    font=ctk.CTkFont(size=11),
                    command=lambda p=_docx_full: _open_with_helper(p),
                ).pack(side="left", padx=(0, 6))
                ctk.CTkButton(
                    _open_btn_row, text="Open Folder", width=110,
                    font=ctk.CTkFont(size=11),
                    command=lambda p=folder: _open_with_helper(p),
                ).pack(side="left")
            tk.Label(
                popup, text=header_text,
                font=("TkDefaultFont", 12), fg=header_color,
            ).pack(pady=(0, 8))

            # Scrollable results
            canvas_frame = tk.Frame(popup)
            canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))
            canvas = tk.Canvas(canvas_frame, highlightthickness=0)
            scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
            inner = tk.Frame(canvas)
            inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            _cw_id = canvas.create_window((0, 0), window=inner, anchor="nw")
            canvas.bind("<Configure>", lambda e: canvas.itemconfig(_cw_id, width=e.width))
            canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)

            for res in scan_results:
                row_frame = tk.Frame(inner, bd=1, relief="groove")
                row_frame.pack(fill="x", padx=5, pady=3)

                top_row = tk.Frame(row_frame)
                top_row.pack(fill="x", padx=8, pady=(4, 2))
                tk.Label(
                    top_row, text=res["name"],
                    font=("TkDefaultFont", 12, "bold"),
                ).pack(side="left")
                if res["files"]:
                    _files_data = res["files"]
                    _cat_name = res["name"]
                    _cat_regex = res["regex"]
                    ctk.CTkButton(
                        top_row, text="View Files",
                        width=80, font=ctk.CTkFont(size=10),
                        command=lambda f=_files_data, c=_cat_name, p=popup, r=_cat_regex: self._show_sensitive_category_files(f, c, p, regex=r),
                    ).pack(side="right", padx=(0, 5))

                count_text = f"{res['match_count']} match(es) in {res['file_count']} file(s)"
                count_color = "green" if res["match_count"] == 0 else "black"
                tk.Label(
                    top_row, text=count_text,
                    font=("TkDefaultFont", 11), fg=count_color,
                ).pack(side="left", padx=(0, 8))

                tk.Label(
                    row_frame, text=f"Regex: {res['regex']}",
                    font=("Courier", 10), fg="gray",
                ).pack(anchor="w", padx=8, pady=(0, 4))

            # Close button
            ctk.CTkButton(
                popup, text="Close", width=80,
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=popup.destroy, font=ctk.CTkFont(size=12),
            ).pack(pady=(5, 10))

            self._apply_dark_theme(popup)

        thread = threading.Thread(target=_thread, daemon=True)
        thread.start()


    def _cancel_regex_search(self):
        """Cancel a running Regex Search."""
        self._regex_search_cancelled = True
        self.status_label.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("status_regex_cancelled"), text_color=("blue", "#66BBFF"))
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        if hasattr(self, "_regex_search_btn"):
            # Restore stacked square layout — same fix as the post-
            # regex-finish restore site.
            self._regex_search_btn.configure(
                state="normal",
                width=44, height=44,
                fg_color="#FF9800", hover_color="#FF9800",
                text_color="white",
                text=self._stack_label(__import__("peekdocs.i18n", fromlist=["t"]).t("regex_search_label")),
                command=self._start_regex_search,
            )

    def _show_regex_tester(self, initial_pattern="", initial_sample="", on_use=None):
        """Live regex tester popup.

        Pattern at the top, sample text in the middle, matches and per-
        match list at the bottom. Typing in either the pattern or the
        sample triggers a debounced re-match (~300 ms) — matches are
        highlighted in yellow in the sample widget as the user types,
        invalid regex shows the compile error inline rather than as a
        modal exception. Closes the build → run → fix loop that the
        Regex Search popup otherwise forces users into.

        Parameters
        ----------
        initial_pattern : str
            Pre-fill the pattern entry. Used when the tester is opened
            from a Regex Search popup row (the row's regex is passed in
            so the user can iterate on an existing pattern).
        initial_sample : str
            Pre-fill the sample text area. Useful when the tester is
            opened with selected text from another widget.
        on_use : callable[[str], None] | None
            Called with the current pattern string when the user clicks
            "Use this pattern." When None, the button is hidden (the
            tester is standalone and there's no caller to hand the
            pattern back to).
        """
        import tkinter as tk
        from tkinter import filedialog

        win, _dark = self._themed_toplevel()
        win.title("Regex Tester")
        win.geometry("760x660")
        win.resizable(True, True)
        try:
            win.transient(self)
        except Exception:
            pass

        # ── Header with title + ? help ──────────────────────
        header = tk.Frame(win)
        header.pack(fill="x", padx=15, pady=(10, 0))
        tk.Label(
            header, text="Regex Tester",
            font=("TkDefaultFont", 13, "bold"),
        ).pack(side="left")
        ctk.CTkButton(
            header, text="?", width=30, height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#1565C0", text_color="white",
            hover_color="#0D47A1",
            corner_radius=15,
            command=lambda: self._show_regex_tester_help(win),
        ).pack(side="right")

        # ── Pattern row ─────────────────────────────────────
        pattern_frame = tk.Frame(win)
        pattern_frame.pack(fill="x", padx=15, pady=(8, 4))
        tk.Label(
            pattern_frame, text="Pattern:",
            font=("TkDefaultFont", 11, "bold"),
        ).pack(side="left", padx=(0, 6))
        pattern_entry = ctk.CTkEntry(
            pattern_frame, width=600,
            font=ctk.CTkFont(family="Courier", size=12),
        )
        pattern_entry.pack(side="left", fill="x", expand=True)
        if initial_pattern:
            pattern_entry.insert(0, initial_pattern)

        status_var = tk.StringVar(value="")
        status_label = tk.Label(
            win, textvariable=status_var,
            font=("TkDefaultFont", 11), anchor="w", justify="left",
        )
        status_label.pack(fill="x", padx=15, pady=(0, 6))

        # ── Sample text widget ──────────────────────────────
        sample_frame = tk.Frame(win)
        sample_frame.pack(fill="both", expand=True, padx=15, pady=(0, 4))
        tk.Label(
            sample_frame, text="Sample text (type, paste, or load a file):",
            font=("TkDefaultFont", 11, "bold"), anchor="w",
        ).pack(fill="x")
        sample_inner = tk.Frame(sample_frame)
        sample_inner.pack(fill="both", expand=True, pady=(2, 0))
        sample_scroll = tk.Scrollbar(sample_inner, orient="vertical")
        sample_scroll.pack(side="right", fill="y")
        sample_text = tk.Text(
            sample_inner, wrap="word", height=10,
            font=("Courier", 11),
            yscrollcommand=sample_scroll.set,
            undo=True,
        )
        sample_text.pack(side="left", fill="both", expand=True)
        sample_scroll.config(command=sample_text.yview)
        # Yellow highlight tag — same color as the standard-search
        # preview's "match" tag so the tester feels of-a-piece with the
        # rest of the GUI.
        sample_text.tag_configure(
            "match", background="#FFFF00", foreground="#000000",
        )
        if initial_sample:
            sample_text.insert("1.0", initial_sample)

        # ── Sample source buttons ──────────────────────────
        source_frame = tk.Frame(win)
        source_frame.pack(fill="x", padx=15, pady=(0, 4))

        def _paste_from_clipboard():
            try:
                content = win.clipboard_get()
            except tk.TclError:
                return
            sample_text.delete("1.0", "end")
            sample_text.insert("1.0", content)
            _rematch_now()

        # Sample-text size cap. Larger samples make the live re-match
        # path feel sluggish (and a pathological regex on a big sample
        # can hang for seconds — Python's re has no native timeout).
        # 50 KB is enough to represent realistic short documents while
        # keeping the debounced re-match snappy.
        _SAMPLE_CAP = 50 * 1024

        # Binary container formats (DOCX = ZIP of XML; PDF = binary
        # stream; XLSX = ZIP; ePub = ZIP; archives; OCR images; etc.)
        # must skip the UTF-8 fast path even though it 'succeeds' under
        # errors='replace' — what users actually want for these formats
        # is the extracted text, not the raw container bytes rendered as
        # replacement characters.
        _NEEDS_EXTRACTION = {
            ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
            ".odt", ".ods", ".odp", ".pdf", ".epub", ".rtf",
            ".pages", ".numbers", ".key",
            ".zip", ".7z", ".rar", ".tar", ".gz", ".tgz", ".bz2",
            ".msg", ".pst",
            ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp",
            ".dxf", ".vsdx",
        }

        def _load_from_file():
            path = filedialog.askopenfilename(parent=win)
            if not path:
                return
            _ext = os.path.splitext(path)[1].lower()
            _force_extract = _ext in _NEEDS_EXTRACTION
            try:
                if _force_extract:
                    # Skip the fast path entirely for binary containers;
                    # falling through to the OSError-style branch via
                    # raise is the cleanest way to route into the
                    # extractor without duplicating its body here.
                    raise UnicodeDecodeError("forced", b"", 0, 1, "binary container")
                # Plain text fast path — read directly.
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read(_SAMPLE_CAP + 1)
                if len(content) > _SAMPLE_CAP:
                    content = content[:_SAMPLE_CAP] + "\n\n…(truncated to 50 KB)…"
            except (UnicodeDecodeError, OSError):
                # Not plain text — route through the same extractor the
                # search engine uses. This is what makes the tester
                # useful against actual Word / PDF / Excel content the
                # user is planning to search.
                try:
                    from peekdocs.scanner import _extract_lines
                    lines = _extract_lines(path, use_ocr=False)
                    content = "\n".join(t for _ln, t in lines)
                    if len(content) > _SAMPLE_CAP:
                        content = content[:_SAMPLE_CAP] + "\n\n…(truncated to 50 KB)…"
                except Exception as exc:
                    self._show_error(
                        f"Couldn't extract text from {os.path.basename(path)}:\n\n{exc}"
                    )
                    return
            sample_text.delete("1.0", "end")
            sample_text.insert("1.0", content)
            _rematch_now()

        ctk.CTkButton(
            source_frame, text="Paste from clipboard", width=160,
            font=ctk.CTkFont(size=11), command=_paste_from_clipboard,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            source_frame, text="Load from file…", width=140,
            font=ctk.CTkFont(size=11), command=_load_from_file,
        ).pack(side="left")

        # ── Match list ──────────────────────────────────────
        matches_frame = tk.Frame(win)
        matches_frame.pack(fill="both", expand=False, padx=15, pady=(8, 4))
        tk.Label(
            matches_frame, text="Matches:",
            font=("TkDefaultFont", 11, "bold"), anchor="w",
        ).pack(fill="x")
        list_inner = tk.Frame(matches_frame)
        list_inner.pack(fill="both", expand=True, pady=(2, 0))
        list_scroll = tk.Scrollbar(list_inner, orient="vertical")
        list_scroll.pack(side="right", fill="y")
        match_list = tk.Text(
            list_inner, wrap="none", height=6,
            font=("Courier", 10),
            yscrollcommand=list_scroll.set,
            state="disabled",
        )
        match_list.pack(side="left", fill="both", expand=True)
        list_scroll.config(command=match_list.yview)

        # ── Action buttons ──────────────────────────────────
        action_frame = tk.Frame(win)
        action_frame.pack(pady=(8, 4))

        def _translate_pattern():
            pat = pattern_entry.get()
            if not pat:
                return
            try:
                from peekdocs.translator import _translate_regex
                translation = _translate_regex(pat)
            except Exception as exc:
                translation = f"(translator error: {exc})"
            self._show_simple_popup(
                "Pattern in plain English",
                f"Regex: {pat}",
                translation,
            )

        if on_use:
            ctk.CTkButton(
                action_frame, text="Use this pattern", width=140,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#1565C0", hover_color="#0D47A1", text_color="white",
                command=lambda: (on_use(pattern_entry.get()), win.destroy()),
            ).pack(side="left", padx=4)

        def _copy_to_clipboard():
            pat = pattern_entry.get()
            if not pat:
                return
            win.clipboard_clear()
            win.clipboard_append(pat)

        ctk.CTkButton(
            action_frame, text="Copy to clipboard", width=140,
            font=ctk.CTkFont(size=12),
            command=_copy_to_clipboard,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            action_frame, text="Translate to plain English", width=190,
            font=ctk.CTkFont(size=12),
            command=_translate_pattern,
        ).pack(side="left", padx=4)

        def _pick_from_wizard():
            """Open the Regex Wizard with its Apply button rewired to
            populate this Tester's pattern field instead of the main
            search bar. Reuses the Wizard's category dropdown +
            checkbox list + OR/AND combiner + custom-regex field so
            there's no duplicated UI to maintain."""
            def _apply_to_tester(combined):
                pattern_entry.delete(0, "end")
                pattern_entry.insert(0, combined)
                # Skip the debounce — the user just clicked Apply, they
                # want to see matches immediately.
                _rematch_now()
                try:
                    pattern_entry.icursor("end")
                except Exception:
                    pass
            self._open_search_wizard(on_apply=_apply_to_tester)

        ctk.CTkButton(
            action_frame, text="Pick from Wizard…", width=160,
            font=ctk.CTkFont(size=12),
            command=_pick_from_wizard,
        ).pack(side="left", padx=4)

        # Close on its own row, centered. Visually separates the
        # dismiss action from the pattern-action row (Use / Copy /
        # Translate) so it's hard to misclick when reaching for one of
        # the pattern actions.
        close_frame = tk.Frame(win)
        close_frame.pack(pady=(0, 12))
        ctk.CTkButton(
            close_frame, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            font=ctk.CTkFont(size=12), command=win.destroy,
        ).pack()

        # ── Live re-match (debounced) ───────────────────────
        # `_pending` holds the after() ID of the next scheduled rematch
        # so we can cancel-and-reschedule on every keystroke. Net effect:
        # one rematch per 300 ms of typing, not one per keystroke.
        _pending = [None]
        _RE_DEBOUNCE_MS = 300

        def _format_position(text, char_index):
            """Translate a character offset within the sample text to
            (line, column), both 1-indexed for display."""
            up_to = text[:char_index]
            line = up_to.count("\n") + 1
            last_newline = up_to.rfind("\n")
            col = char_index - (last_newline + 1) + 1
            return line, col

        def _rematch_now(*_args):
            import re as _re_mod
            pat = pattern_entry.get()
            sample = sample_text.get("1.0", "end-1c")

            # Clear previous match tags + reset the list widget. Tag
            # removal first so a transient-invalid pattern blanks the
            # highlights immediately rather than leaving stale ones.
            sample_text.tag_remove("match", "1.0", "end")
            match_list.configure(state="normal")
            match_list.delete("1.0", "end")

            if not pat:
                status_var.set("(no pattern)")
                status_label.configure(fg="gray")
                match_list.configure(state="disabled")
                return

            try:
                compiled = _re_mod.compile(pat)
            except _re_mod.error as exc:
                status_var.set(f"✗ Invalid regex: {exc}")
                status_label.configure(fg="#CC3333")
                match_list.configure(state="disabled")
                return

            matches = list(compiled.finditer(sample))
            count = len(matches)
            if count == 0:
                status_var.set("✓ Compiles  —  no matches in sample")
                status_label.configure(fg=("gray30" if not _dark else "gray70"))
            else:
                status_var.set(f"✓ Compiles  —  {count} match(es)")
                status_label.configure(fg="#1B7A1B")

            # Apply the yellow tag to every match span. tk.Text indices
            # are line.column 1-based, so we convert char offsets to
            # that shape via Text's "1.0 + N chars" syntax.
            for i, m in enumerate(matches):
                start, end = m.span()
                if start == end:
                    # Zero-width match (e.g., a stray \b). Skip — Text
                    # can't apply a tag over a zero-width range and the
                    # iteration would loop on it.
                    continue
                sample_text.tag_add(
                    "match",
                    f"1.0 + {start} chars",
                    f"1.0 + {end} chars",
                )
                # Cap the list at first 200 entries; users testing
                # against very generic patterns don't need a 10,000-line
                # match list scrolling out of bounds.
                if i < 200:
                    line, col_start = _format_position(sample, start)
                    _, col_end = _format_position(sample, end)
                    snippet = m.group(0)
                    if len(snippet) > 60:
                        snippet = snippet[:57] + "…"
                    match_list.insert(
                        "end",
                        f"  {i + 1:>3}. {snippet}   (L{line}, c{col_start}–c{col_end})\n",
                    )
            if count > 200:
                match_list.insert(
                    "end",
                    f"  … and {count - 200} more (list capped at 200; "
                    f"highlights are applied to all)\n",
                )
            match_list.configure(state="disabled")

        def _schedule_rematch(*_args):
            if _pending[0] is not None:
                try:
                    win.after_cancel(_pending[0])
                except Exception:
                    pass
            _pending[0] = win.after(_RE_DEBOUNCE_MS, _rematch_now)

        # Bind the debounced rematch to both inputs. KeyRelease fires
        # after the character is in the widget, so reading entry.get()
        # / text.get() inside the handler sees the updated content.
        try:
            pattern_entry.bind("<KeyRelease>", _schedule_rematch)
        except Exception:
            pass
        sample_text.bind("<KeyRelease>", _schedule_rematch)
        sample_text.bind("<<Paste>>", lambda _e: win.after(50, _rematch_now))

        self._apply_dark_theme(win)
        # First render — fire the rematch immediately so the highlight
        # state is consistent with the seeded pattern + sample on open.
        _rematch_now()
        try:
            pattern_entry.focus_set()
        except Exception:
            pass

    def _show_regex_tester_help(self, parent):
        """Help popup for the Regex Tester."""
        import tkinter as tk

        help_win, _dark = self._themed_toplevel()
        help_win.title("Regex Tester — Help")
        help_win.geometry("760x600")
        help_win.resizable(True, True)
        try:
            help_win.transient(parent)
        except Exception:
            pass

        # Close button packed FIRST with side="bottom" so it reserves
        # its space before the scrollable Text takes the rest. Matches
        # the convention used by every other help popup in the project.
        ctk.CTkButton(
            help_win, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            font=ctk.CTkFont(size=12), command=help_win.destroy,
        ).pack(side="bottom", pady=(5, 12))

        txt = tk.Text(
            help_win, wrap="word", font=("TkDefaultFont", 12),
            padx=15, pady=10, borderwidth=0, highlightthickness=0,
        )
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

        h("WHAT THIS IS")
        b("The Regex Tester is a scratchpad for crafting a regular")
        b("expression against sample text and watching matches highlight")
        b("in real time. Type a pattern at the top, paste or load sample")
        b("text below, and matches appear in yellow as you type — no need")
        b("to run a full search against a folder just to see whether a")
        b("pattern works.")
        blank()
        b("Open it from Tools → Regex Tester (standalone), or from the")
        b("Test button next to any pattern row in the Regex Search popup")
        b("(pre-fills the tester with that row's regex; the Use this")
        b("pattern button writes the edited regex back to the row).")
        blank()

        h("HOW TO USE IT")
        b("1. Type a regex in the Pattern field at the top.")
        b("2. Type or paste text into the Sample text area, or click")
        b("   Load from file… to extract text from any of the 100+ file")
        b("   types peekdocs supports (Word, PDF, Excel, CSV, .eml,")
        b("   source code, etc.) — the first 50 KB is loaded.")
        b("3. Watch the Sample text area: every match gets a yellow")
        b("   highlight, and the Matches list below shows each match in")
        b("   order with its line + column position.")
        b("4. Tweak the pattern until matches look right.")
        b("5. Use this pattern (if opened from a Regex Search row) writes")
        b("   the pattern back to the row. Copy to clipboard puts it on")
        b("   the system clipboard so you can paste it anywhere.")
        blank()
        b("Re-matching is debounced to ~300 ms after the last keystroke,")
        b("so typing feels smooth even on long sample text.")
        blank()

        h("STATUS LINE")
        b("Just below the Pattern field, the status line tells you what")
        b("the tester sees:")
        e("  (no pattern)                       — Pattern field is empty")
        e("  ✗ Invalid regex: <error>           — Regex won't compile")
        e("  ✓ Compiles — no matches in sample  — Valid, just no hits here")
        e("  ✓ Compiles — N match(es)           — Valid, with N matches")
        blank()
        b("Invalid-regex errors are inline (no modal popup) — fix and")
        b("the status flips back to green as soon as the pattern parses.")
        blank()

        h("PATTERN ACTIONS")
        b("Use this pattern (only shown when the tester was opened from")
        b("a Regex Search row) — copy the current pattern back to that")
        b("row and close the tester.")
        blank()
        b("Copy to clipboard — put the current pattern on the system")
        b("clipboard, then close the tester. Handy when you want to paste")
        b("the pattern into another tool, a chat message, a notebook, etc.")
        blank()
        b("Translate to plain English — describe the pattern in words")
        b("using peekdocs's built-in translator (the same one that")
        b("produces the Translation ==> line in every search report).")
        b("Useful for sanity-checking that a pattern means what you")
        b("intended it to mean.")
        blank()
        b("Pick from Wizard… — open the Regex Wizard (the categorized")
        b("regex picker — same one reached from the main screen's")
        b("Search Wizard → Regex Wizard card) and route its Apply target")
        b("to this Tester's Pattern field instead of the main search")
        b("bar. Useful when you want a ready-made pattern (dates, money,")
        b("identifiers, contacts, code patterns, networking) to start")
        b("from, then tweak or combine inside the Tester. Closes the")
        b("Regex Wizard popup on Apply; matches highlight immediately")
        b("in the sample area below — no debounce delay.")
        b("Note: pick OR mode in the Wizard — AND mode produces a")
        b("multi-term shape that doesn't compile as a single regex.")
        blank()

        h("SAMPLE TEXT SOURCES")
        b("Type directly — small patterns are often easier to verify")
        b("against a handful of typed-out examples than a real document.")
        blank()
        b("Paste from clipboard — fills the sample area with whatever's")
        b("on the system clipboard.")
        blank()
        b("Load from file… — opens a file picker; the selected file is")
        b("read or extracted (Word / PDF / Excel / archives — anything")
        b("peekdocs supports) and the first 50 KB of its text content")
        b("fills the sample area. Use this to verify a pattern against")
        b("the actual shape of content you plan to search.")
        blank()

        h("LIMITS")
        b("Sample text is capped at 50 KB. Larger samples make the live")
        b("debounced re-match path feel sluggish, and a pathological")
        b("regex on a big sample can hang the GUI briefly — Python's")
        b("regex engine has no native timeout, so the cap is the")
        b("simplest protective measure.")
        blank()
        b("The Matches list is capped at the first 200 hits, but the")
        b("yellow highlight in the sample text covers every match. A")
        b("very generic pattern (e.g., \\w+) will produce thousands of")
        b("matches and a 200-line list with a tail count — not a 10,000-")
        b("line list scrolling out of bounds.")
        blank()
        b("Catastrophic backtracking (a runaway pattern with nested")
        b("quantifiers) can still freeze the tester for a few seconds.")
        b("If the GUI stops responding while you're editing a pattern,")
        b("that's the cause — wait, then simplify the pattern.")
        blank()

        h("TESTING AGAINST REAL DOCUMENTS")
        b("The Load from file… button is the killer feature: it routes")
        b("the file through the same text-extraction pipeline that the")
        b("search engine uses, so you can craft a pattern against the")
        b("exact shape of content it will meet in production. A pattern")
        b("that matches \"line 7 of test.txt\" doesn't necessarily match")
        b("\"paragraph 7 of a .docx\" — for Word / PDF / Excel, a")
        b("\"line\" is a paragraph / row, not a 80-character text line.")
        b("Loading the actual file reveals what the pattern will see")
        b("when the search runs.")
        blank()

        txt.configure(state="disabled")
        self._apply_dark_theme(help_win)

    def _show_regex_search_help(self, parent):
        """Show help for the Regex Search feature."""
        import tkinter as tk

        help_win, _dark = self._themed_toplevel()
        help_win.title("Regex Search \u2014 Help")
        help_win.geometry("850x600")
        help_win.resizable(True, True)
        help_win.transient(self)
        help_win.bind("<FocusIn>", lambda e: help_win.lift())
        help_win.lift()
        help_win.after(50, help_win.lift)
        help_win.after(100, help_win.focus_force)

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
                          lmargin2=20,
                          foreground="#999999" if ctk.get_appearance_mode() == "Dark" else "gray40")

        def h(text):
            txt.insert("end", text + "\n", "heading")

        def b(text):
            txt.insert("end", text + "\n", "body")

        def e(text):
            txt.insert("end", text + "\n", "example")

        def blank():
            txt.insert("end", "\n")

        # Table of Contents
        txt.insert("end", "TABLE OF CONTENTS\n", "toc_title")
        for section in [
            "What This Is",
            "How to Use It",
            "Saving and Restoring Collections",
            "Pattern Tips",
            "Common Regex Patterns (50 Examples)",
            "Checkboxes (Whole Word, Report)",
            "Advanced Search Options",
            "Performance and Index",
            "Reports and the DOCX Threshold",
            "Disclaimer",
        ]:
            txt.insert("end", f"\u2022 {section}\n", "toc_item")
        txt.insert("end", "\n")

        h("WHAT THIS IS")
        b("Regex Search lets you define up to 10 named regex patterns")
        b("in this popup and run them all at once against a folder of")
        b("your choice. Each pattern has a Name (for your reference)")
        b("and a Regex (the actual pattern to search for). Each enabled")
        b("pattern with a non-empty Regex field is executed separately,")
        b("with per-pattern match counts shown in the results.")
        blank()
        b("The 10-row limit is a per-popup workbench cap, not a")
        b("collection-size cap. Saved collections on disk can hold")
        b("any number of patterns — the seeded Examples collection")
        b("ships with 17, and you can grow collections beyond 10 via")
        b("Save Collection As (ADD mode). Such collections run")
        b("end-to-end from the CLI with peekdocs --regex-collection")
        b("NAME (every pattern, no cap) or from this popup via Run")
        b("Multiple Collections… at the bottom (every pattern in")
        b("every picked collection, no cap).")
        blank()
        b("Viewing rows beyond 10 in the GUI: there isn't one. The")
        b("workbench is a 10-row editor — Restore From Collection")
        b("loads the first 10 patterns of any collection, and rows")
        b("11+ are not shown here.")
        blank()
        b("Easiest workaround if your goal is just to RUN more than")
        b("10 patterns at once: split them across two or more")
        b("collections of ≤10 patterns each (e.g. 'project-codes',")
        b("'error-shapes', 'todo-markers'), then click Run Multiple")
        b("Collections… at the bottom and check all the ones you")
        b("want. Patterns from every picked collection merge into")
        b("one run; the 10-row workbench limit doesn't apply, and")
        b("every pattern stays editable in its own collection's")
        b("workbench view.")
        blank()
        b("To view, edit, or remove patterns beyond row 10 of a")
        b("single collection without splitting it, hand-edit")
        b("~/.peekdocs_regex_collections.json (plain JSON, one")
        b("top-level key per collection name; each value is a list")
        b("of {name, regex, enabled} objects). The file is documented")
        b("in the User Guide's Regex Collection Use Cases section.")
        b("Run paths (CLI / Run Multiple) read the full collection")
        b("straight off disk, so a hand-edit takes effect on the")
        b("next run with no GUI step required.")
        blank()
        b("This is useful when you have several patterns you want to")
        b("check simultaneously \u2014 for example, searching for multiple")
        b("error codes, project identifiers, or data formats across")
        b("a large folder tree.")
        blank()
        b("Note: you can also run a single regex search via Standard")
        b("Search by checking 'Regex' in Advanced Search Options and")
        b("typing your pattern directly. The Regex Search popup is for")
        b("running multiple named patterns at once with saved settings.")
        blank()
        b("Regex Search is a GUI-only feature. The CLI supports single")
        b("regex searches via the -x flag (e.g., peekdocs -x \"\\d{3}-\\d{4}\").")
        b("To run multiple patterns from the CLI, combine them manually")
        b("with | (e.g., peekdocs -x \"pattern1|pattern2\").")
        blank()
        b("For a detailed comparison of Regex Search vs Standard Search")
        b("and vs Search Suites, see 'Standard Search (blue button) vs")
        b("Regex Search' and 'Regex Search vs Search Suites' in")
        b("the main screen ? help.")
        blank()
        b("Note: Regex Search results appear in a separate popup window,")
        b("not in the main Results Preview pane. This is different from")
        b("Standard Search, which shows results in the Results Preview")
        b("with an green Matched Files button on the status line. The")
        b("popup approach is used because Regex Search runs each pattern")
        b("separately and supports screen-only mode (no reports). Use")
        b("View Files in the results popup to see per-file matches and")
        b("View Text to see highlighted content \u2014 this is the same")
        b("workflow as the main search results.")
        blank()

        h("HOW TO USE IT")
        b("1. Click the Regex Search button on the main screen.")
        b("2. Use Browse to select the folder to search.")
        b("3. Check the Recursive box to include subfolders.")
        b("4. For each pattern you want to use:")
        b("   a. Check the checkbox on the left to enable it.")
        b("   b. Enter a short name in the Name field.")
        b("   c. Enter your regex in the Regex field.")
        b("5. Decide whether to generate report files (see below).")
        b("6. Click Run.")
        blank()
        b("Your pattern names, regex strings, folder, and checkbox")
        b("settings are automatically saved between sessions.")
        blank()
        b("Do NOT wrap your regex in quotes inside the Regex field.")
        b("Type the raw regex pattern directly — peekdocs passes it")
        b("straight to Python's re engine without any shell parsing.")
        b("Quotes are only needed when typing a regex into the CLI")
        b("(e.g. peekdocs -x '\\d+\\.\\d+'), where the shell would")
        b("otherwise interpret special characters before peekdocs sees")
        b("them. In the GUI Regex field, adding quotes makes peekdocs")
        b("look for the literal double-quote character.")
        blank()
        b("Clear All erases all 10 pattern rows (checkboxes, names,")
        b("and regex fields). Restore All puts them back \u2014 it undoes")
        b("the most recent Clear All. Useful if you accidentally clear")
        b("patterns you meant to keep.")
        blank()

        h("SAVING AND RESTORING COLLECTIONS")
        b("Save Collection As saves the enabled (checked) pattern rows")
        b("under a label you choose. Disabled rows and rows with empty")
        b("Regex fields are skipped \u2014 only what is currently checked")
        b("makes it into the collection. This lets you carve out subsets")
        b("of a larger collection: restore the full set, uncheck the")
        b("rows you don't want, then Save Collection As under a new name.")
        blank()
        b("The Save popup picks one of three actions based on how the")
        b("name in the entry got there and whether it matches an")
        b("existing collection:")
        blank()
        b("\u2022 CREATE \u2014 the name is new (does not match any existing")
        b("  collection). A new collection is created with the")
        b("  checked rows.")
        b("\u2022 OVERWRITE \u2014 the name was typed into the entry (or left as")
        b("  the pre-filled active-collection name) AND it matches an")
        b("  existing collection. The collection is replaced with the")
        b("  checked rows; previous contents are discarded.")
        b("\u2022 ADD \u2014 the name was set by clicking an entry under 'Or,")
        b("  click an existing collection...' AND it matches an")
        b("  existing collection. The checked rows are appended to")
        b("  that collection. Editing the name entry after a list")
        b("  click reverts the action to OVERWRITE.")
        blank()
        b("A live status line below the name field tells you which of")
        b("the three actions will happen and shows the resulting count")
        b("(and discard count for OVERWRITE) before you commit.")
        blank()
        b("Workflow 1 \u2014 Remove patterns from a saved collection:")
        b("1. Restore From Collection \u2192 pick the collection.")
        b("2. Click the red \u2212 button next to one or more patterns")
        b("   you want to drop. Each click shifts the rows below")
        b("   up by one. The saved collection on disk is not")
        b("   changed yet.")
        b("3. Click Save Collection As.")
        b("4. In the New collection name field, enter the same name")
        b("   as the loaded collection. The match is case-")
        b("   insensitive \u2014 typing 'examples' resolves to a")
        b("   collection saved as 'Examples'. The name is also")
        b("   pre-filled with the active collection name, so most")
        b("   of the time you can leave it as-is.")
        b("5. Click Save. The collection is overwritten with what")
        b("   remains in the rows \u2014 the \u2212 patterns are gone.")
        blank()
        b("Workflow 2 \u2014 Append patterns from one collection to another:")
        b("1. Restore From Collection \u2192 pick the source collection")
        b("   (the one whose patterns you want to copy from). Its")
        b("   rows now fill the popup.")
        b("2. Click Save Collection As.")
        b("3. In the existing-collections list (the section labeled")
        b("   'Or, click an existing collection to add the checked")
        b("   rows to it'), click the destination collection name.")
        b("   The status line flips to 'Will ADD ...'.")
        b("4. Click Save. The source rows are appended to the")
        b("   destination collection.")
        b("Tip: if you click a collection in the list and then start")
        b("typing in the name entry, the action reverts to OVERWRITE")
        b("\u2014 editing the entry tells peekdocs you no longer want")
        b("the list-click's Add intent.")
        blank()
        b("Workflow 3 \u2014 Run two or more collections together:")
        b("1. Pick a folder in the Regex Search popup (and set")
        b("   Recursive, Whole Word, and the report checkbox to")
        b("   what you want).")
        b("2. Click 'Run Multiple Collections\u2026' (the button just")
        b("   above Close at the bottom of the popup).")
        b("3. In the picker, check two or more collections and click")
        b("   Run Selected. Patterns are pulled straight off disk \u2014")
        b("   the 10 visible rows are ignored, so there's no cap")
        b("   on how many patterns can run together.")
        b("Pattern names in the results popup are prefixed with")
        b("their source collection (e.g. '[Examples] Email address'),")
        b("so you can tell which collection produced which hits.")
        blank()
        b("Restore From Collection loads a previously saved collection,")
        b("replacing whatever is currently in the pattern rows. Saved")
        b("collections with more than 10 patterns are truncated to the")
        b("first 10 in the rows; collections with fewer than 10 leave")
        b("the trailing rows blank and disabled.")
        blank()
        b("Use this to maintain multiple regex profiles \u2014 for example:")
        b("\u2022 'Code patterns' \u2014 TODOs, deprecated APIs, error patterns")
        b("\u2022 'Invoice extraction' \u2014 dollar amounts, account numbers, dates")
        b("\u2022 'Research notes' \u2014 citations, URLs, abbreviations")
        blank()
        b("Collections are stored in ~/.peekdocs_regex_collections.json")
        b("and persist across sessions. The Restore picker also includes")
        b("a Delete button to remove collections you no longer need.")
        blank()
        b("CLI usage and scheduled runs: saved collections can be run")
        b("from the command line for automation. For shell loops,")
        b("--timestamp, the Python API, and a Windows PowerShell variant,")
        b("see \"Regex Collection Use Cases\" in the User Guide. To")
        b("generate a ready-to-paste cron (macOS/Linux) or Task Scheduler")
        b("(Windows) command without leaving the GUI, use Tools →")
        b("Schedule Search.")
        blank()

        h("PATTERN TIPS")
        b("Plain words and phrases work as patterns too \u2014 for example,")
        b("entering budget or quarterly report will match those terms")
        b("literally. If your search term contains special regex characters")
        b("($ . * + ? [ ] ( ) { } | ^), prefix them with a backslash.")
        b("For example, use \\$500 to search for $500.")
        blank()
        b("Patterns use Python regex syntax. A few common examples:")
        blank()
        e("  \\bERR-\\d{4}\\b        Match error codes like ERR-1234")
        e("  (?i)todo|fixme        Case-insensitive TODO or FIXME")
        e("  \\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}   IPv4 addresses")
        e("  https?://\\S+          URLs starting with http or https")
        blank()
        b("Use regex101.com (Python flavor) to test your patterns")
        b("before running them here.")
        blank()

        h("COMMON REGEX PATTERNS (50 EXAMPLES)")
        b("Copy and paste these into the Regex field. All searches")
        b("are case-insensitive. Test on regex101.com first.")
        blank()
        e("  Alphanumeric IDs          [A-Za-z0-9]{8,}")
        e("  Binary numbers            \\b[01]{4,}\\b")
        e("  CSV-style fields          \"[^\"]*\"")
        e("  Currency amounts          \\$[0-9,]+\\.?[0-9]*")
        e("  Dates (MM/DD/YYYY)        \\d{2}/\\d{2}/\\d{4}")
        e("  Dates (YYYY-MM-DD)        \\d{4}-\\d{2}-\\d{2}")
        e("  Dates with month names    (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\\s+\\d{1,2},?\\s+\\d{4}")
        e("  Decimal numbers           \\b\\d+\\.\\d+\\b")
        e("  Domain names              \\b[a-z0-9-]+\\.(com|org|net|edu|gov|io)\\b")
        e("  Email addresses           [A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}")
        e("  Environment variables     \\$\\{?[A-Z_][A-Z0-9_]*\\}?")
        e("  Error codes               \\bERR[-_]?\\d{3,5}\\b")
        e("  File extensions           \\.[a-z]{2,4}\\b")
        e("  Filenames                 [A-Za-z0-9_.-]+\\.[a-z]{2,4}")
        e("  Hexadecimal values        \\b0x[0-9A-Fa-f]+\\b")
        e("  HTML tags                 <[^>]+>")
        e("  Integers                  \\b\\d+\\b")
        e("  Invoice numbers           INV[-#]?\\d{4,}")
        e("  IPv4 addresses            \\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}")
        e("  IPv6 addresses            [0-9a-fA-F:]{15,39}")
        e("  JSON key/value pairs      \"[^\"]+\"\\s*:\\s*\"[^\"]*\"")
        e("  Linux/macOS file paths    /[\\w./-]+")
        e("  Log severity levels       \\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\\b")
        e("  Log timestamps            \\d{4}-\\d{2}-\\d{2}[T ]\\d{2}:\\d{2}:\\d{2}")
        e("  MAC addresses             ([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}")
        e("  Markdown headings         ^#{1,6}\\s+.+")
        e("  Markdown links            \\[([^\\]]+)\\]\\(([^)]+)\\)")
        e("  Negative numbers          -\\d+\\.?\\d*")
        e("  Octal numbers             \\b0[0-7]+\\b")
        e("  Part numbers              \\b[A-Z]{2,3}-\\d{4,}\\b")
        e("  Percentages               \\b\\d+(\\.\\d+)?%")
        e("  Phone numbers             \\d{3}[-.]\\d{3}[-.]\\d{4}")
        e("  Product codes             \\b[A-Z]{2,4}-\\d{3,}[A-Z]?\\b")
        e("  Purchase order numbers    PO[-#]?\\d{4,}")
        e("  Repeated words            \\b(\\w+)\\s+\\1\\b")
        e("  Scientific notation       \\d+\\.?\\d*[eE][+-]?\\d+")
        e("  Semantic versions         \\bv?\\d+\\.\\d+\\.\\d+\\b")
        e("  Serial numbers            \\b[A-Z0-9]{8,12}\\b")
        e("  Time zones                (EST|CST|MST|PST|EDT|CDT|MDT|PDT|UTC|GMT)")
        e("  Times (HH:MM)             \\b\\d{1,2}:\\d{2}\\b")
        e("  Timestamps                \\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}")
        e("  Tracking numbers          \\b1Z[A-Z0-9]{16}\\b")
        e("  12-hour times with AM/PM  \\d{1,2}:\\d{2}\\s*(AM|PM)")
        e("  UNC network paths         \\\\\\\\[\\w.-]+\\\\[\\w.$-]+")
        e("  URLs / web links          https?://\\S+")
        e("  UUID / GUID values        [0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
        e("  Version numbers           \\bv\\d+\\.\\d+(\\.\\d+)?\\b")
        e("  Windows file paths        [A-Z]:\\\\[\\w\\\\.-]+")
        e("  XML tags                  </?[a-zA-Z][a-zA-Z0-9]*[^>]*>")
        e("  ZIP / postal codes        \\b\\d{5}(-\\d{4})?\\b")
        blank()
        b("Note: these patterns are starting points. They may produce")
        b("false positives or miss edge cases. Always review results")
        b("in context and refine patterns as needed.")
        blank()
        b("You can also create your own regex patterns. Good sources")
        b("for learning and finding patterns:")
        blank()
        b("\u2022 regex101.com \u2014 interactive regex tester (select Python flavor)")
        b("\u2022 Search the web for 'regex for [what you need]'")
        b("\u2022 Ask Claude or ChatGPT to write a regex for you \u2014 describe")
        b("  what you want to match in plain English and paste the")
        b("  result into the Regex field")
        blank()
        b("Any valid Python regex can be entered in the Regex field.")
        b("peekdocs validates syntax before running but does not check")
        b("whether the pattern matches what you intend.")
        blank()

        h("CHECKBOXES (WHOLE WORD, REPORT)")
        b("Whole Word")
        blank()
        b("When checked, each enabled pattern is wrapped with \\b...\\b")
        b("at run time (in a non-capturing group so alternation like")
        b("cat|dog still behaves as expected). \\b is a word-boundary")
        b("assertion: it matches at the transition between a word")
        b("character (letter, digit, or underscore) and a non-word")
        b("character. The wrap is harmless when a pattern already has")
        b("its own \\b anchors — \\b is idempotent.")
        blank()
        b("Use Whole Word for short keyword-style patterns. Without the")
        b("wrap, the bare regex 'TODO' matches inside 'TODOIST'; with")
        b("Whole Word on, only standalone occurrences match.")
        blank()
        b("Whole Word does NOT prevent substring matches caused by")
        b("dotted, colon-separated, or dash-separated number sequences.")
        b("A semver pattern like \\d+\\.\\d+\\.\\d+ will still match")
        b("inside an IP address like 192.168.1.100 even with Whole")
        b("Word on, because a dot is a non-word character and \\b")
        b("fires on either side of it. The fix for those is to add")
        b("negative lookbehind/lookahead inside the pattern itself")
        b("(see the seeded Examples collection for working versions).")
        blank()
        b("The setting persists between sessions.")
        blank()
        b("'Do not save regex match contents to reports'")
        blank()
        b("When UNCHECKED (default): the combined regex is placed in")
        b("the main search bar, the Regex checkbox is turned on, and")
        b("a normal search runs. Report files (.txt, .docx, etc.)")
        b("are generated as usual.")
        blank()
        b("The Regex Search Results popup then shows the report paths")
        b("under 'Reports saved to:' with three buttons: Open TXT,")
        b("Open DOCX, and Open Folder. Each one hands the path to the")
        b("OS default viewer — TextEdit / Notepad / your configured")
        b(".txt editor for the .txt, Word / Pages / LibreOffice for the")
        b(".docx, and Finder / Explorer for the folder. The reports")
        b("live next to the searched files (peekdocs_regex_results.txt")
        b("and peekdocs_regex_results.docx), so opening the folder")
        b("also gives you direct access for emailing, archiving, or")
        b("editing.")
        blank()
        b("When checked, the search runs in the background through the")
        b("API. Results are displayed in a screen-only popup and are not")
        b("written to report files on disk. This is designed to prevent")
        b("sensitive information from being saved to files. Use this")
        b("option when your search patterns may match content you prefer")
        b("not to persist on disk. The Open TXT / Open DOCX / Open")
        b("Folder buttons do not appear in screen-only mode because")
        b("there are no files to open.")
        blank()
        b("Note: standard search does not have a screen-only mode, but")
        b("you can achieve a similar effect by checking Delete on Close")
        b("in Advanced Search Options \u2014 report files are created during")
        b("the search but automatically deleted when you close the app.")
        b("For immediate cleanup, use Tools → Clear Files →")
        b("Wipe Session. You can also review results in the Results")
        b("Preview and Matched Files \u2192 View Text without opening any")
        b("report files.")
        blank()

        h("ADVANCED SEARCH OPTIONS")
        b("Regex Search ignores the Advanced Search Options panel on")
        b("the main screen entirely \u2014 file type filters, exclude")
        b("terms, max matches, max file size, context lines, proximity,")
        b("OCR, range filters, and the rest. Everything Regex Search")
        b("needs comes from this popup:")
        blank()
        b("\u2022 Folder \u2014 the popup's folder picker")
        b("\u2022 Recursive \u2014 the popup's checkbox")
        b("\u2022 Output formats \u2014 the 'Also write:' checkboxes")
        b("  (TXT is always written; DOCX / HTML / CSV / JSON / PDF")
        b("  are opt-in per checkbox)")
        blank()
        b("Engine settings are fixed: regex is forced on, fuzzy and")
        b("wildcard are forced off, and the search index is bypassed")
        b("(every run scans files directly).")
        blank()
        b("Screen-only mode ('Do not save regex match contents to")
        b("reports') changes the destination of results \u2014 popup only,")
        b("no files written \u2014 but does not change what is scanned.")
        blank()

        h("PERFORMANCE AND INDEX")
        b("Regex searches do not use the search index. Every search")
        b("scans files directly from disk. This means:")
        blank()
        b("\u2022 No need to build or refresh an index before searching")
        b("\u2022 Results always reflect current file contents")
        b("\u2022 Searches may be slower than indexed keyword searches,")
        b("  especially on large folders or network drives")
        blank()
        b("If a search takes a long time, common causes are:")
        blank()
        b("\u2022 Too many results \u2014 a broad pattern like .+ matches")
        b("  every line in every file. Be specific.")
        b("\u2022 Very large files \u2014 set Max File Size in Advanced")
        b("  Search Options to skip files over a certain size")
        b("  (default 100 MB, set to 0 for no limit).")
        b("\u2022 Large folder tree \u2014 uncheck Recursive to search")
        b("  only the selected folder, not all subfolders.")
        blank()
        b("Tip: set Max Matches in Advanced Search Options to")
        b("limit results. Default is 1000. Set to 0 for unlimited,")
        b("but be aware that very large result sets slow down")
        b("report generation and the Results Preview.")
        blank()

        h("REPORTS AND THE DOCX THRESHOLD")
        b("Regex Search always writes a TXT report. DOCX, HTML, CSV,")
        b("JSON, and PDF are opt-in via the 'Also write:' checkboxes")
        b("at the bottom of the popup — matches the 1.2.6 Standard")
        b("Search behavior where DOCX is also opt-in. Each format:")
        b("• peekdocs_regex_results.txt — always written. Every match")
        b("  grouped by pattern, no cap. Open with any text editor.")
        b("• peekdocs_regex_results.docx — opt-in. Same content with")
        b("  yellow highlighting on each match. SKIPPED above 25,000")
        b("  total matches across all patterns (in-memory build; would")
        b("  freeze the GUI on huge result sets).")
        b("• peekdocs_regex_results.html — opt-in. Highlighted browser-")
        b("  ready report. Streams to disk, no threshold.")
        b("• peekdocs_regex_results.csv — opt-in. Per-match rows for")
        b("  spreadsheet import (utf-8-sig BOM for Excel compat).")
        b("• peekdocs_regex_results.json — opt-in. Machine-readable.")
        b("• peekdocs_regex_results.pdf — opt-in. Highlighted PDF.")
        b("  SAME 25,000-match threshold as DOCX (fpdf2 also builds")
        b("  the whole document in memory before saving).")
        b("Format choices persist across sessions in ~/.peekdocsrc.")
        blank()
        b("Why the threshold? python-docx builds the entire Word")
        b("document in memory before saving. At 100,000+ matches,")
        b("that's enough RAM pressure to make macOS swap-thrash and")
        b("freeze the GUI — you can't even click Cancel because the")
        b("main thread is starved waiting for memory. The 25,000")
        b("threshold is a safety net that keeps the GUI responsive")
        b("on pathological result sets while still producing a DOCX")
        b("for normal regex runs (which rarely hit five digits of")
        b("matches).")
        blank()
        b("If you see the 'too many matches for a Word report' popup")
        b("and you really want a DOCX of the highlighted results,")
        b("three options:")
        blank()
        b("• Narrow the search — fewer patterns, smaller folder,")
        b("  more specific regexes — so the total stays under 25,000.")
        b("• Run patterns one at a time. Each single-pattern run")
        b("  produces its own DOCX with that pattern's matches only;")
        b("  most individual patterns won't trip the threshold.")
        b("• Read the TXT report. It has every match grouped by")
        b("  pattern with the same Document / Line / Match format")
        b("  the DOCX uses — just without the yellow highlighting.")
        blank()
        b("Cancellation: clicking Cancel during report writing now")
        b("stops cleanly between TXT → DOCX → finalize steps. On")
        b("pre-1.2.26 versions a cancel during the DOCX write would")
        b("not take effect because there was no cancel check between")
        b("the writes; the bg thread would keep building the giant")
        b("Word document until done. Fixed.")
        blank()

        h("DISCLAIMER")
        b("peekdocs does NOT validate that your regex patterns")
        b("correctly identify the data you intend to find. You are")
        b("responsible for the accuracy of your patterns and the")
        b("interpretation of results. Regex-based matching is")
        b("heuristic \u2014 false positives and missed matches are")
        b("possible.")
        blank()

        txt.configure(state="disabled")

        ctk.CTkButton(
            help_win, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=help_win.destroy, font=ctk.CTkFont(size=12),
        ).pack(pady=(5, 10))

        self._apply_dark_theme(help_win)
