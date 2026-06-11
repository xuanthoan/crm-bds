BOOKING_STATUS_LABELS = {
    "draft": "Mới tạo", "reserved": "Đã giữ chỗ", "deposited": "Đã cọc",
    "cancelled": "Đã hủy", "expired": "Hết hạn giữ chỗ", "refunded": "Đã hoàn tiền",
}
BOOKING_ACTIVITY_LABELS = {
    "created": "Tạo booking", "updated": "Cập nhật booking", "status_change": "Đổi trạng thái",
    "reserved": "Giữ chỗ", "deposited": "Đặt cọc", "cancelled": "Hủy booking",
    "expired": "Hết hạn giữ chỗ", "refunded": "Hoàn tiền", "deleted": "Xóa booking", "note": "Ghi chú",
}
ACTIVE_BOOKING_STATUSES = {"draft", "reserved", "deposited"}
FINAL_BOOKING_STATUSES = {"cancelled", "expired", "refunded"}
