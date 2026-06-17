import {
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

interface TooltipProps {
  text: string | undefined;
  disabled?: boolean;
  placement?: "top" | "bottom" | "right" | "left";
  children: ReactNode;
  delay?: number;
}

/**
 * Lightweight hover tooltip. Uses a portal-less popover with absolute
 * positioning relative to the wrapper. ~250ms delay before appearing
 * so it doesn't fire on accidental hover, immediate dismiss on leave.
 *
 * Passes through the underlying `title` attribute as well so:
 * - Accessibility tools and keyboard users still get it
 * - Tests that read DOM titles still work
 * - If the user has Tooltips OFF, both visual and title go away
 */
export default function Tooltip({
  text,
  disabled,
  placement = "bottom",
  children,
  delay = 250,
}: TooltipProps) {
  const [show, setShow] = useState(false);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (timer.current) window.clearTimeout(timer.current);
    };
  }, []);

  function onEnter() {
    if (disabled || !text) return;
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setShow(true), delay);
  }

  function onLeave() {
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = null;
    setShow(false);
  }

  if (disabled || !text) {
    return <>{children}</>;
  }

  return (
    <span
      className="tt-wrap"
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      onFocus={onEnter}
      onBlur={onLeave}
      title={text}
    >
      {children}
      {show && <span className={`tt-pop tt-${placement}`}>{text}</span>}
    </span>
  );
}
