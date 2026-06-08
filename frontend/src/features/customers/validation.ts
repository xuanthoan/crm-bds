import type { CustomerPayload } from './types';

const PHONE_PATTERN = /^\+?[\d\s-]+$/;
const EMAIL_PATTERN = /^[A-Za-z0-9_%+-]+(?:\.[A-Za-z0-9_%+-]+)*@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$/;
const NUMERIC_FIELDS = ['budget_min', 'budget_max', 'bedroom_count', 'area_min', 'area_max'] as const;
const OPTIONAL_TEXT_FIELDS = [
  'secondary_phone',
  'email',
  'zalo',
  'facebook',
  'address',
  'source',
  'interested_project',
  'interested_area',
  'purpose',
  'next_follow_up_at',
  'note',
] as const;

export function normalizeCustomerPhone(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  if (!PHONE_PATTERN.test(trimmed)) throw new Error('Số điện thoại không hợp lệ');
  let digits = trimmed.replace(/\D/g, '');
  if (digits.length === 11 && digits.startsWith('84')) digits = `0${digits.slice(2)}`;
  if (digits.length !== 10 || !digits.startsWith('0')) throw new Error('Số điện thoại không hợp lệ');
  return digits;
}

export function buildCustomerPayload(form: Record<string, unknown>): CustomerPayload {
  const payload: Record<string, unknown> = { ...form };
  const fullName = String(form.full_name ?? '').trim();
  if (!fullName) throw new Error('Họ tên khách hàng là bắt buộc');
  payload.full_name = fullName;

  const primaryPhone = normalizeCustomerPhone(String(form.primary_phone ?? ''));
  if (!primaryPhone) throw new Error('Số điện thoại chính là bắt buộc');
  payload.primary_phone = primaryPhone;

  const secondaryPhone = normalizeCustomerPhone(String(form.secondary_phone ?? ''));
  payload.secondary_phone = secondaryPhone;

  const email = String(form.email ?? '').trim();
  if (email && !EMAIL_PATTERN.test(email)) throw new Error('Email không hợp lệ');
  payload.email = email ? email.toLowerCase() : null;

  NUMERIC_FIELDS.forEach((field) => {
    const value = form[field];
    payload[field] = value === '' || value === null || value === undefined ? null : Number(value);
  });
  OPTIONAL_TEXT_FIELDS.forEach((field) => {
    if (field === 'secondary_phone' || field === 'email') return;
    const value = form[field];
    payload[field] = typeof value === 'string' && !value.trim() ? null : value ?? null;
  });

  return payload as CustomerPayload;
}
