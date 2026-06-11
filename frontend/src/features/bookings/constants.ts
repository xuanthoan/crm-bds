export const BOOKING_STATUS_LABELS={draft:'Mới tạo',reserved:'Đã giữ chỗ',deposited:'Đã cọc',cancelled:'Đã hủy',expired:'Hết hạn giữ chỗ',refunded:'Đã hoàn tiền'} as const;
export const BOOKING_ACTIVITY_LABELS={created:'Tạo booking',updated:'Cập nhật booking',status_change:'Đổi trạng thái',reserved:'Giữ chỗ',deposited:'Đặt cọc',cancelled:'Hủy booking',expired:'Hết hạn giữ chỗ',refunded:'Hoàn tiền',deleted:'Xóa booking',note:'Ghi chú'} as const;
export const BOOKING_VIEW_PERMISSIONS=['bookings.view.own','bookings.view.team','bookings.view.department','bookings.view.all'];
export const ACTIVE_BOOKING_STATUSES=['draft','reserved','deposited'] as const;
export const FINAL_BOOKING_STATUSES=['cancelled','expired','refunded'] as const;

export const isFinalBookingStatus=(status:string):status is typeof FINAL_BOOKING_STATUSES[number]=>(FINAL_BOOKING_STATUSES as readonly string[]).includes(status);
