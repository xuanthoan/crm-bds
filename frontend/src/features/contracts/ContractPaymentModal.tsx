import { FormEvent, useState } from 'react';

import { Modal } from '../../components/Modal';
import { FormError } from '../../components/FormError';
import { formatApiError } from '../../services/apiClient';
import { confirmPayment, createPayment } from './api';
import { PAYMENT_METHOD_LABELS } from './constants';
import type { ContractPayment } from './types';

const localDateTime = (value?: string | null) => {
  const date = value ? new Date(value) : new Date();
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
};

export function ContractPaymentModal({
  contractId,
  payment,
  onClose,
  onSaved,
}: {
  contractId: string;
  payment?: ContractPayment;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [amount, setAmount] = useState(String(payment?.amount || ''));
  const [dueDate, setDueDate] = useState('');
  const [method, setMethod] = useState(payment?.payment_method || 'bank_transfer');
  const [referenceNumber, setReferenceNumber] = useState(payment?.reference_number || '');
  const [paidDate, setPaidDate] = useState(localDateTime(payment?.paid_date));
  const [note, setNote] = useState(payment?.note || '');
  const [errors, setErrors] = useState<string[]>([]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setErrors([]);
    if (!payment && (!amount || Number(amount) <= 0)) {
      setErrors(['Số tiền thanh toán phải lớn hơn 0.']);
      return;
    }
    if (payment && !method) {
      setErrors(['Phương thức thanh toán là bắt buộc.']);
      return;
    }
    if (payment && !paidDate) {
      setErrors(['Ngày thanh toán là bắt buộc.']);
      return;
    }
    try {
      if (payment) {
        await confirmPayment(contractId, payment.id, {
          payment_method: method,
          reference_number: referenceNumber.trim() || null,
          paid_date: paidDate ? new Date(paidDate).toISOString() : null,
          note: note.trim() || null,
        });
      } else {
        await createPayment(contractId, {
          amount: Number(amount),
          payment_type: 'installment',
          due_date: dueDate ? new Date(dueDate).toISOString() : null,
          note: note.trim() || null,
        });
      }
      onSaved();
    } catch (error) {
      setErrors(formatApiError(error));
    }
  }

  return (
    <Modal title={payment ? 'Xác nhận thanh toán' : 'Thêm thanh toán'} onClose={onClose}>
      <form className="contract-payment-form" onSubmit={submit}>
        <FormError messages={errors} />
        {!payment ? (
          <>
            <label>Số tiền *<input required type="number" min="1" value={amount} onChange={(event) => setAmount(event.target.value)} /></label>
            <label>Hạn thanh toán<input type="datetime-local" value={dueDate} onChange={(event) => setDueDate(event.target.value)} /></label>
          </>
        ) : (
          <>
            <label>Phương thức thanh toán *
              <select required value={method} onChange={(event) => setMethod(event.target.value)}>
                {Object.entries(PAYMENT_METHOD_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
            </label>
            <label>Mã tham chiếu / mã giao dịch<input value={referenceNumber} onChange={(event) => setReferenceNumber(event.target.value)} /></label>
            <label>Ngày thanh toán *<input required type="datetime-local" value={paidDate} onChange={(event) => setPaidDate(event.target.value)} /></label>
          </>
        )}
        <label className="full-span">Ghi chú<textarea value={note} onChange={(event) => setNote(event.target.value)} /></label>
        <footer className="modal-actions">
          <button type="button" className="secondary-button" onClick={onClose}>Hủy</button>
          <button>{payment ? 'Xác nhận thanh toán' : 'Tạo thanh toán'}</button>
        </footer>
      </form>
    </Modal>
  );
}
