"""PeekDocs GUI — FileAnalysisMixin.

Extracted from ``_mixin_tools.py`` in the mixin-tools-split refactor.
Owns every folder-scanning tool under the Tools menu: File Inventory,
Duplicate Finder, Large Files, Empty Files, Recent Changes, File Age
Distribution, Protected Files, Unsearchable Files, Collection Summary,
and the shared category/sensitive-file helpers used by File Inventory's
Categories view.

Each tool follows the same shape:

* ``_run_<tool>`` — validation + kick off a background thread.
* ``_<tool>_thread`` — walk the folder, do the scan work off the UI thread.
* ``_<tool>_finished`` — receive results back on the UI thread.
* ``_show_<tool>_popup`` — render results into a themed toplevel.
* ``_save_<tool>_report`` (some tools) — export the popup to a text file.
* ``_show_<tool>_chart`` (some tools) — open a matplotlib chart popup.

Shared utilities:

* ``_format_file_size`` — bytes → human-readable string (KB / MB / GB / TB).
* ``_show_category_files_help`` — "?" help popup for File Inventory's
  Categories view.
* ``_show_sensitive_category_files`` — display files in a specific
  category (called via lambda from _mixin_tools.py:8873; still resolves
  through PeekDocsApp's MRO after the extraction).

All methods retain their original names for git-history continuity —
renaming would break git blame and cross-references without adding
value.
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


class FileAnalysisMixin:
    def _run_file_inventory(self):
        """Launch a background scan to inventory all files in the search folder."""
        folder = self.folder_entry.get().strip()
        if not folder or not os.path.isdir(folder):
            self._show_error("Please select a search folder first.")
            return
        recursive = self.recursive_var.get() == "on"
        self.status_label.configure(
            text="Scanning folder for file inventory...", text_color=("blue", "#66BBFF"))
        self.progress_bar.grid(
            row=5, column=0, columnspan=3, padx=10, pady=(2, 2), sticky="ew")
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
            text_color=("blue", "#66BBFF"))
        self._show_file_inventory_popup(results)

    def _show_file_inventory_popup(self, results):
        """Display the file inventory results in a popup window."""
        import tkinter as tk
        fmt = self._format_file_size

        popup, _dark = self._themed_toplevel()


        popup.withdraw()  # hidden during widget setup; centered + shown at end
        popup.title("File Inventory")
        popup.resizable(True, True)
        self._center_popup_on_main(popup, 780, 580)

        # Header
        header_frame = tk.Frame(popup)
        header_frame.pack(fill="x", padx=10, pady=(10, 2))
        tk.Label(
            header_frame,
            text=f"File Inventory — {results['total_files']} file(s)",
            font=("TkDefaultFont", 13, "bold"),
        ).pack(side="left", expand=True)

        # Explanation and folder path
        tk.Label(
            popup,
            text=f"Summary of all files in your Search Folder"
                 + (" and subfolders" if results.get("recursive") else "")
                 + " — includes your documents and any peekdocs-created files. "
                 "Shows total count, size, breakdown by file type, and oldest/newest files.",
            font=("TkDefaultFont", 10), fg="gray", wraplength=740, justify="left",
        ).pack(padx=12, pady=(0, 2))
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

        # Save Report — anchored to the far left in its own row.
        save_row = tk.Frame(popup)
        save_row.pack(fill="x", padx=10, pady=(5, 0))
        save_btn = ctk.CTkButton(
            save_row, text="Save Report", width=100,
            command=lambda: self._save_inventory_report(results),
            font=ctk.CTkFont(size=12),
        )
        save_btn.pack(side="left")
        Tooltip(save_btn, "Save this inventory as a plain text file")

        chart_btn = ctk.CTkButton(
            save_row, text="View Chart", width=110,
            command=lambda: self._show_file_inventory_chart(results, popup),
            font=ctk.CTkFont(size=12),
        )
        chart_btn.pack(side="left", padx=(8, 0))
        Tooltip(chart_btn, "Open a horizontal bar chart of file counts by extension")

        by_type_btn = ctk.CTkButton(
            save_row, text="View by Type (A-Z)", width=160,
            command=lambda: self._show_file_inventory_by_type(results, popup),
            font=ctk.CTkFont(size=12),
        )
        by_type_btn.pack(side="left", padx=(8, 0))
        Tooltip(by_type_btn, "Open a second window listing file types alphabetically with per-type counts and total size")

        # Close — centered, on its own row below Save Report.
        close_row = tk.Frame(popup)
        close_row.pack(pady=(5, 10))
        close_btn = ctk.CTkButton(
            close_row, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=popup.destroy,
            font=ctk.CTkFont(size=12),
        )
        close_btn.pack()

    def _show_file_inventory_chart(self, results, parent):
        """Horizontal bar chart of top 15 file types by count."""
        type_counts = results.get("type_counts", {})
        if not type_counts:
            self._show_error("No files to chart.")
            return
        ranked = sorted(type_counts.items(), key=lambda kv: kv[1], reverse=True)[:15]
        labels = [k for k, _ in ranked]
        counts = [v for _, v in ranked]

        def _plot(ax):
            y_pos = list(range(len(labels)))
            ax.barh(y_pos, counts, color="#76BA1B", edgecolor="#5A8F12")
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=9)
            ax.invert_yaxis()
            ax.set_xlabel("Files", fontsize=10)
            ax.set_title("Top 15 file types by count", fontsize=12, weight="bold")
            ax.grid(axis="x", linestyle="--", alpha=0.4)
            for i, v in enumerate(counts):
                ax.text(v, i, f" {v:,}", va="center", fontsize=9, color="#333333")

        self._open_chart_window("File Inventory by Type", _plot, parent=parent)

    def _show_file_inventory_by_type(self, results, parent):
        """Second popup: file types sorted alphabetically with counts.

        Same data as the main File Inventory popup's breakdown table, but
        sorted A-Z instead of by count descending. Positioned to the
        right of `parent` so the two windows can be compared side by
        side.
        """
        import tkinter as tk
        fmt = self._format_file_size
        type_counts = results.get("type_counts", {})
        if not type_counts:
            self._show_error("No files to list.")
            return

        popup, _dark = self._themed_toplevel()
        popup.withdraw()  # hidden during widget setup; positioned + shown at end
        popup.title("File Inventory — by Type (A-Z)")
        popup.resizable(True, True)

        # Position to the right of the parent inventory popup. Falls
        # back to centered on main if the parent geometry isn't queryable.
        try:
            parent.update_idletasks()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            w, h = 520, 580
            popup.geometry(f"{w}x{h}+{px + pw + 12}+{py}")
        except Exception:
            self._center_popup_on_main(popup, 520, 580)

        # Header
        header_frame = tk.Frame(popup)
        header_frame.pack(fill="x", padx=10, pady=(10, 2))
        tk.Label(
            header_frame,
            text=f"By Type (A-Z) — {len(type_counts)} file type(s), {results['total_files']} file(s)",
            font=("TkDefaultFont", 13, "bold"),
        ).pack(side="left", expand=True)

        tk.Label(
            popup,
            text="File types from the parent File Inventory window, sorted alphabetically. "
                 "Files with no extension are grouped under '(no extension)' at the bottom.",
            font=("TkDefaultFont", 10), fg="gray", wraplength=480, justify="left",
        ).pack(padx=12, pady=(0, 5))

        # Listbox
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

        listbox.insert("end", f"{'Extension':<20}{'Files':>8}{'Size':>14}")
        listbox.insert("end", f"{'─' * 20}{'─' * 8}{'─' * 14}")

        # Sort alphabetically (case-insensitive). Files without an
        # extension surface as empty-string keys from the scanner;
        # display them as '(no extension)' and push to the end so the
        # A-Z ordering of real extensions reads cleanly.
        def _sort_key(item):
            ext = item[0]
            is_empty = ext == ""
            return (is_empty, ext.lower())
        for ext, count in sorted(type_counts.items(), key=_sort_key):
            display_ext = ext if ext else "(no extension)"
            size_str = fmt(results["type_sizes"].get(ext, 0))
            listbox.insert("end", f"{display_ext:<20}{count:>8}{size_str:>14}")

        listbox.insert("end", f"{'─' * 20}{'─' * 8}{'─' * 14}")
        listbox.insert("end", f"{'TOTAL':<20}{results['total_files']:>8}{fmt(results['total_size']):>14}")

        close_btn = ctk.CTkButton(
            popup, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=popup.destroy,
            font=ctk.CTkFont(size=12),
        )
        close_btn.pack(pady=(0, 10))

        popup.deiconify()

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
                text_color=("blue", "#66BBFF"))
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
            text="Scanning for password-protected files...", text_color=("blue", "#66BBFF"))
        self.progress_bar.grid(
            row=5, column=0, columnspan=3, padx=10, pady=(2, 2), sticky="ew")
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
                text_color=("blue", "#66BBFF"))
        else:
            self.status_label.configure(
                text=f"Found {count} password-protected file(s) ({results['scanned']} checked).",
                text_color=("blue", "#66BBFF"))
        self._show_protected_popup(results)



    def _show_protected_popup(self, results):
        """Display the password-protected file scan results."""
        import tkinter as tk
        count = len(results["protected"])

        popup, _dark = self._themed_toplevel()


        popup.withdraw()  # hidden during widget setup; centered + shown at end
        popup.title("Password-Protected Files")
        popup.resizable(True, True)
        self._center_popup_on_main(popup, 800, 500)

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
        self._apply_dark_theme(popup)



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
                text_color=("blue", "#66BBFF"))
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
            text="Scanning for duplicate files...", text_color=("blue", "#66BBFF"))
        self.progress_bar.grid(
            row=5, column=0, columnspan=3, padx=10, pady=(2, 2), sticky="ew")
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

            # Skip peekdocs's own files via the shared naming-convention
            # helper so this surface agrees with the scanner's
            # discover_files exclusion (peekdocs_ visible / .peekdocs
            # hidden prefixes are reserved).
            from peekdocs.scanner import is_peekdocs_internal_file

            for root, dirs, files in walker:
                for fname in files:
                    if is_peekdocs_internal_file(fname):
                        continue
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
                text_color=("blue", "#66BBFF"))
        else:
            self.status_label.configure(
                text=f"No duplicate files found ({results['total_files']} file(s) checked).",
                text_color=("blue", "#66BBFF"))
        self._show_duplicate_popup(results)



    def _show_duplicate_popup(self, results):
        """Display the duplicate file scan results."""
        import tkinter as tk
        fmt = self._format_file_size
        groups = results["groups"]
        total_dupes = sum(len(g[0]) - 1 for g in groups)

        popup, _dark = self._themed_toplevel()


        popup.withdraw()  # hidden during widget setup; centered + shown at end
        popup.title("Duplicate Files")
        popup.resizable(True, True)
        self._center_popup_on_main(popup, 820, 550)

        header_frame = tk.Frame(popup)
        header_frame.pack(fill="x", padx=10, pady=(10, 2))
        tk.Label(
            header_frame,
            text=f"Duplicate Files — {len(groups)} group(s), {total_dupes} extra copy(ies)",
            font=("TkDefaultFont", 13, "bold"),
        ).pack(side="left", expand=True)

        tk.Label(
            popup,
            text="Duplicates are files with identical content but different names or locations. "
                 "Your OS prevents two files with the same name in the same folder, but it can't "
                 "detect when a file has been copied to another folder, renamed, or saved twice "
                 "under a different name. Over time, this leads to wasted disk space and confusion "
                 "about which copy is the current version. peekdocs compares file contents (not names) "
                 "using a digital fingerprint (MD5 hash) — if two files are byte-for-byte identical, "
                 "they appear in the same group below regardless of their names.",
            font=("TkDefaultFont", 10), fg="gray", wraplength=780, justify="left",
        ).pack(padx=12, pady=(0, 5))

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

        # Save Report — anchored to the far left in its own row.
        if groups:
            save_row = tk.Frame(popup)
            save_row.pack(fill="x", padx=10, pady=(5, 0))
            save_btn = ctk.CTkButton(
                save_row, text="Save Report", width=100,
                command=lambda: self._save_duplicate_report(results),
                font=ctk.CTkFont(size=12),
            )
            save_btn.pack(side="left")

        # Close — centered, on its own row below Save Report.
        close_row = tk.Frame(popup)
        close_row.pack(pady=(5, 10))
        ctk.CTkButton(
            close_row, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=popup.destroy, font=ctk.CTkFont(size=12),
        ).pack()
        self._apply_dark_theme(popup)



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
                text_color=("blue", "#66BBFF"))
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
            text="Scanning for large files...", text_color=("blue", "#66BBFF"))

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
            text_color=("blue", "#66BBFF"))
        self._show_large_file_popup(results)



    def _show_large_file_popup(self, results):
        """Display the largest files in a popup."""
        import tkinter as tk
        fmt = self._format_file_size

        popup, _dark = self._themed_toplevel()


        popup.withdraw()  # hidden during widget setup; centered + shown at end
        popup.title("Largest Files")
        popup.resizable(True, True)
        self._center_popup_on_main(popup, 800, 500)

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
            btn_frame, text="View Chart", width=110,
            command=lambda: self._show_large_files_chart(results, popup),
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_frame, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=popup.destroy, font=ctk.CTkFont(size=12),
        ).pack(side="left")
        self._apply_dark_theme(popup)

    def _show_large_files_chart(self, results, parent):
        """Log-scale histogram of file sizes with top 10 outliers labeled."""
        largest = results.get("largest", [])
        if not largest:
            self._show_error("No files to chart.")
            return
        sizes = [s for s, _ in largest if s > 0]
        if not sizes:
            self._show_error("All files report zero bytes — nothing to chart.")
            return

        import math
        fmt = self._format_file_size

        def _plot(ax):
            import numpy as np
            from matplotlib.ticker import FixedLocator, FuncFormatter
            log_sizes = [math.log10(s) for s in sizes]
            lo, hi = min(log_sizes), max(log_sizes)
            # If every file sits on the exact same log value, widen the
            # display window so the bar isn't a 1-pixel sliver.
            if hi - lo < 1e-9:
                lo, hi = lo - 0.5, hi + 0.5
            bins = np.linspace(lo, hi, 25)
            ax.hist(log_sizes, bins=bins, color="#FF9800", edgecolor="#E55A2B", alpha=0.8)
            ax.set_xlabel("File size", fontsize=10)
            ax.set_ylabel("Files", fontsize=10)
            ax.set_title(f"Largest {len(largest)} files — size distribution", fontsize=12, weight="bold")
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            # Always render 6 evenly-spaced tick labels across the data
            # range — covers both narrow distributions (all files within
            # a single decade) and wide distributions (KB to GB).
            tick_positions = np.linspace(lo, hi, 6)
            ax.xaxis.set_major_locator(FixedLocator(tick_positions))
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _pos: fmt(int(10 ** x))))
            for lbl in ax.get_xticklabels():
                lbl.set_rotation(30)
                lbl.set_ha("right")
                lbl.set_fontsize(8)

        self._open_chart_window("Large Files — size distribution", _plot,
                                 figsize=(8.0, 4.6), parent=parent)

    # ── Empty File Detector ──────────────────────────────────



    def _run_empty_file_scan(self):
        """Find zero-length or blank files in the search folder."""
        folder = self.folder_entry.get().strip()
        if not folder or not os.path.isdir(folder):
            self._show_error("Please select a search folder first.")
            return
        recursive = self.recursive_var.get() == "on"
        self.status_label.configure(
            text="Scanning for empty files...", text_color=("blue", "#66BBFF"))

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
            text_color=("blue", "#66BBFF"))
        self._show_empty_file_popup(results)



    def _show_empty_file_popup(self, results):
        """Display empty files in a popup."""
        import tkinter as tk
        count = len(results["empty"])

        popup, _dark = self._themed_toplevel()


        popup.withdraw()  # hidden during widget setup; centered + shown at end
        popup.title("Empty Files")
        popup.resizable(True, True)
        self._center_popup_on_main(popup, 750, 450)

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
        self._apply_dark_theme(popup)

    # ── Recent Changes Dashboard ─────────────────────────────



    def _run_recent_changes(self):
        """Show files modified recently in the search folder."""
        folder = self.folder_entry.get().strip()
        if not folder or not os.path.isdir(folder):
            self._show_error("Please select a search folder first.")
            return
        recursive = self.recursive_var.get() == "on"
        self.status_label.configure(
            text="Scanning for recently modified files...", text_color=("blue", "#66BBFF"))

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
            text_color=("blue", "#66BBFF"))
        self._show_recent_changes_popup(results)



    def _show_recent_changes_popup(self, results):
        """Display recently modified files grouped by time period."""
        import tkinter as tk
        from datetime import datetime
        fmt = self._format_file_size
        b = results["buckets"]

        popup, _dark = self._themed_toplevel()


        popup.withdraw()  # hidden during widget setup; centered + shown at end
        popup.title("Recent Changes")
        popup.resizable(True, True)
        self._center_popup_on_main(popup, 820, 550)

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
        self._apply_dark_theme(popup)

    # ── File Age Distribution ────────────────────────────────

    _AGE_BUCKETS = [
        # (label, max_days)  — files younger than max_days fall into this bucket
        ("0–6 months", 180),
        ("6 months – 1 year", 365),
        ("1–3 years", 365 * 3),
        ("3–5 years", 365 * 5),
        ("5–10 years", 365 * 10),
        ("10+ years", None),  # catchall
    ]

    def _run_file_age_distribution(self):
        """Show files grouped by modification age in a histogram view."""
        folder = self.folder_entry.get().strip()
        if not folder or not os.path.isdir(folder):
            self._show_error("Please select a search folder first.")
            return
        recursive = self.recursive_var.get() == "on"
        self.status_label.configure(
            text="Scanning for file ages...", text_color=("blue", "#66BBFF"))

        import threading
        t = threading.Thread(
            target=self._file_age_distribution_thread,
            args=(folder, recursive), daemon=True)
        t.start()

    def _file_age_distribution_thread(self, folder, recursive):
        """Worker thread: collect files and bucket them by mtime age."""
        import time

        now = time.time()
        buckets = {label: [] for label, _ in self._AGE_BUCKETS}
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
                    except (OSError, PermissionError):
                        continue
                    total_files += 1
                    age_days = (now - mtime) / 86400
                    entry = (filepath, mtime, fsize)
                    # Place into the first matching bucket (smallest threshold wins).
                    placed = False
                    for label, max_days in self._AGE_BUCKETS:
                        if max_days is not None and age_days <= max_days:
                            buckets[label].append(entry)
                            placed = True
                            break
                    if not placed:
                        # Catchall — "10+ years"
                        buckets[self._AGE_BUCKETS[-1][0]].append(entry)
        except Exception:
            pass

        # Sort each bucket by mtime descending (most recent first).
        for key in buckets:
            buckets[key].sort(key=lambda x: x[1], reverse=True)

        results = {
            "folder": folder,
            "recursive": recursive,
            "total_files": total_files,
            "buckets": buckets,
        }
        self.after(0, self._file_age_distribution_finished, results)

    def _file_age_distribution_finished(self, results):
        """Handle file age distribution completion."""
        self.status_label.configure(
            text=f"Scanned {results['total_files']} file(s) — see File Age Distribution.",
            text_color=("blue", "#66BBFF"))
        self._show_file_age_distribution_popup(results)

    def _show_file_age_distribution_popup(self, results):
        """Display the age histogram + per-bucket file lists."""
        import tkinter as tk
        from datetime import datetime
        fmt = self._format_file_size
        buckets = results["buckets"]
        total = results["total_files"]

        popup, _dark = self._themed_toplevel()
        popup.withdraw()  # hidden during widget setup; centered + shown at end
        popup.title("File Age Distribution")
        popup.resizable(True, True)

        # Header
        tk.Label(
            popup,
            text=f"File Age Distribution — {total} file(s)",
            font=("TkDefaultFont", 13, "bold"),
        ).pack(pady=(10, 2))
        recursive_str = " (including subfolders)" if results["recursive"] else ""
        tk.Label(
            popup,
            text=f"{results['folder']}{recursive_str}",
            font=("TkDefaultFont", 10), fg="gray",
        ).pack(pady=(0, 2))
        tk.Label(
            popup,
            text="To analyze a different folder, use Browse on the main page to select it, then reopen this tool.",
            font=("TkDefaultFont", 10, "italic"), fg="gray",
        ).pack(pady=(0, 5))

        # Histogram + per-bucket file lists in a single scrollable Text widget
        text_frame = tk.Frame(popup)
        text_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        vbar = tk.Scrollbar(text_frame, orient="vertical")
        vbar.pack(side="right", fill="y")
        txt = tk.Text(
            text_frame, font=("Courier", 11), wrap="none",
            yscrollcommand=vbar.set,
            bg="#2b2b2b" if _dark else "white",
            fg="white" if _dark else "black",
            borderwidth=1, relief="sunken", highlightthickness=0,
        )
        vbar.config(command=txt.yview)
        txt.pack(side="left", fill="both", expand=True)

        # ASCII histogram across the top.
        max_count = max((len(buckets[lbl]) for lbl, _ in self._AGE_BUCKETS), default=0)
        bar_width = 40
        label_width = max(len(lbl) for lbl, _ in self._AGE_BUCKETS)
        txt.insert("end", "Histogram (by modification date)\n")
        txt.insert("end", "─" * (label_width + bar_width + 22) + "\n")
        for label, _max_days in self._AGE_BUCKETS:
            count = len(buckets[label])
            pct = (count / total * 100) if total else 0
            if max_count > 0:
                fill = int(round(bar_width * count / max_count))
            else:
                fill = 0
            bar = "█" * fill + " " * (bar_width - fill)
            txt.insert("end",
                f"{label:<{label_width}}  {bar} {count:>6} file(s) ({pct:>4.1f}%)\n")
        txt.insert("end", "\n")

        # Per-bucket file lists.
        for label, _max_days in self._AGE_BUCKETS:
            files = buckets[label]
            txt.insert("end", f"── {label} ({len(files)} file(s)) ──\n")
            if not files:
                txt.insert("end", "    (none)\n")
            else:
                for filepath, mtime, fsize in files:
                    date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
                    rel = os.path.relpath(filepath, results["folder"])
                    txt.insert("end", f"    {date_str}  {fmt(fsize):>10}  {rel}\n")
            txt.insert("end", "\n")
        txt.configure(state="disabled")

        # Save Report — anchored to the far left in its own row.
        save_row = tk.Frame(popup)
        save_row.pack(fill="x", padx=10, pady=(5, 0))
        save_btn = ctk.CTkButton(
            save_row, text="Save Report", width=100,
            command=lambda: self._save_file_age_distribution_report(results),
            font=ctk.CTkFont(size=12),
        )
        save_btn.pack(side="left")
        Tooltip(save_btn, "Save this histogram as a plain text file")

        chart_btn = ctk.CTkButton(
            save_row, text="View Chart", width=110,
            command=lambda: self._show_file_age_chart(results, popup),
            font=ctk.CTkFont(size=12),
        )
        chart_btn.pack(side="left", padx=(8, 0))
        Tooltip(chart_btn, "Open this distribution as a matplotlib bar chart")

        # Close — centered, on its own row below Save Report.
        close_row = tk.Frame(popup)
        close_row.pack(pady=(5, 10))
        ctk.CTkButton(
            close_row, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=popup.destroy, font=ctk.CTkFont(size=12),
        ).pack()
        self._apply_dark_theme(popup)
        self._center_popup_on_main(popup, 880, 600)

    def _show_file_age_chart(self, results, parent):
        """Vertical bar chart of files per age bucket."""
        buckets = results.get("buckets", {})
        labels = [lbl for lbl, _ in self._AGE_BUCKETS]
        counts = [len(buckets.get(lbl, [])) for lbl in labels]
        if sum(counts) == 0:
            self._show_error("No files to chart.")
            return

        def _plot(ax):
            x_pos = list(range(len(labels)))
            ax.bar(x_pos, counts, color="#2196F3", edgecolor="#1976D2")
            ax.set_xticks(x_pos)
            ax.set_xticklabels(labels, fontsize=9, rotation=30, ha="right")
            ax.set_ylabel("Files", fontsize=10)
            ax.set_title("File age distribution", fontsize=12, weight="bold")
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            for i, v in enumerate(counts):
                if v:
                    ax.text(i, v, f" {v:,}", ha="center", va="bottom", fontsize=9, color="#333333")

        self._open_chart_window("File Age Distribution", _plot,
                                 figsize=(8.0, 4.6), parent=parent)

    def _save_file_age_distribution_report(self, results):
        """Save the file age distribution as a plain-text report."""
        from datetime import datetime
        from tkinter import filedialog
        fmt = self._format_file_size
        buckets = results["buckets"]
        total = results["total_files"]
        default = os.path.join(
            results["folder"],
            "peekdocs_file_age_distribution.txt",
        )
        path = filedialog.asksaveasfilename(
            title="Save File Age Distribution Report",
            initialfile=os.path.basename(default),
            initialdir=os.path.dirname(default),
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("All Files", "*.*")],
        )
        if not path:
            return
        try:
            lines = []
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"File Age Distribution — {now_str}")
            lines.append(f"Folder: {results['folder']}")
            lines.append(f"Recursive: {results['recursive']}")
            lines.append(f"Total files: {total}")
            lines.append("")
            max_count = max((len(buckets[lbl]) for lbl, _ in self._AGE_BUCKETS), default=0)
            bar_width = 40
            label_width = max(len(lbl) for lbl, _ in self._AGE_BUCKETS)
            lines.append("Histogram")
            lines.append("─" * (label_width + bar_width + 22))
            for label, _max_days in self._AGE_BUCKETS:
                count = len(buckets[label])
                pct = (count / total * 100) if total else 0
                fill = int(round(bar_width * count / max_count)) if max_count else 0
                bar = "█" * fill + " " * (bar_width - fill)
                lines.append(f"{label:<{label_width}}  {bar} {count:>6} file(s) ({pct:>4.1f}%)")
            lines.append("")
            for label, _max_days in self._AGE_BUCKETS:
                files = buckets[label]
                lines.append(f"── {label} ({len(files)} file(s)) ──")
                if not files:
                    lines.append("    (none)")
                else:
                    for filepath, mtime, fsize in files:
                        date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
                        rel = os.path.relpath(filepath, results["folder"])
                        lines.append(f"    {date_str}  {fmt(fsize):>10}  {rel}")
                lines.append("")
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            self.status_label.configure(
                text=f"Report saved: {os.path.basename(path)}",
                text_color="green",
            )
        except OSError as exc:
            self._show_error(f"Could not write report: {exc}")

    # ── Collection Summary ───────────────────────────────────

    def _run_collection_summary(self):
        """Generate a one-page summary combining the lightweight file-analysis
        insights (overview, searchability, file types, age distribution,
        large files, recent activity, empty files) in a single pass."""
        folder = self.folder_entry.get().strip()
        if not folder or not os.path.isdir(folder):
            self._show_error("Please select a search folder first.")
            return
        recursive = self.recursive_var.get() == "on"
        mfs_str = self.max_file_size_entry.get().strip() if hasattr(self, "max_file_size_entry") else ""
        try:
            max_file_size_mb = int(mfs_str) if mfs_str else 100
        except ValueError:
            max_file_size_mb = 100
        use_ocr = self.ocr_var.get() == "on" if hasattr(self, "ocr_var") else False
        self.status_label.configure(
            text="Building Collection Summary...", text_color=("blue", "#66BBFF"))

        import threading
        t = threading.Thread(
            target=self._collection_summary_thread,
            args=(folder, recursive, max_file_size_mb, use_ocr),
            daemon=True)
        t.start()

    def _collection_summary_thread(self, folder, recursive, max_file_size_mb, use_ocr):
        """Worker thread: walk the folder once and aggregate every lightweight
        metric. Duplicate detection and password-protected detection are
        deliberately skipped — those need full file reads / hash computation
        and have dedicated tools."""
        from peekdocs.constants import SUPPORTED_TYPES, OCR_IMAGE_TYPES
        from peekdocs.scanner import RESULT_FILE_PREFIXES
        from collections import Counter, defaultdict
        import time

        now = time.time()

        searchable_exts = set(SUPPORTED_TYPES)
        if use_ocr:
            searchable_exts |= set(OCR_IMAGE_TYPES)

        peekdocs_prefixes = tuple(RESULT_FILE_PREFIXES) + (
            "peekdocs_report_", "peekdocs_accumulated_", "peekdocs_global_test_",
        )
        peekdocs_exact = {
            ".peekdocs.db", ".peekdocs.db-wal", ".peekdocs.db-shm",
            ".peekdocs_collection.json", "peekdocs_errors.log",
        }
        special_searchable = {".env", "dockerfile", ".dockerfile"}
        OS_META = self._UNSEARCHABLE_OS_METADATA
        max_bytes = max_file_size_mb * 1024 * 1024 if max_file_size_mb > 0 else None

        total_files = 0
        total_size = 0
        subfolders = set()
        oldest_mtime = None
        newest_mtime = None
        oldest_path = None
        newest_path = None
        ext_counts = Counter()
        ext_sizes = Counter()
        age_buckets = {label: 0 for label, _ in self._AGE_BUCKETS}
        unsearch_categories = defaultdict(int)
        large_files = []  # list of (size, relative_path) — kept sorted, capped at 10
        recent_30d = 0
        recent_90d = 0
        empty_count = 0

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
                if recursive and root != folder:
                    subfolders.add(root)
                for fname in files:
                    filepath = os.path.join(root, fname)
                    total_files += 1
                    lower = fname.lower()

                    try:
                        fsize = os.path.getsize(filepath)
                        mtime = os.path.getmtime(filepath)
                    except (OSError, PermissionError):
                        unsearch_categories["Read permission denied"] += 1
                        continue

                    total_size += fsize
                    if oldest_mtime is None or mtime < oldest_mtime:
                        oldest_mtime = mtime
                        oldest_path = filepath
                    if newest_mtime is None or mtime > newest_mtime:
                        newest_mtime = mtime
                        newest_path = filepath

                    age_days = (now - mtime) / 86400
                    placed = False
                    for label, max_days in self._AGE_BUCKETS:
                        if max_days is not None and age_days <= max_days:
                            age_buckets[label] += 1
                            placed = True
                            break
                    if not placed:
                        age_buckets[self._AGE_BUCKETS[-1][0]] += 1

                    if age_days <= 30:
                        recent_30d += 1
                    if age_days <= 90:
                        recent_90d += 1

                    ext = os.path.splitext(fname)[1].lower()

                    # Categorize using the same logic as Unsearchable Files.
                    if (lower in peekdocs_exact or
                            fname.startswith(peekdocs_prefixes) or
                            fname.startswith("~$") or
                            (fname.startswith(".") and lower == ".peekdocsrc")):
                        unsearch_categories["peekdocs-created"] += 1
                    elif lower in OS_META or fname.startswith("._"):
                        unsearch_categories["Hidden / OS metadata"] += 1
                    elif fname.startswith(".") and lower not in special_searchable:
                        unsearch_categories["Hidden / OS metadata"] += 1
                    elif ext not in searchable_exts and lower not in special_searchable:
                        unsearch_categories["Unsupported file type"] += 1
                    elif fsize == 0:
                        unsearch_categories["Empty (0 bytes)"] += 1
                        empty_count += 1
                    elif max_bytes is not None and fsize > max_bytes:
                        unsearch_categories["Oversized"] += 1
                    else:
                        # Searchable! Track its extension distribution.
                        ext_label = ext or "(no extension)"
                        ext_counts[ext_label] += 1
                        ext_sizes[ext_label] += fsize

                    # Track top-10 largest files (any file, regardless of category).
                    if len(large_files) < 10 or fsize > large_files[-1][0]:
                        large_files.append((fsize, filepath))
                        large_files.sort(key=lambda x: -x[0])
                        large_files = large_files[:10]
        except Exception:
            pass

        searchable_count = total_files - sum(unsearch_categories.values())
        results = {
            "folder": folder,
            "recursive": recursive,
            "max_file_size_mb": max_file_size_mb,
            "use_ocr": use_ocr,
            "scan_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_files": total_files,
            "total_size": total_size,
            "subfolders": len(subfolders),
            "oldest_mtime": oldest_mtime,
            "newest_mtime": newest_mtime,
            "oldest_path": oldest_path,
            "newest_path": newest_path,
            "searchable_count": searchable_count,
            "unsearch_categories": dict(unsearch_categories),
            "ext_top": ext_counts.most_common(10),
            "ext_sizes": dict(ext_sizes),
            "age_buckets": age_buckets,
            "large_files": large_files,
            "recent_30d": recent_30d,
            "recent_90d": recent_90d,
            "empty_count": empty_count,
        }
        self.after(0, self._collection_summary_finished, results)

    def _collection_summary_finished(self, results):
        """Handle Collection Summary completion."""
        self.status_label.configure(
            text=(
                f"Collection Summary: {results['total_files']} file(s) in "
                f"{self._format_file_size(results['total_size'])}."
            ),
            text_color=("blue", "#66BBFF"))
        self._show_collection_summary_popup(results)

    def _build_collection_summary_text(self, results):
        """Render the Collection Summary as a single plain-text block.
        Used both by the popup (for the read-only display) and the
        Save Report path so what the user sees on screen is byte-
        identical to what gets saved."""
        from datetime import datetime
        fmt = self._format_file_size
        r = results
        lines = []
        lines.append("peekdocs Collection Summary")
        lines.append(f"Folder:        {r['folder']}")
        recursive_str = "yes (including subfolders)" if r["recursive"] else "no"
        lines.append(f"Recursive:     {recursive_str}")
        lines.append(f"Max File Size: {r['max_file_size_mb']} MB (set in Advanced Search Options; 0 = no limit)")
        lines.append(f"OCR enabled:   {r['use_ocr']}")
        lines.append(f"Scanned at:    {r['scan_time']}")
        lines.append("")

        # ── Overview ──
        total = r["total_files"]
        s_pct_overview = (r["searchable_count"] / total * 100) if total else 0
        lines.append("OVERVIEW")
        lines.append(f"  Total files:    {r['total_files']:,}")
        lines.append(
            f"  Searchable:     {r['searchable_count']:,} / {r['total_files']:,} "
            f"({s_pct_overview:.1f}%)"
        )
        lines.append(f"  Total size:     {fmt(r['total_size'])}")
        lines.append(f"  Subfolders:     {r['subfolders']:,}")
        if r["oldest_mtime"] is not None:
            old_d = datetime.fromtimestamp(r["oldest_mtime"]).strftime("%Y-%m-%d")
            rel = os.path.relpath(r["oldest_path"], r["folder"])
            lines.append(f"  Oldest file:    {old_d}  {rel}")
        if r["newest_mtime"] is not None:
            new_d = datetime.fromtimestamp(r["newest_mtime"]).strftime("%Y-%m-%d")
            rel = os.path.relpath(r["newest_path"], r["folder"])
            lines.append(f"  Newest file:    {new_d}  {rel}")
        lines.append("")

        # ── Searchability ──
        # `total` and `s_pct_overview` already computed above for the
        # OVERVIEW section's Searchable summary line — reuse them here.
        s_pct = s_pct_overview
        u_pct = 100 - s_pct
        lines.append("SEARCHABILITY")
        lines.append(f"  Searchable:     {r['searchable_count']:,} ({s_pct:.1f}%)")
        lines.append(f"  Unsearchable:   {total - r['searchable_count']:,} ({u_pct:.1f}%)")
        for cat in self._UNSEARCHABLE_CATEGORIES:
            n = r["unsearch_categories"].get(cat, 0)
            if n > 0:
                lines.append(f"    {cat:<24} {n:,}")
        lines.append("")

        # ── File Types (top 10 by count, searchable only) ──
        if r["ext_top"]:
            lines.append("TOP FILE TYPES (searchable, by count)")
            label_width = max(len(ext) for ext, _ in r["ext_top"])
            for ext, count in r["ext_top"]:
                size = fmt(r["ext_sizes"].get(ext, 0))
                lines.append(f"  {ext:<{label_width}}  {count:>6}  {size:>10}")
            lines.append("")

        # ── Age Distribution histogram ──
        max_count = max(r["age_buckets"].values(), default=0)
        bar_width = 30
        age_label_width = max(len(lbl) for lbl, _ in self._AGE_BUCKETS)
        lines.append("AGE DISTRIBUTION (by modification date)")
        for label, _max_days in self._AGE_BUCKETS:
            count = r["age_buckets"][label]
            pct = (count / total * 100) if total else 0
            fill = int(round(bar_width * count / max_count)) if max_count else 0
            bar = "█" * fill + " " * (bar_width - fill)
            lines.append(
                f"  {label:<{age_label_width}}  {bar} {count:>6} ({pct:>4.1f}%)")
        lines.append("")

        # ── Recent Activity ──
        lines.append("RECENT ACTIVITY")
        lines.append(f"  Modified in last 30 days:  {r['recent_30d']:,}")
        lines.append(f"  Modified in last 90 days:  {r['recent_90d']:,}")
        lines.append("")

        # ── Large Files (top 10) ──
        if r["large_files"]:
            lines.append("LARGEST FILES (top 10)")
            for fsize, filepath in r["large_files"]:
                rel = os.path.relpath(filepath, r["folder"])
                lines.append(f"  {fmt(fsize):>10}  {rel}")
            lines.append("")

        # ── Empty Files ──
        if r["empty_count"]:
            lines.append(f"EMPTY FILES: {r['empty_count']:,}")
            lines.append("")

        # ── Note about heavier scans not included ──
        lines.append(
            "Note: duplicate detection and password-protected detection are\n"
            "  not included in this fast-path summary — they require full\n"
            "  file reads / hash computation. Use the dedicated Tools menu\n"
            "  entries (Duplicate Finder, Protected Files) for those.")
        return "\n".join(lines)

    def _show_collection_summary_popup(self, results):
        """Display the Collection Summary in a scrollable read-only Text widget."""
        import tkinter as tk

        popup, _dark = self._themed_toplevel()
        popup.withdraw()  # hidden during widget setup; centered + shown at end
        popup.title("Collection Summary")
        popup.resizable(True, True)

        tk.Label(
            popup,
            text=f"Collection Summary — {results['total_files']:,} file(s)",
            font=("TkDefaultFont", 13, "bold"),
        ).pack(pady=(10, 2))
        recursive_str = " (including subfolders)" if results["recursive"] else ""
        tk.Label(
            popup,
            text=f"{results['folder']}{recursive_str}",
            font=("TkDefaultFont", 10), fg="gray",
        ).pack(pady=(0, 2))
        tk.Label(
            popup,
            text="To analyze a different folder, use Browse on the main page to select it, then reopen this tool.",
            font=("TkDefaultFont", 10, "italic"), fg="gray",
        ).pack(pady=(0, 5))

        text_frame = tk.Frame(popup)
        text_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        vbar = tk.Scrollbar(text_frame, orient="vertical")
        vbar.pack(side="right", fill="y")
        txt = tk.Text(
            text_frame, font=("Courier", 11), wrap="none",
            yscrollcommand=vbar.set,
            bg="#2b2b2b" if _dark else "white",
            fg="white" if _dark else "black",
            borderwidth=1, relief="sunken", highlightthickness=0,
        )
        vbar.config(command=txt.yview)
        txt.pack(side="left", fill="both", expand=True)
        txt.insert("1.0", self._build_collection_summary_text(results))
        txt.configure(state="disabled")

        # Save Report — anchored to the far left in its own row.
        save_row = tk.Frame(popup)
        save_row.pack(fill="x", padx=10, pady=(5, 0))
        save_btn = ctk.CTkButton(
            save_row, text="Save Report", width=100,
            command=lambda: self._save_collection_summary_report(results),
            font=ctk.CTkFont(size=12),
        )
        save_btn.pack(side="left")
        Tooltip(save_btn, "Save this summary as a plain text file")

        # Close — centered, on its own row below Save Report.
        close_row = tk.Frame(popup)
        close_row.pack(pady=(5, 10))
        ctk.CTkButton(
            close_row, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=popup.destroy, font=ctk.CTkFont(size=12),
        ).pack()
        self._apply_dark_theme(popup)
        self._center_popup_on_main(popup, 920, 640)

    def _save_collection_summary_report(self, results):
        """Save the Collection Summary as a plain-text report."""
        from tkinter import filedialog

        default = os.path.join(
            results["folder"],
            "peekdocs_collection_summary.txt",
        )
        path = filedialog.asksaveasfilename(
            title="Save Collection Summary Report",
            initialfile=os.path.basename(default),
            initialdir=os.path.dirname(default),
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("All Files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._build_collection_summary_text(results))
            self.status_label.configure(
                text=f"Report saved: {os.path.basename(path)}",
                text_color="green",
            )
        except OSError as exc:
            self._show_error(f"Could not write report: {exc}")

    # ── Unsearchable Files ───────────────────────────────────

    # Hidden / OS metadata names — case-insensitive match. Mirrors
    # scanner.py's _EXCLUDE_NAMES set so the categorization here matches
    # what discover_files would actually skip during a real search.
    _UNSEARCHABLE_OS_METADATA = {
        ".ds_store", ".ds_store?", "thumbs.db", "desktop.ini",
        ".spotlight-v100", ".trashes", ".fseventsd",
    }

    # Categories in display + categorization-priority order. First-match wins
    # when a file qualifies for multiple categories (e.g. a peekdocs-created
    # .docx is reported as peekdocs-created, not as a searchable .docx).
    _UNSEARCHABLE_CATEGORIES = [
        "peekdocs-created",
        "Hidden / OS metadata",
        "Read permission denied",
        "Unsupported file type",
        "Empty (0 bytes)",
        "Oversized",
    ]

    def _run_unsearchable_files(self):
        """Scan the folder and group files peekdocs cannot search by reason."""
        folder = self.folder_entry.get().strip()
        if not folder or not os.path.isdir(folder):
            self._show_error("Please select a search folder first.")
            return
        recursive = self.recursive_var.get() == "on"
        # Honor the same Max File Size the user has set in Advanced Search
        # Options so the Oversized bucket matches what a real search would skip.
        mfs_str = self.max_file_size_entry.get().strip() if hasattr(self, "max_file_size_entry") else ""
        try:
            max_file_size_mb = int(mfs_str) if mfs_str else 100
        except ValueError:
            max_file_size_mb = 100
        use_ocr = self.ocr_var.get() == "on" if hasattr(self, "ocr_var") else False
        self.status_label.configure(
            text="Scanning for unsearchable files...", text_color=("blue", "#66BBFF"))

        import threading
        t = threading.Thread(
            target=self._unsearchable_files_thread,
            args=(folder, recursive, max_file_size_mb, use_ocr),
            daemon=True)
        t.start()

    def _unsearchable_files_thread(self, folder, recursive, max_file_size_mb, use_ocr):
        """Worker thread: walk the folder and categorize unsearchable files."""
        from peekdocs.constants import SUPPORTED_TYPES, OCR_IMAGE_TYPES
        from peekdocs.scanner import RESULT_FILE_PREFIXES

        # The full set of extensions peekdocs would try to search.
        searchable_exts = set(SUPPORTED_TYPES)
        if use_ocr:
            searchable_exts |= set(OCR_IMAGE_TYPES)

        # Prefixes that mark peekdocs-created files (mirrors scanner's
        # _EXCLUDE_PREFIXES + the explicit names below).
        peekdocs_prefixes = tuple(RESULT_FILE_PREFIXES) + (
            "peekdocs_report_", "peekdocs_accumulated_",
            "peekdocs_global_test_",
        )
        peekdocs_exact = {
            ".peekdocs.db", ".peekdocs.db-wal", ".peekdocs.db-shm",
            ".peekdocs_collection.json", "peekdocs_errors.log",
        }
        # Special filenames the scanner treats as searchable despite their
        # unusual shape (no real extension, or leading dot). Must stay
        # OUT of the Hidden bucket below — mirrors scanner._SPECIAL_FILENAMES.
        special_searchable = {".env", "dockerfile", ".dockerfile"}

        max_bytes = max_file_size_mb * 1024 * 1024 if max_file_size_mb > 0 else None

        buckets = {cat: [] for cat in self._UNSEARCHABLE_CATEGORIES}
        total_files = 0
        searchable_count = 0

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
                    total_files += 1
                    lower = fname.lower()
                    # Categorize in priority order. First match wins.
                    if (lower in peekdocs_exact or
                            fname.startswith(peekdocs_prefixes) or
                            fname.startswith("~$") or
                            (fname.startswith(".") and lower == ".peekdocsrc")):
                        buckets["peekdocs-created"].append((filepath, 0, "peekdocs-created"))
                        continue
                    if lower in self._UNSEARCHABLE_OS_METADATA or fname.startswith("._"):
                        buckets["Hidden / OS metadata"].append((filepath, 0, "OS metadata file"))
                        continue
                    # Any other dotfile is treated as hidden — matches the
                    # post-search Excluded Files popup ("hidden file (starts
                    # with .)"). Special filenames the scanner explicitly
                    # treats as searchable (.env, .dockerfile, dockerfile)
                    # are NOT swept into Hidden.
                    if fname.startswith(".") and lower not in special_searchable:
                        buckets["Hidden / OS metadata"].append(
                            (filepath, 0, "hidden file (starts with .)"))
                        continue
                    try:
                        fsize = os.path.getsize(filepath)
                    except (OSError, PermissionError) as exc:
                        buckets["Read permission denied"].append((filepath, 0, str(exc)))
                        continue
                    ext = os.path.splitext(fname)[1].lower()
                    # Exempt the scanner's special-case filenames — they're
                    # searchable despite an empty/missing extension. Without
                    # this exemption they would land in Unsupported.
                    if ext not in searchable_exts and lower not in special_searchable:
                        buckets["Unsupported file type"].append(
                            (filepath, fsize, ext or "(no extension)"))
                        continue
                    if fsize == 0:
                        buckets["Empty (0 bytes)"].append((filepath, 0, "zero bytes"))
                        continue
                    if max_bytes is not None and fsize > max_bytes:
                        buckets["Oversized"].append(
                            (filepath, fsize, f"{fsize / (1024*1024):.1f} MB"))
                        continue
                    # File passed every check — searchable.
                    searchable_count += 1
        except Exception:
            pass

        # Sort each bucket by filename ascending (case-insensitive).
        for cat in buckets:
            buckets[cat].sort(key=lambda x: os.path.basename(x[0]).lower())

        unsearchable_count = sum(len(buckets[cat]) for cat in buckets)

        results = {
            "folder": folder,
            "recursive": recursive,
            "max_file_size_mb": max_file_size_mb,
            "use_ocr": use_ocr,
            "total_files": total_files,
            "searchable_count": searchable_count,
            "unsearchable_count": unsearchable_count,
            "buckets": buckets,
        }
        self.after(0, self._unsearchable_files_finished, results)

    def _unsearchable_files_finished(self, results):
        """Handle Unsearchable Files scan completion."""
        self.status_label.configure(
            text=(
                f"Scanned {results['total_files']} file(s): "
                f"{results['searchable_count']} searchable, "
                f"{results['unsearchable_count']} unsearchable."
            ),
            text_color=("blue", "#66BBFF"))
        self._show_unsearchable_files_popup(results)

    def _show_unsearchable_files_popup(self, results):
        """Display the unsearchable-files categorization with per-bucket lists."""
        import tkinter as tk
        fmt = self._format_file_size
        buckets = results["buckets"]
        total = results["total_files"]
        searchable = results["searchable_count"]
        unsearchable = results["unsearchable_count"]
        pct = (unsearchable / total * 100) if total else 0

        popup, _dark = self._themed_toplevel()
        popup.withdraw()  # hidden during widget setup; centered + shown at end
        popup.title("Unsearchable Files")
        popup.resizable(True, True)

        # Header
        tk.Label(
            popup,
            text=(
                f"Unsearchable Files — {unsearchable} of {total} "
                f"({pct:.1f}%); {searchable} searchable"
            ),
            font=("TkDefaultFont", 13, "bold"),
        ).pack(pady=(10, 2))
        recursive_str = " (including subfolders)" if results["recursive"] else ""
        tk.Label(
            popup,
            text=f"{results['folder']}{recursive_str}",
            font=("TkDefaultFont", 10), fg="gray",
        ).pack(pady=(0, 2))
        tk.Label(
            popup,
            text="To analyze a different folder, use Browse on the main page to select it, then reopen this tool.",
            font=("TkDefaultFont", 10, "italic"), fg="gray",
        ).pack(pady=(0, 5))

        # Scrollable text area showing summary + per-category file lists.
        text_frame = tk.Frame(popup)
        text_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        vbar = tk.Scrollbar(text_frame, orient="vertical")
        vbar.pack(side="right", fill="y")
        txt = tk.Text(
            text_frame, font=("Courier", 11), wrap="none",
            yscrollcommand=vbar.set,
            bg="#2b2b2b" if _dark else "white",
            fg="white" if _dark else "black",
            borderwidth=1, relief="sunken", highlightthickness=0,
        )
        vbar.config(command=txt.yview)
        txt.pack(side="left", fill="both", expand=True)

        # Summary table.
        label_width = max(len(c) for c in self._UNSEARCHABLE_CATEGORIES)
        txt.insert("end", "Summary (by reason)\n")
        txt.insert("end", "─" * (label_width + 30) + "\n")
        for cat in self._UNSEARCHABLE_CATEGORIES:
            count = len(buckets[cat])
            cat_pct = (count / total * 100) if total else 0
            txt.insert("end",
                f"{cat:<{label_width}}  {count:>6} file(s) ({cat_pct:>4.1f}%)\n")
        txt.insert("end", "\n")
        txt.insert("end",
            "Tip: 'Empty (0 bytes)' and the password-protected files reported by\n"
            "the Protected Files tool also count as unsearchable. They are listed\n"
            "here for completeness; use the dedicated tools for focused views.\n\n")

        # Per-category file lists.
        for cat in self._UNSEARCHABLE_CATEGORIES:
            files = buckets[cat]
            txt.insert("end", f"── {cat} ({len(files)} file(s)) ──\n")
            if not files:
                txt.insert("end", "    (none)\n")
            else:
                for filepath, fsize, reason in files:
                    rel = os.path.relpath(filepath, results["folder"])
                    size_str = fmt(fsize) if fsize else ""
                    if size_str:
                        txt.insert("end", f"    {size_str:>10}  {reason:<20}  {rel}\n")
                    else:
                        txt.insert("end", f"    {'':>10}  {reason:<20}  {rel}\n")
            txt.insert("end", "\n")
        txt.configure(state="disabled")

        # Save Report — anchored to the far left in its own row.
        save_row = tk.Frame(popup)
        save_row.pack(fill="x", padx=10, pady=(5, 0))
        save_btn = ctk.CTkButton(
            save_row, text="Save Report", width=100,
            command=lambda: self._save_unsearchable_files_report(results),
            font=ctk.CTkFont(size=12),
        )
        save_btn.pack(side="left")
        Tooltip(save_btn, "Save this categorization as a plain text file")

        # Close — centered, on its own row below Save Report.
        close_row = tk.Frame(popup)
        close_row.pack(pady=(5, 10))
        ctk.CTkButton(
            close_row, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=popup.destroy, font=ctk.CTkFont(size=12),
        ).pack()
        self._apply_dark_theme(popup)
        self._center_popup_on_main(popup, 920, 600)

    def _save_unsearchable_files_report(self, results):
        """Save the unsearchable-files categorization as a plain-text report."""
        from datetime import datetime
        from tkinter import filedialog
        fmt = self._format_file_size
        buckets = results["buckets"]
        total = results["total_files"]
        searchable = results["searchable_count"]
        unsearchable = results["unsearchable_count"]
        pct = (unsearchable / total * 100) if total else 0

        default = os.path.join(
            results["folder"],
            "peekdocs_unsearchable_files.txt",
        )
        path = filedialog.asksaveasfilename(
            title="Save Unsearchable Files Report",
            initialfile=os.path.basename(default),
            initialdir=os.path.dirname(default),
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("All Files", "*.*")],
        )
        if not path:
            return
        try:
            lines = []
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"Unsearchable Files — {now_str}")
            lines.append(f"Folder: {results['folder']}")
            lines.append(f"Recursive: {results['recursive']}")
            lines.append(f"Max File Size: {results['max_file_size_mb']} MB (0 = no limit)")
            lines.append(f"OCR: {results['use_ocr']}")
            lines.append(f"Total files: {total}")
            lines.append(f"Searchable: {searchable}")
            lines.append(f"Unsearchable: {unsearchable} ({pct:.1f}%)")
            lines.append("")
            label_width = max(len(c) for c in self._UNSEARCHABLE_CATEGORIES)
            lines.append("Summary (by reason)")
            lines.append("─" * (label_width + 30))
            for cat in self._UNSEARCHABLE_CATEGORIES:
                count = len(buckets[cat])
                cat_pct = (count / total * 100) if total else 0
                lines.append(f"{cat:<{label_width}}  {count:>6} file(s) ({cat_pct:>4.1f}%)")
            lines.append("")
            for cat in self._UNSEARCHABLE_CATEGORIES:
                files = buckets[cat]
                lines.append(f"── {cat} ({len(files)} file(s)) ──")
                if not files:
                    lines.append("    (none)")
                else:
                    for filepath, fsize, reason in files:
                        rel = os.path.relpath(filepath, results["folder"])
                        size_str = fmt(fsize) if fsize else ""
                        if size_str:
                            lines.append(f"    {size_str:>10}  {reason:<20}  {rel}")
                        else:
                            lines.append(f"    {'':>10}  {reason:<20}  {rel}")
                lines.append("")
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            self.status_label.configure(
                text=f"Report saved: {os.path.basename(path)}",
                text_color="green",
            )
        except OSError as exc:
            self._show_error(f"Could not write report: {exc}")

    # ── Search History ───────────────────────────────────────



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



    def _show_sensitive_category_files(self, files_data, category, parent, regex=None):
        """Show files for a specific sensitive data category.

        If regex is provided, the View Text button opens the extracted-text
        view with that regex highlighted (so the user sees the actual
        matches for this category, not whatever is in the main search bar).
        """
        import tkinter as tk
        import subprocess, sys

        popup, _dark = self._themed_toplevel(parent)
        popup.title(f"Regex Search — Files containing: {category}")
        popup.resizable(True, True)
        popup.geometry("750x480")
        parent.update_idletasks()
        x = parent.winfo_rootx() + 25
        y = parent.winfo_rooty() + 25
        popup.geometry(f"+{x}+{y}")

        header_frame = tk.Frame(popup)
        header_frame.pack(fill="x", padx=15, pady=(10, 5))
        tk.Label(
            header_frame, text=f"{category} — {len(files_data)} file(s)",
            font=("TkDefaultFont", 13, "bold"),
        ).pack(side="left", expand=True)
        ctk.CTkButton(
            header_frame, text="?", width=30, height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#1565C0", text_color="white",
            hover_color="#0D47A1",
            corner_radius=15,
            command=lambda: self._show_category_files_help(popup),
        ).pack(side="right")
        tk.Label(
            popup, text="Matches are pattern-based and may include false positives or missed matches.",
            font=("TkDefaultFont", 10), fg="gray",
        ).pack(fill="x", padx=15, pady=(0, 2))

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
                from peekdocs.gui._helpers import safe_open_file
                warning = safe_open_file(path)
                if warning:
                    self._show_error(warning)
            except Exception:
                pass

        listbox.bind("<Double-1>", _on_double_click)

        tk.Label(
            popup, text="Single-click to select a file (above), then click View Text below to review the "
                        "matches with line numbers highlighted. "
                        "Or, double-click a file (above) to open it in its default application.",
            font=("TkDefaultFont", 10), fg="gray", wraplength=700, justify="center",
        ).pack(padx=10)

        def _view_text():
            sel = listbox.curselection()
            if not sel or sel[0] not in file_paths:
                popup.bell()
                self._show_error("Please select a file from the list first.")
                return
            path = file_paths[sel[0]]
            if not os.path.exists(path):
                self._show_error(f"File not found: {path}")
                return
            self._show_file_text_view(
                path, os.path.basename(path),
                highlight_regex_pattern=regex,
                highlight_label=category,
            )

        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=(5, 10))

        view_btn = tk.Label(
            btn_frame, text="View Text (with line numbers)",
            font=("TkDefaultFont", 13, "bold"),
            bg="#FF9800", fg="white",
            relief="raised", borderwidth=2,
            padx=20, pady=8, cursor="hand2",
        )
        view_btn.pack(side="left", padx=5)
        view_btn.bind("<Button-1>", lambda e: _view_text())
        view_btn.bind("<Enter>", lambda e: view_btn.configure(bg="#F57C00"))
        view_btn.bind("<Leave>", lambda e: view_btn.configure(bg="#FF9800"))

        ctk.CTkButton(
            popup, text="Close", width=80, font=ctk.CTkFont(size=12),
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=popup.destroy,
        ).pack(pady=(0, 10))

        self._apply_dark_theme(popup)


    def _show_category_files_help(self, parent):
        """Show help for the Regex Search category files popup."""
        import tkinter as tk
        help_win, _dark = self._themed_toplevel(parent)
        help_win.title("Regex Search — View Files — Help")
        help_win.geometry("650x520")
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
        txt.tag_configure("heading_red", font=("TkDefaultFont", 13, "bold"),
                          spacing1=8, spacing3=4, foreground="red")

        txt.tag_configure("toc_title", font=("TkDefaultFont", 14, "bold"),
                          spacing1=5, spacing3=8)
        txt.tag_configure("toc_item", font=("TkDefaultFont", 11), lmargin1=20,
                          lmargin2=20, foreground="#999999" if ctk.get_appearance_mode() == "Dark" else "gray40")
        txt.tag_configure("toc_item_red", font=("TkDefaultFont", 11, "bold"), lmargin1=20,
                          lmargin2=20, foreground="red")

        def h(text):
            txt.insert("end", text + "\n", "heading")
        def h_red(text):
            txt.insert("end", text + "\n", "heading_red")
        def b(text):
            txt.insert("end", text + "\n", "body")
        def blank():
            txt.insert("end", "\n")

        txt.insert("end", "TABLE OF CONTENTS\n", "toc_title")
        for section in [
            "View Files",
            "What You Can Do",
            "No Files Are Written",
            "False Positives",
        ]:
            txt.insert("end", f"\u2022 {section}\n", "toc_item")
        for section in [
            "Disclaimer",
        ]:
            txt.insert("end", f"\u2022 {section}\n", "toc_item_red")
        txt.insert("end", "\n")

        h("VIEW FILES")
        b("This popup lists every file where the Regex Search found")
        b("matches for this category. Each row shows:")
        blank()
        b("\u2022 The filename")
        b("\u2022 How many matches were found in that file")
        b("\u2022 The line numbers where matches appear (up to 20)")
        blank()

        h("WHAT YOU CAN DO")
        b("\u2022 Double-click a file to open it in its default")
        b("  application so you can review or edit it directly.")
        blank()
        b("\u2022 Select a file and click View Text to see the")
        b("  extracted text with line numbers and matches")
        b("  highlighted in yellow. This lets you see exactly")
        b("  what the Regex Search detected, in context, without")
        b("  opening the original file.")
        blank()

        h("FALSE POSITIVES")
        b("Pattern-based detection produces false positives. Use")
        b("View Text to review each finding in context before")
        b("taking action.")
        blank()

        h_red("DISCLAIMER")
        b("Regex Search is a pattern-matching tool. Results are heuristic")
        b("and may include false positives or missed matches. Users remain")
        b("solely responsible for how they use and interpret its output.")
        blank()

        txt.configure(state="disabled")

        ctk.CTkButton(
            help_win, text="Close", width=80, font=ctk.CTkFont(size=12),
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"), command=help_win.destroy,
        ).pack(pady=(5, 10))
        self._apply_dark_theme(help_win)


