import { useEffect, useState } from 'react';
import { HelpLabel } from '../../components/help/HelpTooltip';
import { navigateTo } from '../../routes/AppRoutes';
import { DashboardDateRangeFilter } from './DashboardDateRangeFilter';
import { getFinanceDashboard } from './api';
import type { DashboardPreset, FinanceDashboard as Data } from './types';

const money = (value:number|null|undefined) => `${new Intl.NumberFormat('vi-VN').format(Number(value || 0))} đ`;
const count = (value:number|null|undefined) => new Intl.NumberFormat('vi-VN').format(Number(value || 0));
const headers:Record<string,string> = { payment_code:'Mã thanh toán', receipt_code:'Mã phiếu thu', contract_code:'Mã hợp đồng', customer_name:'Khách hàng', due_date:'Hạn thanh toán', payment_date:'Ngày thu', expected_amount:'Số tiền phải thu', paid_amount:'Đã thu', remaining_amount:'Còn lại', amount:'Số tiền', creator_name:'Người tạo', status:'Trạng thái', contract_value:'Giá trị hợp đồng' };

function Table({ title, rows, detailsUrl }:{title:string;rows:any[];detailsUrl:(row:any)=>string}) {
  const keys = Object.keys(rows[0] || {}).filter(key => key !== 'id');
  return <section className="card dashboard-table-card"><h3>{title}</h3><div className="responsive-table-wrap"><table><thead><tr>{keys.map(key => <th key={key}>{headers[key] || key}</th>)}<th>Chi tiết</th></tr></thead><tbody>{rows.length ? rows.map((row, index) => <tr key={row.id || index}>{keys.map(key => <td key={key}>{typeof row[key] === 'number' ? count(row[key]) : String(row[key] || '—')}</td>)}<td><button onClick={() => navigateTo(detailsUrl(row))}>Chi tiết</button></td></tr>) : <tr><td colSpan={keys.length + 1}>Chưa có dữ liệu.</td></tr>}</tbody></table></div></section>;
}

