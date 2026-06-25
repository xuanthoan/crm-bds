import { useCallback, useEffect, useState } from 'react';

import { listContracts } from '../contracts/api';
import type { Contract } from '../contracts/types';
import { formatApiError } from '../../services/apiClient';
import { applyPenalty, createInvoice, createPaymentSchedule, createReceipt } from './api';

type PaymentScheduleFormProps = {
  contractId?: string;
  contractLabel?: string;
  onSaved: () => void;
};

export function PaymentScheduleForm({ contractId, contractLabel, onSaved }: PaymentScheduleFormProps) {
  const [form, setForm] = useState({ contract_id: contractId || '', sequence_no: '', title: '', due_date: '', expected_amount: '', note: '' });
  const [contractSearch, setContractSearch] = useState('');
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [errors, setErrors] = useState<string[]>([]);

  const loadContracts = useCallback(async () => {
    if (contractId) return;
    try {
      const filters: Record<string, string> = {};
      if (contractSearch.trim()) filters.q = contractSearch.trim();
      const response = await listContracts(filters);
      setContracts(response.data);
    } catch (error) {
      setErrors(formatApiError(error));
    }
  }, [contractId, contractSearch]);

  useEffect(() => {
    void loadContracts();
  }, [loadContracts]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!form.contract_id) return setErrors(['Vui lòng chọn hợp đồng.']);
    if (Number(form.expected_amount) <= 0) return setErrors(['Số tiền phải thu phải lớn hơn 0.']);
    if (!form.due_date) return setErrors(['Ngày đến hạn là bắt buộc.']);
    try {
      await createPaymentSchedule({ ...form, sequence_no: Number(form.sequence_no), expected_amount: Number(form.expected_amount) });
      setForm({ contract_id: contractId || '', sequence_no: '', title: '', due_date: '', expected_amount: '', note: '' });
      setErrors([]);
      onSaved();
    } catch (error) {
      setErrors(formatApiError(error));
    }
  }

  return (
    <form onSubmit={submit} className="inline-form">
      <h3>Tạo lịch thanh toán</h3>
      {errors.length > 0 && <div className="form-error">{errors.join('. ')}</div>}
      {contractId ? (
        <p className="helper-text">Hợp đồng: {contractLabel || 'Hợp đồng hiện tại'}</p>
      ) : (
        <>
          <input
            placeholder="Tìm hợp đồng theo mã HD, SĐT khách hàng hoặc mã deal"
            value={contractSearch}
            onChange={(event) => setContractSearch(event.target.value)}
          />
          <select value={form.contract_id} onChange={(event) => setForm({ ...form, contract_id: event.target.value })}>
            <option value="">Chọn hợp đồng</option>
            {contracts.map((contract) => (
              <option key={contract.id} value={contract.id}>
                {contract.contract_code} · {contract.customer.full_name} · {contract.customer.primary_phone || 'Chưa có SĐT'} · {contract.deal.deal_code}
              </option>
            ))}
          </select>
        </>
      )}
      <input type="number" placeholder="Số thứ tự đợt" value={form.sequence_no} onChange={(event) => setForm({ ...form, sequence_no: event.target.value })} />
      <input placeholder="Tên đợt thanh toán" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
      <input type="date" value={form.due_date} onChange={(event) => setForm({ ...form, due_date: event.target.value })} />
      <input type="number" placeholder="Số tiền phải thu" value={form.expected_amount} onChange={(event) => setForm({ ...form, expected_amount: event.target.value })} />
      <input placeholder="Ghi chú" value={form.note} onChange={(event) => setForm({ ...form, note: event.target.value })} />
      <button type="submit">Tạo lịch thanh toán</button>
    </form>
  );
}

export function ReceiptForm({ paymentId, onSaved }: { paymentId: string; onSaved: () => void }) {
  const [form, setForm] = useState({ amount: '', payment_date: new Date().toISOString().slice(0, 10), payment_method: 'bank_transfer', reference_no: '', note: '', status: 'confirmed' });
  const [errors, setErrors] = useState<string[]>([]);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (Number(form.amount) <= 0) return setErrors(['Số tiền thanh toán phải lớn hơn 0.']);
    try {
      await createReceipt(paymentId, { ...form, amount: Number(form.amount) });
      onSaved();
    } catch (error) {
      setErrors(formatApiError(error));
    }
  }
  return <form onSubmit={submit} className="inline-form"><h3>Ghi nhận thanh toán</h3>{errors.length > 0 && <div className="form-error">{errors.join('. ')}</div>}<input type="number" placeholder="Số tiền" value={form.amount} onChange={e => setForm({ ...form, amount: e.target.value })} /><input type="date" value={form.payment_date} onChange={e => setForm({ ...form, payment_date: e.target.value })} /><select value={form.payment_method} onChange={e => setForm({ ...form, payment_method: e.target.value })}><option value="bank_transfer">Chuyển khoản</option><option value="cash">Tiền mặt</option><option value="card">Thẻ</option><option value="other">Khác</option></select><input placeholder="Mã giao dịch/chứng từ" value={form.reference_no} onChange={e => setForm({ ...form, reference_no: e.target.value })} /><input placeholder="Ghi chú" value={form.note} onChange={e => setForm({ ...form, note: e.target.value })} /><select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })}><option value="confirmed">Xác nhận thanh toán</option><option value="draft">Lưu bản nháp</option></select><button type="submit">Lưu phiếu thu</button></form>;
}

export function PenaltyForm({ paymentId, onSaved }: { paymentId: string; onSaved: () => void }) {
  const [amount, setAmount] = useState('');
  const [reason, setReason] = useState('');
  const [errors, setErrors] = useState<string[]>([]);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (Number(amount) < 0) return setErrors(['Phí phạt không được âm.']);
    if (Number(amount) > 0 && !reason.trim()) return setErrors(['Phí phạt phải có lý do.']);
    try {
      await applyPenalty(paymentId, { penalty_amount: Number(amount), penalty_reason: reason });
      onSaved();
    } catch (error) {
      setErrors(formatApiError(error));
    }
  }
  return <form onSubmit={submit} className="inline-form"><h3>Áp dụng phí phạt</h3>{errors.length > 0 && <div className="form-error">{errors.join('. ')}</div>}<input type="number" placeholder="Phí phạt" value={amount} onChange={e => setAmount(e.target.value)} /><input placeholder="Lý do phí phạt" value={reason} onChange={e => setReason(e.target.value)} /><button type="submit">Áp dụng phí phạt</button></form>;
}

export function InvoiceForm({ paymentId, onSaved }: { paymentId: string; onSaved: () => void }) {
  async function make() {
    await createInvoice(paymentId, { issued_date: new Date().toISOString().slice(0, 10), status: 'draft' });
    onSaved();
  }
  return <button type="button" onClick={make}>Tạo hóa đơn nháp</button>;
}
