export const PAYMENT_VIEW_PERMISSIONS = ['payments.view', 'payments.view_all'];
export const PAYMENT_STATUS_LABELS: Record<string, string> = { pending: 'Chưa thanh toán', partial: 'Thanh toán một phần', paid: 'Đã thanh toán', overdue: 'Quá hạn', cancelled: 'Đã hủy' };
export const PAYMENT_STATUS_TONES: Record<string, string> = { pending: 'neutral', partial: 'warning', paid: 'success', overdue: 'danger', cancelled: 'muted' };
export const PAYMENT_METHOD_LABELS: Record<string, string> = { cash: 'Tiền mặt', bank_transfer: 'Chuyển khoản', card: 'Thẻ', other: 'Khác' };
export const RECEIPT_STATUS_LABELS: Record<string, string> = { draft: 'Bản nháp', confirmed: 'Đã xác nhận', cancelled: 'Đã hủy' };
export const INVOICE_STATUS_LABELS: Record<string, string> = { draft: 'Bản nháp', issued: 'Đã phát hành', cancelled: 'Đã hủy' };
