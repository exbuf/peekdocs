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
# macOS needs a longer hide delay because we bind <Leave> on every
# inner child of composite CTk widgets (CTkCheckBox / CTkButton each
# wrap a tk.Canvas + a CTkLabel). The cursor crossing one of those
# internal borders fires a child Leave; without a big enough window
# for the matching Enter on the next child to cancel the hide, the
# tooltip would destroy + recreate on every internal sweep.
_HIDE_DELAY_MS = 300 if _IS_MACOS else 150


class Tooltip:
    """Simple hover tooltip for any widget."""

    # Class-level default OFF. _load_settings reads the saved
    # 'hover_text' preference from ~/.peekdocsrc and flips this on if
    # the user previously chose to enable tooltips. First-install /
    # factory-reset users see tooltips off until they click the
    # Tooltips: OFF button in the bottom toolbar.
    enabled = False

    def __init__(self, widget, text, anchor="right", position_widget=None):
        """Bind hover tooltip with the given text to a widget.

        position_widget — if supplied, use this widget's bounding box
        for positioning instead of `widget`. Use with anchor='center'
        to center the tooltip on a different region than the one that
        triggers it (e.g., bind to a label but display centered on
        the surrounding pane)."""
        self.widget = widget
        self.text = text
        self.anchor = anchor
        self.position_widget = position_widget if position_widget is not None else widget
        self.tip_window = None
        self._hide_id = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._schedule_hide)
        # Skip the children-bind loop for CTkOptionMenu widgets entirely.
        # An OptionMenu carries a _dropdown_menu Toplevel child that
        # lives at screen origin until it's opened, and binding Enter on
        # it caused tooltips from one OptionMenu to fire when the cursor
        # hovered a neighbor OptionMenu (e.g., hovering Language fired
        # the Preview-Size 'Results Preview' tooltip near the Language
        # picker, flickering, on macOS). The outer Enter on the
        # OptionMenu surface is enough for those widgets.
        _is_option_menu = hasattr(widget, "_dropdown_menu")
        if not _is_option_menu:
            # Bind to internal children (needed for CTk composite widgets
            # so the tooltip still fires when the cursor lands on the
            # inner canvas / label rather than the outer frame).
            for child in widget.winfo_children():
                child.bind("<Enter>", self._show)
                # Bind <Leave> on every child too. An earlier mac-only
                # workaround skipped this to fight jitter, but that
                # caused the opposite bug: tooltips never hid when the
                # cursor entered via an inner child (CTkCheckBox /
                # CTkButton wrap a canvas + label) and exited the
                # widget without ever touching the outer frame. The
                # bumped _HIDE_DELAY_MS (300 ms on macOS) absorbs the
                # internal Enter/Leave bounces that the cancel-on-Enter
                # path in _show catches in time.
                child.bind("<Leave>", self._schedule_hide)

    def _show(self, event=None):
        """Display the tooltip window near the widget on mouse enter."""
        # Cancel any pending hide — mouse re-entered the widget
        if self._hide_id is not None:
            self.widget.after_cancel(self._hide_id)
            self._hide_id = None
        if self.tip_window or not Tooltip.enabled:
            return
        # Defensive guard: only show if the cursor is genuinely inside
        # the widget's screen bounding box. Without this, spurious
        # <Enter> events delivered by Tk (observed on macOS with
        # CTkOptionMenu widgets, where hovering one OptionMenu would
        # fire tooltips bound to unrelated widgets elsewhere in the
        # window) could pop a tooltip with no cursor near it.
        if event is not None and hasattr(event, "x_root"):
            try:
                wx = self.widget.winfo_rootx()
                wy = self.widget.winfo_rooty()
                ww = self.widget.winfo_width()
                wh = self.widget.winfo_height()
                if not (wx <= event.x_root < wx + ww
                        and wy <= event.y_root < wy + wh):
                    return
            except Exception:
                pass
        try:
            import tkinter as tk

            # Initial x position; y for above-* is computed after the
            # tooltip is rendered so it never overlaps the widget.
            pw = self.position_widget
            if self.anchor == "left":
                x = pw.winfo_rootx() + pw.winfo_width() - 310
                y = pw.winfo_rooty() + pw.winfo_height() + _TOOLTIP_GAP_PX
            elif self.anchor in ("above", "above-left", "above-mid", "above-high", "above-row", "above-row-left"):
                x = pw.winfo_rootx()
                if self.anchor in ("above-left", "above-row-left"):
                    x = pw.winfo_rootx() + pw.winfo_width() - 310
                # Placeholder y; will be corrected after tooltip is laid out
                y = pw.winfo_rooty() - 200
            elif self.anchor == "center":
                # Placeholder; corrected after tooltip is laid out so
                # the final position is at the position_widget's center.
                x = pw.winfo_rootx() + pw.winfo_width() // 2
                y = pw.winfo_rooty() + pw.winfo_height() // 2
            else:
                x = pw.winfo_rootx() + 20
                y = pw.winfo_rooty() + pw.winfo_height() + _TOOLTIP_GAP_PX

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
                # Default 'above' — align BOTTOM edges via max(tip_h, 60)
                # floor. Short tooltips get lifted to a 60-px tip_h
                # baseline so their bottoms don't crowd the widget.
                y = pw.winfo_rooty() - max(tip_h, 60) - 24
                tw.wm_geometry(f"+{x}+{y}")
            elif self.anchor in ("above-row", "above-row-left"):
                # Row-aligned 'above' — align TOPS at a fixed offset
                # above the widget. 150-px floor covers the tallest
                # bottom-toolbar tooltip (Language ~120px, Tools ~110px),
                # so every above-row tooltip starts at widget_rooty - 180
                # regardless of its text length. Short tooltips (Close,
                # About) get a large gap between their bottom edge and
                # the widget; that's the trade for row-level alignment.
                # The -left variant additionally right-edge-anchors X so
                # the tooltip extends leftward — used for buttons on the
                # right side of the toolbar (Tools, About) so their
                # tooltips don't extend past the window edge.
                tw.update_idletasks()
                tip_h = tw.winfo_height()
                y = pw.winfo_rooty() - max(tip_h, 150) - 30
                tw.wm_geometry(f"+{x}+{y}")
            elif self.anchor == "center":
                tw.update_idletasks()
                tip_w = tw.winfo_width()
                tip_h = tw.winfo_height()
                x = pw.winfo_rootx() + (pw.winfo_width() - tip_w) // 2
                y = pw.winfo_rooty() + (pw.winfo_height() - tip_h) // 2
                tw.wm_geometry(f"+{x}+{y}")

            # Reveal the tooltip only after the final geometry is set,
            # so Cocoa never paints the placeholder frame to screen.
            if _IS_MACOS:
                tw.deiconify()
            # lift() pushes the tooltip Toplevel above sibling windows.
            # Replaces the earlier -topmost attribute which didn't
            # reliably keep wm_overrideredirect Toplevels above the
            # main window on Cocoa (tooltips would sink behind the app
            # and stay there). Harmless on Windows/Linux.
            try:
                tw.lift()
            except Exception:
                pass
        except Exception:
            self.tip_window = None

    def _schedule_hide(self, event=None):
        """Schedule tooltip hide with a short delay to prevent flicker on Linux."""
        # An earlier defensive guard here checked event.x_root/y_root
        # against the widget bounding box to skip hide-scheduling for
        # internal child→child bounces. It backfired: on Windows, Tk
        # fires <Leave> with the cursor position reported at the
        # widget's edge inclusively, so the guard treated genuine
        # widget-exits as bounces and the tooltip persisted indefinitely.
        # Removed. The Enter-cancellation in _show is sufficient to
        # prevent destroy/recreate on real internal bounces.
        if self._hide_id is not None:
            self.widget.after_cancel(self._hide_id)
        self._hide_id = self.widget.after(_HIDE_DELAY_MS, self._hide)

    def _hide(self, event=None):
        """Destroy the tooltip window."""
        self._hide_id = None
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None
