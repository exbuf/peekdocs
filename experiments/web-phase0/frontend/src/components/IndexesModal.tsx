import { useEffect, useState } from "react";
import Modal from "./Modal";

interface Props {
  directory: string;
  onClose: () => void;
}

interface IndexInfo {
  exists: boolean;
  path: string;
  size_bytes: number;
}

function fmtBytes(b: number): string {
  if (b < 1024) return `${b} B`;
  if (b < 1024 ** 2) return `${(b / 1024).toFixed(1)} KB`;
  if (b < 1024 ** 3) return `${(b / 1024 ** 2).toFixed(1)} MB`;
  return `${(b / 1024 ** 3).toFixed(2)} GB`;
}

export default function IndexesModal({ directory, onClose }: Props) {
  const [info, setInfo] = useState<IndexInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [recursive, setRecursive] = useState(true);

  async function load() {
    setError(null);
    try {
      const r = await fetch(
        `http://127.0.0.1:8000/indexes/info?directory=${encodeURIComponent(directory)}`
      );
      if (!r.ok) throw new Error(await r.text());
      setInfo(await r.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [directory]);

  async function onBuild() {
    setBusy(true);
    setError(null);
    try {
      const r = await fetch("http://127.0.0.1:8000/indexes/build", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ directory, recursive, use_ocr: false }),
      });
      if (!r.ok) throw new Error(await r.text());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onDelete() {
    if (!confirm(`Delete the index for ${directory}? Searches will read files directly afterwards.`))
      return;
    setBusy(true);
    setError(null);
    try {
      const r = await fetch(
        `http://127.0.0.1:8000/indexes?directory=${encodeURIComponent(directory)}`,
        { method: "DELETE" }
      );
      if (!r.ok) throw new Error(await r.text());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="Indexes" onClose={onClose} width={560}>
      <p className="muted small">
        SQLite FTS5 index at <code>{directory}/.peekdocs.db</code>. Build
        once and subsequent searches with <strong>Use Index</strong> checked
        run in milliseconds.
      </p>
      {error && <div className="modal-error">{error}</div>}
      {info && (
        <table className="check-table">
          <tbody>
            <tr>
              <th>Status</th>
              <td>
                {info.exists ? (
                  <span style={{ color: "#2e7d32" }}>✓ built</span>
                ) : (
                  <span style={{ color: "#999" }}>not built</span>
                )}
              </td>
            </tr>
            <tr><th>Path</th><td><code>{info.path}</code></td></tr>
            <tr><th>Size</th><td>{fmtBytes(info.size_bytes)}</td></tr>
          </tbody>
        </table>
      )}
      <div className="adv-checkrow" style={{ marginTop: 12 }}>
        <label>
          <input
            type="checkbox"
            checked={recursive}
            onChange={(e) => setRecursive(e.target.checked)}
          />
          Recursive (include subfolders when building)
        </label>
      </div>
      <div className="modal-buttons">
        <button onClick={onClose}>Close</button>
        {info?.exists && (
          <button onClick={onDelete} disabled={busy}>
            Delete Index
          </button>
        )}
        <button className="primary" onClick={onBuild} disabled={busy}>
          {busy ? "Building…" : info?.exists ? "Rebuild Index" : "Build Index"}
        </button>
      </div>
    </Modal>
  );
}
