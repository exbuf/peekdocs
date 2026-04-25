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
        for btn in (self.report_btn_docx, self.report_btn_txt, self.report_btn_csv,
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
