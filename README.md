# CRM BDS

Web-based Real Estate CRM foundation.

## Stack

- Backend: FastAPI, Python 3.12, SQLAlchemy, PostgreSQL, Redis
- Frontend: React, TypeScript, Vite, TailwindCSS
- Infrastructure: Docker Compose

## How to run

```bash
docker compose up --build
```

The backend container runs Alembic migrations automatically before starting the FastAPI app. On startup, the app seeds default roles, permissions, role-permission assignments, and the default admin user if they do not already exist.

## Run migrations manually

If you need to run migrations outside the container startup command:

```bash
docker compose run --rm backend alembic upgrade head
```

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

> Change default admin password before production.

## Auth Test

1. Open the frontend at `http://localhost:3000`.
2. Login with the default admin credentials.
3. Confirm you are redirected to `/dashboard`.
4. Open Swagger at `http://localhost:8000/docs`.
5. Call `POST /api/v1/auth/login` with the default admin credentials.
6. Copy the returned `access_token`.
7. Click **Authorize** in Swagger and enter `Bearer <access_token>`.
8. Test `GET /api/v1/auth/me` with the Bearer token.

## Testing 401 and 403 behavior

### 401 Unauthorized

Call a protected endpoint without a Bearer token:

```bash
curl -i http://localhost:8000/api/v1/auth/me
```

Expected result: `401 Unauthorized`.

### 403 Forbidden

Login as a user that does not have the required permission, then call a restricted endpoint such as:

```bash
curl -i -H "Authorization: Bearer <access_token>" http://localhost:8000/api/v1/users
```

Expected result: `403 Forbidden` if the user lacks `users.view`.

## Sprint 2 scope

Implemented in Sprint 2:

- User accounts
- Roles
- Permissions
- User-role assignment
- Role-permission assignment
- Refresh token storage and revocation
- Audit log table and login/logout/user action audit entries
- JWT login, refresh, logout, and current user APIs
- RBAC backend dependencies
- Protected frontend routes
- Login UI connected to the backend

Not implemented in Sprint 2:

- Customers module
- Leads module
- Properties/inventory module
- Deals pipeline
- Payments/commissions module
- Reports module
- Workflow engine business flows
