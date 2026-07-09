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
const formatPercent = (value: number | null | undefined) => (Number.isFinite(Number(value)) ? `${(Number(value) * 100).toFixed(1)}%` : '—');
const safeLabel = (value: unknown, fallback: string) => (typeof value === 'string' && value.trim() && value !== 'unknown' ? value : fallback);

type ChartRow = { label: string; value: number; meta?: string };

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
  const visibleRows = rows.filter((row) => row.value > 0 || rows.length <= 45).slice(-45);
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

function FunnelStep({ label, value, rate }: { label: string; value: number | null | undefined; rate?: string }) {
  return (
    <div className="dashboard-funnel-step">
      <span>{label}</span>
      <strong>{formatNumber(value)}</strong>
      {rate ? <em>{rate}</em> : null}
    </div>
  );
}

function FunnelCard({ title, children, note }: { title: string; children: ReactNode; note: string }) {
  return (
    <section className="card dashboard-funnel-card">
      <h3>{title}</h3>
      <div className="dashboard-funnel-flow">{children}</div>
      <p>{note}</p>
    </section>
  );
}

function DetailTable({ title, rows, type }: { title: string; rows: any[]; type: 'sale' | 'team' | 'project' | 'source' }) {
  return (
    <section className="card ranking-card">
      <h3>{title}</h3>
      <div className="table-scroll-wrapper">
        <table>
          <thead><tr><th>Tên</th><th>Doanh số</th><th>Hợp đồng/Lead</th></tr></thead>
          <tbody>
            {rows.length === 0 ? <tr><td colSpan={3}>{EMPTY_TEXT}</td></tr> : rows.slice(0, 10).map((row, index) => (
              <tr key={`${title}-${index}`}>
                <td>{safeLabel(row.sale_name || row.team_name || row.project_name || row.source, type === 'project' ? 'Chưa có dự án' : type === 'sale' ? 'Chưa có sale' : type === 'team' ? 'Chưa có team' : 'Chưa xác định')}{row.team_name && type === 'sale' ? <small>{safeLabel(row.team_name, 'Chưa có team')}</small> : null}</td>
                <td>{formatCurrencyVnd(row.revenue)}</td>
                <td>{formatNumber(row.contract_count ?? row.lead_count)}</td>
              </tr>
            ))}
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

  const cards = useMemo(() => data ? [
    ['Lead mới', formatNumber(data.summary.lead_new_count)],
    ['Lead chuyển khách hàng', formatNumber(data.summary.lead_converted_to_customer_count)],
    ['Booking', formatNumber(data.summary.booking_count)],
    ['Khách đã cọc', formatNumber(data.summary.deposit_count)],
    ['Deal', formatNumber(data.summary.deal_count)],
    ['Hợp đồng ký', formatNumber(data.summary.contract_signed_count)],
    ['Doanh số', formatCompactCurrencyVnd(data.summary.revenue_total)],
    ['Hoa hồng công ty', formatCompactCurrencyVnd(data.summary.company_commission_total)],
    ['Hoa hồng sale', formatCompactCurrencyVnd(data.summary.sales_commission_total)],
    ['Chi phí quảng cáo', formatCompactCurrencyVnd(data.summary.ads_cost_total)],
    ['ROI doanh thu/ads', formatPercent(data.summary.roi_ratio)],
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
            <section className="summary-grid dashboard-section-grid">
              {cards.map(([label, value]) => <article className="card summary-card" key={label}><span>{label}</span><strong>{value}</strong></article>)}
            </section>

            <section className="dashboard-grid dashboard-section-grid">
              <AreaTrendCard title="Lead mới theo ngày" rows={leadRows} />
              <AreaTrendCard title="Doanh số theo ngày" rows={revenueRows} valueType="money" featured />
              <BarChartCard title="Lead theo nguồn" rows={sourceRows} horizontal />
              <BarChartCard title="Top nguồn lead" rows={topSourceRows} horizontal />
            </section>

            <section className="dashboard-funnel-grid dashboard-section-grid">
              <FunnelCard title="Funnel Lead → Customer" note={`Tỷ lệ chuyển đổi Lead → Customer: ${formatPercent(data.funnel.lead_to_customer_rate)}`}>
                <FunnelStep label="Lead" value={data.funnel.leads} />
                <FunnelStep label="Customer" value={data.funnel.customers} rate={formatPercent(data.funnel.lead_to_customer_rate)} />
              </FunnelCard>
              <FunnelCard title="Funnel Booking → Cọc → Deal → Hợp đồng" note={`Tỷ lệ Booking → Hợp đồng: ${formatPercent(data.funnel.booking_to_contract_rate)}`}>
                <FunnelStep label="Booking" value={data.funnel.bookings} />
                <FunnelStep label="Cọc" value={data.funnel.deposits} />
                <FunnelStep label="Deal" value={data.funnel.deals} />
                <FunnelStep label="Hợp đồng" value={data.funnel.contracts} rate={formatPercent(data.funnel.booking_to_contract_rate)} />
              </FunnelCard>
            </section>

            <section className="dashboard-grid dashboard-section-grid">
              <BarChartCard title="Top sale 7 ngày qua" rows={sale7Rows} valueType="money" horizontal />
              <BarChartCard title="Top sale 30 ngày qua" rows={sale30Rows} valueType="money" horizontal />
              <BarChartCard title="Top team 7 ngày qua" rows={team7Rows} valueType="money" horizontal />
              <BarChartCard title="Top team 30 ngày qua" rows={team30Rows} valueType="money" horizontal />
              <BarChartCard title="Top dự án theo doanh số" rows={projectRows} valueType="money" horizontal />
            </section>

            <section className="ranking-grid dashboard-section-grid">
              <DetailTable title="Chi tiết top sale 7 ngày qua" rows={data.rankings.top_sales_7_days} type="sale" />
              <DetailTable title="Chi tiết top sale 30 ngày qua" rows={data.rankings.top_sales_30_days} type="sale" />
              <DetailTable title="Chi tiết top team 7 ngày qua" rows={data.rankings.top_teams_7_days} type="team" />
              <DetailTable title="Chi tiết top team 30 ngày qua" rows={data.rankings.top_teams_30_days} type="team" />
              <DetailTable title="Chi tiết top dự án" rows={data.rankings.top_projects} type="project" />
              <DetailTable title="Chi tiết top nguồn lead" rows={data.rankings.top_sources} type="source" />
            </section>
          </>
        )}
      </div>
    </div>
  );
}
