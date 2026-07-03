from fastapi import APIRouter

from app.api.v1 import auth, bookings, contracts, customers, dashboard, deals, lead_appointments, lead_tasks, leads, notifications, organization, permissions, projects, properties, roles, tasks, users, payments, reports, commissions, company_commissions, settings

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(permissions.router)

api_router.include_router(organization.departments_router)
api_router.include_router(organization.teams_router)
api_router.include_router(organization.organization_router)
api_router.include_router(leads.router)
api_router.include_router(customers.router)
api_router.include_router(deals.router)
api_router.include_router(bookings.router)
api_router.include_router(contracts.router)
api_router.include_router(projects.router)
api_router.include_router(properties.router)

api_router.include_router(lead_tasks.router)
api_router.include_router(tasks.router)
api_router.include_router(payments.router)
api_router.include_router(notifications.router)
api_router.include_router(lead_appointments.router)
api_router.include_router(dashboard.router)
api_router.include_router(reports.router)

api_router.include_router(commissions.router)
api_router.include_router(company_commissions.router)
api_router.include_router(settings.router)
