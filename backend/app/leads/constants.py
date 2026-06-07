LEAD_STATUS_LABELS = {
    "new": "Mới",
    "contacted": "Đã liên hệ",
    "qualified": "Tiềm năng",
    "appointment": "Hẹn gặp",
    "site_visit": "Đã xem nhà",
    "negotiating": "Đàm phán",
    "deposit_ready": "Sẵn sàng cọc",
    "converted": "Đã chuyển đổi",
    "lost": "Mất khách",
}
LEAD_STATUSES = set(LEAD_STATUS_LABELS)

LEAD_PRIORITY_LABELS = {
    "low": "Thấp",
    "medium": "Trung bình",
    "high": "Cao",
    "urgent": "Khẩn cấp",
}
LEAD_PRIORITIES = set(LEAD_PRIORITY_LABELS)

LEAD_ACTIVITY_TYPE_LABELS = {
    "note": "Ghi chú",
    "call": "Cuộc gọi",
    "zalo": "Zalo",
    "meeting": "Cuộc hẹn",
    "follow_up": "Chăm sóc",
    "status_change": "Đổi trạng thái",
    "assignment": "Phân công",
}
LEAD_ACTIVITY_TYPES = set(LEAD_ACTIVITY_TYPE_LABELS)
CONTACT_ACTIVITY_TYPES = {"call", "zalo", "meeting"}
CONTACT_STATUSES = {"contacted", "qualified", "appointment", "site_visit", "negotiating", "deposit_ready"}
SALES_ROLE_CODES = {"sale", "leader", "sales_manager", "admin"}
VIEW_PERMISSIONS = {"leads.view.own", "leads.view.team", "leads.view.department", "leads.view.all"}
UPDATE_PERMISSIONS = {"leads.update.own", "leads.update.team", "leads.update.all"}
ASSIGN_PERMISSIONS = {"leads.assign.team", "leads.assign.all"}
