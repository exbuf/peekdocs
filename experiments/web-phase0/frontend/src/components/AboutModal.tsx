import { useEffect, useState } from "react";
import Modal from "./Modal";
import { getAbout, type AboutInfo } from "../api";

interface Props {
  onClose: () => void;
}

export default function AboutModal({ onClose }: Props) {
  const [info, setInfo] = useState<AboutInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAbout()
      .then(setInfo)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  return (
    <Modal title="About peekdocs" onClose={onClose} width={500}>
      {error && <div className="modal-error">{error}</div>}
      {!info && !error && <p>Loading…</p>}
      {info && (
        <>
          <div className="about-row">
            <strong>Name</strong> · {info.name}
          </div>
          <div className="about-row">
            <strong>Version</strong> · {info.version}
          </div>
          <div className="about-row">
            <strong>Author</strong> · {info.author}
          </div>
          <div className="about-row">
            <strong>License</strong> · {info.license}
          </div>
          <div className="about-row">
            <strong>Repository</strong> ·{" "}
            <a href={info.repo} target="_blank" rel="noreferrer">
              {info.repo}
            </a>
          </div>
          <div className="about-row">
            <strong>Web backend</strong> · v{info.web_backend_version} (localhost-only experiment)
          </div>
          <p className="muted small" style={{ marginTop: 16 }}>
            {info.description}
          </p>
        </>
      )}
      <div className="modal-buttons">
        <button onClick={onClose}>Close</button>
      </div>
    </Modal>
  );
}
