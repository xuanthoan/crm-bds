import type { Contract } from '../types';
const m = (v: number) => `${new Intl.NumberFormat('vi-VN').format(Math.max(v, 0))} đ`;
export function ContractSummaryCard({ contract: c, paymentState }: { contract: Contract; paymentState?: string }) {
  return <div className="summary-grid"><article><span>Giá trị hợp đồng</span><strong>{m(c.contract_value)}</strong></article><article><span>Tiền cọc</span><strong>{m(c.deposit_amount)}</strong></article><article><span>Đã thanh toán</span><strong>{m(c.total_paid)}</strong></article><article><span>Còn lại</span><strong>{m(c.remaining_amount)}</strong></article><article><span>Trạng thái thanh toán</span><strong>{paymentState || 'Chưa thanh toán'}</strong></article></div>;
}
