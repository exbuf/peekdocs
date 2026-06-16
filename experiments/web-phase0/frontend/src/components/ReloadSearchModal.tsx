import { useEffect, useState } from "react";
import Modal from "./Modal";
import {
  listSavedSearches,
  loadSavedSearch,
  deleteSavedSearch,
  type SearchRequest,
} from "../api";

interface Props {
  directory: string;
  onLoad: (patch: Partial<SearchRequest>) => void;
  onClose: () => void;
}

export default function ReloadSearchModal({ directory, onLoad, onClose }: Props) {
  const [names, setNames] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const list = await listSavedSearches(directory);
      setNames(list);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [directory]);

  async function onPickName(name: string) {
    try {
      const params = await loadSavedSearch(name, directory);
      onLoad(params);
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function onDelete(name: string) {
    if (!confirm(`Delete saved search "${name}"?`)) return;
    try {
      await deleteSavedSearch(name, directory);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <Modal title="Reload Saved Search" onClose={onClose} width={500}>
      <p className="muted small">
        Saved searches for: <code>{directory}</code>
      </p>
      {loading && <p>Loading…</p>}
      {error && <div className="modal-error">{error}</div>}
      {!loading && names.length === 0 && (
        <p className="muted small">
          No saved searches yet for this folder. Use <strong>Save</strong> next
          to the search bar to save the current configuration by name.
        </p>
      )}
      {names.length > 0 && (
        <ul className="saved-search-list">
          {names.map((n) => (
            <li key={n}>
              <button className="link-btn" onClick={() => onPickName(n)}>
                {n}
              </button>
              <button
                className="del-btn"
                onClick={() => onDelete(n)}
                title="Delete this saved search"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className="modal-buttons">
        <button onClick={onClose}>Close</button>
      </div>
    </Modal>
  );
}
