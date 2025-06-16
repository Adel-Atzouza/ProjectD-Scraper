import React from 'react';

export default function Header() {
  return (
    <header>
      <div className="logo">
        <div className="logo-icon">🕷️</div>
        WebScraper
      </div>
      <button className="primary">
        <svg width="14" height="16" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M2 8h10M7 2v12" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        Add Website
      </button>
    </header>
  );
}
