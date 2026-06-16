import { useEffect, useState } from "react";
import Modal from "./Modal";
import { getHistory } from "../api";

interface Props {
  onPick: (terms: string) => void;
  onClose: () => void;
}

export default function SearchHistoryModal({ onPick, onClose }: Props) {
  const [history, setHistory] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHistory()
      .then(setHistory)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  return (
    <Modal title="Search History" onClose={onClose} width={520}>
      <p className="muted small">
        Recent searches from <code>~/.peekdocs_history.json</code>. Click one
        to load it into the search bar.
      </p>
      {error && <div className="modal-error">{error}</div>}
      {history.length === 0 && !error && (
        <p className="muted small">No search history yet.</p>
      )}
      <ul className="saved-search-list">
        {history.map((h, i) => (
          <li key={`${h}-${i}`}>
            <button
              className="link-btn"
              onClick={() => {
                onPick(h);
                onClose();
              }}
            >
              {h}
            </button>
          </li>
        ))}
      </ul>
      <div className="modal-buttons">
        <button onClick={onClose}>Close</button>
      </div>
    </Modal>
  );
}
