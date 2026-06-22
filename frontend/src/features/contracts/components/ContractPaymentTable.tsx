import type { ContractPayment } from '../types';

const money = (value: number) => `${new Intl.NumberFormat('vi-VN').format(value)} đ`;
const date = (value: string | null) => value ? new Date(value).toLocaleString('vi-VN') : 'Chưa cập nhật';

export function ContractPaymentTable({ items, onConfirm }: { items: ContractPayment[]; onConfirm: (payment: ContractPayment) => void }) {
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>Mã</th><th>Loại</th><th>Số tiền</th><th>Hạn thanh toán</th><th>Ngày thanh toán</th><th>Phương thức</th><th>Trạng thái</th><th /></tr></thead>
        <tbody>
          {items.map((payment) => (
            <tr key={payment.id}>
              <td>{payment.payment_code}</td>
              <td>{payment.payment_type_label}</td>
              <td>{money(payment.amount)}</td>
              <td>{date(payment.due_date)}</td>
              <td>{payment.status === 'paid' ? date(payment.paid_date) : 'Chưa thanh toán'}</td>
              <td>{payment.payment_method_label || 'Chưa cập nhật'}</td>
              <td>{payment.status_label}</td>
              <td>{payment.status === 'planned' && <button onClick={() => onConfirm(payment)}>Xác nhận thanh toán</button>}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
