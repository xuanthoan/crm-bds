import { Modal } from './Modal';

type ConfirmDialogProps = {
  title: string;
  message: string;
  confirmLabel?: string;
  onCancel: () => void;
  onConfirm: () => void;
};

export function ConfirmDialog({ title, message, confirmLabel = 'Xác nhận', onCancel, onConfirm }: ConfirmDialogProps) {
  return (
    <Modal title={title} onClose={onCancel}>
      <p className="dialog-message">{message}</p>
      <footer className="modal-actions">
        <button type="button" className="secondary-button" onClick={onCancel}>
          Hủy
        </button>
        <button type="button" className="danger-button" onClick={onConfirm}>
          {confirmLabel}
        </button>
      </footer>
    </Modal>
  );
}
