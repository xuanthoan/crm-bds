# DEVELOPMENT_PLAN.md

# REAL ESTATE CRM - DEVELOPMENT PLAN

Version: 1.0
Status: Draft
Project Type: Web-based CRM / Sales Management System
Suggested Stack: FastAPI + PostgreSQL + React + TypeScript + Docker

---

# 1. MỤC TIÊU TÀI LIỆU

Tài liệu này dùng để hướng dẫn quá trình phát triển phần mềm CRM bất động sản từ đầu đến khi có bản MVP hoạt động được.

Mục tiêu:

* Chia dự án thành các giai đoạn rõ ràng.
* Tránh code dàn trải, thiếu kiến trúc.
* Ưu tiên module quan trọng trước.
* Giúp Codex hoặc đội lập trình biết nên code theo thứ tự nào.
* Đảm bảo mỗi sprint có đầu ra kiểm thử được.
* Đảm bảo hệ thống dễ mở rộng sau này.

---

# 2. TÀI LIỆU LIÊN QUAN

Trước khi code, cần có các file tài liệu sau:

* `PRD.md`
* `DATABASE_SCHEMA.md`
* `PERMISSION_SYSTEM.md`
* `WORKFLOW_ENGINE.md`
* `API_SPEC.md`
* `UI_UX.md`
* `DEVELOPMENT_PLAN.md`

Không nên code nếu chưa có tối thiểu:

* PRD
* Database Schema
* Permission System
* API Spec
* UI/UX

---

# 3. MỤC TIÊU SẢN PHẨM

Xây dựng hệ thống CRM bất động sản quản lý toàn bộ vòng đời:

```text
Marketing
→ Lead
→ Khách hàng
→ Chăm sóc
→ Kho hàng
→ Giao dịch
→ Thanh toán
→ Hoa hồng
→ Báo cáo
```

---

# 4. ĐỐI TƯỢNG NGƯỜI DÙNG

Hệ thống cần phục vụ các vai trò:

* Admin
* Director / Giám đốc
* Sales Manager
* Leader
* Sale
* Marketing
* Accountant
* Inventory Manager

---

# 5. KIẾN TRÚC TỔNG THỂ

## 5.1. Frontend

Công nghệ đề xuất:

* React
* TypeScript
* TailwindCSS
* React Router
* TanStack Query
* Zustand hoặc Redux Toolkit
* React Hook Form
* Zod
* Axios

---

## 5.2. Backend

Công nghệ đề xuất:

* Python
* FastAPI
* SQLAlchemy
* Alembic
* Pydantic
* PostgreSQL
* Redis
* Celery hoặc RQ cho background jobs

---

## 5.3. Database

Công nghệ:

* PostgreSQL

Yêu cầu:

* UUID primary key
* Soft delete
* Audit log
* Index đầy đủ cho field hay filter
* Không xóa cứng dữ liệu nghiệp vụ

---

## 5.4. File Storage

Phase 1:

* Local storage

Phase 2:

* MinIO hoặc S3-compatible storage

---

## 5.5. Authentication

* JWT access token
* Refresh token
* RBAC
* Data scope
* Object access control

---

## 5.6. Deployment

Phase 1:

* Docker Compose local/server

Phase 2:

* VPS / Cloud Server

Phase 3:

* CI/CD

---

# 6. CẤU TRÚC REPOSITORY ĐỀ XUẤT

## 6.1. Monorepo

```text
real-estate-crm/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── permissions/
│   │   ├── workflows/
│   │   ├── jobs/
│   │   └── main.py
│   │
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── stores/
│   │   ├── hooks/
│   │   ├── utils/
│   │   └── main.tsx
│   │
│   ├── package.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── .env.example
│
├── docs/
│   ├── PRD.md
│   ├── DATABASE_SCHEMA.md
│   ├── PERMISSION_SYSTEM.md
│   ├── WORKFLOW_ENGINE.md
│   ├── API_SPEC.md
│   ├── UI_UX.md
│   └── DEVELOPMENT_PLAN.md
│
├── docker-compose.yml
├── README.md
└── .gitignore
```

