import { useEffect, useState } from "react";

type OutputModalProps = {
  isOpen: boolean;
  onClose: () => void;
};

const API = "http://127.0.0.1:8000";

export default function OutputModal({ isOpen, onClose }: OutputModalProps) {
  const [runs, setRuns] = useState<string[]>([]);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [files, setFiles] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContents, setFileContents] = useState<Record<string, any>>({});

  useEffect(() => {
    if (isOpen) {
      fetch(`${API}/runs`)
        .then(r => r.json())
        .then(json => setRuns(json.runs || []));
    } else {
      setSelectedRun(null);
      setFiles([]);
      setSelectedFile(null);
      setFileContents({});
    }
  }, [isOpen]);

  const fetchFiles = (date: string) => {
    setSelectedRun(date);
    setSelectedFile(null);
    setFileContents({});
    fetch(`${API}/output/${date}`)
      .then(r => r.json())
      .then(json => setFiles(json.entries || []));
  };

  const fetchContent = (filename: string) => {
    setSelectedFile(filename);
    if (fileContents[filename]) return;
    fetch(`${API}/output/${selectedRun}/${filename}`)
      .then(r => r.json())
      .then(json => setFileContents(prev => ({ ...prev, [filename]: json })));
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div
        className="modal"
        style={{
          width: "90vw",
          height: "85vh",
          overflow: "hidden",
          display: "flex",
          flexDirection: "column"
        }}
      >
        <div className="modal-header" style={{ padding: "10px 20px" }}>
          <h3>Available Runs</h3>
        </div>

        <div className="badge-container" style={{ padding: "0 20px 10px" }}>
          {runs.map(date => (
            <button
              key={date}
              className={`badge ${selectedRun === date ? "selected" : ""}`}
              onClick={() => fetchFiles(date)}
              style={{
                marginRight: "6px",
                background: selectedRun === date ? "#cce4ff" : "#e5e7eb",
                border: "none",
                borderRadius: "16px",
                padding: "6px 12px",
                cursor: "pointer"
              }}
            >
              {date}
            </button>
          ))}
        </div>

        <div style={{ display: "flex", flex: 1, overflow: "hidden", borderTop: "1px solid #ddd" }}>
          <ul style={{
            width: "20%",
            padding: "12px",
            listStyle: "none",
            overflowY: "auto",
            borderRight: "1px solid #e5e7eb",
            background: "#f9fafb",
            margin: 0
          }}>
            {files.map(fname => (
              <li key={fname} style={{ marginBottom: "8px" }}>
                <button
                  onClick={() => fetchContent(fname)}
                  style={{
                    width: "100%",
                    textAlign: "left",
                    background: fname === selectedFile ? "#cce4ff" : "#fff",
                    color: fname === selectedFile ? "#0b3d91" : "#111827",
                    border: "1px solid #ddd",
                    padding: "6px",
                    borderRadius: "6px",
                    fontWeight: fname === selectedFile ? "600" : "400",
                    cursor: "pointer"
                  }}
                >
                  {fname}
                </button>
              </li>
            ))}
          </ul>

          <section style={{
            flex: 1,
            padding: "12px",
            overflowY: "auto",
            background: "#f3f4f6"
          }}>
            {selectedFile && fileContents[selectedFile] ? (
              <>
                <h4 style={{ marginBottom: "12px" }}>{selectedFile}</h4>
                <pre style={{
                  background: "#1e1e1e",
                  color: "#d4d4d4",
                  padding: "16px",
                  borderRadius: "6px",
                  fontSize: "13px",
                  maxHeight: "60vh",
                  overflowY: "auto",
                  whiteSpace: "pre-wrap",
                  wordWrap: "break-word"
                }}>
                  <code>{JSON.stringify(fileContents[selectedFile], null, 2)}</code>
                </pre>
              </>
            ) : selectedFile ? (
              <p>Loading...</p>
            ) : (
              <p>Select a file to preview.</p>
            )}
          </section>
        </div>

        <div className="modal-buttons" style={{ padding: "10px 20px", borderTop: "1px solid #e5e7eb" }}>
          <button className="primary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}
