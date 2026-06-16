import { useEffect, useState } from "react";
import Modal from "./Modal";
import { listRegexCollections, runRegexCollection } from "../api";

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

export default function RegexCollectionsModal({ directory, onClose }: Props) {
  const [collections, setCollections] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<string | null>(null);
  const [result, setResult] = useState<RegexRunResult | null>(null);

  useEffect(() => {
    listRegexCollections()
      .then((d) => setCollections(d.collections))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, []);

  async function onRun(name: string) {
    setRunning(name);
    setError(null);
    setResult(null);
    try {
      const r = (await runRegexCollection(name, directory)) as RegexRunResult;
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(null);
    }
  }

  return (
    <Modal title="Regex Search Collections" onClose={onClose} width={620}>
      <p className="muted small">
        Regex collections are stored in <code>~/.peekdocs_regex_collections.json</code>{" "}
        and the seeded <strong>Examples</strong> collection has 17 universal
        patterns (email, URL, dates, etc.). Running a collection against:{" "}
        <code>{directory}</code>
      </p>

      {loading && <p>Loading…</p>}
      {error && <div className="modal-error">{error}</div>}

      {!loading && collections.length === 0 && !error && (
        <p className="muted small">No regex collections yet.</p>
      )}

      {collections.length > 0 && !result && (
        <ul className="saved-search-list">
          {collections.map((n) => (
            <li key={n}>
              <button className="link-btn" onClick={() => onRun(n)}>
                {n}
              </button>
              {running === n && (
                <span className="muted small"> · running…</span>
              )}
            </li>
          ))}
        </ul>
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
          <button className="link-btn" onClick={() => setResult(null)}>
            ← back to collections
          </button>
        </div>
      )}

      <div className="modal-buttons">
        <button onClick={onClose}>Close</button>
      </div>
    </Modal>
  );
}
