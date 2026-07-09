import { useState, type FocusEvent, type FormEvent } from 'react';
import { FormError } from '../../components/FormError';
import { Modal } from '../../components/Modal';
import type { AdminUser } from '../admin/users/api';
import { formatApiError } from '../../services/apiClient';
import { navigateTo } from '../../routes/AppRoutes';
import { PRIORITY_LABELS, SOURCE_LABELS } from './constants';
import { checkLeadDuplicate } from './api';
import type { DuplicateInfo, Lead, LeadPayload, LeadPriority } from './types';

const text = (value: unknown) => value == null ? '' : String(value);
const numberOrNull = (value: string) => value === '' ? null : Number(value);
const localDateTime = (value?: string | null) => value ? new Date(value).toISOString().slice(0, 16) : '';

function DuplicateLeadModal({ info, onClose, onOpen }: { info: DuplicateInfo; onClose: () => void; onOpen: () => void }) {
  return <Modal title="Số điện thoại đã tồn tại" onClose={onClose}>
    <div className="duplicate-lead-modal">
      <p>{info.message || 'Lead/khách hàng này đã có trong hệ thống. Bạn có thể mở hồ sơ hiện có để tiếp tục chăm sóc.'}</p>
      <dl className="info-grid">
        <div><dt>SĐT trùng</dt><dd>{info.matched_phone || 'Chưa cập nhật'}</dd></div>
        <div><dt>Khách/Lead</dt><dd>{info.lead_name || info.customer_name || 'Trong phạm vi quyền của bạn'}</dd></div>
        <div><dt>Mã hồ sơ</dt><dd>{info.lead_code || info.customer_code || '—'}</dd></div>
        <div><dt>Lý do trùng</dt><dd>{info.match_reason || 'phone_primary/phone_secondary'}</dd></div>
      </dl>
      <p className="form-hint">Bạn chỉ thấy thông tin/hành trình thuộc phạm vi quyền của mình.</p>
      <footer className="modal-actions"><button type="button" className="secondary-button" onClick={onClose}>Đóng</button><button type="button" onClick={onOpen}>Mở thông tin</button></footer>
    </div>
  </Modal>;
}

