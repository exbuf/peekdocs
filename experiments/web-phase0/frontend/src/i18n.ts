// Web UI i18n. Fetches the active-language strings from the backend
// (which proxies to peekdocs/i18n.py — 134 keys × 7 languages already
// available) and exposes a small t() function with English fallback.
//
// The web UI only uses a subset of the tkinter labels; everything not
// covered by the catalog falls back to the English passed in by the
// caller.

import { useEffect, useState } from "react";

let strings: Record<string, string> = {};
const subscribers = new Set<() => void>();

export async function setLanguage(lang: string): Promise<void> {
  if (lang === "en") {
    strings = {};
  } else {
    try {
      const r = await fetch(`http://127.0.0.1:8000/i18n/${lang}`);
      const d = await r.json();
      strings = (d.strings as Record<string, string>) || {};
    } catch {
      strings = {};
    }
  }
  subscribers.forEach((s) => s());
}

export function t(key: string, fallback: string): string {
  // peekdocs/i18n.py label values often include space-padding meant for
  // the tkinter widget (e.g. " Step 1 "). The web GUI uses CSS padding,
  // so strip leading/trailing whitespace.
  const v = strings[key];
  return v != null ? v.trim() : fallback;
}

export function useI18n(): { t: typeof t } {
  const [, setTick] = useState(0);
  useEffect(() => {
    const sub = () => setTick((x) => x + 1);
    subscribers.add(sub);
    return () => {
      subscribers.delete(sub);
    };
  }, []);
  return { t };
}
