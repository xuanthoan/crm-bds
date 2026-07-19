import { useEffect, useRef, useState } from 'react';
import { queryFilters } from '../../utils/urlFilters';
import { can } from '../auth/authStore';
import { navigateTo } from '../../routes/AppRoutes';
import { approveCommission, cancelCommission, commissionSummary, generateCommission, holdCommission, listCommissions, type Commission } from './api';
import { createVoucher } from '../commissionPaymentVouchers/api';
import { ActionModal, GenerateModal, GuideModal } from './CommissionModals';
import { Pagination } from '../../components/common/Pagination';
import { GuideBox } from '../../components/help/GuideBox';
import { HelpLabel, HelpTooltip } from '../../components/help/HelpTooltip';
import { tooltipTexts } from '../help/helpContent';

const money = (v: number) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(v || 0);
const date = (v: string | null) => v ? new Date(v).toLocaleDateString('vi-VN') : '-';
const policyReason = (c: Commission, kind: 'approve' | 'paid') => kind === 'approve' ? c.approve_block_reason : c.mark_paid_block_reason;
const canByPolicy = (c: Commission, kind: 'approve' | 'paid') => kind === 'approve' ? c.can_approve_by_company_commission_policy !== false : c.can_mark_paid_by_company_commission_policy !== false;
const companyCommissionStatusClass = (status?: string | null) => `commission-company-status-badge status-${status || 'missing'}`;

type ActionState = { type: 'approve' | 'hold' | 'cancel' | 'paid'; c: Commission };

