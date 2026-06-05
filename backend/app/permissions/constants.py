DEFAULT_ROLES = [
    {"name": "Admin", "code": "admin", "description": "System administrator"},
    {"name": "Director", "code": "director", "description": "Executive/director access"},
    {"name": "Sales Manager", "code": "sales_manager", "description": "Sales department manager"},
    {"name": "Leader", "code": "leader", "description": "Sales team leader"},
    {"name": "Sale", "code": "sale", "description": "Salesperson"},
    {"name": "Marketing", "code": "marketing", "description": "Marketing team"},
    {"name": "Accountant", "code": "accountant", "description": "Finance/accounting team"},
    {"name": "Inventory Manager", "code": "inventory_manager", "description": "Inventory/project manager"},
    {"name": "Viewer", "code": "viewer", "description": "Read-only limited role"},
]

PERMISSION_CODES_BY_MODULE = {
    "customers": ["customers.view.own", "customers.view.team", "customers.view.department", "customers.view.all", "customers.create", "customers.update.own", "customers.update.team", "customers.update.all", "customers.delete", "customers.transfer_owner", "customers.export"],
    "leads": ["leads.view.own", "leads.view.team", "leads.view.department", "leads.view.all", "leads.create", "leads.import", "leads.update.own", "leads.update.team", "leads.update.all", "leads.assign.team", "leads.assign.all", "leads.reclaim.team", "leads.reclaim.all", "leads.delete", "leads.export"],
    "inventory": ["inventory.view.available", "inventory.view.all", "inventory.create_project", "inventory.create_property", "inventory.update_project", "inventory.update_property", "inventory.update_status", "inventory.import", "inventory.export", "inventory.delete"],
    "deals": ["deals.view.own", "deals.view.team", "deals.view.department", "deals.view.all", "deals.create", "deals.update.own", "deals.update.team", "deals.update.all", "deals.update_stage", "deals.approve", "deals.delete", "deals.export"],
    "activities": ["activities.view.own", "activities.view.team", "activities.view.all", "activities.create", "activities.update.own", "activities.update.team", "activities.delete"],
    "marketing": ["marketing.view", "marketing.create_campaign", "marketing.update_campaign", "marketing.delete_campaign", "marketing.import_leads", "marketing.view_roi", "marketing.export"],
    "payments": ["payments.view", "payments.create", "payments.update", "payments.approve", "payments.export"],
    "commissions": ["commissions.view.own", "commissions.view.team", "commissions.view.all", "commissions.update", "commissions.approve", "commissions.mark_paid", "commissions.export"],
    "reports": ["reports.view.own", "reports.view.team", "reports.view.department", "reports.view.all", "reports.view.ceo_dashboard", "reports.view.marketing_roi", "reports.view.finance", "reports.export"],
    "settings": ["settings.manage_master_data", "settings.manage_status", "settings.manage_workflow", "settings.manage_permissions", "settings.manage_integrations"],
    "audit_logs": ["audit_logs.view", "audit_logs.export"],
    "users": ["users.view", "users.create", "users.update", "users.deactivate"],
    "roles": ["roles.view", "roles.create", "roles.update", "roles.assign_permissions"],
    "permissions": ["permissions.view"],
}

ALL_PERMISSION_CODES = [code for codes in PERMISSION_CODES_BY_MODULE.values() for code in codes]

ROLE_PERMISSION_MAP = {
    "admin": ALL_PERMISSION_CODES,
    "director": ["customers.view.all", "leads.view.all", "inventory.view.all", "deals.view.all", "activities.view.all", "marketing.view", "marketing.view_roi", "payments.view", "commissions.view.all", "reports.view.all", "reports.view.ceo_dashboard", "reports.view.marketing_roi", "reports.view.finance", "reports.export", "audit_logs.view"],
    "sales_manager": ["customers.view.department", "customers.create", "customers.update.all", "customers.transfer_owner", "leads.view.department", "leads.create", "leads.update.all", "leads.assign.all", "leads.reclaim.all", "inventory.view.all", "deals.view.department", "deals.create", "deals.update.all", "deals.update_stage", "deals.approve", "activities.view.all", "activities.create", "reports.view.department", "reports.export"],
    "leader": ["customers.view.team", "customers.create", "customers.update.team", "leads.view.team", "leads.create", "leads.update.team", "leads.assign.team", "leads.reclaim.team", "inventory.view.available", "deals.view.team", "deals.create", "deals.update.team", "deals.update_stage", "activities.view.team", "activities.create", "reports.view.team"],
    "sale": ["customers.view.own", "customers.create", "customers.update.own", "leads.view.own", "leads.create", "leads.update.own", "inventory.view.available", "deals.view.own", "deals.create", "deals.update.own", "deals.update_stage", "activities.view.own", "activities.create", "reports.view.own", "commissions.view.own"],
    "marketing": ["leads.view.all", "leads.create", "leads.import", "marketing.view", "marketing.create_campaign", "marketing.update_campaign", "marketing.import_leads", "marketing.view_roi", "marketing.export", "reports.view.marketing_roi", "reports.export"],
    "accountant": ["deals.view.all", "payments.view", "payments.create", "payments.update", "payments.approve", "payments.export", "commissions.view.all", "commissions.update", "commissions.approve", "commissions.mark_paid", "commissions.export", "reports.view.finance", "reports.export"],
    "inventory_manager": ["inventory.view.all", "inventory.create_project", "inventory.create_property", "inventory.update_project", "inventory.update_property", "inventory.update_status", "inventory.import", "inventory.export", "inventory.delete"],
    "viewer": ["reports.view.own"],
}
