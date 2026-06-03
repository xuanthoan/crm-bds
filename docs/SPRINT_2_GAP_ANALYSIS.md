# Sprint 2 Gap Analysis

## Review context

This review was performed from the available repository state on the `dev`-based working branch. The remote `origin/dev` branch could not be pulled because no `origin` remote is configured in this checkout.

The requested canonical source documents are still absent from the repository:

- `docs/PRD.md`
- `docs/DATABASE_SCHEMA.md`
- `docs/PERMISSION_SYSTEM.md`
- `docs/WORKFLOW_ENGINE.md`
- `docs/API_SPEC.md`
- `docs/UI_UX.md`
- `docs/UI_UX_WIREFRAME.md`
- `docs/SYSTEM_ARCHITECTURE.md`
- `docs/DEVELOPMENT_PLAN.md`

Because those files are missing, this gap analysis validates Sprint 2 against the explicit Sprint 2 requirements provided in the task and against the current implementation present in the repository.

## Implemented correctly

### Backend foundation

- FastAPI application still exposes the Sprint 1 `/health` endpoint.
- API v1 routing is mounted under `/api/v1`.
- SQLAlchemy database configuration and session dependency exist.
- Alembic configuration and a migration exist for Sprint 2 auth/RBAC tables.
- Backend container runs `alembic upgrade head` before starting Uvicorn.

### Database tables

The current migration creates the Sprint 2 tables required by the task:

- `users`
- `roles`
- `permissions`
- `user_roles`
- `role_permissions`
- `refresh_tokens`
- `audit_logs`

### Seeding

- Default role codes are present.
- Required permission codes are present.
- Role-permission mappings are present for Admin, Director, Sales Manager, Leader, Sale, Marketing, Accountant, Inventory Manager, and Viewer.
- Default admin creation is duplicate-safe by email.
- Default admin password is hashed.
- Default admin is active, superuser, and assigned the Admin role.

### Authentication and RBAC

- Login endpoint exists and returns access token, refresh token, token type, and current user data.
- Refresh endpoint validates refresh token existence, revocation status, and expiry.
- Logout endpoint revokes the provided refresh token and writes an audit log.
- Current user endpoint returns user identity, status, roles, permissions, and `is_superuser`.
- Reusable auth/RBAC dependencies exist.
- Superuser authorization bypass exists.
- Missing token and invalid token paths return 401.
- Missing permission path returns 403.
- Future data-scope and object-access stubs exist.

### Frontend foundation

- Login page exists and calls `POST /api/v1/auth/login`.
- Access token, refresh token, and current user are persisted in local storage.
- Protected routes exist for `/dashboard`, `/customers`, `/properties`, `/deals`, and `/reports`.
- Authenticated layout has sidebar, header, and main content regions.
- Sidebar permission helper exists.
- Business module pages remain placeholders only.

### Docker and README

- Docker Compose includes backend, frontend, PostgreSQL, and Redis services.
- Required auth environment variables are present.
- README includes run instructions, test URLs, default admin, auth test instructions, and 401/403 test guidance.

## Missing

- The canonical planning documents required for full product consistency review are missing from the repository.
- Runtime validation with `docker compose up --build` could not be completed in this environment because Docker is not installed.
- Dependency installation validation could not be completed in this environment because package registry access is blocked by proxy/registry 403 responses.

## Implemented incorrectly or needing correction

### User status validation

The previous implementation accepted arbitrary `status` strings in user create/update payloads. Sprint 2 defines the allowed statuses as:

- `active`
- `inactive`
- `suspended`
- `resigned`

This has been corrected by constraining API schemas to the allowed status values.

### Frontend auth reactivity

The previous frontend read authentication state directly from the store without subscribing React components to store updates. This worked for simple navigation after login/logout, but it could leave protected route/layout rendering stale if auth state changed outside the current render cycle.

This has been corrected by adding a `useAuth()` hook backed by `useSyncExternalStore` and updating auth-sensitive components to use it.

## Remaining limitations

- Full end-to-end verification requires an environment with Docker and package registry access.
- The current Sprint 2 implementation intentionally does not implement Customers, Leads, Properties, Deals, Reports, Workflow, Payments, or Commissions business modules.
- The missing canonical documentation should be restored before Sprint 3 scope is finalized.
