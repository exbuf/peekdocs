import { useEffect, useState } from "react";
import Modal from "./Modal";
import {
  listRegexCollections,
  runRegexCollection,
  getRegexCollectionPatterns,
  updateRegexCollectionPatterns,
  type RegexPattern,
} from "../api";

interface Props {
  directory: string;
  onClose: () => void;
}

interface RegexRunResult {
  collection: string;
  total_matches: number;
  elapsed: number;
  pattern_results: Array<{
    name: string;
    pattern: string;
    match_count: number;
    files_count: number;
  }>;
}

type View = "list" | "patterns";

export default function RegexCollectionsModal({ directory, onClose }: Props) {
  const [view, setView] = useState<View>("list");
  const [collections, setCollections] = useState<string[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [patterns, setPatterns] = useState<RegexPattern[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RegexRunResult | null>(null);

  useEffect(() => {
    listRegexCollections()
      .then((d) => setCollections(d.collections))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  async function openPatterns(name: string) {
    setBusy(true);
    setError(null);
    try {
      const d = await getRegexCollectionPatterns(name);
      setActive(name);
      setPatterns(d.patterns);
      setView("patterns");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  function toggle(idx: number) {
    setPatterns((prev) =>
      prev.map((p, i) => (i === idx ? { ...p, enabled: !p.enabled } : p))
    );
  }

  function setAll(enabled: boolean) {
    setPatterns((prev) => prev.map((p) => ({ ...p, enabled })));
  }

  async function saveAndRun() {
    if (!active) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      await updateRegexCollectionPatterns(active, patterns);
      const r = (await runRegexCollection(active, directory)) as RegexRunResult;
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  const enabledCount = patterns.filter((p) => p.enabled).length;

  return (
    <Modal
      title={
        view === "list"
          ? "Regex Search Collections"
          : `Regex Search — ${active}`
      }
      onClose={onClose}
      width={680}
    >
      {error && <div className="modal-error">{error}</div>}

      {view === "list" && (
        <>
          <p className="muted small">
            Stored in <code>~/.peekdocs_regex_collections.json</code>. Click a
            collection to view its patterns, check the ones you want, then
            Save and Run against: <code>{directory}</code>
          </p>
          {collections.length === 0 && !error && (
            <p className="muted small">No regex collections yet.</p>
          )}
          {collections.length > 0 && (
            <ul className="saved-search-list">
              {collections.map((n) => (
                <li key={n}>
                  <button className="link-btn" onClick={() => openPatterns(n)}>
                    {n}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </>
      )}

      {view === "patterns" && (
        <>
          {!result && (
            <>
              <div className="adv-checkrow" style={{ marginBottom: 8 }}>
                <span className="muted small">
                  {enabledCount} of {patterns.length} enabled
                </span>
                <button onClick={() => setAll(true)} disabled={busy}>
                  Enable all
                </button>
                <button onClick={() => setAll(false)} disabled={busy}>
                  Disable all
                </button>
              </div>
              <ul className="saved-search-list">
                {patterns.map((p, i) => (
                  <li
                    key={i}
                    style={{ flexDirection: "column", alignItems: "flex-start" }}
                  >
                    <label
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                        width: "100%",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={p.enabled}
                        onChange={() => toggle(i)}
                      />
                      <strong>{p.name || "(unnamed)"}</strong>
                    </label>
                    <code style={{ fontSize: 11, marginLeft: 24 }}>
                      {p.regex || "(empty)"}
                    </code>
                  </li>
                ))}
              </ul>
              {enabledCount === 0 && (
                <p className="muted small" style={{ marginTop: 8 }}>
                  At least one pattern must be checked to run.
                </p>
              )}
            </>
          )}

          {result && (
            <div>
              <h4 style={{ marginTop: 16 }}>
                Collection "{result.collection}" — {result.total_matches} match
                {result.total_matches === 1 ? "" : "es"} ·{" "}
                {result.elapsed.toFixed(2)}s
              </h4>
              <ul className="saved-search-list">
                {result.pattern_results.map((pr) => (
                  <li key={pr.name}>
                    <span>
                      <strong>{pr.name}</strong>{" "}
                      <code style={{ fontSize: 11 }}>{pr.pattern}</code>
                    </span>
                    <span className="muted small">
                      {pr.match_count} match{pr.match_count === 1 ? "" : "es"} ·{" "}
                      {pr.files_count} file{pr.files_count === 1 ? "" : "s"}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      <div className="modal-buttons">
        {view === "patterns" && (
          <button
            onClick={() => {
              setView("list");
              setActive(null);
              setPatterns([]);
              setResult(null);
            }}
            disabled={busy}
          >
            ← Back
          </button>
        )}
        <button onClick={onClose}>Close</button>
        {view === "patterns" && !result && (
          <button
            className="primary"
            disabled={busy || enabledCount === 0}
            onClick={saveAndRun}
          >
            {busy ? "Running…" : "Save and Run"}
          </button>
        )}
      </div>
    </Modal>
  );
}
