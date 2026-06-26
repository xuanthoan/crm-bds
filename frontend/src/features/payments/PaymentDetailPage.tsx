import { useCallback, useEffect, useState } from 'react';
import { formatApiError } from '../../services/apiClient';
import { getPayment, cancelPaymentSchedule, cancelReceipt } from './api';
import { PaymentBadge } from './PaymentBadge';
import { InvoiceForm, PenaltyForm, ReceiptForm } from './PaymentForms';
import type { PaymentSchedule } from './types';

const money = (value: number) => new Intl.NumberFormat('vi-VN').format(value || 0) + 'đ';

export function PaymentDetailPage({ paymentId }: { paymentId: string }) {
  const [item, setItem] = useState<PaymentSchedule | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const load = useCallback(async () => {
    try {
      setItem((await getPayment(paymentId)).data);
      setErrors([]);
    } catch (error) {
      setErrors(formatApiError(error));
    }
  }, [paymentId]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!item) return <p>Đang tải thanh toán...</p>;

  const isFullyPaid = item.status === 'paid' || Number(item.remaining_amount || 0) <= 0;
  const canEditPayment = item.status !== 'cancelled' && !isFullyPaid;

  async function cancel() {
    try {
      await cancelPaymentSchedule(item.id);
      await load();
    } catch (error) {
      setErrors(formatApiError(error));
    }
  }

  async function cancelR(id: string) {
    try {
      await cancelReceipt(id, { note: 'Hủy từ giao diện' });
      await load();
    } catch (error) {
      setErrors(formatApiError(error));
    }
  }

  return (
    <section className="admin-page">
      <header className="detail-hero">
        <div><p>Thanh toán</p><h1>{item.payment_code}</h1><PaymentBadge status={item.status}/><p>Hợp đồng {item.contract.contract_code} · {item.customer?.full_name || 'Chưa cập nhật'}</p></div>
        <div><button disabled={item.status === 'paid' || item.status === 'cancelled'} onClick={cancel}>Hủy đợt thanh toán</button></div>
      </header>
      {errors.length > 0 && <div className="form-error">{errors.join('. ')}</div>}
      <section className="detail-card"><h2>Thông tin đợt thanh toán</h2><dl className="info-grid"><div><dt>Đợt</dt><dd>{item.sequence_no}. {item.title}</dd></div><div><dt>Hạn thanh toán</dt><dd>{new Date(item.due_date).toLocaleDateString('vi-VN')}</dd></div><div><dt>Phải thu</dt><dd>{money(item.expected_amount)}</dd></div><div><dt>Phí phạt</dt><dd>{money(item.penalty_amount)}</dd></div><div><dt>Đã thu</dt><dd>{money(item.paid_amount)}</dd></div><div><dt>Còn lại</dt><dd>{money(item.remaining_amount)}</dd></div><div><dt>Deal</dt><dd>{item.deal?.deal_code || 'Chưa cập nhật'}</dd></div><div><dt>BĐS</dt><dd>{item.property?.property_code || 'Chưa cập nhật'}</dd></div></dl></section>
      {isFullyPaid && <div className="form-warning">Đợt thanh toán này đã được thanh toán đủ.</div>}
      {canEditPayment && item.status !== 'paid' && item.contract.status !== 'completed' && <><ReceiptForm paymentId={item.id} onSaved={load}/><PenaltyForm paymentId={item.id} onSaved={load}/></>}{item.status === 'paid' && <div className="form-warning">Đợt thanh toán này đã được thanh toán đủ.</div>}
      {item.status !== 'cancelled' && <InvoiceForm paymentId={item.id} onSaved={load}/>}<section className="detail-card"><h2>Phiếu thu</h2><table><thead><tr><th>Mã phiếu</th><th>Số tiền</th><th>Ngày thanh toán</th><th>Phương thức</th><th>Mã chứng từ</th><th>Trạng thái</th><th>Hành động</th></tr></thead><tbody>{(item.receipts || []).map((receipt) => <tr key={receipt.id}><td><button className="link-button" onClick={() => navigateTo(`/receipts/${receipt.id}`)}>{receipt.receipt_code}</button></td><td>{money(receipt.amount)}</td><td>{receipt.payment_date ? new Date(receipt.payment_date).toLocaleDateString('vi-VN') : 'Chưa cập nhật'}</td><td>{receipt.payment_method_label || 'Chưa cập nhật'}</td><td>{receipt.reference_no}</td><td>{receipt.status_label}</td><td><button onClick={() => navigateTo(`/receipts/${receipt.id}`)}>Chi tiết</button>{receipt.status !== 'cancelled' && <button onClick={() => void cancelR(receipt.id)}>Hủy</button>}</td></tr>)}</tbody></table></section><section className="detail-card"><h2>Hóa đơn</h2><table><thead><tr><th>Mã hóa đơn</th><th>Số tiền</th><th>Ngày phát hành</th><th>Trạng thái</th><th>Hành động</th></tr></thead><tbody>{(item.invoices || []).map((invoice) => <tr key={invoice.id}><td><button className="link-button" onClick={() => navigateTo(`/invoices/${invoice.id}`)}>{invoice.invoice_code}</button></td><td>{money(invoice.amount)}</td><td>{invoice.issued_date ? new Date(invoice.issued_date).toLocaleDateString('vi-VN') : 'Chưa phát hành'}</td><td>{invoice.status_label}</td><td><button onClick={() => navigateTo(`/invoices/${invoice.id}`)}>Chi tiết</button></td></tr>)}</tbody></table></section>
    </section>
  );
}
