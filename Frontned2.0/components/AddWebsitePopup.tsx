import React, { useState } from "react";
import "../src/style.css";

interface AddWebsiteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: () => void;
}

const API = "http://127.0.0.1:8000";

export default function AddWebsiteModal({
  isOpen,
  onClose,
  onAdd,
}: AddWebsiteModalProps) {
  const [url, setUrl] = useState("");
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    if (!url.trim()) {
      setError("Please enter a valid URL.");
      return;
    }

    try {
      const res = await fetch(`${API}/websites`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      if (!res.ok) throw new Error("Failed to add website.");

      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        setUrl("");
        onAdd();
        onClose();
      }, 1200);
    } catch (err) {
      setError("Error adding website.");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal">
        <h3>Add New Website</h3>
        <input
          type="text"
          value={url}
          placeholder="https://example.com"
          onChange={(e) => setUrl(e.target.value)}
        />
        {error && <p className="modal-error">{error}</p>}

        <div className="modal-buttons">
          <button className="primary" onClick={handleSubmit}>
            Add
          </button>
          <button onClick={onClose}>Cancel</button>
        </div>

        {success && (
          <div className="toast success" style={{ marginTop: "12px" }}>
            ✅ Website added!
          </div>
        )}
      </div>
    </div>
  );
}
