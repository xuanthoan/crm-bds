import { useEffect, useState } from 'react';
import { formatApiError } from '../../services/apiClient';
import { CancelReasonModal } from '../payments/CancelReasonModal';
import { cancelReceipt, getReceipt } from '../payments/api';
import type { PaymentReceipt } from '../payments/types';

const money = (value: number) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(value);

export function ReceiptDetailPage({ receiptId }: { receiptId: string }) {
  const [item, setItem] = useState<PaymentReceipt | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const [showCancelModal, setShowCancelModal] = useState(false);

  async function load() {
    setItem((await getReceipt(receiptId)).data);
  }

  useEffect(() => { void load(); }, [receiptId]);

  async function confirmCancel(reason: string) {
    try {
      await cancelReceipt(receiptId, { cancel_reason: reason });
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
      <header className="page-header no-print"><div><h1>Phiếu thu {item.receipt_code}</h1><p>{item.status_label}</p></div><button onClick={() => window.print()}>In phiếu thu</button>{item.status !== 'cancelled' && <button className="secondary-button" onClick={() => setShowCancelModal(true)}>Hủy phiếu thu</button>}</header>
      {errors.length > 0 && <div className="form-error no-print">{errors.join('. ')}</div>}
      <section className="detail-card"><h2>Phiếu thu</h2><dl className="info-grid"><div><dt>Mã phiếu thu</dt><dd>{item.receipt_code}</dd></div><div><dt>Trạng thái</dt><dd>{item.status_label}</dd></div><div><dt>Số tiền</dt><dd>{money(item.amount)}</dd></div><div><dt>Ngày thanh toán</dt><dd>{item.payment_date ? new Date(item.payment_date).toLocaleDateString('vi-VN') : 'Chưa cập nhật'}</dd></div><div><dt>Phương thức</dt><dd>{item.payment_method_label || 'Chưa cập nhật'}</dd></div><div><dt>Mã giao dịch/chứng từ</dt><dd>{item.reference_no || '—'}</dd></div><div><dt>Hợp đồng</dt><dd>{item.contract?.contract_code || '—'}</dd></div><div><dt>Lịch thanh toán</dt><dd>{item.payment_schedule?.payment_code} · {item.payment_schedule?.title}</dd></div><div><dt>Khách hàng</dt><dd>{item.customer?.full_name || '—'}</dd></div><div><dt>BĐS</dt><dd>{item.property?.property_code || '—'} · {item.property?.title || ''}</dd></div><div><dt>Ghi chú</dt><dd>{item.note || '—'}</dd></div><div><dt>Lý do hủy</dt><dd>{item.cancel_reason || '—'}</dd></div></dl></section>
      {showCancelModal && <CancelReasonModal title="Hủy phiếu thu" warning="Hủy phiếu thu sẽ trừ lại số tiền đã thu khỏi lịch thanh toán. Thao tác này cần lý do để đối chiếu." label="Lý do hủy *" emptyMessage="Vui lòng nhập lý do hủy phiếu thu." confirmLabel="Xác nhận hủy" onClose={() => setShowCancelModal(false)} onConfirm={confirmCancel} />}
    </div>
  );
}
