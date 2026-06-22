# Kiến trúc hệ thống hiện tại

> Tài liệu này mô tả mã nguồn tại commit nền `554caab`. Các đường dẫn được nêu là nguồn kiểm chứng; nội dung thiết kế chưa được hiện thực hóa không được coi là kiến trúc hiện hành.

## 1. Tổng quan

Hệ thống là một monorepo gồm:

- `backend/`: FastAPI, SQLAlchemy 2, Pydantic 2 và Alembic.
- `frontend/`: React 18, TypeScript và Vite; không có UI framework bên thứ ba.
- PostgreSQL 16 là cơ sở dữ liệu chính.
- Redis 7 được khai báo trong Docker Compose và cấu hình môi trường, nhưng chưa thấy service nghiệp vụ sử dụng Redis.
- `docker-compose.yml` chạy `postgres`, `redis`, `backend` và `frontend`.

Luồng HTTP:

```text
Browser
  -> React/Vite frontend
  -> /api/v1/*
  -> FastAPI routers
  -> service functions
  -> SQLAlchemy ORM
  -> PostgreSQL
```

## 2. Backend

### 2.1 Điểm vào

- `backend/app/main.py` tạo FastAPI application, cấu hình CORS, đăng ký router `/api/v1`, cung cấp `/health`, và gọi `init_db()` trong lifespan.
- `backend/app/api/v1/__init__.py` tập hợp các router: auth, admin users/roles/permissions, organization, leads, tasks, appointments, dashboard, customers, deals, projects, properties, bookings và contracts.
- Dependency xác thực/ủy quyền nằm trong `backend/app/auth/` và `backend/app/permissions/`.

### 2.2 Phân lớp thực tế

```text
api/v1/*.py       HTTP parsing, dependency injection, response envelope
schemas/*.py      Pydantic request/response validation
services/*.py     quyền theo scope, nghiệp vụ, audit, transaction
models/*.py       SQLAlchemy mappings và relationships
db/*.py           session, base, model registry, seed
alembic/          lịch sử schema
```

Các service là function-based, nhận `Session`, actor hiện tại và payload. Transaction thường được commit ngay trong service.

### 2.3 Xác thực và RBAC

- Access token và refresh token dùng JWT.
- Refresh token được lưu dạng hash trong bảng `refresh_tokens`.
- Quyền được lưu theo mã chuỗi; role nhận quyền qua `role_permissions`.
- Permission scope phổ biến: `own`, `team`, `department`, `all`.
- Organization scope dựa trên `departments`, `teams`, `user_organization_memberships`.
- Superuser bỏ qua các kiểm tra permission thông thường.
- Các thao tác chính ghi `audit_logs` qua `audit_service.write_audit_log`.

### 2.4 Các miền nghiệp vụ đã có backend

- Auth/RBAC và quản trị người dùng.
- Cơ cấu phòng ban/nhóm.
- Lead, lead activity, task, appointment, dashboard.
- Customer 360, chuyển Lead thành Customer, related people và scoring.
- Deal pipeline và deal timeline.
- Project/Property inventory, lịch sử giá và trạng thái.
- Booking/reservation/deposit và booking timeline.
- Contract, contract payment và contract timeline.

## 3. Frontend

### 3.1 Nền tảng

- Entry: `frontend/src/main.tsx`.
- Route tree: `frontend/src/routes/AppRoutes.tsx`.
- Auth state và API client nằm dưới `frontend/src/auth/` và `frontend/src/api/`.
- Layout/navigation: `frontend/src/layouts/AppLayout.tsx`.
- Feature code được chia dưới `frontend/src/features/<module>/`.

### 3.2 Routing hiện có

Các route được đăng ký gồm:

- `/login`
- `/dashboard/my`, `/dashboard/team`
- `/tasks`, `/appointments`
- `/leads`
- `/customers`, `/customers/:id`
- `/deals`, `/deals/:id`
- `/projects`, `/projects/:id`
- `/properties`, `/properties/:id`
- `/bookings`, `/bookings/:id`
- `/contracts`, `/contracts/:id`
- `/reports`
- các route quản trị users, roles, permissions, departments, teams và memberships.

Route và menu được bảo vệ bằng permission checks. Frontend chỉ là lớp UX; backend vẫn thực thi quyền và business validation.

### 3.3 Trạng thái UI Contract

`ContractsPage`, `ContractDetailPage`, `ContractFormModal` và `ContractTimeline` có implementation. Một số file component/modal được tạo nhưng hiện chỉ là placeholder một dòng, gồm payment/status/activity modal và một số table/filter/badge/summary components. Chức năng contract hiện tập trung trực tiếp trong page/form thay vì toàn bộ cấu trúc component đã dự kiến.

## 4. Dữ liệu và migration

- Schema được quản lý bởi 10 migration liên tiếp, revision `20260603_0001` đến `20260613_0010`.
- UUID là khóa chính xuyên suốt.
- Phần lớn aggregate dùng soft delete (`deleted_at`, `deleted_by_id`).
- Timeline nghiệp vụ được tách thành các bảng activity theo aggregate.
- Audit bảo mật/hệ thống dùng bảng `audit_logs`.
- Mã hiển thị như `LEAD-*`, `KH-*`, `DL-*`, `PRJ-*`, `PROP-*`, `BK-*`, `HD-*`, `PAY-*` được sinh ở application service bằng cách đọc mã hiện có; code có TODO chuyển sang database sequence.

## 5. Runtime bằng Docker

`docker-compose.yml`:

- PostgreSQL expose cổng `5432`.
- Redis expose cổng `6379`.
- Backend expose `8000`, đợi Postgres healthy, chạy `alembic upgrade head` rồi `uvicorn`.
- Frontend expose `3000`, dùng Vite development server và gọi backend qua `VITE_API_BASE_URL`.
- Volume lưu dữ liệu PostgreSQL và bind mount source phục vụ phát triển.

## 6. Quan sát kiến trúc cần lưu ý

- Không có background worker, scheduler hay message broker consumer trong code.
- Không có repository abstraction; service truy vấn SQLAlchemy trực tiếp.
- Không có frontend test runner trong `frontend/package.json`; script chỉ có `dev`, `build`, `preview`.
- Redis hiện là hạ tầng được cấu hình nhưng chưa có integration nghiệp vụ.
- Các permission marketing, commission, generic payments và reports tồn tại trong vocabulary, nhưng không đồng nghĩa các module nghiệp vụ đó đã được triển khai.

## 7. Nguồn kiểm chứng chính

- `backend/app/main.py`
- `backend/app/api/v1/`
- `backend/app/services/`
- `backend/app/models/`
- `backend/app/permissions/constants.py`
- `backend/alembic/versions/`
- `frontend/src/routes/AppRoutes.tsx`
- `frontend/src/layouts/AppLayout.tsx`
- `frontend/src/features/`
- `backend/requirements.txt`
- `frontend/package.json`
- `docker-compose.yml`
