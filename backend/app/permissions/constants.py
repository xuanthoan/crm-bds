DEFAULT_ROLES = [
    {"name": "Admin", "code": "admin"},
    {"name": "Director", "code": "director"},
    {"name": "Sales Manager", "code": "sales_manager"},
    {"name": "Leader", "code": "leader"},
    {"name": "Sale", "code": "sale"},
    {"name": "Marketing", "code": "marketing"},
    {"name": "Accountant", "code": "accountant"},
    {"name": "Inventory Manager", "code": "inventory_manager"},
    {"name": "Viewer", "code": "viewer"},
]

PERMISSION_CODES = [
    "customers.view.own", "customers.view.team", "customers.view.department", "customers.view.all", "customers.create", "customers.update.own", "customers.update.team", "customers.update.all", "customers.delete", "customers.transfer_owner", "customers.export",
    "leads.view.own", "leads.view.team", "leads.view.department", "leads.view.all", "leads.create", "leads.import", "leads.update.own", "leads.update.team", "leads.update.all", "leads.assign.team", "leads.assign.all", "leads.reclaim.team", "leads.reclaim.all", "leads.delete", "leads.export",
    "inventory.view.available", "inventory.view.all", "inventory.create_project", "inventory.create_property", "inventory.update_project", "inventory.update_property", "inventory.update_status", "inventory.import", "inventory.export", "inventory.delete",
    "deals.view.own", "deals.view.team", "deals.view.department", "deals.view.all", "deals.create", "deals.update.own", "deals.update.team", "deals.update.all", "deals.update_stage", "deals.approve", "deals.delete", "deals.export",
    "activities.view.own", "activities.view.team", "activities.view.all", "activities.create", "activities.update.own", "activities.update.team", "activities.delete",
    "marketing.view", "marketing.create_campaign", "marketing.update_campaign", "marketing.delete_campaign", "marketing.import_leads", "marketing.view_roi", "marketing.export",
    "payments.view", "payments.create", "payments.update", "payments.approve", "payments.export",
    "commissions.view.own", "commissions.view.team", "commissions.view.all", "commissions.update", "commissions.approve", "commissions.mark_paid", "commissions.export",
    "reports.view.own", "reports.view.team", "reports.view.department", "reports.view.all", "reports.view.ceo_dashboard", "reports.view.marketing_roi", "reports.view.finance", "reports.export",
    "settings.manage_master_data", "settings.manage_status", "settings.manage_workflow", "settings.manage_permissions", "settings.manage_integrations",
    "audit_logs.view", "audit_logs.export",
    "users.view", "users.create", "users.update", "users.deactivate", "roles.view", "roles.create", "roles.update", "roles.assign_permissions", "permissions.view",
]

ROLE_PERMISSION_CODES = {
    "admin": PERMISSION_CODES,
    "director": ["customers.view.all", "leads.view.all", "inventory.view.all", "deals.view.all", "activities.view.all", "marketing.view", "marketing.view_roi", "payments.view", "commissions.view.all", "reports.view.all", "reports.view.ceo_dashboard", "reports.view.marketing_roi", "reports.view.finance", "reports.export", "audit_logs.view"],
    "sales_manager": ["customers.view.department", "customers.create", "customers.update.all", "customers.transfer_owner", "leads.view.department", "leads.create", "leads.update.all", "leads.assign.all", "leads.reclaim.all", "inventory.view.all", "deals.view.department", "deals.create", "deals.update.all", "deals.update_stage", "deals.approve", "activities.view.all", "activities.create", "reports.view.department", "reports.export"],
    "leader": ["customers.view.team", "customers.create", "customers.update.team", "leads.view.team", "leads.create", "leads.update.team", "leads.assign.team", "leads.reclaim.team", "inventory.view.available", "deals.view.team", "deals.create", "deals.update.team", "deals.update_stage", "activities.view.team", "activities.create", "reports.view.team"],
    "sale": ["customers.view.own", "customers.create", "customers.update.own", "leads.view.own", "leads.create", "leads.update.own", "inventory.view.available", "deals.view.own", "deals.create", "deals.update.own", "deals.update_stage", "activities.view.own", "activities.create", "reports.view.own", "commissions.view.own"],
    "marketing": ["leads.view.all", "leads.create", "leads.import", "marketing.view", "marketing.create_campaign", "marketing.update_campaign", "marketing.import_leads", "marketing.view_roi", "marketing.export", "reports.view.marketing_roi", "reports.export"],
    "accountant": ["deals.view.all", "payments.view", "payments.create", "payments.update", "payments.approve", "payments.export", "commissions.view.all", "commissions.update", "commissions.approve", "commissions.mark_paid", "commissions.export", "reports.view.finance", "reports.export"],
    "inventory_manager": ["inventory.view.all", "inventory.create_project", "inventory.create_property", "inventory.update_project", "inventory.update_property", "inventory.update_status", "inventory.import", "inventory.export", "inventory.delete"],
    "viewer": ["reports.view.own"],
}


def permission_module(code: str) -> str:
    return code.split(".", maxsplit=1)[0]


def permission_name(code: str) -> str:
    return code.replace("_", " ").replace(".", " ").title()
