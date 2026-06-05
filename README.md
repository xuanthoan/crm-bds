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

## Sprint 4 Lead Management Foundation

Sprint 4 introduces the first CRM business module while preserving the Sprint 2 authentication/RBAC and Sprint 3 administration flows. Customer, property/inventory, deal, payment/commission, marketing campaign, report dashboard, workflow automation, and file attachment modules remain out of scope.

### New database tables

- `leads`: lead profile, interest, ownership, status, priority, contact scheduling, and soft-delete metadata.
- `lead_activities`: basic notes/contact/status/assignment timeline entries.

Migration: `backend/alembic/versions/20260605_0002_lead_management_foundation.py`.

### Lead API endpoints

- `GET /api/v1/leads`: scoped, paginated search/filter list.
- `GET /api/v1/leads/{lead_id}`: full lead detail and activity timeline.
- `POST /api/v1/leads`: create a lead.
- `PUT /api/v1/leads/{lead_id}`: update lead profile and interest fields.
- `POST /api/v1/leads/{lead_id}/status`: change status and record timeline/audit history.
- `POST /api/v1/leads/{lead_id}/assign`: assign an eligible active sale user.
- `POST /api/v1/leads/{lead_id}/activities`: add a note, call, Zalo, or meeting activity.
- `DELETE /api/v1/leads/{lead_id}`: soft delete a lead.

Important lead actions write `leads.create`, `leads.update`, `leads.status_change`, `leads.assign`, `leads.add_activity`, and `leads.delete` audit records.

### Frontend routes

```text
/leads
/leads/:id
```

The CRM sidebar and lead actions are permission-aware. Backend RBAC and object scope checks remain the source of truth.

### Lead CRUD manual checklist

1. Start the stack with `docker compose up --build` and login as admin.
2. Open `http://localhost:3000/leads`.
3. Select **Tạo lead**, enter a name and primary phone, then save.
4. Open the lead detail from its code or **Chi tiết** action.
5. Edit profile, interest, priority, follow-up, and note fields.
6. Change the status to **Đã liên hệ** and verify the timeline and last-contact time.
7. Assign the lead to an active user with role `sale`, `leader`, `sales_manager`, or `admin`.
8. Add a note/call/Zalo/meeting activity and verify the timeline.
9. As a user with `leads.delete`, delete the lead and verify it disappears from normal list/detail requests.

### Duplicate phone test

1. Create a lead with primary phone `0987654321`.
2. Create another lead using `0987654321` as either primary or secondary phone.
3. Verify the API returns `Số điện thoại đã tồn tại trong hệ thống` and the frontend displays that message.
4. Edit an existing lead and attempt to use another non-deleted lead's primary or secondary phone; verify the same rejection.

Phone values are normalized to digits before comparison. Duplicate checks cover both phone columns of all other non-deleted leads.

### Permission and scope tests

- Call `GET /api/v1/leads` without a Bearer token: expect `401 Unauthorized`.
- Login as a user without any `leads.view.*` permission and call/open `/api/v1/leads`: expect API `403 Forbidden` and a frontend forbidden page.
- Login as a Sale user with `leads.view.own`: verify only leads owned by or created by that user appear.
- Verify `leads.update.own` only updates own-scope leads.
- Verify `leads.assign.team` only assigns own-scope leads in Sprint 4.
- Verify `leads.assign.all` can assign any visible lead to an eligible active sales-role user.

### Known limitation

Team and department hierarchy is not implemented yet. In Sprint 4, `leads.view.team`, `leads.view.department`, `leads.update.team`, and `leads.assign.team` deliberately use the same owner/creator condition as own scope. The scope helpers are isolated so real team and department membership can replace this placeholder in a later sprint.
