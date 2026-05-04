"""Tooltip widget for peekdocs GUI."""


class Tooltip:
    """Simple hover tooltip for any widget."""

    enabled = True

    def __init__(self, widget, text, anchor="right"):
        """Bind hover tooltip with the given text to a widget."""
        self.widget = widget
        self.text = text
        self.anchor = anchor
        self.tip_window = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)
        # Bind to internal children (needed for CTk composite widgets)
        for child in widget.winfo_children():
            child.bind("<Enter>", self._show)
            child.bind("<Leave>", self._hide)

    def _show(self, event=None):
        """Display the tooltip window near the widget on mouse enter."""
        if self.tip_window or not Tooltip.enabled:
            return
        try:
            import tkinter as tk

            # Initial x position; y for above-* is computed after the
            # tooltip is rendered so it never overlaps the widget.
            if self.anchor == "left":
                x = self.widget.winfo_rootx() + self.widget.winfo_width() - 310
                y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
            elif self.anchor in ("above", "above-left", "above-mid", "above-high"):
                x = self.widget.winfo_rootx()
                if self.anchor == "above-left":
                    x = self.widget.winfo_rootx() + self.widget.winfo_width() - 310
                # Placeholder y; will be corrected after tooltip is laid out
                y = self.widget.winfo_rooty() - 200
            else:
                x = self.widget.winfo_rootx() + 20
                y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

            self.tip_window = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            display_text = self.text
            label = tk.Label(
                tw, text=display_text, background="#333333", foreground="white",
                relief="solid", borderwidth=1, font=("TkDefaultFont", 12),
                padx=6, pady=4, wraplength=300, justify="left",
            )
            label.pack()

            # For "above" variants, measure the rendered tooltip height
            # and place it so its bottom edge sits just above the widget.
            # This guarantees the tooltip never covers the widget itself,
            # regardless of how much text it contains.
            if self.anchor in ("above", "above-left", "above-mid", "above-high"):
                tw.update_idletasks()
                tip_h = tw.winfo_height()
                y = self.widget.winfo_rooty() - tip_h - 6
                tw.wm_geometry(f"+{x}+{y}")
        except Exception:
            self.tip_window = None

    def _hide(self, event=None):
        """Destroy the tooltip window on mouse leave."""
        if self.tip_window:
            # On Linux, moving the mouse into the tooltip itself triggers a
            # Leave event on the widget. Check if the pointer is still inside
            # the tooltip window before destroying it — prevents flicker loops.
            if event and self.tip_window.winfo_exists():
                try:
                    x = self.widget.winfo_pointerx()
                    y = self.widget.winfo_pointery()
                    tx = self.tip_window.winfo_rootx()
                    ty = self.tip_window.winfo_rooty()
                    tw = self.tip_window.winfo_width()
                    th = self.tip_window.winfo_height()
                    if tx <= x <= tx + tw and ty <= y <= ty + th:
                        return  # Pointer is over the tooltip — don't hide
                except Exception:
                    pass
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None
