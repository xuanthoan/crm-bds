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

## Sprint 8 — Deal Pipeline Foundation

Sprint 8 introduces the first production-ready **Giao dịch (Deal)** workflow after a lead becomes a qualified customer. It extends Customer 360 without changing lead-to-customer conversion, lead tasks, or appointments.

### Database migration

- Migration: `backend/alembic/versions/20260609_0006_deal_pipeline.py`
- Revision chain: `20260608_0005 -> 20260609_0006`
- New tables:
  - `deals`: customer-linked opportunity, pipeline/status/priority, property context, expected financial values, milestone dates, ownership, soft deletion, and audit timestamps.
  - `deal_activities`: immutable deal timeline entries with user, activity type, human-readable old/new values, optional JSON metadata, and timestamp.
- Deal codes use application-level `DL-000001` generation. A database sequence is recommended before high-concurrency production use.

### Deal pipeline

1. `new` — Mới tạo
2. `consulting` — Đang tư vấn
3. `viewing` — Đã xem nhà / xem dự án
4. `negotiating` — Đang đàm phán
5. `deposit` — Đặt cọc
6. `contract` — Ký hợp đồng
7. `completed` — Hoàn tất
8. `lost` — Thất bại / Hủy

Statuses are `open`, `won`, `lost`, and `cancelled`. Priorities are `low`, `medium`, `high`, and `urgent`.

### API endpoints

- `GET /api/v1/deals` — scoped, paginated filtering/search.
- `POST /api/v1/deals` — create a deal.
- `GET /api/v1/deals/assignees` — eligible assignees for the current assignment scope.
- `GET /api/v1/deals/{deal_id}` — detail, linked customer summary, source lead summary, and timeline.
- `PUT /api/v1/deals/{deal_id}` — update deal information.
- `POST /api/v1/deals/{deal_id}/stage` — change pipeline stage and milestone data.
- `POST /api/v1/deals/{deal_id}/status` — change open/won/lost/cancelled status.
- `POST /api/v1/deals/{deal_id}/assign` — assign an eligible owner.
- `POST /api/v1/deals/{deal_id}/activities` — add a timeline activity.
- `DELETE /api/v1/deals/{deal_id}` — soft delete.

### Frontend routes and Customer 360

- `/deals` — filters, paginated table, permission-aware actions, and create form.
- `/deals/:id` — deal summary, values, milestones, customer link, activity form, and timeline.
- Customer Detail includes a **Giao dịch** section and a **Tạo giao dịch** action. Customer, source lead, and customer owner are prefilled when available.

### Permissions and organization scope

Deal permissions use explicit `own`, `team`, `department`, and `all` scopes for `view`, `update`, `assign`, `stage`, `status`, `add_activity`, and `delete`, plus `deals.create`. Scope priority is `all > department > team > own`; own access includes deals owned or created by the current user.

- **Admin:** every deal permission.
- **Director:** all-scoped view/update/assign/stage/status/activity; no delete by the current director pattern.
- **Sales Manager:** create and department-scoped view/update/assign/stage/status/activity.
- **Leader:** create and team-scoped view/update/assign/stage/status/activity.
- **Sale:** create and own-scoped view/update/stage/status/activity; no assignment permission.
- **Viewer:** own-scoped read-only access.

### Manual test checklist

- [ ] Admin creates a deal from `/deals`.
- [ ] Admin creates a deal from Customer Detail.
- [ ] Sale creates a deal for an own customer.
- [ ] Sale cannot see another sale's deal.
- [ ] Leader sees team deals.
- [ ] Sales Manager sees department deals.
- [ ] Change stage `new -> consulting -> viewing -> negotiating`.
- [ ] Change stage to `deposit` and verify deposit fields and timeline.
- [ ] Change stage to `contract` and verify contract fields and timeline.
- [ ] Mark a deal won/completed and verify `closed_at`.
- [ ] Mark a deal lost without a reason and verify rejection.
- [ ] Add a deal activity.
- [ ] Assignment timeline shows user names rather than UUIDs.
- [ ] Customer Detail shows its related deals and detail links.
- [ ] Soft delete hides a deal from normal lists.

