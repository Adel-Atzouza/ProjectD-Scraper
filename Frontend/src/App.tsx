import React, { useState } from "react";
import "./App.css";
import ScrapeForm from "./Components/ScrapeForm";
import WebsiteList from "./Components/WebsiteList";
import ExportMenu from "./Components/ExportMenu";

const App: React.FC = () => {
  const [selected, setSelected] = useState<number[]>([]);

  const [websites, setWebsites] = useState<{ id: number; url: string }[]>([]);


  const handleScrape = async (url: string) => {
    try {
        const response = await fetch("http://localhost:8000/websites", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ url }),
        });

        if (!response.ok) {
            throw new Error(`Failed to scrape website: ${response.statusText}`);
        }

        const data = await response.json();

        setWebsites([{ id: data.id, url: data.url }, ...websites]);

        alert(`Scraping gestart voor: ${data.url}`);
    } catch (error) {
        alert(`Error: ${error}`);
    }
  };


  const toggleSelect = (id: number) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((u) => u !== id) : [...prev, id]
    );
  };



  const handleDelete = async (id: number) => {
    try {
        const response = await fetch(`http://localhost:8000/websites/${id}`, {
            method: "DELETE",
        });

        if (!response.ok) {
            throw new Error(`Failed to delete website`);
        }


        setWebsites((prev) => prev.filter((site) => site.id !== id));
        setSelected((prev) => prev.filter((siteId) => siteId !== id));
    } catch (error) {
        alert(`Error deleting website: ${error}`);
    }
  };

  return (
    <div className="container">
      <h1>Sociaal Domein Scraper</h1>
      <ScrapeForm onScrape={handleScrape} />
      <WebsiteList
        websites={websites}
        selected={selected}
        toggleSelect={toggleSelect}
        onDelete={handleDelete}
      />

  <ExportMenu selectedWebsites={websites.filter((site) => selected.includes(site.id))}/>
    </div>
  );
};

export default App;
