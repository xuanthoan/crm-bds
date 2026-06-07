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

Sprint 4 originally shipped team and department scope as an own-scope placeholder. Sprint 5 supersedes that limitation with the organization membership hierarchy documented below.

## Sprint 5 - Organization Structure & Real Lead Scope

Sprint 5 introduces persistent organization hierarchy and replaces the Sprint 4 team/department placeholder with database-backed lead scope.

### New database tables

- `departments`: department code/name, manager, status, timestamps, and soft deletion.
- `teams`: department-owned sales teams with optional leader, status, timestamps, and soft deletion.
- `user_organization_memberships`: future-ready multiple department/team memberships with one primary membership supported by the current UI.

Run the new migration with:

```bash
cd backend
alembic upgrade head
```

The Sprint 5 migration is `20260606_0003_organization_structure.py` and follows the Sprint 4 lead migration.

### Organization and lead endpoints

- `GET|POST /api/v1/departments`
- `GET|PUT|DELETE /api/v1/departments/{department_id}`
- `GET|POST /api/v1/teams`
- `GET|PUT|DELETE /api/v1/teams/{team_id}`
- `GET|POST /api/v1/organization/memberships`
- `PUT|DELETE /api/v1/organization/memberships/{membership_id}`
- `GET /api/v1/users/{user_id}/organization`
- `GET /api/v1/organization/lead-scope-users`
- `GET /api/v1/leads/overdue`
- `POST /api/v1/leads/{lead_id}/transfer`
- `POST /api/v1/leads/{lead_id}/reclaim`

Department/team administration reuses `settings.manage_master_data`; membership reads and writes reuse `users.view` and `users.update`. No new permission codes are introduced. Organization actions and lead transfer/reclaim write audit records.

### Frontend routes

- `/admin/departments` - Quản lý phòng ban
- `/admin/teams` - Quản lý nhóm sale
- `/admin/memberships` - Phân bổ nhân sự
- `/leads/overdue` - Lead quá hạn chăm sóc

### Real lead scope

Scope priority is `all > department > team > own`:

- Own scope includes leads owned or created by the current user.
- Team scope includes the current user and members of active teams led by the current user.
- Department scope includes the current user and members of departments managed by the current user. A team leader with department permission uses the leader's primary department.
- All scope includes all non-deleted leads.
- Team assignment, transfer, and reclaim reject target owners outside the leader's accessible team.
- Overdue leads have `next_follow_up_at` in the past and exclude `converted` and `lost` statuses.

### Sprint 5 manual test checklist

#### Setup

1. Login as admin.
2. Open `/admin/departments` and create `kinh_doanh_1` / `Phòng Kinh Doanh 1`.
3. Open `/admin/teams` and create `team_a` / `Team A` in that department.
4. Create users Leader A, Sale A1, Sale A2, and Sale B1.
5. Set Leader A as the Team A leader.
6. Open `/admin/memberships`; assign Leader A, Sale A1, and Sale A2 to Team A. Assign Sale B1 to another team or leave that user without a team.

#### Scope test

1. Assign Lead 1 to Sale A1, Lead 2 to Sale A2, and Lead 3 to Sale B1.
2. Login as Sale A1: only Lead 1 should be visible (plus leads created by Sale A1).
3. Login as Leader A: Lead 1 and Lead 2 should be visible; Lead 3 should be forbidden.
4. Set a Sales Manager as department manager and verify all department leads are visible.
5. Login as Admin and verify all three leads are visible.

#### Assignment and transfer test

1. Login as Leader A and assign/transfer Lead 1 from Sale A1 to Sale A2: it should pass.
2. Try assigning/transferring Lead 1 to Sale B1: API should return `Người phụ trách không nằm trong phạm vi bạn được phân công`.
3. Login as Admin and assign Lead 1 to Sale B1: it should pass.
4. Verify the lead timeline contains `Chuyển lead` and the audit log contains `leads.transfer`.

#### Reclaim test

1. Login as Leader A and reclaim a lead in Team A: it should pass.
2. Reclaim a lead outside Team A: it should fail with 403.
3. Login as Admin and reclaim any lead: it should pass.
4. Verify the timeline contains `Thu hồi lead` and the audit log contains `leads.reclaim`.

#### Overdue test