---

# 7. BACKEND STRUCTURE

## 7.1. app/api

Chứa route API.

```text
api/
├── v1/
│   ├── auth.py
│   ├── users.py
│   ├── roles.py
│   ├── customers.py
│   ├── leads.py
│   ├── projects.py
│   ├── properties.py
│   ├── deals.py
│   ├── activities.py
│   ├── appointments.py
│   ├── payments.py
│   ├── commissions.py
│   ├── marketing.py
│   ├── reports.py
│   ├── files.py
│   ├── workflows.py
│   ├── notifications.py
│   └── audit_logs.py
```

---

## 7.2. app/models

Chứa SQLAlchemy models.

```text
models/
├── user.py
├── role.py
├── team.py
├── customer.py
├── lead.py
├── project.py
├── property.py
├── deal.py
├── activity.py
├── appointment.py
├── payment.py
├── commission.py
├── marketing.py
├── file.py
├── workflow.py
├── notification.py
└── audit_log.py
```

---

## 7.3. app/schemas

Chứa Pydantic schemas.

```text
schemas/
├── customer.py
├── lead.py
├── property.py
├── deal.py
├── activity.py
├── payment.py
└── report.py
```

---

## 7.4. app/services

Chứa business logic.

```text
services/
├── auth_service.py
├── customer_service.py
├── lead_service.py
├── property_service.py
├── deal_service.py
├── activity_service.py
├── workflow_service.py
├── permission_service.py
├── report_service.py
└── audit_service.py
```

---

## 7.5. app/permissions

Chứa logic phân quyền.

```text
permissions/
├── constants.py
├── dependencies.py
├── scope.py
└── object_access.py
```

---

## 7.6. app/workflows

Chứa workflow engine.

```text
workflows/
├── state_machine.py
├── rule_engine.py
├── trigger_engine.py
├── action_engine.py
├── sla_engine.py
└── events.py
```

---

# 8. FRONTEND STRUCTURE

## 8.1. features

Mỗi module là một feature.

```text
features/
├── auth/
├── dashboard/
├── customers/
├── leads/
├── inventory/
├── projects/
├── deals/
├── activities/
├── appointments/
├── marketing/
├── reports/
├── users/
├── permissions/
├── workflows/
└── settings/
```

---

## 8.2. components

Component dùng chung.

```text
components/
├── ui/
├── data-table/
├── forms/
├── badges/
├── layout/
├── charts/
├── kanban/
└── timeline/
```

---

# 9. CODING PRINCIPLES

## 9.1. Backend

* Không viết toàn bộ logic trong route.
* Route chỉ nhận request và trả response.
* Business logic nằm trong service.
* Query phức tạp nằm trong repository.
* Permission check bắt buộc ở API/service.
* Audit log bắt buộc với thao tác quan trọng.
* Dữ liệu nghiệp vụ phải soft delete.
* Validation quan trọng phải nằm ở backend.

---

## 9.2. Frontend

* Không hard-code permission trong nhiều nơi.
* Dùng helper `can(permission_key)`.
* Sidebar render theo permission.
* Form dùng schema validation.
* Table dùng server-side pagination/filter/sort.
* Không load toàn bộ dữ liệu lớn.
* Tách page, component, hook, service rõ ràng.

---

# 10. PHASE ROADMAP

## Phase 0 - Project Setup

Mục tiêu:

* Tạo project structure.
* Setup Docker.
* Setup database.
* Setup frontend.
* Setup backend.
* Setup basic CI nếu có.

Đầu ra:

* Backend chạy được.
* Frontend chạy được.
* PostgreSQL chạy được.
* Docker Compose chạy được.
* API health check hoạt động.

---

## Phase 1 - Authentication & Permission

Mục tiêu:

* Login
* JWT
* User
* Role
* Permission
* Team
* Data scope

