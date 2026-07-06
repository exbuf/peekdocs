"""PeekDocs GUI — SuitesMixin.

Extracted from ``_mixin_tools.py`` in the mixin-tools-split refactor.
Owns Search Suites end-to-end: a saved group of standard searches that
run together as a single unit, producing one combined highlighted
report with per-search sections. The green Search Suites button on the
main page opens the suite picker; each suite runs its constituent
saved searches in sequence with each search's original settings
(AND/OR, regex, recursive, etc.) preserved.

Method surface:

  Popup / management:
    _show_search_suites           Opens the Search Suites picker
                                  popup (create, run, edit, delete
                                  suites; opt into output formats;
                                  "Run Multiple Search Suites…" combined
                                  runner)
    _show_search_suites_help      "?" help for the picker

  Suite execution:
    _run_suite_searches           Loop each saved search in the suite,
                                  invoke the CLI, gather match blocks
                                  into per-search sections
    _suite_finished               Assemble the combined TXT / DOCX /
                                  HTML / CSV / JSON / PDF reports and
                                  render into the GUI
    _cancel_suite                 User-cancel handler
    _update_suite_elapsed         Ticking elapsed-time updater
    _show_suite_completion_popup  Small confirmation popup after
                                  the suite finishes with "Open TXT /
                                  DOCX / Folder" buttons

External call surface: only one caller in _mixin_build.py:578
(the Search Suites button on the main page); still resolves via
PeekDocsApp's MRO after this extraction.
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


class SuitesMixin:
    def _show_search_suites(self):
        """Show a popup for creating, editing, and running search suites."""
        import tkinter as tk
        from peekdocs.collection import (
            load_collection, add_suite, remove_suite, rename_suite,
            update_suite_searches, get_search_params,
        )

        folder = self.folder_entry.get().strip()
        if not folder or not os.path.isdir(folder):
            self._show_error("Please select a Search Folder first.")
            return

        win, _dark = self._themed_toplevel()
        win.withdraw()  # invisible during widget setup; repositioned + shown at end
        self._suite_popup = win
        win.protocol("WM_DELETE_WINDOW", lambda: (setattr(self, "_suite_popup", None), win.destroy()))
        win.title("Search Suites")
        win.resizable(True, True)
        # Width reduced 20% from 720 → 576 per UX request; height unchanged.
        win.geometry("576x640")

        _sf = self._scaled_font

        # ── Header ──
        header = tk.Frame(win)
        header.pack(fill="x", padx=12, pady=(10, 5))
        tk.Label(header, text="Search Suites", font=_sf(14, "bold")).pack(side="left")
        ctk.CTkButton(
            header, text="?", width=30, height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#1565C0", text_color="white",
            hover_color="#0D47A1",
            corner_radius=15,
            command=lambda: self._show_search_suites_help(win),
        ).pack(side="right")
        # Top text — one sentence per row so the narrower popup reads
        # cleanly without mid-sentence wrapping.
        _top_lines = (
            "Group saved searches and run them together.\n"
            "Results go into a single combined report.\n"
            "Suites are saved in the Search Folder shown below.\n"
            "The Search Folder is controlled by the search folder on the main page (Step 1)."
        )
        tk.Label(
            win,
            text=_top_lines,
            font=_sf(10), fg="gray", justify="left", anchor="w",
        ).pack(fill="x", padx=12, pady=(0, 2))

        tk.Label(
            win,
            text=f"Search Folder: {folder}",
            font=_sf(10), fg="#66BBFF" if ctk.get_appearance_mode() == "Dark" else "blue",
        ).pack(anchor="w", padx=12, pady=(0, 3))

        # ── Main area: left (suite list) + right (suite contents) ──
        body = tk.Frame(win)
        body.pack(fill="both", expand=True, padx=12, pady=5)

        # Left panel — suite list
        left = tk.Frame(body, width=250)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        tk.Label(left, text="Suites:", font=_sf(11, "bold")).pack(anchor="w")
        suite_listbox = tk.Listbox(left, font=_sf(11), exportselection=False)
        suite_listbox.pack(fill="both", expand=True, pady=(4, 4))

        left_btns = tk.Frame(left)
        left_btns.pack(fill="x")

        # Right panel — suite contents
        right = tk.Frame(body)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="Searches in this suite (run in order, top to bottom):", font=_sf(10)).pack(anchor="w", pady=(0, 2))
        search_listbox = tk.Listbox(right, font=_sf(11), exportselection=False)
        search_listbox.pack(fill="both", expand=True, pady=(0, 4))

        right_btns = tk.Frame(right)
        right_btns.pack(fill="x")

        # ── State ──
        current_suite = [None]  # mutable reference

        def _refresh_suite_list():
            suite_listbox.delete(0, "end")
            data = load_collection(folder)
            for name in sorted(data["suites"].keys()):
                suite_listbox.insert("end", name)

        def _refresh_search_list():
            search_listbox.delete(0, "end")
            if current_suite[0] is None:
                return
            data = load_collection(folder)
            searches = data["suites"].get(current_suite[0], [])
            for s in searches:
                search_listbox.insert("end", s)

        def _on_suite_select(event=None):
            sel = suite_listbox.curselection()
            if not sel:
                return
            name = suite_listbox.get(sel[0])
            current_suite[0] = name
            _refresh_search_list()

        suite_listbox.bind("<<ListboxSelect>>", _on_suite_select)

        # ── Left panel buttons ──
        def _new_suite():
            from peekdocs.gui._helpers import themed_ask_string
            name = themed_ask_string(win, "New Suite", "Suite name:")
            if not name or not name.strip():
                return
            name = name.strip()
            data = load_collection(folder)
            if name in data["suites"]:
                self._show_error(f"Suite '{name}' already exists.")
                return
            add_suite(folder, name)
            _refresh_suite_list()
            # Select the new suite
            items = suite_listbox.get(0, "end")
            for i, item in enumerate(items):
                if item == name:
                    suite_listbox.selection_set(i)
                    _on_suite_select()
                    break

        def _rename_suite_btn():
            if current_suite[0] is None:
                return
            from peekdocs.gui._helpers import themed_ask_string
            new_name = themed_ask_string(
                win, "Rename Suite", f"New name for '{current_suite[0]}':",
                initial=current_suite[0],
            )
            if not new_name or not new_name.strip() or new_name.strip() == current_suite[0]:
                return
            new_name = new_name.strip()
            if not rename_suite(folder, current_suite[0], new_name):
                self._show_error(f"Suite '{new_name}' already exists.")
                return
            current_suite[0] = new_name
            _refresh_suite_list()
            items = suite_listbox.get(0, "end")
            for i, item in enumerate(items):
                if item == new_name:
                    suite_listbox.selection_set(i)
                    break

        def _delete_suite():
            if current_suite[0] is None:
                return
            from tkinter import messagebox
            if not messagebox.askyesno("Delete Suite", f"Delete suite '{current_suite[0]}'?", parent=win):
                return
            remove_suite(folder, current_suite[0])
            current_suite[0] = None
            search_listbox.delete(0, "end")
            _refresh_suite_list()

        _btn_new = ctk.CTkButton(left_btns, text="New", width=60, font=ctk.CTkFont(size=12), command=_new_suite)
        _btn_new.pack(side="left", padx=2)
        Tooltip(_btn_new, "Create a new named suite")
        _btn_rename = ctk.CTkButton(left_btns, text="Rename", width=70, font=ctk.CTkFont(size=12), command=_rename_suite_btn)
        _btn_rename.pack(side="left", padx=2)
        Tooltip(_btn_rename, "Rename the selected suite")
        _btn_delete = ctk.CTkButton(left_btns, text="Delete", width=60, font=ctk.CTkFont(size=12),
                       fg_color="#CC3333", hover_color="#AA2222", command=_delete_suite)
        _btn_delete.pack(side="left", padx=2)
        Tooltip(_btn_delete, "Delete the selected suite (does not delete the saved searches)")

        # ── Right panel buttons ──
        def _add_search():
            if current_suite[0] is None:
                self._show_error("Select or create a suite first.")
                return
            data = load_collection(folder)
            available = sorted(data["saved_searches"].keys())
            already_in = list(data["suites"].get(current_suite[0], []))
            remaining = [s for s in available if s not in already_in]
            if not remaining:
                if not available:
                    # Case 1: no saved searches exist in this folder at all
                    self._show_error(
                        "No saved searches yet.\n\n"
                        "Save a search first (main screen → Save button), then come "
                        "back to add it to this suite."
                    )
                else:
                    # Case 2: saved searches exist but every one is already in this suite
                    self._show_error(
                        "Every saved search in this folder is already in this suite.\n\n"
                        "Save another search first (main screen → Save button) before "
                        "adding it here."
                    )
                return

            # Popup to pick a search.
            #
            # X11/Linux gotcha: grab_set() raises TclError("grab failed:
            # window not viewable") if called before the WM has mapped the
            # toplevel. macOS Aqua maps Toplevels synchronously so this
            # never fires there. We have to (a) finish positioning, (b)
            # wait for the window to become visible, and (c) treat the
            # grab as best-effort. If we let the grab_set exception
            # propagate, the whole function aborts and the user sees an
            # empty half-built popup.
            pick_win, _ = self._themed_toplevel(win)
            pick_win.title("Add Search to Suite")
            pick_win.geometry("350x400")
            pick_win.transient(win)
            self.update_idletasks()
            px = win.winfo_rootx() + (win.winfo_width() - 350) // 2
            py = win.winfo_rooty() + (win.winfo_height() - 400) // 2
            pick_win.geometry(f"+{px}+{py}")
            pick_win.update_idletasks()
            try:
                pick_win.wait_visibility()
            except tk.TclError:
                pass  # window already destroyed (unlikely here)
            try:
                pick_win.grab_set()
            except tk.TclError:
                pass  # X11 race; transient + lift below keeps it modal-ish

            tk.Label(pick_win, text="Select a saved search:", font=_sf(11, "bold")).pack(anchor="w", padx=10, pady=(10, 4))

            def _do_add():
                sel = pick_lb.curselection()
                if not sel:
                    return
                chosen = pick_lb.get(sel[0])
                data2 = load_collection(folder)
                searches = data2["suites"].get(current_suite[0], [])
                searches.append(chosen)
                update_suite_searches(folder, current_suite[0], searches)
                pick_win.destroy()
                _refresh_search_list()

            # Pack buttons BEFORE the listbox so their rows are reserved
            # at the bottom; otherwise the listbox's expand=True grows to
            # fill the toplevel and pushes the buttons off the visible area.
            # tk packs side='bottom' from the bottom up, so Close (packed
            # first) ends up on the absolute-bottom row and Add (packed
            # second) sits just above it on its own row.
            ctk.CTkButton(pick_win, text="Close", width=80,
                          fg_color="transparent", text_color=("gray30", "gray70"),
                          hover_color=("gray90", "gray25"),
                          font=ctk.CTkFont(size=12),
                          command=pick_win.destroy).pack(side="bottom", pady=(0, 10))
            ctk.CTkButton(pick_win, text="Add", width=80, font=ctk.CTkFont(size=12),
                          command=_do_add).pack(side="bottom", pady=(8, 4))

            pick_lb = tk.Listbox(pick_win, font=_sf(11), exportselection=False)
            # Populate BEFORE packing so items are in the data model when
            # the widget is first laid out — belt-and-suspenders against
            # any remaining race between insert() and X11 expose events.
            for s in remaining:
                pick_lb.insert("end", s)
            pick_lb.pack(fill="both", expand=True, padx=10, pady=(0, 5))
            self._apply_dark_theme(pick_win)
            # Linux/X11: transient+grab_set doesn't always raise children
            # above the parent. Explicitly lift and focus so the picker
            # ends up visible and keystroke-accepting on first open.
            pick_win.lift()
            pick_win.focus_force()

        def _remove_search():
            if current_suite[0] is None:
                return
            sel = search_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            data = load_collection(folder)
            searches = data["suites"].get(current_suite[0], [])
            if idx < len(searches):
                searches.pop(idx)
                update_suite_searches(folder, current_suite[0], searches)
                _refresh_search_list()

        def _move_up():
            if current_suite[0] is None:
                return
            sel = search_listbox.curselection()
            if not sel or sel[0] == 0:
                return
            idx = sel[0]
            data = load_collection(folder)
            searches = data["suites"].get(current_suite[0], [])
            searches[idx - 1], searches[idx] = searches[idx], searches[idx - 1]
            update_suite_searches(folder, current_suite[0], searches)
            _refresh_search_list()
            search_listbox.selection_set(idx - 1)

        def _move_down():
            if current_suite[0] is None:
                return
            sel = search_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            data = load_collection(folder)
            searches = data["suites"].get(current_suite[0], [])
            if idx >= len(searches) - 1:
                return
            searches[idx], searches[idx + 1] = searches[idx + 1], searches[idx]
            update_suite_searches(folder, current_suite[0], searches)
            _refresh_search_list()
            search_listbox.selection_set(idx + 1)

        _btn_add = ctk.CTkButton(right_btns, text="Add Search", width=90, font=ctk.CTkFont(size=12), command=_add_search)
        _btn_add.pack(side="left", padx=2)
        Tooltip(_btn_add, "Add a saved search to this suite — save searches first from the main screen")
        _btn_remove = ctk.CTkButton(right_btns, text="Remove", width=70, font=ctk.CTkFont(size=12), command=_remove_search)
        _btn_remove.pack(side="left", padx=2)
        Tooltip(_btn_remove, "Remove the selected search from this suite")
        _btn_up = ctk.CTkButton(right_btns, text="\u25b2 Up", width=60, font=ctk.CTkFont(size=12), command=_move_up)
        _btn_up.pack(side="left", padx=2)
        Tooltip(_btn_up, "Move the selected search up in the run order")
        _btn_down = ctk.CTkButton(right_btns, text="\u25bc Down", width=70, font=ctk.CTkFont(size=12), command=_move_down)
        _btn_down.pack(side="left", padx=2)
        Tooltip(_btn_down, "Move the selected search down in the run order")

        # ── Output formats ──
        output_frame = tk.Frame(win)
        output_frame.pack(fill="x", padx=12, pady=(8, 2))
        tk.Label(output_frame, text="Suite report formats:", font=_sf(11, "bold")).pack(side="left", padx=(0, 8))

        # TXT is always generated; DOCX is opt-in via the checkbox
        # below (matches the 1.2.6 / 1.2.26 policy across Standard,
        # Suite, and Regex Search).
        tk.Label(output_frame, text="TXT \u2713", font=_sf(10), fg="gray").pack(side="left", padx=(0, 10))

        # Seed each checkbox from ~/.peekdocsrc so the user's last selection
        # persists across popup invocations. Saved on every toggle.
        try:
            from peekdocs.cli import _load_config as _load_cfg_suite
            _suite_cfg = _load_cfg_suite()
        except Exception:
            _suite_cfg = {}
        # DOCX is opt-in as of this release — matches the 1.2.6 Standard
        # Search policy and the recent Regex Search opt-in conversion.
        # Default OFF; persists across sessions via the same suite_*
        # config keys as the other formats. TXT remains always-on.
        _suite_docx_var = tk.BooleanVar(value=bool(_suite_cfg.get("suite_docx", False)))
        _suite_html_var = tk.BooleanVar(value=bool(_suite_cfg.get("suite_html", False)))
        _suite_csv_var = tk.BooleanVar(value=bool(_suite_cfg.get("suite_csv", False)))
        _suite_json_var = tk.BooleanVar(value=bool(_suite_cfg.get("suite_json", False)))
        _suite_pdf_var = tk.BooleanVar(value=bool(_suite_cfg.get("suite_pdf", False)))

        def _save_suite_fmt(key, var):
            self._save_ui_preference(key, bool(var.get()))

        tk.Checkbutton(output_frame, text="DOCX", variable=_suite_docx_var, font=_sf(10),
                       command=lambda: _save_suite_fmt("suite_docx", _suite_docx_var)).pack(side="left", padx=(0, 5))
        tk.Checkbutton(output_frame, text="HTML", variable=_suite_html_var, font=_sf(10),
                       command=lambda: _save_suite_fmt("suite_html", _suite_html_var)).pack(side="left", padx=(0, 5))
        tk.Checkbutton(output_frame, text="CSV", variable=_suite_csv_var, font=_sf(10),
                       command=lambda: _save_suite_fmt("suite_csv", _suite_csv_var)).pack(side="left", padx=(0, 5))
        tk.Checkbutton(output_frame, text="JSON", variable=_suite_json_var, font=_sf(10),
                       command=lambda: _save_suite_fmt("suite_json", _suite_json_var)).pack(side="left", padx=(0, 5))
        tk.Checkbutton(output_frame, text="PDF", variable=_suite_pdf_var, font=_sf(10),
                       command=lambda: _save_suite_fmt("suite_pdf", _suite_pdf_var)).pack(side="left", padx=(0, 5))

        # ── Bottom: Run Search Suite + Close ──
        bottom = tk.Frame(win)
        bottom.pack(pady=(8, 2))

        def _run_suite():
            if current_suite[0] is None:
                self._show_error("Select a suite first.")
                return
            data = load_collection(folder)
            searches = data["suites"].get(current_suite[0], [])
            if not searches:
                self._show_error("This suite has no searches. Add some first.")
                return
            # Validate all searches exist
            missing = [s for s in searches if s not in data["saved_searches"]]
            if missing:
                self._show_error(f"Missing saved search(es): {', '.join(missing)}\n\nRemove them from the suite or re-create them.")
                return
            suite_name = current_suite[0]
            suite_formats = {
                "docx": _suite_docx_var.get(),
                "html": _suite_html_var.get(),
                "csv": _suite_csv_var.get(),
                "json": _suite_json_var.get(),
                "pdf": _suite_pdf_var.get(),
            }
            win.destroy()
            self._run_suite_searches(suite_name, searches, folder, suite_formats=suite_formats)

        _btn_run = ctk.CTkButton(
            bottom, text="Run Search Suite", width=160,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#76BA1B", hover_color="#5E9516", text_color="white",
            command=_run_suite,
        )
        _btn_run.pack()
        Tooltip(_btn_run, "Run all searches in this suite — results are combined into a single highlighted report")

        def _run_multiple_suites():
            """Pick two or more saved suites and run all their searches
            together. The combined run reuses the existing suite-run
            pipeline (_run_suite_searches) so the report formatting,
            cancel button, status updates, and Open Report buttons all
            behave identically to a single-suite run — there's just
            more sections in the combined report. Search names that
            appear in multiple picked suites run only once (dedup by
            saved-search name); the display label in the combined
            report records every source suite.
            """
            _data_mc = load_collection(folder)
            _suites_mc = _data_mc.get("suites", {}) or {}
            if not _suites_mc:
                self._show_error(
                    "No saved suites found.\n\n"
                    "Use Create New (above) to make a suite, then add "
                    "saved searches to it."
                )
                return

            ms_win, _ = self._themed_toplevel(win)
            ms_win.title("Run Multiple Search Suites")
            ms_win.geometry("440x460")
            ms_win.transient(win)
            self.update_idletasks()
            _msx = win.winfo_rootx() + (win.winfo_width() - 440) // 2
            # Anchor the picker's bottom to the parent popup's bottom so
            # it overlays the Run Search Suite button below — keeps the
            # user from misclicking the parent's Run while the picker is
            # open, and visually confirms "this is the active picker now."
            _msy = win.winfo_rooty() + win.winfo_height() - 460
            ms_win.geometry(f"+{_msx}+{_msy}")
            ms_win.update_idletasks()
            try:
                ms_win.wait_visibility()
            except tk.TclError:
                pass
            try:
                ms_win.grab_set()
            except tk.TclError:
                pass

            tk.Label(
                ms_win,
                text="Select two or more suites to run together. The "
                     "saved searches from each are combined into one "
                     "run (output formats are taken from the Suites "
                     "popup). Searches present in more than one suite "
                     "run only once.",
                font=("TkDefaultFont", 11),
                wraplength=410, justify="left", anchor="w",
            ).pack(fill="x", padx=15, pady=(12, 8))

            # Scrollable list — long suite lists shouldn't push the
            # Run / Cancel buttons off the bottom of the popup.
            _list_frame = tk.Frame(ms_win)
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

            _ms_check_vars = {}
            for _sname in sorted(_suites_mc.keys()):
                _v = tk.BooleanVar(value=False)
                _ms_check_vars[_sname] = _v
                _n = len(_suites_mc[_sname])
                tk.Checkbutton(
                    _list_inner, variable=_v,
                    text=f"{_sname}  ({_n} search{'es' if _n != 1 else ''})",
                    font=("TkDefaultFont", 11), anchor="w",
                ).pack(fill="x", anchor="w", padx=4, pady=1)

            def _do_run_multi_suites():
                _picked = [n for n, v in _ms_check_vars.items() if v.get()]
                if len(_picked) < 2:
                    self._show_error(
                        "Select at least two suites.\n\n"
                        "To run a single suite, pick it in the list "
                        "above and click Run Search Suite."
                    )
                    return
                # Combine search names, deduping. Order: walk suites
                # in pick order; within each suite walk searches in
                # their saved order. Skip names we've already added.
                _combined = []
                _seen = set()
                _per_suite = {}
                for _sname in _picked:
                    _per_suite[_sname] = []
                    for _search in _suites_mc.get(_sname, []):
                        _per_suite[_sname].append(_search)
                        if _search not in _seen:
                            _seen.add(_search)
                            _combined.append(_search)
                # Validate every search exists as a saved search.
                _saved = _data_mc.get("saved_searches", {}) or {}
                _missing = [s for s in _combined if s not in _saved]
                if _missing:
                    self._show_error(
                        "Missing saved search(es): "
                        + ", ".join(_missing)
                        + "\n\nOpen each affected suite and remove "
                        "the missing search, or re-create the saved "
                        "search."
                    )
                    return
                if not _combined:
                    self._show_error(
                        "The selected suites have no searches.\n\n"
                        "Add saved searches to them first."
                    )
                    return
                _formats = {
                    "docx": _suite_docx_var.get(),
                    "html": _suite_html_var.get(),
                    "csv": _suite_csv_var.get(),
                    "json": _suite_json_var.get(),
                    "pdf": _suite_pdf_var.get(),
                }
                # Friendly suite-name label for the status line and
                # the combined report header. Listing every suite gets
                # unwieldy past three.
                if len(_picked) <= 3:
                    _label = " + ".join(_picked)
                else:
                    _label = f"{len(_picked)} suites"
                ms_win.destroy()
                win.destroy()
                self._run_suite_searches(
                    _label, _combined, folder, suite_formats=_formats,
                    show_completion_popup=True,
                )

            _ms_btns = tk.Frame(ms_win)
            _ms_btns.pack(pady=(0, 12))
            ctk.CTkButton(
                _ms_btns, text="Run Selected", width=130,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#76BA1B", hover_color="#5E9516", text_color="white",
                command=_do_run_multi_suites,
            ).pack(side="left", padx=5)
            ctk.CTkButton(
                _ms_btns, text="Cancel", width=90,
                font=ctk.CTkFont(size=12),
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=ms_win.destroy,
            ).pack(side="left", padx=5)

            self._apply_dark_theme(ms_win)

        # Run Multiple Search Suites button — own row, just above Close.
        # Mirrors the Regex Search popup's Run Multiple Collections
        # placement so users find the same pattern in both surfaces.
        _multi_suite_frame = tk.Frame(win)
        _multi_suite_frame.pack(pady=(4, 0))
        _multi_suite_btn = ctk.CTkButton(
            _multi_suite_frame, text="Run Multiple Search Suites…",
            width=220, font=ctk.CTkFont(size=11),
            fg_color="#76BA1B", hover_color="#5E9516", text_color="white",
            command=_run_multiple_suites,
        )
        _multi_suite_btn.pack()
        Tooltip(
            _multi_suite_btn,
            "Pick two or more saved suites and run all their searches "
            "together. Output formats and search folder are taken from "
            "this popup. Searches that appear in more than one of the "
            "picked suites run only once.",
        )

        close_frame = tk.Frame(win)
        close_frame.pack(pady=(0, 10))
        ctk.CTkButton(
            close_frame, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            font=ctk.CTkFont(size=12), command=win.destroy,
        ).pack()

        _refresh_suite_list()
        self._apply_dark_theme(win)

        # Center on the main window and show. Withdraw + final geometry +
        # deiconify avoids the visible flicker of the popup briefly opening
        # on the system primary monitor before jumping to the main window's
        # monitor in multi-monitor setups.
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 720) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 640) // 2
        win.geometry(f"720x640+{x}+{y}")
        win.deiconify()

    def _run_suite_searches(self, suite_name, search_names, folder, suite_formats=None, show_completion_popup=False):
        """Execute all searches in a suite sequentially using subprocess.

        ``show_completion_popup`` is set by the Run Multiple Search Suites
        path so the user gets a clearly-labeled "reports written" popup
        with Open TXT / Open DOCX / Open Folder buttons at the end of the
        run. Single-suite runs leave it False — they rely on the existing
        main-page report-button row, which is unambiguous for that flow
        because there's only one search type involved.
        """
        import threading
        import subprocess as _sp
        from peekdocs.collection import get_search_params
        from peekdocs.gui._helpers import _build_command_from_values
        from peekdocs.reporter import write_suite_txt_report, write_suite_docx_report, write_suite_html_report

        # Cloud-output guard runs on the main thread BEFORE the worker
        # thread is spawned. Tkinter modals from worker threads hang on
        # wait_window() — GUI state can only be modified from the main
        # thread. So we resolve the write target here and pass it into
        # the closure for _run to use unchanged.
        from peekdocs.gui._helpers import gui_cloud_guard
        from peekdocs.cli import _load_config as _load_cfg_guard
        _redirect_pref = bool(_load_cfg_guard().get("redirect_cloud_output", False))
        _resolved_output_folder, _cloud_decision = gui_cloud_guard(
            self, folder, redirect_to_safe=_redirect_pref,
        )
        if _resolved_output_folder is None:
            # User picked Cancel — abort before any UI state changes.
            self.status_label.configure(
                text_color=("red", "#FF6666"),
                text="Search cancelled — output folder is cloud-synced.",
            )
            return

        # Clear stale state from any previous standard search before
        # showing the suite's own progress. Without this, the Results
        # Preview pane keeps the previous standard search's matches
        # while the suite runs — directly contradicting the suite-
        # progress text on the status line ("Suite: X (Y searches)...").
        # Mirrors the start_search() reset block in _mixin_search.py.
        # Note: _hide_preview() clears the Text widget but intentionally
        # leaves _preview_count_label alone. The count label is what
        # renders "N match(es) in M file(s)" above the preview; without
        # an explicit reset, the previous standard search's count
        # survives into the suite run and re-contradicts the
        # suite-progress status.
        self.matched_files = []
        self._inverse_results = False
        self._clear_action_buttons()
        self._hide_files_list()
        self._hide_preview()
        # _preview_count_label removed — counts moved to the headline.
        self._matched_files_link.pack_forget()
        self._excluded_files_btn.pack_forget()

        # Show progress bar and start elapsed timer — same as regular search
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        self.progress_bar.grid(
            row=5, column=0, columnspan=3, padx=10, pady=(2, 2), sticky="ew"
        )
        self.search_start_time = time.time()
        # Captured separately for _show_action_buttons' mtime-vs-cutoff
        # check (see _mixin_search.py _show_action_buttons docstring).
        self._last_search_start_time = self.search_start_time
        self._suite_elapsed_active = True
        self._suite_cancelled = False
        # Repurpose the GREEN suites button as Cancel during the run. The
        # standard search button stays alone — flipping it would suggest
        # the standard search is the thing running, which it isn't.
        self._suites_btn.configure(text="Cancel", fg_color="#D32F2F", hover_color="#B71C1C",
                                   command=self._cancel_suite)
        self.status_label.configure(text_color=("blue", "#66BBFF"),
            text=f"Suite: {suite_name} ({len(search_names)} searches)...")
        self._update_suite_elapsed(suite_name)

        def _run():
            sections = []
            for i, search_name in enumerate(search_names, 1):
                if getattr(self, "_suite_cancelled", False):
                    return
                _total = len(search_names)
                self.after(0, lambda i=i, n=search_name, t=_total: self.status_label.configure(
                    text_color=("blue", "#66BBFF"),
                    text=f"Search [{i}/{t}] {n}..."
                ))
                params = get_search_params(folder, search_name)
                if params is None:
                    continue

                # Build CLI command from saved params
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
                    proximity=str(params.get("proximity", "")) if params.get("proximity") else "",
                    context_before=str(params.get("context_before", "")) if params.get("context_before") else "",
                    context_after=str(params.get("context_after", "")) if params.get("context_after") else "",
                    cores=str(params.get("cores", "")) if params.get("cores") else "",
                    specific_files=params.get("specific_files", ""),
                    index_search=params.get("index_search", False),
                    inverse=params.get("inverse", False),
                    expression=params.get("expression", False),
                    whole_word=params.get("whole_word", False),
                    max_matches=str(params.get("max_matches", "")) if params.get("max_matches") else "",
                    max_file_size_mb=str(params.get("max_file_size_mb", "")) if params.get("max_file_size_mb") else "",
                    range_filters=params.get("range_filters", ""),
                )
                if cmd is None or cmd == "FLAGS_IN_SEARCH":
                    continue

                # Run via subprocess or in-process (see
                # peekdocs.gui._helpers._run_peekdocs_cli for why both
                # paths exist — short version: PyInstaller-bundled
                # standalone exes can't relaunch themselves as CLI).
                import time
                start = time.time()
                try:
                    from peekdocs.gui._helpers import _run_peekdocs_cli
                    stdout, stderr, _rc = _run_peekdocs_cli(cmd, folder)
                except Exception:
                    continue
                elapsed = time.time() - start

                # Parse results from the generated txt report
                import re as _re
                matches = []
                all_files = []
                txt_result = os.path.join(folder, "peekdocs_standard_results.txt")
                if os.path.exists(txt_result):
                    try:
                        with open(txt_result, "r", encoding="utf-8") as f:
                            content = f.read()
                        # Extract file list from "Files searched" section of txt report
                        files_searched_match = _re.search(r"Files searched ==> (\d+)", content)
                        file_count = int(files_searched_match.group(1)) if files_searched_match else 0

                        # Parse matches from txt report — split on Document: boundaries
                        for m in _re.finditer(
                            r'Document: (.+?) \(\d+ match(?:es)?\), Line: (\d+), Match:\n\((.+?)\)\n"(.*?)"(?=\n\nDocument:|\n\n\Z|\Z)',
                            content, _re.DOTALL
                        ):
                            filename, line_num, file_dir, text = m.groups()
                            matches.append((file_dir, filename, int(line_num), text.strip()))
                    except Exception:
                        pass

                terms_str = params.get("search_text", "")
                # Three modes to distinguish for the display-terms build
                # that feeds the section-render + Matched Files highlighter.
                # Expression mode stores a boolean flag in params; the
                # search_text IS the expression string. Regex/wildcard are
                # single tokens (shlex would eat backslashes — same bug
                # class that broke highlighting in the earlier r"print\("
                # incident). Plain text goes through shlex for quoted
                # phrases.
                if params.get("expression"):
                    search_terms = []
                    expr = terms_str or None
                elif params.get("regex") or params.get("wildcard"):
                    search_terms = [terms_str] if terms_str else []
                    expr = None
                else:
                    import shlex as _shlex
                    try:
                        search_terms = _shlex.split(terms_str) if terms_str else []
                    except ValueError:
                        search_terms = terms_str.split() if terms_str else []
                    expr = None
                mode = "ALL" if params.get("and_mode") else "ANY"
                display_terms = search_terms if not expr else [expr]

                # Parse match count and matched file count from stdout (same numbers regular search displays)
                clean_stdout = _re.sub(r"\033\[[0-9;]*m", "", stdout)  # strip ANSI codes
                found_match_m = _re.search(r"Found\s+(\d+)\s+match", clean_stdout)
                total_match_count = int(found_match_m.group(1)) if found_match_m else len(matches)
                matched_file_count_m = _re.search(r"match\(es\)\s+in\s+(\d+)\s+file\(s\)", clean_stdout)
                matched_file_count = int(matched_file_count_m.group(1)) if matched_file_count_m else 0

                # Parse matched files using the same parser as regular search
                from peekdocs.gui._helpers import _parse_matched_files
                parsed_files = _parse_matched_files(folder, "peekdocs_standard_results.txt")

                sections.append({
                    "search_name": search_name,
                    "search_terms": display_terms,
                    "matches": matches,
                    "total_match_count": total_match_count,
                    "all_files": [f"{search_name}_{j}" for j in range(file_count)],
                    "matched_file_count": matched_file_count,
                    "parsed_files": parsed_files,
                    "elapsed": elapsed,
                    "report_mode": mode,
                    "params": params,
                    "stdout": stdout,
                })

            # Per-search loop done. Switch the status from
            # 'Search [N/N] ...' to 'Writing reports...' before the
            # combined-report block runs, so the user has feedback
            # during what can be a multi-second gap on big suites
            # (especially with HTML / CSV / JSON / PDF formats all
            # enabled). The elapsed-time updater appends '(Ns)' on
            # the next tick, matching the format of the per-search
            # progress line just before this.
            self.after(0, lambda: self.status_label.configure(
                text_color=("blue", "#66BBFF"),
                text="Writing reports...",
            ))

            # Cloud-output guard was resolved on the main thread before
            # this worker was spawned — output_folder is the resolved
            # write target (may be a redirected safe dir if the user's
            # search folder was cloud-synced).
            output_folder = _resolved_output_folder

            # Generate combined suite reports
            # Set restrictive file permissions if enabled
            import peekdocs.reporter as _reporter_mod
            _reporter_mod.restrict_permissions = (
                getattr(self, "restrict_permissions_var", None)
                and self.restrict_permissions_var.get() == "on"
            )

            txt_path = os.path.join(output_folder, "peekdocs_suite_results.txt")
            docx_path = ""
            _fmts = suite_formats or {}
            # Threshold parity with Regex Search: skip in-memory-build
            # formats (DOCX, PDF) above 25K matches. python-docx and
            # fpdf2 both load the full document into RAM before saving;
            # for huge suite runs this could otherwise freeze the GUI.
            _SUITE_DOCX_MATCH_THRESHOLD = 25_000
            _suite_total_matches = sum(
                s.get("total_match_count", len(s["matches"])) for s in sections
            )
            write_suite_txt_report(txt_path, suite_name, sections)
            if _fmts.get("docx", False):
                if _suite_total_matches > _SUITE_DOCX_MATCH_THRESHOLD:
                    _ts_msg = (
                        f"{_suite_total_matches:,} matches is too many for a "
                        f"Word report (threshold: "
                        f"{_SUITE_DOCX_MATCH_THRESHOLD:,}). The TXT report "
                        f"has every match — open it with any text editor.\n\n"
                        f"To get a DOCX too, narrow the suite (fewer "
                        f"searches or more specific terms) so the total "
                        f"stays under {_SUITE_DOCX_MATCH_THRESHOLD:,}."
                    )
                    self.after(0, lambda m=_ts_msg: self._show_error(m))
                else:
                    docx_path = os.path.join(output_folder, "peekdocs_suite_results.docx")
                    write_suite_docx_report(docx_path, txt_path, sections)
            html_path = ""
            csv_path = ""
            json_path = ""
            if _fmts.get("html", False):
                html_path = os.path.join(output_folder, "peekdocs_suite_results.html")
                try:
                    write_suite_html_report(html_path, suite_name, sections)
                except Exception:
                    html_path = ""
            if _fmts.get("csv", False):
                csv_path = os.path.join(output_folder, "peekdocs_suite_results.csv")
                try:
                    import csv as _csv_s
                    all_matches = []
                    for s in sections:
                        for fd, fn, ln, text in s["matches"]:
                            all_matches.append((fn, fd, ln, text, s["search_name"]))
                    # utf-8-sig writes a UTF-8 BOM so legacy Excel on
                    # Windows reads accented characters correctly. No
                    # effect on LibreOffice, Excel 365, or text tooling.
                    with open(csv_path, "w", newline="", encoding="utf-8-sig") as cf:
                        writer = _csv_s.writer(cf)
                        writer.writerow(["search_name", "filename", "folder", "line_number", "matched_text"])
                        for fn, fd, ln, text, sn in all_matches:
                            writer.writerow([sn, fn, fd, ln, text])
                    from peekdocs.reporter import _restrict_file_permissions
                    _restrict_file_permissions(csv_path)
                except Exception:
                    csv_path = ""
            if _fmts.get("json", False):
                json_path = os.path.join(output_folder, "peekdocs_suite_results.json")
                try:
                    import json as _json_s
                    from peekdocs.cli import VERSION as _ver_sj
                    json_data = {
                        "generator": f"peekdocs v{_ver_sj}",
                        "suite_name": suite_name,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "searches": len(sections),
                        "total_matches": sum(s.get("total_match_count", len(s["matches"])) for s in sections),
                        "sections": [
                            {
                                "search_name": s["search_name"],
                                "terms": s["search_terms"],
                                "mode": s["report_mode"],
                                "match_count": s.get("total_match_count", len(s["matches"])),
                                "matched_file_count": s.get("matched_file_count", 0),
                                "elapsed": round(s["elapsed"], 2),
                                "matches": [
                                    {"filename": fn, "folder": fd, "line": ln, "text": text}
                                    for fd, fn, ln, text in s["matches"]
                                ],
                            }
                            for s in sections
                        ],
                    }
                    with open(json_path, "w", encoding="utf-8") as jf:
                        _json_s.dump(json_data, jf, indent=2, ensure_ascii=False)
                    from peekdocs.reporter import _restrict_file_permissions
                    _restrict_file_permissions(json_path)
                except Exception:
                    json_path = ""

            pdf_path = ""
            if _fmts.get("pdf", False):
                if _suite_total_matches > _SUITE_DOCX_MATCH_THRESHOLD:
                    _ts_pdf = (
                        f"{_suite_total_matches:,} matches is too many for a "
                        f"PDF report (threshold: "
                        f"{_SUITE_DOCX_MATCH_THRESHOLD:,}). The TXT report "
                        f"has every match.\n\nTo get a PDF too, narrow the "
                        f"suite so the total stays under "
                        f"{_SUITE_DOCX_MATCH_THRESHOLD:,}."
                    )
                    self.after(0, lambda m=_ts_pdf: self._show_error(m))
                else:
                    pdf_path = os.path.join(output_folder, "peekdocs_suite_results.pdf")
                    try:
                        from peekdocs.reporter import write_pdf_report
                        # Flatten matches across all suite sections — every match
                        # gets a row in the PDF, with the suite name as the search
                        # context. (Per-section delimiters are a polish item.)
                        flat_matches = []
                        flat_terms = []
                        for s in sections:
                            for fd, fn, ln, text in s["matches"]:
                                flat_matches.append((fd, fn, ln, text))
                            for t in s.get("search_terms", []):
                                if t not in flat_terms:
                                    flat_terms.append(t)
                        write_pdf_report(
                            pdf_path, flat_matches,
                            search_terms=flat_terms or [suite_name],
                            report_mode="ANY",
                        )
                    except Exception:
                        pdf_path = ""

            total_matches = sum(s.get("total_match_count", len(s["matches"])) for s in sections)
            total_elapsed = time.time() - self.search_start_time
            extra_paths = {"html": html_path, "csv": csv_path, "json": json_path, "pdf": pdf_path}
            self.after(0, lambda: self._suite_finished(suite_name, sections, total_matches, txt_path, docx_path, total_elapsed, folder, html_path, extra_paths, show_completion_popup=show_completion_popup))

        threading.Thread(target=_run, daemon=True).start()

    def _suite_finished(self, suite_name, sections, total_matches, txt_path, docx_path, total_elapsed=0, folder="", html_path="", extra_paths=None, show_completion_popup=False):
        """Handle suite completion — show results summary and report buttons.

        ``show_completion_popup`` triggers a small modal at the end of
        the run with Open TXT / Open DOCX / Open Folder buttons and the
        resolved report paths — used by Run Multiple Search Suites to
        make it unambiguous that the main-page report buttons now point
        at the just-finished combined suite run (vs leftover from a
        previous standard search).
        """
        self._suite_elapsed_active = False
        self.search_start_time = None
        try:
            self.progress_bar.stop()
        except Exception:
            pass
        self.progress_bar.grid_remove()
        # Restore the SUITES button (the one we flipped to Cancel at run-start).
        # Use _stack_label and re-affirm width/height so the button
        # stays the same 44x44 square shape it started as — without
        # _stack_label the multi-word 'Search Suites' label fits on
        # one line and the button auto-grows rectangular.
        self._suites_btn.configure(
            text=self._stack_label(__import__("peekdocs.i18n", fromlist=["t"]).t("search_suites_label")),
            width=44, height=44,
            fg_color="#76BA1B", hover_color="#76BA1B",
            text_color="white", command=self._show_search_suites,
        )

        import re as _re_fin

        # Unique file count across all sub-searches. The previous formula
        # sum(s["matched_file_count"]) double-counted any file that hit
        # in more than one sub-search (e.g. a file matching both TODO
        # and FIXME counted twice). The green Matched Files button and
        # the popup both show the deduplicated unique count; the status
        # line should too. The total_matches figure stays a sum because
        # match-locations are genuinely independent across sub-searches.
        _unique_filepaths = set()
        for _sec in sections:
            for fp, _, cnt, _ in _sec.get("parsed_files", []):
                if cnt > 0:
                    _unique_filepaths.add(fp)
        total_matched_files_status = len(_unique_filepaths)
        # "Files searched" is the size of the corpus, not a count of
        # search operations. Every sub-search in a suite runs against
        # the same folder, so sum() across sections counted the same
        # files once per sub-search and showed e.g. 2225 (5 × 445) for
        # a 5-sub-search suite over 445 files. max() is the right
        # answer for the typical case (all sub-searches see the same
        # corpus, so max == any one) and gracefully handles suites
        # where one sub-search narrows with -t while another doesn't.
        total_files_searched = max(
            (len(s["all_files"]) for s in sections), default=0
        )

        # Parse error/skip counts from subprocess stdout
        total_errors = 0
        total_size = ""
        for s in sections:
            stdout = s.get("stdout", "")
            err_m = _re_fin.search(r"(\d+)\s+error\(s\)", stdout)
            if err_m:
                total_errors += int(err_m.group(1))
            skip_m = _re_fin.search(r"(\d+)\s+file\(s\)\s+skipped", stdout)
            if skip_m:
                total_errors += int(skip_m.group(1))
            size_m = _re_fin.search(r"Files searched:\s*\d+\s*\(([\d.]+ [KMGT]?B)\)", stdout)
            if size_m and not total_size:
                total_size = size_m.group(1)

        # Build status text matching regular search format
        status = f"Found {total_matches} match(es) in {total_matched_files_status} file(s)"
        status += f" — {total_files_searched} file(s) searched"
        if total_size:
            status += f" ({total_size})"
        status += f" in {total_elapsed:.1f}s"
        if total_errors:
            status += f"  ({total_errors} file(s) skipped — see Error Log)"
        self.status_label.configure(text_color=("blue", "#66BBFF"), text=status)

        # Suggest indexing for large folders
        if total_files_searched >= 100 and folder:
            try:
                from peekdocs.indexer import index_exists
                if not index_exists(folder):
                    current = self.status_label.cget("text")
                    self.status_label.configure(
                        text=current + "  |  Tip: Build an index for faster searches"
                    )
            except Exception:
                pass

        # Build matched files list by aggregating each section's
        # parsed_files (captured in _run_suite_searches before the next
        # sub-search overwrote peekdocs_standard_results.txt). Re-reading
        # the file here would only see the last sub-search's results —
        # and if that was an inverse search, _parse_matched_files would
        # return the "Files WITHOUT matches:" entries with count=0, which
        # is what was showing up when the Matched Files button was
        # clicked after a mixed normal+inverse suite. Filter to count>0
        # so inverse sections don't contribute zero-match files; the
        # status label already only counts non-inverse sub-search hits
        # (matched_file_count is parsed from stdout's "match(es) in N
        # file(s)" line, which an inverse run never prints).
        _seen = {}
        _order = []
        for _sec in sections:
            for fp, fname, cnt, lines in _sec.get("parsed_files", []):
                if cnt <= 0:
                    continue
                if fp in _seen:
                    _seen[fp]["count"] += cnt
                    _seen[fp]["lines"].extend(lines)
                else:
                    _seen[fp] = {"filename": fname, "count": cnt, "lines": list(lines)}
                    _order.append(fp)
        self.matched_files = [
            (fp, _seen[fp]["filename"], _seen[fp]["count"], _seen[fp]["lines"])
            for fp in _order
        ]
        self._inverse_results = False

        # Show matched files button — advertise the de-duplicated unique
        # file count (len(self.matched_files)) rather than the summed
        # total_matched_files_status. The status line above still uses
        # the summed count as a meaningful "this many file-level hits
        # across the whole suite" aggregate, but the BUTTON has to match
        # what the Matched Files popup will actually display when clicked.
        # Using the summed count here was advertising e.g. 177 files
        # while the popup contained 73 unique files (the difference being
        # files that matched in multiple sub-searches, counted once per
        # sub-search by the sum but de-duped in self.matched_files).
        unique_matched_count = len(self.matched_files)
        if unique_matched_count > 0:
            link_text = __import__("peekdocs.i18n", fromlist=["t"]).t("matched_files_format").format(n=unique_matched_count)
            self._matched_files_link.configure(text=link_text, fg_color="#81C784", hover_color="#66BB6A")
            self._matched_files_link.pack(side="left", padx=(5, 0))

        # Excluded Files button — same treatment as standard search (see
        # _mixin_search.py lines 629-641). Suites used to omit this, which
        # made the right-pane button row inconsistent across search types.
        # Every sub-search runs against the same folder/recursive setting,
        # so a single _compute_excluded_files() call is enough.
        try:
            _suite_recursive = self.recursive_var.get() == "on"
            self._excluded_files = self._compute_excluded_files(folder, recursive=_suite_recursive)
        except Exception:
            self._excluded_files = []
        _excl_count = len(self._excluded_files)
        if _excl_count > 0:
            self._excluded_files_btn.configure(
                text=__import__("peekdocs.i18n", fromlist=["t"]).t("excluded_files_format").format(n=_excl_count)
            )
            self._excluded_files_btn.pack(side="left", padx=(5, 0))
        else:
            self._excluded_files_btn.pack_forget()

        # Reuse the existing report-button row (DOCX / TXT / CSV / JSON / PDF /
        # HTML) for suite reports rather than creating a parallel row that
        # overwrites it. Set the mode marker and the timestamp suffix that the
        # standard report row already uses, then let _show_action_buttons()
        # render and color the buttons.
        import re as _re_ts
        self.results_dir = folder
        self._report_file_prefix = "peekdocs_suite_results"
        _ts_match = _re_ts.search(r"_(\d{8}_\d{6})\.", txt_path)
        self._last_ts_suffix = _ts_match.group(1) if _ts_match else ""
        self._show_action_buttons()

        # Show results in preview (right pane of the split — pack, not grid)
        if hasattr(self, "preview_frame"):
            self.preview_frame.pack(fill="both", expand=True, padx=0, pady=0)
        if hasattr(self, "preview_text"):
            # Build a combined highlight regex from every section's terms so
            # matched text in the preview gets the same yellow "match" tag the
            # standard search uses.
            import re as _re_hl
            from peekdocs.scanner import _wildcard_to_regex as _wc2re
            hl_patterns = []
            for section in sections:
                params = section.get("params", {}) or {}
                use_regex = params.get("regex", False)
                use_wildcard = params.get("wildcard", False)
                use_whole_word = params.get("whole_word", False)
                for term in section.get("search_terms", []):
                    if not term:
                        continue
                    if use_wildcard:
                        hl_patterns.append(_wc2re(term))
                    elif use_regex:
                        hl_patterns.append(term)
                    elif use_whole_word:
                        pfx = r"\b" if _re_hl.match(r"\w", term) else ""
                        sfx = r"\b" if _re_hl.search(r"\w$", term) else ""
                        hl_patterns.append(pfx + _re_hl.escape(term) + sfx)
                    else:
                        hl_patterns.append(_re_hl.escape(term))
            hl_re = None
            if hl_patterns:
                try:
                    hl_re = _re_hl.compile("|".join(hl_patterns), _re_hl.IGNORECASE)
                except _re_hl.error:
                    hl_re = None

            # Stash the combined regex so the per-file Matched Files popup
            # can highlight matches when the user clicks a file from a
            # suite run. Without this the popup falls back to the main
            # search bar — which is empty after a suite — and reports
            # "No matches in this file" with no yellow highlights even
            # though the file truly does contain hits for one or more
            # sub-searches. The regex already accounts for each
            # sub-search's regex / wildcard / whole-word flags.
            self._suite_highlight_re = hl_re

            def _insert_hl(text):
                if not hl_re:
                    self.preview_text.insert("end", text)
                    return
                pos = 0
                for m in hl_re.finditer(text):
                    if m.start() > pos:
                        self.preview_text.insert("end", text[pos:m.start()])
                    self.preview_text.insert("end", m.group(), "match")
                    pos = m.end()
                if pos < len(text):
                    self.preview_text.insert("end", text[pos:])

            self.preview_text.configure(state="normal")
            self.preview_text.delete("1.0", "end")
            self.preview_text.insert("end", f"Suite Report: {suite_name}\n", "filename")
            self.preview_text.insert("end", f"Searches: {len(sections)}, Found {total_matches} match(es) in {total_matched_files_status} file(s)\n\n")

            # Up-front section summary so the user sees every search and its
            # match count without having to scroll past the first section.
            if len(sections) > 1:
                self.preview_text.insert("end", "Section summary:\n", "filename")
                name_w = max(len(s["search_name"]) for s in sections)
                for i, s in enumerate(sections, 1):
                    stot = s.get("total_match_count", len(s["matches"]))
                    smfc = s.get("matched_file_count", 0)
                    self.preview_text.insert(
                        "end",
                        f"  {i}. {s['search_name']:<{name_w}}  {stot} match(es) in {smfc} file(s)\n",
                    )
                self.preview_text.insert("end", "\n")

            for section in sections:
                name = section["search_name"]
                mfc = section.get("matched_file_count", 0)
                files_searched = len(section["all_files"])
                self.preview_text.insert("end", f"{'='*60}\n")
                self.preview_text.insert("end", f"{name}", "filename")
                s_total = section.get("total_match_count", len(section["matches"]))
                self.preview_text.insert("end", f" — {s_total} match(es) in {mfc} file(s). Files searched: {files_searched}\n")
                s_matches = section["matches"]
                for fd, fn, ln, text in s_matches[:20]:  # first 20 per section
                    self.preview_text.insert("end", f"  {fn}:{ln}: ")
                    _insert_hl(text[:120])
                    self.preview_text.insert("end", "\n")
                if len(s_matches) > 20:
                    self.preview_text.insert("end", f"  ... and {len(s_matches) - 20} more\n")
                self.preview_text.insert("end", "\n")
            self.preview_text.insert("end", f"\nClick DOCX or TXT above to open the full report.\n")
            self.preview_text.configure(state="disabled")

        # Desktop notification (opt-in, focus-suppressed). Fires for
        # both single-suite runs and Run Multiple Search Suites.
        self._fire_completion_notification(
            f"peekdocs — Suite complete: {suite_name}",
            self.status_label.cget("text") or "Suite complete.",
        )

        # Optional completion popup — used by Run Multiple Search
        # Suites so the user gets an unambiguous "the reports you
        # just generated are here" affirmation, separate from the
        # main-page Step 4 buttons (which look identical regardless
        # of whether the previous search was Standard or Suite).
        if show_completion_popup:
            self._show_suite_completion_popup(
                suite_name, total_matches, total_elapsed,
                folder, txt_path, docx_path, extra_paths or {},
            )

    def _show_suite_completion_popup(self, suite_name, total_matches, elapsed, folder, txt_path, docx_path, extra_paths):
        """Small modal shown after a multi-suite run with Open TXT /
        Open DOCX / Open Folder buttons. Parallel to the Regex Search
        results popup so the two batch-run workflows present the same
        post-run UI."""
        import tkinter as tk
        pop, _dark = self._themed_toplevel()
        pop.title(f"Suite Reports — {suite_name}")
        pop.resizable(True, False)
        self._center_popup_on_main(pop, 640, 360)

        tk.Label(
            pop, text=f"Run complete: {suite_name}",
            font=("TkDefaultFont", 14, "bold"),
        ).pack(pady=(12, 4), padx=15)
        tk.Label(
            pop,
            text=f"{total_matches} match(es) in {elapsed:.1f}s",
            font=("TkDefaultFont", 12),
        ).pack(pady=(0, 8), padx=15)

        report_lines = ["Reports saved to:"]
        report_lines.append(f"  {txt_path}")
        report_lines.append(f"  {docx_path}")
        for fmt, path in (extra_paths or {}).items():
            if path:
                report_lines.append(f"  {path}")
        tk.Label(
            pop, text="\n".join(report_lines),
            font=("TkDefaultFont", 10), fg="gray",
            justify="left", anchor="w", wraplength=600,
        ).pack(fill="x", padx=15, pady=(0, 8))

        def _open_helper(path):
            try:
                from peekdocs.gui._helpers import safe_open_file
                w = safe_open_file(path)
                if w:
                    self._show_error(w)
            except Exception as exc:
                self._show_error(f"Could not open {path}:\n{exc}")

        btn_row = tk.Frame(pop)
        btn_row.pack(pady=(4, 8))
        ctk.CTkButton(
            btn_row, text="Open TXT", width=110, font=ctk.CTkFont(size=12),
            command=lambda p=txt_path: _open_helper(p),
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            btn_row, text="Open DOCX", width=110, font=ctk.CTkFont(size=12),
            command=lambda p=docx_path: _open_helper(p),
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            btn_row, text="Open Folder", width=120, font=ctk.CTkFont(size=12),
            command=lambda p=folder: _open_helper(p),
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            pop, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            font=ctk.CTkFont(size=12), command=pop.destroy,
        ).pack(pady=(0, 12))

        self._apply_dark_theme(pop)

    def _cancel_suite(self):
        """Cancel a running suite search."""
        self._suite_cancelled = True
        self._suite_elapsed_active = False
        self.search_start_time = None
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        # Restore the SUITES button — same _stack_label + 44x44
        # pattern as the post-suite-finish restore site.
        self._suites_btn.configure(
            text=self._stack_label(__import__("peekdocs.i18n", fromlist=["t"]).t("search_suites_label")),
            width=44, height=44,
            fg_color="#76BA1B", hover_color="#76BA1B",
            text_color="white", command=self._show_search_suites,
        )
        self.status_label.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("status_suite_cancelled"), text_color=("blue", "#66BBFF"))

    def _update_suite_elapsed(self, suite_name):
        """Update the status label with elapsed time during suite execution."""
        if not getattr(self, "_suite_elapsed_active", False):
            return
        if self.search_start_time is not None:
            elapsed = time.time() - self.search_start_time
            current = self.status_label.cget("text") or ""
            # Strip old elapsed time and append new one
            import re as _re_el
            current = _re_el.sub(r"\s*\(\d+s\)\s*$", "", current)
            self.status_label.configure(
                text=f"{current}  ({elapsed:.0f}s)",
                text_color=("blue", "#66BBFF"),
            )
        self.after(1000, lambda: self._update_suite_elapsed(suite_name))

    def _show_search_suites_help(self, parent):
        """Show help for the Search Suites popup."""
        import tkinter as tk
        help_win, _dark = self._themed_toplevel(parent)
        help_win.title("Search Suites — Help")
        help_win.geometry("640x700")
        help_win.resizable(True, True)
        help_win.transient(parent)
        # No grab_set() — user should be able to follow along in the Suites panel

        txt_frame = tk.Frame(help_win)
        txt_frame.pack(fill="both", expand=True, padx=10, pady=10)
        scrollbar = tk.Scrollbar(txt_frame)
        scrollbar.pack(side="right", fill="y")
        txt = tk.Text(txt_frame, wrap="word", font=("TkDefaultFont", 12),
                      padx=15, pady=10, spacing3=4, yscrollcommand=scrollbar.set)
        txt.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=txt.yview)

        def b(text):
            txt.insert("end", text + "\n", "bold")
        def n(text):
            txt.insert("end", text + "\n")

        txt.tag_configure("bold", font=("TkDefaultFont", 12, "bold"))

        b("What are Search Suites?")
        n("A search suite is a named group of saved searches that run")
        n("together with one click. Instead of running the same 5 or 10")
        n("searches one at a time, create a suite and run them all at once.")
        n("Results are combined into a single highlighted report.\n")

        b("How to Create a Suite")
        n("1. First, save some searches using the Save button on the main screen")
        n("2. Click Suites from the main screen")
        n("3. Click New to create a named suite")
        n("4. Click Add Search to add saved searches to the suite")
        n("5. Use \u25b2 Up and \u25bc Down to set the run order")
        n("6. Click Run Search Suite to execute all searches\n")

        b("Managing Suites")
        n("\u2022 Rename \u2014 change a suite's name")
        n("\u2022 Delete \u2014 remove a suite (does not delete the saved searches)")
        n("\u2022 Add Search \u2014 add a saved search to the suite")
        n("\u2022 Remove \u2014 remove a search from the suite (does not delete the saved search)")
        n("\u2022 \u25b2 Up / \u25bc Down \u2014 change the order searches run in\n")

        b("What Happens When You Run a Suite")
        n("Each search runs independently with its own settings (AND/OR,")
        n("regex, recursive, etc.). Results are organized by search in a")
        n("combined report. TXT is always written. DOCX, HTML, CSV, JSON,")
        n("and PDF are opt-in via the checkboxes in this popup — all")
        n("default OFF, matching the 1.2.6 Standard Search policy. Check")
        n("a format and the next suite run produces it; uncheck and the")
        n("file stops being written. The format checkboxes here are")
        n("independent from the Advanced Search Options checkboxes")
        n("(those only apply to Standard Search).\n")
        n("DOCX and PDF are skipped above 25,000 total matches across")
        n("the suite's combined search results — python-docx and fpdf2")
        n("both build the document in memory before saving, so very large")
        n("result sets would otherwise pressure RAM and freeze the GUI.")
        n("TXT (which streams to disk) has every match regardless of")
        n("size. CLI: `peekdocs --suite NAME -o docx` for TXT + DOCX. The")
        n("CLI suite -o supports docx only; for the other formats, run")
        n("the suite from this popup.\n")

        b("Run Multiple Search Suites")
        n("The Run Multiple Search Suites… button on its own row, just")
        n("above Close, lets you run two or more saved suites in one go.")
        n("Click it to open a checkbox picker over every saved suite in the")
        n("current folder (each line shows the suite's search count). Check")
        n("two or more, click Run Selected, and every saved search across")
        n("the picked suites runs in sequence:\n")
        n("• Saved-search names that appear in more than one of the")
        n("  picked suites run only once (dedup by name; duplicates don't")
        n("  re-run).")
        n("• The status line and combined report header show the label")
        n("  \"Suite A + Suite B\" when three or fewer suites are picked,")
        n("  or \"N suites\" otherwise.")
        n("• Output format checkboxes (HTML/CSV/JSON/PDF) and the search")
        n("  folder are taken from the parent Search Suites popup.")
        n("• When the run finishes, a small popup confirms the combined")
        n("  reports are written and offers Open TXT / Open DOCX / Open")
        n("  Folder buttons. That's the unambiguous way to open the")
        n("  just-generated reports — separate from the main-page")
        n("  Step 4 buttons, which look identical regardless of which")
        n("  search produced them.\n")
        n("CLI parity: to fan out a single suite across several folders,")
        n("use a shell loop with `peekdocs --suite \"$s\"`. The GUI")
        n("multi-run is the only path that fuses several suites into one")
        n("combined report — from the CLI, run each suite separately and")
        n("aggregate the reports yourself, or use the Python API")
        n("(`run_suite`) and merge `SuiteResult` objects.\n")

        b("Use Cases")
        n("\u2022 Pre-publication checklist \u2014 search for outdated terms, placeholder")
        n("  text, and other items you want to catch before publishing")
        n("\u2022 Quarterly review \u2014 run the same set of searches every quarter")
        n("\u2022 Onboarding review \u2014 search policy documents for required terms")
        n("\u2022 Any recurring workflow with multiple searches\n")

        b("CLI and Scheduled Runs")
        n("Run a suite from the command line — note that suites are")
        n("folder-scoped, so `cd` to the folder first:")
        n("  cd /path/to/folder")
        n("  peekdocs --suite \"My Suite\"")
        n("For shell loops over multiple suites, --timestamp to avoid")
        n("report overwrites, the Python API, and a Windows PowerShell")
        n("variant, see \"Search Suite Use Cases\" in the User Guide. To")
        n("generate a ready-to-paste cron (macOS/Linux) or Task Scheduler")
        n("(Windows) command without leaving the GUI, use Tools →")
        n("Schedule Search.\n")

        b("Storage — Why Per Folder?")
        n("Suites are saved in .peekdocs_collection.json alongside your")
        n("saved searches. Each folder has its own collection \u2014 if you")
        n("switch to a different Search Folder, you'll see a different set")
        n("of suites and saved searches. This is by design: the searches")
        n("you need for tax documents are different from the ones you need")
        n("for insurance paperwork, so each folder keeps only what's relevant.")
        n("Copy a folder to another computer and the suites come with it")
        n("automatically. They persist across sessions and are never")
        n("affected by upgrades or Clear Files. Use All Collections in the")
        n("Tools menu to see saved searches across all your folders.\n")

        b("Can a Suite Include Searches from Different Folders?")
        n("No — a suite can only contain saved searches from its own")
        n("folder. Each folder's saved searches and suites live in that")
        n("folder's .peekdocs_collection.json file; a suite references its")
        n("searches by name, and those names only exist inside one")
        n("folder's collection. Letting a suite span folders would require")
        n("either sharing collections across folders (breaks the")
        n("'searches live with your folder' model) or duplicating saved")
        n("searches into multiple collections (drift between copies).\n")
        n("Workarounds when you do need cross-folder reach:")
        n("• Multi-folder standard search — use the +Folder button on")
        n("  the main page to search several folders in one query")
        n("  (one search at a time, not a suite of several).")
        n("• Shell loop — `cd` to each folder and run `peekdocs")
        n("  --suite NAME` in turn; produces one report per folder.")
        n("• Python API — call `run_suite(name, directory=d)` per")
        n("  folder and aggregate the SuiteResult objects in memory.\n")

        b("Folder Changes")
        n("The Search Suites popup always uses the Search Folder from the")
        n("main screen. If you change the Search Folder while the popup")
        n("is open, the popup closes automatically to prevent a mismatch")
        n("\u2014 suites and saved searches belong to a specific folder, so")
        n("showing a stale folder could lead to confusion. Just reopen")
        n("Search Suites from the Tools menu to see the new folder's")
        n("suites and saved searches.")

        txt.configure(state="disabled")

        close_frame = tk.Frame(help_win)
        close_frame.pack(pady=(5, 10))
        ctk.CTkButton(
            close_frame, text="Close", width=80,
            font=ctk.CTkFont(size=12),
            command=help_win.destroy,
        ).pack()

        ctk.CTkButton(
            help_win, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=help_win.destroy, font=ctk.CTkFont(size=12),
        ).pack(pady=(5, 10))

        self._apply_dark_theme(help_win)


    # ── System Check ──────────────────────────────────────────────────

