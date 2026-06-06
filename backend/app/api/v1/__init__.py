from fastapi import APIRouter

from app.api.v1 import auth, leads, organization, permissions, roles, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(permissions.router)

api_router.include_router(organization.departments_router)
api_router.include_router(organization.teams_router)
api_router.include_router(organization.organization_router)
api_router.include_router(leads.router)