Đầu ra:

* User đăng nhập được.
* Admin tạo user được.
* Admin gán role được.
* API chặn user không có quyền.
* Sale chỉ thấy dữ liệu của mình.

---

## Phase 2 - CRM Customers

Mục tiêu:

* Quản lý khách hàng.
* Chống trùng số điện thoại.
* Customer detail.
* Customer timeline.
* Tag.
* Related people.
* Notes.

Đầu ra:

* Thêm/sửa/xem khách hàng.
* Tìm khách theo số điện thoại.
* Không tạo trùng khách.
* Sale chỉ xem khách của mình.
* Leader xem khách team mình.

---

## Phase 3 - Lead Center

Mục tiêu:

* Quản lý lead.
* Import lead.
* Giao lead.
* Thu hồi lead.
* Convert lead to customer.
* SLA lead cơ bản.

Đầu ra:

* Marketing import lead được.
* Leader giao lead được.
* Lead trùng được phát hiện.
* Lead quá SLA có cảnh báo.

---

## Phase 4 - Inventory / Properties

Mục tiêu:

* Quản lý dự án.
* Quản lý căn hộ.
* Import bảng hàng.
* Lọc căn hộ.
* Lịch sử giá.
* Lịch sử trạng thái.
* File/media.

Đầu ra:

* Tạo dự án.
* Tạo căn hộ.
* Import căn hộ từ Excel.
* Lọc căn theo giá, diện tích, phòng ngủ, trạng thái.
* Đổi giá lưu lịch sử.
* Đổi trạng thái lưu lịch sử.

---

## Phase 5 - Deals / Pipeline

Mục tiêu:

* Tạo deal.
* Deal Kanban.
* State transition.
* Cọc.
* Hợp đồng.
* Closed Won/Lost.
* Timeline giao dịch.

Đầu ra:

* Sale tạo deal được.
* Kéo deal qua pipeline.
* Không cho chuyển stage sai.
* Deposit tự đổi trạng thái căn hộ.
* Closed Won tự đổi căn hộ sold.
* Closed Lost bắt buộc lý do.

---

## Phase 6 - Activities / Follow-up

Mục tiêu:

* Nhiệm vụ chăm sóc.
* Lịch hẹn.
* Hoàn thành task.
* Khách quá hạn.
* Playbook cơ bản.

Đầu ra:

* Sale thấy việc hôm nay.
* Sale hoàn thành task.
* Có thể tạo việc tiếp theo.
* Leader thấy khách bị bỏ quên.

---

## Phase 7 - Payment & Commission

Mục tiêu:

* Thanh toán nhiều đợt.
* Công nợ.
* Hoa hồng.
* Duyệt hoa hồng.
* Thanh toán hoa hồng.

Đầu ra:

* Deal có payment schedule.
* Kế toán cập nhật thanh toán.
* Hoa hồng tự tạo khi deal deposit/contract.
* Kế toán duyệt và đánh dấu đã trả hoa hồng.

---

## Phase 8 - Marketing

Mục tiêu:

* Campaign.
* Adset.
* Ads.
* Tracking lead source.
* CPL, CPA, CPD.
* Marketing ROI.

Đầu ra:

* Marketing tạo campaign.
* Lead gắn campaign.
* Báo cáo CPL/ROI có dữ liệu.

---

## Phase 9 - Reports & Dashboard

Mục tiêu:

* Sale Dashboard.
* Leader Dashboard.
* Director Dashboard.
* Marketing Dashboard.
* Reports.
* Export Excel/PDF/CSV.

Đầu ra:

* Dashboard theo vai trò.
* Báo cáo sales funnel.
* Báo cáo sale/team.
* Báo cáo marketing ROI.
* Báo cáo kho hàng.
* Báo cáo forecast cơ bản.

---

## Phase 10 - Workflow Engine

Mục tiêu:

* State machine.
* Rule engine.
* SLA engine.
* Notification.
* Background jobs.
* Workflow log.

