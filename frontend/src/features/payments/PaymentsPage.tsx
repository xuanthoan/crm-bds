import { useCallback, useEffect, useState } from 'react';

import { Pagination } from '../../components/common/Pagination';
import { navigateTo } from '../../routes/AppRoutes';
import { formatApiError } from '../../services/apiClient';
import { listPayments } from './api';
import { PaymentBadge } from './PaymentBadge';
import { PaymentScheduleForm } from './PaymentForms';
import { PAYMENT_STATUS_LABELS } from './constants';
import { queryFilters } from '../../utils/urlFilters';
import type { PaymentSchedule } from './types';

const money = (value: number) => new Intl.NumberFormat('vi-VN').format(value || 0) + 'đ';
const pageSize = 20;

export function PaymentsPage() {
  const urlFilters = queryFilters<Record<string, string>>({});
  const [items, setItems] = useState<PaymentSchedule[]>([]);
  const [q, setQ] = useState(urlFilters.q || '');
  const [status, setStatus] = useState(urlFilters.status || '');
  const [page, setPage] = useState(1);
  const [meta, setMeta] = useState({ page: 1, total: 0, total_pages: 1 });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);

  const load = useCallback(async (nextPage = page, nextFilters = { q, status }) => {
    setLoading(true);
    try {
      const filters: Record<string, string> = { ...urlFilters, page: String(nextPage), page_size: String(pageSize) };
      if (nextFilters.q) filters.q = nextFilters.q;
      if (nextFilters.status) filters.status = nextFilters.status;
      const response = await listPayments(filters);
      setItems(Array.isArray(response.data) ? response.data : []);
      setMeta({ page: Number(response.meta.page || nextPage), total: Number(response.meta.total || 0), total_pages: Number(response.meta.total_pages || 1) });
      setErrors([]);
    } catch (error) {
      setItems([]);
      setMeta({ page: nextPage, total: 0, total_pages: 1 });
      setErrors(formatApiError(error));
    } finally {
      setLoading(false);
    }
  }, [page, q, status]);

  useEffect(() => { void load(page); }, [load, page]);
  const apply = () => { setPage(1); void load(1, { q, status }); };
  const reset = () => { const next = { q: '', status: '' }; setQ(''); setStatus(''); setPage(1); void load(1, next); };

  return (
    <section className="admin-page">
      <header className="page-header"><div><p>Quản lý thanh toán</p><h1>Lịch thanh toán</h1><span>Quản lý các đợt thanh toán theo hợp đồng.</span></div></header>
      {errors.length > 0 && <div className="form-error">{errors.join('. ')}</div>}
      <div className="filters">
        <input placeholder="Tìm mã thanh toán, hợp đồng, khách hàng, SĐT, deal" value={q} onChange={(event) => setQ(event.target.value)} />
        <select value={status} onChange={(event) => setStatus(event.target.value)}><option value="">Tất cả trạng thái</option>{Object.entries(PAYMENT_STATUS_LABELS).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select>
        <button onClick={apply}>Lọc</button><button className="secondary-button" onClick={reset}>Xóa lọc</button>
      </div>
      <PaymentScheduleForm onSaved={() => load(page)} />
      <div className="table-wrapper"><table><thead><tr><th>Mã lịch thanh toán</th><th>Hợp đồng</th><th>Khách hàng</th><th>Đợt</th><th>Hạn thanh toán</th><th>Phải thu</th><th>Đã thu</th><th>Còn lại</th><th>Phí phạt</th><th>Trạng thái</th><th>Hành động</th></tr></thead><tbody>{items.map((payment) => <tr key={payment.id}><td>{payment.payment_code}</td><td>{payment.contract.contract_code}</td><td>{payment.customer?.full_name || 'Chưa cập nhật'}<br /><small>{payment.customer?.primary_phone}</small></td><td>{payment.sequence_no}. {payment.title}</td><td>{new Date(payment.due_date).toLocaleDateString('vi-VN')}</td><td>{money(payment.expected_amount)}</td><td>{money(payment.paid_amount)}</td><td>{money(payment.remaining_amount)}</td><td>{money(payment.penalty_amount)}</td><td><PaymentBadge status={payment.status} /></td><td><button onClick={() => navigateTo(`/payments/${payment.id}`)}>Chi tiết</button></td></tr>)}</tbody></table></div>
      {loading && <p>Đang tải...</p>}{!loading && !errors.length && items.length === 0 && <p className="empty-state">Không có dữ liệu phù hợp.</p>}
      <Pagination currentPage={meta.page} totalPages={meta.total_pages} totalItems={meta.total} itemLabel="lịch thanh toán" loading={loading} onPageChange={setPage} />
    </section>
  );
}
