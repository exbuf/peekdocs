import { useEffect, useMemo, useState } from "react";
import Modal from "./Modal";

interface Props {
  onApply: (regexPattern: string) => void;
  onClose: () => void;
}

interface WizardData {
  categories: Array<{
    name: string;
    patterns: Array<{ name: string; pattern: string }>;
  }>;
}

export default function WizardModal({ onApply, onClose }: Props) {
  const [data, setData] = useState<WizardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState(0);
  const [checked, setChecked] = useState<Record<string, Set<string>>>({});
  const [mode, setMode] = useState<"OR" | "AND">("OR");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/wizard-patterns")
      .then((r) => r.json())
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  const selectedPatterns = useMemo(() => {
    if (!data) return [];
    const out: { name: string; pattern: string }[] = [];
    data.categories.forEach((cat) => {
      const set = checked[cat.name] || new Set();
      cat.patterns.forEach((p) => {
        if (set.has(p.name)) out.push(p);
      });
    });
    // De-duplicate by pattern string
    const seen = new Set<string>();
    return out.filter((p) => {
      if (seen.has(p.pattern)) return false;
      seen.add(p.pattern);
      return true;
    });
  }, [data, checked]);

  const combinedRegex = useMemo(() => {
    if (selectedPatterns.length === 0) return "";
    if (mode === "OR") {
      // Wrap each in (?:...) and join with |
      return selectedPatterns.map((p) => `(?:${p.pattern})`).join("|");
    } else {
      // AND mode — peekdocs's wizard joins with spaces for the search
      // bar. We render each as a separate quoted term.
      return selectedPatterns.map((p) => p.pattern).join(" ");
    }
  }, [selectedPatterns, mode]);

  function toggle(cat: string, name: string) {
    setChecked((prev) => {
      const next = { ...prev };
      const set = new Set(next[cat] || []);
      if (set.has(name)) set.delete(name);
      else set.add(name);
      next[cat] = set;
      return next;
    });
  }

  return (
    <Modal title="Regex Wizard" onClose={onClose} width={760}>
      <p className="muted small">
        Pick a category, check the patterns you want, choose OR (combine into
        one regex with alternation) or AND (each pattern as a separate term).
      </p>
      {error && <div className="modal-error">{error}</div>}

      {data && (
        <>
          <div className="wizard-tabs">
            {data.categories.map((c, i) => (
              <button
                key={c.name}
                className={`tab ${activeCategory === i ? "on" : ""}`}
                onClick={() => setActiveCategory(i)}
              >
                {c.name}
              </button>
            ))}
          </div>

          <div className="wizard-pattern-list">
            {data.categories[activeCategory].patterns.map((p) => {
              const isChecked = (checked[data.categories[activeCategory].name] || new Set()).has(p.name);
              return (
                <label key={p.name} className="wizard-pattern-row">
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => toggle(data.categories[activeCategory].name, p.name)}
                  />
                  <span className="wizard-pattern-name">{p.name}</span>
                  <code style={{ fontSize: 11 }}>{p.pattern}</code>
                </label>
              );
            })}
          </div>

          <div className="adv-checkrow" style={{ marginTop: 10 }}>
            <label>
              <input type="radio" checked={mode === "OR"} onChange={() => setMode("OR")} />
              OR (any match)
            </label>
            <label>
              <input type="radio" checked={mode === "AND"} onChange={() => setMode("AND")} />
              AND (all must match)
            </label>
            <span className="muted small">
              {selectedPatterns.length} selected
            </span>
          </div>

          {selectedPatterns.length > 0 && (
            <label className="modal-field">
              <span>Combined regex (preview)</span>
              <textarea
                readOnly
                value={combinedRegex}
                rows={2}
                style={{ fontFamily: "monospace", fontSize: 11, padding: 8, width: "100%" }}
                onFocus={(e) => e.target.select()}
              />
            </label>
          )}
        </>
      )}

      <div className="modal-buttons">
        <button onClick={onClose}>Cancel</button>
        <button
          className="primary"
          disabled={selectedPatterns.length === 0}
          onClick={() => {
            onApply(combinedRegex);
            onClose();
          }}
        >
          Apply to Search
        </button>
      </div>
    </Modal>
  );
}
