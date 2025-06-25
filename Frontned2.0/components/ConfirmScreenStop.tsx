// src/components/ConfirmScreenStop.tsx

interface ConfirmModalProps {
  isOpen: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export default function ConfirmModal({ isOpen, onCancel, onConfirm }: ConfirmModalProps) {
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <h3>⚠️ Confirm Action</h3>
        <p>Are you sure you want to stop scraping</p>
        <div className="modal-buttons">
          <button className="danger" onClick={onConfirm}>Yes, Stop</button>
          <button onClick={onCancel}>Cancel</button>
        </div>
      </div>
    </div>
  );
}
