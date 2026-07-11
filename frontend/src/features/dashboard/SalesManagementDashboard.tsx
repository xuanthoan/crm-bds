import { useEffect, useMemo, useState } from 'react';

import { HelpLabel } from '../../components/help/HelpTooltip';
import { ApiRequestError } from '../../services/apiClient';
import { DashboardDateRangeFilter } from './DashboardDateRangeFilter';
import { getSalesManagementDashboard } from './api';
import type { DashboardPreset, SalesManagementDashboard as Data } from './types';

const EMPTY_TEXT = 'Chưa có dữ liệu trong khoảng thời gian này.';
const TASK_EMPTY_TEXT = 'Không có công việc quá hạn trong khoảng thời gian này.';

const formatNumber = (value: number | null | undefined) => (Number.isFinite(Number(value)) ? new Intl.NumberFormat('vi-VN').format(Number(value)) : '—');
const formatCurrencyVnd = (value: number | null | undefined) => (Number.isFinite(Number(value)) ? `${new Intl.NumberFormat('vi-VN').format(Number(value))} đ` : '—');
const formatCompactCurrencyVnd = (value: number | null | undefined) => {
  if (!Number.isFinite(Number(value))) return '—';
  const amount = Number(value);
  if (Math.abs(amount) >= 1_000_000_000) return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 }).format(amount / 1_000_000_000)} tỷ đ`;
  if (Math.abs(amount) >= 1_000_000) return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 }).format(amount / 1_000_000)} triệu đ`;
  return formatCurrencyVnd(amount);
};
const formatPercent = (value: number | null | undefined) => (Number.isFinite(Number(value)) ? `${(Number(value) * 100).toFixed(1)}%` : '—');
const safeText = (value: unknown, fallback: string) => (typeof value === 'string' && value.trim() && value !== 'unknown' ? value : fallback);

type ChartRow = { label: string; value: number; fullLabel?: string };
type RankingRow = { name: string; subtitle?: string; value: number | string; valueRaw?: number };

function formatDayTick(dateText: string) {
  const parts = dateText.split('-');
  return parts.length === 3 ? parts[2] : dateText;
}

function formatFullDateTooltip(dateText: string) {
  const parts = dateText.split('-');
  return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : dateText;
}

