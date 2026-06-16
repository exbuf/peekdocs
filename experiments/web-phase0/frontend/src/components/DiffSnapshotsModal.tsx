import { useState } from "react";
import Modal from "./Modal";

interface Props {
  onClose: () => void;
}

interface DiffResp {
  new: Array<{ filename: string; count: number }>;
  removed: Array<{ filename: string; count: number }>;
  changed: Array<{ filename: string; old: number; new: number }>;
  unchanged_summary: { count: number; total_matches: number };
}

export default function DiffSnapshotsModal({ onClose }: Props) {
  const [oldPath, setOldPath] = useState("");
  const [newPath, setNewPath] = useState("");
  const [result, setResult] = useState<DiffResp | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function pickFile(target: (s: string) => void) {
    const r = await fetch("http://127.0.0.1:8000/pick-file", { method: "POST" });
    const d = await r.json();
    if (d.path) target(d.path);
  }

  async function onCompare() {
    if (!oldPath || !newPath) {
      setError("Both snapshot files are required");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const r = await fetch("http://127.0.0.1:8000/diff-snapshots", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ old_path: oldPath, new_path: newPath }),
      });
      if (!r.ok) throw new Error(await r.text());
      setResult(await r.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="Diff Snapshots" onClose={onClose} width={620}>
      <p className="muted small">
        Compare two peekdocs JSON snapshots ({" "}
        <code>peekdocs ... --stdout {">"} snapshot.json</code>) and show what's
        new, removed, changed, or unchanged. Useful for periodic scans.
      </p>

      <label className="modal-field">
        <span>Old snapshot</span>
        <div style={{ display: "flex", gap: 4 }}>
          <input
            type="text"
            value={oldPath}
            placeholder="/path/to/old_snapshot.json"
            onChange={(e) => setOldPath(e.target.value)}
            style={{ flex: 1 }}
          />
          <button onClick={() => pickFile(setOldPath)}>Browse</button>
        </div>
      </label>

      <label className="modal-field">
        <span>New snapshot</span>
        <div style={{ display: "flex", gap: 4 }}>
          <input
            type="text"
            value={newPath}
            placeholder="/path/to/new_snapshot.json"
            onChange={(e) => setNewPath(e.target.value)}
            style={{ flex: 1 }}
          />
          <button onClick={() => pickFile(setNewPath)}>Browse</button>
        </div>
      </label>

      {error && <div className="modal-error">{error}</div>}

      {result && (
        <div style={{ marginTop: 12 }}>
          <h4 style={{ fontSize: 13, color: "#2e7d32" }}>
            NEW ({result.new.length})
          </h4>
          {result.new.length === 0 ? (
            <p className="muted small">none</p>
          ) : (
            <ul className="saved-search-list">
              {result.new.map((f) => (
                <li key={f.filename}>
                  <code>{f.filename}</code>
                  <span className="muted small">+{f.count}</span>
                </li>
              ))}
            </ul>
          )}

          <h4 style={{ fontSize: 13, color: "#f57c00" }}>
            CHANGED ({result.changed.length})
          </h4>
          {result.changed.length === 0 ? (
            <p className="muted small">none</p>
          ) : (
            <ul className="saved-search-list">
              {result.changed.map((f) => (
                <li key={f.filename}>
                  <code>{f.filename}</code>
                  <span className="muted small">
                    {f.old} → {f.new}
                  </span>
                </li>
              ))}
            </ul>
          )}

          <h4 style={{ fontSize: 13, color: "#c62828" }}>
            REMOVED ({result.removed.length})
          </h4>
          {result.removed.length === 0 ? (
            <p className="muted small">none</p>
          ) : (
            <ul className="saved-search-list">
              {result.removed.map((f) => (
                <li key={f.filename}>
                  <code>{f.filename}</code>
                  <span className="muted small">−{f.count}</span>
                </li>
              ))}
            </ul>
          )}

          <p className="muted small" style={{ marginTop: 8 }}>
            <strong>UNCHANGED:</strong> {result.unchanged_summary.count} files /{" "}
            {result.unchanged_summary.total_matches} matches
          </p>
        </div>
      )}

      <div className="modal-buttons">
        <button onClick={onClose}>Close</button>
        <button className="primary" disabled={busy} onClick={onCompare}>
          {busy ? "Comparing…" : "Compare"}
        </button>
      </div>
    </Modal>
  );
}
