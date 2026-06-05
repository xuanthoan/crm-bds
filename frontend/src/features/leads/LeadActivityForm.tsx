import { useState, type FormEvent } from 'react';
import { FormError } from '../../components/FormError';
import { formatApiError } from '../../services/apiClient';
import { ACTIVITY_LABELS } from './constants';
import type { LeadActivityType } from './types';

export function LeadActivityForm({ onSubmit }: { onSubmit: (payload: { activity_type: LeadActivityType; title: string; content: string }) => Promise<void> }) {
  const [type, setType] = useState<LeadActivityType>('note'); const [title, setTitle] = useState(''); const [content, setContent] = useState(''); const [errors, setErrors] = useState<string[] | null>(null); const [saving, setSaving] = useState(false);
  async function submit(e: FormEvent) { e.preventDefault(); if (!content.trim()) return setErrors(['Nội dung hoạt động là bắt buộc.']); setSaving(true); setErrors(null); try { await onSubmit({ activity_type: type, title, content }); setTitle(''); setContent(''); } catch (error) { setErrors(formatApiError(error)); } finally { setSaving(false); } }
  return <form className="activity-form" onSubmit={submit}><div className="form-grid"><label>Loại hoạt động<select value={type} onChange={(e: any) => setType(e.target.value)}>{(['note','call','zalo','meeting'] as LeadActivityType[]).map((v) => <option key={v} value={v}>{ACTIVITY_LABELS[v]}</option>)}</select></label><label>Tiêu đề<input value={title} onChange={(e: any) => setTitle(e.target.value)} /></label><label className="full-span">Nội dung *<textarea rows={3} value={content} onChange={(e: any) => setContent(e.target.value)} required /></label></div><FormError messages={errors}/><button disabled={saving}>{saving ? 'Đang thêm…' : 'Thêm hoạt động'}</button></form>;
}
