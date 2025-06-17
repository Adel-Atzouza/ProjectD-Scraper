import React from "react";

interface ExportMenuProps {
    selectedWebsites: { id: number; url: string }[];
}

const ExportMenu: React.FC<ExportMenuProps> = ({ selectedWebsites }) => {
    const formats = ["csv", "txt", "json"];

    const handleExport = (format: string) => {
        if (selectedWebsites.length === 0) {
            alert("Selecteer eerst websites om te exporteren.");
            return;
        }
// export nog niet gelukt idk hoe het beste dit gedaan kan worden.
        alert(
            `Mock export van ${selectedWebsites.length} website(s) als ${format.toUpperCase()}:\n` +
            selectedWebsites.map(site => site.url)
        );
    };

    return (
        <div style={{ marginTop: "2rem" }}>
            <h2>Exporteer data</h2>
            {formats.map((fmt) => (
                <button
                    key={fmt}
                    onClick={() => handleExport(fmt)}
                    style={{ marginRight: "1rem" }}
                >
                    Exporteer als {fmt.toUpperCase()}
                </button>
            ))}
        </div>
    );
};

export default ExportMenu;
