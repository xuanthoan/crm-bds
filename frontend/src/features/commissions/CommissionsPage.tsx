import { useEffect, useState } from 'react';
import { can } from '../auth/authStore';
import { navigateTo } from '../../routes/AppRoutes';
import { approveCommission, cancelCommission, commissionSummary, generateCommission, holdCommission, listCommissions, markPaidCommission, type Commission } from './api';
import { ActionModal, GenerateModal, GuideModal } from './CommissionModals';

const money = (v: number) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(v || 0);
const date = (v: string | null) => v ? new Date(v).toLocaleDateString('vi-VN') : '-';

type ActionState = { type: 'approve' | 'hold' | 'cancel' | 'paid'; c: Commission };

export function CommissionsPage() {
  const [items, setItems] = useState<Commission[]>([]);
  const [summary, setSummary] = useState<Record<string, number>>({});
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [guide, setGuide] = useState(false);
  const [gen, setGen] = useState(false);
  const [action, setAction] = useState<ActionState | null>(null);

  async function load(nextFilters = filters) {
    const [listResponse, summaryResponse] = await Promise.all([listCommissions(nextFilters), commissionSummary(nextFilters)]);
    setItems(listResponse.data.items);
    setSummary(summaryResponse.data);
  }

  useEffect(() => { void load(); }, []);

  const set = (k: string, v: string) => setFilters((current) => ({ ...current, [k]: v }));
  const clearFilters = () => { setFilters({}); void load({}); };

  async function submitAction(p: Record<string, unknown>) {
    if (!action) return;
    if (action.type === 'approve') await approveCommission(action.c.id, p);
    if (action.type === 'hold') await holdCommission(action.c.id, p);
    if (action.type === 'cancel') await cancelCommission(action.c.id, p);
    if (action.type === 'paid') await markPaidCommission(action.c.id, p);
    await load();
  }

  function exportCsv() {
    window.location.href = `/api/v1/commissions/export?${new URLSearchParams(filters).toString()}`;
  }

  const cards = [
    ['Tổng HH đủ điều kiện', money(summary.total_eligible_commission)],
    ['Tổng HH đã duyệt', money(summary.total_approved_commission)],
    ['Tổng đã chi trả', money(summary.total_paid_amount)],
    ['Chờ duyệt', summary.pending_count || 0],
    ['Đã duyệt', summary.approved_count || 0],
    ['Đã chi trả', summary.paid_count || 0],
    ['Tạm giữ', summary.on_hold_count || 0],
    ['Đã hủy', summary.cancelled_count || 0],
  ];

  return (
    <div className="admin-page commissions-page">
      <header className="page-header">
        <div><h1>Quản lý hoa hồng</h1><p>Quản lý hoa hồng đủ điều kiện, duyệt hoa hồng và theo dõi chi trả.</p></div>
        <div className="header-actions">
          <button onClick={() => setGuide(true)}>Hướng dẫn sử dụng</button>
          {can('commissions.create') && <button onClick={() => setGen(true)}>Tạo từ hợp đồng</button>}
          {can('commissions.export') && <button onClick={exportCsv}>Xuất CSV</button>}
        </div>
      </header>
      <div className="filter-bar filter-panel commission-filter-panel">
        <label>Từ ngày<input type="date" value={filters.date_from || ''} onChange={(e) => set('date_from', e.target.value)} /></label>
        <label>Đến ngày<input type="date" value={filters.date_to || ''} onChange={(e) => set('date_to', e.target.value)} /></label>
        <label>Trạng thái<select value={filters.status || ''} onChange={(e) => set('status', e.target.value)}><option value="">Tất cả trạng thái</option><option value="eligible">Đủ điều kiện</option><option value="approved">Đã duyệt</option><option value="paid">Đã chi trả</option><option value="on_hold">Tạm giữ</option><option value="cancelled">Đã hủy</option></select></label>
        <label>Từ khóa<input value={filters.keyword || ''} placeholder="Mã HĐ / mã HH / khách hàng" onChange={(e) => set('keyword', e.target.value)} /></label>
        <div className="filter-actions"><button onClick={() => void load()}>Lọc</button><button className="secondary-button" onClick={clearFilters}>Xóa lọc</button></div>
      </div>
      <section className="metric-grid commission-kpi-grid" aria-label="Chỉ số hoa hồng">
        {cards.map(([label, value], index) => <article className="metric-card" key={String(label)}><span>{label}</span><strong className={index > 2 ? 'commission-count-value' : undefined}>{value}</strong></article>)}
      </section>
      <section className="table-card commission-table-card">
        <div className="section-header commission-table-header"><div><h2>Danh sách hoa hồng</h2><p>{items.length ? `Có ${items.length} hoa hồng đang hiển thị.` : 'Chưa có hoa hồng nào.'}</p></div></div>
        <div className="responsive-table-wrap"><table><thead><tr><th>Mã HH</th><th>Mã HĐ</th><th>Sale</th><th>Khách hàng</th><th>Giá trị HĐ</th><th>Đã thu</th><th>Tỷ lệ HH</th><th>HH đủ điều kiện</th><th>HH đã duyệt</th><th>Đã chi trả</th><th>Trạng thái</th><th>Ngày duyệt</th><th>Ngày chi trả</th><th>Hành động</th></tr></thead><tbody>{items.map((c) => <tr key={c.id}><td>{c.commission_code}</td><td>{c.contract_code}</td><td>{c.sale_name}</td><td>{c.customer_name}</td><td>{money(c.contract_value)}</td><td>{money(c.total_collected_with_deposit)}</td><td>{c.commission_rate_percent}%</td><td>{money(c.eligible_commission)}</td><td>{money(c.approved_commission)}</td><td>{money(c.paid_amount)}</td><td>{c.status_label}</td><td>{date(c.approved_at)}</td><td>{date(c.paid_at)}</td><td><div className="table-actions"><button onClick={() => navigateTo(`/commissions/${c.id}`)}>Xem</button>{can('commissions.approve') && ['eligible', 'on_hold'].includes(c.status) && <button onClick={() => setAction({ type: 'approve', c })}>Duyệt</button>}{can('commissions.hold') && ['eligible', 'approved'].includes(c.status) && <button onClick={() => setAction({ type: 'hold', c })}>Tạm giữ</button>}{can('commissions.mark_paid') && c.status === 'approved' && <button onClick={() => setAction({ type: 'paid', c })}>Đã chi trả</button>}{can('commissions.cancel') && c.status !== 'paid' && <button onClick={() => setAction({ type: 'cancel', c })}>Hủy</button>}</div></td></tr>)}</tbody></table></div>
        {!items.length && <p className="empty-state">Chưa có hoa hồng nào.</p>}
      </section>
      {guide && <GuideModal onClose={() => setGuide(false)} />}
      {gen && <GenerateModal onClose={() => setGen(false)} onSubmit={async (p) => { await generateCommission(p); await load(); }} />}
      {action && <ActionModal type={action.type} commission={action.c} onClose={() => setAction(null)} onSubmit={submitAction} />}
    </div>
  );
}
