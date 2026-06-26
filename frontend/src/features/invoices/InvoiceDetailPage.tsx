import { useEffect, useState } from 'react';
import { formatApiError } from '../../services/apiClient';
import { CancelReasonModal } from '../payments/CancelReasonModal';
import { cancelInvoice, getInvoice, issueInvoice } from '../payments/api';
import type { PaymentInvoice } from '../payments/types';

const money = (value: number) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(value);

export function InvoiceDetailPage({ invoiceId }: { invoiceId: string }) {
  const [item, setItem] = useState<PaymentInvoice | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const [showCancelModal, setShowCancelModal] = useState(false);

  async function load() {
    setItem((await getInvoice(invoiceId)).data);
  }

  useEffect(() => { void load(); }, [invoiceId]);

  async function issue() {
    try {
      await issueInvoice(invoiceId, {});
      await load();
    } catch (error) {
      setErrors(formatApiError(error));
    }
  }

  async function confirmCancel(reason: string) {
    try {
      await cancelInvoice(invoiceId, { cancel_reason: reason });
      setShowCancelModal(false);
      await load();
    } catch (error) {
      setErrors(formatApiError(error));
      throw error;
    }
  }

  if (!item) return <div>Đang tải…</div>;

  return (
    <div className="admin-page print-page">
      <header className="page-header no-print"><div><h1>Hóa đơn {item.invoice_code}</h1><p>{item.status_label}</p></div>{item.status === 'draft' && <button onClick={issue}>Phát hành hóa đơn</button>}{item.status !== 'cancelled' && <button className="secondary-button" onClick={() => setShowCancelModal(true)}>Hủy hóa đơn</button>}<button onClick={() => window.print()}>In hóa đơn</button></header>
      {errors.length > 0 && <div className="form-error no-print">{errors.join('. ')}</div>}
      <section className="detail-card"><h2>Hóa đơn</h2><dl className="info-grid"><div><dt>Mã hóa đơn</dt><dd>{item.invoice_code}</dd></div><div><dt>Trạng thái</dt><dd>{item.status_label}</dd></div><div><dt>Số tiền</dt><dd>{money(item.amount)}</dd></div><div><dt>Ngày phát hành</dt><dd>{item.issued_date ? new Date(item.issued_date).toLocaleDateString('vi-VN') : 'Chưa phát hành'}</dd></div><div><dt>Hợp đồng</dt><dd>{item.contract?.contract_code || '—'}</dd></div><div><dt>Phiếu thu</dt><dd>{item.receipt?.receipt_code || '—'}</dd></div><div><dt>Lịch thanh toán</dt><dd>{item.payment_schedule?.payment_code} · {item.payment_schedule?.title}</dd></div><div><dt>Khách hàng</dt><dd>{item.customer?.full_name || '—'}</dd></div><div><dt>BĐS</dt><dd>{item.property?.property_code || '—'} · {item.property?.title || ''}</dd></div><div><dt>Mô tả</dt><dd>{item.description || '—'}</dd></div><div><dt>Ghi chú</dt><dd>{item.note || '—'}</dd></div><div><dt>Lý do hủy</dt><dd>{item.cancel_reason || '—'}</dd></div></dl></section>
      {showCancelModal && <CancelReasonModal title="Hủy hóa đơn" warning="Hủy hóa đơn sẽ chuyển hóa đơn sang trạng thái đã hủy. Thao tác này cần lý do để đối chiếu." label="Lý do hủy *" emptyMessage="Vui lòng nhập lý do hủy hóa đơn." confirmLabel="Xác nhận hủy" onClose={() => setShowCancelModal(false)} onConfirm={confirmCancel} />}
    </div>
  );
}
