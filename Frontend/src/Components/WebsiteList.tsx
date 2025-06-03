import React from "react";

interface WebsiteListProps {
    websites: string[];
    selected: string[];
    toggleSelect: (url: string) => void;
}

const WebsiteList: React.FC<WebsiteListProps> = ({
    websites,
    selected,
    toggleSelect,
}) => {
    return (
        <div style={{ marginTop: "2rem" }}>
            <h2>Gescrapete websites</h2>
            <ul>
                {websites.map((url, index) => (
                    <li key={index}>
                        <label>
                            <input
                                type="checkbox"
                                checked={selected.includes(url)}
                                onChange={() => toggleSelect(url)}
                            />{" "}
                            {url}
                        </label>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default WebsiteList;