export function FinanceDashboard() {
  const today = new Date().toISOString().slice(0, 10);
  const [preset, setPreset] = useState<DashboardPreset>('last_30_days');
  const [fromDate, setFromDate] = useState(today);
  const [toDate, setToDate] = useState(today);
  const [data, setData] = useState<Data|null>(null);
  useEffect(() => { void getFinanceDashboard({ preset, fromDate, toDate }).then(response => setData(response.data)); }, [preset, fromDate, toDate]);
  if (!data) return <section className="page-card">Đang tải tổng quan tài chính…</section>;

  const summary = data.summary;
  const period = `date_from=${data.range.from_date}&date_to=${data.range.to_date}`;
  const asOf = `as_of=${data.range.to_date}`;
  const cards:[string,string,string,(money?:boolean)=>string,boolean?][] = [
    ['Doanh số hợp đồng', 'contract_revenue', 'Tổng giá trị hợp đồng hợp lệ trong khoảng thời gian đã chọn.', () => `/contracts?status=signed,active,completed&${period}`, true],
    ['Tiền đã thu', 'collected_amount', 'Tổng tiền từ phiếu thu đã xác nhận trong khoảng thời gian đã chọn.', () => `/receipts?status=confirmed&${period}`, true],
    ['Còn phải thu', 'outstanding_amount', 'Tổng số tiền còn phải thu từ lịch thanh toán chưa thu đủ.', () => `/payments?outstanding=true&${asOf}`, true],
    ['Lịch thanh toán đến hạn', 'due_schedule_count', 'Lịch thanh toán đến hạn trong khoảng đã chọn và chưa thu đủ.', () => `/payments?due=true&${period}`],
    ['Thanh toán quá hạn', 'overdue_schedule_count', 'Lịch thanh toán đã quá hạn và còn số tiền chưa thu tại ngày chốt.', () => `/payments?overdue=true&${asOf}`],
    ['Phiếu thu chờ xác nhận', 'pending_receipt_count', 'Phiếu thu chưa được xác nhận được tạo trong khoảng thời gian đã chọn.', () => `/receipts?status=draft&${period}`],
    ['Hóa đơn nháp', 'draft_invoice_count', 'Hóa đơn đang ở trạng thái bản nháp được tạo trong khoảng thời gian đã chọn.', () => `/invoices?invoice_status=draft&${period}`],
    ['Hóa đơn đã phát hành', 'issued_invoice_count', 'Hóa đơn đã phát hành trong khoảng thời gian đã chọn.', () => `/invoices?invoice_status=issued&${period}`],
    ['Hoa hồng đã duyệt', 'commission_approved', 'Tổng hoa hồng được duyệt trong khoảng thời gian đã chọn.', () => `/commissions?status=approved&approved_from=${data.range.from_date}&approved_to=${data.range.to_date}`, true],
    ['Hoa hồng đã chi', 'commission_paid', 'Tổng hoa hồng đã chi trong khoảng thời gian đã chọn.', () => `/commissions?status=paid&paid_from=${data.range.from_date}&paid_to=${data.range.to_date}`, true],
    ['Hoa hồng còn phải chi', 'commission_outstanding', 'Hoa hồng đã duyệt trừ hoa hồng đã chi tại ngày chốt.', () => `/commissions?status=remaining&${asOf}`, true],
    ['Phiếu chi hoa hồng chờ xử lý', 'pending_commission_voucher_count', 'Phiếu chi hoa hồng chưa hoàn tất xử lý trong khoảng thời gian đã chọn.', () => `/commission-payment-vouchers?status=draft&${period}`]
  ];
  const alerts:Record<string,[string,string]> = {
    overdue: ['/payments?overdue=true', 'Lịch thanh toán đã quá hạn và còn số tiền chưa thu tại ngày chốt.'],
    pending_receipts: ['/receipts?status=draft', 'Phiếu thu chưa được xác nhận được tạo trong khoảng thời gian đã chọn.'],
    draft_invoices: ['/invoices?invoice_status=draft', 'Hóa đơn nháp chưa phát hành được tạo trong khoảng thời gian đã chọn.'],
    commission_due: ['/commissions?status=remaining', 'Hoa hồng đã duyệt nhưng chưa chi đủ tại ngày chốt.']
  };
  const Card = ({ card }: {card:typeof cards[number]}) => { const [label, key, help, url, isMoney] = card; return <button type="button" className="card summary-card kpi-cash dashboard-kpi-button" onClick={() => navigateTo(url(Boolean(isMoney)))}><span><HelpLabel content={help}>{label}</HelpLabel></span><strong>{isMoney ? money(summary[key]) : count(summary[key])}</strong></button>; };
  return <div className="dashboard-page"><header className="page-header dashboard-header"><div><p className="eyebrow">Dashboard · Finance</p><h1>Tổng quan tài chính</h1><p>Theo dõi doanh số, dòng tiền, công nợ, hóa đơn, phiếu thu và hoa hồng.</p></div></header><DashboardDateRangeFilter preset={preset} fromDate={fromDate} toDate={toDate} onChange={next => { setPreset(next.preset); setFromDate(next.fromDate); setToDate(next.toDate); }}/>
    <section className="dashboard-kpi-section"><h2>Tổng quan dòng tiền</h2><div className="summary-grid dashboard-section-grid">{cards.slice(0, 3).map(card => <Card key={card[1]} card={card}/>)}<button type="button" className="card summary-card kpi-cash dashboard-kpi-button" onClick={() => navigateTo(`/contracts?status=signed,active,completed&${period}`)}><span><HelpLabel content="Tiền đã thu chia cho doanh số hợp đồng.">Tỷ lệ thu tiền</HelpLabel></span><strong>{summary.collection_rate == null ? '—' : `${(Number(summary.collection_rate) * 100).toFixed(1)}%`}</strong></button></div></section>
    <section className="dashboard-kpi-section"><h2>Thanh toán, phiếu thu, hóa đơn & hoa hồng</h2><div className="summary-grid dashboard-section-grid">{cards.slice(3).map(card => <Card key={card[1]} card={card}/>)}</div></section>
    <section className="dashboard-kpi-section"><h2>Cảnh báo tài chính</h2><div className="summary-grid dashboard-section-grid">{data.alerts.map(alert => { const [path, help] = alerts[alert.key]; const balance = alert.key === 'overdue' || alert.key === 'commission_due'; return <button type="button" className="card summary-card kpi-ops dashboard-kpi-button" key={alert.key} onClick={() => navigateTo(`${path}&${balance ? asOf : period}`)}><span><HelpLabel content={help}>{alert.label}</HelpLabel></span><strong>{count(alert.count)}</strong></button>; })}</div></section>
    <div className="dashboard-section-grid"><Table title="Thanh toán quá hạn" rows={data.tables.overdue_payments} detailsUrl={row => `/payments/${row.id}`}/><Table title="Phiếu thu chờ xác nhận" rows={data.tables.pending_receipts} detailsUrl={row => `/receipts/${row.id}`}/><Table title="Hợp đồng còn phải thu" rows={data.tables.outstanding_contracts} detailsUrl={row => `/contracts/${row.id}`}/></div>
  </div>;
}
