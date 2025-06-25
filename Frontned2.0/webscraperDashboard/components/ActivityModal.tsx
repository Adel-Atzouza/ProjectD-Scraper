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
  job_id: string;
  timestamp?: string;
};

const API = "http://127.0.0.1:8000";

export default function ActivityModal({ isOpen, onClose }: ActivityModalProps) {
  const [entries, setEntries] = useState<ActivityEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  function formatDateTime(dt?: string): string {
    if (!dt) return "Unknown";
    const d = new Date(dt);
    if (isNaN(d.getTime())) return "Unknown";
    return d.toLocaleString(undefined, {
      year: "numeric", month: "short", day: "2-digit",
      hour: "2-digit", minute: "2-digit", second: "2-digit"
    });
  }

  const fetchActivity = async () => {
    try {
      const r = await fetch(`${API}/activity`);
      if (!r.ok) throw new Error("Failed to load activity");
      const json = await r.json();
      setEntries(json.entries ?? []);
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    if (!isOpen) return;

    fetchActivity();
    const interval = setInterval(fetchActivity, 2000);
    return () => clearInterval(interval);
  }, [isOpen]);

  const handleDelete = async (jobId: string) => {
    try {
      await fetch(`${API}/activity/${encodeURIComponent(jobId)}`, {
        method: "DELETE",
      });
      fetchActivity(); 
    } catch (err) {
      console.error("Error deleting activity:", err);
      setError("Failed to delete activity");
    }
  };

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

        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "16px",
          }}
        >
          {error && (
            <div
              style={{
                color: "red",
                display: "flex",
                gap: "8px",
                alignItems: "center",
              }}
            >
              <p>{error}</p>
              <button className="primary" onClick={fetchActivity}>
                Retry
              </button>
            </div>
          )}
          {!error && entries.length === 0 && <p>No activity available.</p>}

          <ul
            className="activity-list"
            style={{ width: "100%", margin: 0, padding: 0 }}
          >
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
                <div
                  style={{
                    fontWeight: 500,
                    marginBottom: "6px",
                    wordBreak: "break-all",
                  }}
                >
                  {e.url || `Job ID: ${e.job_id}`} {}
                </div>
                <span className={`badge ${e.status.toLowerCase()}`}>
                  {e.status}
                </span>

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
                      Progress: {e.done ?? 0}/{e.total ?? 0} items
                      <br />✅ Success: {e.success ?? 0} | ❌ Failed:{" "}
                      {e.failed ?? 0}
                    </small>
                    <div style={{ fontSize: "12px", color: "#555", marginTop: "4px" }}>
                      <span>Started: {formatDateTime(e.timestamp)}</span>
                    </div>
                  </>
                )}
                <button
                  onClick={() => handleDelete(e.job_id)}
                  style={{
                    backgroundColor: "#ff4444",
                    color: "white",
                    padding: "5px 10px",
                    border: "none",
                    borderRadius: "3px",
                    marginTop: "12px",
                    marginLeft: "auto",
                    display: "block", 
                  }}
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="modal-buttons">
          <button className="primary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