Đầu ra:

* Lead mới tự tạo task.
* Activity quá hạn tự cảnh báo.
* Deal stage validation chạy qua state machine.
* Notification center hoạt động.
* Workflow log xem được.

---

## Phase 11 - Import / Export Center

Mục tiêu:

* Excel templates.
* Preview import.
* Confirm import.
* Export dữ liệu theo filter.

Đầu ra:

* Import khách hàng có preview lỗi/trùng.
* Import bảng hàng có preview lỗi/trùng.
* Export khách hàng/căn hộ/deal/report.

---

## Phase 12 - AI & Advanced Automation

Mục tiêu:

* AI lead scoring.
* AI deal scoring.
* AI gợi ý chăm sóc.
* AI gợi ý căn phù hợp.
* AI forecast.

Đầu ra:

* Chưa bắt buộc ở MVP.
* Chỉ triển khai sau khi dữ liệu nền ổn định.

---

# 11. MVP SCOPE

Bản MVP nên bao gồm:

## Bắt buộc

* Auth
* RBAC
* User/Team
* Customers
* Leads
* Projects
* Properties
* Deals
* Activities
* Basic Dashboard
* Audit Log
* Import/Export cơ bản

---

## Chưa cần trong MVP

* AI Assistant
* Mobile App
* Zalo OA Integration
* Call Center Integration
* Advanced Workflow Builder
* Advanced Forecast
* Multi-tenant SaaS

---

# 12. SPRINT PLAN CHI TIẾT

## Sprint 1 - Project Foundation

Tasks:

* Init backend FastAPI.
* Init frontend React.
* Setup Docker Compose.
* Setup PostgreSQL.
* Setup Alembic.
* Setup environment config.
* Create health check API.
* Create base response format.

Acceptance:

* `docker-compose up` chạy được.
* Frontend mở được.
* Backend health check trả OK.
* Database kết nối được.

---

## Sprint 2 - Auth & Users

Tasks:

* User model.
* Role model.
* Permission model.
* Login API.
* JWT.
* Current user API.
* Frontend login screen.
* Protected routes.

Acceptance:

* Login thành công.
* Token lưu được.
* Logout được.
* Route cần login bị chặn nếu chưa đăng nhập.

---

## Sprint 3 - RBAC & Teams

Tasks:

* Team model.
* Department model.
* User team assignment.
* Role permission assignment.
* Permission middleware.
* Data scope helper.
* Sidebar theo permission.

Acceptance:

* Admin tạo team được.
* Admin gán role được.
* Sale không gọi được API admin.
* Menu ẩn theo quyền.

---

## Sprint 4 - Customer Core

Tasks:

* Customer model.
* Customer API.
* Customer list UI.
* Customer form.
* Phone duplicate check.
* Customer detail basic.

Acceptance:

* Tạo khách hàng được.
* Không tạo trùng số điện thoại.
* Lọc/tìm kiếm khách.
* Sale chỉ thấy khách của mình.

---

## Sprint 5 - Customer 360

Tasks:

* Customer timeline.
* Customer tags.
* Related people.
* Notes.
* Files basic.
* Customer detail tabs.

Acceptance:

* Customer detail hiển thị đầy đủ.
* Ghi chú được.
* Gắn tag được.
* Timeline có sự kiện tạo/sửa/chăm sóc.

---

## Sprint 6 - Lead Center

Tasks:

* Lead model.
* Lead API.
* Lead list UI.
* Assign lead.
* Reclaim lead.
* Convert lead to customer.
* Duplicate lead logic.

Acceptance:

* Import/tạo lead được.
* Giao lead cho sale được.
* Thu hồi lead được.
* Convert lead sang customer được.

---

## Sprint 7 - Project & Inventory

Tasks:

* Project model/API/UI.
* Property model/API/UI.
* Property filters.
* Property detail.
* Price history.
* Status history.

Acceptance:

* Tạo dự án được.
* Tạo căn hộ được.
* Lọc kho hàng được.
* Đổi giá ghi lịch sử.
* Đổi trạng thái ghi lịch sử.

---

## Sprint 8 - Deal Pipeline

Tasks:

* Deal model/API.
* Deal list.
* Deal Kanban.
* Stage transition.
* Deal detail.
* Closed lost reason.

Acceptance:

* Tạo deal được.
* Kéo deal qua stage hợp lệ.
* Không cho stage sai.
* Closed lost bắt buộc lý do.

---

## Sprint 9 - Deposit, Contract, Property Sync

Tasks:

* Deposit fields.
* Contract fields.
* Property status sync.
* Deal timeline.
* Deal audit log.

Acceptance:

* Deal sang deposit cập nhật property deposited.
* Deal closed won cập nhật property sold.
* Deal closed lost xử lý đúng trạng thái.

---

## Sprint 10 - Activities & Appointments

Tasks:

* Activity model/API/UI.
* Appointment model/API/UI.
* Task dashboard.
* Complete activity.
* Overdue activity.

Acceptance:

* Sale thấy việc hôm nay.
* Hoàn thành activity được.
* Tạo lịch hẹn được.
* Việc quá hạn hiển thị đúng.

---

## Sprint 11 - Payment & Commission

Tasks:

* Payment schedule.
* Commission model.
* Commission calculation.
* Accountant UI.
* Mark paid.

Acceptance:

* Tạo lịch thanh toán.
* Cập nhật thanh toán.
* Hoa hồng tạo tự động.
* Duyệt/trả hoa hồng được.

---

## Sprint 12 - Marketing

Tasks:

* Campaign model/API/UI.
* Adset/Ads basic.
* Lead source tracking.
* Marketing dashboard.
* CPL/ROI calculation.

Acceptance:

* Tạo campaign.
* Lead gắn campaign.
* Marketing dashboard có CPL/ROI.

---

## Sprint 13 - Reports

Tasks:

* CEO dashboard.
* Sale dashboard.
* Leader dashboard.
* Sales funnel report.
* Inventory report.
* Deal report.
* Export basic.

Acceptance:

* Dashboard theo role chạy đúng.
* Báo cáo lọc theo quyền.
* Export được dữ liệu.

---

## Sprint 14 - Workflow Basic

Tasks:

* State transition table.
* Workflow event bus.
* Basic workflow runner.
* SLA lead.
* Notification center.
* Background jobs.

Acceptance:

* Lead được giao tự tạo task.
* Lead quá SLA có cảnh báo.
* Notification hiển thị.
* Workflow log ghi lại.

---

## Sprint 15 - Import/Export Advanced

Tasks:

* Customer import template.
* Property import template.
* Import preview.
* Import confirm.
* Error rows.
* Duplicate rows.

Acceptance:

* Upload Excel preview được.
* Dòng lỗi hiển thị rõ.
* Chỉ import dòng hợp lệ.
* Không import trùng.

---

## Sprint 16 - Hardening & Release

Tasks:

* Fix bug.
* Improve performance.
* Security review.
* Data permission review.
* UI polish.
* Seed data.
* Backup guide.
* Deployment guide.

Acceptance:

* MVP demo được end-to-end.
* Không có lỗi phân quyền nghiêm trọng.
* Không mất dữ liệu khi thao tác sai.
* Có tài liệu cài đặt.

---

# 13. THỨ TỰ CODE KHUYẾN NGHỊ CHO CODEX

Không yêu cầu Codex code toàn bộ hệ thống một lần.

Nên chia prompt theo thứ tự:

1. Setup backend structure.
2. Setup frontend structure.
3. Create database models for auth.
4. Create auth API.
5. Create RBAC system.
6. Create customer module.
7. Create lead module.
8. Create inventory module.
9. Create deal module.
10. Create activity module.
11. Create reports.
12. Create workflow engine.
13. Polish UI.
14. Write tests.
15. Dockerize.

---

# 14. CODING PROMPT FORMAT CHO CODEX

