import { useCallback, useEffect, useState } from 'react';

import { navigateTo } from '../../routes/AppRoutes';
import { formatApiError } from '../../services/apiClient';
import { listPayments } from './api';
import { PaymentBadge } from './PaymentBadge';
import { PaymentScheduleForm } from './PaymentForms';
import { PAYMENT_STATUS_LABELS } from './constants';
import type { PaymentSchedule } from './types';

const money = (value: number) => new Intl.NumberFormat('vi-VN').format(value || 0) + 'đ';

export function PaymentsPage() {
  const [items, setItems] = useState<PaymentSchedule[]>([]);
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('');
  const [errors, setErrors] = useState<string[]>([]);

  const load = useCallback(async () => {
    try {
      const filters: Record<string, string> = {};
      if (q) filters.q = q;
      if (status) filters.status = status;
      const response = await listPayments(filters);
      setItems(response.data);
      setErrors([]);
    } catch (error) {
      setErrors(formatApiError(error));
    }
  }, [q, status]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <section className="admin-page">
      <header className="page-header">
        <div>
          <p>Quản lý thanh toán</p>
          <h1>Lịch thanh toán</h1>
          <span>Trang này hiển thị lịch thanh toán Sprint 16. Các khoản PAY cũ vẫn nằm trong chi tiết Hợp đồng để đối chiếu dữ liệu cũ.</span>
        </div>
      </header>
      {errors.length > 0 && <div className="form-error">{errors.join('. ')}</div>}
      <div className="filters">
        <input placeholder="Tìm mã thanh toán, hợp đồng, khách hàng, SĐT, deal" value={q} onChange={(event) => setQ(event.target.value)} />
        <select value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">Tất cả trạng thái</option>
          {Object.entries(PAYMENT_STATUS_LABELS).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
        </select>
        <button onClick={() => void load()}>Lọc</button>
      </div>
      <PaymentScheduleForm onSaved={load} />
      {items.length === 0 && <div className="form-warning">Chưa có lịch thanh toán Sprint 16. Nếu hợp đồng đang có mã PAY cũ, hãy mở chi tiết Hợp đồng để xem mục thanh toán ghi nhận nhanh trước Sprint 16.</div>}
      <div className="table-wrapper">
        <table>
          <thead><tr><th>Mã lịch thanh toán</th><th>Hợp đồng</th><th>Khách hàng</th><th>Đợt</th><th>Hạn thanh toán</th><th>Phải thu</th><th>Đã thu</th><th>Còn lại</th><th>Phí phạt</th><th>Trạng thái</th><th>Hành động</th></tr></thead>
          <tbody>{items.map((payment) => <tr key={payment.id}><td>{payment.payment_code}</td><td>{payment.contract.contract_code}</td><td>{payment.customer?.full_name || 'Chưa cập nhật'}<br /><small>{payment.customer?.primary_phone}</small></td><td>{payment.sequence_no}. {payment.title}</td><td>{new Date(payment.due_date).toLocaleDateString('vi-VN')}</td><td>{money(payment.expected_amount)}</td><td>{money(payment.paid_amount)}</td><td>{money(payment.remaining_amount)}</td><td>{money(payment.penalty_amount)}</td><td><PaymentBadge status={payment.status} /></td><td><button onClick={() => navigateTo(`/payments/${payment.id}`)}>Chi tiết</button></td></tr>)}</tbody>
        </table>
      </div>
    </section>
  );
}
