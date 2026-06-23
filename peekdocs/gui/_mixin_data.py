"""PeekDocs GUI — DataMixin."""

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
import json
import webbrowser
from tkinter import filedialog, messagebox
from importlib.metadata import version as pkg_version

class DataMixin:
    _TEXT_SIZE_SCALES = {
        "Small": 0.85,
        "Normal": 1.0,
        "Large": 1.2,
        "Extra Large": 1.4,
        "Huge": 1.7,
    }

    _REFRESH_INTERVALS = {
        "Off": 0, "5 min": 5, "15 min": 15, "30 min": 30,
        "1 hour": 60, "4 hours": 240, "8 hours": 480, "24 hours": 1440,
    }

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
        settings["output_docx"] = (self.output_docx_var.get() == "on")
        settings["output_csv"] = (self.output_csv_var.get() == "on")
        settings["output_json"] = (self.output_json_var.get() == "on")
        settings["output_pdf"] = (self.output_pdf_var.get() == "on")
        settings["output_html"] = (self.output_html_var.get() == "on")
        settings["delete_reports_on_close"] = (self.delete_reports_var.get() == "on")
        settings["clear_history_on_close"] = (self.clear_history_var.get() == "on")
        settings["notify_on_complete"] = (self.notify_on_complete_var.get() == "on")
        settings["restrict_permissions"] = (self.restrict_permissions_var.get() == "on")
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
        if hasattr(self, "_preview_cap_var"):
            settings["preview_cap"] = self._preview_cap_var.get()
        if hasattr(self, "_appearance_mode") and self._appearance_mode != "System":
            settings["appearance_mode"] = self._appearance_mode

        if settings:
            _save_config(settings)
        else:
            path = _config_path()
            if os.path.exists(path):
                os.remove(path)
        self.status_label.configure(
            text="Settings saved to ~/.peekdocsrc",
            text_color=("blue", "#66BBFF"),
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
        # output_docx defaults TRUE when the key is absent (preserves
        # the always-write-DOCX behaviour of older configs).
        self.output_docx_var.set("on" if config.get("output_docx", True) else "off")
        self.output_csv_var.set("on" if config.get("output_csv") else "off")
        self.output_json_var.set("on" if config.get("output_json") else "off")
        self.output_pdf_var.set("on" if config.get("output_pdf") else "off")
        self.output_html_var.set("on" if config.get("output_html") else "off")
        self.inverse_var.set("on" if config.get("inverse") else "off")
        self.expression_var.set("on" if config.get("expression") else "off")
        self.whole_word_var.set("on" if config.get("whole_word", _whole_word_default) else "off")
        self.timestamp_var.set("on" if config.get("timestamp", False) else "off")
        self.delete_reports_var.set("on" if config.get("delete_reports_on_close", False) else "off")
        self.clear_history_var.set("on" if config.get("clear_history_on_close", False) else "off")
        self.notify_on_complete_var.set("on" if config.get("notify_on_complete", False) else "off")
        self.restrict_permissions_var.set("on" if config.get("restrict_permissions", False) else "off")
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
        self.max_matches_entry.insert(0, str(config.get("max_matches", 1000)))
        self.max_file_size_entry.delete(0, "end")
        self.max_file_size_entry.insert(0, str(config.get("max_file_size_mb", 100)))
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
        # Restore preview cap (browser-GUI dropdown — 100/500/1000/5000/No cap)
        if hasattr(self, "_preview_cap_var"):
            preview_cap = config.get("preview_cap", "500")
            if preview_cap not in self._PREVIEW_CAP_VALUES:
                preview_cap = "500"
            self._preview_cap_var.set(preview_cap)
        # Restore appearance mode
        appearance = config.get("appearance_mode", "System")
        if appearance not in ("System", "Light", "Dark"):
            appearance = "System"
        self._set_appearance_mode(appearance)
        # Restore hover text preference
        hover = config.get("hover_text", True)
        Tooltip.enabled = bool(hover)
        if hasattr(self, "_hover_toggle_btn"):
            self._hover_toggle_btn.configure(
                text="Tooltips: ON" if Tooltip.enabled else "Tooltips: OFF"
            )



    def _reset_saved_defaults(self):
        """Delete ~/.peekdocsrc and reset all GUI fields to factory defaults."""
        import tkinter.messagebox as mb
        confirm = mb.askyesno(
            "Restore Factory Settings",
            "This will delete ~/.peekdocsrc and return all of the following to "
            "factory defaults:\n\n"
            "  • Search mode (AND / OR), Recursive, Whole Word, Use Index\n"
            "  • Regex, Fuzzy, Wildcard, OCR, Inverse, Expression mode\n"
            "  • File types and Exclude terms\n"
            "  • Output formats (TXT, DOCX, CSV, JSON, PDF, HTML)\n"
            "  • Output directory and Timestamp setting\n"
            "  • Max Matches, Max File Size, CPU Cores\n"
            "  • Word Proximity, Lines Before, Lines After\n"
            "  • Recent searches and last-used Search Folder\n"
            "  • Session checkboxes (Delete on Close, Clear History on Close,\n"
            "    Restrict File Permissions, Notify on Search Complete)\n"
            "  • Quiet mode and appearance (dark / light theme, text size)\n\n"
            "Your documents, search history, saved searches, bookmarks, and any "
            "personal files are not affected.\n\n"
            "This cannot be undone.\n\n"
            "Continue?",
            parent=self,
            default=mb.NO,
        )
        if not confirm:
            return
        import os
        rc_path = os.path.expanduser("~/.peekdocsrc")
        try:
            if os.path.exists(rc_path):
                os.remove(rc_path)
        except Exception:
            pass
        # Reset GUI fields to factory defaults
        if hasattr(self, "_reset_all_fields"):
            self._reset_all_fields()
        self.status_label.configure(
            text="All saved defaults have been reset to factory settings.",
            text_color=("blue", "#66BBFF"),
        )

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

        win, _dark = self._themed_toplevel()
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
        ctk.CTkButton(win, text="Close", width=80, font=ctk.CTkFont(size=12), fg_color="transparent", text_color=("gray30", "gray70"), hover_color=("gray90", "gray25"), command=win.destroy).pack(pady=(0, 10))
        self._apply_dark_theme(win)



    def _on_preview_size_changed(self, value):
        """Change the Results Preview font size."""
        try:
            size = int(value)
        except ValueError:
            return
        self._preview_font_size = size
        self._apply_preview_font(size)
        self._save_ui_preference("preview_size", value)



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
        # Close ephemeral tool popups — they use fonts set at creation
        # time and won't update in place.  Skip persistent windows.
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
        # Shorten row 3 button labels at Extra Large and Huge to save width
        try:
            if value in ("Extra Large", "Huge"):
                self.search_button.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("run_standard_search_label"))
                self.save_to_collection_btn.configure(text="\u25b6 Save")
                self.load_search_btn.configure(text="\u25b6 Reload")
            else:
                self.search_button.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("run_standard_search_label"))
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

        popup, _dark = self._themed_toplevel()


        popup.withdraw()  # hidden during widget setup; centered + shown at end
        popup.title("Search History")
        popup.resizable(True, True)
        self._center_popup_on_main(popup, 850, 500)

        hist_header = tk.Frame(popup)
        hist_header.pack(fill="x", padx=10, pady=(10, 2))
        tk.Label(
            hist_header,
            text=f"Search History — {len(history)} search(es)",
            font=("TkDefaultFont", 13, "bold"),
        ).pack(side="left")
        ctk.CTkButton(
            hist_header, text="?", width=30, height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#1565C0", text_color="white",
            hover_color="#0D47A1",
            corner_radius=15,
            command=lambda: self._show_search_history_help(popup),
        ).pack(side="right")

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

        # Clear History — anchored to the far left in its own row.
        if history:
            clear_row = tk.Frame(popup)
            clear_row.pack(fill="x", padx=10, pady=(5, 0))
            clear_btn = ctk.CTkButton(
                clear_row, text="Clear History", width=100,
                fg_color="#CC3333", hover_color="#AA2222",
                command=lambda: self._clear_search_history(popup),
                font=ctk.CTkFont(size=12),
            )
            clear_btn.pack(side="left")

            timeline_btn = ctk.CTkButton(
                clear_row, text="View Timeline", width=130,
                command=lambda: self._show_search_history_chart(history, popup),
                font=ctk.CTkFont(size=12),
            )
            timeline_btn.pack(side="left", padx=(8, 0))

        # Close — centered, on its own row below Clear History.
        close_row = tk.Frame(popup)
        close_row.pack(pady=(5, 10))
        ctk.CTkButton(
            close_row, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=popup.destroy, font=ctk.CTkFont(size=12),
        ).pack()
        self._apply_dark_theme(popup)



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
                text="Search history cleared.", text_color=("blue", "#66BBFF"))

    def _show_search_history_chart(self, history, parent):
        """Timeline of past searches: matches & elapsed time over time."""
        if not history:
            self._show_error("No history to chart yet.")
            return

        from datetime import datetime
        points = []
        for entry in history:
            ts_raw = entry.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_raw[:19])
            except Exception:
                continue
            try:
                matches = int(entry.get("matches", 0) or 0)
                elapsed = float(entry.get("elapsed", 0) or 0)
            except Exception:
                continue
            points.append((ts, matches, elapsed, entry.get("search_text", "")))

        if not points:
            self._show_error("History entries missing timestamps — nothing to plot.")
            return
        points.sort(key=lambda p: p[0])
        ts_list   = [p[0] for p in points]
        matches   = [p[1] for p in points]
        elapsed_l = [p[2] for p in points]

        def _plot(ax):
            line1, = ax.plot(ts_list, matches, marker="o", color="#2196F3",
                              linewidth=1.6, markersize=4, label="Matches")
            ax.set_ylabel("Matches", fontsize=10, color="#2196F3")
            ax.tick_params(axis="y", colors="#2196F3")
            ax.set_title(f"Search history timeline — {len(points)} run(s)",
                         fontsize=12, weight="bold")
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            # Second axis for elapsed time on the right.
            ax2 = ax.twinx()
            line2, = ax2.plot(ts_list, elapsed_l, marker="s", color="#76BA1B",
                               linewidth=1.2, markersize=3, alpha=0.7, label="Elapsed (s)")
            ax2.set_ylabel("Elapsed (s)", fontsize=10, color="#76BA1B")
            ax2.tick_params(axis="y", colors="#76BA1B")
            ax.legend(handles=[line1, line2], loc="upper left", fontsize=9)
            # Rotate date ticks if there are many points.
            import matplotlib.dates as mdates
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
            for lbl in ax.get_xticklabels():
                lbl.set_rotation(30)
                lbl.set_ha("right")
                lbl.set_fontsize(8)

        self._open_chart_window("Search History — timeline", _plot,
                                 figsize=(9.0, 4.6), parent=parent)

    def _show_search_history_help(self, parent):
        """Show help for the Search History popup."""
        import tkinter as tk
        help_win, _dark = self._themed_toplevel(parent)
        help_win.title("Search History — Help")
        help_win.geometry("600x420")
        help_win.resizable(True, True)
        help_win.transient(parent)
        try:
            help_win.grab_set()
        except Exception:
            help_win.after(150, lambda: help_win.grab_set() if help_win.winfo_exists() else None)

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

        b("What is Search History?")
        n("Every search you run is automatically logged here with the date,")
        n("search terms, number of matches, number of files searched, and")
        n("elapsed time. Most recent searches appear first.\n")

        b("What it shows")
        n("Each row displays:")
        n("\u2022 Date and time of the search")
        n("\u2022 Number of matches found")
        n("\u2022 Number of files searched")
        n("\u2022 How long the search took")
        n("\u2022 The search terms used\n")

        b("How to use it")
        n("\u2022 Review past searches to remember what you looked for")
        n("\u2022 Compare results across searches (did a folder grow?)")
        n("\u2022 Click Clear History to delete the log and start fresh\n")

        b("Storage")
        n("History is saved in ~/.peekdocs_history.json and persists across")
        n("sessions. It is never affected by upgrades or Clear Files.")
        n("History is view-only \u2014 you cannot re-run a search from here.")
        n("To re-run a past search, use Save Search on the main screen")
        n("to save searches you want to repeat.")

        txt.configure(state="disabled")

        ctk.CTkButton(
            help_win, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=help_win.destroy, font=ctk.CTkFont(size=12),
        ).pack(pady=(5, 10))

        self._apply_dark_theme(help_win)

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
                    text_color=("blue", "#66BBFF"))
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
            text_color=("blue", "#66BBFF"))



    def _show_bookmarks(self):
        """Display bookmarked files."""
        import tkinter as tk

        bookmarks = self._load_bookmarks()

        popup, _dark = self._themed_toplevel()


        popup.withdraw()  # hidden during widget setup; centered + shown at end
        popup.title("Bookmarks")
        popup.resizable(True, True)
        self._center_popup_on_main(popup, 800, 480)

        bm_header = tk.Frame(popup)
        bm_header.pack(fill="x", padx=10, pady=(10, 2))
        tk.Label(
            bm_header,
            text=f"Bookmarks — {len(bookmarks)} file(s)",
            font=("TkDefaultFont", 13, "bold"),
        ).pack(side="left")
        ctk.CTkButton(
            bm_header, text="?", width=30, height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#1565C0", text_color="white",
            hover_color="#0D47A1",
            corner_radius=15,
            command=lambda: self._show_bookmarks_help(popup),
        ).pack(side="right")

        tk.Label(
            popup,
            text="Bookmarks let you pin important files for quick access — files you refer to often or "
                 "want to find again without re-running a search. Double-click a file to open it. "
                 "Right-click to remove it. To add a bookmark: run a search, click Matched Files, "
                 "then right-click a file and choose 'Add Bookmark.'",
            font=("TkDefaultFont", 10), fg="gray", wraplength=760, justify="left",
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
                    from peekdocs.gui._helpers import safe_open_file
                    warning = safe_open_file(fp)
                    if warning:
                        self._show_error(warning)

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

        # Remove Selected — anchored to the far left in its own row.
        if bookmarks:
            remove_row = tk.Frame(popup)
            remove_row.pack(fill="x", padx=10, pady=(5, 0))
            remove_btn = ctk.CTkButton(
                remove_row, text="Remove Selected", width=120,
                fg_color="#CC3333", hover_color="#AA2222",
                command=lambda: _remove_selected() if bookmarks else None,
                font=ctk.CTkFont(size=12),
            )
            remove_btn.pack(side="left")

        # Close — centered, on its own row below Remove Selected.
        close_row = tk.Frame(popup)
        close_row.pack(pady=(5, 10))
        ctk.CTkButton(
            close_row, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=popup.destroy, font=ctk.CTkFont(size=12),
        ).pack()
        self._apply_dark_theme(popup)

    def _show_bookmarks_help(self, parent):
        """Show help for the Bookmarks popup."""
        import tkinter as tk
        help_win, _dark = self._themed_toplevel(parent)
        help_win.title("Bookmarks — Help")
        help_win.geometry("600x420")
        help_win.resizable(True, True)
        help_win.transient(parent)
        try:
            help_win.grab_set()
        except Exception:
            help_win.after(150, lambda: help_win.grab_set() if help_win.winfo_exists() else None)

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

        b("What are Bookmarks?")
        n("Bookmarks let you pin important files for quick access. Instead of")
        n("re-running a search to find a file you use often, bookmark it once")
        n("and open it any time from the Tools menu.\n")

        b("How to Add a Bookmark")
        n("1. Run a search")
        n("2. Click the Matched Files button on the status bar")
        n("3. Right-click a file in the list")
        n("4. Choose 'Add Bookmark'\n")

        b("Using Bookmarks")
        n("\u2022 Double-click a bookmarked file to open it in its default application")
        n("\u2022 Right-click a bookmark to remove it")
        n("\u2022 Click 'Remove Selected' to delete the highlighted bookmark\n")

        b("Storage")
        n("Bookmarks are saved in ~/.peekdocs_bookmarks.json and persist")
        n("across sessions. They are global \u2014 not tied to a specific folder.")
        n("Bookmarks are never affected by upgrades or Clear Files.")

        txt.configure(state="disabled")

        ctk.CTkButton(
            help_win, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=help_win.destroy, font=ctk.CTkFont(size=12),
        ).pack(pady=(5, 10))

        self._apply_dark_theme(help_win)

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
        dialog, _dark = self._themed_toplevel()
        dialog.title("Save to Collection")
        dialog.resizable(False, False)
        w, h = 350, 230
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
            padx=15, pady=(15, 2), anchor="w"
        )
        ctk.CTkLabel(frame, text=f"Saving to: {folder}",
                     font=ctk.CTkFont(size=10), text_color="gray").pack(
            padx=15, pady=(0, 5), anchor="w"
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
                    text_color=("blue", "#66BBFF"), font=ctk.CTkFont(size=13),
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
        self._apply_dark_theme(dialog)

    # ── Search Wizard ────────────────────────────────────────



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
            "output_docx": self.output_docx_var.get() == "on",
            "output_csv": self.output_csv_var.get() == "on",
            "output_json": self.output_json_var.get() == "on",
            "output_pdf": self.output_pdf_var.get() == "on",
            "output_html": self.output_html_var.get() == "on",
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
        self.output_docx_var.set("on" if params.get("output_docx", True) else "off")
        self.output_csv_var.set("on" if params.get("output_csv") else "off")
        self.output_json_var.set("on" if params.get("output_json") else "off")
        self.output_pdf_var.set("on" if params.get("output_pdf") else "off")
        self.output_html_var.set("on" if params.get("output_html") else "off")
        self.range_entry.delete(0, "end")
        self.range_entry.insert(0, params.get("range_filters", ""))
        self.append_name_entry.delete(0, "end")
        self.append_name_entry.insert(0, params.get("append_name", ""))
        self.save_name_entry.delete(0, "end")
        self.save_name_entry.insert(0, params.get("save_name", ""))
        self.timestamp_var.set("on" if params.get("timestamp") else "off")



    def _show_matched_files_popup(self):
        """Show a popup listing all matched files. Click a file to open it."""
        if not self.matched_files:
            return
        import tkinter as tk

        popup, _dark = self._themed_toplevel()
        count = len(self.matched_files)

        # Search-terms prefix — quoted, comma-separated, capped at ~80
        # chars so a long expression doesn't blow out the header. Same
        # pattern as the Chart-File Type Count title. Empty search bar
        # (Expression-mode runs where terms live elsewhere) falls back
        # to the bare 'Matched Files (N)' heading.
        try:
            import shlex as _shlex_mf
            _terms_raw = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""
            try:
                _terms_tokens = _shlex_mf.split(_terms_raw)
            except ValueError:
                _terms_tokens = _terms_raw.split()
            _terms_display = ", ".join(f"'{t}'" for t in _terms_tokens)
            if len(_terms_display) > 80:
                _terms_display = _terms_display[:77] + "..."
        except Exception:
            _terms_display = ""

        if self._inverse_results:
            base_heading = f"Files Without Matches ({count})"
        else:
            base_heading = f"Matched Files ({count})"
        heading = f"{_terms_display} — {base_heading}" if _terms_display else base_heading
        popup.title(heading)
        popup.resizable(True, True)
        win_h = max(400, min(720, count * 28 + 250))
        popup.geometry(f"500x{win_h}")
        popup.transient(self)
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 500) // 2
        y = self.winfo_rooty() + (self.winfo_height() - win_h) // 2
        popup.geometry(f"+{x}+{y}")
        popup.lift()
        popup.after(50, popup.lift)
        popup.after(100, popup.focus_force)

        header_frame = tk.Frame(popup)
        header_frame.pack(fill="x", padx=10, pady=(10, 2))
        tk.Label(
            header_frame, text=heading,
            font=("TkDefaultFont", 13, "bold"),
        ).pack(side="left", expand=True)
        help_btn = ctk.CTkButton(
            header_frame, text="?", width=30, height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#1565C0", text_color="white",
            hover_color="#0D47A1",
            corner_radius=15,
            command=lambda: self._show_matched_files_help(popup),
        )
        help_btn.pack(side="right")
        tk.Label(
            popup, text="Single-click a file and click View Text to see the highlighted matches. "
                        "Double-click a file to open it in its default application (Word, Adobe Reader, etc.). "
                        "Right-click a file to add it to your Bookmarks for quick access later.",
            font=("TkDefaultFont", 10), fg="gray", wraplength=460, justify="left",
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
            from peekdocs.gui._helpers import safe_open_file
            try:
                warning = safe_open_file(filepath)
                if warning:
                    self._show_error(warning)
            except Exception:
                pass

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
        btn_frame.pack(pady=(5, 4))

        view_btn = tk.Label(
            btn_frame, text="View Text (with line numbers)",
            font=("TkDefaultFont", 13, "bold"),
            bg="#888888", fg="white",
            relief="raised", borderwidth=2,
            padx=20, pady=8, cursor="hand2",
        )
        view_btn.pack(side="left", padx=5)
        view_btn.bind("<Button-1>", lambda e: _view_text())
        view_btn.bind("<Enter>", lambda e: view_btn.configure(bg="#666666"))
        view_btn.bind("<Leave>", lambda e: view_btn.configure(bg="#888888"))

        def _show_heatmap():
            selection = listbox.curselection()
            if not selection:
                self._show_error("Select a file first to view its match heatmap.")
                return
            self._show_file_heatmap(self.matched_files[selection[0]], popup)

        heatmap_btn = ctk.CTkButton(
            btn_frame, text="Heatmap", width=110,
            command=_show_heatmap,
            font=ctk.CTkFont(size=12),
        )
        heatmap_btn.pack(side="left", padx=5)
        from peekdocs.gui._tooltip import Tooltip as _TT_hm
        _TT_hm(heatmap_btn,
               "Open a chart showing where the matches sit in the selected file "
               "(by line number). Useful for spotting clusters at the top, "
               "middle, or end of the document.")

        # Close on its own bottom row, centered, muted style — matches the
        # standard Close-button look used in every other help / info popup.
        ctk.CTkButton(
            popup, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            font=ctk.CTkFont(size=12),
            command=popup.destroy,
        ).pack(pady=(0, 10))
        self._apply_dark_theme(popup)

    def _show_file_heatmap(self, item, parent):
        """Per-file match heatmap: density of matches by line number."""
        filename = item[1]
        line_nums = item[3] if len(item) > 3 else []
        if not line_nums:
            self._show_error(
                f"No line-number data captured for {filename} — the heatmap "
                "needs per-match line numbers, which weren't included in this "
                "search's results."
            )
            return

        def _plot(ax):
            # Two-panel chart: hist on top (density), strip plot on bottom
            # (every match as a vertical tick).
            ax.hist(line_nums, bins=min(40, max(8, len(line_nums) // 5)),
                    color="#FF6B35", edgecolor="#E55A2B", alpha=0.85)
            for ln in line_nums:
                ax.axvline(ln, color="#1565C0", alpha=0.15, linewidth=0.6)
            ax.set_xlabel("Line number", fontsize=10)
            ax.set_ylabel("Matches in bin", fontsize=10)
            ax.set_title(f"Match heatmap — {filename} ({len(line_nums)} matches)",
                         fontsize=12, weight="bold")
            ax.grid(axis="y", linestyle="--", alpha=0.4)

        self._open_chart_window(f"Match heatmap — {filename}", _plot,
                                 figsize=(8.4, 4.4), parent=parent)

    def _show_excluded_files_popup(self):
        """Show a popup listing files excluded from the search with reasons."""
        import tkinter as tk
        if not self._excluded_files:
            return
        popup, _dark = self._themed_toplevel()
        count = len(self._excluded_files)

        # Search-terms prefix — same pattern as Matched Files / Chart-
        # File Type Count. Quoted, comma-separated, capped at ~80 chars.
        # Empty search bar falls back to the bare heading.
        try:
            import shlex as _shlex_ef
            _terms_raw = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""
            try:
                _terms_tokens = _shlex_ef.split(_terms_raw)
            except ValueError:
                _terms_tokens = _terms_raw.split()
            _terms_display = ", ".join(f"'{t}'" for t in _terms_tokens)
            if len(_terms_display) > 80:
                _terms_display = _terms_display[:77] + "..."
        except Exception:
            _terms_display = ""

        title_text = f"Excluded Files ({count})"
        header_text = f"Files Excluded from Search ({count})"
        if _terms_display:
            title_text = f"{_terms_display} — {title_text}"
            header_text = f"{_terms_display} — {header_text}"
        popup.title(title_text)
        popup.resizable(True, True)
        popup.geometry("560x500")
        popup.transient(self)
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 560) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 500) // 2
        popup.geometry(f"+{x}+{y}")
        popup.lift()
        popup.after(50, popup.lift)
        popup.after(100, popup.focus_force)

        header_frame = tk.Frame(popup)
        header_frame.pack(fill="x", padx=10, pady=(10, 2))
        tk.Label(
            header_frame, text=header_text,
            font=("TkDefaultFont", 13, "bold"),
        ).pack(side="left", expand=True)
        help_btn = ctk.CTkButton(
            header_frame, text="?", width=30, height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#1565C0", text_color="white",
            hover_color="#0D47A1",
            corner_radius=15,
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

        # Top action row — View Chart on its own line so it has room
        # without colliding with the centered Close button below.
        action_row = tk.Frame(popup)
        action_row.pack(pady=(5, 4))
        ctk.CTkButton(
            action_row, text="View Chart", width=110,
            command=lambda: self._show_excluded_reasons_chart(by_reason, popup),
            font=ctk.CTkFont(size=12),
        ).pack()

        # Close on its own bottom row, centered — matches the standard
        # Close-button layout used in the other peekdocs popups.
        close_row = tk.Frame(popup)
        close_row.pack(pady=(0, 10))
        ctk.CTkButton(
            close_row, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            font=ctk.CTkFont(size=12),
            command=popup.destroy,
        ).pack()
        self._apply_dark_theme(popup)

    def _show_excluded_reasons_chart(self, by_reason, parent):
        """Donut chart of skip-reason proportions."""
        if not by_reason:
            self._show_error("No excluded files to chart.")
            return
        reasons = sorted(by_reason.keys(), key=lambda r: len(by_reason[r]), reverse=True)
        sizes = [len(by_reason[r]) for r in reasons]
        # peekdocs palette — recycled if more than 6 reasons appear
        palette = ["#2196F3", "#FF6B35", "#76BA1B", "#FF9800",
                   "#9C27B0", "#1565C0", "#666666", "#CC3333"]
        colors = [palette[i % len(palette)] for i in range(len(reasons))]
        total = sum(sizes)

        def _plot(ax):
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=reasons,
                colors=colors,
                autopct=lambda pct: f"{pct:.0f}%\n({int(round(pct * total / 100))})",
                startangle=90,
                wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 1.5},
                textprops={"fontsize": 9},
                pctdistance=0.78,
            )
            for at in autotexts:
                at.set_color("white")
                at.set_fontsize(8)
                at.set_weight("bold")
            ax.set_title(f"Excluded files by reason — {total} file(s)",
                         fontsize=12, weight="bold")

        self._open_chart_window("Excluded Files by Reason", _plot,
                                 figsize=(7.4, 5.0), parent=parent)

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

                if fname.startswith("peekdocs_suite_results"):
                    app_files.append((filepath, "Suite results"))
                elif fname.startswith("peekdocs_standard_results"):
                    app_files.append((filepath, "Standard search results"))
                elif fname.startswith("peekdocs_regex_results"):
                    app_files.append((filepath, "Regex search results"))
                elif fname.startswith("peekdocs_accumulated_"):
                    app_files.append((filepath, "Accumulated results"))
                elif fname.startswith("peekdocs_report_"):
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
                text_color=("blue", "#66BBFF"),
            )
            return

        popup, _dark = self._themed_toplevel()


        popup.withdraw()  # hidden during widget setup; centered + shown at end
        popup.title(f"peekdocs App Files ({len(app_files)})")
        popup.resizable(True, True)
        self._center_popup_on_main(popup, 1000, 500)

        tk.Label(
            popup, text=f"peekdocs Files ({len(app_files)} file(s) in {folder})",
            font=("TkDefaultFont", 13, "bold"),
        ).pack(pady=(10, 2))
        tk.Label(
            popup, text="Every peekdocs-created file has 'peekdocs' in the filename. "
                        "If you see 'peekdocs' in a filename, it's ours. If you don't, it's your document. "
                        "Note: this list only shows files in the current Search Folder. If you've used peekdocs "
                        "in other folders, those folders will have their own peekdocs files. Some peekdocs files "
                        "are hidden (names starting with a dot, like .peekdocs_collection.json) \u2014 you may "
                        "need to enable 'Show hidden files' in File Explorer (Windows), Finder (macOS), or "
                        "your file manager (Linux) to see them.\n\n"
                        "To clean up: Tools \u2192 Clear Files lets you choose exactly which "
                        "peekdocs files to delete. Your original documents, saved searches "
                        "(.peekdocs_collection.json), and settings (~/.peekdocsrc) are never "
                        "shown in Clear Files and cannot be accidentally deleted.",
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

        ctk.CTkButton(popup, text="Close", width=80, font=ctk.CTkFont(size=12), fg_color="transparent", text_color=("gray30", "gray70"), hover_color=("gray90", "gray25"), command=popup.destroy).pack(pady=(5, 10))
        self._apply_dark_theme(popup)



    def _show_all_collections(self):
        """Scan home directory for all .peekdocs_collection.json files and display a summary."""
        import tkinter as tk
        from collections import defaultdict
        from peekdocs.collection import COLLECTION_FILENAME, load_collection

        home = os.path.expanduser("~")
        self.status_label.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("status_scanning_collections"), text_color=("blue", "#66BBFF"))
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
                text_color=("blue", "#66BBFF"),
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
            text_color=("blue", "#66BBFF"),
        )

        popup, _dark = self._themed_toplevel()


        popup.withdraw()  # hidden during widget setup; centered + shown at end
        popup.title(f"All Saved Collections ({len(collections)} folder(s))")
        popup.resizable(True, True)
        self._center_popup_on_main(popup, 1050, 550)

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
                    text_color=("blue", "#66BBFF"),
                )
                popup.destroy()

        listbox.bind("<Double-1>", _on_double_click)

        ctk.CTkButton(
            popup, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=popup.destroy, font=ctk.CTkFont(size=12),
        ).pack(pady=(5, 10))
        self._apply_dark_theme(popup)



    def _show_file_text_view(self, filepath, filename, highlight_regex_pattern=None, highlight_label=None):
        """Display extracted text of a file with line numbers and match highlighting.

        If highlight_regex_pattern is provided, matches for that regex are
        highlighted instead of matches for the main search bar's terms. This
        is used by the Regex Search View Files popup so the highlights reflect
        the regex category rather than whatever is
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

        win, _dark = self._themed_toplevel()
        win.title(f"Text View — {filename}")

        # Position on the same screen as the main app window. Tk's
        # default position is "primary display center" or "cursor's
        # display" depending on platform — neither follows where the
        # main window (or the Matched Files popup that just invoked
        # this) actually lives. On multi-monitor setups (e.g. laptop
        # + external display) this stranded the Text View popup on the
        # laptop while the user was working on the external display.
        # Computing a top-left from the main window's screen rectangle
        # and letting the OS keep the window inside that screen fixes
        # the strand without forcing a specific monitor.
        _tv_w, _tv_h = 900, 720
        try:
            self.update_idletasks()
            _mx = self.winfo_rootx()
            _my = self.winfo_rooty()
            _mw = max(self.winfo_width(), 1)
            _mh = max(self.winfo_height(), 1)
            _tv_x = _mx + (_mw - _tv_w) // 2
            _tv_y = _my + (_mh - _tv_h) // 2
            win.geometry(f"{_tv_w}x{_tv_h}+{_tv_x}+{_tv_y}")
        except Exception:
            win.geometry(f"{_tv_w}x{_tv_h}")
        win.resizable(True, True)

        _tv_header = tk.Frame(win)
        _tv_header.pack(fill="x", padx=15, pady=(10, 2))
        tk.Label(
            _tv_header, text=f"{filename}  —  {len(lines)} line(s) extracted",
            font=("TkDefaultFont", 12, "bold"),
        ).pack(side="left", expand=True)
        ctk.CTkButton(
            _tv_header, text="?", width=30, height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#1565C0", text_color="white",
            hover_color="#0D47A1",
            corner_radius=15,
            command=lambda: self._show_text_view_help(win),
        ).pack(side="right")
        if highlight_label:
            tk.Label(
                win, text=f"Regex Search category: {highlight_label}",
                font=("TkDefaultFont", 11, "bold"), fg="#CC0000",
            ).pack(pady=(0, 2))
        tk.Label(
            win, text="Line numbers match those shown in the Results Preview.",
            font=("TkDefaultFont", 10), fg="gray",
        ).pack(pady=(0, 0))
        tk.Label(
            win, text="Possible matches are highlighted in yellow.",
            font=("TkDefaultFont", 10), fg="gray",
        ).pack(pady=(0, 0))
        tk.Label(
            win, text="Review each in context — not all highlights are actual sensitive data.",
            font=("TkDefaultFont", 10), fg="gray",
        ).pack(pady=(0, 2))
        tk.Label(
            win, text="Highlighted matches are pattern-based and may include false positives or missed matches.",
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
        txt.tag_configure("match", background="yellow", foreground="black")

        # Build highlight pattern — priority order:
        #   1. caller-supplied regex (Regex Search path)
        #   2. combined regex saved at Search Suites completion
        #      (suite mode — the suite runs multiple sub-searches each
        #      with their own terms; one combined regex covers them all)
        #   3. main search bar terms (normal Standard Search path)
        #
        # The suite-mode branch sets ``combined_re`` directly because the
        # regex was pre-compiled at suite-finish; the other paths still
        # build a ``patterns`` list that gets compiled below.
        patterns = []
        combined_re = None
        suite_re = getattr(self, '_suite_highlight_re', None)
        if highlight_regex_pattern:
            patterns.append(highlight_regex_pattern)
        elif suite_re is not None:
            # Suite-run viewer: use the combined regex from the suite run.
            # Ignore whatever's in the main search bar — it may hold stale
            # text from a Standard Search the user ran before the suite,
            # which would highlight the wrong terms here.
            combined_re = suite_re
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
                    import shlex as _shlex_view
                    try:
                        terms = _shlex_view.split(search_text)
                    except ValueError:
                        terms = search_text.split()
                for term in terms:
                    if use_wildcard:
                        from peekdocs.scanner import _wildcard_to_regex
                        patterns.append(_wildcard_to_regex(term))
                    elif use_regex:
                        patterns.append(term)
                    elif use_whole_word:
                        _pfx = r'\b' if _re_view.match(r'\w', term) else ''
                        _sfx = r'\b' if _re_view.search(r'\w$', term) else ''
                        patterns.append(_pfx + _re_view.escape(term) + _sfx)
                    else:
                        patterns.append(_re_view.escape(term))

        if combined_re is None and patterns:
            # Strip inline global flags like (?i) — we already pass re.IGNORECASE.
            # Inline flags must be at the start of the expression, but wrapping
            # in a group for alternation moves them away from position 0.
            cleaned = [_re_view.sub(r'^\(\?[aiLmsux]+\)', '', p) for p in patterns]
            try:
                combined_re = _re_view.compile("|".join(f"({p})" for p in cleaned), _re_view.IGNORECASE)
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
            txt.tag_configure("first_match", background="yellow", foreground="black")
            txt.tag_add("first_match", first_match_range[0], first_match_range[1])

        ctk.CTkButton(
            win, text="Close", width=80, font=ctk.CTkFont(size=12),
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"), command=win.destroy,
        ).pack(pady=(5, 10))
        self._apply_dark_theme(win)


    def _show_text_view_help(self, parent):
        """Show help for the Text View popup."""
        import tkinter as tk
        help_win, _dark = self._themed_toplevel(parent)
        help_win.title("Text View — Help")
        help_win.geometry("650x520")
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
        txt.tag_configure("toc_title", font=("TkDefaultFont", 14, "bold"), spacing1=5, spacing3=8)
        txt.tag_configure("toc_item", font=("TkDefaultFont", 11), lmargin1=20, lmargin2=20,
                          foreground="#999999" if ctk.get_appearance_mode() == "Dark" else "gray40")
        txt.tag_configure("toc_item_red", font=("TkDefaultFont", 11, "bold"), lmargin1=20,
                          lmargin2=20, foreground="red")
        txt.tag_configure("heading_red", font=("TkDefaultFont", 13, "bold"),
                          spacing1=8, spacing3=4, foreground="red")

        def h(s): txt.insert("end", s + "\n", "heading")
        def h_red(s): txt.insert("end", s + "\n", "heading_red")
        def b(s): txt.insert("end", s + "\n", "body")
        def blank(): txt.insert("end", "\n")

        txt.insert("end", "TABLE OF CONTENTS\n", "toc_title")
        for section in [
            "What This Window Shows",
            "Line Numbers",
            "Highlighting",
        ]:
            txt.insert("end", f"\u2022 {section}\n", "toc_item")
        for section in [
            "Disclaimer",
        ]:
            txt.insert("end", f"\u2022 {section}\n", "toc_item_red")
        txt.insert("end", "\n")

        h("WHAT THIS WINDOW SHOWS")
        b("The full extracted text of the selected file, with line")
        b("numbers down the left side and every match highlighted")
        b("in yellow. This lets you see exactly where your search")
        b("terms (or regex patterns) appear in the file, in context,")
        b("without opening the original document.")
        blank()

        h("LINE NUMBERS")
        b("Line numbers refer to the extracted text, not the original")
        b("page or paragraph number in the source document. For plain")
        b("text files, these match. For PDFs, Word docs, and other")
        b("formats, peekdocs extracts the text content and numbers the")
        b("resulting lines \u2014 so line 47 here will match line 47 in")
        b("the Results Preview, but may not match a page number in")
        b("the original file.")
        blank()

        h("HIGHLIGHTING")
        b("Yellow highlighting shows where your search terms (or regex")
        b("patterns) matched in the text. For regular searches, the")
        b("highlighting uses the terms from the search bar. For Regex")
        b("Search, it uses the regex pattern for the selected category.")
        blank()

        h_red("DISCLAIMER")
        b("Highlighted matches are pattern-based and may include false")
        b("positives or missed matches. Pattern-based detection is a")
        b("discovery aid, not a guarantee. Users remain")
        b("solely responsible for how they use and interpret its output.")
        blank()

        txt.configure(state="disabled")

        close_frame = tk.Frame(help_win)
        close_frame.pack(pady=(5, 10))
        ctk.CTkButton(
            close_frame, text="Close", width=80,
            font=ctk.CTkFont(size=12),
            command=help_win.destroy,
        ).pack()

        self._apply_dark_theme(help_win)


    def _add_folder_bar(self, parent, message="Your search will run against this folder.", initial_folder=None, recursive_var=None):
        """Add a folder display bar with Change Folder button to a wizard window.

        Returns the folder label widget so callers can read the current value.
        If initial_folder is provided, it overrides the main screen's folder.
        If recursive_var is provided, a Recursive checkbox is added inside the bar.
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

        _is_dark = ctk.get_appearance_mode() == "Dark"
        _folder_text = initial_folder or self.folder_entry.get().strip() or "(none)"
        folder_label = tk.Label(
            top_row, text=_folder_text,
            font=("TkDefaultFont", 11),
            fg="#66BBFF" if _is_dark else "blue",
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

        change_btn = ctk.CTkButton(
            top_row, text="Browse", command=_change_folder,
            font=ctk.CTkFont(size=11), width=80, height=28,
        )
        change_btn.pack(side="right")
        from peekdocs.gui._tooltip import Tooltip
        Tooltip(change_btn, "Select the folder to scan. Linux: double-click to select a folder in the dialog")

        if recursive_var is not None:
            tk.Checkbutton(
                bar, variable=recursive_var,
                text="Include subfolders (Recursive)", font=("TkDefaultFont", 11),
            ).pack(anchor="w", pady=(2, 0))
        elif message:
            tk.Label(
                bar, text=message,
                font=("TkDefaultFont", 10), fg="gray", anchor="w",
            ).pack(fill="x", pady=(2, 0))

        return folder_label

    # ── Search Collections ─────────────────────────────────



    def open_help(self):
        """Open the peekdocs User Guide in the default web browser."""
        webbrowser.open("https://github.com/exbuf/peekdocs/blob/main/docs/USER_GUIDE.md")



    def show_about(self):
        """Show the About dialog with version and author information."""
        import tkinter as tk
        about_win, _dark = self._themed_toplevel()
        about_win.title("About peekdocs")
        about_win.resizable(False, False)
        about_win.geometry("300x245")
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
        tk.Label(about_win, text="Privacy-first local document search\nand analysis workbench\nwith yellow-highlighted reports",
                 font=("TkDefaultFont", 10), fg="gray", justify="center").pack(pady=(0, 4))
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
        self._apply_dark_theme(about_win)



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
            text_color=("blue", "#66BBFF"),
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
                    text_color=("blue", "#66BBFF"),
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
            self.search_button.configure(state="normal", fg_color="#2196F3", hover_color="#1976D2", text_color="white")
            self._update_index_button_color()
            if returncode == 0 and result:
                fc = result.get("file_count", 0)
                lc = result.get("line_count", 0)
                el = result.get("elapsed", 0)
                display = f"Index built: {fc} files, {lc:,} lines in {el:.1f}s"
                self.status_label.configure(text=display, text_color=("blue", "#66BBFF"))
                # Default auto-refresh to 1 hour if currently Off
                if self.refresh_interval_var.get() == "Off":
                    self.refresh_interval_var.set("1 hour")
                    self._on_refresh_interval_changed("1 hour")
            elif returncode == 2:
                self.status_label.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("status_index_cancelled"), text_color=("blue", "#66BBFF"))
            else:
                err_msg = (result or {}).get("error", "Unknown error")
                self.status_label.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("status_index_failed_format").format(err=err_msg), text_color="red")

        threading.Thread(target=_run, daemon=True).start()
        self.after(300, _poll_progress)



    def delete_index_action(self):
        """Delete the search index from the selected folder."""
        folder = self.folder_entry.get().strip()
        if not folder or not os.path.isdir(folder):
            self._show_error("Please select a valid folder.")
            return

        # Confirm before destroying the index. The cost is rebuild time on
        # the next search (seconds for small folders, minutes for large or
        # PDF-heavy ones); searches stay correct regardless.
        from tkinter import messagebox
        if not messagebox.askyesno(
            "Delete Index",
            f"Delete the search index for:\n{folder}\n\n"
            "The next search in this folder will rebuild the index by reading every "
            "file once — this can take seconds for small folders or minutes for "
            "large or PDF-heavy ones. Searches stay correct either way; only the "
            "speed of repeated searches is affected until the index is rebuilt.\n\n"
            "This cannot be undone (but you can rebuild the index later by running "
            "another search or clicking Build Index).\n\n"
            "Continue?",
            default=messagebox.NO,
        ):
            return

        cmd = [sys.executable, "-m", "peekdocs", "-q", "--index-clear"]
        try:
            # Same in-process-when-frozen helper as the main search.
            from peekdocs.gui._helpers import _run_peekdocs_cli
            stdout, _stderr, _rc = _run_peekdocs_cli(cmd, folder)
            msg = stdout.strip()
        except Exception:
            self._show_error("Failed to delete index.")
            return
        self.status_label.configure(
            text=msg or "Index removed.",
            text_color=("blue", "#66BBFF"),
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
                text_color=("blue", "#66BBFF"),
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
        status_win, _dark = self._themed_toplevel()
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
        self._apply_dark_theme(status_win)



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
        self.status_label.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("status_cancelling_index"), text_color=("blue", "#66BBFF"))


