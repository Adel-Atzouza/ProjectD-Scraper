import React from "react";

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
  const isWorking = ["discovering", "scraping", "done"].includes(status);
  const displayStatus = status === "done" && done >= total ? "done" : status;

  return (
    <div className="website-card">
      <div className="website-details">
        <div className="logo-icon">🌐</div>
        <div className="website-info">
          <p>{url}</p>
          <div>
            <span className={`badge ${displayStatus}`}>
              {displayStatus.charAt(0).toUpperCase() + displayStatus.slice(1)}
            </span>
            <span style={{ fontSize: "12px", color: "#9ca3af" }}>
              Last scraped: {lastScraped ?? "Unknown"}
            </span>

            {isWorking && (
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
