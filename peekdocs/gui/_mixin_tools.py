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
        popup.title("File Inventory")
        popup.resizable(True, True)
        popup.geometry("780x580")
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 780) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 580) // 2
        popup.geometry(f"+{x}+{y}")

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

        # Buttons
        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=(5, 10))

        save_btn = ctk.CTkButton(
            btn_frame, text="Save Report", width=100,
            command=lambda: self._save_inventory_report(results),
            font=ctk.CTkFont(size=12),
        )
        save_btn.pack(side="left", padx=5)
        Tooltip(save_btn, "Save this inventory as a plain text file")

        close_btn = ctk.CTkButton(
            btn_frame, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=popup.destroy,
            font=ctk.CTkFont(size=12),
        )
        close_btn.pack(side="left", padx=5)

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
        popup.title("Password-Protected Files")
        popup.resizable(True, True)
        popup.geometry("800x500")
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 800) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 500) // 2
        popup.geometry(f"+{x}+{y}")

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

            _SKIP_PREFIXES = ("peekdocs_results", "peekdocs_report_",
                              "peekdocs_accumulated_",
                              "peekdocs_suite_results")
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
        popup.title("Duplicate Files")
        popup.resizable(True, True)
        popup.geometry("820x550")
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 820) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 550) // 2
        popup.geometry(f"+{x}+{y}")

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

        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=(5, 10))

        if groups:
            save_btn = ctk.CTkButton(
                btn_frame, text="Save Report", width=100,
                command=lambda: self._save_duplicate_report(results),
                font=ctk.CTkFont(size=12),
            )
            save_btn.pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=popup.destroy, font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=5)
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
        popup.title("Largest Files")
        popup.resizable(True, True)
        popup.geometry("800x500")
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 800) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 500) // 2
        popup.geometry(f"+{x}+{y}")

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
        popup.title("Empty Files")
        popup.resizable(True, True)
        popup.geometry("750x450")
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 750) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 450) // 2
        popup.geometry(f"+{x}+{y}")

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
        popup.title("Recent Changes")
        popup.resizable(True, True)
        popup.geometry("820x550")
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 820) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 550) // 2
        popup.geometry(f"+{x}+{y}")

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



    def _start_sensitive_scan(self):
        """Show a configuration popup for the sensitive data scan."""
        import tkinter as tk
        from peekdocs.sensitive_patterns import SENSITIVE_PATTERNS, SEVERITY_COLORS

        if self.process is not None:
            self._show_error("A search is already running.")
            return

        win, _dark = self._themed_toplevel()
        win.title("PII Scan — Select Categories")
        win.resizable(False, False)
        win.transient(self)
        # No grab_set() — the help window (?) must remain interactive
        # alongside this popup so users can copy regex examples and
        # paste them into the Custom Pattern fields.
        # Raise on focus so this window comes to front when clicked
        # anywhere (macOS doesn't auto-reorder transient siblings).
        win.bind("<FocusIn>", lambda e: win.lift())

        header = tk.Frame(win)
        header.pack(fill="x", padx=15, pady=(12, 4))
        tk.Label(
            header, text="Select which categories to scan for:",
            font=("TkDefaultFont", 13, "bold"),
        ).pack(side="left")
        ctk.CTkButton(
            header, text="?", width=30, font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._show_pii_scan_help(win),
        ).pack(side="right")

        # Use saved PII folder: in-memory first, then config file
        _saved_pii_folder = getattr(self, "_last_pii_folder", None)
        if not _saved_pii_folder:
            try:
                from peekdocs.cli import _load_config
                _saved_pii_folder = _load_config().get("pii_scan_folder")
            except Exception:
                pass
        # Recursive checkbox — inside the folder bar, independent from main search
        from peekdocs.cli import _load_config as _lc_pii
        _pii_recursive_saved = _lc_pii().get("pii_scan_recursive", True)
        _pii_recursive_var = tk.BooleanVar(value=_pii_recursive_saved)
        _pii_folder_label = self._add_folder_bar(
            win, "",
            initial_folder=_saved_pii_folder,
            recursive_var=_pii_recursive_var)

        # Load saved selections (default: all enabled)
        if not hasattr(self, "_pii_scan_enabled"):
            from peekdocs.cli import _load_config
            config = _load_config()
            saved = config.get("pii_scan_categories")
            if isinstance(saved, list):
                self._pii_scan_enabled = set(saved)
            else:
                self._pii_scan_enabled = {cat for cat, _, _, _ in SENSITIVE_PATTERNS}

        # Load saved dollar amount range (defaults to $10,000 – $999,999,999)
        from peekdocs.cli import _load_config
        _cfg = _load_config()
        saved_min = _cfg.get("pii_scan_dollar_min", "10000")
        saved_max = _cfg.get("pii_scan_dollar_max", "999999999")

        # Checkboxes for each pattern
        check_vars = []
        dollar_min_entry = None
        dollar_max_entry = None
        checks_frame = tk.Frame(win)
        checks_frame.pack(fill="x", padx=20)

        for i, (category, _regex, severity, description) in enumerate(SENSITIVE_PATTERNS):
            var = tk.BooleanVar(value=(category in self._pii_scan_enabled))
            check_vars.append(var)
            row = tk.Frame(checks_frame)
            row.pack(fill="x", pady=2)

            sev = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["info"])
            tk.Label(
                row, text=f" {sev['label']} ", font=("TkDefaultFont", 9, "bold"),
                bg=sev["bg"], fg=sev["fg"], width=10,
            ).pack(side="left", padx=(0, 8))

            cb = tk.Checkbutton(row, variable=var, text=category, font=("TkDefaultFont", 12))
            cb.pack(side="left")

            if category == "Dollar Amounts":
                # Inline Min/Max entries for the dollar amount range
                tk.Label(
                    row, text="  Min $", font=("TkDefaultFont", 11),
                ).pack(side="left", padx=(10, 2))
                dollar_min_entry = ctk.CTkEntry(row, width=100, font=ctk.CTkFont(size=11))
                dollar_min_entry.insert(0, str(saved_min))
                dollar_min_entry.pack(side="left")
                tk.Label(
                    row, text="  Max $", font=("TkDefaultFont", 11),
                ).pack(side="left", padx=(10, 2))
                dollar_max_entry = ctk.CTkEntry(row, width=100, font=ctk.CTkFont(size=11))
                dollar_max_entry.insert(0, str(saved_max))
                dollar_max_entry.pack(side="left")
            else:
                tk.Label(
                    row, text=f"  {description}", font=("TkDefaultFont", 10), fg="gray",
                ).pack(side="left")

        # Select All / Deselect All
        toggle_frame = tk.Frame(win)
        toggle_frame.pack(pady=(8, 4))

        def _select_all():
            for v in check_vars:
                v.set(True)

        def _deselect_all():
            for v in check_vars:
                v.set(False)

        ctk.CTkButton(toggle_frame, text="Select All", width=80, font=ctk.CTkFont(size=12), command=_select_all).pack(side="left", padx=5)
        ctk.CTkButton(toggle_frame, text="Deselect All", width=80, font=ctk.CTkFont(size=12), command=_deselect_all).pack(side="left", padx=5)

        # ── Advanced: user-supplied custom regex patterns (2 rows) ──
        from tkinter import ttk as _ttk
        _ttk.Separator(win, orient="horizontal").pack(fill="x", padx=15, pady=(10, 4))

        custom_outer = tk.Frame(win)
        custom_outer.pack(fill="x", padx=20, pady=(0, 2))
        tk.Label(
            custom_outer,
            text="Advanced \u2014 Custom Patterns (optional)",
            font=("TkDefaultFont", 11, "bold"),
        ).pack(anchor="w")
        tk.Label(
            custom_outer,
            text="Add up to two of your own regex patterns to the scan. Requires regex knowledge. "
                 "See the ? help for examples and disclaimers.",
            font=("TkDefaultFont", 9), fg="gray",
        ).pack(anchor="w")

        # Build two custom-pattern rows with shared structure.
        # Config keys use "" for the first row and "2" for the second,
        # so existing configs with pii_scan_custom_* still work.
        _custom_suffixes = ["", "2"]
        custom_rows = []  # list of (enabled_var, name_entry, regex_entry, severity_var)
        for suffix in _custom_suffixes:
            saved_enabled = bool(_cfg.get(f"pii_scan_custom{suffix}_enabled", False))
            saved_name = _cfg.get(f"pii_scan_custom{suffix}_name", "")
            saved_regex = _cfg.get(f"pii_scan_custom{suffix}_regex", "")
            saved_severity = _cfg.get(f"pii_scan_custom{suffix}_severity", "moderate")
            if saved_severity not in ("high", "moderate", "info"):
                saved_severity = "moderate"

            row = tk.Frame(custom_outer)
            row.pack(fill="x", pady=(4, 0))

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
                "Your custom regex. peekdocs does NOT validate that it "
                "correctly identifies the data you intend to find \u2014 you "
                "own the outcome. Syntax errors are caught before the scan "
                "runs, and obviously too-broad patterns will trigger a "
                "warning. Findings from your pattern are marked '(custom)' "
                "in the results and report. See the ? help for details.",
            )

            tk.Label(row, text="Severity:", font=("TkDefaultFont", 11)).pack(side="left", padx=(0, 2))
            severity_var = ctk.StringVar(value=saved_severity)
            ctk.CTkOptionMenu(
                row, variable=severity_var,
                values=["high", "moderate", "info"],
                width=100, font=ctk.CTkFont(size=11),
            ).pack(side="left")

            custom_rows.append((enabled_var, name_entry, regex_entry, severity_var))

        # Persistent amber warning below the custom-pattern rows
        tk.Label(
            custom_outer,
            text=(
                "\u26a0  peekdocs does NOT validate your regex. You own the outcome. "
                "Findings from your patterns are marked '(custom)' in the results and report."
            ),
            font=("TkDefaultFont", 9, "italic"),
            fg="#996600",
            wraplength=820,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        # Run button on its own row; Close button on a separate row below
        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=(8, 2))
        close_frame = tk.Frame(win)
        close_frame.pack(pady=(0, 12))

        def _run():
            from tkinter import messagebox as _mb
            import re as _re
            # 5-tuples: (category, regex, severity, description, is_custom)
            # Built-in patterns get is_custom=False explicitly.
            selected = [(*SENSITIVE_PATTERNS[i], False) for i, v in enumerate(check_vars) if v.get()]

            # Validate Dollar Amounts min/max if that category is selected
            dollar_min = dollar_max = None
            dollar_selected = any(
                SENSITIVE_PATTERNS[i][0] == "Dollar Amounts"
                for i, v in enumerate(check_vars) if v.get()
            )
            if dollar_selected and dollar_min_entry is not None:
                min_str = dollar_min_entry.get().strip().replace(",", "").replace("$", "")
                max_str = dollar_max_entry.get().strip().replace(",", "").replace("$", "")
                try:
                    dollar_min = float(min_str) if min_str else 0.0
                    dollar_max = float(max_str) if max_str else 999999999.0
                except ValueError:
                    self._show_error("Dollar amount Min and Max must be numbers.")
                    return
                if dollar_min < 0 or dollar_max < 0:
                    self._show_error("Dollar amount Min and Max must be non-negative.")
                    return
                if dollar_min > dollar_max:
                    self._show_error("Dollar amount Min must be less than or equal to Max.")
                    return

            # Validate and include custom patterns if enabled
            for row_idx, (c_enabled_var, c_name_entry, c_regex_entry, c_sev_var) in enumerate(custom_rows):
                c_enabled = c_enabled_var.get()
                c_name = c_name_entry.get().strip()
                c_regex = c_regex_entry.get().strip()
                c_severity = c_sev_var.get()
                if c_severity not in ("high", "moderate", "info"):
                    c_severity = "moderate"
                label = f"Custom Pattern {row_idx + 1}"
                if c_enabled:
                    if not c_name:
                        self._show_error(f"{label}: please enter a Name.")
                        return
                    if not c_regex:
                        self._show_error(f"{label}: please enter a Regex.")
                        return
                    try:
                        _re.compile(c_regex)
                    except _re.error as exc:
                        self._show_error(
                            f"{label} regex is invalid:\n\n{exc}\n\n"
                            "Fix the pattern and try again."
                        )
                        return
                    stripped = c_regex.strip()
                    looks_too_broad = (
                        len(stripped) < 3
                        or stripped in (".", ".*", ".+", "\\w", "\\w+", "\\w*",
                                        "\\S", "\\S+", "\\S*", "\\d", "\\d+",
                                        "\\d*", "[^ ]", "[^ ]*", "[^ ]+")
                    )
                    if looks_too_broad:
                        if not _mb.askyesno(
                            f"Very Broad {label}",
                            f"Your custom regex is {repr(stripped)}, which is likely to "
                            "match almost every file in the folder and produce a huge "
                            "number of findings.\n\nRun the scan anyway?",
                            parent=win,
                        ):
                            return
                    description = f"Custom user pattern: {c_regex}"
                    selected.append((c_name, c_regex, c_severity, description, True))

            if not selected:
                self._show_error("Select at least one category or add a custom pattern.")
                return

            # Remember selections for next time
            self._pii_scan_enabled = {SENSITIVE_PATTERNS[i][0] for i, v in enumerate(check_vars) if v.get()}
            try:
                from peekdocs.cli import _load_config, _save_config
                config = _load_config()
                config["pii_scan_categories"] = sorted(self._pii_scan_enabled)
                if dollar_selected and dollar_min is not None:
                    config["pii_scan_dollar_min"] = str(int(dollar_min)) if dollar_min.is_integer() else str(dollar_min)
                    config["pii_scan_dollar_max"] = str(int(dollar_max)) if dollar_max.is_integer() else str(dollar_max)
                # Always persist the custom-pattern fields so the popup
                # restores them next time, even if the checkbox is off.
                for row_idx, (c_ev, c_ne, c_re, c_sv) in enumerate(custom_rows):
                    suffix = _custom_suffixes[row_idx]
                    config[f"pii_scan_custom{suffix}_enabled"] = c_ev.get()
                    config[f"pii_scan_custom{suffix}_name"] = c_ne.get().strip()
                    config[f"pii_scan_custom{suffix}_regex"] = c_re.get().strip()
                    config[f"pii_scan_custom{suffix}_severity"] = c_sv.get()
                pii_folder = _pii_folder_label.cget("text")
                if pii_folder and pii_folder != "(none)":
                    config["pii_scan_folder"] = pii_folder
                config["pii_scan_recursive"] = _pii_recursive_var.get()
                _save_config(config)
            except Exception:
                pass
            pii_folder = _pii_folder_label.cget("text")
            pii_recursive = _pii_recursive_var.get()
            self._last_pii_folder = pii_folder  # Remember for next invocation
            win.destroy()
            self._run_sensitive_scan(selected, pii_folder, dollar_range=(dollar_min, dollar_max) if dollar_selected else None, recursive=pii_recursive)

        ctk.CTkButton(btn_frame, text="Run Scan", width=100, font=ctk.CTkFont(size=12, weight="bold"),
                      fg_color="green", hover_color="darkgreen", command=_run).pack()
        ctk.CTkButton(
            close_frame, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=win.destroy,
            font=ctk.CTkFont(size=12),
        ).pack()

        self._apply_dark_theme(win)



    def _show_pii_scan_help(self, parent):
        """Show help for the PII Scan.

        Non-modal (no grab_set) so the user can copy regex examples
        from this window and paste them into the Custom Pattern fields
        on the categories popup without closing the help first.
        """
        import tkinter as tk
        # Both this help window and the categories popup are
        # transient(self) so they stay above the main window as a
        # group.  macOS doesn't auto-reorder transient siblings on
        # click, so we add a <Button-1> → lift() binding on both
        # windows — whichever you click comes to front.
        help_win, _dark = self._themed_toplevel()
        help_win.title("PII Scan — Help")
        help_win.geometry("750x700")
        help_win.resizable(True, True)
        help_win.transient(self)
        help_win.bind("<FocusIn>", lambda e: help_win.lift())
        # Ensure the window is visible on Linux (X11 window managers
        # can silently open new windows behind existing ones).
        help_win.lift()
        help_win.after(50, help_win.lift)
        help_win.after(100, help_win.focus_force)

        txt = tk.Text(help_win, wrap="word", font=("TkDefaultFont", 12),
                      padx=15, pady=10, borderwidth=0, highlightthickness=0)
        scroll = tk.Scrollbar(help_win, command=txt.yview)
        txt.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True)

        # Right-click context menu for copying selected text
        _copy_menu = tk.Menu(txt, tearoff=0)
        _copy_menu.add_command(
            label="Copy",
            command=lambda: (
                help_win.clipboard_clear(),
                help_win.clipboard_append(txt.get("sel.first", "sel.last")),
            ) if txt.tag_ranges("sel") else None,
        )

        def _show_copy_menu(event):
            try:
                _copy_menu.tk_popup(event.x_root, event.y_root)
            finally:
                _copy_menu.grab_release()

        # Bind right-click on all platforms
        txt.bind("<Button-3>", _show_copy_menu)          # Windows / Linux
        txt.bind("<Button-2>", _show_copy_menu)          # macOS
        txt.bind("<Control-Button-1>", _show_copy_menu)  # macOS ctrl+click

        txt.tag_configure("heading", font=("TkDefaultFont", 14, "bold"),
                          spacing1=10, spacing3=5)
        txt.tag_configure("body", font=("TkDefaultFont", 12), spacing1=2)
        txt.tag_configure("example", font=("Courier", 11), lmargin1=30,
                          lmargin2=30, spacing1=2)
        txt.tag_configure("toc_title", font=("TkDefaultFont", 14, "bold"),
                          spacing1=5, spacing3=8)
        txt.tag_configure("toc_item", font=("TkDefaultFont", 11), lmargin1=20,
                          lmargin2=20, foreground="#999999" if ctk.get_appearance_mode() == "Dark" else "gray40")
        txt.tag_configure("heading_red", font=("TkDefaultFont", 14, "bold"),
                          spacing1=10, spacing3=5, foreground="red")

        def h(text):
            txt.insert("end", text + "\n", "heading")

        def h_red(text):
            txt.insert("end", text + "\n", "heading_red")

        def b(text):
            txt.insert("end", text + "\n", "body")

        def e(text):
            txt.insert("end", text + "\n", "example")

        def blank():
            txt.insert("end", "\n")

        txt.tag_configure("toc_item_red", font=("TkDefaultFont", 11, "bold"), lmargin1=20,
                          lmargin2=20, foreground="red")
        txt.insert("end", "TABLE OF CONTENTS\n", "toc_title")
        for section in [
            "What Is the PII Scan?",
            "How to Use It",
            "Scan Categories",
            "Severity Levels",
            "Custom Pattern (Advanced)",
            "Understanding Results",
            "Why No Report File?",
            "Saving Your Selections",
            "Search Folder",
            "How It Differs from Regular Search",
        ]:
            txt.insert("end", f"\u2022 {section}\n", "toc_item")
        for section in [
            "Disclaimer",
            "MIT License",
        ]:
            txt.insert("end", f"\u2022 {section}\n", "toc_item")
        txt.insert("end", "\n")

        b("The PII Scan helps locate personally identifiable information")
        b("you may have inadvertently left in your files \u2014 SSNs, credit")
        b("cards, tax IDs, passwords, and more \u2014 with one click.")
        blank()

        h("WHAT IS THE PII SCAN?")
        b("The PII Scan helps locate personally identifiable information")
        b("you may have inadvertently left in your files. It")
        b("runs a battery of regex pattern searches \u2014 SSNs, credit cards,")
        b("tax IDs, emails, phone numbers, passwords, dates of birth, and")
        b("large dollar amounts \u2014 and shows you exactly where they are.")
        blank()
        b("Use it to discover sensitive data hiding in your files before")
        b("someone else finds it. Check years of personal documents for")
        b("exposed SSNs, scan an old laptop before you sell it, or review")
        b("files in a shared drive to see what might need to be cleaned up.")
        blank()

        h("HOW TO USE IT")
        b("1. Make sure the Search Folder points to the folder you want")
        b("   to check (use Change Folder if needed)")
        b("2. Check the categories you want to scan for (all are checked")
        b("   by default)")
        b("3. Click Run Scan")
        b("4. Results appear in a popup with color-coded severity badges")
        b("5. Click View Files on any category to see affected files")
        b("6. Click Open Report to view the highlighted .docx report")
        blank()

        h("SCAN CATEGORIES")
        blank()
        b("Social Security Numbers (HIGH)")
        e("  Pattern: XXX-XX-XXXX (e.g., 123-45-6789)")
        blank()
        b("Credit Card Numbers (HIGH)")
        e("  Visa, Mastercard, Amex, Discover patterns")
        e("  (e.g., 4111-1111-1111-1111)")
        blank()
        b("Tax ID / EIN (HIGH)")
        e("  Employer Identification Numbers: XX-XXXXXXX")
        e("  (e.g., 12-3456789)")
        blank()
        b("Email Addresses (MODERATE)")
        e("  Standard email patterns (e.g., name@example.com)")
        blank()
        b("Phone Numbers (MODERATE)")
        e("  US phone patterns with separators")
        e("  (e.g., 555-123-4567 or (555) 123-4567)")
        blank()
        b("Passwords / Secrets (MODERATE)")
        e("  Lines containing password=, secret=, api_key=,")
        e("  token=, or similar assignments")
        blank()
        b("Dates of Birth (MODERATE)")
        e("  Date patterns near keywords like DOB, date of birth,")
        e("  or born (e.g., DOB: 03/15/1990)")
        blank()
        b("Dollar Amounts Over $10,000 (INFO)")
        e("  Dollar amounts $10,000 and above")
        e("  (e.g., $15,000 or $250,000.00)")
        blank()

        h("SEVERITY LEVELS")
        b("HIGH (red) \u2014 Data that could cause serious harm if exposed:")
        b("SSNs, credit cards, tax IDs. These should be investigated")
        b("immediately.")
        blank()
        b("MODERATE (yellow) \u2014 Data that may be sensitive depending on")
        b("context: emails, phone numbers, passwords, dates of birth.")
        b("Review to determine if exposure is a concern.")
        blank()
        b("INFO (blue) \u2014 Data that is noteworthy but not necessarily")
        b("sensitive: large dollar amounts. Useful for financial review")
        b("but unlikely to be a privacy risk on its own.")
        blank()

        h("CUSTOM PATTERN (ADVANCED)")
        b("The eight built-in categories cover common US PII. If you")
        b("need to scan for something else \u2014 an international ID, a")
        b("company-specific account number, an internal reference code")
        b("\u2014 the Custom Pattern section at the bottom of the category")
        b("selection popup lets you add your own regex to the scan.")
        blank()

        b("WHAT IS REGEX?")
        blank()
        b("Regex (short for 'regular expression') is a mini-language")
        b("for describing text patterns. Instead of searching for an")
        b("exact word like 'budget', a regex lets you describe a")
        b("shape \u2014 for example, 'three digits, a dash, two digits,")
        b("a dash, four digits' matches the SSN format 123-45-6789.")
        blank()
        b("You don't need to be a programmer to use basic regex.")
        b("Most useful patterns are built from a handful of building")
        b("blocks described below. If you can read a pattern like")
        b("\\d{3}-\\d{2}-\\d{4} and understand that \\d means 'any digit'")
        b("and {3} means 'exactly three,' you know enough to write")
        b("your own custom patterns for the PII Scan.")
        blank()
        b("If you've never used regex before, these free resources")
        b("can help you get started in 15\u201330 minutes:")
        blank()
        b("\u2022 regex101.com \u2014 an interactive regex tester where you can")
        b("  type a pattern, paste some sample text, and see what")
        b("  matches in real time. Choose the 'Python' flavor on the")
        b("  left sidebar. This is the single best way to learn.")
        b("\u2022 regexone.com \u2014 a free, step-by-step tutorial that teaches")
        b("  one concept at a time with interactive exercises.")
        b("\u2022 rexegg.com/regex-quickstart.html \u2014 a one-page cheat")
        b("  sheet with every regex symbol and what it does.")
        blank()

        b("HOW TO USE THE CUSTOM PATTERN")
        blank()
        b("1. Check the box next to 'Advanced \u2014 Custom Pattern'")
        b("2. Enter a short Name (e.g., 'UK NINO' or 'Client ID')")
        b("3. Enter the Regex pattern")
        b("4. Pick a Severity (HIGH / MODERATE / INFO)")
        b("5. Click Run Scan")
        blank()
        b("The custom pattern runs alongside the built-in categories")
        b("you have checked. Findings appear in the results popup and")
        b("report as a separate category with the name you entered,")
        b("marked with '(custom)' so you can tell it apart from the")
        b("built-in categories.")
        blank()

        b("REGEX BASICS")
        blank()
        b("Characters and digits:")
        e("  \\d              any single digit (0\u20139)")
        e("  \\D              any character that is NOT a digit")
        e("  \\w              any letter, digit, or underscore")
        e("  \\W              any character that is NOT a letter/digit/_")
        e("  \\s              any whitespace (space, tab, newline)")
        e("  \\S              any character that is NOT whitespace")
        e("  .               any single character except newline")
        e("  \\.              a literal dot (the backslash 'escapes' it)")
        blank()
        b("Repetition (how many times to match):")
        e("  \\d{3}           exactly 3 digits")
        e("  \\d{3,5}         3 to 5 digits")
        e("  \\d{3,}          3 or more digits")
        e("  \\d+             one or more digits (same as \\d{1,})")
        e("  \\d*             zero or more digits")
        e("  \\d?             zero or one digit (the digit is optional)")
        blank()
        b("Character classes (match one of a set):")
        e("  [A-Z]           any uppercase letter A\u2013Z")
        e("  [a-z]           any lowercase letter a\u2013z")
        e("  [A-Za-z]        any letter (upper or lower)")
        e("  [0-9]           any digit (same as \\d)")
        e("  [A-Z0-9]        any uppercase letter or digit")
        e("  [- ]            a dash or a space")
        e("  [^0-9]          any character EXCEPT a digit")
        blank()
        b("Anchors and grouping:")
        e("  ^               start of line")
        e("  $               end of line")
        e("  ( )             group characters together")
        e("  |               OR  (e.g., cat|dog matches 'cat' or 'dog')")
        e("  (?:  )          group without capturing (more efficient)")
        blank()
        b("Escaping special characters:")
        b("These characters have special meaning in regex:")
        e("  . * + ? [ ] ( ) { } ^ $ \\ |")
        b("To search for one of them literally, put a backslash")
        b("in front of it. For example:")
        e("  \\.              matches a literal dot")
        e("  \\$              matches a literal dollar sign")
        e("  \\(              matches a literal opening parenthesis")
        blank()
        b("Putting it together \u2014 reading a pattern:")
        e("  \\d{3}-\\d{2}-\\d{4}")
        b("  means: 3 digits, a dash, 2 digits, a dash, 4 digits")
        b("  matches: 123-45-6789 (SSN format)")
        blank()
        e("  [A-Z]{2}\\d{6}[A-Z]")
        b("  means: 2 uppercase letters, 6 digits, 1 uppercase letter")
        b("  matches: AB123456C (UK National Insurance Number)")
        blank()
        e("  \\$[\\d,]+\\.\\d{2}")
        b("  means: a dollar sign, one or more digits/commas, a dot,")
        b("  exactly 2 digits")
        b("  matches: $1,234.56  $99.00  $1,000,000.00")
        blank()

        b("EXAMPLE PATTERNS FOR COMMON FORMATS")
        blank()
        b("National ID numbers:")
        e("  US SSN:            \\d{3}-\\d{2}-\\d{4}")
        e("  UK NINO:           [A-Z]{2}\\d{6}[A-Z]")
        e("  Canadian SIN:      \\d{3}[- ]?\\d{3}[- ]?\\d{3}")
        e("  Australian TFN:    \\d{3}[ ]?\\d{3}[ ]?\\d{3}")
        e("  Indian PAN:        [A-Z]{5}\\d{4}[A-Z]")
        e("  Indian Aadhaar:    \\d{4}[ ]?\\d{4}[ ]?\\d{4}")
        e("  German Steuer-ID:  \\d{2}[ ]?\\d{3}[ ]?\\d{3}[ ]?\\d{3}")
        e("  French INSEE/NIR:  [12]\\d{2}[01]\\d{9}([ ]?\\d{2})?")
        e("  South Korean RRN:  \\d{6}-\\d{7}")
        e("  Brazilian CPF:     \\d{3}\\.\\d{3}\\.\\d{3}-\\d{2}")
        e("  Mexican CURP:      [A-Z]{4}\\d{6}[A-Z]{6}\\d{2}")
        blank()
        b("Tax and business numbers:")
        e("  US EIN:            \\d{2}-\\d{7}")
        e("  UK VAT:            GB\\d{9}")
        e("  EU VAT (generic):  [A-Z]{2}\\d{8,12}")
        e("  Australian ABN:    \\d{2}[ ]?\\d{3}[ ]?\\d{3}[ ]?\\d{3}")
        blank()
        b("Financial:")
        e("  IBAN (generic):    [A-Z]{2}\\d{2}[A-Z0-9]{4,30}")
        e("  SWIFT/BIC:         [A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?")
        e("  Dollar amounts:    \\$[\\d,]+\\.\\d{2}")
        e("  Euro amounts:      \\d+[,.]\\d{2}[ ]?\u20ac")
        blank()
        b("Technology:")
        e("  AWS access key:    AKIA[0-9A-Z]{16}")
        e("  Generic API key:   [A-Za-z0-9_]{20,}")
        e("  IPv4 address:      \\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}")
        e("  Email address:     [A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}")
        blank()
        b("Other:")
        e("  US passport:       [A-Z]\\d{8}")
        e("  UK passport:       \\d{9}")
        e("  US license plate:  [A-Z0-9]{2,7}")
        e("  Dates (YYYY-MM-DD): \\d{4}-\\d{2}-\\d{2}")
        e("  Dates (DD/MM/YYYY): \\d{2}/\\d{2}/\\d{4}")
        e("  Phone (intl):      \\+\\d{1,3}[- ]?\\d{4,14}")
        blank()
        b("Tip: copy a pattern from above, paste it into the Regex")
        b("field, give it a Name, and click Run Scan. You can also")
        b("test patterns at regex101.com (choose the Python flavor)")
        b("before running the scan.")
        blank()

        b("IMPORTANT NOTES")
        blank()
        b("\u2022 Don't worry about getting your regex wrong. peekdocs")
        b("  never modifies, moves, or deletes the files it searches")
        b("  \u2014 it only reads them and writes a summary report. The")
        b("  worst thing a bad regex can do is produce a useless or")
        b("  confusing report, which you can fix by running the scan")
        b("  again with a better pattern.")
        b("\u2022 Syntax errors in your regex are caught before the scan")
        b("  runs, so an invalid pattern will produce a friendly error")
        b("  message and not start the scan.")
        b("\u2022 Very broad patterns (like . or \\d) will match almost")
        b("  everything and produce a flood of findings. peekdocs")
        b("  warns you before running the scan if it detects one.")
        b("\u2022 Your Custom Pattern is saved between sessions. Uncheck")
        b("  the box to skip it for a scan without losing the pattern.")
        b("\u2022 Read the Disclaimer section below for the full list of")
        b("  what peekdocs does and does not promise about regex-based")
        b("  detection. Custom patterns are your responsibility.")
        blank()

        h("UNDERSTANDING RESULTS")
        b("The results popup shows each category with:")
        b("\u2022 A color-coded severity badge (HIGH/MODERATE/INFO)")
        b("\u2022 The number of matches and files affected")
        b("\u2022 'Clean' (green) if no matches were found")
        b("\u2022 A View Files button to see per-file details")
        blank()
        b("Click View Files to see which files contain that type of data,")
        b("with match counts and line numbers. Double-click a file to")
        b("open it in its default application.")
        blank()

        h("WHY NO REPORT FILE?")
        b("The PII Scan shows results on screen only \u2014 it does not")
        b("write a report file to disk. This is a deliberate safety")
        b("measure. A report file that collects all your SSNs, credit")
        b("card numbers, and passwords into a single document would")
        b("itself be a data exposure risk \u2014 it could be uploaded to")
        b("the cloud by backup software, synced by OneDrive or")
        b("Dropbox, or left behind when you sell or donate a computer.")
        blank()
        b("By keeping results on screen only, the sensitive data is")
        b("never concentrated into a file that could leak. You can")
        b("always re-run the scan to see the results again.")
        blank()

        h("SAVING YOUR SELECTIONS")
        b("Your checkbox selections are saved to ~/.peekdocsrc and")
        b("remembered between sessions. The next time you open the PII")
        b("Scan, the same categories will be checked. Use Select All")
        b("or Deselect All for quick toggling.")
        blank()

        h("SEARCH FOLDER")
        b("The scan runs against whatever folder is shown at the top")
        b("of this window. Use Change Folder to switch without closing")
        b("the window. Check Include subfolders (Recursive) to scan")
        b("all subfolders as well.")
        blank()
        b("The PII Scan always searches ALL supported file types in the")
        b("selected folder \u2014 it ignores any File Types filter you may")
        b("have set in Advanced Search Options. This ensures no files")
        b("are accidentally skipped during a sensitive data check.")
        blank()
        b("The scan always searches files directly \u2014 it does not use")
        b("the search index, because regex pattern matching requires")
        b("scanning every line of text. The Use Index checkbox is")
        b("temporarily unchecked during the scan and restored afterward.")
        blank()

        h("HOW IT DIFFERS FROM REGULAR SEARCH")
        b("The PII Scan is completely independent from the main search.")
        b("It has its own folder, its own Recursive checkbox, and always")
        b("scans all file types. It does not read or change any settings")
        b("in Advanced Search Options.")
        blank()
        b("A regular search looks for terms you type. The PII Scan")
        b("runs 8 pre-built regex patterns designed to detect specific")
        b("types of sensitive data. You don't need to know regex \u2014")
        b("the patterns are built in.")
        blank()
        b("The PII Scan is a standalone one-click scan. It does not")
        b("save anything to your collection or write any files. If")
        b("you want to reuse the same regex patterns as normal searches,")
        b("use the Search Wizard to build an equivalent search and then")
        b("click Save Search to store it by name.")
        blank()

        h("DISCLAIMER")
        b("The PII Scan is a pattern-matching discovery aid, not a")
        b("security product or a compliance certification. Please read")
        b("the following before relying on it.")
        blank()
        b("\u2022 False positives happen. A 9-digit account number can")
        b("  look like an SSN. A tracking number can match the credit")
        b("  card pattern. The word 'password' can appear in a help")
        b("  document that contains no actual passwords. Always review")
        b("  findings in context before taking action \u2014 click View")
        b("  Files to see the matched text with surrounding context")
        b("  so you can judge whether each finding is real.")
        blank()
        b("\u2022 False negatives happen. The PII Scan cannot find PII")
        b("  that does not match its built-in regex patterns. An SSN")
        b("  written as '123 45 6789' (spaces instead of dashes) may")
        b("  not be detected. A credit card number without separators")
        b("  may be missed. A foreign tax ID in a format peekdocs")
        b("  does not know will not be flagged. A clean scan does")
        b("  NOT prove that a file is free of sensitive data \u2014 it")
        b("  proves only that peekdocs's specific regex patterns did")
        b("  not match anything in the file's extracted text.")
        blank()
        b("\u2022 Some file formats may not be fully extracted. peekdocs")
        b("  searches 86 file types, but extraction quality varies. A")
        b("  scanned PDF without OCR enabled will not surface any")
        b("  text. An image file is ignored unless OCR is on. Complex")
        b("  binary formats may yield partial text. Files that")
        b("  peekdocs could not read will not produce findings even")
        b("  if they contain PII. Check View N excluded file(s) after")
        b("  each scan to see which files were skipped.")
        blank()
        b("\u2022 Not a breach prevention tool. The PII Scan finds and")
        b("  displays results only. It does not block, encrypt, move, delete,")
        b("  or otherwise secure any data. Any action taken based on")
        b("  this report is the reader's decision and responsibility.")
        blank()
        b("\u2022 Not compliance software. A clean scan does not certify")
        b("  HIPAA, GDPR, PCI-DSS, SOX, or any other regulatory")
        b("  compliance. The PII Scan can be one input to a review")
        b("  process, but it is not a substitute for professional")
        b("  compliance expertise or a formal audit.")
        blank()
        b("\u2022 Custom user-supplied patterns are your responsibility.")
        b("  When you enter your own regex in the Custom Pattern section,")
        b("  peekdocs does not validate that your pattern correctly")
        b("  identifies the data you intend to find, and makes no")
        b("  representation about whether a custom pattern will match")
        b("  all instances of the data you are looking for. If you type")
        b("  your own regex, you own the outcome. peekdocs never")
        b("  modifies, moves, or deletes the files it searches, so a")
        b("  bad pattern cannot harm your documents \u2014 the worst outcome")
        b("  is a useless report, which you can fix by editing the")
        b("  pattern and re-running the scan.")
        blank()
        b("\u2022 Provided as-is under the MIT License. peekdocs comes")
        b("  with no warranty of any kind, express or implied. Users")
        b("  are solely responsible for how they interpret and act on")
        b("  these results. The full MIT License text is reproduced")
        b("  below.")
        blank()
        b("In short: the PII Scan is a helpful set of eyes on your own")
        b("files. It is not a guarantee, a certification, or a security")
        b("system. Use the results as a starting point for your own")
        b("review, not as a final answer.")
        blank()

        h("MIT LICENSE")
        b("Copyright (c) 2026 Robert D. Schoening")
        blank()
        b("Permission is hereby granted, free of charge, to any person")
        b("obtaining a copy of this software and associated documentation")
        b("files (the \"Software\"), to deal in the Software without")
        b("restriction, including without limitation the rights to use,")
        b("copy, modify, merge, publish, distribute, sublicense, and/or")
        b("sell copies of the Software, and to permit persons to whom")
        b("the Software is furnished to do so, subject to the following")
        b("conditions:")
        blank()
        b("The above copyright notice and this permission notice shall")
        b("be included in all copies or substantial portions of the")
        b("Software.")
        blank()
        b("THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY")
        b("KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE")
        b("WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR")
        b("PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS")
        b("OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR")
        b("OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR")
        b("OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE")
        b("SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.")
        blank()

        txt.configure(state="disabled")

        # Ensure Cmd+C (macOS) and Ctrl+C (Windows/Linux) copy the
        # selected text even though the widget is in disabled state.
        def _keyboard_copy(event):
            try:
                sel = txt.get("sel.first", "sel.last")
                if sel:
                    help_win.clipboard_clear()
                    help_win.clipboard_append(sel)
            except tk.TclError:
                pass  # No selection
            return "break"

        txt.bind("<Command-c>", _keyboard_copy)   # macOS
        txt.bind("<Control-c>", _keyboard_copy)    # Windows / Linux

        close_btn = ctk.CTkButton(
            help_win, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=help_win.destroy,
            font=ctk.CTkFont(size=12),
        )
        close_btn.pack(pady=(5, 10))

        self._apply_dark_theme(help_win)



    def _run_sensitive_scan(self, selected_patterns, folder=None, dollar_range=None, recursive=True):
        """Launch the sensitive data scan with the selected patterns."""
        if not folder:
            folder = self.folder_entry.get().strip()
        if not folder or folder == "(none)" or not os.path.isdir(folder):
            self._show_error("Please select a valid folder first.")
            return
        # PII scan searches all supported file types — independent of main search
        file_types = None

        # Save recursive setting so the report can include it
        self._pii_scan_recursive = recursive

        # Save and uncheck Use Index — regex scans don't benefit from the index
        self._sensitive_scan_saved_index = self.index_search_var.get()
        self.index_search_var.set("off")

        if hasattr(self, "sensitive_scan_btn"):
            self.sensitive_scan_btn.configure(state="disabled", text="\u25b6 Scanning...")
        self._pii_scan_cancelled = False
        if hasattr(self, "_pii_scan_btn"):
            self._pii_scan_btn.configure(
                fg_color="red", hover_color="darkred", text="Cancel",
                command=self._cancel_pii_scan,
            )
        self.status_label.configure(text="Scanning for sensitive data (index not used — regex scans files directly)...", text_color=("blue", "#66BBFF"))
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        self.progress_bar.grid(row=5, column=0, columnspan=3, padx=10, pady=(2, 2), sticky="ew")

        thread = threading.Thread(
            target=self._sensitive_scan_thread,
            args=(folder, recursive, file_types, selected_patterns, dollar_range),
            daemon=True,
        )
        thread.start()



    def _sensitive_scan_thread(self, folder, recursive, file_types, selected_patterns=None, dollar_range=None):
        """Run selected sensitive data patterns in a background thread."""
        from peekdocs.api import search
        from peekdocs.sensitive_patterns import SENSITIVE_PATTERNS

        patterns = selected_patterns if selected_patterns else SENSITIVE_PATTERNS
        total_patterns = len(patterns)
        scan_results = []
        start = time.time()
        files_searched = 0

        for pat_idx, pattern_tuple in enumerate(patterns, 1):
            if getattr(self, "_pii_scan_cancelled", False):
                return
            # 5-tuple: (category, regex, severity, description, is_custom)
            # Fall back to 4-tuple with is_custom=False for safety.
            if len(pattern_tuple) >= 5:
                category, regex, severity, description, is_custom = pattern_tuple[:5]
            else:
                category, regex, severity, description = pattern_tuple[:4]
                is_custom = False
            self.after(0, lambda i=pat_idx, t=total_patterns, c=category:
                self.status_label.configure(
                    text=f"Scanning for sensitive data... ({i}/{t}) {c}",
                    text_color=("blue", "#66BBFF"),
                )
            )
            # For the Dollar Amounts category, inject a range filter and
            # update the display name/description to reflect the user's range
            range_filters = None
            if category == "Dollar Amounts" and dollar_range is not None:
                lo, hi = dollar_range
                range_filters = [f"amount:{lo}..{hi}"]
                lo_label = f"${int(lo):,}" if float(lo).is_integer() else f"${lo:,}"
                hi_label = f"${int(hi):,}" if float(hi).is_integer() else f"${hi:,}"
                category = f"Dollar Amounts ({lo_label} \u2013 {hi_label})"
                description = f"Dollar amounts between {lo_label} and {hi_label}"
            try:
                result = search(
                    [regex],
                    directory=folder,
                    recursive=recursive,
                    use_regex=True,
                    use_index=False,
                    file_types=file_types,
                    range_filters=range_filters,
                )
                files_searched = max(files_searched, len(result.files_searched))
                # Build per-file breakdown
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
                scan_results.append({
                    "category": category,
                    "severity": severity,
                    "description": description,
                    "regex": regex,
                    "match_count": len(result.matches),
                    "file_count": len(file_matches),
                    "files": file_matches,
                    "is_custom": is_custom,
                })
            except Exception:
                scan_results.append({
                    "category": category,
                    "severity": severity,
                    "description": description,
                    "match_count": 0,
                    "file_count": 0,
                    "files": {},
                    "is_custom": is_custom,
                })

        elapsed = time.time() - start
        self.after(0, self._sensitive_scan_finished, scan_results, elapsed, files_searched)



    def _cancel_pii_scan(self):
        """Cancel a running PII scan."""
        self._pii_scan_cancelled = True
        self.status_label.configure(text="PII Scan cancelled.", text_color=("blue", "#66BBFF"))
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        if hasattr(self, "sensitive_scan_btn"):
            self.sensitive_scan_btn.configure(state="normal", text="\u25b6 PII Scan")
        if hasattr(self, "_pii_scan_btn"):
            self._pii_scan_btn.configure(
                state="normal", fg_color="#0D9488", hover_color="#0B7A70",
                text_color="white", text="\U0001f50d PII Scan",
                command=self._start_sensitive_scan,
            )
        # Restore Use Index checkbox
        if hasattr(self, "_sensitive_scan_saved_index"):
            self.index_search_var.set(self._sensitive_scan_saved_index)

    def _sensitive_scan_finished(self, scan_results, elapsed, files_searched):
        """Restore UI and show results popup after sensitive data scan."""
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        if hasattr(self, "sensitive_scan_btn"):
            self.sensitive_scan_btn.configure(state="normal", text="\u25b6 PII Scan")
        if hasattr(self, "_pii_scan_btn"):
            self._pii_scan_btn.configure(
                state="normal", fg_color="#0D9488", hover_color="#0B7A70",
                text_color="white", text="\U0001f50d PII Scan",
                command=self._start_sensitive_scan,
            )

        # Restore Use Index checkbox
        if hasattr(self, "_sensitive_scan_saved_index"):
            self.index_search_var.set(self._sensitive_scan_saved_index)

        total = sum(r["match_count"] for r in scan_results)
        high = sum(r["match_count"] for r in scan_results if r["severity"] == "high")

        if total == 0:
            self.status_label.configure(
                text=f"Sensitive data scan complete ({elapsed:.1f}s, {files_searched} files) — no findings.",
                text_color="green",
            )
        else:
            self.status_label.configure(
                text=f"Sensitive data scan complete ({elapsed:.1f}s, {files_searched} files) — {total} finding(s) ({high} high severity).",
                text_color="red" if high > 0 else ("black", "#e0e0e0"),
            )
        self._show_sensitive_scan_results(scan_results, elapsed, files_searched)



    def _show_sensitive_scan_results(self, scan_results, elapsed, files_searched):
        """Show a popup with categorized sensitive data scan results."""
        import tkinter as tk
        from peekdocs.sensitive_patterns import SEVERITY_COLORS, SEVERITY_ORDER
        popup, _dark = self._themed_toplevel()
        popup.title("Sensitive Data Scan Results")
        popup.resizable(True, True)
        popup.geometry("800x520")
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 800) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 520) // 2
        popup.geometry(f"+{x}+{y}")

        total = sum(r["match_count"] for r in scan_results)
        high = sum(r["match_count"] for r in scan_results if r["severity"] == "high")

        # Header
        if total == 0:
            header_text = f"No sensitive data found — {files_searched} files scanned in {elapsed:.1f}s"
            header_color = "green"
        else:
            header_text = f"{total} finding(s) across {files_searched} files ({elapsed:.1f}s)"
            header_color = "#CC0000" if high > 0 else "black"

        header_frame = tk.Frame(popup)
        header_frame.pack(fill="x", padx=15, pady=(10, 2))
        tk.Label(
            header_frame, text="Sensitive Data Scan Results",
            font=("TkDefaultFont", 14, "bold"),
        ).pack(side="left", expand=True)
        ctk.CTkButton(
            header_frame, text="?", width=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._show_pii_scan_results_help(popup),
        ).pack(side="right")
        tk.Label(
            popup, text=header_text,
            font=("TkDefaultFont", 12), fg=header_color,
        ).pack(pady=(0, 8))

        # Scrollable results frame
        canvas_frame = tk.Frame(popup)
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, command=canvas.yview)
        inner = tk.Frame(canvas)

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Sort built-in categories by severity, then custom patterns
        # at the bottom where the user expects to find them.
        severity_rank = {s: i for i, s in enumerate(SEVERITY_ORDER)}
        builtin = [r for r in scan_results if not r.get("is_custom")]
        custom = [r for r in scan_results if r.get("is_custom")]
        sorted_results = sorted(
            builtin,
            key=lambda r: (severity_rank.get(r["severity"], 99), -r["match_count"]),
        ) + sorted(
            custom,
            key=lambda r: (severity_rank.get(r["severity"], 99), -r["match_count"]),
        )

        for result in sorted_results:
            sev = SEVERITY_COLORS.get(result["severity"], SEVERITY_COLORS["info"])
            row = tk.Frame(inner, pady=3)
            row.pack(fill="x", padx=5, pady=2)

            # Severity badge
            badge = tk.Label(
                row, text=f" {sev['label']} ", font=("TkDefaultFont", 10, "bold"),
                bg=sev["bg"], fg=sev["fg"], width=10,
            )
            badge.pack(side="left", padx=(0, 8))

            # Category name
            tk.Label(
                row, text=result["category"],
                font=("TkDefaultFont", 12, "bold"), anchor="w",
            ).pack(side="left", padx=(0, 4))

            # Custom pattern marker — visually distinguish user-supplied
            # pattern findings from peekdocs's built-in categories
            if result.get("is_custom"):
                tk.Label(
                    row, text="(custom)",
                    font=("TkDefaultFont", 10, "italic"),
                    fg="#996600",
                ).pack(side="left", padx=(0, 8))

            if result["match_count"] == 0:
                tk.Label(
                    row, text="Clean",
                    font=("TkDefaultFont", 11), fg="green",
                ).pack(side="left")
            else:
                count_text = f"{result['match_count']} match(es) in {result['file_count']} file(s)"
                tk.Label(
                    row, text=count_text,
                    font=("TkDefaultFont", 11), fg="#CC0000" if result["severity"] == "high" else "black",
                ).pack(side="left", padx=(0, 8))

                files_data = result["files"]
                cat_name = result["category"]
                cat_regex = result.get("regex")
                view_btn = ctk.CTkButton(
                    row, text="View Files",
                    width=80, font=ctk.CTkFont(size=10),
                    command=lambda f=files_data, c=cat_name, p=popup, r=cat_regex: self._show_sensitive_category_files(f, c, p, regex=r),
                )
                view_btn.pack(side="right", padx=(0, 5))

            # Description
            desc_row = tk.Frame(inner)
            desc_row.pack(fill="x", padx=5)
            tk.Label(
                desc_row, text=f"    {result['description']}",
                font=("TkDefaultFont", 10), fg="gray",
            ).pack(side="left")

        # Mousewheel scrolling
        def _on_mousewheel(event):
            delta = event.delta
            if abs(delta) > 10:
                delta = 1 if delta > 0 else -1
            else:
                delta = max(-1, min(1, delta))
            canvas.yview_scroll(-delta, "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        popup.protocol("WM_DELETE_WINDOW", lambda: (canvas.unbind_all("<MouseWheel>"), popup.destroy()))

        _close_btn = ctk.CTkButton(
            popup, text="Close", width=80, font=ctk.CTkFont(size=12),
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=lambda: (canvas.unbind_all("<MouseWheel>"), popup.destroy()),
        )
        _close_btn.pack(pady=(0, 10))
        Tooltip(_close_btn, "Closing this window permanently deletes all PII scan data — by design, nothing is saved to disk. You can always re-run the PII Scan to see the results again", anchor="above")

        self._apply_dark_theme(popup)


    def _show_pii_scan_results_help(self, parent):
        """Show help for interpreting the PII Scan Results window."""
        import tkinter as tk
        help_win, _dark = self._themed_toplevel(parent)
        help_win.title("PII Scan Results — Help")
        help_win.geometry("700x580")
        help_win.resizable(True, True)
        help_win.transient(parent)
        try:
            help_win.grab_set()
        except Exception:
            help_win.after(150, lambda: help_win.grab_set() if help_win.winfo_exists() else None)

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
                          lmargin2=20, foreground="#999999" if ctk.get_appearance_mode() == "Dark" else "gray40")
        txt.tag_configure("heading_red", font=("TkDefaultFont", 13, "bold"),
                          spacing1=8, spacing3=4, foreground="red")

        def h(text):
            txt.insert("end", text + "\n", "heading")
        def h_red(text):
            txt.insert("end", text + "\n", "heading_red")
        def b(text):
            txt.insert("end", text + "\n", "body")
        def e(text):
            txt.insert("end", text + "\n", "example")
        def blank():
            txt.insert("end", "\n")

        txt.tag_configure("toc_item_red", font=("TkDefaultFont", 11, "bold"), lmargin1=20,
                          lmargin2=20, foreground="red")
        txt.insert("end", "TABLE OF CONTENTS\n", "toc_title")
        for section in [
            "What This Window Shows",
            "Severity Badges",
            "Reading the Match Counts",
            "View Files Button",
            "What to Do Next",
            "Why No Report File?",
            "False Positives",
        ]:
            txt.insert("end", f"\u2022 {section}\n", "toc_item")
        txt.insert("end", "\n")

        b("This window shows the results of the PII Scan \u2014 each")
        b("category the scan checked, with counts of matches found.")
        blank()

        h("WHAT THIS WINDOW SHOWS")
        b("Each row represents one of the 8 scan categories you ran.")
        b("The categories are sorted by severity (HIGH first, then")
        b("MODERATE, then INFO). Categories with no matches show a")
        b("green 'Clean' label \u2014 nothing to worry about.")
        blank()

        h("SEVERITY BADGES")
        b("HIGH (red) \u2014 Data that could cause serious harm if exposed:")
        b("Social Security numbers, credit card numbers, tax IDs.")
        b("Investigate these immediately.")
        blank()
        b("MODERATE (yellow) \u2014 Data that may be sensitive depending on")
        b("context: emails, phone numbers, passwords, dates of birth.")
        b("Review to determine if exposure is a concern.")
        blank()
        b("INFO (blue) \u2014 Noteworthy but not necessarily sensitive:")
        b("large dollar amounts. Useful for financial review.")
        blank()

        h("READING THE MATCH COUNTS")
        b("Each category with findings shows:")
        e("  12 match(es) in 3 file(s)")
        blank()
        b("This means peekdocs found 12 instances of that pattern across")
        b("3 different files. Some files may contain multiple matches.")
        blank()

        h("VIEW FILES BUTTON")
        b("Click View Files on any category to see exactly which files")
        b("contain that type of data. The sub-popup shows:")
        b("\u2022 Each affected file with its match count")
        b("\u2022 Line numbers where matches appear (up to 20 per file)")
        b("\u2022 Double-click a file to open it in its default application")
        blank()
        b("This is how you drill into a specific finding \u2014 start at")
        b("the category, find the file, open it, and look at the line.")
        blank()

        h("WHAT TO DO NEXT")
        b("For HIGH severity findings:")
        b("1. Click View Files to see which files are affected")
        b("2. Open each file and go to the listed line numbers")
        b("3. Determine whether the data should be there or not")
        b("4. If it shouldn't: redact, move to a secured location, or delete")
        b("5. Re-run the scan to verify the finding is gone")
        blank()
        b("For MODERATE/INFO findings: review to determine if any action")
        b("is needed based on your context. Some findings may be")
        b("legitimate (e.g., your own email address in a template).")
        blank()

        h("WHY NO REPORT FILE?")
        b("The PII Scan shows results on screen only \u2014 it does not")
        b("write a report file to disk. This is a deliberate safety")
        b("measure. A report file that collects all your SSNs, credit")
        b("card numbers, and passwords into a single document would")
        b("itself be a data exposure risk \u2014 it could be uploaded to")
        b("the cloud by backup software, synced by OneDrive or")
        b("Dropbox, or left behind when you sell or donate a computer.")
        blank()
        b("By keeping results on screen only, the sensitive data is")
        b("never concentrated into a file that could leak. You can")
        b("always re-run the scan to see the results again.")
        blank()
        b("As soon as you close the Sensitive Data Scan Results window, the scan data is")
        b("permanently gone \u2014 nothing is saved, cached, or")
        b("recoverable. This is intentional.")
        blank()

        h("FALSE POSITIVES")
        b("Pattern-based detection produces false positives. For example:")
        b("\u2022 A 9-digit account number that looks like an SSN")
        b("\u2022 A tracking number that matches the credit card pattern")
        b("\u2022 The word 'password' in a help document")
        blank()
        b("Always review findings in context before taking action.")
        b("Click View Files to see the matched text with surrounding")
        b("context so you can quickly judge whether a finding is real.")
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

    def _show_sensitive_category_files(self, files_data, category, parent, regex=None):
        """Show files for a specific sensitive data category.

        If regex is provided, the View Text button opens the extracted-text
        view with that regex highlighted (so the user sees the actual PII
        matches for this category, not whatever is in the main search bar).
        """
        import tkinter as tk
        import subprocess, sys

        popup, _dark = self._themed_toplevel(parent)
        popup.title(f"Files containing: {category}")
        popup.resizable(True, True)
        popup.geometry("750x400")
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
            header_frame, text="?", width=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._show_category_files_help(popup),
        ).pack(side="right")

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
            popup, text="Double-click a file to open it in its default application — "
                        "from there you can edit the file to remove or redact the sensitive data. "
                        "Or select a file and click View Text below to review the "
                        "matches with line numbers highlighted.",
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
            bg="#FF6B35", fg="white",
            relief="raised", borderwidth=2,
            padx=20, pady=8, cursor="hand2",
        )
        view_btn.pack(side="left", padx=5)
        view_btn.bind("<Button-1>", lambda e: _view_text())
        view_btn.bind("<Enter>", lambda e: view_btn.configure(bg="#E55A2B"))
        view_btn.bind("<Leave>", lambda e: view_btn.configure(bg="#FF6B35"))

        ctk.CTkButton(
            popup, text="Close", width=80, font=ctk.CTkFont(size=12),
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=popup.destroy,
        ).pack(pady=(0, 10))

        self._apply_dark_theme(popup)


    def _show_category_files_help(self, parent):
        """Show help for the PII Scan category files popup."""
        import tkinter as tk
        help_win, _dark = self._themed_toplevel(parent)
        help_win.title("View Files — Help")
        help_win.geometry("650x520")
        help_win.resizable(True, True)
        help_win.transient(parent)
        try:
            help_win.grab_set()
        except Exception:
            help_win.after(150, lambda: help_win.grab_set() if help_win.winfo_exists() else None)

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

        def h(text):
            txt.insert("end", text + "\n", "heading")
        def h_red(text):
            txt.insert("end", text + "\n", "heading_red")
        def b(text):
            txt.insert("end", text + "\n", "body")
        def blank():
            txt.insert("end", "\n")

        h("VIEW FILES")
        b("This popup lists every file where the PII Scan found")
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
        b("  what the PII Scan detected, in context, without")
        b("  opening the original file.")
        blank()

        h_red("NO FILES ARE WRITTEN")
        b("The PII Scan shows results on screen only \u2014 it does")
        b("not write any report file to disk. This is a deliberate")
        b("safety measure to prevent concentrating sensitive data")
        b("(SSNs, credit card numbers, passwords) into a single")
        b("file that could be exposed.")
        blank()
        b("As soon as you close the Sensitive Data Scan Results window, the scan data is")
        b("permanently gone \u2014 nothing is saved, cached, or")
        b("recoverable. This is intentional. You can always re-run")
        b("the PII Scan to see the results again.")
        blank()

        h("FALSE POSITIVES")
        b("Pattern-based detection produces false positives. A")
        b("9-digit account number can look like an SSN, a tracking")
        b("number can match the credit card pattern, or the word")
        b("'password' can appear in a help document. Use View Text")
        b("to review each finding in context before taking action.")
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
                 "then just click Run Search. Close this window at any time to cancel \u2014 nothing changes until you click Apply.",
            font=ctk.CTkFont(size=13),
            wraplength=650, justify="center",
        ).pack(expand=True)
        ctk.CTkButton(
            header_frame, text="?", width=30,
            command=lambda: self._show_search_wizard_help(win),
            font=ctk.CTkFont(size=14, weight="bold"),
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

            ("Find SSNs", "Social Security numbers (XXX-XX-XXXX)",
             [],
             lambda v: self._apply_wizard(search_text=r"\d{3}-\d{2}-\d{4}", regex=True)),

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

            ("Regex pattern builder", "Opens a separate window with categorized regex presets (SSNs, invoices, part numbers, etc.).\n"
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
        try:
            help_win.grab_set()
        except Exception:
            help_win.after(150, lambda: help_win.grab_set() if help_win.winfo_exists() else None)

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
        b("Proximity — find two terms within N words of each other")
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
        b("Regex pattern builder — opens the categorized regex picker")
        b("with checkboxes for SSNs, invoice numbers, part numbers,")
        b("and dozens more patterns organized by profession.")
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



    def _open_search_wizard(self):
        """Open the Search Wizard popup for building regex patterns."""
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
        wiz.title("Search Wizard")
        wiz.resizable(True, True)
        wiz.geometry("560x640")
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 560) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 640) // 2
        wiz.geometry(f"+{x}+{y}")

        tk.Label(
            wiz, text="Search Wizard",
            font=("TkDefaultFont", 15, "bold"),
        ).pack(pady=(10, 2))
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
        try:
            win.grab_set()
        except Exception:
            win.after(150, lambda: win.grab_set() if win.winfo_exists() else None)

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
        try:
            help_win.grab_set()
        except Exception:
            help_win.after(150, lambda: help_win.grab_set() if help_win.winfo_exists() else None)
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
        b("archives, and 46 file types \u2014 all at once, all offline. Your")
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
        b("You don't need to use every feature. Start with a simple")
        b("keyword search and explore from there.")
        blank()

        h("GETTING STARTED")
        b("All searches are case-insensitive. Type your terms in the Search Bar,")
        b("pick a folder with Browse, and click Run Search. Use the checkboxes")
        b("under Advanced Search Options to change search modes \u2014 do not type flags in")
        b("the search box. Results are saved to peekdocs_results.txt and .docx.")
        blank()
        b("Quick tips: Click the \u25bc button next to the search bar to reuse one of")
        b("your last 10 searches. While a search is running, the status line shows")
        b("how many terms are being searched. In the Results Preview, right-click")
        b("to copy text and double-click a filename to open it in your default app.")
        blank()
        b("After a search, click the View N matched file(s) link on the status")
        b("line to see the list of files with match counts and line numbers.")
        b("Double-click a file to open it in its default app, or click View Text")
        b("(with line numbers) to see the file's extracted content with line")
        b("numbers and matches highlighted in yellow.")
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
        b("settings. Buttons like Clear Results and Delete Index only")
        b("delete files that peekdocs created \u2014 never your documents.")
        b("All peekdocs files are safe to delete manually too \u2014")
        b("peekdocs recreates them as needed.")
        blank()
        s("Search reports (overwritten each search)")
        e("peekdocs_results.txt       \u2014 text report")
        e("peekdocs_results.docx      \u2014 Word report with highlights")
        e("peekdocs_results.csv       \u2014 optional (-o csv)")
        e("peekdocs_results.json      \u2014 optional (-o json)")
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
        b("\u2022 Use Clear Results, Clear Error Log, or Delete Index to manage")
        b("  files from the GUI")
        blank()
        s("Building a search index")
        b("1. Browse to the folder you want to index")
        b("2. Click Manage Indexes (below Advanced Search Options)")
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
            "Search Mode Checkboxes", "Text Fields",
            "Combining Modes", "Settings Buttons", "Troubleshooting",
        ]:
            txt.insert("end", f"\u2022 {section}\n", "toc_item")
        txt.insert("end", "\n")

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
        e("\\d{3}-\\d{2}-\\d{4}     \u2192  SSN pattern (123-45-6789)")
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

        s("Proximity")
        b("Find terms that appear within N words of each other.")
        b("Requires 2 or more search terms. AND mode is applied automatically.")
        e("Terms: breach contract    Proximity: 5")
        e("\u2192  both words must appear within 5 words of each other")
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
        b("Set to 0 for unlimited.")
        blank()

        s("Max File Size (MB)")
        b("Skip files larger than this size. Default: 100 MB. Very large files")
        b("(huge PDFs, massive spreadsheets) can cause slow searches or exhaust")
        b("memory. Skipped files are logged to peekdocs_errors.log with a message")
        b("explaining why. Set to 0 for no limit if you need to search large files.")
        b("Changing this value automatically rebuilds the index on the next")
        b("indexed search, so results stay consistent.")
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
        b("Find files with both an SSN and a dollar amount in subfolders:")
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
        s("Whole Word + Proximity")
        b("'breach' and 'contract' as whole words within 5 words:")
        e("      Terms:  breach contract")
        e("Checkboxes:  Whole Word     Proximity: 5")
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
        b("Save all current Advanced Search Options as defaults to ~/.peekdocsrc.")
        b("These are restored automatically when peekdocs starts.")
        b("Not required for the current search \u2014 your selections take")
        b("effect immediately on the next Run Search. Save Defaults is")
        b("only for making your choices persist across sessions.")
        blank()
        b("This is different from Save Search on the main screen, which")
        b("saves the current search terms and settings by name so you")
        b("can reload them later. Save Defaults sets your preferred")
        b("starting configuration. Save Search saves a specific named")
        b("search.")
        s("Restore Settings")
        b("Reload saved defaults from ~/.peekdocsrc into the GUI.")
        s("Reset All Fields")
        b("Clear all fields and reset to defaults. Does not modify the config file.")
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
        try:
            help_win.grab_set()
        except Exception:
            help_win.after(150, lambda: help_win.grab_set() if help_win.winfo_exists() else None)

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
        b("folder, medical records in another, work projects in a third.")
        b("The searches you need for tax documents (W-2, 1099, deduction)")
        b("are completely different from the searches you need for medical")
        b("records (lab results, prescriptions, Dr. Smith). Keeping them")
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
        try:
            help_win.grab_set()
        except Exception:
            help_win.after(150, lambda: help_win.grab_set() if help_win.winfo_exists() else None)

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
        try:
            help_win.grab_set()
        except Exception:
            help_win.after(150, lambda: help_win.grab_set() if help_win.winfo_exists() else None)

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
            "Quick Start",
            "Buttons on This Panel",
            "Use Index Checkbox (Main Screen)",
            "Do I Need an Index?",
            "Good to Know",
        ]:
            txt.insert("end", f"\u2022 {section}\n", "toc_item")
        txt.insert("end", "\n")

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
        self._suite_popup = win
        win.protocol("WM_DELETE_WINDOW", lambda: (setattr(self, "_suite_popup", None), win.destroy()))
        win.title("Search Suites")
        win.resizable(True, True)
        win.geometry("880x520")
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 880) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 520) // 2
        win.geometry(f"+{x}+{y}")

        _sf = self._scaled_font

        # ── Header ──
        header = tk.Frame(win)
        header.pack(fill="x", padx=12, pady=(10, 5))
        tk.Label(header, text="Search Suites", font=_sf(14, "bold")).pack(side="left")
        ctk.CTkButton(
            header, text="?", width=30, height=26,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda: self._show_search_suites_help(win),
        ).pack(side="right")
        tk.Label(
            win,
            text="Group saved searches and run them together. Results go into a single combined report. "
                 "Suites are saved in the Search Folder shown below. To change it, update the Search Folder on the main screen, then reopen Search Suites.",
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
            from tkinter import simpledialog
            name = simpledialog.askstring("New Suite", "Suite name:", parent=win)
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
            from tkinter import simpledialog
            new_name = simpledialog.askstring(
                "Rename Suite", f"New name for '{current_suite[0]}':",
                parent=win, initialvalue=current_suite[0],
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

        ctk.CTkButton(left_btns, text="New", width=60, font=ctk.CTkFont(size=12), command=_new_suite).pack(side="left", padx=2)
        ctk.CTkButton(left_btns, text="Rename", width=70, font=ctk.CTkFont(size=12), command=_rename_suite_btn).pack(side="left", padx=2)
        ctk.CTkButton(left_btns, text="Delete", width=60, font=ctk.CTkFont(size=12),
                       fg_color="#CC3333", hover_color="#AA2222", command=_delete_suite).pack(side="left", padx=2)

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

            # Popup to pick a search
            pick_win, _ = self._themed_toplevel(win)
            pick_win.title("Add Search to Suite")
            pick_win.geometry("350x300")
            pick_win.transient(win)
            pick_win.grab_set()
            self.update_idletasks()
            px = win.winfo_rootx() + (win.winfo_width() - 350) // 2
            py = win.winfo_rooty() + (win.winfo_height() - 300) // 2
            pick_win.geometry(f"+{px}+{py}")

            tk.Label(pick_win, text="Select a saved search:", font=_sf(11, "bold")).pack(anchor="w", padx=10, pady=(10, 4))
            pick_lb = tk.Listbox(pick_win, font=_sf(11), exportselection=False)
            pick_lb.pack(fill="both", expand=True, padx=10, pady=(0, 5))
            for s in remaining:
                pick_lb.insert("end", s)

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

            ctk.CTkButton(pick_win, text="Add", width=80, font=ctk.CTkFont(size=12), command=_do_add).pack(pady=(0, 10))
            self._apply_dark_theme(pick_win)

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

        ctk.CTkButton(right_btns, text="Add Search", width=90, font=ctk.CTkFont(size=12), command=_add_search).pack(side="left", padx=2)
        ctk.CTkButton(right_btns, text="Remove", width=70, font=ctk.CTkFont(size=12), command=_remove_search).pack(side="left", padx=2)
        ctk.CTkButton(right_btns, text="\u25b2 Up", width=60, font=ctk.CTkFont(size=12), command=_move_up).pack(side="left", padx=2)
        ctk.CTkButton(right_btns, text="\u25bc Down", width=70, font=ctk.CTkFont(size=12), command=_move_down).pack(side="left", padx=2)

        # ── Output formats ──
        output_frame = tk.Frame(win)
        output_frame.pack(fill="x", padx=12, pady=(8, 2))
        tk.Label(output_frame, text="Suite report formats:", font=_sf(11, "bold")).pack(side="left", padx=(0, 8))

        # TXT and DOCX are always generated
        tk.Label(output_frame, text="TXT \u2713  DOCX \u2713", font=_sf(10), fg="gray").pack(side="left", padx=(0, 10))

        _suite_html_var = tk.BooleanVar(value=True)
        _suite_csv_var = tk.BooleanVar(value=False)
        _suite_json_var = tk.BooleanVar(value=False)
        _suite_pdf_var = tk.BooleanVar(value=False)

        tk.Checkbutton(output_frame, text="HTML", variable=_suite_html_var, font=_sf(10)).pack(side="left", padx=(0, 5))
        tk.Checkbutton(output_frame, text="CSV", variable=_suite_csv_var, font=_sf(10)).pack(side="left", padx=(0, 5))
        tk.Checkbutton(output_frame, text="JSON", variable=_suite_json_var, font=_sf(10)).pack(side="left", padx=(0, 5))
        tk.Checkbutton(output_frame, text="PDF", variable=_suite_pdf_var, font=_sf(10)).pack(side="left", padx=(0, 5))

        # ── Bottom: Run Suite + Close ──
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

        ctk.CTkButton(
            bottom, text="Run Suite", width=120,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#76BA1B", hover_color="#5E9516", text_color="white",
            command=_run_suite,
        ).pack()

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

    def _run_suite_searches(self, suite_name, search_names, folder, suite_formats=None):
        """Execute all searches in a suite sequentially using subprocess."""
        import threading
        import subprocess as _sp
        from peekdocs.collection import get_search_params
        from peekdocs.gui._helpers import _build_command_from_values
        from peekdocs.reporter import write_suite_txt_report, write_suite_docx_report, write_suite_html_report

        # Show progress bar and start elapsed timer — same as regular search
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        self.progress_bar.grid(
            row=5, column=0, columnspan=3, padx=10, pady=(2, 2), sticky="ew"
        )
        self.search_start_time = time.time()
        self._suite_elapsed_active = True
        self._suite_cancelled = False
        self.search_button.configure(text="Cancel", fg_color="red", hover_color="darkred",
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

                # Run via subprocess (same as regular search)
                import time
                start = time.time()
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                env["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
                try:
                    proc = _sp.Popen(
                        cmd, cwd=folder,
                        stdout=_sp.PIPE, stderr=_sp.PIPE,
                        text=True, encoding="utf-8", errors="replace",
                        env=env,
                    )
                    stdout, stderr = proc.communicate()
                except Exception:
                    continue
                elapsed = time.time() - start

                # Parse results from the generated txt report
                import re as _re
                matches = []
                all_files = []
                txt_result = os.path.join(folder, "peekdocs_results.txt")
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
                parsed_files = _parse_matched_files(folder, "peekdocs_results.txt")

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

            # Auto-redirect to a safe local folder if output dir is cloud-synced.
            from peekdocs.gui._helpers import check_cloud_folder, get_safe_output_dir
            cloud_warning = check_cloud_folder(folder)
            if cloud_warning:
                folder = get_safe_output_dir()

            # Generate combined suite reports
            # Set restrictive file permissions if enabled
            import peekdocs.reporter as _reporter_mod
            _reporter_mod.restrict_permissions = (
                getattr(self, "restrict_permissions_var", None)
                and self.restrict_permissions_var.get() == "on"
            )

            txt_path = os.path.join(folder, "peekdocs_suite_results.txt")
            docx_path = os.path.join(folder, "peekdocs_suite_results.docx")
            _fmts = suite_formats or {}
            write_suite_txt_report(txt_path, suite_name, sections)
            write_suite_docx_report(docx_path, txt_path, sections)
            html_path = ""
            csv_path = ""
            json_path = ""
            if _fmts.get("html", False):
                html_path = os.path.join(folder, "peekdocs_suite_results.html")
                try:
                    write_suite_html_report(html_path, suite_name, sections)
                except Exception:
                    html_path = ""
            if _fmts.get("csv", False):
                csv_path = os.path.join(folder, "peekdocs_suite_results.csv")
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
                json_path = os.path.join(folder, "peekdocs_suite_results.json")
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

            total_matches = sum(s.get("total_match_count", len(s["matches"])) for s in sections)
            total_elapsed = time.time() - self.search_start_time
            extra_paths = {"html": html_path, "csv": csv_path, "json": json_path}
            self.after(0, lambda: self._suite_finished(suite_name, sections, total_matches, txt_path, docx_path, total_elapsed, folder, html_path, extra_paths))

        threading.Thread(target=_run, daemon=True).start()

    def _suite_finished(self, suite_name, sections, total_matches, txt_path, docx_path, total_elapsed=0, folder="", html_path="", extra_paths=None):
        """Handle suite completion — show results summary and report buttons."""
        self._suite_elapsed_active = False
        self.search_start_time = None
        try:
            self.progress_bar.stop()
        except Exception:
            pass
        self.progress_bar.grid_remove()
        self.search_button.configure(text="Search", fg_color="#76BA1B", hover_color="#5E9516",
                                     text_color="white", command=self.start_search)

        import re as _re_fin

        total_matched_files_status = sum(s.get("matched_file_count", 0) for s in sections)
        total_files_searched = sum(len(s["all_files"]) for s in sections)

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

        # Build matched files list from the last search's peekdocs_results.txt
        # (each subprocess overwrites it, so the last one is current)
        from peekdocs.gui._helpers import _parse_matched_files
        if folder:
            self.matched_files = _parse_matched_files(folder, "peekdocs_results.txt")
        else:
            self.matched_files = []
        self._inverse_results = False

        # Show matched files button — use stdout-parsed count for display
        if total_matched_files_status > 0:
            link_text = f"{total_matched_files_status} Matched File(s)"
            self._matched_files_link.configure(text=link_text, fg_color="#FF6B35", hover_color="#E55A2B")
            self._matched_files_link.pack(side="left", padx=(5, 0))

        # Show View Suite Report buttons on the status bar
        import tkinter as tk

        # Remove any previous suite report buttons
        if hasattr(self, "_suite_report_frame"):
            self._suite_report_frame.destroy()

        self._suite_report_frame = tk.Frame(self._input_frame)
        self._suite_report_frame.grid(row=8, column=0, columnspan=3, padx=(10, 5), pady=(2, 5), sticky="w")

        tk.Label(self._suite_report_frame, text="View Suite Report:",
                 font=("TkDefaultFont", 11, "bold")).pack(side="left", padx=(0, 5))

        def _open_file(path):
            from peekdocs.gui._helpers import safe_open_file
            try:
                warning = safe_open_file(path)
                if warning:
                    self._show_error(warning)
            except Exception:
                pass

        if os.path.exists(docx_path):
            ctk.CTkButton(
                self._suite_report_frame, text="DOCX", width=60,
                font=ctk.CTkFont(size=11), fg_color="green", hover_color="darkgreen",
                command=lambda: _open_file(docx_path),
            ).pack(side="left", padx=2)

        if os.path.exists(txt_path):
            ctk.CTkButton(
                self._suite_report_frame, text="TXT", width=50,
                font=ctk.CTkFont(size=11), fg_color="green", hover_color="darkgreen",
                command=lambda: _open_file(txt_path),
            ).pack(side="left", padx=2)

        _ep = extra_paths or {}
        for fmt, label in [("html", "HTML"), ("csv", "CSV"), ("json", "JSON")]:
            path = _ep.get(fmt, "")
            if path and os.path.exists(path):
                ctk.CTkButton(
                    self._suite_report_frame, text=label, width=60,
                    font=ctk.CTkFont(size=11), fg_color="green", hover_color="darkgreen",
                    command=lambda p=path: _open_file(p),
                ).pack(side="left", padx=2)

        # Show results in preview
        if hasattr(self, "preview_frame"):
            self.preview_frame.grid()
        if hasattr(self, "preview_text"):
            self.preview_text.configure(state="normal")
            self.preview_text.delete("1.0", "end")
            self.preview_text.insert("end", f"Suite Report: {suite_name}\n", "filename")
            self.preview_text.insert("end", f"Searches: {len(sections)}, Found {total_matches} match(es) in {total_matched_files_status} file(s)\n\n")
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
                    self.preview_text.insert("end", f"  {fn}:{ln}: {text[:120]}\n")
                if len(s_matches) > 20:
                    self.preview_text.insert("end", f"  ... and {len(s_matches) - 20} more\n")
                self.preview_text.insert("end", "\n")
            self.preview_text.insert("end", f"\nClick DOCX or TXT above to open the full report.\n")
            self.preview_text.configure(state="disabled")

    def _cancel_suite(self):
        """Cancel a running suite search."""
        self._suite_cancelled = True
        self._suite_elapsed_active = False
        self.search_start_time = None
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        self.search_button.configure(text="Search", fg_color="#76BA1B", hover_color="#5E9516",
                                     text_color="white", command=self.start_search)
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
        help_win.geometry("640x520")
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

        b("What are Search Suites?")
        n("A search suite is a named group of saved searches that run")
        n("together with one click. Instead of running the same 5 or 10")
        n("searches one at a time, create a suite and run them all at once.")
        n("Results are combined into a single highlighted report.\n")

        b("How to Create a Suite")
        n("1. First, save some searches using the Save button on the main screen")
        n("2. Open Search Suites from the Tools menu")
        n("3. Click New to create a named suite")
        n("4. Click Add Search to add saved searches to the suite")
        n("5. Use \u25b2 Up and \u25bc Down to set the run order")
        n("6. Click Run Suite to execute all searches\n")

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

        b("Use Cases")
        n("\u2022 Pre-publication checklist \u2014 search for outdated terms, placeholder")
        n("  text, and sensitive data before publishing")
        n("\u2022 Quarterly audit \u2014 run the same compliance searches every quarter")
        n("\u2022 Onboarding review \u2014 search policy documents for required terms")
        n("\u2022 Any recurring workflow with multiple searches\n")

        b("CLI")
        n("Run a suite from the command line:")
        n("  peekdocs --suite \"My Suite\"\n")

        b("Storage — Why Per Folder?")
        n("Suites are saved in .peekdocs_collection.json alongside your")
        n("saved searches. Each folder has its own collection \u2014 if you")
        n("switch to a different Search Folder, you'll see a different set")
        n("of suites and saved searches. This is by design: the searches")
        n("you need for tax documents are different from the ones you need")
        n("for medical records, so each folder keeps only what's relevant.")
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

        ctk.CTkButton(
            help_win, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=help_win.destroy, font=ctk.CTkFont(size=12),
        ).pack(pady=(5, 10))

        self._apply_dark_theme(help_win)