export function CommissionsPage() {
  const [items, setItems] = useState<Commission[]>([]);
  const [summary, setSummary] = useState<Record<string, number>>({});
  const [filters, setFilters] = useState<Record<string, string>>(()=>queryFilters<Record<string,string>>({ page: '1', page_size: '20' }));
  const [guide, setGuide] = useState(false);
  const [gen, setGen] = useState(false);
  const [action, setAction] = useState<ActionState | null>(null);
  const [notice, setNotice] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [meta, setMeta] = useState({ page: 1, total_pages: 1, total: 0 });
  const [isFiltering, setIsFiltering] = useState(false);
  const [isClearingFilters, setIsClearingFilters] = useState(false);
  const tableScrollRef = useRef<HTMLDivElement | null>(null);
  const topScrollRef = useRef<HTMLDivElement | null>(null);
  const [tableScrollWidth, setTableScrollWidth] = useState(0);

  async function load(nextFilters = filters) {
    setNotice(''); setError(''); setLoading(true);
    try {
      const [listResponse, summaryResponse] = await Promise.all([listCommissions(nextFilters), commissionSummary(nextFilters)]);
      const total = Number(listResponse.data.total || 0); const pageSize = Number(nextFilters.page_size || 20);
      setItems(Array.isArray(listResponse.data.items) ? listResponse.data.items : []);
      setMeta({ page: Number(nextFilters.page || 1), total_pages: Math.max(1, Math.ceil(total / pageSize)), total });
      setSummary(summaryResponse.data || {});
    } catch { setItems([]); setMeta({ page: Number(nextFilters.page || 1), total_pages: 1, total: 0 }); setError('Không thể tải danh sách hoa hồng.'); }
    finally { setLoading(false); }
  }

  useEffect(() => { void load(); }, []);

  useEffect(() => {
    const updateTableScrollWidth = () => setTableScrollWidth(tableScrollRef.current?.scrollWidth || 0);
    updateTableScrollWidth();
    const frame = window.requestAnimationFrame(updateTableScrollWidth);
    window.addEventListener('resize', updateTableScrollWidth);
    return () => { window.cancelAnimationFrame(frame); window.removeEventListener('resize', updateTableScrollWidth); };
  }, [items.length]);

  const set = (k: string, v: string) => setFilters((current) => ({ ...current, [k]: v }));
  const clearFilters = async () => { const next={page:'1',page_size:'20'}; setIsClearingFilters(true); setFilters(next); try { await load(next); } finally { setIsClearingFilters(false); } };
  const applyFilters = async () => { const next={...filters,page:'1'}; setIsFiltering(true); setFilters(next); try { await load(next); } finally { setIsFiltering(false); } };

  async function submitAction(p: Record<string, unknown>) {
    if (!action) return;
    if (action.type === 'approve') await approveCommission(action.c.id, p);
    if (action.type === 'hold') await holdCommission(action.c.id, p);
    if (action.type === 'cancel') await cancelCommission(action.c.id, p);
    if (action.type === 'paid') await createVoucher({sales_commission_id: action.c.id, amount: p.paid_amount, payment_date: p.payment_date, payment_method: p.payment_method || 'bank_transfer', payment_reference: p.payment_reference, note: p.note, attachment_url: p.attachment_url, status: p.status || 'paid'});
    await load();
  }

  function syncTableScroll(source: 'top' | 'bottom') {
    const top = topScrollRef.current;
    const bottom = tableScrollRef.current;
    if (!top || !bottom) return;
    if (source === 'top' && bottom.scrollLeft !== top.scrollLeft) bottom.scrollLeft = top.scrollLeft;
    if (source === 'bottom' && top.scrollLeft !== bottom.scrollLeft) top.scrollLeft = bottom.scrollLeft;
  }

  function exportCsv() {
    window.location.href = `/api/v1/commissions/export?${new URLSearchParams(filters).toString()}`;
  }

  function renderCompanyCommissionCell(c: Commission) {
    const reason = c.approve_block_reason || c.mark_paid_block_reason || 'Hợp đồng chưa có khoản hoa hồng công ty.';
    if (!c.company_commission_code) return <span className="commission-company-missing-badge" title={reason}>Chưa có HH công ty</span>;
    return <div className="commission-company-cell"><strong className="commission-company-code">{c.company_commission_code}</strong><span className={companyCommissionStatusClass(c.company_commission_status)}>{c.company_commission_status_label || c.company_commission_status}</span><small>Đã nhận: {money(c.company_commission_received_amount || 0)}</small><small>Còn phải thu: {money(c.company_commission_remaining_amount || 0)}</small><small>Chính sách chi: {c.payout_policy_label || c.payout_policy?.payout_policy_label || 'Chi theo hạn mức tiền hoa hồng công ty đã nhận'} ({c.payout_policy_source_label || c.payout_policy?.payout_policy_source_label || 'mặc định hệ thống'})</small><small>Tối đa chi lần này <HelpTooltip content={tooltipTexts.remainingPayableCapacity} />: {money(c.remaining_payable_capacity || c.payout_policy?.remaining_payable_capacity || 0)}</small></div>;
  }

  function renderRowActions(c: Commission) {
    const isFinal = c.status === 'paid' || c.status === 'cancelled';
    const canApproveAction = can('commissions.approve') && ['eligible', 'on_hold'].includes(c.status);
    const approvePolicyOk = canByPolicy(c, 'approve');
    const canHoldAction = can('commissions.hold') && ['eligible', 'approved'].includes(c.status);
    const canMarkPaidAction = can('commissions.mark_paid') && ['approved', 'partially_paid'].includes(c.status) && Number(c.paid_amount || 0) < Number(c.approved_commission || 0);
    const paidPolicyOk = canByPolicy(c, 'paid');
    const canCancelAction = can('commissions.cancel') && ['eligible', 'approved', 'on_hold'].includes(c.status);
    const blockedReason = policyReason(c, ['approved', 'partially_paid'].includes(c.status) ? 'paid' : 'approve');
    return <div className="table-actions commission-row-actions"><button onClick={() => navigateTo(`/commissions/${c.id}`)}>Xem</button>{!isFinal && canApproveAction && <button disabled={!approvePolicyOk} title={policyReason(c, 'approve') || undefined} onClick={() => approvePolicyOk && setAction({ type: 'approve', c })}>Duyệt</button>}{!isFinal && canHoldAction && <button onClick={() => setAction({ type: 'hold', c })}>Tạm giữ</button>}{!isFinal && canMarkPaidAction && <><button disabled={!paidPolicyOk} title={policyReason(c, 'paid') || undefined} onClick={() => paidPolicyOk && setAction({ type: 'paid', c })}>Lập phiếu chi</button><HelpTooltip content={tooltipTexts.createPaymentVoucher} /></>}{!isFinal && canCancelAction && <button onClick={() => setAction({ type: 'cancel', c })}>Hủy</button>}{blockedReason && <span className="commission-policy-blocked-caption" title={blockedReason}>Bị chặn</span>}</div>;
  }

  const cards = [
    [<HelpLabel content={tooltipTexts.eligibleCommission}>Tổng HH đủ điều kiện</HelpLabel>, money(summary.total_eligible_commission)],
    [<HelpLabel content={tooltipTexts.approvedCommission}>Tổng HH đã duyệt</HelpLabel>, money(summary.total_approved_commission)],
    [<HelpLabel content={tooltipTexts.paidAmount}>Tổng đã chi trả</HelpLabel>, money(summary.total_paid_amount)],
    ['Chưa có HH công ty', summary.missing_company_commission_count || 0],
    ['Bị chặn chi', summary.blocked_mark_paid_count || 0],
    ['Chờ duyệt', summary.pending_count || 0],
    ['Đã duyệt', summary.approved_count || 0],
    ['Đã chi một phần', summary.partially_paid_count || 0],
    ['Đã chi trả', summary.paid_count || 0],
    ['Tạm giữ', summary.on_hold_count || 0],
    ['Đã hủy', summary.cancelled_count || 0],
  ];

  return (
    <div className="admin-page commissions-page">
      <header className="page-header">
        <div><h1>Quản lý hoa hồng</h1><p>Quản lý hoa hồng đủ điều kiện, duyệt hoa hồng và theo dõi chi trả.</p></div>
        <div className="header-actions">
          <button type="button" className="secondary-button" onClick={() => navigateTo('/help')}>Xem hướng dẫn</button><button type="button" className="secondary-button" onClick={() => setGuide(true)}>Hướng dẫn nhanh</button>
        </div>
      </header>
      <GuideBox title="Cách hiểu hoa hồng sale" items={["Hoa hồng sale cần được duyệt trước khi chi.", "Số đã chi chỉ tính từ phiếu chi đã xác nhận.", "Nếu bị chặn theo chính sách, cần kiểm tra hoa hồng công ty đã nhận hoặc policy chi."]} />
      <div className="commission-primary-actions">
        {can('commissions.create') && <button onClick={() => setGen(true)}>Tạo từ hợp đồng</button>}
        {can('commissions.export') && <button onClick={exportCsv}>Xuất CSV</button>}
      </div>
      {notice && <div className="form-warning">{notice}</div>}
      {error && <div className="form-error">{error}</div>}
      <div className="filter-bar filter-panel commission-filter-panel">
        <label>Từ ngày<input type="date" value={filters.date_from || ''} onChange={(e) => set('date_from', e.target.value)} /></label>
        <label>Đến ngày<input type="date" value={filters.date_to || ''} onChange={(e) => set('date_to', e.target.value)} /></label>
        <label>Trạng thái<select value={filters.status || ''} onChange={(e) => set('status', e.target.value)}><option value="">Tất cả trạng thái</option><option value="eligible">Đủ điều kiện</option><option value="approved">Đã duyệt</option><option value="partially_paid">Đã chi một phần</option><option value="paid">Đã chi trả</option><option value="on_hold">Tạm giữ</option><option value="cancelled">Đã hủy</option></select></label>
        <label>Từ khóa<input value={filters.keyword || ''} placeholder="Mã HĐ / mã HH / khách hàng" onChange={(e) => set('keyword', e.target.value)} /></label>
        <div className="filter-actions"><button disabled={isFiltering} onClick={() => void applyFilters()}>{isFiltering ? 'Đang lọc...' : 'Lọc'}</button><button className="secondary-button" disabled={isClearingFilters} onClick={() => void clearFilters()}>{isClearingFilters ? 'Đang xóa...' : 'Xóa lọc'}</button></div>
      </div>
      <section className="metric-grid commission-kpi-grid" aria-label="Chỉ số hoa hồng">
        {cards.map(([label, value], index) => <article className="metric-card" key={String(label)}><span>{label}</span><strong className={index > 2 ? 'commission-count-value' : undefined}>{value}</strong></article>)}
      </section>
      <section className="table-card commission-table-card">
        <div className="section-header commission-table-header"><div><h2>Danh sách hoa hồng</h2><p>{items.length ? `Có ${items.length} hoa hồng đang hiển thị.` : 'Chưa có hoa hồng nào.'}</p></div></div>
        <p className="muted-text commission-policy-note">Hoa hồng sale chỉ được chi trong phạm vi hoa hồng công ty đã nhận. Chính sách toàn hệ thống đang áp dụng sẽ quyết định tối đa có thể chi.</p><div className="commission-table-top-scroll" ref={topScrollRef} onScroll={() => syncTableScroll('top')}><div className="commission-table-scroll-spacer" style={{ width: tableScrollWidth }} /></div><div className="responsive-table-wrap commission-table-scroll" ref={tableScrollRef} onScroll={() => syncTableScroll('bottom')}><table className="commission-policy-table"><colgroup><col className="commission-col-code"/><col className="commission-col-contract"/><col className="commission-col-sale"/><col className="commission-col-customer"/><col className="commission-col-company"/><col className="commission-col-money"/><col className="commission-col-money"/><col className="commission-col-rate"/><col className="commission-col-money"/><col className="commission-col-money"/><col className="commission-col-money"/><col className="commission-col-status"/><col className="commission-col-date"/><col className="commission-col-date"/><col className="commission-col-actions"/></colgroup><thead><tr><th>Mã HH</th><th>Mã HĐ</th><th>Sale</th><th>Khách hàng</th><th>HH công ty</th><th>Giá trị HĐ</th><th>Đã thu</th><th>Tỷ lệ HH</th><th><HelpLabel content={tooltipTexts.eligibleCommission}>HH đủ điều kiện</HelpLabel></th><th><HelpLabel content={tooltipTexts.approvedCommission}>HH đã duyệt</HelpLabel></th><th><HelpLabel content={tooltipTexts.paidAmount}>Đã chi trả</HelpLabel></th><th><HelpLabel content={tooltipTexts.commissionStatus}>Trạng thái</HelpLabel></th><th>Ngày duyệt</th><th>Ngày chi trả</th><th>Hành động</th></tr></thead><tbody>{items.map((c) => <tr key={c.id}><td>{c.commission_code}</td><td>{c.contract_code}</td><td>{c.sale_name}</td><td>{c.customer_name}</td><td className="commission-company-column">{renderCompanyCommissionCell(c)}</td><td className="commission-money-cell">{money(c.contract_value)}</td><td className="commission-money-cell">{money(c.total_collected_with_deposit)}</td><td className="commission-nowrap-cell">{c.commission_rate_percent}%</td><td className="commission-money-cell">{money(c.eligible_commission)}</td><td className="commission-money-cell">{money(c.approved_commission)}</td><td className="commission-money-cell">{money(c.paid_amount)}</td><td className="commission-nowrap-cell">{c.status_label}</td><td className="commission-nowrap-cell">{date(c.approved_at)}</td><td className="commission-nowrap-cell">{date(c.paid_at)}</td><td className="commission-actions-column">{renderRowActions(c)}</td></tr>)}</tbody></table></div>
        {loading && <p>Đang tải...</p>}
        {!loading && !items.length && <p className="empty-state">Không có dữ liệu phù hợp.</p>}
        <Pagination currentPage={meta.page} totalPages={meta.total_pages} totalItems={meta.total} itemLabel="hoa hồng" loading={loading} onPageChange={(page)=>{const next={...filters,page:String(page)};setFilters(next);void load(next);}} />
      </section>
      {guide && <GuideModal onClose={() => setGuide(false)} />}
      {gen && <GenerateModal onClose={() => setGen(false)} onSubmit={async (p) => { await generateCommission(p); try { await load(); setNotice('Tạo hoa hồng thành công.'); } catch { setNotice('Đã tạo hoa hồng nhưng chưa tải lại được danh sách. Vui lòng bấm Lọc hoặc tải lại trang.'); } }} />}
      {action && <ActionModal type={action.type} commission={action.c} onClose={() => setAction(null)} onSubmit={submitAction} />}
    </div>
  );
}
