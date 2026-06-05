export const LEAD_STATUSES: Record<string, string> = { new: 'Mới', contacted: 'Đã liên hệ', qualified: 'Tiềm năng', appointment: 'Hẹn gặp', site_visit: 'Đã xem nhà', negotiating: 'Đàm phán', deposit_ready: 'Sẵn sàng cọc', converted: 'Đã chuyển đổi', lost: 'Mất khách' };
export const LEAD_PRIORITIES: Record<string, string> = { low: 'Thấp', medium: 'Trung bình', high: 'Cao', urgent: 'Khẩn cấp' };
export const LEAD_SOURCES = ['facebook_ads', 'google_ads', 'tiktok', 'zalo', 'referral', 'website', 'hotline', 'walk_in', 'other'];
export const ACTIVITY_TYPES: Record<string, string> = { note: 'Ghi chú', call: 'Cuộc gọi', zalo: 'Zalo', meeting: 'Cuộc hẹn', status_change: 'Đổi trạng thái', assignment: 'Phân công' };
export const VIEW_PERMISSIONS = ['leads.view.own', 'leads.view.team', 'leads.view.department', 'leads.view.all'];
export const UPDATE_PERMISSIONS = ['leads.update.own', 'leads.update.team', 'leads.update.all'];
export const ASSIGN_PERMISSIONS = ['leads.assign.team', 'leads.assign.all'];
