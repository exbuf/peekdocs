import { useState } from "react";
import Modal from "./Modal";
import { saveSavedSearch, type SearchRequest } from "../api";

interface Props {
  params: SearchRequest;
  onClose: () => void;
}

export default function SaveSearchModal({ params, onClose }: Props) {
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSave() {
    if (!name.trim()) {
      setError("Name is required");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      // Save the full params object so Reload restores exactly the
      // same configuration. The backend uses peekdocs.collection's
      // add_saved_search which roundtrips JSON cleanly.
      await saveSavedSearch(name.trim(), params.directory, params);
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="Save Search" onClose={onClose} width={460}>
      <p className="muted small">
        Saves the current configuration (terms + every option you've set) to
        the folder's <code>.peekdocs_collection.json</code> file. You can
        reload it later by name.
      </p>
      <label className="modal-field">
        <span>Save as name</span>
        <input
          type="text"
          autoFocus
          value={name}
          placeholder="quarterly_budget_check"
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") onSave();
          }}
        />
      </label>
      {error && <div className="modal-error">{error}</div>}
      <div className="modal-buttons">
        <button onClick={onClose}>Cancel</button>
        <button className="primary" disabled={busy} onClick={onSave}>
          {busy ? "Saving…" : "Save"}
        </button>
      </div>
    </Modal>
  );
}