export function LeadFormModal({ lead, owners, canAssign, onClose, onSubmit }: { lead?: Lead | null; owners: AdminUser[]; canAssign: boolean; onClose: () => void; onSubmit: (payload: LeadPayload) => Promise<any> }) {
  const [form, setForm] = useState<Record<string, string>>({
    full_name: lead?.full_name ?? '', phone_primary: lead?.phone_primary ?? '', phone_secondary: lead?.phone_secondary ?? '', zalo: lead?.zalo ?? '', facebook: lead?.facebook ?? '', email: lead?.email ?? '', address: lead?.address ?? '', source: lead?.source ?? '', project_interest: lead?.project_interest ?? '', location_interest: lead?.location_interest ?? '', budget_min: text(lead?.budget_min), budget_max: text(lead?.budget_max), bedroom_need: text(lead?.bedroom_need), area_min: text(lead?.area_min), area_max: text(lead?.area_max), priority: lead?.priority ?? 'medium', owner_id: lead?.owner?.id ?? '', next_follow_up_at: localDateTime(lead?.next_follow_up_at), note: lead?.note ?? '',
  });
  const [errors, setErrors] = useState<string[] | null>(null);
  const [saving, setSaving] = useState(false);
  const [duplicateInfo, setDuplicateInfo] = useState<DuplicateInfo | null>(null);
  const set = (key: string, value: string) => setForm((current) => ({ ...current, [key]: value }));
  async function checkDuplicateOnBlur(event: FocusEvent<HTMLInputElement>) {
    if (lead) return;
    const phone = event.currentTarget.value.trim();
    if (!phone) return;
    try {
      const response = await checkLeadDuplicate(phone);
      if (response.data?.is_duplicate) setDuplicateInfo(response.data);
    } catch {
      // Duplicate pre-check is advisory; submit still handles duplicate safely.
    }
  }
  function openDuplicateInfo() {
    const url = duplicateInfo?.open_url || (duplicateInfo?.lead_id ? `/leads/${duplicateInfo.lead_id}` : duplicateInfo?.customer_id ? `/customers/${duplicateInfo.customer_id}` : null);
    if (!url) return setDuplicateInfo(null);
    setDuplicateInfo(null);
    onClose();
    navigateTo(url);
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!form.full_name.trim() || !form.phone_primary.trim()) return setErrors(['Họ tên và số điện thoại chính là bắt buộc.']);
    if (form.budget_min && form.budget_max && Number(form.budget_min) > Number(form.budget_max)) return setErrors(['Ngân sách tối thiểu không được lớn hơn ngân sách tối đa']);
    if (form.area_min && form.area_max && Number(form.area_min) > Number(form.area_max)) return setErrors(['Diện tích tối thiểu không được lớn hơn diện tích tối đa']);
    const payload: LeadPayload = { full_name: form.full_name.trim(), phone_primary: form.phone_primary.trim(), phone_secondary: form.phone_secondary || null, zalo: form.zalo || null, facebook: form.facebook || null, email: form.email || null, address: form.address || null, source: form.source || null, project_interest: form.project_interest || null, location_interest: form.location_interest || null, budget_min: numberOrNull(form.budget_min), budget_max: numberOrNull(form.budget_max), bedroom_need: numberOrNull(form.bedroom_need), area_min: numberOrNull(form.area_min), area_max: numberOrNull(form.area_max), priority: form.priority as LeadPriority, next_follow_up_at: form.next_follow_up_at ? new Date(form.next_follow_up_at).toISOString() : null, note: form.note || null };
    if (!lead && canAssign && form.owner_id) payload.owner_id = form.owner_id;
    setSaving(true); setErrors(null);
    try {
      const response = await onSubmit(payload);
      const info = response?.data?.duplicate_info;
      if (info?.is_duplicate) setDuplicateInfo(info);
    } catch (error) { setErrors(formatApiError(error, 'Không thể lưu lead.')); } finally { setSaving(false); }
  }
  return <Modal title={lead ? 'Cập nhật lead' : 'Tạo lead'} onClose={onClose}><form className="admin-form lead-form" onSubmit={submit}>
    <fieldset><legend>Thông tin khách hàng</legend><div className="form-grid">
      {!lead&&<p className="form-hint full-span">Nếu số điện thoại đã tồn tại, hệ thống sẽ ghi nhận lượt tiếp cận lại và cho bạn mở hồ sơ hiện có, không tạo lead trùng mới.</p>}
      <label>Họ tên *<input value={form.full_name} onChange={(e: any) => set('full_name', e.target.value)} required /></label><label>Số điện thoại chính *<input value={form.phone_primary} onBlur={checkDuplicateOnBlur} onChange={(e: any) => set('phone_primary', e.target.value)} required /></label>
      <label>Số điện thoại phụ<input value={form.phone_secondary} onBlur={checkDuplicateOnBlur} onChange={(e: any) => set('phone_secondary', e.target.value)} /></label><label>Zalo<input value={form.zalo} onChange={(e: any) => set('zalo', e.target.value)} /></label>
      <label>Facebook<input value={form.facebook} onChange={(e: any) => set('facebook', e.target.value)} /></label><label>Email<input type="email" value={form.email} onChange={(e: any) => set('email', e.target.value)} /></label>
      <label className="full-span">Địa chỉ<textarea value={form.address} onChange={(e: any) => set('address', e.target.value)} /></label>
    </div></fieldset>
    <fieldset><legend>Nhu cầu quan tâm</legend><div className="form-grid">
      <label>Nguồn<select value={form.source} onChange={(e: any) => set('source', e.target.value)}><option value="">Chọn nguồn</option>{Object.entries(SOURCE_LABELS).map(([v,l]) => <option key={v} value={v}>{l}</option>)}</select></label><label>Dự án quan tâm<input value={form.project_interest} onChange={(e: any) => set('project_interest', e.target.value)} /></label>
      <label>Khu vực quan tâm<input value={form.location_interest} onChange={(e: any) => set('location_interest', e.target.value)} /></label><label>Số phòng ngủ<input type="number" min="0" value={form.bedroom_need} onChange={(e: any) => set('bedroom_need', e.target.value)} /></label>
      <label>Ngân sách tối thiểu<input type="number" min="0" value={form.budget_min} onChange={(e: any) => set('budget_min', e.target.value)} /></label><label>Ngân sách tối đa<input type="number" min="0" value={form.budget_max} onChange={(e: any) => set('budget_max', e.target.value)} /></label>
      <label>Diện tích tối thiểu (m²)<input type="number" min="0" step="0.01" value={form.area_min} onChange={(e: any) => set('area_min', e.target.value)} /></label><label>Diện tích tối đa (m²)<input type="number" min="0" step="0.01" value={form.area_max} onChange={(e: any) => set('area_max', e.target.value)} /></label>
    </div></fieldset>
    <fieldset><legend>Quản lý</legend><div className="form-grid">
      <label>Ưu tiên<select value={form.priority} onChange={(e: any) => set('priority', e.target.value)}>{Object.entries(PRIORITY_LABELS).map(([v,l]) => <option key={v} value={v}>{l}</option>)}</select></label>
      {!lead && canAssign && <label>Sale phụ trách<select value={form.owner_id} onChange={(e: any) => set('owner_id', e.target.value)}><option value="">Tự phụ trách</option>{owners.map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}</select></label>}
      <label>Chăm sóc tiếp theo<input type="datetime-local" value={form.next_follow_up_at} onChange={(e: any) => set('next_follow_up_at', e.target.value)} /></label><label className="full-span">Ghi chú<textarea rows={3} value={form.note} onChange={(e: any) => set('note', e.target.value)} /></label>
    </div></fieldset>
    <FormError messages={errors} /><footer className="modal-actions"><button type="button" className="secondary-button" onClick={onClose}>Hủy</button><button disabled={saving}>{saving ? 'Đang lưu…' : 'Lưu lead'}</button></footer>
  </form>{duplicateInfo&&<DuplicateLeadModal info={duplicateInfo} onClose={()=>setDuplicateInfo(null)} onOpen={openDuplicateInfo}/>}</Modal>;
}