1. Create/update a lead with `next_follow_up_at` in the past.
2. Open `/leads/overdue` and confirm it appears within the current permission scope.
3. Change the lead to `lost` or `converted` and confirm it disappears.

#### Regression test

- Login/logout and 401/403 behavior.
- `/admin/users`: create, edit, deactivate, and reset password.
- `/admin/roles` and `/admin/permissions`.
- `/leads`: create, edit, duplicate-phone validation, detail, status change, timeline, assignment, and soft delete.
- Open and close each modal by buttons, backdrop, Escape, and route change; confirm no stuck modal overlay.

### Known limitations

- Membership consistency between team and department is enforced in the service layer rather than by a cross-table database constraint.
- Sprint 5 provides manual reclaim only; no neglected-lead scheduler or workflow automation is included.
- The current UI manages one primary membership conveniently, while the schema supports multiple memberships for future use.
- Department deletion is blocked while active teams exist; teams must be deactivated first.
- No Customer, Deal, Inventory, Commission, Payment, Marketing, reporting dashboard, or workflow module is added in this sprint.

## Sprint 6 - Lead Care, Tasks, Appointments & Sales Dashboard

Sprint 6 adds the daily operating layer used by salespeople and team leaders while preserving the Sprint 4/5 lead and organization scope implementation.

### New database tables

- `lead_tasks`: soft-deleted lead care tasks/reminders with type, priority, due time, reminder time, assignee, completion/cancellation metadata, and result notes.
- `lead_appointments`: soft-deleted office meetings, site visits, calls, contract meetings, and other scheduled appointments with assignee and outcome metadata.
- Migration: `backend/alembic/versions/20260607_0004_lead_tasks_appointments.py` (`20260606_0003 -> 20260607_0004`).

### New API endpoints

Tasks:

- `GET/POST /api/v1/lead-tasks`
- `GET/PUT/DELETE /api/v1/lead-tasks/{task_id}`
- `POST /api/v1/lead-tasks/{task_id}/status`
- `GET /api/v1/lead-tasks/my/today`
- `GET /api/v1/lead-tasks/my/overdue`

Appointments:

- `GET/POST /api/v1/lead-appointments`
- `GET/PUT/DELETE /api/v1/lead-appointments/{appointment_id}`
- `POST /api/v1/lead-appointments/{appointment_id}/status`
- `GET /api/v1/lead-appointments/my/today`
- `GET /api/v1/lead-appointments/my/upcoming`

Dashboards:

- `GET /api/v1/dashboard/my-work` and alias `/api/v1/dashboard/sale`
- `GET /api/v1/dashboard/team-work` and alias `/api/v1/dashboard/leader`

### New frontend routes

- `/tasks`, `/tasks/today`, `/tasks/overdue`
- `/appointments`, `/appointments/today`
- `/dashboard/my-work`, `/dashboard/team-work`
- `/dashboard` now opens the authenticated user's work summary.
- Lead detail now includes recent task and appointment sections, create actions, and the existing activity timeline.

### Permissions added

- Tasks: `lead_tasks.view.{own,team,all}`, `lead_tasks.create`, `lead_tasks.update.{own,team,all}`, `lead_tasks.delete`, `lead_tasks.complete.{own,team,all}`.
- Appointments: `lead_appointments.view.{own,team,all}`, `lead_appointments.create`, `lead_appointments.update.{own,team,all}`, `lead_appointments.delete`, `lead_appointments.complete.{own,team,all}`.
- Dashboards: `dashboard.view.{own,team,all}`.
- Admin receives every new permission. Director receives all-scope read/update/complete and dashboard access. Sales Manager and Leader receive team task/appointment/dashboard access. Sale receives own task/appointment/dashboard access.

Task and appointment list/object access reuses Sprint 5 accessible-user and lead-scope rules. Direct access is also allowed for the assigned user. Changes write both audit log actions and Vietnamese lead activity timeline entries.

### Sprint 6 manual test checklist

#### Setup

1. Login admin.
2. Ensure there is Department `Kinh doanh Miền Bắc`, Team `Team A`, Sale7 assigned to Team A, and a lead owned by Sale7.
3. Login Sale7.

#### Task tests

1. Open a lead owned by Sale7.
2. Create `Gọi lại khách`, type Call, due today, priority High.
3. Confirm it appears in lead detail, `/tasks`, and `/tasks/today`.
4. Complete it with `Đã gọi, khách hẹn xem nhà cuối tuần`.
5. Confirm status/completed time, `Hoàn thành công việc` in the timeline, and updated `lead.last_contact_at`.

