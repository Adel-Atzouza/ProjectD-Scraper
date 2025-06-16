// src/components/StatCard.tsx
import React from 'react';
import '../src/style.css'; // Ensure you have the correct path to your CSS file


interface StatCardProps {
  label: string;
  value: string;
  icon: string;
}

const iconMap: Record<string, string> = {
  globe: '🌐',
  play: '▶️',
  check: '✅',
  chart: '📈',
};

export default function StatCard({ label, value, icon }: StatCardProps) {
  return (
    <div className="stat-card">
      <div>
        <p className="card-title">{label}</p>
        <p className="card-value">{value}</p>
      </div>
      <div className="stat-icon">{iconMap[icon]}</div>
    </div>
  );
}
