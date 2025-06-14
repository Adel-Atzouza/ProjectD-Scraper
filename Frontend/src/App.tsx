import React, { useState } from "react";
import "./App.css";
import ScrapeForm from "./Components/ScrapeForm";
import WebsiteList from "./Components/WebsiteList";
import ExportMenu from "./Components/ExportMenu";

const App: React.FC = () => {
  const [websites, setWebsites] = useState<string[]>([
    "https://voorbeeld1.nl",
    "https://voorbeeld2.nl",
    "https://voorbeeld3.nl",
  ]);
  const [selected, setSelected] = useState<string[]>([]);

  const handleScrape = (url: string) => {
    if (!websites.includes(url)) {
      setWebsites([url, ...websites]);
    }
  };

  const toggleSelect = (url: string) => {
    setSelected((prev) =>
      prev.includes(url) ? prev.filter((u) => u !== url) : [...prev, url]
    );
  };



  const handleDelete = (url: string) => {
    setWebsites((prev) => prev.filter((site) => site !== url));
    setSelected((prev) => prev.filter((site) => site !== url)); // deselect if deleted
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

      <ExportMenu selectedWebsites={selected} />
    </div>
  );
};

export default App;