function formatDateTime(value?: string | null) {
  if (!value) return 'Chưa có hạn';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Chưa có hạn';
  return new Intl.DateTimeFormat('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }).format(date);
}

const STATUS_LABELS: Record<string, string> = {
  new: 'Mới', converted: 'Đã chuyển đổi', pending: 'Đang chờ', in_progress: 'Đang xử lý', completed: 'Hoàn thành', scheduled: 'Đã lên lịch', rescheduled: 'Đổi lịch', cancelled: 'Đã hủy', lost: 'Thất bại', overdue: 'Quá hạn',
};
const statusLabel = (value?: string | null) => (value ? STATUS_LABELS[value] || value.replace(/_/g, ' ') : 'Chưa có trạng thái');

function getXAxisTicks(rows: ChartRow[]) {
  if (rows.length <= 30) return rows.map((row, index) => ({ ...row, index }));
  const step = Math.ceil((rows.length - 1) / 29);
  const ticks = rows.map((row, index) => ({ ...row, index })).filter((_, index) => index === 0 || index === rows.length - 1 || index % step === 0);
  return ticks[ticks.length - 1]?.index === rows.length - 1 ? ticks : [...ticks, { ...rows[rows.length - 1], index: rows.length - 1 }];
}

function KpiCard({ icon, label, value, help, tone = 'ops' }: { icon: string; label: string; value: string; help: string; tone?: 'ops' | 'cash' | 'commission' }) {
  return <article className={`card summary-card kpi-${tone}`}><div className="kpi-icon">{icon}</div><div className="kpi-label-row"><HelpLabel content={help}>{label}</HelpLabel></div><strong title={value}>{value}</strong></article>;
}

function AreaTrendCard({ title, rows, valueType = 'count', emptyText = EMPTY_TEXT, featured = false }: { title: string; rows: ChartRow[]; valueType?: 'count' | 'money'; emptyText?: string; featured?: boolean }) {
  const max = Math.max(1, ...rows.map((row) => row.value));
  const total = rows.reduce((sum, row) => sum + row.value, 0);
  const format = valueType === 'money' ? formatCurrencyVnd : formatNumber;
  const width = 640;
  const height = featured ? 300 : 270;
  const paddingX = 34;
  const paddingTop = 22;
  const paddingBottom = 58;
  const chartWidth = width - paddingX * 2;
  const chartHeight = height - paddingTop - paddingBottom;
  const baselineY = height - paddingBottom;
  const points = rows.map((row, index) => ({ x: paddingX + (rows.length === 1 ? chartWidth / 2 : (index * chartWidth) / Math.max(1, rows.length - 1)), y: paddingTop + chartHeight - (row.value / max) * chartHeight, row }));
  const linePoints = points.map((point) => `${point.x},${point.y}`).join(' ');
  const areaPoints = points.length > 0 ? `${paddingX},${baselineY} ${linePoints} ${width - paddingX},${baselineY}` : '';
  const ticks = getXAxisTicks(rows);
  const last = rows[rows.length - 1];
  const allZero = rows.length > 0 && total === 0;

  return <section className={`card dashboard-chart-card dashboard-area-card${featured ? ' featured' : ''}`}>
    <div className="chart-card-heading"><h3>{title}</h3><span>{rows.length > 0 ? `Tổng: ${valueType === 'money' ? formatCompactCurrencyVnd(total) : format(total)}` : emptyText}</span></div>
    {rows.length === 0 || allZero ? <div className="chart-empty-state">{allZero ? emptyText : EMPTY_TEXT}</div> : <div className="dashboard-area-chart" role="img" aria-label={title}>
      <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
        <defs><linearGradient id={`${title.replace(/\s+/g, '-')}-sales-gradient`} x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#2563eb" stopOpacity="0.34" /><stop offset="100%" stopColor="#2563eb" stopOpacity="0.04" /></linearGradient></defs>
        <line x1={paddingX} x2={width - paddingX} y1={baselineY} y2={baselineY} className="area-axis" /><line x1={paddingX} x2={paddingX} y1={paddingTop} y2={baselineY} className="area-axis" />
        {[0.25, 0.5, 0.75].map((ratio) => <line key={`${title}-grid-${ratio}`} x1={paddingX} x2={width - paddingX} y1={paddingTop + chartHeight * ratio} y2={paddingTop + chartHeight * ratio} className="area-grid-line" />)}
        <polygon points={areaPoints} fill={`url(#${title.replace(/\s+/g, '-')}-sales-gradient)`} /><polyline points={linePoints} className="area-line" />
        {ticks.map((tick) => { const x = paddingX + (rows.length === 1 ? chartWidth / 2 : (tick.index * chartWidth) / Math.max(1, rows.length - 1)); return <g key={`${title}-tick-${tick.index}`}><line x1={x} x2={x} y1={baselineY} y2={baselineY + 5} className="area-tick-line" /><text x={x} y={baselineY + 23} className="area-tick-label" transform={`rotate(-55 ${x} ${baselineY + 23})`}>{tick.label}</text></g>; })}
        {points.map((point, index) => <circle key={`${title}-point-${index}`} cx={point.x} cy={point.y} r={featured ? 4 : 3} className="area-dot"><title>{`${point.row.fullLabel || point.row.label}: ${format(point.row.value)}`}</title></circle>)}
      </svg>
      <div className="area-chart-footer"><span>{rows[0]?.label}</span><strong>{last ? `${last.label}: ${format(last.value)}` : '—'}</strong></div>
    </div>}
  </section>;
}

function TrapezoidFunnel({ title, steps, conversionLabel, conversionRate }: { title: string; steps: { label: string; value: number | null | undefined; color: string }[]; conversionLabel: string; conversionRate: number | null | undefined }) {
  const max = Math.max(1, ...steps.map((step) => Number(step.value || 0)));
  return <section className="card dashboard-funnel-card trapezoid-funnel-card"><h3>{title}</h3><div className="trapezoid-funnel-layout"><div className="trapezoid-funnel">{steps.map((step, index) => { const rawRatio = Number(step.value || 0) / max; const width = Math.max(46, 100 - index * 12, rawRatio * 100); return <div className="trapezoid-segment" style={{ width: `${width}%`, background: step.color }} key={`${title}-${step.label}`}><span>{step.label}</span><strong>{formatNumber(step.value)}</strong></div>; })}</div><aside className="funnel-rate-panel"><span>{conversionLabel}</span><strong>{formatPercent(conversionRate)}</strong></aside></div></section>;
}

function RankingCard({ title, rows, emptyText = EMPTY_TEXT }: { title: string; rows: RankingRow[]; emptyText?: string }) {
  const visibleRows = rows.slice(0, 10);
  const max = Math.max(1, ...visibleRows.map((row) => Number(row.valueRaw ?? 0)));
  return <section className="card ranking-card detail-list-card"><div className="detail-list-header"><h3>{title}</h3></div>{visibleRows.length === 0 ? <div className="chart-empty-state">{emptyText}</div> : <div className="detail-ranking-list sales-ranking-list">{visibleRows.map((row, index) => { const rankTone = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : ''; const width = Math.max(4, (Number(row.valueRaw ?? 0) / max) * 100); return <article className="detail-ranking-row" key={`${title}-${index}`}><div className="detail-rank-name"><span className={`rank-badge ${rankTone}`}>#{index + 1}</span><div title={row.name}><strong>{row.name}</strong>{row.subtitle ? <small>{row.subtitle}</small> : null}<span className="ranking-progress"><i style={{ width: `${width}%` }} /></span></div></div><div className="detail-row-metrics"><strong>{row.value}</strong></div></article>; })}</div>}</section>;
}

function AlertList({ title, rows, emptyText }: { title: string; rows: any[]; emptyText: string }) {
  return <section className="card ranking-card sales-alert-card"><h3>{title}</h3>{rows?.length ? <div className="sales-alert-list">{rows.slice(0, 10).map((item, index) => { const assignee = item.assignee?.full_name || item.owner?.full_name || 'Chưa phân công'; const timeValue = item.due_at || item.start_at || item.last_contact_at; return <article className="sales-alert-row" key={`${title}-${item.id || index}`}><div><strong>{safeText(item.title, 'Chưa có tiêu đề')}</strong><small>{statusLabel(item.status)} · {assignee} · {formatDateTime(timeValue)}</small></div><a href={item.url || '/tasks'}>Mở</a></article>; })}</div> : <div className="chart-empty-state">{emptyText}</div>}</section>;
}

function scopeLabel(scope?: Data['scope']) {
  if (!scope) return '';
  const type = scope.scope_type === 'all' ? 'Toàn bộ' : scope.scope_type === 'team' ? (scope.team_name || 'Nhóm sale') : scope.scope_type === 'department' ? (scope.department_name || 'Phòng ban') : 'Phạm vi được phép';
  return `Phạm vi: ${type} · ${formatNumber(scope.member_count)} sale`;
}

export function SalesManagementDashboard() {
  const today = new Date().toISOString().slice(0, 10);
  const [preset, setPreset] = useState<DashboardPreset>('last_7_days');
  const [fromDate, setFromDate] = useState(today);
  const [toDate, setToDate] = useState(today);
  const [data, setData] = useState<Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let alive = true;
    setLoading(true); setError('');
    getSalesManagementDashboard({ preset, startDate: fromDate, endDate: toDate, scopeType: 'auto' })
      .then((response) => { if (alive) setData(response.data); })
      .catch((err) => { if (alive) setError(err instanceof ApiRequestError && err.status === 403 ? 'Bạn không có quyền xem dashboard quản lý sale.' : 'Không tải được dashboard quản lý sale. Vui lòng thử lại hoặc kiểm tra quyền truy cập.'); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [preset, fromDate, toDate]);

  const s = data?.summary || {};
  const rankings = data?.rankings || {};
  const alerts = data?.alerts || {};
  const leadRows: ChartRow[] = (data?.time_series.leads_by_day ?? []).map((row) => ({ label: formatDayTick(row.date), fullLabel: formatFullDateTooltip(row.date), value: row.count }));
  const revenueRows: ChartRow[] = (data?.time_series.revenue_by_day ?? []).map((row) => ({ label: formatDayTick(row.date), fullLabel: formatFullDateTooltip(row.date), value: row.amount }));
  const overdueRows: ChartRow[] = (data?.time_series.tasks_overdue_by_day ?? []).map((row) => ({ label: formatDayTick(row.date), fullLabel: formatFullDateTooltip(row.date), value: row.count }));
  const headerScope = useMemo(() => scopeLabel(data?.scope), [data]);
  const saleSubtitle = (row: any) => [safeText(row.team_name, ''), safeText(row.department_name, '')].filter(Boolean).join(' · ') || 'Trong phạm vi quản lý';

  return <div className="page dashboard-page boss-dashboard sales-management-dashboard"><div className="dashboard-content">
    <header className="page-header dashboard-header"><div><p className="eyebrow">Dashboard · Sales Management</p><h1>Tổng quan quản lý sale</h1><p>Theo dõi lead, công việc, pipeline và hiệu suất sale trong phạm vi quản lý.</p>{headerScope ? <span className="scope-badge">{headerScope}</span> : null}</div></header>
    <DashboardDateRangeFilter preset={preset} fromDate={fromDate} toDate={toDate} onChange={(next) => { setPreset(next.preset); setFromDate(next.fromDate); setToDate(next.toDate); }} />
    {loading && <div className="card dashboard-state-card">Đang tải dashboard quản lý sale...</div>}
    {error && <div className="card error-state dashboard-state-card">{error}</div>}
    {!loading && !error && data && <>
      <section className="dashboard-kpi-section"><h2>Tổng quan team</h2><div className="summary-grid dashboard-section-grid"><KpiCard icon="👥" label="Sale trong phạm vi" value={formatNumber(s.member_count)} help="Số nhân sự sale thuộc phạm vi quản lý hiện tại." /><KpiCard icon="◦" label="Lead mới" value={formatNumber(s.lead_new_count)} help="Số lead mới được tạo trong khoảng thời gian đã chọn." /><KpiCard icon="✓" label="Lead đã phân công" value={formatNumber(s.lead_assigned_count)} help="Số lead đã có sale phụ trách trong phạm vi quản lý." /><KpiCard icon="!" label="Lead chưa phân công" value={formatNumber(s.lead_unassigned_count)} help="Số lead chưa có sale phụ trách cần được xử lý." /><KpiCard icon="↻" label="Khách trùng tiếp cận lại" value={formatNumber(s.duplicate_reengagement_count)} help="Số lượt khách trùng được ghi nhận là tiếp cận lại." /></div></section>
      <section className="dashboard-kpi-section"><h2>Cảnh báo cần xử lý</h2><div className="summary-grid dashboard-section-grid"><KpiCard icon="!" tone="commission" label="Lead quá hạn" value={formatNumber(s.lead_overdue_count)} help="Số lead đã quá hạn chăm sóc theo quy tắc hiện tại." /><KpiCard icon="?" tone="commission" label="Lead chưa có hoạt động" value={formatNumber(s.lead_without_activity_count)} help="Số lead chưa có hoạt động chăm sóc nào được ghi nhận." /><KpiCard icon="7d" tone="commission" label="Khách lâu chưa tương tác" value={formatNumber(s.lead_stale_count)} help="Số khách/lead chưa có tương tác mới trong hơn 7 ngày." /><KpiCard icon="☑" label="Công việc hôm nay" value={formatNumber(s.task_today_count)} help="Số công việc đến hạn trong ngày hôm nay." /><KpiCard icon="⚠" tone="cash" label="Công việc quá hạn" value={formatNumber(s.task_overdue_count)} help="Số công việc đã quá hạn và chưa hoàn thành." /><KpiCard icon="📅" label="Lịch hẹn hôm nay" value={formatNumber(s.appointment_today_count)} help="Số lịch hẹn diễn ra trong ngày hôm nay." /></div></section>
      <section className="dashboard-kpi-section"><h2>Pipeline & doanh số</h2><div className="summary-grid dashboard-section-grid"><KpiCard icon="□" label="Booking" value={formatNumber(s.booking_count)} help="Số booking/giữ chỗ trong khoảng thời gian đã chọn." /><KpiCard icon="●" label="Khách đã cọc" value={formatNumber(s.deposit_count)} help="Số giao dịch đã ghi nhận cọc trong khoảng thời gian đã chọn." /><KpiCard icon="◇" label="Deal" value={formatNumber(s.deal_count)} help="Số deal/giao dịch trong khoảng thời gian đã chọn." /><KpiCard icon="✓" label="Hợp đồng ký" value={formatNumber(s.contract_signed_count)} help="Số hợp đồng hợp lệ trong khoảng thời gian đã chọn." /><KpiCard icon="$" tone="cash" label="Doanh số" value={formatCompactCurrencyVnd(s.revenue_total)} help="Tổng giá trị hợp đồng hợp lệ trong khoảng thời gian đã chọn." /><KpiCard icon="◈" tone="commission" label="HH sale còn phải chi" value={formatCompactCurrencyVnd(s.sales_commission_outstanding_total)} help="Hoa hồng sale đã duyệt nhưng chưa ghi nhận chi." /></div></section>
      <section className="dashboard-section-block"><h2>Xu hướng</h2><div className="dashboard-grid dashboard-section-grid trend-grid"><AreaTrendCard title="Doanh số theo ngày" rows={revenueRows} valueType="money" featured /><AreaTrendCard title="Lead mới theo ngày" rows={leadRows} /><AreaTrendCard title="Công việc quá hạn theo ngày" rows={overdueRows} emptyText={TASK_EMPTY_TEXT} /></div></section>
      <section className="dashboard-section-block"><h2>Funnel chuyển đổi</h2><div className="dashboard-funnel-grid dashboard-section-grid"><TrapezoidFunnel title="Funnel Lead → Customer" conversionLabel="Lead → Customer" conversionRate={data.funnel.lead_to_customer_rate} steps={[{ label: 'Lead', value: data.funnel.lead_count, color: '#2563eb' }, { label: 'Customer', value: data.funnel.customer_count, color: '#38bdf8' }]} /><TrapezoidFunnel title="Funnel Booking → Cọc → Deal → Hợp đồng" conversionLabel="Booking → Hợp đồng" conversionRate={data.funnel.booking_to_contract_rate} steps={[{ label: 'Booking', value: data.funnel.booking_count, color: '#14b8a6' }, { label: 'Cọc', value: data.funnel.deposit_count, color: '#22c55e' }, { label: 'Deal', value: data.funnel.deal_count, color: '#f59e0b' }, { label: 'Hợp đồng', value: data.funnel.contract_count, color: '#7c3aed' }]} /></div></section>
      <section className="dashboard-section-block"><h2>Hiệu suất sale</h2><div className="ranking-grid dashboard-section-grid"><RankingCard title="Top sale theo doanh số" rows={(rankings.top_sales_by_revenue ?? []).map((r: any) => ({ name: safeText(r.sale_name, 'Chưa có sale'), subtitle: saleSubtitle(r), value: formatCompactCurrencyVnd(r.revenue), valueRaw: r.revenue ?? 0 }))} /><RankingCard title="Top sale theo số hợp đồng" rows={(rankings.top_sales_by_contract_count ?? []).map((r: any) => ({ name: safeText(r.sale_name, 'Chưa có sale'), subtitle: saleSubtitle(r), value: `${formatNumber(r.contract_count)} hợp đồng`, valueRaw: r.contract_count ?? 0 }))} /><RankingCard title="Top sale theo hoạt động chăm sóc" rows={(rankings.top_sales_by_activity_count ?? []).map((r: any) => ({ name: safeText(r.sale_name, 'Chưa có sale'), subtitle: saleSubtitle(r), value: `${formatNumber(r.activity_count)} hoạt động`, valueRaw: r.activity_count ?? 0 }))} /><RankingCard title="Sale có nhiều lead quá hạn" rows={(rankings.top_sales_with_overdue_leads ?? []).map((r: any) => ({ name: safeText(r.sale_name, 'Chưa có sale'), subtitle: saleSubtitle(r), value: `${formatNumber(r.overdue_lead_count)} lead`, valueRaw: r.overdue_lead_count ?? 0 }))} /></div></section>
      <section className="dashboard-section-block"><h2>Nguồn & dự án</h2><div className="ranking-grid dashboard-section-grid"><RankingCard title="Top nguồn lead theo số lead" rows={(rankings.top_sources_by_lead_count ?? []).map((r: any) => ({ name: safeText(r.source, 'Chưa xác định'), subtitle: `${formatNumber(r.contract_count ?? 0)} hợp đồng`, value: `${formatNumber(r.lead_count)} lead`, valueRaw: r.lead_count ?? 0 }))} /><RankingCard title="Top dự án theo doanh số" rows={(rankings.top_projects_by_revenue ?? []).map((r: any) => ({ name: safeText(r.project_name, 'Chưa có dự án'), subtitle: `${formatNumber(r.contract_count ?? 0)} hợp đồng`, value: formatCompactCurrencyVnd(r.revenue), valueRaw: r.revenue ?? 0 }))} /></div></section>
      <section className="dashboard-section-block"><h2>Danh sách cần xử lý</h2><div className="dashboard-section-grid"><AlertList title="Lead quá hạn" rows={alerts.overdue_leads ?? []} emptyText="Không có lead quá hạn." /><AlertList title="Công việc quá hạn" rows={alerts.overdue_tasks ?? []} emptyText="Không có công việc quá hạn." /><AlertList title="Lead chưa phân công" rows={alerts.unassigned_leads ?? []} emptyText="Không có lead chưa phân công." /><AlertList title="Lịch hẹn hôm nay" rows={alerts.today_appointments ?? []} emptyText="Không có lịch hẹn hôm nay." /></div></section>
    </>}
  </div></div>;
}
