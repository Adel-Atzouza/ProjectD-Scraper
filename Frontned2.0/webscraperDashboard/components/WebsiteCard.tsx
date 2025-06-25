import { useState, useEffect } from "react";

export interface WebsiteCardProps {
  url: string;
  lastScraped?: string;
  onDelete: () => void;
  progress?: number;
  status?: string;
  total?: number;
  done?: number;
  success?: number;
  failed?: number;
}

export default function WebsiteCard({
  url,
  lastScraped,
  onDelete,
  progress = 0,
  status = "idle",
  total = 0,
  done = 0,
  success = 0,
  failed = 0,
}: WebsiteCardProps) {
  // Track if "done" info should be shown after mouse leaves
  const [showDone, setShowDone] = useState(true);

  // Reset showDone if we start a new scrape/discovering/idle
  useEffect(() => {
    if (status !== "done") setShowDone(true);
  }, [status]);

  // Show progress/info if:
  // - discovering/scraping (always)
  // - done AND showDone is true
  const showProgress =
    status === "discovering" ||
    status === "scraping" ||
    (status === "done" && showDone);

  function formatDateTime(dt?: string): string {
    if (!dt) return "Unknown";
    const d = new Date(dt);
    if (isNaN(d.getTime())) return "Unknown";
    return d.toLocaleString(undefined, {
      year: "numeric", month: "short", day: "2-digit",
      hour: "2-digit", minute: "2-digit", second: "2-digit"
    });
  }

  return (
    <div
      className="website-card"
      onMouseLeave={() => {
        if (status === "done" && showDone) setShowDone(false);
      }}
    >
      <div className="website-details">
        <div className="website-icon">🌐</div>
        <div className="website-info">
          <p>{url}</p>
          <div>
            <span className={`badge ${status}`}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
            <span style={{ fontSize: "12px", color: "#283593", marginLeft: "8px" }}>
              Last scraped: {formatDateTime(lastScraped)}
            </span>
            {showProgress && (
              <>
                <div className="progress-info">
                  <small>
                    {done} / {total} – ✔️{success} / ❌{failed}
                  </small>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${progress}%` }} />
                </div>
              </>
            )}
          </div>
        </div>
      </div>
      <div className="card-actions">
        <button title="Delete" onClick={onDelete}>🗑️</button>
      </div>
    </div>
  );
}
