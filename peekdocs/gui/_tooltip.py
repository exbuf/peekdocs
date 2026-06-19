"""Tooltip widget for peekdocs GUI."""
import platform

# macOS Cocoa is the source of two tooltip-jitter symptoms that don't
# appear on Windows or Linux:
#   1. wm_overrideredirect(True) Toplevels still receive mouse-tracking
#      events, so a tooltip placed too close to the widget bounces the
#      cursor between widget and tooltip (Enter on tooltip fires Leave
#      on widget → schedule hide → cursor exits tooltip → show again).
#      Mitigation: bigger gap between widget edge and tooltip top.
#   2. The two-step "place placeholder → measure → reposition" used by
#      the above-* anchors paints the placeholder frame to screen on
#      Cocoa before the final geometry lands, producing a visible jump.
#      Mitigation: withdraw the window during the two-step dance and
#      deiconify it only once the final position is set.
_IS_MACOS = platform.system() == "Darwin"
_TOOLTIP_GAP_PX = 16 if _IS_MACOS else 5


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
        # Bind to internal children (needed for CTk composite widgets so
        # the tooltip still fires when the cursor lands on the inner
        # canvas / label rather than the outer frame).
        for child in widget.winfo_children():
            child.bind("<Enter>", self._show)
            # On macOS, skip the child <Leave> binding. macOS fires
            # Leave on inner children more aggressively as the cursor
            # crosses the implicit borders inside a CTk composite, and
            # each Leave→schedule_hide→Enter cycle was destroying and
            # recreating the tooltip — reading fresh winfo_rootx/y each
            # time and producing a visible position-shake. The outer
            # widget's Leave still fires when the cursor genuinely
            # leaves the widget, so hide still works correctly.
            if not _IS_MACOS:
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
                y = self.widget.winfo_rooty() + self.widget.winfo_height() + _TOOLTIP_GAP_PX
            elif self.anchor in ("above", "above-left", "above-mid", "above-high"):
                x = self.widget.winfo_rootx()
                if self.anchor == "above-left":
                    x = self.widget.winfo_rootx() + self.widget.winfo_width() - 310
                # Placeholder y; will be corrected after tooltip is laid out
                y = self.widget.winfo_rooty() - 200
            else:
                x = self.widget.winfo_rootx() + 20
                y = self.widget.winfo_rooty() + self.widget.winfo_height() + _TOOLTIP_GAP_PX

            self.tip_window = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)
            # On macOS, hide the window during the placeholder-paint dance
            # so only the final position is ever visible. Harmless on
            # other platforms; gated to Darwin to avoid changing behavior
            # where the issue doesn't occur.
            if _IS_MACOS:
                tw.withdraw()
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

            # Reveal the tooltip only after the final geometry is set,
            # so Cocoa never paints the placeholder frame to screen.
            if _IS_MACOS:
                tw.deiconify()
        except Exception:
            self.tip_window = None

    def _schedule_hide(self, event=None):
        """Schedule tooltip hide with a short delay to prevent flicker on Linux."""
        # If the cursor is still within the widget's bounding box, this
        # is an internal Enter/Leave bounce between composite children
        # — don't schedule a hide. Prevents the destroy/recreate cycle
        # that causes the tooltip to visibly shake on macOS as fresh
        # winfo_rootx/y reads land at slightly different pixel offsets.
        if event is not None and hasattr(event, "x_root"):
            try:
                wx = self.widget.winfo_rootx()
                wy = self.widget.winfo_rooty()
                ww = self.widget.winfo_width()
                wh = self.widget.winfo_height()
                if wx <= event.x_root < wx + ww and wy <= event.y_root < wy + wh:
                    return
            except Exception:
                pass
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