### Known limitations

- No payment schedule yet.
- No contract or invoice module yet.
- No commission calculation yet; `commission_expected` is informational only.
- No inventory/property catalog yet.
- No kanban drag-and-drop pipeline yet.
- Deal code generation is application-level and should use a database sequence later.
- Deal reporting dashboard is not included in Sprint 8.

### Suggested Sprint 9 scope

A future sprint can add a kanban pipeline, richer stage-transition policies, reminders tied to deal milestones, and focused deal dashboards. Payment schedules, formal contracts/invoices, inventory, and commission calculation should remain separate modules with their own approved scope.

## Sprint 9 — Customer Profile Advanced, Financial Profile & Scoring

Sprint 9 expands Customer 360 with optional personal, financial, demand, search-criteria, buying-timeline, related-person, and rule-based scoring data. Existing customer records remain valid and only name plus primary phone remain required.

### Database migration

- Migration: `backend/alembic/versions/20260610_0007_customer_profile_advanced.py` (`20260609_0006 -> 20260610_0007`).
- New customer fields: gender, birth date, province/district, occupation/company/job title, expected budget, available cash, loan need/ratio, preferred bank, monthly income, financial rating, buying purpose, interested property type, preferred direction/view, buying timeline, related-people note, score total/label/update time/note.
- New `customer_related_people` table stores simple related contacts with relationship, phone/email, notes, creator, timestamps, and soft deletion.
- Indexed filters include personal location, financial/demand/timeline values, score values, and owner combinations.

### Customer score formula

- Timeline: immediate 30, one month 25, three months 15, six months 8, over six months 3.
- Financial rating: A 30, B 20, C 10, D/unknown 0.
- Available cash versus expected budget: at least 30% = 20, 20% = 15, 10% = 8.
- Monthly income: at least VND 50m = 10, VND 30m = 6, VND 15m = 3.
- Engagement: contact in the last seven days = 10; a next follow-up exists = 5.
- Labels: hot >= 75, warm >= 45, cold >= 20, otherwise unqualified. Scores recalculate on customer create/update and contact activities.

### API and UI

`GET /api/v1/customers` supports gender, province, district, financial rating, buying purpose, interested property type, buying timeline, score label, and score range filters. Customer detail returns advanced fields, score, and related people. Related contacts use nested GET/POST/PUT/DELETE endpoints under `/api/v1/customers/{customer_id}/related-people` with existing customer view/update scope.

The customer form now uses five collapsible sections. Customer Detail adds personal, financial, demand/search criteria, related people, and score sections while retaining deals, activities, and source-lead history. Empty detail values display **Chưa cập nhật**. The customer list adds qualification filters and compact score/financial/timeline information.

### Manual test checklist

- [ ] Create a customer with only name and phone.
- [ ] Create a customer with a full advanced profile.
- [ ] Save empty optional fields.
- [ ] Reject invalid phone and email.
- [ ] Reject negative financial values and loan ratio above 100.
- [ ] Validate buying timeline and financial rating.
- [ ] Verify hot and low-quality score calculations.
- [ ] Filter customers by score label and financial rating.
- [ ] Verify advanced profile and **Chưa cập nhật** placeholders in Customer Detail.
- [ ] Add, update through API, and delete a related person.
- [ ] Verify existing Customer CRUD, Lead → Customer conversion, Deal list/customer deals, and Sale scope.

### Known limitations

- Scoring is rule-based, not AI-based; there is no external credit scoring, bank integration, or advanced reporting dashboard.
- Province and district are free text because no location master-data table exists yet.
- Related people are simple contacts and are not duplicate-checked against customers.

### Suggested Sprint 10 scope

Add location master data, configurable score rules/history, related-person duplicate matching, qualification reports, and customer segmentation. Inventory, contracts, payments, invoices, commissions, and marketing should remain separate approved modules.

## Sprint 10 — Property Inventory Foundation

Sprint 10 introduces the production foundation for the real-estate inventory domain without changing Customer Profile/Scoring, Lead → Customer conversion, or Deal Pipeline behavior.

