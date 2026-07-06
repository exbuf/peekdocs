"""Themed dialog + OS-file-open helpers.

Splitting concern from the former ``gui/_helpers.py`` grab-bag.
Contains only the small, focused helpers that other mixins call to
present a themed input prompt or hand a file off to the OS.
"""
from __future__ import annotations

import os
import platform
import subprocess


def themed_ask_string(parent, title, prompt, initial=""):
    """Modal text-input dialog centered over *parent*.

    Replacement for ``tkinter.simpledialog.askstring`` that uses
    ``CTkToplevel`` plus manual centering so the popup reliably appears
    over the parent window. ``simpledialog.askstring`` on macOS can
    position the dialog far from the parent (or near a screen edge),
    depending on Tk version and HiDPI scaling — observed in practice
    with the Save Collection As dialog appearing partly off-screen.

    Returns the entered string (an empty string is a valid result), or
    ``None`` if the user cancelled / closed the dialog.
    """
    import customtkinter as ctk
    import tkinter as tk

    parent.update_idletasks()
    w, h = 380, 160
    result = [None]

    win = ctk.CTkToplevel(parent)
    win.title(title)
    win.geometry(f"{w}x{h}")
    win.resizable(False, False)

    # Center on parent (manually — no reliance on Tk's positioning).
    px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
    py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
    win.geometry(f"+{px}+{py}")
    win.transient(parent)

    # X11 / Linux: grab_set fails on a not-yet-viewable window. Wait
    # for visibility, then grab as best-effort.
    win.update_idletasks()
    try:
        win.wait_visibility()
    except tk.TclError:
        pass
    try:
        win.grab_set()
    except tk.TclError:
        pass

    ctk.CTkLabel(win, text=prompt, font=ctk.CTkFont(size=12)).pack(
        padx=15, pady=(15, 5), anchor="w")
    entry = ctk.CTkEntry(win, font=ctk.CTkFont(size=12))
    entry.pack(padx=15, fill="x")
    if initial:
        entry.insert(0, initial)
    entry.focus_set()

    def _ok(_event=None):
        result[0] = entry.get()
        win.destroy()

    def _cancel(_event=None):
        result[0] = None
        win.destroy()

    btn_row = tk.Frame(win)
    btn_row.pack(side="bottom", pady=(0, 12))
    ctk.CTkButton(btn_row, text="OK", width=80,
                  font=ctk.CTkFont(size=12),
                  command=_ok).pack(side="left", padx=4)
    ctk.CTkButton(btn_row, text="Cancel", width=80,
                  font=ctk.CTkFont(size=12),
                  fg_color="transparent", text_color=("gray30", "gray70"),
                  hover_color=("gray90", "gray25"),
                  command=_cancel).pack(side="left", padx=4)

    entry.bind("<Return>", _ok)
    entry.bind("<Escape>", _cancel)
    win.protocol("WM_DELETE_WINDOW", _cancel)

    # Bring to front and focus the entry on first render.
    win.lift()
    win.focus_force()
    entry.focus_set()

    parent.wait_window(win)
    return result[0]


def safe_open_file(filepath):
    """Open *filepath* with the OS default handler for its extension.

    Always returns ``None``. The return value exists for backwards
    compatibility with callers that historically displayed a warning
    string when the open failed; today the OS surfaces its own error
    if no handler is registered.
    """
    system = platform.system()
    if system == "Windows":
        os.startfile(filepath)  # type: ignore[attr-defined]
    elif system == "Darwin":
        subprocess.Popen(["open", filepath])
    else:
        subprocess.Popen(["xdg-open", filepath])
    return None
