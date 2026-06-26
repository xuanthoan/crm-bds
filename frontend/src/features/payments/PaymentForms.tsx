import { useCallback, useEffect, useMemo, useState } from 'react';

import { listContracts } from '../contracts/api';
import type { Contract } from '../contracts/types';
import { formatApiError } from '../../services/apiClient';
import { applyPenalty, contractPaymentSummary, createInvoice, createPaymentSchedule, createReceipt } from './api';

const money = (value: number) => `${new Intl.NumberFormat('vi-VN').format(value || 0)}đ`;

type PaymentScheduleFormProps = {
  contractId?: string;
  contractLabel?: string;
  contractValue?: number;
  scheduledTotal?: number;
  depositAmount?: number;
  onSaved: () => void;
};

export function PaymentScheduleForm({ contractId, contractLabel, contractValue, scheduledTotal, depositAmount, onSaved }: PaymentScheduleFormProps) {
  const [form, setForm] = useState({ contract_id: contractId || '', sequence_no: '', title: '', due_date: '', expected_amount: '', note: '' });
  const [contractSearch, setContractSearch] = useState('');
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [selectedContract, setSelectedContract] = useState<Contract | null>(null);
  const [selectedScheduledTotal, setSelectedScheduledTotal] = useState<number>(scheduledTotal || 0);
  const [errors, setErrors] = useState<string[]>([]);

  const effectiveContractValue = contractValue ?? selectedContract?.contract_value ?? 0;
  const effectiveDepositAmount = depositAmount ?? selectedContract?.deposit_amount ?? selectedContract?.deposit_value ?? 0;
  const schedulableAmount = Math.max(effectiveContractValue - effectiveDepositAmount, 0);
  const remainingSchedulable = Math.max(schedulableAmount - selectedScheduledTotal, 0);
  const hasSelectedContract = Boolean(form.contract_id);
  const hasFullyScheduledContract = hasSelectedContract && effectiveContractValue > 0 && remainingSchedulable <= 0;

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

  useEffect(() => {
    setForm((current) => ({ ...current, contract_id: contractId || current.contract_id }));
    setSelectedScheduledTotal(scheduledTotal || 0);
  }, [contractId, scheduledTotal]);

  useEffect(() => {
    if (!form.contract_id || contractId) return;
    const contract = contracts.find((item) => item.id === form.contract_id) || null;
    setSelectedContract(contract);
    if (!contract) return;
    void contractPaymentSummary(contract.id)
      .then((response) => setSelectedScheduledTotal(Number(response.data.total_expected || 0)))
      .catch((error) => setErrors(formatApiError(error)));
  }, [contracts, contractId, form.contract_id]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!form.contract_id) return setErrors(['Vui lòng chọn hợp đồng.']);
    if (hasFullyScheduledContract) return setErrors(['Hợp đồng này đã lập đủ lịch thanh toán.']);
    const expectedAmount = Number(form.expected_amount);
    if (expectedAmount <= 0) return setErrors(['Số tiền phải thu phải lớn hơn 0.']);
    if (!form.due_date) return setErrors(['Ngày đến hạn là bắt buộc.']);
    if (effectiveContractValue > 0 && expectedAmount > remainingSchedulable) return setErrors(['Tổng lịch thanh toán không được vượt quá số tiền còn phải thu sau cọc.']);
    try {
      await createPaymentSchedule({ ...form, sequence_no: Number(form.sequence_no), expected_amount: expectedAmount });
      setForm({ contract_id: contractId || '', sequence_no: '', title: '', due_date: '', expected_amount: '', note: '' });
      setErrors([]);
      onSaved();
    } catch (error) {
      setErrors(formatApiError(error));
    }
  }

  const contractOptions = useMemo(() => contracts.map((contract) => (
    <option key={contract.id} value={contract.id}>
      {contract.contract_code} · {contract.customer.full_name} · {contract.customer.primary_phone || 'Chưa có SĐT'} · {contract.deal.deal_code}
    </option>
  )), [contracts]);

  return (
    <form onSubmit={submit} className="inline-form">
      <h3>Tạo lịch thanh toán</h3>
      {errors.length > 0 && <div className="form-error">{errors.join('. ')}</div>}
      {contractId ? (
        <p className="helper-text">Hợp đồng: {contractLabel || 'Hợp đồng hiện tại'}</p>
      ) : (
        <>
          <input placeholder="Tìm hợp đồng theo mã HD, SĐT khách hàng hoặc mã deal" value={contractSearch} onChange={(event) => setContractSearch(event.target.value)} />
          <select value={form.contract_id} onChange={(event) => setForm({ ...form, contract_id: event.target.value })}>
            <option value="">Chọn hợp đồng</option>
            {contractOptions}
          </select>
        </>
      )}
      {effectiveContractValue > 0 && <dl className="info-grid"><div><dt>Giá trị hợp đồng</dt><dd>{money(effectiveContractValue)}</dd></div><div><dt>Tiền cọc đã ghi nhận</dt><dd>{money(effectiveDepositAmount)}</dd></div><div><dt>Còn phải lập lịch</dt><dd>{money(schedulableAmount)}</dd></div><div><dt>Tổng đã lập lịch</dt><dd>{money(selectedScheduledTotal)}</dd></div><div><dt>Còn có thể lập lịch</dt><dd>{money(remainingSchedulable)}</dd></div></dl>}
      {hasFullyScheduledContract ? <div className="form-warning">Hợp đồng này đã lập đủ lịch thanh toán.</div> : <>
        <input type="number" placeholder="Số thứ tự đợt" value={form.sequence_no} onChange={(event) => setForm({ ...form, sequence_no: event.target.value })} />
        <input placeholder="Tên đợt thanh toán" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
        <input type="date" value={form.due_date} onChange={(event) => setForm({ ...form, due_date: event.target.value })} />
        <input type="number" placeholder="Số tiền phải thu" value={form.expected_amount} onChange={(event) => setForm({ ...form, expected_amount: event.target.value })} />
        <input placeholder="Ghi chú" value={form.note} onChange={(event) => setForm({ ...form, note: event.target.value })} />
        <button type="submit" disabled={!form.contract_id}>Tạo lịch thanh toán</button>
      </>}
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
