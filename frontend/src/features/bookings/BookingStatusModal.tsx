import { useState, type FormEvent } from 'react';
import { Modal } from '../../components/Modal';
import { formatApiError } from '../../services/apiClient';
import { changeBookingStatus } from './api';
import { BOOKING_STATUS_LABELS, isFinalBookingStatus } from './constants';
import { buildBookingStatusPayload, type BookingStatusForm } from './statusPayload';
import type { Booking, BookingStatus } from './types';

export function BookingStatusModal({ booking, onClose, onSaved }: { booking: Booking; onClose: () => void; onSaved: () => void }) {
  const isLocked = !!booking.has_effective_contract;
  const isFinal = isFinalBookingStatus(booking.status);
  const statusOptions = Object.entries(BOOKING_STATUS_LABELS).filter(([key]) => !isFinal || key === booking.status);
  const [status, setStatus] = useState<BookingStatus>(booking.status);
  const [form, setForm] = useState<BookingStatusForm>({});
  const [error, setError] = useState('');
  const set = (key: string, value: string) => setForm((current) => ({ ...current, [key]: value }));
  const refundBasis = booking.deposit_amount ?? booking.booking_amount ?? 0;
  const refundAmount = form.refund_amount === undefined || form.refund_amount === '' ? null : Number(form.refund_amount);
  const deductionAmount = status === 'refunded' && refundAmount !== null ? Math.max(refundBasis - refundAmount, 0) : null;

  function selectStatus(nextStatus: BookingStatus) {
    setStatus(nextStatus);
    setError('');
    setForm(nextStatus === 'reserved' && booking.booking_amount != null
      ? { booking_amount: String(booking.booking_amount) }
      : {});
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (isLocked) return setError('Booking đã có hợp đồng hiệu lực nên không thể hủy, hoàn tiền, hết hạn, đổi trạng thái hoặc xóa. Vui lòng hủy hợp đồng trước.');
    if (isFinal && status !== booking.status) return setError('Booking đã ở trạng thái kết thúc nên không thể chuyển lại trạng thái hoạt động.');
    if (status === 'reserved' && (!form.booking_amount || Number(form.booking_amount) <= 0)) return setError('Tiền giữ chỗ là bắt buộc khi giữ chỗ');
    if (status === 'deposited' && (!form.deposit_amount || Number(form.deposit_amount) <= 0)) return setError('Tiền cọc là bắt buộc khi đặt cọc');
    if (status === 'cancelled' && !form.cancel_reason?.trim()) return setError('Lý do hủy là bắt buộc');
    if (status === 'refunded' && (form.refund_amount === undefined || form.refund_amount === '')) return setError('Số tiền hoàn là bắt buộc');
    if (status === 'refunded' && Number(form.refund_amount) < 0) return setError('Số tiền hoàn không được âm');
    if (status === 'refunded' && Number(form.refund_amount) > refundBasis) return setError('Số tiền hoàn không được vượt quá số tiền booking.');
    if (status === 'refunded' && !form.refund_reason?.trim()) return setError('Lý do hoàn tiền là bắt buộc');
    try {
      await changeBookingStatus(booking.id, buildBookingStatusPayload(status, form));
      onSaved();
    } catch (requestError) {
      setError(formatApiError(requestError).join('. '));
    }
  }

  return <Modal title="Đổi trạng thái booking" onClose={onClose}>
    <form className="property-form" onSubmit={submit}>
      {isLocked && <div className="form-warning">Booking đã có hợp đồng hiệu lực nên không thể hủy, hoàn tiền, hết hạn, đổi trạng thái hoặc xóa. Vui lòng hủy hợp đồng trước.</div>}
      {error && <div className="form-error">{error}</div>}
      <label>Trạng thái hiện tại<input readOnly value={BOOKING_STATUS_LABELS[booking.status] || booking.status} /></label>
      <label>Trạng thái mới<select value={status} disabled={isLocked || isFinal} onChange={(event) => selectStatus(event.target.value as BookingStatus)}>{statusOptions.map(([key, value]) => <option key={key} value={key}>{value}</option>)}</select></label>
      {status === 'reserved' && <><label>Hết hạn giữ chỗ<input type="datetime-local" onChange={(event) => set('reservation_expires_at', event.target.value)} /></label><label>Tiền giữ chỗ *<input type="number" min="1" required value={form.booking_amount || ''} onChange={(event) => set('booking_amount', event.target.value)} /></label></>}
      {status === 'deposited' && <><label>Tiền cọc *<input type="number" min="1" required value={form.deposit_amount || ''} onChange={(event) => set('deposit_amount', event.target.value)} /></label><label>Ngày cọc<input type="datetime-local" onChange={(event) => set('deposit_date', event.target.value)} /></label></>}
      {status === 'cancelled' && <label>Lý do hủy *<textarea value={form.cancel_reason || ''} onChange={(event) => set('cancel_reason', event.target.value)} /></label>}
      {status === 'refunded' && <><label>Số tiền hoàn *<input type="number" min="0" max={refundBasis} required value={form.refund_amount || ''} onChange={(event) => set('refund_amount', event.target.value)} /></label><div className="form-hint">Số tiền booking: {new Intl.NumberFormat('vi-VN').format(refundBasis)} VNĐ · Khấu trừ tự động: {deductionAmount === null ? 'Chưa cập nhật' : `${new Intl.NumberFormat('vi-VN').format(deductionAmount)} VNĐ`}</div><label>Lý do hoàn tiền *<textarea value={form.refund_reason || ''} onChange={(event) => set('refund_reason', event.target.value)} /></label><label>Lý do khấu trừ<textarea value={form.deduction_reason || ''} onChange={(event) => set('deduction_reason', event.target.value)} /></label></>}
      <label>Ghi chú<textarea value={form.note || ''} onChange={(event) => set('note', event.target.value)} /></label>
      <footer className="modal-actions"><button type="button" className="secondary-button" onClick={onClose}>Hủy</button><button type="submit" disabled={isLocked || isFinal}>Lưu trạng thái</button></footer>
    </form>
  </Modal>;
}
