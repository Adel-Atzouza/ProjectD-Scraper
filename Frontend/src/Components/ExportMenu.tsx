import React from "react";

interface ExportMenuProps {
    selectedWebsites: string[];
}

const ExportMenu: React.FC<ExportMenuProps> = ({ selectedWebsites }) => {
    const formats = ["csv", "txt", "json"];

    const handleExport = (format: string) => {
        if (selectedWebsites.length === 0) {
            alert("Selecteer eerst websites om te exporteren.");
            return;
        }

        alert(
            `Mock export van ${selectedWebsites.length} website(s) als ${format.toUpperCase()}:\n` +
            selectedWebsites.join("\n")
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
