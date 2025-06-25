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

type ConfirmModalProps = {
  isOpen: boolean;
  onCancel: () => void;
  onConfirm: () => void;
};

const API = "http://127.0.0.1:8000";

function ConfirmModal({ isOpen, onCancel, onConfirm }: ConfirmModalProps) {
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <h3>⚠️ Confirm Deletion</h3>
        <p>Are you sure you want to delete this activity?</p>
        <div className="modal-buttons">
          <button className="confirm" onClick={onConfirm}>Yes, Delete</button>
          <button onClick={onCancel}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

export default function ActivityModal({ isOpen, onClose }: ActivityModalProps) {
  const [entries, setEntries] = useState<ActivityEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"timestamp" | "status">("timestamp");
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  const sortedEntries = [...entries].sort((a, b) => {
    if (sortBy === "status") {
      // Define status priority order
      const statusOrder = {
        "discovering": 1,
        "running": 2,
        "stopped": 3,
        "done": 4,
        "failed": 5,
        "error": 6
      };
      
      const priorityA = statusOrder[a.status.toLowerCase() as keyof typeof statusOrder] ?? 999;
      const priorityB = statusOrder[b.status.toLowerCase() as keyof typeof statusOrder] ?? 999;
      
      return priorityA - priorityB;
    }
    
    // Default timestamp sorting
    // Helper function to get valid date or null
    const getValidDate = (timestamp?: string): Date | null => {
      if (!timestamp || timestamp.trim() === '') return null;
      const date = new Date(timestamp);
      return isNaN(date.getTime()) ? null : date;
    };

    const dateA = getValidDate(a.timestamp);
    const dateB = getValidDate(b.timestamp);

    // Both have valid timestamps - sort by timestamp descending (newest first)
    if (dateA && dateB) {
      return dateB.getTime() - dateA.getTime();
    }
    
    // Only A has valid timestamp - A comes first
    if (dateA && !dateB) return -1;
    
    // Only B has valid timestamp - B comes first
    if (!dateA && dateB) return 1;
    
    // Neither has valid timestamp - maintain original order
    return 0;
  });

  function formatDateTime(dt?: string): string {
    if (!dt || dt.trim() === '') return "Unknown";
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
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  useEffect(() => {
    if (!isOpen) return;

    fetchActivity();
    const interval = setInterval(fetchActivity, 2000);
    return () => clearInterval(interval);
  }, [isOpen]);

  const handleDeleteClick = (jobId: string) => {
    setConfirmDelete(jobId);
  };

  const handleConfirmDelete = async () => {
    if (!confirmDelete) return;
    
    try {
      await fetch(`${API}/activity/${encodeURIComponent(confirmDelete)}`, {
        method: "DELETE",
      });
      fetchActivity(); 
      setConfirmDelete(null);
    } catch (err) {
      console.error("Error deleting activity:", err);
      setError("Failed to delete activity");
      setConfirmDelete(null);
    }
  };

  const handleCancelDelete = () => {
    setConfirmDelete(null);
  };

  if (!isOpen) return null;

  return (
    <>
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
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span style={{ fontSize: "14px", color: "#6b7280", fontWeight: "500" }}>Sort by:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as "timestamp" | "status")}
                style={{
                  padding: "8px 12px",
                  borderRadius: "8px",
                  border: "1px solid #000000",
                  backgroundColor: "#3b82f6",
                  color: "white",
                  fontSize: "14px",
                  fontWeight: "500",
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                  outline: "none"
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = "#2563eb";
                  e.currentTarget.style.boxShadow = "0 4px 10px rgba(0, 0, 0, 0.12)";
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = "#3b82f6";
                  e.currentTarget.style.boxShadow = "none";
                }}
              >
                <option value="timestamp" style={{ backgroundColor: "white", color: "#374151" }}>
                  Time (Newest First)
                </option>
                <option value="status" style={{ backgroundColor: "white", color: "#374151" }}>
                  Status (Active First)
                </option>
              </select>
            </div>
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
              {sortedEntries.map((e, i) => (
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
                    {e.url || `Job ID: ${e.job_id}`}
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
                    onClick={() => handleDeleteClick(e.job_id)}
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

      <ConfirmModal
        isOpen={confirmDelete !== null}
        onCancel={handleCancelDelete}
        onConfirm={handleConfirmDelete}
      />
    </>
  );
}