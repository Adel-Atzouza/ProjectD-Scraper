import React, { useState, useEffect } from "react";

const [websites, setWebsites] = useState<string[]>([]);

useEffect(() => {
    // Load websites from backend
    const fetchWebsites = async () => {
        try {
            const response = await fetch("http://localhost:8000/websites");
            const data = await response.json();
            setWebsites(data.map((w: any) => w.url)); // assuming Website has {id, url}
        } catch (error) {
            console.error("Error loading websites:", error);
        }
    };

    fetchWebsites();
}, []);
