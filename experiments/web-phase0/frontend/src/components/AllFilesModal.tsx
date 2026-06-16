import { useEffect, useState } from "react";
import Modal from "./Modal";

interface Props {
  directory: string;
  onClose: () => void;
}

interface FilesResp {
  files: Array<{ path: string; size: number }>;
  total_bytes: number;
}

function fmtBytes(b: number): string {
  if (b < 1024) return `${b} B`;
  if (b < 1024 ** 2) return `${(b / 1024).toFixed(1)} KB`;
  if (b < 1024 ** 3) return `${(b / 1024 ** 2).toFixed(1)} MB`;
  return `${(b / 1024 ** 3).toFixed(2)} GB`;
}

export default function AllFilesModal({ directory, onClose }: Props) {
  const [data, setData] = useState<FilesResp | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(
      `http://127.0.0.1:8000/peekdocs-files?directory=${encodeURIComponent(directory)}`
    )
      .then((r) => r.json())
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [directory]);

  return (
    <Modal title="View All peekdocs Files" onClose={onClose} width={680}>
      <p className="muted small">
        Every file peekdocs has created under <code>{directory}</code>:
        results, reports, indexes, saved searches, error logs.
      </p>
      {error && <div className="modal-error">{error}</div>}
      {data && (
        <>
          <div className="tool-summary">
            <span>
              <strong>{data.files.length}</strong> files
            </span>
            <span>
              <strong>{fmtBytes(data.total_bytes)}</strong> total
            </span>
          </div>
          <ul className="saved-search-list">
            {data.files.map((f) => (
              <li key={f.path}>
                <code style={{ fontSize: 11 }}>{f.path}</code>
                <span className="muted small">{fmtBytes(f.size)}</span>
              </li>
            ))}
          </ul>
        </>
      )}
      <div className="modal-buttons">
        <button onClick={onClose}>Close</button>
      </div>
    </Modal>
  );
}
