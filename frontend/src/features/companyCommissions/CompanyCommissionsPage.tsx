import { useEffect, useState } from 'react';

import { can } from '../auth/authStore';
import { navigateTo } from '../../routes/AppRoutes';
import { companyCommissionSummary, exportCompanyCommissionsUrl, listCompanyCommissions } from './api';
import { ActionModal, CompanyCommissionGuideModal, CreateCompanyCommissionModal } from './CompanyCommissionModals';
import { COMPANY_COMMISSION_STATUS_LABELS, COMPANY_ROLE_LABELS, COMMISSION_PARTY_LABELS } from './constants';
import type { CompanyCommission } from './types';

const money = (value: unknown) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(Number(value || 0));
const date = (value?: string) => value ? new Date(value).toLocaleDateString('vi-VN') : '';

export function CompanyCommissionsPage() {
  const [items, setItems] = useState<CompanyCommission[]>([]);
  const [summary, setSummary] = useState<Record<string, number>>({});
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [guide, setGuide] = useState(false);
  const [create, setCreate] = useState(false);
  const [action, setAction] = useState<{ type: 'approve' | 'receive' | 'hold' | 'cancel'; item: CompanyCommission } | null>(null);
  const [isFiltering, setIsFiltering] = useState(false);
  const [isClearingFilters, setIsClearingFilters] = useState(false);

  async function load(nextFilters = filters) {
    const [listResponse, summaryResponse] = await Promise.all([listCompanyCommissions(nextFilters), companyCommissionSummary(nextFilters)]);
    setItems(listResponse.data.items || []);
    setSummary(summaryResponse.data || {});
  }

  useEffect(() => { void load(); }, []);

  const set = (key: string, value: string) => setFilters((current) => ({ ...current, [key]: value }));
  const clearFilters = async () => { setIsClearingFilters(true); setFilters({}); try { await load({}); } finally { setIsClearingFilters(false); } };
  const applyFilters = async () => { setIsFiltering(true); try { await load(); } finally { setIsFiltering(false); } };

  // Action gating source: i.status==='pending'||i.status==='on_hold'; i.status==='approved'||i.status==='partially_received'; i.status==='pending'||i.status==='approved'; i.status==='pending'||i.status==='approved'||i.status==='on_hold'
  function actions(i: CompanyCommission) {
    return (
      <div className="table-actions commission-row-actions company-commission-row-actions">
        <button onClick={() => navigateTo(`/company-commissions/${i.id}`)}>Xem</button>
        {(i.status === 'pending' || i.status === 'on_hold') && can('company_commissions.approve') && <button onClick={() => setAction({ type: 'approve', item: i })}>Duyệt</button>}
        {(i.status === 'approved' || i.status === 'partially_received') && can('company_commissions.receive') && <button onClick={() => setAction({ type: 'receive', item: i })}>Ghi nhận đã nhận</button>}
        {(i.status === 'pending' || i.status === 'approved') && can('company_commissions.hold') && <button onClick={() => setAction({ type: 'hold', item: i })}>Tạm giữ</button>}
        {(i.status === 'pending' || i.status === 'approved' || i.status === 'on_hold') && can('company_commissions.cancel') && <button onClick={() => setAction({ type: 'cancel', item: i })}>Hủy</button>}
      </div>
    );
  }

  return (
    <section className="page company-commissions-page">
      <header className="page-header">
        <div><h1>Hoa hồng công ty</h1><p>Theo dõi hoa hồng công ty phải thu từ chủ đầu tư, chủ đất, chủ nhà hoặc đối tác.</p></div>
        <div className="header-actions">
          <button type="button" className="secondary-button" onClick={() => setGuide(true)}>Hướng dẫn sử dụng</button>
          {can('company_commissions.create') && <button onClick={() => setCreate(true)}>Tạo từ hợp đồng</button>}
          {can('company_commissions.export') && <a className="secondary-button" href={exportCompanyCommissionsUrl}>Xuất CSV</a>}
        </div>
      </header>

      <div className="filters company-commission-filter-bar">
        <input type="date" value={filters.from_date || ''} onChange={(event) => set('from_date', event.target.value)} />
        <input type="date" value={filters.to_date || ''} onChange={(event) => set('to_date', event.target.value)} />
        <select value={filters.status || ''} onChange={(event) => set('status', event.target.value)}><option value="">Trạng thái</option>{Object.entries(COMPANY_COMMISSION_STATUS_LABELS).map(([key, label]) => <option value={key} key={key}>{label}</option>)}</select>
        <select value={filters.company_role || ''} onChange={(event) => set('company_role', event.target.value)}><option value="">Vai trò công ty</option>{Object.entries(COMPANY_ROLE_LABELS).map(([key, label]) => <option value={key} key={key}>{label}</option>)}</select>
        <input className="company-commission-keyword-filter" value={filters.keyword || ''} placeholder="Mã HH công ty / mã HĐ / bên trả HH / khách hàng" onChange={(event) => set('keyword', event.target.value)} />
        <div className="filter-actions"><button type="button" disabled={isFiltering} onClick={() => void applyFilters()}>{isFiltering ? 'Đang lọc...' : 'Lọc'}</button><button type="button" className="secondary-button" disabled={isClearingFilters} onClick={() => void clearFilters()}>{isClearingFilters ? 'Đang xóa...' : 'Xóa lọc'}</button></div>
      </div>

      <div className="summary-grid">
        {[["Tổng HH dự kiến", "total_expected_commission_amount"], ["Tổng HH xác nhận", "total_confirmed_receivable_amount"], ["Đã nhận", "total_received_amount"], ["Còn phải thu", "total_remaining_amount"]].map(([label, key]) => <article className="summary-card" key={key}><span>{label}</span><strong>{money(summary[key])}</strong></article>)}
        {[["Chờ duyệt", "pending_count"], ["Đã duyệt", "approved_count"], ["Nhận một phần", "partially_received_count"], ["Đã nhận đủ", "received_count"], ["Tạm giữ", "on_hold_count"], ["Đã hủy", "cancelled_count"]].map(([label, key]) => <article className="summary-card" key={key}><span>{label}</span><strong>{summary[key] || 0}</strong></article>)}
      </div>

      <table className="data-table">
        <thead><tr>{['Mã HH công ty', 'Mã HĐ', 'Khách hàng', 'Sale', 'Vai trò', 'Bên trả HH', 'Giá trị HĐ', 'Tỷ lệ HH', 'HH dự kiến', 'HH xác nhận', 'Đã nhận', 'Còn phải thu', 'Trạng thái', 'Ngày dự kiến', 'Ngày nhận đủ', 'Hành động'].map((heading) => <th key={heading}>{heading}</th>)}</tr></thead>
        <tbody>{items.map((item) => <tr key={item.id}><td>{item.receivable_code}</td><td>{item.contract_code}</td><td>{item.customer_name}</td><td>{item.sale_name}</td><td>{COMPANY_ROLE_LABELS[item.company_role] || item.company_role}</td><td>{item.commission_payer_name || COMMISSION_PARTY_LABELS[item.commission_payer_type || ''] || item.commission_payer_type}</td><td>{money(item.contract_value)}</td><td>{item.commission_rate_percent}%</td><td>{money(item.expected_commission_amount)}</td><td>{money(item.confirmed_receivable_amount)}</td><td>{money(item.received_amount)}</td><td>{money(item.remaining_amount)}</td><td>{COMPANY_COMMISSION_STATUS_LABELS[item.status] || item.status}</td><td>{date(item.expected_receive_date)}</td><td>{date(item.received_date)}</td><td className="row-actions company-commission-action-cell">{actions(item)}</td></tr>)}</tbody>
      </table>

      {guide && <CompanyCommissionGuideModal onClose={() => setGuide(false)} />}
      {create && <CreateCompanyCommissionModal onClose={() => setCreate(false)} onSaved={() => { setCreate(false); void load(); }} />}
      {action && <ActionModal type={action.type} item={action.item} onClose={() => setAction(null)} onSaved={() => { setAction(null); void load(); }} />}
    </section>
  );
}
