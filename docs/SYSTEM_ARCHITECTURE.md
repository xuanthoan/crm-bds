# SYSTEM_ARCHITECTURE.md

# REAL ESTATE CRM - SYSTEM ARCHITECTURE

Version: 1.0
Status: Production Architecture
Project: Real Estate CRM & Sales Management System

---

# 1. MỤC TIÊU KIẾN TRÚC

Hệ thống phải đáp ứng:

* 50 → 500 sale sử dụng đồng thời
* Hàng triệu bản ghi khách hàng
* Hàng trăm nghìn giao dịch
* Dễ mở rộng module
* Dễ bảo trì
* Dễ nâng cấp AI sau này
* Không phụ thuộc vendor
* Chạy được On-Premise hoặc Cloud

---

# 2. KIẾN TRÚC TỔNG THỂ

```text
┌─────────────────────┐
│      React UI       │
└──────────┬──────────┘
           │ HTTPS
           ▼
┌─────────────────────┐
│      Nginx          │
│ Reverse Proxy       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│     FastAPI API     │
│     Backend Core    │
└──────┬──────┬───────┘
       │      │
       │      │
       ▼      ▼
 PostgreSQL  Redis
       │      │
       │      ▼
       │   Background Jobs
       │   Notification
       │   SLA Engine
       │
       ▼
 File Storage
(Local/MinIO/S3)

```

---

# 3. CÔNG NGHỆ CHUẨN

## Frontend

* React
* TypeScript
* Vite
* TailwindCSS
* TanStack Query
* React Hook Form
* Zod
* Zustand

---

## Backend

* Python 3.12+
* FastAPI
* SQLAlchemy 2.x
* Alembic
* Pydantic v2

---

## Database

* PostgreSQL 16+

---

## Cache

* Redis

---

## Queue

* Celery hoặc RQ

---

## Storage

Phase 1

```text
Local Storage
```

Phase 2

```text
MinIO
```

Phase 3

```text
AWS S3
```

---

# 4. DOMAIN ARCHITECTURE

Hệ thống chia thành các Domain độc lập.

```text
Auth
Users
Permissions

CRM
Lead
Customer

Inventory
Project
Property

Sales
Deal
Activity
Appointment

Finance
Payment
Commission

Marketing
Campaign
Lead Source

Workflow
SLA
Notification

Reporting
Audit Log

Files
```

---

# 5. CLEAN ARCHITECTURE

Backend áp dụng kiến trúc:

```text
Controller
   ↓
Service
   ↓
Repository
   ↓
Database
```

---

# 6. REQUEST FLOW

Ví dụ:

```text
User
 ↓
Frontend
 ↓
API
 ↓
Permission Check
 ↓
Service
 ↓
Repository
 ↓
PostgreSQL
 ↓
Response
```

---

# 7. FRONTEND ARCHITECTURE

```text
src/

app/
components/
features/
layouts/
pages/
services/
stores/
hooks/
utils/
routes/
```

---

# 8. FEATURE BASED STRUCTURE

```text
features/

customers/
leads/
properties/
projects/
deals/
activities/
appointments/
marketing/
reports/
settings/
```

---

# 9. BACKEND ARCHITECTURE

```text
app/

api/
core/
db/
models/
schemas/
repositories/
services/
permissions/
workflows/
jobs/
utils/
```

---

# 10. API LAYER

Chỉ làm nhiệm vụ:

* Nhận request
* Validate
* Gọi service
* Trả response

Không chứa business logic.

Ví dụ:

```python
@router.post("/customers")
def create_customer():
    return customer_service.create()
```

---

# 11. SERVICE LAYER

Chứa toàn bộ business logic.

Ví dụ:

```python
CustomerService
LeadService
DealService
WorkflowService
```

---

# 12. REPOSITORY LAYER

Chỉ làm việc với database.

Ví dụ:

```python
CustomerRepository
DealRepository
LeadRepository
```

---

# 13. AUTHENTICATION ARCHITECTURE

```text
User Login
    ↓
JWT Access Token
    ↓
Permission Check
    ↓
Data Scope Check
    ↓
API
```

---

# 14. AUTHORIZATION ARCHITECTURE

RBAC

```text
User
 ↓
Role
 ↓
Permission
```

Ví dụ:

```text
Sale
 ↓
customers.view.own
```

---

# 15. DATA SCOPE ARCHITECTURE

4 cấp dữ liệu:

```text
OWN
TEAM
DEPARTMENT
ALL
```

---

# 16. CUSTOMER DOMAIN

Bao gồm:

```text
Customer
Related Person
Tag
Note
File
Timeline
```

---

# 17. LEAD DOMAIN

```text
Lead
Lead Source
Campaign
Lead Assignment
Lead Reclaim
Lead SLA
```

---

# 18. INVENTORY DOMAIN

```text
Project
Property
Price History
Status History
Property Media
```

---

# 19. DEAL DOMAIN

```text
Deal
Deal Stage
Deal Timeline
Deposit
Contract
```

---

# 20. FINANCE DOMAIN

```text
Payment
Payment Schedule

Commission
Commission Payment
```

---

# 21. ACTIVITY DOMAIN

