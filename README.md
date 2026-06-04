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

## Sprint 3 Admin Operations Test Checklist

Sprint 3 adds Admin UI and API operations for user, role, and permission management. No CRM business modules are implemented in this sprint.

### Admin routes

```text
/admin/users
/admin/roles
/admin/permissions
```

### User management

1. Login as `admin@example.com` / `Admin@123456`.
2. Open `http://localhost:3000/admin/users`.
3. Use **Tạo người dùng** to create a Sale user with role `sale`.
4. Edit the Sale user and update name, phone, status, or roles.
5. Use **Reset Password** to set a new password.
6. Use **Deactivate** and confirm `Bạn có chắc muốn khóa người dùng này không?`.

### Role management

1. Open `http://localhost:3000/admin/roles` as admin.
2. Use **Tạo vai trò** to create a custom role with lowercase snake_case code.
3. Use the grouped permission picker to assign permissions.
4. Edit the role and verify permission count updates.

### Permission management

1. Open `http://localhost:3000/admin/permissions` as admin.
2. Search by permission code/name.
3. Filter by module.
4. Verify permissions remain read-only and grouped by module.

### 401 / 403 verification

```bash
curl -i http://localhost:8000/api/v1/users
```

Expected: `401 Unauthorized` without a Bearer token.

Create or use a non-admin user that does not have `users.view`, login as that user, then open:

```text
http://localhost:3000/admin/users
```

Expected: the frontend shows `Bạn không có quyền truy cập trang này.` and direct API calls to `/api/v1/users` return `403 Forbidden`.
