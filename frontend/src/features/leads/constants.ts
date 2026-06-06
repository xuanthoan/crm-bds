import type { LeadActivityType, LeadPriority, LeadStatus } from './types';

export const LEAD_VIEW_PERMISSIONS = ['leads.view.own', 'leads.view.team', 'leads.view.department', 'leads.view.all'];
export const LEAD_UPDATE_PERMISSIONS = ['leads.update.own', 'leads.update.team', 'leads.update.all'];
export const LEAD_ASSIGN_PERMISSIONS = ['leads.assign.team', 'leads.assign.all'];
export const SALES_ROLE_CODES = ['sale', 'leader', 'sales_manager', 'admin'];

export const STATUS_LABELS: Record<LeadStatus, string> = {
  new: 'Mới', contacted: 'Đã liên hệ', qualified: 'Tiềm năng', appointment: 'Hẹn gặp', site_visit: 'Đã xem nhà',
  negotiating: 'Đàm phán', deposit_ready: 'Sẵn sàng cọc', converted: 'Đã chuyển đổi', lost: 'Mất khách',
};
export const PRIORITY_LABELS: Record<LeadPriority, string> = { low: 'Thấp', medium: 'Trung bình', high: 'Cao', urgent: 'Khẩn cấp' };
export const ACTIVITY_LABELS: Record<LeadActivityType, string> = { note: 'Ghi chú', call: 'Cuộc gọi', zalo: 'Zalo', meeting: 'Cuộc hẹn', follow_up: 'Chăm sóc', status_change: 'Đổi trạng thái', assignment: 'Phân công' };
export const SOURCE_LABELS: Record<string, string> = {
  facebook_ads: 'Facebook Ads', google_ads: 'Google Ads', tiktok: 'TikTok', zalo: 'Zalo', referral: 'Giới thiệu',
  website: 'Website', hotline: 'Hotline', walk_in: 'Khách vãng lai', other: 'Khác',
};