Mỗi prompt gửi Codex nên có cấu trúc:

```text
You are coding inside this existing project.

Read these files first:
- docs/PRD.md
- docs/DATABASE_SCHEMA.md
- docs/PERMISSION_SYSTEM.md
- docs/API_SPEC.md
- docs/UI_UX.md
- docs/DEVELOPMENT_PLAN.md

Task:
[Việc cần làm]

Requirements:
- [Yêu cầu 1]
- [Yêu cầu 2]

Do not:
- Do not break existing API.
- Do not remove existing permission checks.
- Do not hard-code business data.
- Do not ignore audit log for important changes.

Acceptance Criteria:
- [Tiêu chí 1]
- [Tiêu chí 2]

After coding:
- Explain changed files.
- Explain how to test.
```

---

# 15. TESTING STRATEGY

## 15.1. Backend Tests

Cần test:

* Auth
* Permission
* Data scope
* Customer duplicate
* Lead assignment
* Deal transition
* Property status sync
* Payment status
* Commission calculation
* Workflow trigger

---

## 15.2. Frontend Tests

Cần test:

* Login
* Sidebar theo quyền
* Customer list
* Customer form validation
* Deal Kanban
* Import preview
* Permission hide buttons

---

## 15.3. End-to-End Tests

Luồng test quan trọng:

```text
Marketing tạo lead
→ Leader giao lead
→ Sale gọi khách
→ Convert thành customer
→ Tạo deal
→ Chọn căn hộ
→ Đặt cọc
→ Ký hợp đồng
→ Thanh toán
→ Tính hoa hồng
→ Báo cáo CEO cập nhật
```

---

# 16. SEED DATA

Cần tạo dữ liệu mẫu:

## Users

* 1 Admin
* 1 Director
* 1 Sales Manager
* 2 Leader
* 6 Sale
* 1 Marketing
* 1 Accountant
* 1 Inventory Manager

---

## Projects

* 3 dự án

---

## Properties

* 100 căn hộ mẫu

---

## Customers

* 100 khách hàng mẫu

---

## Leads

* 200 lead mẫu

---

## Deals

* 30 deal mẫu ở nhiều stage

---

## Activities

* 300 activity mẫu

---

# 17. DATABASE MIGRATION PLAN

## 17.1. Alembic

Mọi thay đổi database phải qua migration.

Không sửa database thủ công.

---

## 17.2. Migration Naming

Format:

```text
YYYYMMDD_HHMM_description.py
```

Ví dụ:

```text
20260531_0900_create_customers_table.py
```

---

## 17.3. Migration Order

1. Auth tables
2. RBAC tables
3. Organization tables
4. Customer tables
5. Lead tables
6. Project/property tables
7. Deal tables
8. Activity tables
9. Payment/commission tables
10. Marketing tables
11. Workflow tables
12. Audit log tables

---

# 18. DEPLOYMENT PLAN

## 18.1. Local Development

Dùng Docker Compose:

Services:

* postgres
* redis
* backend
* frontend

---

## 18.2. Production Basic

Services:

* nginx
* frontend
* backend
* postgres
* redis
* worker

---

## 18.3. Environment Variables

Backend:

```text
DATABASE_URL
REDIS_URL
SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS
CORS_ORIGINS
FILE_STORAGE_PATH
```

Frontend:

```text
VITE_API_BASE_URL
VITE_APP_NAME
```

---

# 19. BACKUP PLAN

## 19.1. Database Backup

Tối thiểu:

* Backup hằng ngày
* Giữ 7 bản gần nhất
* Giữ bản cuối tháng

---

## 19.2. File Backup

Backup thư mục upload:

* Ảnh
* Video
* Hợp đồng
* Phiếu cọc
* Chứng từ

---

# 20. SECURITY CHECKLIST

Trước khi release:

