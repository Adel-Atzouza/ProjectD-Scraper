import { useEffect, useState } from "react";
import Header from "../components/Header";
import StatCard from "../components/Statchecker";
import WebsiteCard from "../components/WebsiteCard";
import ConfirmModal from "../components/ConfirmScreen";
import AddWebsiteModal from "../components/AddWebsitePopup";
import OutputModal from "../components/OutputModal";
import ActivityModal from "../components/ActivityModal";

interface Website {
  id: number;
  url: string;
}

interface Stats {
  total: number;
  active: number;
  completed: number;
  success_rate: string;
}

type ProgressStatus = {
  jobId: string;
  progress: number;
  status: string;
  total: number;
  done: number;
  success: number;
  failed: number;
};

const API = "http://127.0.0.1:8000";

export default function Dashboard() {
  const [websites, setWebsites] = useState<Website[]>([]);
  const [stats, setStats] = useState<Stats>({ total: 0, active: 0, completed: 0, success_rate: "0%" });
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const [progressMap, setProgressMap] = useState<Record<string, ProgressStatus>>({});
  const [scrapingStarted, setScrapingStarted] = useState(false);
  const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [stuck, setStuck] = useState(false);

  const [outputOpen, setOutputOpen] = useState(false);
  const [activityOpen, setActivityOpen] = useState(false);

  const showToast = (msg: string, duration = 3000) => {
    setToast(msg);
    setTimeout(() => setToast(null), duration);
  };

  const loadData = async () => {
    const [wRes, sRes] = await Promise.all([
      fetch(`${API}/websites`),
      fetch(`${API}/stats`)
    ]);
    setWebsites(await wRes.json());
    setStats(await sRes.json());
  };

  useEffect(() => {
    loadData();
    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, []);

  const handleStart = async () => {
    if (pollInterval) clearInterval(pollInterval);

    const res = await fetch(`${API}/start-scrape`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ urls: selected }),
    });
    const { jobs } = await res.json();

    const newMap: Record<string, ProgressStatus> = {};
    jobs.forEach((j: any) => {
      newMap[j.url] = {
        jobId: j.job_id,
        progress: 0,
        status: "discovering",
        total: 0,
        done: 0,
        success: 0,
        failed: 0,
      };
    });

    setProgressMap(newMap);
    setScrapingStarted(true);
    showToast("🚀 Scraping started!");
    loadData();

    const interval = setInterval(async () => {
      let allStopped = true;
      const updatedMap = { ...newMap };

      for (const url of selected) {
        const entry = updatedMap[url];
        try {
          const r = await fetch(`${API}/scrape-progress/${entry.jobId}`);
          if (r.ok) {
            const data = await r.json();
            updatedMap[url] = { ...entry, ...data };
            if (!["idle", "done", "stopped"].includes(data.status)) {
              allStopped = false;
            }
          }
        } catch { /* ignore */ }

        if (updatedMap[url].status === "stopped") {
          setStuck(true);
        }
      }

      setProgressMap(updatedMap);

      if (allStopped) {
        clearInterval(interval);
        setPollInterval(null);
        setScrapingStarted(false);
      }
    }, 2000);

    setPollInterval(interval);
  };

  const handleStop = async () => {
    if (pollInterval) {
      clearInterval(pollInterval);
      setPollInterval(null);
    }

    await fetch(`${API}/stop-scrape`, { method: "POST" });

    setTimeout(() => {
      setScrapingStarted(false);
      showToast("🛑 Scraping stopped");
      setProgressMap(prev => {
        const pv = { ...prev };
        selected.forEach(url => {
          if (pv[url]?.status !== "done") {
            pv[url] = { ...pv[url], status: "stopped", progress: 0 };
          }
        });
        return pv;
      });
    }, 1500);
    loadData();
  };

  const toggleSelect = (url: string) =>
    setSelected(prev =>
      prev.includes(url) ? prev.filter(u => u !== url) : [...prev, url]
    );

  const toggleSelectAll = () =>
    setSelected(prev =>
      prev.length === websites.length ? [] : websites.map(w => w.url)
    );

  const handleDelete = async () => {
    if (deleteId !== null) {
      await fetch(`${API}/websites/${deleteId}`, { method: "DELETE" });
      setDeleteId(null);
      setConfirmOpen(false);
      loadData();
    }
  };

  return (
    <>
      <Header />
      <main className="main">
        {toast && <div className="toast success">{toast}</div>}
        {stuck && <div className="toast error">⚠️ Scrape status may be stuck. Please refresh the page.</div>}

        <div className="stats">
          <StatCard label="Total Websites" value={`${stats.total}`} icon="globe" />
          <StatCard label="Active Scrapes" value={`${stats.active}`} icon="play" />
          <StatCard label="Completed" value={`${stats.completed}`} icon="check" />
          <StatCard label="Success Rate" value={stats.success_rate} icon="chart" />
        </div>

        <section className="website-section">
          <h2 style={{ textAlign: "center" }}>Websites</h2>
          <div className="website-header">
            <button className="primary" onClick={() => setAddModalOpen(true)}>Add Website</button>
            <button className="primary" onClick={() => setOutputOpen(true)}>View Output</button>
            <button className="primary" onClick={() => setActivityOpen(true)}>View Activity</button>
            <button className="primary" onClick={toggleSelectAll}>Select All</button>
            
            {!scrapingStarted ? (
              <button className="primary" onClick={handleStart}>Start Scraping</button>
            ) : (
              <button className="primary danger" onClick={handleStop}>Stop Scraping</button>
            )}
          </div>

          <div className="website-list">
            {websites.map(w => (
              <div className="website-row" key={w.id}>
                <input
                  type="checkbox"
                  className="clean-checkbox"
                  checked={selected.includes(w.url)}
                  onChange={() => toggleSelect(w.url)}
                />
                <WebsiteCard
                  url={w.url}
                  onDelete={() => {
                    setDeleteId(w.id);
                    setConfirmOpen(true);
                  }}
                  progress={progressMap[w.url]?.progress}
                  status={progressMap[w.url]?.status}
                  total={progressMap[w.url]?.total}
                  done={progressMap[w.url]?.done}
                  success={progressMap[w.url]?.success}
                  failed={progressMap[w.url]?.failed}
                />
              </div>
            ))}
          </div>
        </section>
      </main>

      <ConfirmModal
        isOpen={confirmOpen}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={handleDelete}
      />

      <AddWebsiteModal
        isOpen={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        onAdd={loadData}
      />

      <OutputModal
        isOpen={outputOpen}
        onClose={() => setOutputOpen(false)}
      />

      <ActivityModal
        isOpen={activityOpen}
        onClose={() => setActivityOpen(false)}
      />
    </>
  );
}
