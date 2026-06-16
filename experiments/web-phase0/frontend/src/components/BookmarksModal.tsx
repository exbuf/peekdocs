import { useEffect, useState } from "react";
import Modal from "./Modal";

interface Props {
  onClose: () => void;
}

interface BookmarksResp {
  bookmarks: Array<{ path: string; name?: string; folder?: string }>;
}

export default function BookmarksModal({ onClose }: Props) {
  const [data, setData] = useState<BookmarksResp | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/bookmarks")
      .then((r) => r.json())
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  return (
    <Modal title="Bookmarks" onClose={onClose} width={620}>
      <p className="muted small">
        Pinned files from <code>~/.peekdocs_bookmarks.json</code>. Add new ones
        in the tkinter GUI (the web UI doesn't have a per-file pin yet).
      </p>
      {error && <div className="modal-error">{error}</div>}
      {data && data.bookmarks.length === 0 && (
        <p className="muted small">No bookmarks saved.</p>
      )}
      {data && data.bookmarks.length > 0 && (
        <ul className="saved-search-list">
          {data.bookmarks.map((b, i) => (
            <li key={i}>
              <code style={{ fontSize: 11 }}>{b.path}</code>
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
