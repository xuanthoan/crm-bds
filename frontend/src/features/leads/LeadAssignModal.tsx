import { useState, type FormEvent } from 'react';
import { FormError } from '../../components/FormError';
import { Modal } from '../../components/Modal';
import type { AdminUser } from '../admin/users/api';
import { formatApiError } from '../../services/apiClient';
import type { Lead } from './types';

export function LeadAssignModal({ lead, owners, onClose, onSubmit, title = 'Phân công lead' }: { lead: Lead; owners: AdminUser[]; onClose: () => void; onSubmit: (ownerId: string, note: string) => Promise<void>; title?: string }) {
  const [ownerId, setOwnerId] = useState(lead.owner?.id ?? ''); const [note, setNote] = useState(''); const [errors, setErrors] = useState<string[] | null>(null); const [saving, setSaving] = useState(false);
  async function submit(e: FormEvent) { e.preventDefault(); if (!ownerId) return setErrors(['Vui lòng chọn người phụ trách.']); setSaving(true); setErrors(null); try { await onSubmit(ownerId, note); } catch (error) { setErrors(formatApiError(error)); } finally { setSaving(false); } }
  return <Modal title={title} onClose={onClose}><form className="admin-form" onSubmit={submit}><label>Người phụ trách<select value={ownerId} onChange={(e: any) => setOwnerId(e.target.value)} required><option value="">Chọn người phụ trách</option>{owners.map((u) => <option key={u.id} value={u.id}>{u.full_name} ({u.roles.map((r) => r.code).join(', ')})</option>)}</select></label><label>Ghi chú<textarea value={note} onChange={(e: any) => setNote(e.target.value)} /></label>{owners.length === 0 && <p className="hint">Không tải được danh sách người dùng phù hợp. Tài khoản cần quyền xem người dùng.</p>}<FormError messages={errors}/><footer className="modal-actions"><button type="button" className="secondary-button" onClick={onClose}>Hủy</button><button disabled={saving || !owners.length}>Phân công</button></footer></form></Modal>;
}
