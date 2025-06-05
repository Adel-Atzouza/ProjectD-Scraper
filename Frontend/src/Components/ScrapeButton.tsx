import React from "react";

const ScrapeButton: React.FC = () => {
    const handleClick = () => {
        alert("Scraping zou nu starten (nog geen backend gekoppeld)");
    };

    return (
        <button onClick={handleClick} style={{ marginTop: "1rem" }}>
            Scrape website
        </button>
    );
};

export default ScrapeButton;