* API có authentication.
* API có permission.
* API có data scope.
* Không lộ dữ liệu khách sale khác.
* Password hash bằng bcrypt/argon2.
* JWT secret không hard-code.
* Export có permission riêng.
* File upload kiểm tra định dạng.
* Không cho upload file nguy hiểm.
* Audit log cho thao tác quan trọng.
* CORS cấu hình đúng.
* Rate limit login nếu có thể.

---

# 21. PERFORMANCE CHECKLIST

Cần đảm bảo:

* Customer list có pagination.
* Lead list có pagination.
* Property list có pagination.
* Deal list có pagination.
* Search có debounce.
* Field filter quan trọng có index.
* Không load toàn bộ timeline nếu quá lớn.
* Không load toàn bộ file cùng lúc.
* Report query cần tối ưu.

---

# 22. IMPORTANT INDEXES

Database cần index tối thiểu:

* customers.phone_primary
* customers.owner_user_id
* customers.team_id
* customers.status
* customers.temperature
* leads.phone
* leads.assigned_user_id
* leads.status
* leads.source
* properties.project_id
* properties.status
* properties.price
* properties.bedrooms
* deals.customer_id
* deals.property_id
* deals.owner_user_id
* deals.stage
* activities.assigned_user_id
* activities.due_at
* activities.status
* payments.due_date
* payments.status

---

# 23. RELEASE CRITERIA

MVP được coi là hoàn thành khi:

* Admin tạo user, team, role được.
* Sale đăng nhập và chỉ thấy khách của mình.
* Leader thấy khách của team.
* Tạo khách hàng có chống trùng.
* Tạo lead, giao lead, thu hồi lead được.
* Tạo dự án, căn hộ được.
* Lọc kho hàng được.
* Tạo deal được.
* Deal pipeline hoạt động.
* Tạo nhiệm vụ chăm sóc được.
* Dashboard cơ bản hoạt động.
* Export cơ bản hoạt động.
* Audit log hoạt động.
* Không có lỗi phân quyền nghiêm trọng.

---

# 24. KNOWN RISKS

## 24.1. Scope quá lớn

CRM này có nhiều module.

Giải pháp:

* Không code tất cả cùng lúc.
* Làm MVP trước.
* Mỗi sprint chỉ làm một nhóm chức năng.

---

## 24.2. Sai database từ đầu

Giải pháp:

* Hoàn thiện DATABASE_SCHEMA.md trước.
* Dùng migration.
* Review quan hệ bảng kỹ.

---

## 24.3. Lỗi phân quyền

Giải pháp:

* Code RBAC sớm.
* Test data scope kỹ.
* Không để frontend quyết định quyền.

---

## 24.4. Báo cáo chậm

Giải pháp:

* Index field quan trọng.
* Tối ưu query.
* Có thể tạo materialized view sau.

---

## 24.5. Workflow quá phức tạp

Giải pháp:

* Phase 1 chỉ làm workflow cơ bản.
* Phase 2 mới làm workflow builder nâng cao.

---

# 25. FUTURE ROADMAP

## Version 1.1

* Workflow Builder nâng cao
* Report Builder
* Import/Export nâng cao
* Notification email

---

## Version 1.2

* AI Lead Scoring
* AI Deal Scoring
* Matching Engine nâng cao
* Forecast nâng cao

---

## Version 1.3

* Zalo OA Integration
* Call Center Integration
* SMS Integration
* Mobile App

---

## Version 2.0

* Multi-tenant SaaS
* Subscription billing
* Marketplace template
* Advanced analytics

---

# 26. FINAL NOTE FOR CODEX

Khi bắt đầu code, cần tuân thủ nghiêm ngặt thứ tự:

1. Database
2. Auth
3. Permission
4. Customer
5. Lead
6. Inventory
7. Deal
8. Activity
9. Report
10. Workflow

Không được code UI trước khi có API và permission cơ bản.

Không được bỏ qua:

* Audit log
* Soft delete
* Data scope
* Phone duplicate check
* State transition validation

Đây là các phần quyết định hệ thống có dùng thực tế được hay không.
