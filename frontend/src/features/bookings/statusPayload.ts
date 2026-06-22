import type { BookingStatus } from './types';

export type BookingStatusForm = Record<string, string>;

const optionalNumber = (value: string | undefined) => value ? Number(value) : undefined;
const optionalDate = (value: string | undefined) => value ? new Date(value).toISOString() : undefined;

export function buildBookingStatusPayload(status: BookingStatus, form: BookingStatusForm): Record<string, unknown> {
  const payload: Record<string, unknown> = { status };
  if (form.note?.trim()) payload.note = form.note.trim();

  if (status === 'reserved') {
    payload.booking_amount = optionalNumber(form.booking_amount);
    if (form.reservation_expires_at) payload.reservation_expires_at = optionalDate(form.reservation_expires_at);
  } else if (status === 'deposited') {
    payload.deposit_amount = optionalNumber(form.deposit_amount);
    if (form.deposit_date) payload.deposit_date = optionalDate(form.deposit_date);
  } else if (status === 'cancelled') {
    payload.cancel_reason = form.cancel_reason?.trim();
  } else if (status === 'refunded') {
    payload.refund_amount = optionalNumber(form.refund_amount);
    payload.refund_reason = form.refund_reason?.trim();
    if (form.deduction_reason?.trim()) payload.deduction_reason = form.deduction_reason.trim();
  }

  return payload;
}
