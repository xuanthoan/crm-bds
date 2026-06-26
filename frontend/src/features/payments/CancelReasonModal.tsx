import { useState, type FormEvent } from 'react';
import { Modal } from '../../components/Modal';
import { FormError } from '../../components/FormError';

type CancelReasonModalProps = {
  title: string;
  warning: string;
  label: string;
  emptyMessage: string;
  confirmLabel: string;
  onClose: () => void;
  onConfirm: (reason: string) => Promise<void> | void;
};

export function CancelReasonModal({ title, warning, label, emptyMessage, confirmLabel, onClose, onConfirm }: CancelReasonModalProps) {
  const [reason, setReason] = useState('');
  const [errors, setErrors] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const trimmed = reason.trim();
    if (!trimmed) {
      setErrors([emptyMessage]);
      return;
    }
    setSaving(true);
    try {
      await onConfirm(trimmed);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title={title} onClose={onClose}>
      <form className="admin-form" onSubmit={submit}>
        <div className="form-warning">{warning}</div>
        <label>{label}<textarea value={reason} onChange={(event) => setReason(event.target.value)} autoFocus /></label>
        <FormError messages={errors} />
        <footer className="modal-actions">
          <button type="button" className="secondary-button" onClick={onClose}>Hủy thao tác</button>
          <button type="submit" disabled={saving}>{saving ? 'Đang xử lý…' : confirmLabel}</button>
        </footer>
      </form>
    </Modal>
  );
}
