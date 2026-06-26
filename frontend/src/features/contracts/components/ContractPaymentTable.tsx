import type { ContractPayment } from '../types';

const money = (value: number) => `${new Intl.NumberFormat('vi-VN').format(value)} đ`;
const date = (value: string | null) => value ? new Date(value).toLocaleString('vi-VN') : 'Chưa cập nhật';

export function ContractPaymentTable({ items }: { items: ContractPayment[] }) {
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>Mã thanh toán</th><th>Số tiền</th><th>Loại</th><th>Trạng thái</th><th>Hạn thanh toán</th><th>Ngày thanh toán</th><th>Phương thức</th><th>Mã tham chiếu</th></tr></thead>
        <tbody>
          {items.map((payment) => (
            <tr key={payment.id}>
              <td>{payment.payment_code}</td>
              <td>{money(payment.amount)}</td>
              <td>{payment.payment_type_label}</td>
              <td>{payment.status_label}</td>
              <td>{date(payment.due_date)}</td>
              <td>{payment.status === 'paid' ? date(payment.paid_date) : 'Chưa thanh toán'}</td>
              <td>{payment.payment_method_label || 'Chưa cập nhật'}</td>
              <td>{payment.reference_number || 'Chưa cập nhật'}</td>
            </tr>
          ))}
          {!items.length && <tr><td colSpan={8} className="empty-cell">Không có khoản thanh toán.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