```text
Call
Meeting
Site Visit
Task
Reminder
```

---

# 22. REPORT DOMAIN

```text
Dashboard
Sales Funnel
ROI
Inventory Report
Forecast
```

---

# 23. WORKFLOW ARCHITECTURE

```text
Event
 ↓
Trigger
 ↓
Rule Engine
 ↓
Action Engine
 ↓
Notification
```

---

# 24. EVENT BUS

Ví dụ:

```python
publish(
 "lead.created"
)
```

Workflow Engine lắng nghe.

---

# 25. STATE MACHINE

Quản lý:

```text
Lead Status
Customer Status
Deal Stage
Property Status
Payment Status
Commission Status
```

---

# 26. SLA ENGINE

Quản lý:

```text
Lead SLA
Customer SLA
Deal SLA
```

---

# 27. NOTIFICATION ARCHITECTURE

```text
System Event
 ↓
Notification Service
 ↓
Database
 ↓
User
```

---

# 28. NOTIFICATION CHANNELS

Phase 1

```text
In-App
Email
```

Phase 2

```text
Zalo
Telegram
SMS
```

---

# 29. AUDIT ARCHITECTURE

Mọi thay đổi:

```text
Before
After
User
IP
Timestamp
```

được ghi log.

---

# 30. FILE ARCHITECTURE

```text
Customer Files
Property Files
Contracts
Receipts
Videos
Images
```

---

# 31. FILE STORAGE STRUCTURE

```text
storage/

customers/
properties/
contracts/
payments/
marketing/
```

---

# 32. DATABASE ARCHITECTURE

Schema:

```text
auth
crm
inventory
sales
finance
marketing
workflow
system
```

---

# 33. INDEX STRATEGY

Bắt buộc index:

```text
phone
email
status
owner_user_id
team_id
project_id
deal_stage
```

---

# 34. SEARCH ARCHITECTURE

Global Search:

```text
Phone
Customer
Property Code
Project
Deal
```

---

# 35. CACHING STRATEGY

Redis cache:

```text
Permissions
Master Data
Dashboard
Reports
```

---

# 36. BACKGROUND JOBS

```text
Lead SLA Check
Task Reminder
Payment Reminder
Commission Reminder
Notification Sender
```

---

# 37. IMPORT ENGINE

Flow:

```text
Upload
 ↓
Validate
 ↓
Preview
 ↓
Import
```

---

# 38. EXPORT ENGINE

```text
Query
 ↓
Generate
 ↓
Excel/PDF
 ↓
Download
```

---

# 39. REPORT ENGINE

```text
Transactional Data
 ↓
Aggregation
 ↓
Dashboard
```

---

# 40. SECURITY ARCHITECTURE

Bắt buộc:

* JWT
* RBAC
* Data Scope
* Audit Log
* Soft Delete

---

# 41. SOFT DELETE

Không xóa cứng.

Tất cả bảng nghiệp vụ:

```sql
deleted_at
deleted_by
```

---

# 42. DEPLOYMENT ARCHITECTURE

Docker Compose

```text
nginx
frontend
backend
postgres
redis
worker
```

---

# 43. SCALING PLAN

## Phase 1

1 Server

```text
Frontend
Backend
Postgres
Redis
```

---

## Phase 2

Tách:

```text
Frontend
Backend
Worker
Postgres
Redis
```

---

## Phase 3

Load Balancer

```text
Nginx

Backend 1
Backend 2
Backend 3

Redis

Postgres Primary
Postgres Replica
```

---

# 44. OBSERVABILITY

Logging:

```text
API Logs
Workflow Logs
Error Logs
Audit Logs
```

---

# 45. MONITORING

Khuyến nghị:

```text
Prometheus
Grafana
```

---

# 46. BACKUP STRATEGY

Database

```text
Daily Backup
Weekly Backup
Monthly Backup
```

---

# 47. HIGH RISK AREAS

Cần ưu tiên kiểm tra:

* Permission
* Data Scope
* Deal Stage
* Lead Assignment
* Commission Calculation
* Import Excel

---

# 48. PHASE IMPLEMENTATION

Phase 1

```text
Auth
Customer
Lead
Inventory
Deal
```

---

Phase 2

```text
Activities
Payment
Commission
Reports
```

---

Phase 3

```text
Workflow
Automation
Notifications
```

---

Phase 4

```text
AI Assistant
AI Lead Scoring
AI Forecast
```

---

# 49. FUTURE AI ARCHITECTURE

Sau này có thể bổ sung:

```text
OpenAI
Claude
Gemini
Ollama
```

thông qua:

```text
AI Service Layer
```

không ảnh hưởng hệ thống hiện tại.

---

# 50. FINAL ARCHITECTURE PRINCIPLES

CRM phải đảm bảo:

* Module độc lập
* Dễ mở rộng
* Không phụ thuộc vendor
* Permission chặt chẽ
* Workflow linh hoạt
* Audit đầy đủ
* Hiệu năng cao
* Có thể phục vụ từ 5 sale tới 500+ sale

Đây là kiến trúc chuẩn để triển khai CRM bất động sản quy mô doanh nghiệp và đủ nền tảng để phát triển thành SaaS trong tương lai.
