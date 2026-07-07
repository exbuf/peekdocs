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

    def _show_schedule_search_help(self, parent):
        """Help popup for Schedule Search."""
        import tkinter as tk
        help_win, _dark = self._themed_toplevel(parent)
        help_win.title("Schedule Search — Help")
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

        h("What does Schedule Search do?")
        b("It builds the exact command to run a saved Search Suite or Regex")
        b("Collection automatically on a schedule — daily, weekly, or monthly.")
        b("Pick what to run, the folder, and how often; this dialog generates")
        b("the command and the step-by-step setup instructions for your OS.")
        blank()

        h("Why doesn't peekdocs just run the schedule itself?")
        b("By design, peekdocs hands the command to your operating system's")
        b("own scheduler — cron/launchd on Mac and Linux, Task Scheduler on")
        b("Windows — rather than running the schedule from inside the app.")
        b("Three reasons:")
        blank()
        b("• The app isn't running when it's closed. A scheduled search has")
        b("  to fire on its own, across reboots, whether or not peekdocs is")
        b("  open. Only the OS scheduler can guarantee that. Running it from")
        b("  the app would require an always-on background process, which")
        b("  peekdocs deliberately does not have.")
        b("• It stays out of your system. Registering a schedule for you")
        b("  means silently editing your crontab or Windows Task Scheduler.")
        b("  A privacy-first tool should not write to your system scheduler")
        b("  behind your back.")
        b("• It's transparent. You see the exact command that will run and")
        b("  stay in control of it — nothing is hidden inside the app.")
        blank()
        b("So the split is simple: your OS owns the scheduling; peekdocs")
        b("owns building the correct command for it.")
        blank()

        h("How to set it up")
        b("1. Choose a Search Suite or Regex Collection, the folder, and how")
        b("   often to run.")
        b("2. Copy the generated command.")
        b("3. Follow the numbered instructions shown in the dialog for your")
        b("   operating system to register it with cron (Mac/Linux) or")
        b("   Task Scheduler (Windows).")
        blank()
        b("Results are appended to a JSON file in the search folder, so each")
        b("run adds to the record rather than overwriting it. Pair this with")
        b("Diff Snapshots to answer “what is new since last time?”")
        blank()

        h("Same idea on the CLI")
        b("Schedule Search only assembles a normal peekdocs command — you can")
        b("write it by hand and schedule it however you prefer. See the User")
        b("Guide → Automation and IT Use for the full pattern, including")
        b("diff-flavored exit codes for cron and CI pipelines.")

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
        header = tk.Frame(body)
        header.pack(fill="x", padx=15, pady=(10, 0))
        tk.Label(
            header, text="Schedule Search",
            font=("TkDefaultFont", 13, "bold"),
        ).pack(side="left")
        ctk.CTkButton(
            header, text="?", width=30, height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#1565C0", text_color="white",
            hover_color="#0D47A1",
            corner_radius=15,
            command=lambda: self._show_schedule_search_help(win),
        ).pack(side="right")
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

