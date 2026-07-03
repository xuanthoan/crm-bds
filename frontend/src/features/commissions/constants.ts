export const COMMISSION_VIEW_PERMISSIONS = ['commissions.view', 'commissions.view.all', 'commissions.view.own', 'commissions.view.team'];
export const COMMISSION_STATUS_LABELS: Record<string, string> = { draft: 'Tạm tính', eligible: 'Đủ điều kiện', approved: 'Đã duyệt', partially_paid: 'Đã chi một phần', paid: 'Đã chi trả', on_hold: 'Tạm giữ', cancelled: 'Đã hủy' };
export const COMMISSION_PAYOUT_POLICY_LABELS: Record<string, string> = {
  received_amount_capacity: 'Chi theo hạn mức tiền hoa hồng công ty đã nhận',
  received_ratio: 'Chi theo tỷ lệ hoa hồng công ty đã thu',
};
