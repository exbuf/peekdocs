"""PeekDocs GUI — main application class."""

import os
import platform
import re
import subprocess
import sys
import threading
import time
from datetime import datetime

import customtkinter as ctk
from peekdocs.scanner import RESULT_FILE_PREFIXES

import webbrowser
from tkinter import filedialog, messagebox
from importlib.metadata import version as pkg_version

from peekdocs.gui._tooltip import Tooltip
from peekdocs.gui._helpers import (
    _build_command_from_values,
    _parse_summary_text,
    _parse_matched_files,
    _parse_inverse_files,
    _build_wizard_regex,
)
from peekdocs.gui._mixin_build import BuildMixin
from peekdocs.gui._mixin_search import SearchMixin
from peekdocs.gui._mixin_tools import ToolsMixin
from peekdocs.gui._mixin_data import DataMixin


class PeekDocsApp(BuildMixin, SearchMixin, ToolsMixin, DataMixin, ctk.CTk):
    def __init__(self):
        """Initialize the main application window, widgets, and saved settings."""
        super().__init__()

        # Use peekdocs.__version__ as the single source of truth: it
        # tries installed-package metadata first, then falls back to a
        # hardcoded value. Works in normal pip/pipx installs AND in
        # PyInstaller-bundled standalone exes (which don't ship the
        # .dist-info that pkg_version needs).
        from peekdocs import __version__ as _peekdocs_version
        self.title(f"\U0001F440 peekdocs {_peekdocs_version}".strip())
        self.withdraw()  # Hide until setup is complete to prevent flicker
        self.geometry("1280x800")
        self.minsize(1280, 700)
        self._center_window(1280, 760)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.process = None
        self.search_thread = None
        self.results_dir = None
        # Load persisted recent searches AND language preference. The
        # language pointer is module-level state on peekdocs.i18n, so
        # setting it here BEFORE any widgets are built means the build
        # methods pick up the right language on first paint — no
        # re-render needed at startup.
        try:
            from peekdocs.cli import _load_config
            _cfg = _load_config()
            self._recent_searches = _cfg.get("recent_searches", [])[:10]
            _lang = _cfg.get("language")
            if _lang:
                from peekdocs.i18n import set_language as _set_lang
                _set_lang(_lang)
        except Exception:
            self._recent_searches = []
        self._excluded_files = []
        # Combined highlight regex built at Search Suites completion time
        # from every sub-search's terms (with per-sub-search regex /
        # wildcard / whole-word flags honored). Used by the per-file
        # Matched Files popup so a suite-run file viewer doesn't fall
        # back to reading the (empty) main search bar and end up
        # displaying "No matches in this file." Reset to None whenever a
        # Standard Search starts or Clear Preview is clicked.
        self._suite_highlight_re = None
        self._searched_folders = set()  # track all folders searched this session
        self.advanced_visible = False
        self.elapsed_timer_id = None
        self.search_start_time = None
        # Stable cutoff used by _show_action_buttons to compare report
        # file mtimes against the most recent search's start time, so
        # leftover files from prior sessions don't show as green
        # report buttons. Initialized None so the first render before
        # any search has run falls back to exists-only semantics.
        self._last_search_start_time = None
        self._refresh_timer_id = None
        self._refresh_running = False
        self._text_size_var = ctk.StringVar(value="Normal")

        # App-level focus tracking for the desktop-notification feature.
        # Tk's focus_displayof() is per-application on macOS — it reports
        # our toplevel even when macOS has given another app the
        # foreground. <FocusIn> / <FocusOut> on the root toplevel DO
        # fire on OS-level app transitions (verified on darwin Tk 8.6+).
        # Filtered to only the root-toplevel events (event.widget is
        # self) so widget-to-widget transitions inside our own UI don't
        # flip the flag.
        self._gui_has_focus = True
        self.bind("<FocusIn>", self._on_app_focus_in, add="+")
        self.bind("<FocusOut>", self._on_app_focus_out, add="+")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Tab view: Getting Started + Search
        self._tabview = ctk.CTkTabview(self, anchor="nw", command=self._on_tab_changed)
        self._tabview.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5, 0))

        # CTkTabview uses the tab name string as both the lookup key and
        # the visible button text. To keep the experiment additive (and
        # avoid breaking every existing `_tabview.set("Getting Started")`
        # call site), keep the internal name English and override the
        # button's visible text via the underlying segmented_button.
        # `_set_language` re-runs the override on every language change.
        self._tab_started = self._tabview.add("Getting Started")
        self._tab_search = self._tabview.add("Search")

        from peekdocs.i18n import t as _t
        try:
            self._gs_tab_btn = self._tabview._segmented_button._buttons_dict.get("Getting Started")
            if self._gs_tab_btn:
                self._gs_tab_btn.configure(text=_t("getting_started_tab_label"))
                self._gs_tab_tooltip = Tooltip(self._gs_tab_btn, _t("getting_started_tab_tooltip"))
        except Exception:
            self._gs_tab_btn = None
            self._gs_tab_tooltip = None

        # Build Getting Started tab
        self._build_getting_started_tab()

        # Use an inner frame with grid layout inside the Search tab
        self._search_parent = ctk.CTkFrame(self._tab_search, fg_color="transparent")
        self._search_parent.pack(fill="both", expand=True)
        self._search_parent.grid_columnconfigure(0, weight=0)
        self._search_parent.grid_columnconfigure(1, weight=1)
        self._search_parent.grid_rowconfigure(1, weight=1)  # PanedWindow row (row 0 = Main page header; row 2 = footer)

        # Horizontal split — controls on the left, results preview on
        # the right. ttk.PanedWindow gives a draggable sash; the panes
        # are CTkFrames so the inside matches the rest of the theme.
        # ttk's default sash is ~4 px wide and the same color as the
        # window background — hard to discover and easy to misclick.
        # Style it visibly chunkier with a contrasting color so users
        # can see it and grab it.
        from tkinter import ttk as _ttk_split
        _sash_style = _ttk_split.Style()
        _is_dark = ctk.get_appearance_mode() == "Dark"
        _sash_bg = "#5A8FCC" if _is_dark else "#2196F3"  # peekdocs blue
        _sash_active = "#3B7CC0" if _is_dark else "#1976D2"
        _sash_style.configure("Peekdocs.TPanedwindow",
                              background=_sash_bg)
        _sash_style.configure("Sash",
                              sashthickness=10,
                              gripcount=14)
        # macOS / aqua needs the sash color rebuilt in every theme map.
        _sash_style.map("Peekdocs.TPanedwindow",
                        background=[("active", _sash_active)])
        self._paned = _ttk_split.PanedWindow(
            self._search_parent, orient="horizontal",
            style="Peekdocs.TPanedwindow",
        )
        self._paned.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=(5, 0))
        self._left_pane = ctk.CTkFrame(self._paned, fg_color="transparent")
        self._right_pane = ctk.CTkFrame(self._paned, fg_color="transparent")
        self._paned.add(self._left_pane, weight=1)
        self._paned.add(self._right_pane, weight=1)

        # Wrap the left pane in a scrollable frame so the controls
        # overflow gracefully when the window is narrow or short.
        self._left_scroll = ctk.CTkScrollableFrame(self._left_pane, fg_color="transparent")
        self._left_scroll.pack(fill="both", expand=True)

        # Footer area spans the full window width below the split so
        # the bottom toolbar isn't cramped on one side.
        self._footer_area = ctk.CTkFrame(self._search_parent, fg_color="transparent")
        self._footer_area.grid(row=2, column=0, columnspan=3, sticky="ew")

        # Empty toggle_row kept for compatibility (no longer displayed)
        self._toggle_row = ctk.CTkFrame(self._search_parent, fg_color="transparent")

        self._build_search_row()
        self._build_folder_row()
        self._build_advanced_toggle()
        self._build_advanced_panel()
        self._build_progress_area()
        self._build_open_report()
        self._build_index_panel()
        self._build_bottom_row()

        # Show the View Report row on startup (buttons grayed out until a search runs)
        for btn in (self.report_btn_docx, self.report_btn_txt, self.report_btn_csv,
                    self.report_btn_json, self.report_btn_pdf, self.report_btn_html):
            btn.pack(side="left", padx=(0, 2))
            btn.configure(state="disabled", fg_color="gray60", hover_color="gray60")
        # Delete on Close checkbox removed from this row — equivalent
        # control lives inside Advanced Search Options.
        # row=3: Step 3 label row (chip + "Use Advanced Search Options below..." message)
        self.report_frame.grid(
            row=3, column=0, columnspan=3, padx=(10, 5), pady=(5, 5), sticky="w"
        )
        # row=6: open-report buttons (DOCX/TXT/CSV/JSON/PDF/HTML + Delete on Close).
        # Sits below status_row (row 5) and above the Advanced container (row 7).
        self.report_btn_frame.grid(
            row=6, column=0, columnspan=3, padx=(10, 5), pady=(2, 5), sticky="w"
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
        # Force the horizontal split to open 50/50. weight=1 on each
        # pane only governs how resize deltas are shared — the initial
        # sash position falls out of natural pane widths, which the
        # left-pane controls otherwise bias slightly wider.
        self.after(1150, self._set_initial_pane_split)
        if self._is_first_run:
            self._tabview.set("Getting Started")
        else:
            self._tabview.set("Search")
        # Apply the Search-tab-visibility rules to the initial tab
        # (fire after deiconify so the segmented button is fully laid out)
        self.after(1200, self._on_tab_changed)
        # Sync entry field widths after layout is complete
        self.after(1300, self._sync_input_widths)



    def _on_app_focus_in(self, event):
        """Maintain `_gui_has_focus` for desktop-notification suppression.
        Only respond to the root toplevel's own focus event so widget-to-
        widget transitions inside the UI don't flip the flag."""
        if event.widget is self:
            self._gui_has_focus = True

    def _on_app_focus_out(self, event):
        """Counterpart to `_on_app_focus_in`. Fires when macOS / Windows
        / X11 switches the foreground app away from peekdocs."""
        if event.widget is self:
            self._gui_has_focus = False

    def destroy(self):
        """Override destroy to optionally delete report files and clear history on close."""
        if getattr(self, "delete_reports_var", None) and self.delete_reports_var.get() == "on":
            # Collect all folders that may contain peekdocs files:
            # every folder searched this session, plus current state and safe dir.
            folders_to_clean = set(getattr(self, "_searched_folders", set()))
            results_dir = getattr(self, "results_dir", None)
            if results_dir and os.path.isdir(results_dir):
                folders_to_clean.add(results_dir)
            search_folder = self.folder_entry.get().strip() if hasattr(self, "folder_entry") else ""
            if search_folder and os.path.isdir(search_folder):
                folders_to_clean.add(search_folder)
            safe_dir = os.path.join(os.path.expanduser("~"), "peekdocs_reports")
            if os.path.isdir(safe_dir):
                folders_to_clean.add(safe_dir)
            for folder in folders_to_clean:
                if not os.path.isdir(folder):
                    continue
                for fname in os.listdir(folder):
                    if fname.startswith(RESULT_FILE_PREFIXES):
                        try:
                            os.remove(os.path.join(folder, fname))
                        except OSError:
                            pass
                # Delete search index in each searched folder
                for idx_file in (".peekdocs.db", ".peekdocs.db-wal", ".peekdocs.db-shm"):
                    try:
                        idx_path = os.path.join(folder, idx_file)
                        if os.path.exists(idx_path):
                            os.remove(idx_path)
                    except OSError:
                        pass
        if getattr(self, "clear_history_var", None) and self.clear_history_var.get() == "on":
            # Delete search history file
            history_path = os.path.join(os.path.expanduser("~"), ".peekdocs_history.json")
            try:
                if os.path.exists(history_path):
                    os.remove(history_path)
            except OSError:
                pass
            # Clear recent searches from config
            try:
                from peekdocs.cli import _load_config, _save_config
                cfg = _load_config()
                cfg["recent_searches"] = []
                cfg["search_terms"] = ""
                cfg["folder"] = ""
                _save_config(cfg)
            except Exception:
                pass
        super().destroy()

    def _on_tab_changed(self):
        """Hide the Search tab button when on Search (redundant), and
        rename it to 'Done' when on Getting Started so clicking it
        returns the user to the Search tab."""
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
                # On Getting Started — show the button labeled "Done"
                search_btn.grid()
                search_btn.configure(text="Done")
        except Exception:
            pass



    def _sync_input_widths(self):
        """No-op — kept for compatibility.  Entry alignment is now handled
        by the shared _input_frame grid (both rows share the same columns).
        """
        pass

    def _set_initial_pane_split(self):
        """Place the horizontal sash at the exact 50% mark on first
        paint so the controls and results panes start equal width."""
        try:
            self.update_idletasks()
            w = self._paned.winfo_width()
            if w > 0:
                self._paned.sashpos(0, w // 2)
        except Exception:
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




def create_app():
    """Instantiate and run the PeekDocsApp."""
    app = PeekDocsApp()
    app.mainloop()
