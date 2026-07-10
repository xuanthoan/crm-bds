import { useEffect, useMemo, useState, type ReactNode } from 'react';

import { DashboardDateRangeFilter } from './DashboardDateRangeFilter';
import { getBossDashboard } from './api';
import type { BossDashboard as BossDashboardData, DashboardPreset } from './types';

const EMPTY_TEXT = 'Chưa có dữ liệu trong khoảng thời gian này.';

const formatNumber = (value: number | null | undefined) => (Number.isFinite(Number(value)) ? new Intl.NumberFormat('vi-VN').format(Number(value)) : '—');
const formatCurrencyVnd = (value: number | null | undefined) => (Number.isFinite(Number(value)) ? `${new Intl.NumberFormat('vi-VN').format(Number(value))} đ` : '—');
const formatCompactCurrencyVnd = (value: number | null | undefined) => {
  if (!Number.isFinite(Number(value))) return '—';
  const amount = Number(value);
  if (Math.abs(amount) >= 1_000_000_000) return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 }).format(amount / 1_000_000_000)} tỷ đ`;
  if (Math.abs(amount) >= 1_000_000) return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 }).format(amount / 1_000_000)} triệu đ`;
  return formatCurrencyVnd(amount);
};
const formatCurrencyTooltip = formatCurrencyVnd;
const formatPercent = (value: number | null | undefined) => (Number.isFinite(Number(value)) ? `${(Number(value) * 100).toFixed(1)}%` : '—');
const safeLabel = (value: unknown, fallback: string) => (typeof value === 'string' && value.trim() && value !== 'unknown' ? value : fallback);

type ChartRow = { label: string; value: number; meta?: string };

function normalizeDailySeries(rows: ChartRow[], maxPoints = 30) {
  if (rows.length <= maxPoints) return rows;
  const step = Math.ceil(rows.length / maxPoints);
  const sampled = rows.filter((_, index) => index % step === 0).slice(0, maxPoints - 1);
  const last = rows[rows.length - 1];
  return sampled[sampled.length - 1]?.label === last.label ? sampled : [...sampled, last];
}

type BarChartProps = {
  title: string;
  rows: ChartRow[];
  valueType?: 'count' | 'money';
  horizontal?: boolean;
};

function ChartEmptyState() {
  return <div className="chart-empty-state">{EMPTY_TEXT}</div>;
}

