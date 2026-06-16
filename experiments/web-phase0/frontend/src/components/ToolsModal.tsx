import { useEffect, useMemo, useState } from "react";
import { Bar, Doughnut } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import Modal from "./Modal";
import {
  getFileInventory,
  getAgeDistribution,
  getDuplicates,
  getLargeFiles,
  getEmptyFiles,
  getRecentChanges,
  getProtectedFiles,
  getUnsearchableFiles,
} from "../api";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

export type ToolKind =
  | "file-inventory"
  | "age-distribution"
  | "duplicates"
  | "large-files"
  | "empty-files"
  | "recent-changes"
  | "protected-files"
  | "unsearchable-files";

interface Props {
  kind: ToolKind;
  directory: string;
  onClose: () => void;
}

function fmtBytes(b: number): string {
  if (b < 1024) return `${b} B`;
  if (b < 1024 ** 2) return `${(b / 1024).toFixed(1)} KB`;
  if (b < 1024 ** 3) return `${(b / 1024 ** 2).toFixed(1)} MB`;
  return `${(b / 1024 ** 3).toFixed(2)} GB`;
}

export default function ToolsModal({ kind, directory, onClose }: Props) {
  const [data, setData] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setData(null);
    const promise = (() => {
      switch (kind) {
        case "file-inventory":
          return getFileInventory(directory);
        case "age-distribution":
          return getAgeDistribution(directory);
        case "duplicates":
          return getDuplicates(directory);
        case "large-files":
          return getLargeFiles(directory);
        case "empty-files":
          return getEmptyFiles(directory);
        case "recent-changes":
          return getRecentChanges(directory);
        case "protected-files":
          return getProtectedFiles(directory);
        case "unsearchable-files":
          return getUnsearchableFiles(directory);
      }
    })();

    promise
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e) => {
        if (!cancelled)
          setError(e instanceof Error ? e.message : String(e));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [kind, directory]);

  return (
    <Modal title={TITLES[kind]} onClose={onClose} width={760}>
      <p className="muted small">
        Target: <code>{directory}</code>
      </p>
      {loading && <p>Running…</p>}
      {error && <div className="modal-error">{error}</div>}
      {!loading && data !== null && (
        <ToolBody kind={kind} data={data} />
      )}
      <div className="modal-buttons">
        <button onClick={onClose}>Close</button>
      </div>
    </Modal>
  );
}

const TITLES: Record<ToolKind, string> = {
  "file-inventory": "File Inventory",
  "age-distribution": "File Age Distribution",
  "duplicates": "Duplicate Finder",
  "large-files": "Large Files",
  "empty-files": "Empty Files",
  "recent-changes": "Recent Changes",
  "protected-files": "Protected Files",
  "unsearchable-files": "Unsearchable Files",
};

interface ToolBodyProps {
  kind: ToolKind;
  data: unknown;
}

function ToolBody({ kind, data }: ToolBodyProps) {
  switch (kind) {
    case "file-inventory":
      return <FileInventoryView data={data as Awaited<ReturnType<typeof getFileInventory>>} />;
    case "age-distribution":
      return <AgeView data={data as Awaited<ReturnType<typeof getAgeDistribution>>} />;
    case "duplicates":
      return <DuplicatesView data={data as Awaited<ReturnType<typeof getDuplicates>>} />;
    case "large-files":
      return <LargeView data={data as Awaited<ReturnType<typeof getLargeFiles>>} />;
    case "empty-files":
      return <PathListView paths={(data as { files: string[] }).files} label="empty file" />;
    case "recent-changes":
      return <RecentView data={data as Awaited<ReturnType<typeof getRecentChanges>>} />;
    case "protected-files":
      return <PathListView paths={(data as { files: string[] }).files} label="protected file" />;
    case "unsearchable-files":
      return <UnsearchableView data={data as Awaited<ReturnType<typeof getUnsearchableFiles>>} />;
  }
}

