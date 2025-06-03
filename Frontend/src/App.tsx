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
    setSelected((prev) => (prev[0] === url ? [] : [url]));
  };

  return (
    <div className="container">
      <h1>Sociaal Domein Scraper</h1>
      <ScrapeForm onScrape={handleScrape} />
      <WebsiteList
        websites={websites}
        selected={selected}
        toggleSelect={toggleSelect}
      />
      <ExportMenu selectedWebsites={selected} />
    </div>
  );
};

export default App;
