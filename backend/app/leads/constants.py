LEAD_STATUSES = {
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
LEAD_PRIORITIES = {"low": "Thấp", "medium": "Trung bình", "high": "Cao", "urgent": "Khẩn cấp"}
LEAD_ACTIVITY_TYPES = {"note", "call", "zalo", "meeting", "status_change", "assignment"}
CONTACT_STATUSES = {"contacted", "qualified", "appointment", "site_visit", "negotiating", "deposit_ready"}
SALES_ROLE_CODES = {"sale", "leader", "sales_manager", "admin"}
VIEW_PERMISSIONS = ("leads.view.all", "leads.view.department", "leads.view.team", "leads.view.own")
UPDATE_PERMISSIONS = ("leads.update.all", "leads.update.team", "leads.update.own")
ASSIGN_PERMISSIONS = ("leads.assign.all", "leads.assign.team")