function FileInventoryView({ data }: { data: Awaited<ReturnType<typeof getFileInventory>> }) {
  const chartData = useMemo(() => {
    const top = data.by_extension.slice(0, 10);
    return {
      labels: top.map((e) => e.ext),
      datasets: [
        {
          label: "Files",
          data: top.map((e) => e.count),
          backgroundColor: "rgba(33, 150, 243, 0.7)",
        },
      ],
    };
  }, [data]);
  return (
    <>
      <div className="tool-summary">
        <span>
          <strong>{data.total_files}</strong> files
        </span>
        <span>
          <strong>{fmtBytes(data.total_bytes)}</strong> total
        </span>
        <span>
          <strong>{data.by_extension.length}</strong> distinct extensions
        </span>
      </div>
      <div className="chart-wrap" style={{ height: 280 }}>
        <Bar
          data={chartData}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: { title: { display: true, text: "Top 10 extensions by file count" }, legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
          }}
        />
      </div>
      <table className="check-table" style={{ marginTop: 12 }}>
        <thead>
          <tr><th>Extension</th><th>Files</th><th>Size</th></tr>
        </thead>
        <tbody>
          {data.by_extension.slice(0, 20).map((e) => (
            <tr key={e.ext}>
              <td>{e.ext}</td>
              <td>{e.count}</td>
              <td>{fmtBytes(e.bytes)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

function AgeView({ data }: { data: Awaited<ReturnType<typeof getAgeDistribution>> }) {
  const labels = Object.keys(data.buckets);
  const values = labels.map((k) => data.buckets[k]);
  return (
    <>
      <div className="tool-summary">
        <span>
          <strong>{data.total_files}</strong> files distributed across age buckets
        </span>
      </div>
      <div className="chart-wrap" style={{ height: 280 }}>
        <Bar
          data={{
            labels,
            datasets: [
              {
                label: "Files",
                data: values,
                backgroundColor: [
                  "rgba(76, 175, 80, 0.7)",   // newest = green
                  "rgba(139, 195, 74, 0.7)",
                  "rgba(255, 235, 59, 0.7)",
                  "rgba(255, 152, 0, 0.7)",
                  "rgba(255, 87, 34, 0.7)",
                  "rgba(158, 158, 158, 0.7)", // oldest = gray
                ],
              },
            ],
          }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: { title: { display: true, text: "Files by modification age" }, legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
          }}
        />
      </div>
    </>
  );
}

function DuplicatesView({ data }: { data: Awaited<ReturnType<typeof getDuplicates>> }) {
  if (data.groups.length === 0) {
    return (
      <p className="muted small">
        No duplicates found. Files are compared by SHA-256 across same-size groups.
      </p>
    );
  }
  return (
    <>
      <div className="tool-summary">
        <span>
          <strong>{data.groups.length}</strong> duplicate group{data.groups.length === 1 ? "" : "s"}
        </span>
        <span>
          <strong>{fmtBytes(data.wasted_bytes)}</strong> wasted on extra copies
        </span>
      </div>
      <ul className="saved-search-list" style={{ marginTop: 8 }}>
        {data.groups.slice(0, 30).map((g, i) => (
          <li key={i} style={{ flexDirection: "column", alignItems: "flex-start" }}>
            <span>
              <code>{g.hash}…</code> · {fmtBytes(g.size)} ·{" "}
              {g.paths.length} copies
            </span>
            <ul style={{ paddingLeft: 16, fontSize: 11, fontFamily: "monospace" }}>
              {g.paths.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </>
  );
}

function LargeView({ data }: { data: Awaited<ReturnType<typeof getLargeFiles>> }) {
  return (
    <ul className="saved-search-list">
      {data.files.map((f) => (
        <li key={f.path}>
          <code style={{ fontSize: 11 }}>{f.path}</code>
          <span className="muted small">{fmtBytes(f.size)}</span>
        </li>
      ))}
    </ul>
  );
}

function PathListView({ paths, label }: { paths: string[]; label: string }) {
  if (paths.length === 0) {
    return <p className="muted small">No {label}s found.</p>;
  }
  return (
    <ul className="saved-search-list">
      {paths.slice(0, 100).map((p) => (
        <li key={p}>
          <code style={{ fontSize: 11 }}>{p}</code>
        </li>
      ))}
      {paths.length > 100 && (
        <li className="muted small">… {paths.length - 100} more</li>
      )}
    </ul>
  );
}

function RecentView({ data }: { data: Awaited<ReturnType<typeof getRecentChanges>> }) {
  return (
    <>
      <p className="muted small">
        Files modified in the last <strong>{data.days}</strong> days:{" "}
        <strong>{data.files.length}</strong>
      </p>
      <ul className="saved-search-list">
        {data.files.slice(0, 100).map((f) => {
          const date = new Date(f.mtime * 1000).toLocaleString();
          return (
            <li key={f.path}>
              <code style={{ fontSize: 11 }}>{f.path}</code>
              <span className="muted small">{date}</span>
            </li>
          );
        })}
      </ul>
    </>
  );
}

function UnsearchableView({ data }: { data: Awaited<ReturnType<typeof getUnsearchableFiles>> }) {
  const cats = Object.entries(data.categories);
  const chartData = {
    labels: cats.map(([k]) => k.replace(/_/g, " ")),
    datasets: [
      {
        data: cats.map(([, v]) => v.count),
        backgroundColor: ["#90caf9", "#ffcc80", "#ef9a9a"],
      },
    ],
  };
  return (
    <>
      <div className="chart-wrap" style={{ height: 240 }}>
        <Doughnut data={chartData} options={{ responsive: true, maintainAspectRatio: false }} />
      </div>
      {cats.map(([k, v]) => (
        <div key={k} style={{ marginTop: 12 }}>
          <h4 style={{ fontSize: 13, marginBottom: 4 }}>
            {k.replace(/_/g, " ")} · {v.count}
          </h4>
          {v.files.length === 0 ? (
            <p className="muted small">none</p>
          ) : (
            <ul style={{ paddingLeft: 16, fontSize: 11, fontFamily: "monospace" }}>
              {v.files.slice(0, 20).map((p) => (
                <li key={p}>{p}</li>
              ))}
              {v.files.length > 20 && (
                <li className="muted small">… {v.files.length - 20} more</li>
              )}
            </ul>
          )}
        </div>
      ))}
    </>
  );
}