#### Overdue task test

1. Create a task due yesterday and confirm it appears in `/tasks/overdue`.
2. Complete it and confirm it disappears from the overdue list.

#### Appointment test

1. From lead detail create `Hẹn khách xem nhà`, type Site Visit, tomorrow at 10:00, location `Vinhomes Ocean Park`.
2. Confirm it appears in lead detail and `/appointments`.
3. Complete it and confirm `Hoàn thành lịch hẹn` appears in the timeline.
4. Also verify cancel, no-show, and reschedule (including old/new times in the timeline).

#### Dashboard test

1. Login Sale7 and confirm `/dashboard/my-work` shows today tasks, overdue tasks, today appointments, upcoming appointments, follow-up leads, and completed tasks.
2. Login Leader/Admin and confirm `/dashboard/team-work` shows Sale7 workload and per-user counts.

#### Scope test

1. Confirm Sale7 only lists own accessible tasks/appointments.
2. Open another user's object URL directly and expect 403/access denied.
3. Confirm Leader sees the accessible team and Admin sees all records.

#### Regression test

Verify login/logout, all `/admin/*` pages, lead list/create/duplicate-phone/detail/status/assignment/overdue, Sale own scope, and modal cleanup still work.

### Known limitations

- Reminder times are stored and displayed, but no background notification, email, SMS, or Zalo scheduler is included.
- Dashboard time boundaries currently use UTC; deployment-specific business timezone configuration is a future improvement.
- No calendar synchronization, recurring tasks, bulk operations, or complex charts are included.
- Customer, Deal, Inventory, Payment, Commission, and Marketing modules are intentionally outside Sprint 6.

### Suggested Sprint 7 scope

- Configurable business timezone and in-app notification center for due reminders.
- Recurring care plans/playbooks and task templates.
- Calendar/week view and optional external calendar integration design.
- Dashboard drill-down/export and workload balancing.
- Expanded automated integration tests for PostgreSQL migrations, scope rules, and timeline side effects.

## Sprint 7 - Customer 360 & Lead-to-Customer Conversion Foundation

Sprint 7 introduces the first production-oriented customer module. It preserves the original lead and all lead activities, tasks, appointments, ownership history, and organization scope while creating a long-term Customer 360 profile. Deal, inventory booking, payment, commission, contract, and invoice modules remain out of scope.

### New database tables and migration

Migration: `backend/alembic/versions/20260608_0005_customer_360_conversion.py` (`20260607_0004 -> 20260608_0005`).

- `customers`: customer identity, normalized contact data, source lead, real-estate interest, owner, follow-up dates, conversion metadata, notes, audit users, and soft delete.
- `customer_activities`: manual contacts plus creation, conversion, edit, status, and owner timeline events.
- `leads` gains `converted_at` and `converted_by_id`; its existing `converted_customer_id` is linked to `customers.id` by a PostgreSQL foreign key.

Customer phone numbers are normalized to digits. Service validation prevents any active customer phone from appearing in either phone column of another non-deleted customer and returns `Số điện thoại khách hàng đã tồn tại` with HTTP 409.

### Customer and conversion API endpoints

- `GET /api/v1/customers`: scoped, paginated search/filter list.
- `GET /api/v1/customers/assignees`: users available within the actor's assignment scope.
- `POST /api/v1/customers`: manually create a customer.
- `GET /api/v1/customers/{customer_id}`: Customer 360 detail, source lead history, tasks, and appointments.
- `PUT /api/v1/customers/{customer_id}`: update customer profile and interest data.
- `POST /api/v1/customers/{customer_id}/status`: change status and write timeline/audit records.
- `POST /api/v1/customers/{customer_id}/owner`: change owner within organization scope.
- `POST /api/v1/customers/{customer_id}/activities`: add note/call/Zalo/email/meeting activity.
- `DELETE /api/v1/customers/{customer_id}`: soft delete.
- `POST /api/v1/leads/{lead_id}/convert`: atomically create the customer, mark the lead converted, and write both timelines and audit events.

### Frontend routes

```text
/customers
/customers/:id
```

