export const CONTRACT_VIEW_PERMISSIONS=['contracts.view.own','contracts.view.team','contracts.view.department','contracts.view.all'];
export const CONTRACT_STATUS_LABELS:Record<string,string>={draft:'Bản nháp',pending_signature:'Chờ ký',signed:'Đã ký',active:'Có hiệu lực',completed:'Hoàn tất',cancelled:'Đã hủy'};
export const CONTRACT_TYPE_LABELS:Record<string,string>={deposit_contract:'Hợp đồng đặt cọc',sale_contract:'Hợp đồng mua bán',transfer_contract:'Hợp đồng chuyển nhượng',other:'Khác'};
export const PAYMENT_STATUS_LABELS:Record<string,string>={planned:'Dự kiến',paid:'Đã thanh toán',overdue:'Quá hạn',cancelled:'Đã hủy'};
export const PAYMENT_METHOD_LABELS:Record<string,string>={cash:'Tiền mặt',bank_transfer:'Chuyển khoản',card:'Thẻ/POS',e_wallet:'Ví điện tử',other:'Khác'};
