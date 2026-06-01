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
        self._hide_id = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._schedule_hide)
        # Bind to internal children (needed for CTk composite widgets)
        for child in widget.winfo_children():
            child.bind("<Enter>", self._show)
            child.bind("<Leave>", self._schedule_hide)

    def _show(self, event=None):
        """Display the tooltip window near the widget on mouse enter."""
        # Cancel any pending hide — mouse re-entered the widget
        if self._hide_id is not None:
            self.widget.after_cancel(self._hide_id)
            self._hide_id = None
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
            #
            # Two defenses against the Enter/Leave flicker loop that
            # long "above" tooltips trigger if they overlap the widget:
            # (1) clamp tip_h to at least 60px in case winfo_height()
            # returns a partial value during measurement (Tk on macOS
            # occasionally does this); (2) widen the safety gap from
            # 6px to 24px so even a small height-measurement error
            # still keeps the tooltip clear of the widget.
            if self.anchor in ("above", "above-left", "above-mid", "above-high"):
                tw.update_idletasks()
                tip_h = tw.winfo_height()
                y = self.widget.winfo_rooty() - max(tip_h, 60) - 24
                tw.wm_geometry(f"+{x}+{y}")
        except Exception:
            self.tip_window = None

    def _schedule_hide(self, event=None):
        """Schedule tooltip hide with a short delay to prevent flicker on Linux."""
        if self._hide_id is not None:
            self.widget.after_cancel(self._hide_id)
        self._hide_id = self.widget.after(150, self._hide)

    def _hide(self, event=None):
        """Destroy the tooltip window."""
        self._hide_id = None
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None
