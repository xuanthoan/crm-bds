import { useEffect, useState, type ReactNode } from 'react';
import { ActivityTimeline } from '../../components/audit/ActivityTimeline';
import { navigateTo } from '../../routes/AppRoutes';
import { can } from '../auth/authStore';
import { cancelVoucher, getVoucher, markPaidVoucher, PAYMENT_METHOD_LABELS, VOUCHER_STATUS_LABELS, type Voucher } from './api';

const money = (v: number) => new Intl.NumberFormat('vi-VN').format(v || 0);
const date = (value?: string | null) => value ? new Date(value).toLocaleDateString('vi-VN') : '—';
const dateTime = (value?: string | null) => value ? new Date(value).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—';
const isHttpUrl = (value?: string | null) => Boolean(value && /^https?:\/\//i.test(value));

function Field({ label, children }: { label: string; children: ReactNode }) {
  return <div><dt>{label}</dt><dd>{children}</dd></div>;
}

function AttachmentValue({ value }: { value?: string | null }) {
  if (!value) return <>—</>;
  if (isHttpUrl(value)) return <a href={value} target="_blank" rel="noreferrer">{value}</a>;
  return <>{value}</>;
}

export function CommissionPaymentVoucherDetailPage({ voucherId }: { voucherId: string }) {
  const [v, setV] = useState<Voucher | null>(null);
  const load = () => getVoucher(voucherId).then((r) => setV(r.data));

  useEffect(() => { void load(); }, [voucherId]);

  if (!v) return <p>Đang tải...</p>;

  const cancel = async () => {
    const reason = prompt('Vui lòng nhập lý do hủy phiếu chi.');
    if (reason) {
      await cancelVoucher(v.id, reason);
      await load();
    }
  };

  return (
    <section className="page-card detail-page">
      <header className="detail-header">
        <div>
          <button className="secondary-button" onClick={() => navigateTo('/commission-payment-vouchers')}>Quay lại danh sách</button>
          <h1>Chi tiết phiếu chi hoa hồng</h1>
          <p>Mã phiếu: <b>{v.code}</b></p>
        </div>
        <div className="header-actions">
          {v.status === 'draft' && can('commissions.payment_vouchers.mark_paid') && <button onClick={async () => { await markPaidVoucher(v.id, {}); await load(); }}>Xác nhận đã chi</button>}
          {v.status === 'draft' && can('commissions.payment_vouchers.cancel') && <button className="secondary-button" onClick={cancel}>Hủy</button>}
          {v.status === 'paid' && can('commissions.payment_vouchers.cancel_paid') && <button className="secondary-button" onClick={cancel}>Hủy phiếu đã chi</button>}
        </div>
      </header>

      <section className="detail-section">
        <h2>Thông tin phiếu chi</h2>
        <dl className="detail-grid">
          <Field label="Mã phiếu">{v.code}</Field>
          <Field label="Trạng thái">{VOUCHER_STATUS_LABELS[v.status]}</Field>
          <Field label="Số tiền">{money(v.amount)}</Field>
          <Field label="Ngày chi">{date(v.payment_date)}</Field>
          <Field label="Phương thức">{PAYMENT_METHOD_LABELS[v.payment_method]}</Field>
          <Field label="Mã giao dịch/chứng từ">{v.payment_reference || '—'}</Field>
          <Field label="Người tạo">{v.created_by_name || '—'}</Field>
          <Field label="Ngày tạo">{dateTime(v.created_at)}</Field>
          <Field label="Người xác nhận chi">{v.paid_by_name || '—'}</Field>
          <Field label="Thời gian xác nhận">{dateTime(v.paid_at)}</Field>
          <Field label="Lý do hủy">{v.cancel_reason || '—'}</Field>
          <Field label="Link chứng từ"><AttachmentValue value={v.attachment_url} /></Field>
        </dl>
      </section>

      <section className="detail-section">
        <h2>Đối tượng liên quan</h2>
        <dl className="detail-grid">
          <Field label="Sale nhận tiền">{v.sale_name || '—'}</Field>
          <Field label="Hợp đồng">{v.contract_code || '—'}</Field>
          <Field label="Hoa hồng sale liên quan">{v.sales_commission_code || '—'}</Field>
          <Field label="Ghi chú">{v.note || '—'}</Field>
        </dl>
      </section>
      <ActivityTimeline entityType="commission_payment_voucher" entityId={voucherId} title="Lịch sử thao tác hệ thống" />
    </section>
  );
}
