import { useEffect, useState } from "react";

type ActivityModalProps = { isOpen: boolean; onClose: () => void };
type ActivityEntry = {
  url: string;
  status: string;
  progress: number;
  done?: number;
  total?: number;
  success?: number;
  failed?: number;
};

const API = "http://127.0.0.1:8000";

export default function ActivityModal({ isOpen, onClose }: ActivityModalProps) {
  const [entries, setEntries] = useState<ActivityEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetch(`${API}/activity`)
        .then(r => { if (!r.ok) throw new Error("Failed to load activity"); return r.json() })
        .then(json => { setEntries(json.entries ?? []); setError(null) })
        .catch(err => setError(err.message));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div
        className="modal"
        style={{
          width: "80vw",
          height: "75vh",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div className="modal-header">
          <h3>Scrape Activity</h3>
        </div>

        {/* Expanded scrollable container */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "16px",
          }}
        >
          {error && <p style={{ color: "red" }}>{error}</p>}
          {!error && entries.length === 0 && <p>No activity available.</p>}

          <ul className="activity-list" style={{ width: "100%", margin: 0, padding: 0 }}>
            {entries.map((e, i) => (
              <li
                key={i}
                style={{
                  width: "100%",
                  boxSizing: "border-box",
                  marginBottom: "16px",
                  background: "#f3f4f6",
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid rgb(8, 8, 8)",
                  listStyle: "none",
                }}
              >
                <div style={{ fontWeight: 500, marginBottom: "6px", wordBreak: "break-all", }}>
                  {e.url || "Unknown URL"}
                </div>
                <span className={`badge ${e.status.toLowerCase()}`}>{e.status}</span>

                {typeof e.progress === "number" && (
                  <>
                    <div className="progress-bar" style={{ marginTop: "8px" }}>
                      <div
                        className="progress-fill"
                        style={{
                          width: `${e.progress}%`,
                          transition: "width 0.3s ease",
                        }}
                      />
                    </div>
                    <small>
                      Progress: {e.done ?? 0}/{e.total ?? 0} items<br />
                      ✅ Success: {e.success ?? 0} | ❌ Failed: {e.failed ?? 0}
                    </small>
                  </>
                )}
              </li>
            ))}
          </ul>
        </div>

        <div className="modal-buttons">
          <button className="primary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}
