import { useState, type FormEvent } from 'react';
import { FormError } from '../../components/FormError';
import { Modal } from '../../components/Modal';
import { formatApiError } from '../../services/apiClient';
import { STATUS_LABELS } from './constants';
import type { Lead, LeadStatus } from './types';

export function LeadStatusModal({ lead, onClose, onSubmit }: { lead: Lead; onClose: () => void; onSubmit: (payload: { status: LeadStatus; lost_reason?: string; note?: string }) => Promise<void> }) {
  const [status, setStatus] = useState<LeadStatus>(lead.status); const [lostReason, setLostReason] = useState(lead.lost_reason ?? ''); const [note, setNote] = useState(''); const [errors, setErrors] = useState<string[] | null>(null); const [saving, setSaving] = useState(false);
  async function submit(e: FormEvent) { e.preventDefault(); if (status === 'lost' && !lostReason.trim()) return setErrors(['Vui lòng nhập lý do mất khách']); setSaving(true); setErrors(null); try { await onSubmit({ status, lost_reason: status === 'lost' ? lostReason : undefined, note }); } catch (error) { setErrors(formatApiError(error)); } finally { setSaving(false); } }
  return <Modal title="Thay đổi trạng thái" onClose={onClose}><form className="admin-form" onSubmit={submit}><label>Trạng thái<select value={status} onChange={(e: any) => setStatus(e.target.value)}>{Object.entries(STATUS_LABELS).map(([v,l]) => <option key={v} value={v}>{l}</option>)}</select></label>{status === 'lost' && <label>Lý do mất khách *<textarea value={lostReason} onChange={(e: any) => setLostReason(e.target.value)} required /></label>}<label>Ghi chú<textarea value={note} onChange={(e: any) => setNote(e.target.value)} /></label><FormError messages={errors}/><footer className="modal-actions"><button type="button" className="secondary-button" onClick={onClose}>Hủy</button><button disabled={saving}>Cập nhật</button></footer></form></Modal>;
}
