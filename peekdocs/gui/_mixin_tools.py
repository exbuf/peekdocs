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

        self._apply_dark_theme(popup)


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

            _SKIP_PREFIXES = RESULT_FILE_PREFIXES + (
                "peekdocs_report_", "peekdocs_accumulated_",
            )
            _SKIP_NAMES = {".peekdocs_collection.json", ".peekdocs.db",
                           ".peekdocs.db-wal", ".peekdocs.db-shm",
                           ".peekdocsrc", "peekdocs_errors.log"}

            for root, dirs, files in walker:
                for fname in files:
                    if fname in _SKIP_NAMES or any(fname.startswith(p) for p in _SKIP_PREFIXES):
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
            btn_frame, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=popup.destroy, font=ctk.CTkFont(size=12),
        ).pack()
        self._apply_dark_theme(popup)

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
                 "fill in your values, then click Apply. Apply configures the main search bar and Advanced Search Options for you \u2014 "
                 "then click Search on the main screen. Close this window at any time to cancel \u2014 nothing changes until you click Apply.",
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
        b("  sudo apt install tesseract-ocr. See the User Guide")
        b("  'Prerequisites' section for full details.")
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

    def _show_regex_builder_help(self, parent):
        """Help popup for the Regex Wizard (the picker invoked by
        `_open_search_wizard`).

        Distinct from `_show_search_wizard_help`, which documents the
        search-type wizard (the category-cards popup behind the
        main-screen Search Wizard button). This one documents the
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
        b("Don't confuse it with the main-screen Search Wizard button —")
        b("that one opens the category-cards search-type wizard, and")
        b("one of its cards (\"Regex Wizard\") leads here.")
        blank()
        b("Six categories ship out of the box, 35 patterns total:")
        e("  Dates        — ISO, US, EU, month-name, weekday, etc.")
        e("  Money        — USD, EUR, generic currency amounts")
        e("  Identifiers  — UUID, hex, ISBN, DOI, semver, JIRA ticket")
        e("  Contacts     — email, phone (US and international), URL")
        e("  Code patterns — TODO/FIXME, env var, Markdown link, ANSI")
        e("  Networking   — IPv4, IPv6, MAC address, hex color")
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
        e("  Main search bar (Search Wizard button on the main screen)")
        e("  Regex Tester       (Tools → Regex Tester → Pick from Wizard…)")
        e("  Regex Search popup (Regex Search → Pick from Wizard…)")
        b("Pick OR if you're unsure. It's the safe default.")
        blank()

        h("WHERE AND APPLIES — AND WHERE IT DOESN'T")
        b("AND mode only works for the main search bar, because that's")
        b("the only context that parses multi-term shapes:")
        blank()
        b("✓ Main search bar (Search Wizard button on the main screen)")
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

    # ── Mutual exclusion for search modes ────────────────────



    def _show_search_options_help(self):
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
        b("Search Options and click 'Save Settings'. Your choices are")
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
            "Standard Search (green button) vs Regex Search",
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
        b("After a search, click the orange Matched Files button on the status")
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
        b("Standard Search (green button, main search bar \u2014 next to Step 2):")
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
        e("  Search for a word or phrase            Standard Search (green button)")
        e("  Use AND, Boolean, fuzzy, proximity     Standard Search (green button)")
        e("  Search with one regex pattern           Standard Search (green button)")
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
        help_win, _dark = self._themed_toplevel(self.advanced_window or self)
        help_win.title("Advanced Search Options — Help")
        help_win.geometry("750x620")
        help_win.resizable(True, True)
        if self.advanced_window:
            help_win.transient(self.advanced_window)

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
        b("Tip: Use the Wizard button for pre-built regex patterns.")
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
        b("Cap the number of matches written to report files. Default: 1000.")
        b("The total count is always accurate — only the report is capped.")
        b("The Matched Files list is also affected — when capped, only files")
        b("with matches within the cap are shown. Set to 0 for unlimited.")
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
        b("This includes all settings on this Advanced Search Options screen")
        b("and on the main screen (search terms, folder, recursive, AND/OR")
        b("mode, whole word, etc.). These become the defaults every time you")
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
        b("Clear all fields and reset to defaults for the current session.")
        b("Does not modify the saved config file (~/.peekdocsrc).")
        blank()

        s("Restore Factory Settings")
        b("Delete ~/.peekdocsrc entirely and return all settings to factory")
        b("defaults. The app will start fresh next time as if newly installed.")
        b("Your documents, search history, and personal files are not affected.")
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
        blank()
        b("Click Reset All Fields (the red button at the bottom) to")
        b("clear everything and start fresh.")
        blank()
        b("If Use Index is checked on the main screen, try unchecking")
        b("it and searching directly. A stale index may not contain")
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
        """Show help for the Save Search and Load Search buttons."""
        import tkinter as tk
        help_win, _dark = self._themed_toplevel()
        help_win.title("Save Search & Load Search \u2014 Help")
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
            "What Save Search Does",
            "What Load Search Does",
            "Where Saved Searches Are Stored",
            "Editing a Saved Search",
            "Deleting a Saved Search",
            "Sharing Saved Searches",
            "Tips",
        ]:
            txt.insert("end", f"\u2022 {section}\n", "toc_item")
        txt.insert("end", "\n")

        h("WHAT SAVE SEARCH DOES")
        b("Save Search takes everything you currently have configured")
        b("on the main screen \u2014 search terms, mode (AND/OR/Boolean/")
        b("regex/fuzzy/wildcard/whole word), inverse, file type filters,")
        b("exclude terms, proximity, range filters, context lines,")
        b("recursive, OCR, max file size, and use-index \u2014 and stores")
        b("it under a name you choose.")
        blank()
        b("Once saved, you can reload the exact same configuration")
        b("later with one click from Load Search. Nothing is \"locked")
        b("in\" \u2014 you can always edit and re-save it.")
        blank()
        b("Saving does NOT run the search. If you want to verify that")
        b("the search works the way you expect, click Run Search")
        b("first, check the results, then click Save Search.")
        blank()

        h("WHAT LOAD SEARCH DOES")
        b("Load Search \u25bc opens a popup listing every saved search in")
        b("the current folder's collection. Click one to load it back")
        b("into the main screen \u2014 the search terms and all options")
        b("are restored exactly as they were when you saved.")
        blank()
        b("After loading, you can:")
        b("\u2022 Click Run Search to execute it as-is")
        b("\u2022 Modify any field and click Run Search to try a variation")
        b("\u2022 Click Save Search to overwrite the saved version (use")
        b("  the same name) or save it as a new one (use a new name)")
        b("\u2022 Delete the saved search from the Load Search popup")
        blank()
        b("Saving does NOT run the search. To verify a search works")
        b("the way you expect, click Run Search first, check the")
        b("results, then click Save Search.")
        blank()

        h("WHERE SAVED SEARCHES ARE STORED")
        b("Saved searches live in a file called .peekdocs_collection.json")
        b("inside the search folder itself. Each folder has its own")
        b("collection \u2014 the saved searches for ~/Documents/Contracts are")
        b("separate from those in ~/Documents/HR_Files. When you switch")
        b("folders on the main screen, the Load Search dropdown")
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
        b("1. Click Load Search \u25bc and pick the one you want to edit")
        b("2. The search bar and Advanced Search Options are filled in")
        b("   with the saved values")
        b("3. Change whatever you need to (terms, filters, options)")
        b("4. Click Run Search to verify the new version works")
        b("5. Click Save Search and give it the SAME name \u2014 you'll")
        b("   be asked to confirm overwriting the existing entry")
        blank()
        b("If you give it a new name instead, you'll end up with two")
        b("saved searches: the original and your modified version.")
        blank()

        h("DELETING A SAVED SEARCH")
        b("Open Load Search \u25bc. Each entry in the popup has a Delete")
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
            "Line Numbers",
            "Why Some Files May Be Missing",
        ]:
            txt.insert("end", f"\u2022 {section}\n", "toc_item")
        txt.insert("end", "\n")

        h("WHAT THIS POPUP SHOWS")
        b("You opened this popup by clicking the orange Matched Files")
        b("button on the status line at the bottom of the main window.")
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
        b("button on the status line at the bottom of the main window.")
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
        b("on the main screen is automatically unchecked and grayed out.")
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

        txt.configure(state="disabled")
        self._apply_dark_theme(help_win)

    # ── Search Suites ──────────────────────────────────────────────

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
        win.geometry("880x640")

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
        tk.Label(
            win,
            text="Group saved searches and run them together. Results go into a single combined report. "
                 "Suites are saved in the Search Folder shown below. To change it, update the Search Folder on the main page, then reopen Search Suites.",
            font=_sf(10), fg="gray", wraplength=850, justify="left", anchor="w",
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
                self._show_error("No saved searches available to add.\n\nSave a search first (main screen → Save button).")
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

            # Pack the Add button BEFORE the listbox so its row is reserved
            # at the bottom; otherwise the listbox's expand=True grows to
            # fill the toplevel and pushes the button off the visible area.
            ctk.CTkButton(pick_win, text="Add", width=80, font=ctk.CTkFont(size=12),
                          command=_do_add).pack(side="bottom", pady=(0, 10))

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

        # TXT and DOCX are always generated
        tk.Label(output_frame, text="TXT \u2713  DOCX \u2713", font=_sf(10), fg="gray").pack(side="left", padx=(0, 10))

        # Seed each checkbox from ~/.peekdocsrc so the user's last selection
        # persists across popup invocations. Saved on every toggle.
        try:
            from peekdocs.cli import _load_config as _load_cfg_suite
            _suite_cfg = _load_cfg_suite()
        except Exception:
            _suite_cfg = {}
        _suite_html_var = tk.BooleanVar(value=bool(_suite_cfg.get("suite_html", False)))
        _suite_csv_var = tk.BooleanVar(value=bool(_suite_cfg.get("suite_csv", False)))
        _suite_json_var = tk.BooleanVar(value=bool(_suite_cfg.get("suite_json", False)))
        _suite_pdf_var = tk.BooleanVar(value=bool(_suite_cfg.get("suite_pdf", False)))

        def _save_suite_fmt(key, var):
            self._save_ui_preference(key, bool(var.get()))

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
        x = self.winfo_rootx() + (self.winfo_width() - 880) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 640) // 2
        win.geometry(f"880x640+{x}+{y}")
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
        self._preview_count_label.configure(text="")
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
                    text=f"Suite [{i}/{t}] {n}..."
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
                import shlex as _shlex
                try:
                    search_terms = _shlex.split(terms_str) if terms_str else []
                except ValueError:
                    search_terms = terms_str.split() if terms_str else []
                expr = params.get("expression") if params.get("expression") else None
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

            # Auto-redirect to a safe local folder if the search folder is
            # cloud-synced. `folder` is the search folder (read-only here);
            # `output_folder` is where suite reports get written.
            from peekdocs.gui._helpers import check_cloud_folder, get_safe_output_dir
            cloud_warning = check_cloud_folder(folder)
            output_folder = get_safe_output_dir() if cloud_warning else folder

            # Generate combined suite reports
            # Set restrictive file permissions if enabled
            import peekdocs.reporter as _reporter_mod
            _reporter_mod.restrict_permissions = (
                getattr(self, "restrict_permissions_var", None)
                and self.restrict_permissions_var.get() == "on"
            )

            txt_path = os.path.join(output_folder, "peekdocs_suite_results.txt")
            docx_path = os.path.join(output_folder, "peekdocs_suite_results.docx")
            _fmts = suite_formats or {}
            write_suite_txt_report(txt_path, suite_name, sections)
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
                    with open(csv_path, "w", newline="", encoding="utf-8") as cf:
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
        self._suites_btn.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("search_suites_label"), fg_color="#76BA1B", hover_color="#76BA1B",
                                   text_color="white", command=self._show_search_suites)

        import re as _re_fin

        # Unique file count across all sub-searches. The previous formula
        # sum(s["matched_file_count"]) double-counted any file that hit
        # in more than one sub-search (e.g. a file matching both TODO
        # and FIXME counted twice). The orange Matched Files button and
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
            link_text = f"{unique_matched_count} Matched File(s)"
            self._matched_files_link.configure(text=link_text, fg_color="#FF6B35", hover_color="#E55A2B")
            self._matched_files_link.pack(side="left", padx=(5, 0))

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

        # Show results in preview
        if hasattr(self, "preview_frame"):
            self.preview_frame.grid()
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

    def _cancel_suite(self):
        """Cancel a running suite search."""
        self._suite_cancelled = True
        self._suite_elapsed_active = False
        self.search_start_time = None
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        # Restore the SUITES button (the one we flipped to Cancel at run-start).
        self._suites_btn.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("search_suites_label"), fg_color="#76BA1B", hover_color="#76BA1B",
                                   text_color="white", command=self._show_search_suites)
        self.status_label.configure(text="Suite cancelled.", text_color=("blue", "#66BBFF"))

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
        n("combined report. TXT and DOCX are always generated. You can")
        n("also check HTML, CSV, JSON, or PDF in the suite popup to get")
        n("additional output formats. These checkboxes are independent")
        n("from the ones in Advanced Search Options.\n")

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
            add("Fix missing dependencies with: pip install --upgrade peekdocs", "warn")

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
                 "\u2014 peekdocs does not validate correctness. Regex entries persist between invocations.",
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
                mc_win.destroy()
                win.destroy()
                self._run_regex_search_per_pattern(
                    _active, _combined, _folder, _recursive,
                    _screen_only, collection_name=_cn_label,
                )

            _mc_btns = tk.Frame(mc_win)
            _mc_btns.pack(pady=(0, 12))
            ctk.CTkButton(
                _mc_btns, text="Run Selected", width=130,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#FF9800", hover_color="#F57C00",
                command=_do_run_multi,
            ).pack(side="left", padx=5)
            ctk.CTkButton(
                _mc_btns, text="Cancel", width=90,
                font=ctk.CTkFont(size=12),
                fg_color="transparent", text_color=("gray30", "gray70"),
                hover_color=("gray90", "gray25"),
                command=mc_win.destroy,
            ).pack(side="left", padx=5)

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
            win.destroy()
            self._run_regex_search_per_pattern(
                active, combined, rs_folder, rs_recursive, screen_only,
                collection_name=collection_name,
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


    def _run_regex_search_per_pattern(self, active_patterns, combined_regex, folder, recursive, screen_only=True, collection_name=""):
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

        mode_label = "screen only, no reports" if screen_only else "with reports"
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

            # Write reports in the background thread (not on GUI thread)
            if not screen_only and all_matches and not getattr(self, "_regex_search_cancelled", False):
                self.after(0, lambda: self.status_label.configure(
                    text="Regex Search \u2014 writing reports...",
                    text_color=("blue", "#66BBFF"),
                ))
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
                    command_str = "Regex Search: " + ", ".join(f"{n} ({r})" for n, r in active_patterns)
                    output_path = os.path.join(folder, "peekdocs_regex_results.txt")
                    docx_path = os.path.join(folder, "peekdocs_regex_results.docx")
                    write_txt_report(
                        output_path, all_matches,
                        sorted(_files_searched_set),
                        search_terms, command_str,
                        "ANY", False, [], False, False, True, False,
                        elapsed, max(1, os.cpu_count() // 2), os.cpu_count() or 1,
                        recursive=recursive, use_index=False,
                    )
                    result_doc = write_docx_report(
                        docx_path, output_path,
                        search_terms=search_terms,
                        use_regex=True,
                    )
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
                self._regex_search_btn.configure(
                    state="normal", fg_color="#FF9800", hover_color="#FF9800",
                    text_color="white", text=__import__("peekdocs.i18n", fromlist=["t"]).t("run_regex_search_label"),
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
                # and actively misleading. Regex Search writes only TXT
                # and DOCX, so the CSV / JSON / PDF / HTML buttons will
                # flip red (no file); the Advanced Search Options output-
                # format checkboxes do NOT apply to Regex Search, which
                # is called out in the Getting Started step 4 disclaimer
                # and in the format-checkbox tooltips.
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
        self.status_label.configure(text="Regex Search cancelled.", text_color=("blue", "#66BBFF"))
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        if hasattr(self, "_regex_search_btn"):
            self._regex_search_btn.configure(
                state="normal", fg_color="#FF9800", hover_color="#FF9800",
                text_color="white", text="Run Regex Search",
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

        def _load_from_file():
            path = filedialog.askopenfilename(parent=win)
            if not path:
                return
            try:
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
        b("Save Collection As (ADD mode). Larger collections run")
        b("from the CLI with peekdocs --regex-collection NAME (every")
        b("pattern, no cap) or from this popup via Run Multiple")
        b("Collections… at the bottom (every pattern in every picked")
        b("collection, no cap).")
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
        b("and vs Search Suites, see 'Standard Search (green button) vs")
        b("Regex Search' and 'Regex Search vs Search Suites' in")
        b("the main screen ? help.")
        blank()
        b("Note: Regex Search results appear in a separate popup window,")
        b("not in the main Results Preview pane. This is different from")
        b("Standard Search, which shows results in the Results Preview")
        b("with an orange Matched Files button on the status line. The")
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
        b("When 'Do not save regex match contents to reports' is")
        b("UNCHECKED (normal mode), Regex Search triggers a standard")
        b("search and respects most Advanced Search Options settings:")
        blank()
        b("\u2022 Max Matches, Max File Size, Context Lines (Before/After)")
        b("\u2022 Output formats (CSV, JSON, PDF, HTML)")
        b("\u2022 File type filters, Exclude terms")
        b("\u2022 Save report as, Delete on Close, Notify on Search Complete")
        blank()
        b("These settings are overridden by the Regex Search popup:")
        blank()
        b("\u2022 Folder \u2014 uses the popup's folder, not the main screen")
        b("\u2022 Recursive \u2014 uses the popup's checkbox")
        b("\u2022 Regex \u2014 forced on")
        b("\u2022 Fuzzy / Wildcard \u2014 forced off")
        b("\u2022 Index \u2014 forced off (always scans files directly)")
        blank()
        b("When 'Do not save regex match contents to reports' is")
        b("CHECKED (screen-only mode), the search runs through the")
        b("API and none of the Advanced Search Options apply. Only")
        b("the popup's folder and Recursive setting are used.")
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
