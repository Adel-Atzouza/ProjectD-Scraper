import React from "react";

interface WebsiteListProps {
    websites: { id: number; url: string }[];
    selected: number[];
    toggleSelect: (id: number) => void;
    onDelete: (id: number) => void;
}


const WebsiteList: React.FC<WebsiteListProps> = ({
    websites,
    selected,
    toggleSelect,
    onDelete, // ← deze toevoegen
}) => {
    return (
        <div style={{ marginTop: "2rem" }}>
            <h2>Gescrdapete websites</h2>
            <ul>
            {websites.map((site) => (
                <li key={site.id}>
                    <input
                        type="checkbox"
                        checked={selected.includes(site.id)}
                        onChange={() => toggleSelect(site.id)}
                    />
                    {site.url}
                    <button onClick={() => onDelete(site.id)}>Verwijderen</button>
                </li>
            ))}
            </ul>

        </div>
    );
};

export default WebsiteList;