The customer list includes search, status/type/source/project filters, pagination, customer CRUD actions, status and owner actions. Customer detail includes contact, interest, ownership, dates, notes, activity form/timeline, and a concise source-lead history. Lead detail now displays **Chuyển thành khách hàng** when the actor has an applicable `leads.convert.*` permission, or links to the converted customer after conversion.

### Permissions added

Customer permissions:

```text
customers.view.own / team / department / all
customers.create
customers.update.own / team / department / all
customers.delete
customers.assign.own / team / department / all
customers.add_activity.own / team / department / all
```

Lead conversion permissions:

```text
leads.convert.own / team / department / all
```

Default mapping follows `all > department > team > own`: Director uses all scope, Sales Manager department scope, Leader team scope, Sale own scope, Viewer own read-only scope, and Admin receives every permission.

### Lead conversion flow

1. Confirm the actor can view and convert the lead in the applicable organization scope.
2. Reject an already converted lead and reject a phone already used by another non-deleted customer.
3. Copy the lead's identity, phones, channels, source, project/area, budget, bedroom/area need, owner, contact/follow-up dates, and notes.
4. Create `CUS-000001`-style customer code and source-lead relationship.
5. Set lead status to `converted`, `converted_customer_id`, `converted_at`, and `converted_by_id`.
6. Write customer conversion activity, lead conversion activity, `customers.create`, and `leads.convert` audit records in the same transaction.
7. Keep every existing lead activity, task, and appointment in place and expose them from Customer 360.

### Customer scope rules

- Own: customer owner is the current user.
- Team: owner belongs to a team led by the current user.
- Department: owner belongs to an accessible/managed department.
- All: all non-deleted customers.
- Assignment targets must be active users inside the actor's `customers.assign.*` scope.
- Backend scope checks remain authoritative; frontend permission checks only control visibility.

### Sprint 7 manual test checklist

#### Setup

1. Login as Admin.
2. Confirm Sprint 6 still works: leads, tasks, appointments, and dashboards.
3. Ensure Sale7 exists and has an own-scope lead.

#### Customer create test

1. Open `/customers`.
2. Create `Khách hàng A`, phone `0900000001`, type `individual`, status `active`.
3. Confirm the customer appears, then open detail.
4. Add call activity `Đã gọi xác nhận nhu cầu`.
5. Confirm the timeline entry and updated `last_contact_at`.

#### Duplicate phone test

1. Create a customer with phone `0900000002`.
2. Create another customer with the same phone in either phone field.
3. Confirm `Số điện thoại khách hàng đã tồn tại`.

#### Lead conversion test

1. Open a non-converted lead and select **Chuyển thành khách hàng**.
2. Confirm lead code, customer name, phone, source, project, budget, and owner preview.
3. Submit and confirm customer creation, converted lead status/link, source-lead customer link, both conversion timeline entries, and preserved lead tasks/appointments.
4. Convert the same lead again and confirm `Lead này đã được chuyển thành khách hàng`.

#### Customer scope test

1. Login as Sale7 and confirm only own customers are listed/openable.
2. Try another sale's customer and expect access denied.
3. Login as Leader and confirm team customers.
4. Login as Admin and confirm all customers.

#### Regression test

Verify login/logout, all Admin pages, organization pages, lead list/create/detail/status/assignment/reclaim/overdue, duplicate lead phone, tasks/today/overdue, appointments/today/validation, dashboards, own scope, and modal cleanup.

### Known limitations

- Sprint 7 implements `reject_existing`; automatic customer merge is intentionally deferred.
- Customer tasks and appointments are displayed through the immutable source lead. Dedicated customer-native task/appointment foreign keys are deferred.
- Customer code generation is application-managed. TODO: Replace with database sequence for high-concurrency production.
- Cross-column duplicate phone protection is service-level because a portable partial cross-column unique constraint is not available. All supported writes must use the service/API layer.
- This source snapshot has no configured `origin`, local `dev` branch, or tag refs. Sprint 7 was based on local commit `faebe3d`, whose history contains the required Sprint 6 and Sprint 5 merge commits.

### Suggested Sprint 8 scope

Implement the Deal foundation after Customer 360 stabilizes: customer-linked pipeline stages, project/property selection, negotiation history, scoped ownership, deal activity timeline, and basic forecast metrics. Keep deposits, payments, contracts, invoices, and commissions in later dedicated sprints unless separately approved.