### Database

Migration: `backend/alembic/versions/20260611_0008_property_inventory.py` (`20260610_0007` → `20260611_0008`). It creates `projects`, `property_units`, `property_price_history`, and `property_status_history`, including soft-delete/audit actor columns and inventory filter indexes.

Project statuses: `planning`, `opening`, `selling`, `handover`, `completed`, `paused`, `cancelled`.

Inventory statuses: `available`, `reserved`, `negotiating`, `deposited`, `sold`, `locked`, `unavailable`.

### API and frontend

* Projects: `GET/POST /api/v1/projects`, `GET/PUT/DELETE /api/v1/projects/{project_id}`.
* Properties: `GET/POST /api/v1/properties`, `GET/PUT/DELETE /api/v1/properties/{property_id}`, `POST /status`, and `POST /prices`.
* Frontend routes: `/projects`, `/projects/:id`, `/properties`, `/properties/:id`.
* Project/property create, update, filtering, detail views, soft deletion, status history, price history, legal/owner/commission data, and text/link media references are included.

### Permission mapping

* Admin and Inventory Manager: all 29 Sprint 10 inventory permissions.
* Director: project/property all-scope view/update/status/price management; no default delete.
* Sales Manager: project management plus department-scoped property view/update/status/price.
* Leader: project view plus team-scoped property view/update/status/price and create.
* Sale: project view plus own-created property view/update/status, price view, and create.
* Viewer: project view and own-created property/price read only.

Property scope priority is `all > department > team > own`; Sprint 10 own scope uses `created_by_id`. Team and department scopes reuse the existing organization access helper.

### Manual test checklist

1. Create a project with minimal fields.
2. Create a project with full fields.
3. Edit a project.
4. Soft-delete a project.
5. Create a property without a project.
6. Create a property under a project.
7. Create a property with full owner, price, legal, commission, and media information.
8. Verify an invalid price is rejected.
9. Verify an invalid area is rejected.
10. Verify an invalid owner phone is rejected.
11. Verify an invalid owner email is rejected.
12. Change property status and verify status history.
13. Update prices and verify only changed fields create price-history rows.
14. Soft-delete a property and verify it is hidden from the list.
15. Verify project detail shows related properties.
16. Verify property detail shows the project summary.
17. Verify Sale sees own-created properties.
18. Verify Leader sees team properties.
19. Verify Sales Manager sees department properties.
20. Verify Admin sees all properties.
21. Regression-check Sprint 9 Customer Profile and Scoring.
22. Regression-check Sprint 8 Deal Pipeline.

### Known limitations and suggested Sprint 11 scope

* No file upload or MinIO/S3 integration; media is stored as text/links.
* No matching engine or inventory-to-customer recommendations.
* No strict Deal ↔ Property foreign-key linkage; this is recommended for Sprint 11.
* No inventory analytics dashboard or property duplicate detection.
* Province and district remain free text.
* Project/property codes are generated at application level and include TODOs to move to database sequences for high concurrency.
* Suggested Sprint 11: strict deal-property linkage, availability-aware deal transitions, duplicate controls, and the first customer-property matching workflow.

## Sprint 11 — Booking / Giữ chỗ / Đặt cọc Foundation

Sprint 11 adds the first production-oriented reservation layer between Customer and Property Inventory without changing Customer Scoring, Lead → Customer conversion, Deal Pipeline, or Sprint 10 inventory behavior.

### Migration and tables

- Migration: `backend/alembic/versions/20260612_0009_booking_reservation.py` (`20260611_0008` → `20260612_0009`).
- New table `bookings` stores the customer, property, optional source lead/deal, assignee, reservation/deposit/refund amounts and dates, lifecycle reasons, audit users, and soft-delete timestamps.
- New table `booking_activities` stores the booking timeline and actor.
- A PostgreSQL partial unique index prevents more than one non-deleted `draft`, `reserved`, or `deposited` booking for the same property. The service also validates this rule while holding a row lock on creation.

### Booking lifecycle

