import { useEffect, useState } from "react";
import Modal from "./Modal";
import { getSystemCheck } from "../api";

interface Props {
  onClose: () => void;
}

interface CheckInfo {
  peekdocs_version: string;
  python_version: string;
  platform: string;
  free_disk_gb: number;
  sqlite_version: string;
  tesseract_available: boolean;
  tesseract_version: string | null;
  dependencies: Record<string, string | null>;
}

export default function SystemCheckModal({ onClose }: Props) {
  const [info, setInfo] = useState<CheckInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSystemCheck()
      .then((d) => setInfo(d as unknown as CheckInfo))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  return (
    <Modal title="System Check" onClose={onClose} width={640}>
      {error && <div className="modal-error">{error}</div>}
      {!info && !error && <p>Loading…</p>}
      {info && (
        <>
          <table className="check-table">
            <tbody>
              <tr><th>peekdocs version</th><td>{info.peekdocs_version}</td></tr>
              <tr><th>Python</th><td>{info.python_version}</td></tr>
              <tr><th>Platform</th><td>{info.platform}</td></tr>
              <tr><th>SQLite</th><td>{info.sqlite_version}</td></tr>
              <tr>
                <th>Tesseract (OCR)</th>
                <td>
                  {info.tesseract_available ? (
                    <span style={{ color: "#2e7d32" }}>
                      ✓ available {info.tesseract_version ? `· ${info.tesseract_version}` : ""}
                    </span>
                  ) : (
                    <span style={{ color: "#999" }}>
                      not installed (optional — needed only for OCR on scanned PDFs/images)
                    </span>
                  )}
                </td>
              </tr>
              <tr><th>Free disk</th><td>{info.free_disk_gb} GB</td></tr>
            </tbody>
          </table>

          <h4 style={{ marginTop: 16, fontSize: 14 }}>Dependencies</h4>
          <table className="check-table">
            <tbody>
              {Object.entries(info.dependencies).map(([name, ver]) => (
                <tr key={name}>
                  <th>{name}</th>
                  <td>
                    {ver ? (
                      <span style={{ color: "#2e7d32" }}>{ver}</span>
                    ) : (
                      <span style={{ color: "#999" }}>missing</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
      <div className="modal-buttons">
        <button onClick={onClose}>Close</button>
      </div>
    </Modal>
  );
}
