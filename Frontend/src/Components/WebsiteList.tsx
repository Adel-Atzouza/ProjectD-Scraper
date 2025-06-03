import React from "react";

interface WebsiteListProps {
    websites: string[];
    selected: string[];
    toggleSelect: (url: string) => void;
    onDelete: (url: string) => void;
}


const WebsiteList: React.FC<WebsiteListProps> = ({
    websites,
    selected,
    toggleSelect,
    onDelete, // ← deze toevoegen
}) => {
    return (
        <div style={{ marginTop: "2rem" }}>
            <h2>Gescrapete websites</h2>
            <ul>
                {websites.map((url, index) => (
                    <li
                        key={index}
                        style={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            padding: "0.5rem 0",
                        }}
                    >
                        <label style={{ flex: 1 }}>
                            <input
                                type="checkbox"
                                checked={selected.includes(url)}
                                onChange={() => toggleSelect(url)}
                                name="website-selection"
                            />{" "}
                            {url}
                        </label>
                        <button
                            onClick={() => onDelete(url)}
                            style={{
                                backgroundColor: "#ef4444",
                                padding: "0.4rem 0.8rem",
                                borderRadius: "6px",
                                color: "#fff",
                                border: "none",
                                cursor: "pointer",
                                marginLeft: "1rem",
                            }}
                        >
                            Verwijderen
                        </button>
                    </li>
                ))}
            </ul>

        </div>
    );
};

export default WebsiteList;
