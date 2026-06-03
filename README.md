# CRM Bất Động Sản

Web-based Real Estate CRM foundation using FastAPI, PostgreSQL, Redis, React, TypeScript, Vite, and Docker Compose.

## Documentation

Primary product and architecture documents remain in `docs/`:

- `docs/PRD.md`
- `docs/DATABASE_SCHEMA.md`
- `docs/PERMISSION_SYSTEM.md`
- `docs/WORKFLOW_ENGINE.md`
- `docs/API_SPEC.md`
- `docs/UI_UX.md`
- `docs/UI_UX_WIREFRAME.md`
- `docs/SYSTEM_ARCHITECTURE.md`
- `docs/DEVELOPMENT_PLAN.md`

## How to run

```bash
docker compose up --build
```

The backend container runs Alembic migrations before starting FastAPI, then seeds default roles, permissions, role-permission mappings, and the default admin user during startup.

## Test URLs

```text
Frontend: http://localhost:3000
Backend: http://localhost:8000
Swagger: http://localhost:8000/docs
Health: http://localhost:8000/health
```

## Default Admin

```text
Email: admin@example.com
Password: Admin@123456
```

> Warning: Change default admin password before production.

## Sprint 2 Authentication & RBAC

Sprint 2 adds the authentication and RBAC foundation only. Customer, lead, inventory/property, deal, payment/commission, report, and workflow business modules are intentionally not implemented yet.

### New database tables

- `users`
- `roles`
- `permissions`
- `user_roles`
- `role_permissions`
- `refresh_tokens`
- `audit_logs`

### New API endpoints

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/users`
- `POST /api/v1/users`
- `GET /api/v1/users/{user_id}`
- `PUT /api/v1/users/{user_id}`
- `POST /api/v1/users/{user_id}/deactivate`
- `GET /api/v1/roles`
- `POST /api/v1/roles`
- `PUT /api/v1/roles/{role_id}`
- `POST /api/v1/roles/{role_id}/permissions`
- `GET /api/v1/permissions`

## How to run migrations

Inside the backend container or from the `backend/` directory with dependencies installed:

```bash
alembic upgrade head
```

## Auth Test

1. Open the frontend at `http://localhost:3000`.
2. Login with the default admin credentials.
3. Confirm the app redirects to `/dashboard`.
4. Open Swagger at `http://localhost:8000/docs`.
5. Use `POST /api/v1/auth/login` to get an access token.
6. Click **Authorize** in Swagger and enter `Bearer <access_token>`.
7. Test `GET /api/v1/auth/me` with the Bearer token.

### Test 401

Call a protected endpoint without a token:

```bash
curl -i http://localhost:8000/api/v1/auth/me
```

Expected result: `401 Unauthorized`.

### Test 403

Login as a non-admin user that lacks a specific permission, then call an endpoint protected by that permission. For example, create a `viewer` user as admin, login as that user, then call:

```bash
curl -i -H "Authorization: Bearer <viewer_access_token>" http://localhost:8000/api/v1/users
```

Expected result: `403 Forbidden` because `viewer` does not have `users.view`.
