import { useState, type FormEvent } from 'react';

import { FormError } from '../../components/FormError';
import { Modal } from '../../components/Modal';
import { formatApiError } from '../../services/apiClient';
import type { AdminUser } from '../admin/users/api';
import type { Lead } from './types';

type LeadAssignModalProps = {
  lead: Lead;
  owners: AdminUser[];
  ownersLoading?: boolean;
  ownersError?: string[] | null;
  onClose: () => void;
  onRetryOwners?: () => void;
  onSubmit: (ownerId: string, note: string) => Promise<void>;
  title?: string;
};

export function LeadAssignModal({
  lead,
  owners,
  ownersLoading = false,
  ownersError = null,
  onClose,
  onRetryOwners,
  onSubmit,
  title = 'Phân công lead',
}: LeadAssignModalProps) {
  const [ownerId, setOwnerId] = useState(lead.owner?.id ?? '');
  const [note, setNote] = useState('');
  const [errors, setErrors] = useState<string[] | null>(null);
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!ownerId) {
      setErrors(['Vui lòng chọn người phụ trách.']);
      return;
    }
    setSaving(true);
    setErrors(null);
    try {
      await onSubmit(ownerId, note);
    } catch (error) {
      setErrors(formatApiError(error));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title={title} onClose={onClose}>
      <form className="admin-form" onSubmit={submit}>
        <label>
          Người phụ trách
          <select
            value={ownerId}
            onChange={(event: any) => setOwnerId(event.target.value)}
            required
            disabled={ownersLoading}
          >
            <option value="">
              {ownersLoading ? 'Đang tải người phụ trách…' : 'Chọn người phụ trách'}
            </option>
            {owners.map((owner) => (
              <option key={owner.id} value={owner.id}>
                {owner.full_name} ({owner.roles.map((role) => role.code).join(', ')})
              </option>
            ))}
          </select>
        </label>
        <label>
          Ghi chú
          <textarea value={note} onChange={(event: any) => setNote(event.target.value)} />
        </label>
        {ownersError && (
          <div>
            <FormError messages={ownersError} />
            {onRetryOwners && (
              <button type="button" className="link-button" onClick={onRetryOwners}>
                Tải lại danh sách
              </button>
            )}
          </div>
        )}
        {!ownersLoading && !ownersError && owners.length === 0 && (
          <p className="hint">Không có người phụ trách phù hợp trong phạm vi được phân công.</p>
        )}
        <FormError messages={errors} />
        <footer className="modal-actions">
          <button type="button" className="secondary-button" onClick={onClose}>Hủy</button>
          <button disabled={saving || ownersLoading || owners.length === 0}>Phân công</button>
        </footer>
      </form>
    </Modal>
  );
}
