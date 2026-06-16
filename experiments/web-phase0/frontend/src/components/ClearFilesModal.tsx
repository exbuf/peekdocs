import { useState } from "react";
import Modal from "./Modal";

interface Props {
  directory: string;
  kind: "clear" | "clean";
  onClose: () => void;
}

interface ClearResp {
  deleted: string[];
  failed: string[];
  count: number;
}

export default function ClearFilesModal({ directory, kind, onClose }: Props) {
  const [target, setTarget] = useState(directory);
  const [includeIndex, setIncludeIndex] = useState(false);
  const [includeReports, setIncludeReports] = useState(false);
  const [includeSaved, setIncludeSaved] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ClearResp | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onClear() {
    if (!target) {
      setError("Target folder is required");
      return;
    }
    if (
      !confirm(
        `Delete peekdocs-generated files in:\n\n${target}\n\nThis cannot be undone.`
      )
    )
      return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/peekdocs-files/clear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          directory: target,
          include_index: includeIndex,
          include_reports: includeReports,
          include_saved_searches: includeSaved,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal
      title={kind === "clear" ? "Clear Files" : "Clean Folder"}
      onClose={onClose}
      width={520}
    >
      <p className="muted small">
        Deletes peekdocs-generated files. Standard / suite / regex result
        files and the error log are always deleted. The three checkboxes
        below include additional categories. <strong>Your own documents
        are never touched.</strong>
      </p>
      {kind === "clean" && (
        <label className="modal-field">
          <span>Target folder</span>
          <input
            type="text"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
          />
        </label>
      )}
      <div className="adv-checkrow" style={{ marginTop: 10 }}>
        <label>
          <input
            type="checkbox"
            checked={includeReports}
            onChange={(e) => setIncludeReports(e.target.checked)}
          />
          Saved reports (peekdocs_report_*, peekdocs_accumulated_*)
        </label>
      </div>
      <div className="adv-checkrow">
        <label>
          <input
            type="checkbox"
            checked={includeIndex}
            onChange={(e) => setIncludeIndex(e.target.checked)}
          />
          Search index (.peekdocs.db)
        </label>
      </div>
      <div className="adv-checkrow">
        <label>
          <input
            type="checkbox"
            checked={includeSaved}
            onChange={(e) => setIncludeSaved(e.target.checked)}
          />
          Saved searches (.peekdocs_collection.json)
        </label>
      </div>
      {error && <div className="modal-error">{error}</div>}
      {result && (
        <div style={{ marginTop: 12 }}>
          <p>
            Deleted <strong>{result.count}</strong> file
            {result.count === 1 ? "" : "s"}.
          </p>
          {result.failed.length > 0 && (
            <div className="modal-error">
              {result.failed.length} failure(s): {result.failed.slice(0, 3).join("; ")}
            </div>
          )}
        </div>
      )}
      <div className="modal-buttons">
        <button onClick={onClose}>Close</button>
        <button className="primary" disabled={busy} onClick={onClear}>
          {busy ? "Deleting…" : "Delete"}
        </button>
      </div>
    </Modal>
  );
}
