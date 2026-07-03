import { useEffect, useState } from 'react';
import { navigateTo } from '../../routes/AppRoutes';
import { CONTRACT_STATUS_LABELS } from '../contracts/constants';
import { getCompanyCommission } from './api';
import type { CompanyCommission } from './types';
import { COMPANY_COMMISSION_EVENT_LABELS, COMPANY_COMMISSION_STATUS_LABELS, COMPANY_ROLE_LABELS, COMMISSION_PARTY_LABELS } from './constants';

const money = (v: unknown) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(Number(v || 0));
const label = (map: Record<string, string>, value?: string | null) => value ? (map[value] || value) : 'Chưa cập nhật';
const dateTime = (value?: string | null) => value ? new Date(value).toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit', year: 'numeric' }) : 'Chưa cập nhật';

export function CompanyCommissionDetailPage({ receivableId }: { receivableId: string }) {
  const [item, setItem] = useState<CompanyCommission | null>(null);
  useEffect(() => { getCompanyCommission(receivableId).then((r) => setItem(r.data)); }, [receivableId]);
  if (!item) return <p>Đang tải...</p>;
  return (
    <section className="page">
      <button className="secondary-button" onClick={() => navigateTo('/company-commissions')}>Quay lại danh sách</button>
      <h1>Hoa hồng công ty {item.receivable_code}</h1>
      <div className="detail-grid">
        <section className="detail-card"><h2>Thông tin hoa hồng công ty</h2><p>Mã: {item.receivable_code}</p><p>Trạng thái: {label(COMPANY_COMMISSION_STATUS_LABELS, item.status)}</p><p>Tỷ lệ: {item.commission_rate_percent}%</p><p>HH dự kiến: {money(item.expected_commission_amount)}</p><p>HH xác nhận: {money(item.confirmed_receivable_amount)}</p><p>Đã nhận: {money(item.received_amount)}</p><p>Còn phải thu: {money(item.remaining_amount)}</p><p>Ngày dự kiến nhận: {item.expected_receive_date || 'Chưa cập nhật'}</p><p>Ngày nhận đủ: {item.received_date || 'Chưa cập nhật'}</p></section>
        <section className="detail-card"><h2>Hợp đồng / giao dịch</h2><p>Mã hợp đồng: {item.contract_code}</p><p>Giá trị hợp đồng: {money(item.contract_value)}</p><p>Trạng thái hợp đồng: {label(CONTRACT_STATUS_LABELS, item.contract?.status)}</p><p>Khách hàng: {item.customer_name}</p><p>Sale: {item.sale_name}</p></section>
        <section className="detail-card"><h2>Bên bán / bên trả hoa hồng</h2><p>Vai trò công ty: {label(COMPANY_ROLE_LABELS, item.company_role)}</p><p>Bên bán thực tế: {label(COMMISSION_PARTY_LABELS, item.actual_seller_type)}</p><p>Tên bên bán: {item.actual_seller_name || 'Chưa cập nhật'}</p><p>Bên trả hoa hồng: {label(COMMISSION_PARTY_LABELS, item.commission_payer_type)}</p><p>Tên bên trả hoa hồng: {item.commission_payer_name || 'Chưa cập nhật'}</p><p>Mã hợp đồng/chính sách môi giới: {item.brokerage_contract_code || 'Chưa cập nhật'}</p><p>Ghi chú căn cứ hoa hồng: {item.brokerage_policy_note || 'Chưa cập nhật'}</p></section>
        <section className="detail-card"><h2>Lý do / ghi chú</h2><p>Lý do tạm giữ: {item.hold_reason || 'Không có'}</p><p>Lý do hủy: {item.cancel_reason || 'Không có'}</p><p>Ghi chú: {item.note || 'Không có'}</p></section>
        <section className="detail-card"><h2>Timeline thao tác</h2><ul className="commission-timeline-list">{(item.events || []).map((event) => <li key={event.id}><b>{dateTime(event.created_at)}</b> — {label(COMPANY_COMMISSION_EVENT_LABELS, event.event_type)}<br /><small>{event.reason || event.note || 'Không có ghi chú'}</small></li>)}</ul></section>
      </div>
    </section>
  );
}
