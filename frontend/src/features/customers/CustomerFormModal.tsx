import { useEffect, useState } from 'react';

import { FormError } from '../../components/FormError';
import { Modal } from '../../components/Modal';
import { formatApiError } from '../../services/apiClient';
import { createCustomer, updateCustomer } from './api';
import { CUSTOMER_STATUS_LABELS, CUSTOMER_TYPE_LABELS } from './constants';
import type { Customer } from './types';
import { buildCustomerPayload } from './validation';

const emptyForm = {
  full_name: '',
  primary_phone: '',
  secondary_phone: '',
  email: '',
  customer_type: 'individual',
  status: 'active',
  source: '',
  interested_project: '',
  interested_area: '',
  budget_min: '',
  budget_max: '',
  bedroom_count: '',
  area_min: '',
  area_max: '',
  purpose: '',
  next_follow_up_at: '',
  note: '',
};

type CustomerFormModalProps = {
  customer?: Customer | null;
  onClose: () => void;
  onSaved: () => void;
};

export function CustomerFormModal({ customer, onClose, onSaved }: CustomerFormModalProps) {
  const [form, setForm] = useState<Record<string, unknown>>(emptyForm);
  const [errors, setErrors] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!customer) return;
    setForm({
      ...emptyForm,
      ...customer,
      next_follow_up_at: customer.next_follow_up_at?.slice(0, 16) ?? '',
    });
  }, [customer]);

  function set(field: string, value: unknown) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrors([]);

    let payload;
    try {
      payload = buildCustomerPayload(form);
    } catch (error) {
      setErrors(formatApiError(error));
      return;
    }

    setSaving(true);
    try {
      if (customer) await updateCustomer(customer.id, payload);
      else await createCustomer(payload);
      onSaved();
    } catch (error) {
      setErrors(formatApiError(error));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title={customer ? 'Chỉnh sửa khách hàng' : 'Tạo khách hàng'} onClose={onClose}>
      <form className="admin-form lead-form" onSubmit={submit} noValidate>
        <div className="form-grid">
          <label>Họ tên *<input required value={String(form.full_name ?? '')} onChange={(event) => set('full_name', event.target.value)} /></label>
          <label>Số điện thoại chính *<input required value={String(form.primary_phone ?? '')} onChange={(event) => set('primary_phone', event.target.value)} /></label>
          <label>Số điện thoại phụ<input value={String(form.secondary_phone ?? '')} onChange={(event) => set('secondary_phone', event.target.value)} /></label>
          <label>Email<input type="email" value={String(form.email ?? '')} onChange={(event) => set('email', event.target.value)} /></label>
          <label>Loại<select value={String(form.customer_type ?? 'individual')} onChange={(event) => set('customer_type', event.target.value)}>{Object.entries(CUSTOMER_TYPE_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          <label>Trạng thái<select value={String(form.status ?? 'active')} onChange={(event) => set('status', event.target.value)}>{Object.entries(CUSTOMER_STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          <label>Nguồn<input value={String(form.source ?? '')} onChange={(event) => set('source', event.target.value)} /></label>
          <label>Dự án quan tâm<input value={String(form.interested_project ?? '')} onChange={(event) => set('interested_project', event.target.value)} /></label>
          <label>Khu vực<input value={String(form.interested_area ?? '')} onChange={(event) => set('interested_area', event.target.value)} /></label>
          <label>Ngân sách tối thiểu<input type="number" min="0" value={String(form.budget_min ?? '')} onChange={(event) => set('budget_min', event.target.value)} /></label>
          <label>Ngân sách tối đa<input type="number" min="0" value={String(form.budget_max ?? '')} onChange={(event) => set('budget_max', event.target.value)} /></label>
          <label>Phòng ngủ<input type="number" min="0" value={String(form.bedroom_count ?? '')} onChange={(event) => set('bedroom_count', event.target.value)} /></label>
          <label>Diện tích tối thiểu<input type="number" min="0" value={String(form.area_min ?? '')} onChange={(event) => set('area_min', event.target.value)} /></label>
          <label>Diện tích tối đa<input type="number" min="0" value={String(form.area_max ?? '')} onChange={(event) => set('area_max', event.target.value)} /></label>
          <label>Chăm sóc tiếp<input type="datetime-local" value={String(form.next_follow_up_at ?? '')} onChange={(event) => set('next_follow_up_at', event.target.value)} /></label>
          <label className="full-span">Ghi chú<textarea rows={3} value={String(form.note ?? '')} onChange={(event) => set('note', event.target.value)} /></label>
        </div>
        <FormError messages={errors} />
        <footer className="modal-actions">
          <button type="button" className="secondary-button" onClick={onClose}>Hủy</button>
          <button disabled={saving}>{saving ? 'Đang lưu…' : 'Lưu khách hàng'}</button>
        </footer>
      </form>
    </Modal>
  );
}