| Code | Vietnamese label |
| --- | --- |
| `draft` | Mới tạo |
| `reserved` | Đã giữ chỗ |
| `deposited` | Đã cọc |
| `cancelled` | Đã hủy |
| `expired` | Hết hạn giữ chỗ |
| `refunded` | Đã hoàn tiền |

Activity types are `created`, `updated`, `status_change`, `reserved`, `deposited`, `cancelled`, `expired`, `refunded`, `deleted`, and `note`.

### API routes

- `GET /api/v1/bookings` supports pagination, search, customer/property/assignee/status, created-date, and expiry-date filters.
- `POST /api/v1/bookings`
- `GET /api/v1/bookings/assignees`
- `GET /api/v1/bookings/{booking_id}`
- `PUT /api/v1/bookings/{booking_id}`
- `POST /api/v1/bookings/{booking_id}/status`
- `POST /api/v1/bookings/{booking_id}/activities`
- `DELETE /api/v1/bookings/{booking_id}`

### Frontend routes and integrations

- `/bookings` — booking list, filters, create/edit/status/delete actions.
- `/bookings/:id` — booking financial information, dates, reasons, links, and timeline.
- Customer Detail includes **Booking của khách hàng**.
- Property Detail includes **Booking liên quan**.
- Sidebar and route guards require any `bookings.view.*` permission.

### Permission mapping

- **Admin:** every booking permission.
- **Director:** view/update/status/refund all; no delete by default.
- **Sales Manager:** create and department view/update/status/refund.
- **Leader:** create and team view/update/status/refund.
- **Sale:** create and own view/update/status; no refund/delete.
- **Viewer:** own view only.
- Scope priority is `all > department > team > own`; access matches bookings assigned to or created by accessible users.

### Property status integration

- `draft` may be created without money; any submitted reservation or deposit amount must be greater than zero, and the draft remains active for duplicate-booking protection.
- `reserved` requires a positive reservation amount, changes the property to `reserved`, and records property status history.
- `deposited` requires a deposit amount, defaults the deposit date to now, changes the property to `deposited`, and records history.
- `cancelled` requires a reason and releases a non-sold property to `available`.
- `expired` releases a non-sold property to `available`.
- `refunded` requires a positive refund amount and reason, and releases the property unless it is `sold`, `locked`, or `unavailable`.
- A property in `reserved`, `deposited`, `sold`, `locked`, or `unavailable` cannot receive a new booking. Only `available` and `negotiating` properties can be booked.
- Sold properties are never automatically returned to available.
- Soft delete is limited to final statuses `cancelled`, `expired`, and `refunded`; active draft/reserved/deposited bookings must transition to a final status first.

### Manual test checklist

1. Create a booking with an available property and confirm code `BK-000001`.
2. Try missing customer and missing property payloads.
3. Try a second active booking for the same property.
4. Move the booking to reserved and verify property status/history.
5. Move it to deposited; verify deposit amount is required and property becomes deposited.
6. Cancel it; verify cancellation reason and property release.
7. Refund it; verify refund amount/reason and property release safety rules.
8. Verify booking timeline and audit logs.
9. Verify related bookings on Property Detail and Customer Detail.
10. Reject deletion of draft/reserved/deposited bookings and allow soft deletion only after cancelled/expired/refunded.
11. Test Sale own, Leader team, Sales Manager department, and Admin all scope.
12. Regression-check Sprint 10 Project/Property, Sprint 9 Customer, and Sprint 8 Deal flows.

### Known limitations

- No contract generation, payment schedule, invoice, commission payout, reporting dashboard, or deposit-proof file upload.
- No strict Deal ↔ Booking linkage yet; `source_deal_id` is informational and no `booking_id` is added to deals.
- No automatic expiry background job; expiry is changed manually through booking status.
- Booking code generation is application-level and has a TODO to move to a database sequence for high-concurrency production.

### Suggested Sprint 12

Add controlled Deal ↔ Booking ↔ Property linkage, contract preparation, transition validation, and a database-backed booking code sequence before contract/payment modules are introduced.
