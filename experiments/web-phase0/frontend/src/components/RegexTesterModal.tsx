import { useEffect, useState } from "react";
import Modal from "./Modal";

interface Props {
  onClose: () => void;
}

interface TestResp {
  matches?: Array<{ start: number; end: number; text: string }>;
  count?: number;
  error?: string;
}

const SAMPLE = `Order #INV-2024-0042 dated 09/15/2024 for $1,250.00 (15% deposit).
Contact: jane@example.com or +1 (415) 555-0123.
Reference: 24-CV-12345 — see also DWG-114002 (Rev. B2).
Bore diameter 120 mm at ±0.05 tolerance, pressure 300 psi.`;

export default function RegexTesterModal({ onClose }: Props) {
  const [pattern, setPattern] = useState(String.raw`\$[\d,]+\.?\d*`);
  const [text, setText] = useState(SAMPLE);
  const [caseSensitive, setCaseSensitive] = useState(false);
  const [result, setResult] = useState<TestResp | null>(null);

  // Live re-test as the user types (debounced).
  useEffect(() => {
    const t = setTimeout(async () => {
      try {
        const r = await fetch("http://127.0.0.1:8000/regex-test", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ pattern, text, case_sensitive: caseSensitive }),
        });
        const d = await r.json();
        setResult(d);
      } catch (e) {
        setResult({ error: e instanceof Error ? e.message : String(e), matches: [] });
      }
    }, 250);
    return () => clearTimeout(t);
  }, [pattern, text, caseSensitive]);

  // Render text with matches highlighted in yellow
  function highlightedText(): React.ReactNode {
    if (!result?.matches || result.matches.length === 0) return text;
    const parts: React.ReactNode[] = [];
    let last = 0;
    result.matches.forEach((m, i) => {
      if (m.start > last) parts.push(text.substring(last, m.start));
      parts.push(<mark key={i} className="hl">{text.substring(m.start, m.end)}</mark>);
      last = m.end;
    });
    if (last < text.length) parts.push(text.substring(last));
    return parts;
  }

  return (
    <Modal title="Regex Tester" onClose={onClose} width={720}>
      <p className="muted small">
        Live pattern testing. Type a regex and watch matches highlight in
        the sample text below.
      </p>

      <label className="modal-field">
        <span>Pattern</span>
        <input
          type="text"
          value={pattern}
          onChange={(e) => setPattern(e.target.value)}
          style={{ fontFamily: "monospace" }}
          autoFocus
        />
      </label>

      <div className="adv-checkrow" style={{ margin: "8px 0" }}>
        <label>
          <input
            type="checkbox"
            checked={caseSensitive}
            onChange={(e) => setCaseSensitive(e.target.checked)}
          />
          Case-sensitive
        </label>
        {result?.error && (
          <span style={{ color: "#c00", fontFamily: "monospace", fontSize: 11 }}>
            ✗ {result.error}
          </span>
        )}
        {!result?.error && result?.count !== undefined && (
          <span className="muted small">
            {result.count} match{result.count === 1 ? "" : "es"}
          </span>
        )}
      </div>

      <label className="modal-field">
        <span>Sample text</span>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={6}
          style={{ fontFamily: "monospace", fontSize: 12, padding: 8, width: "100%" }}
        />
      </label>

      <label className="modal-field">
        <span>Live preview</span>
        <div
          className="match-text"
          style={{
            padding: 10,
            background: "#fafafa",
            border: "1px solid #ddd",
            borderRadius: 4,
            fontFamily: "monospace",
            fontSize: 12,
            whiteSpace: "pre-wrap",
            minHeight: 100,
          }}
        >
          {highlightedText()}
        </div>
      </label>

      <div className="modal-buttons">
        <button onClick={onClose}>Close</button>
      </div>
    </Modal>
  );
}
