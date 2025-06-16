// src/pages/Dashboard.tsx
import Header from '../components/Header';
import StatCard from '../components/Statchecker';
import WebsiteCard from '../components/WebsiteCard';

const websites = [
  { name: 'example.com', url: 'https://example.com', status: 'Active', lastScraped: '2 hours ago' },
  { name: 'news.ycombinator.com', url: 'https://news.ycombinator.com', status: 'Active', lastScraped: '1 hour ago' },
  { name: 'github.com', url: 'https://github.com', status: 'Paused', lastScraped: '1 day ago' },
] as const;

export default function Dashboard() {
  return (
    <div>
      <Header />
      <main className="main">
        <div className="stats">
          <StatCard label="Total Websites" value="3" icon="globe" />
          <StatCard label="Active Scrapes" value="0" icon="play" />
          <StatCard label="Completed" value="12" icon="check" />
          <StatCard label="Success Rate" value="94%" icon="chart" />
        </div>

        <section className="website-section">
          <div className="website-header">
            <h2>Websites</h2>
            <button className="primary">
              <svg width="12" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M2 8h8M6 2v12" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              Start Scraping
            </button>
          </div>

          <div className="website-list">
            {websites.map((w, i) => <WebsiteCard key={i} {...w} />)}
          </div>
        </section>
      </main>
    </div>
  );
}
