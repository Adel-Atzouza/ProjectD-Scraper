// src/components/WebsiteCard.tsx
import React from 'react';


interface WebsiteCardProps {
  name: string;
  url: string;
  status: 'Active' | 'Paused';
  lastScraped: string;
}

export default function WebsiteCard({ name, url, status, lastScraped }: WebsiteCardProps) {
  return (
    <div className="website-card">
      <div className="website-details">
        <div className="logo-icon">🌐</div>
        <div className="website-info">
          <h3>{name}</h3>
          <p>{url}</p>
          <div>
            <span className={`badge ${status.toLowerCase()}`}>{status}</span>
            <span style={{ fontSize: '12px', color: '#9ca3af' }}>Last scraped: {lastScraped}</span>
          </div>
        </div>
      </div>
      <div className="card-actions">
        <button title="Delete">🗑️</button>
      </div>
    </div>
  );
}
