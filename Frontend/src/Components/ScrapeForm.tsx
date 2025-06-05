import React, { useState } from "react";

interface ScrapeFormProps {
    onScrape: (url: string) => void;
}

const ScrapeForm: React.FC<ScrapeFormProps> = ({ onScrape }) => {
    const [url, setUrl] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        const trimmedUrl = url.trim();

        // Regex voor basis website-validatie (.com, .org, .nl, etc.)
        const urlPattern = /^(https?:\/\/)?([a-z0-9-]+\.)+[a-z]{2,}$/i;

        if (!urlPattern.test(trimmedUrl)) {
            alert("Voer een geldige website-URL in (zoals https://voorbeeld.com)");
            return;
        }

        onScrape(trimmedUrl.startsWith("http") ? trimmedUrl : `https://${trimmedUrl}`);
        setUrl("");
    };

    return (
        <form onSubmit={handleSubmit} style={{ display: "flex", gap: "1rem" }}>
            <input
                type="text"
                placeholder="Voer een website in"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                style={{
                    flex: 1,
                    padding: "0.5rem",
                    borderRadius: "6px",
                    border: "1px solid #ccc",
                }}
            />
            <button type="submit">Scrape website</button>
        </form>
    );
};

export default ScrapeForm;
