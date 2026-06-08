from fastapi import APIRouter

from app.api.v1 import auth, customers, dashboard, deals, lead_appointments, lead_tasks, leads, organization, permissions, roles, users

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

api_router.include_router(lead_tasks.router)
api_router.include_router(lead_appointments.router)
api_router.include_router(dashboard.router)