function BarChartCard({ title, rows, valueType = 'count', horizontal = false }: BarChartProps) {
  const visibleRows = rows.filter((row) => row.value > 0).slice(0, 10);
  const max = Math.max(1, ...visibleRows.map((row) => row.value));
  const format = valueType === 'money' ? formatCurrencyVnd : formatNumber;

  return (
    <section className="card dashboard-chart-card">
      <h3>{title}</h3>
      {visibleRows.length === 0 ? <ChartEmptyState /> : (
        <div className={horizontal ? 'dashboard-hbar-chart' : 'dashboard-column-chart'}>
          {visibleRows.map((row) => {
            const size = Math.max(6, (row.value / max) * 100);
            return (
              <div className="dashboard-chart-item" key={`${title}-${row.label}`}>
                {horizontal ? (
                  <>
                    <div className="chart-item-label"><strong>{row.label}</strong>{row.meta ? <span>{row.meta}</span> : null}</div>
                    <div className="chart-item-track"><span style={{ width: `${size}%` }} /></div>
                    <em>{format(row.value)}</em>
                  </>
                ) : (
                  <>
                    <div className="column-bar-wrap"><span style={{ height: `${size}%` }} /></div>
                    <strong>{format(row.value)}</strong>
                    <em>{row.label}</em>
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}


function AreaTrendCard({ title, rows, valueType = 'count', featured = false }: { title: string; rows: ChartRow[]; valueType?: 'count' | 'money'; featured?: boolean }) {
  const visibleRows = normalizeDailySeries(rows, 30);
  const max = Math.max(1, ...visibleRows.map((row) => row.value));
  const format = valueType === 'money' ? formatCurrencyVnd : formatNumber;
  const width = 640;
  const height = featured ? 260 : 210;
  const paddingX = 28;
  const paddingY = 22;
  const chartWidth = width - paddingX * 2;
  const chartHeight = height - paddingY * 2;
  const points = visibleRows.map((row, index) => {
    const x = paddingX + (visibleRows.length === 1 ? chartWidth / 2 : (index * chartWidth) / (visibleRows.length - 1));
    const y = paddingY + chartHeight - (row.value / max) * chartHeight;
    return { x, y, row };
  });
  const linePoints = points.map((point) => `${point.x},${point.y}`).join(' ');
  const areaPoints = points.length > 0 ? `${paddingX},${height - paddingY} ${linePoints} ${width - paddingX},${height - paddingY}` : '';
  const last = visibleRows[visibleRows.length - 1];
  const total = visibleRows.reduce((sum, row) => sum + row.value, 0);

  return (
    <section className={`card dashboard-chart-card dashboard-area-card${featured ? ' featured' : ''}`}>
      <div className="chart-card-heading">
        <h3>{title}</h3>
        <span>{visibleRows.length > 0 ? `Tổng: ${valueType === 'money' ? formatCompactCurrencyVnd(total) : format(total)}` : EMPTY_TEXT}</span>
      </div>
      {visibleRows.length === 0 ? <ChartEmptyState /> : (
        <div className="dashboard-area-chart" role="img" aria-label={title}>
          <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
            <defs>
              <linearGradient id={`${title.replace(/\s+/g, '-')}-gradient`} x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#2563eb" stopOpacity="0.34" />
                <stop offset="100%" stopColor="#2563eb" stopOpacity="0.04" />
              </linearGradient>
            </defs>
            <line x1={paddingX} x2={width - paddingX} y1={height - paddingY} y2={height - paddingY} className="area-axis" />
            <line x1={paddingX} x2={paddingX} y1={paddingY} y2={height - paddingY} className="area-axis" />
            <polygon points={areaPoints} fill={`url(#${title.replace(/\s+/g, '-')}-gradient)`} />
            <polyline points={linePoints} className="area-line" />
            {points.map((point, index) => <circle key={`${title}-${index}`} cx={point.x} cy={point.y} r={featured ? 4 : 3} className="area-dot"><title>{`${point.row.label}: ${format(point.row.value)}`}</title></circle>)}
          </svg>
          <div className="area-chart-footer">
            <span>{visibleRows[0]?.label}</span>
            <strong>{last ? `${last.label}: ${format(last.value)}` : '—'}</strong>
          </div>
        </div>
      )}
    </section>
  );
}

function TrapezoidFunnel({ title, steps, conversionLabel, conversionRate }: { title: string; steps: { label: string; value: number | null | undefined; color: string }[]; conversionLabel: string; conversionRate: number | null | undefined }) {
  const max = Math.max(1, ...steps.map((step) => Number(step.value || 0)));
  return (
    <section className="card dashboard-funnel-card trapezoid-funnel-card">
      <h3>{title}</h3>
      <div className="trapezoid-funnel-layout">
        <div className="trapezoid-funnel">
          {steps.map((step, index) => {
            const rawRatio = Number(step.value || 0) / max;
            const width = Math.max(46, 100 - index * 12, rawRatio * 100);
            return (
              <div className="trapezoid-segment" style={{ width: `${width}%`, background: step.color }} key={`${title}-${step.label}`}>
                <span>{step.label}</span>
                <strong>{formatNumber(step.value)}</strong>
              </div>
            );
          })}
        </div>
        <aside className="funnel-rate-panel">
          <span>{conversionLabel}</span>
          <strong>{formatPercent(conversionRate)}</strong>
        </aside>
      </div>
    </section>
  );
}

function DetailTable({ title, rows, type }: { title: string; rows: any[]; type: 'sale' | 'team' | 'project' | 'source' }) {
  const visibleRows = rows.slice(0, 10);
  const fallback = type === 'project' ? 'Chưa có dự án' : type === 'sale' ? 'Chưa có sale' : type === 'team' ? 'Chưa có team' : 'Chưa xác định';
  const getName = (row: any) => safeLabel(row.sale_name || row.team_name || row.project_name || row.source, fallback);
  const getSubtitle = (row: any) => {
    if (type === 'sale') return safeLabel(row.team_name, 'Chưa có team');
    if (type === 'team') return safeLabel(row.department_name, 'Chưa có phòng ban');
    if (type === 'project') return `${formatNumber(row.contract_count)} hợp đồng`;
    return `${formatNumber(row.lead_count)} lead · ${formatNumber(row.contract_count ?? 0)} hợp đồng`;
  };

  return (
    <section className="card ranking-card detail-table-card">
      <div className="detail-table-header">
        <div>
          <h3>{title}</h3>
          <p>Thông tin chi tiết theo top 10, sắp xếp theo hiệu suất.</p>
        </div>
        <span className="detail-table-badge">Top {Math.min(visibleRows.length || 10, 10)}</span>
      </div>
      <div className="table-scroll-wrapper">
        <table className="detail-table-modern">
          <thead><tr><th>Hạng</th><th>Tên</th><th>Doanh số</th><th>Hợp đồng/Lead</th></tr></thead>
          <tbody>
            {visibleRows.length === 0 ? <tr><td colSpan={4}>{EMPTY_TEXT}</td></tr> : visibleRows.map((row, index) => {
              const rankTone = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : '';
              const name = getName(row);
              return (
                <tr key={`${title}-${index}`}>
                  <td><span className={`rank-badge ${rankTone}`}>#{index + 1}</span></td>
                  <td className="detail-name-cell" title={name}><strong>{name}</strong><small>{getSubtitle(row)}</small></td>
                  <td className="numeric-cell">{formatCurrencyVnd(row.revenue)}</td>
                  <td className="numeric-cell">{formatNumber(row.contract_count ?? row.lead_count)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function BossDashboard() {
  const today = new Date().toISOString().slice(0, 10);
  const [preset, setPreset] = useState<DashboardPreset>('last_30_days');
  const [fromDate, setFromDate] = useState(today);
  const [toDate, setToDate] = useState(today);
  const [data, setData] = useState<BossDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError('');
    getBossDashboard({ preset, fromDate, toDate })
      .then((response) => { if (alive) setData(response.data); })
      .catch(() => { if (alive) setError('Không tải được dữ liệu dashboard. Vui lòng thử lại sau.'); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [preset, fromDate, toDate]);

  const kpiSections = useMemo(() => data ? [
    {
      title: 'Tổng quan vận hành',
      tone: 'ops',
      cards: [
        ['◌', 'Lead mới', formatNumber(data.summary.lead_new_count)],
        ['⇄', 'Lead chuyển khách hàng', formatNumber(data.summary.lead_converted_to_customer_count)],
        ['□', 'Booking', formatNumber(data.summary.booking_count)],
        ['●', 'Khách đã cọc', formatNumber(data.summary.deposit_count)],
        ['◇', 'Deal', formatNumber(data.summary.deal_count)],
        ['✓', 'Hợp đồng ký', formatNumber(data.summary.contract_signed_count)],
        ['↻', 'Khách trùng tiếp cận lại', formatNumber(data.summary.duplicate_reengagement_count)],
      ],
    },
    {
      title: 'Doanh số & dòng tiền',
      tone: 'cash',
      cards: [
        ['₫', 'Doanh số', formatCompactCurrencyVnd(data.summary.revenue_total), formatCurrencyTooltip(data.summary.revenue_total)],
        ['↓', 'Tiền khách đã thu', formatCompactCurrencyVnd(data.summary.customer_paid_total), formatCurrencyTooltip(data.summary.customer_paid_total)],
        ['!', 'Công nợ khách còn phải thu', formatCompactCurrencyVnd(data.summary.customer_outstanding_total), formatCurrencyTooltip(data.summary.customer_outstanding_total)],
        ['Ø', 'Giá trị HĐ trung bình', formatCompactCurrencyVnd(data.summary.avg_contract_value), formatCurrencyTooltip(data.summary.avg_contract_value)],
        ['↗', 'Lợi nhuận gộp tạm tính', formatCompactCurrencyVnd(data.summary.gross_profit_received_estimate), 'Tạm tính = HH công ty đã thu - HH sale đã chi - chi phí quảng cáo'],
      ],
    },
    {
      title: 'Hoa hồng & chi phí',
      tone: 'commission',
      cards: [
        ['◆', 'HH công ty phải thu', formatCompactCurrencyVnd(data.summary.company_commission_receivable_total), formatCurrencyTooltip(data.summary.company_commission_receivable_total)],
        ['◆', 'HH công ty đã thu', formatCompactCurrencyVnd(data.summary.company_commission_received_total), formatCurrencyTooltip(data.summary.company_commission_received_total)],
        ['◆', 'HH công ty còn phải thu', formatCompactCurrencyVnd(data.summary.company_commission_outstanding_total), formatCurrencyTooltip(data.summary.company_commission_outstanding_total)],
        ['◈', 'HH sale phải chi', formatCompactCurrencyVnd(data.summary.sales_commission_approved_total), formatCurrencyTooltip(data.summary.sales_commission_approved_total)],
        ['◈', 'HH sale đã chi', formatCompactCurrencyVnd(data.summary.sales_commission_paid_total), formatCurrencyTooltip(data.summary.sales_commission_paid_total)],
        ['◈', 'HH sale còn phải chi', formatCompactCurrencyVnd(data.summary.sales_commission_outstanding_total), formatCurrencyTooltip(data.summary.sales_commission_outstanding_total)],
        ['Ads', 'Chi phí quảng cáo', formatCompactCurrencyVnd(data.summary.ads_cost_total), formatCurrencyTooltip(data.summary.ads_cost_total)],
        ['ROI', 'ROI doanh thu/ads', formatPercent(data.summary.roi_ratio)],
        ['%', 'Tỷ lệ thu HH công ty', formatPercent(data.summary.company_commission_collection_rate)],
        ['%', 'Tỷ lệ chi HH sale', formatPercent(data.summary.sales_commission_payment_rate)],
      ],
    },
  ] : [], [data]);

  const leadRows: ChartRow[] = (data?.time_series.leads_by_day ?? []).map((row) => ({ label: row.date.slice(5), value: row.count }));
  const revenueRows: ChartRow[] = (data?.time_series.revenue_by_day ?? []).map((row) => ({ label: row.date.slice(5), value: row.amount }));
  const sourceRows: ChartRow[] = (data?.breakdowns.lead_by_source ?? []).map((row) => ({ label: safeLabel(row.source, 'Chưa xác định'), value: row.count }));
  const topSourceRows: ChartRow[] = (data?.rankings.top_sources ?? []).map((row) => ({ label: safeLabel(row.source, 'Chưa xác định'), value: row.lead_count ?? 0, meta: `${formatNumber(row.contract_count ?? 0)} hợp đồng` }));
  const sale7Rows: ChartRow[] = (data?.rankings.top_sales_7_days ?? []).map((row) => ({ label: safeLabel(row.sale_name, 'Chưa có sale'), value: row.revenue ?? 0, meta: `${safeLabel(row.team_name, 'Chưa có team')} · ${formatNumber(row.contract_count)} hợp đồng` }));
  const sale30Rows: ChartRow[] = (data?.rankings.top_sales_30_days ?? []).map((row) => ({ label: safeLabel(row.sale_name, 'Chưa có sale'), value: row.revenue ?? 0, meta: `${safeLabel(row.team_name, 'Chưa có team')} · ${formatNumber(row.contract_count)} hợp đồng` }));
  const team7Rows: ChartRow[] = (data?.rankings.top_teams_7_days ?? []).map((row) => ({ label: safeLabel(row.team_name, 'Chưa có team'), value: row.revenue ?? 0, meta: `${safeLabel(row.department_name, 'Chưa có phòng ban')} · ${formatNumber(row.contract_count)} hợp đồng` }));
  const team30Rows: ChartRow[] = (data?.rankings.top_teams_30_days ?? []).map((row) => ({ label: safeLabel(row.team_name, 'Chưa có team'), value: row.revenue ?? 0, meta: `${safeLabel(row.department_name, 'Chưa có phòng ban')} · ${formatNumber(row.contract_count)} hợp đồng` }));
  const projectRows: ChartRow[] = (data?.rankings.top_projects ?? []).map((row) => ({ label: safeLabel(row.project_name, 'Chưa có dự án'), value: row.revenue ?? 0, meta: `${formatNumber(row.contract_count)} hợp đồng` }));

  return (
    <div className="page dashboard-page boss-dashboard">
      <div className="dashboard-content">
        <header className="page-header dashboard-header">
          <div>
            <h1>Tổng quan giám đốc</h1>
            <p>Theo dõi toàn cảnh lead, giao dịch, doanh số, hoa hồng và hiệu quả nguồn.</p>
          </div>
        </header>

        <DashboardDateRangeFilter preset={preset} fromDate={fromDate} toDate={toDate} onChange={(next) => { setPreset(next.preset); setFromDate(next.fromDate); setToDate(next.toDate); }} />

        {loading && <div className="card dashboard-state-card">Đang tải dashboard...</div>}
        {error && <div className="card error-state dashboard-state-card">{error}</div>}

        {!loading && !error && data && (
          <>
            <p className="muted">Khoảng dữ liệu: {data.range.label}</p>
            {kpiSections.map((section) => (
              <section className="dashboard-kpi-section" key={section.title}>
                <h2>{section.title}</h2>
                <div className="summary-grid dashboard-section-grid">
                  {section.cards.map(([icon, label, value, subtitle]) => (
                    <article className={`card summary-card kpi-${section.tone}`} key={`${section.title}-${label}`}>
                      <div className="kpi-icon">{icon}</div>
                      <span>{label}</span>
                      <strong title={subtitle || value}>{value}</strong>
                      {subtitle ? <small>{subtitle}</small> : null}
                    </article>
                  ))}
                </div>
              </section>
            ))}

            <section className="dashboard-section-block"><h2>Xu hướng</h2><div className="dashboard-grid dashboard-section-grid trend-grid">
              <AreaTrendCard title="Doanh số theo ngày" rows={revenueRows} valueType="money" featured />
              <AreaTrendCard title="Lead mới theo ngày" rows={leadRows} />
            </div></section>

            <section className="dashboard-section-block"><h2>Funnel chuyển đổi</h2><div className="dashboard-funnel-grid dashboard-section-grid">
              <TrapezoidFunnel title="Funnel Lead → Customer" conversionLabel="Lead → Customer" conversionRate={data.funnel.lead_to_customer_rate} steps={[{ label: 'Lead', value: data.funnel.leads, color: '#2563eb' }, { label: 'Customer', value: data.funnel.customers, color: '#38bdf8' }]} />
              <TrapezoidFunnel title="Funnel Booking → Cọc → Deal → Hợp đồng" conversionLabel="Booking → Hợp đồng" conversionRate={data.funnel.booking_to_contract_rate} steps={[{ label: 'Booking', value: data.funnel.bookings, color: '#14b8a6' }, { label: 'Cọc', value: data.funnel.deposits, color: '#22c55e' }, { label: 'Deal', value: data.funnel.deals, color: '#f59e0b' }, { label: 'Hợp đồng', value: data.funnel.contracts, color: '#7c3aed' }]} />
            </div></section>

            <section className="dashboard-section-block"><h2>Nguồn & dự án</h2><div className="dashboard-grid dashboard-section-grid">
              <BarChartCard title="Top nguồn lead" rows={topSourceRows} horizontal />
              <BarChartCard title="Top dự án theo doanh số" rows={projectRows} valueType="money" horizontal />
            </div></section>

            <section className="dashboard-section-block"><h2>Xếp hạng hiệu suất</h2><div className="dashboard-grid dashboard-section-grid">
              <BarChartCard title="Top sale 7 ngày qua" rows={sale7Rows} valueType="money" horizontal />
              <BarChartCard title="Top sale 30 ngày qua" rows={sale30Rows} valueType="money" horizontal />
              <BarChartCard title="Top team 7 ngày qua" rows={team7Rows} valueType="money" horizontal />
              <BarChartCard title="Top team 30 ngày qua" rows={team30Rows} valueType="money" horizontal />
            </div></section>

            <section className="dashboard-section-block"><h2>Bảng chi tiết</h2><div className="ranking-grid dashboard-section-grid">
              <DetailTable title="Chi tiết top sale 7 ngày qua" rows={data.rankings.top_sales_7_days} type="sale" />
              <DetailTable title="Chi tiết top sale 30 ngày qua" rows={data.rankings.top_sales_30_days} type="sale" />
              <DetailTable title="Chi tiết top team 7 ngày qua" rows={data.rankings.top_teams_7_days} type="team" />
              <DetailTable title="Chi tiết top team 30 ngày qua" rows={data.rankings.top_teams_30_days} type="team" />
              <DetailTable title="Chi tiết top dự án" rows={data.rankings.top_projects} type="project" />
              <DetailTable title="Chi tiết top nguồn lead" rows={data.rankings.top_sources} type="source" />
            </div></section>
          </>
        )}
      </div>
    </div>
  );
}
