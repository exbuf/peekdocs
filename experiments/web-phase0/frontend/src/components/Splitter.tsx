import { useCallback, useEffect, useRef } from "react";

interface SplitterProps {
  // Current left-pane width as a percentage (0–100)
  leftPercent: number;
  // Setter; clamped by parent to a sensible min/max
  onChange: (pct: number) => void;
}

/**
 * Vertical splitter between the left and right panes.
 *
 * Native mousedown/mousemove/mouseup — no library. Pointer events
 * would be marginally better for touch, but desktop is the only
 * target right now.
 */
export default function Splitter({ leftPercent, onChange }: SplitterProps) {
  const dragging = useRef(false);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    dragging.current = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }, []);

  useEffect(() => {
    function onMouseMove(e: MouseEvent) {
      if (!dragging.current) return;
      // Convert pixel position to percentage of viewport width,
      // clamped to 20–80% so neither pane disappears.
      const pct = (e.clientX / window.innerWidth) * 100;
      const clamped = Math.max(20, Math.min(80, pct));
      onChange(clamped);
    }
    function onMouseUp() {
      if (!dragging.current) return;
      dragging.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    }
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, [onChange]);

  return (
    <div
      className="splitter"
      onMouseDown={onMouseDown}
      role="separator"
      aria-orientation="vertical"
      aria-valuenow={Math.round(leftPercent)}
      aria-valuemin={20}
      aria-valuemax={80}
      title="Drag to resize panes"
    >
      <div className="splitter-grip" />
    </div>
  );
}
