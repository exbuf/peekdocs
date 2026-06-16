import { useEffect, useState } from "react";
import Modal from "./Modal";

interface Props {
  directory: string;
  onClose: () => void;
}

interface SuitesResp { suites: Record<string, string[]>; }
interface ScheduleResp { command: string; instructions: string[]; }

const isWindows = navigator.userAgent.toLowerCase().includes("win");

export default function ScheduleSearchModal({ directory, onClose }: Props) {
  const [kind, setKind] = useState<"suite" | "regex-collection">("suite");
  const [name, setName] = useState("");
  const [frequency, setFrequency] = useState<"daily" | "weekly" | "monthly">("daily");
  const [osTarget, setOsTarget] = useState<"unix" | "windows">(isWindows ? "windows" : "unix");
  const [suites, setSuites] = useState<string[]>([]);
  const [collections, setCollections] = useState<string[]>([]);
  const [result, setResult] = useState<ScheduleResp | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`http://127.0.0.1:8000/suites?directory=${encodeURIComponent(directory)}`)
      .then((r) => r.json())
      .then((d: SuitesResp) => setSuites(Object.keys(d.suites)))
      .catch(() => {});
    fetch("http://127.0.0.1:8000/regex-collections")
      .then((r) => r.json())
      .then((d: { collections: string[] }) => setCollections(d.collections))
      .catch(() => {});
  }, [directory]);

  async function onGenerate() {
    if (!name) {
      setError("Pick a suite or collection name first");
      return;
    }
    setError(null);
    try {
      const r = await fetch("http://127.0.0.1:8000/schedule-search/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kind, name, directory, frequency, os_target: osTarget }),
      });
      if (!r.ok) throw new Error(await r.text());
      setResult(await r.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  const choices = kind === "suite" ? suites : collections;

  return (
    <Modal title="Schedule Search" onClose={onClose} width={620}>
      <p className="muted small">
        Generates a ready-to-paste cron (Mac/Linux) or Task Scheduler
        (Windows) command. peekdocs does <em>not</em> install the schedule
        for you — you paste the command yourself.
      </p>

      <div className="adv-grid adv-grid-cols-4" style={{ marginTop: 8 }}>
        <label>
          Schedule type
          <select value={kind} onChange={(e) => { setKind(e.target.value as "suite" | "regex-collection"); setName(""); setResult(null); }}>
            <option value="suite">Search Suite</option>
            <option value="regex-collection">Regex Collection</option>
          </select>
        </label>
        <label>
          Name
          <select value={name} onChange={(e) => { setName(e.target.value); setResult(null); }}>
            <option value="">— pick —</option>
            {choices.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
        <label>
          Frequency
          <select value={frequency} onChange={(e) => { setFrequency(e.target.value as "daily" | "weekly" | "monthly"); setResult(null); }}>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
        </label>
        <label>
          Target OS
          <select value={osTarget} onChange={(e) => { setOsTarget(e.target.value as "unix" | "windows"); setResult(null); }}>
            <option value="unix">Mac / Linux (cron)</option>
            <option value="windows">Windows (Task Scheduler)</option>
          </select>
        </label>
      </div>

      {error && <div className="modal-error">{error}</div>}

      {result && (
        <div style={{ marginTop: 16 }}>
          <p><strong>Command:</strong></p>
          <textarea
            readOnly
            value={result.command}
            rows={3}
            style={{ width: "100%", fontFamily: "monospace", fontSize: 11, padding: 8 }}
            onFocus={(e) => e.target.select()}
          />
          <button
            onClick={() => navigator.clipboard.writeText(result.command)}
            style={{ marginTop: 4 }}
          >
            Copy to clipboard
          </button>
          <p style={{ marginTop: 16 }}><strong>Steps:</strong></p>
          <ol className="muted small">
            {result.instructions.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ol>
        </div>
      )}

      <div className="modal-buttons">
        <button onClick={onClose}>Close</button>
        <button className="primary" onClick={onGenerate}>
          Generate Command
        </button>
      </div>
    </Modal>
  );
}
