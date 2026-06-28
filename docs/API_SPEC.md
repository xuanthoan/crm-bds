# API_SPEC.md

# REAL ESTATE CRM - API SPECIFICATION

Version: 1.0
Status: Draft
Backend Suggested Stack: FastAPI + PostgreSQL + SQLAlchemy
Auth: JWT + RBAC + Data Scope Permission

---

# 1. API DESIGN PRINCIPLES

## 1.1. Base URL

```text
/api/v1
```

---

## 1.2. Response Format

Tất cả API trả về theo format thống nhất:

```json
{
  "success": true,
  "message": "OK",
  "data": {},
  "meta": {}
}
```

Khi lỗi:

```json
{
  "success": false,
  "message": "Validation error",
  "errors": [
    {
      "field": "phone_primary",
      "message": "Phone number already exists"
    }
  ]
}
```

---

## 1.3. Pagination Format

Các API danh sách phải hỗ trợ phân trang.

Query params:

```text
?page=1&page_size=20
```

Response:

```json
{
  "success": true,
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 120,
    "total_pages": 6
  }
}
```

---

## 1.4. Sorting

Query params:

```text
?sort_by=created_at&sort_order=desc
```

---

## 1.5. Filtering

Các API danh sách phải hỗ trợ filter theo field quan trọng.

Ví dụ:

```text
/customers?status=hot&owner_user_id=123&source=facebook
```

---

## 1.6. Authentication Header

```http
Authorization: Bearer <access_token>
```

---

## 1.7. Permission

Mọi API phải kiểm tra:

* User đã đăng nhập chưa
* User có permission không
* User có quyền xem/sửa object cụ thể không
* User có đúng data scope không

---

# 2. STATUS CODES

## 2.1. Success

```text
200 OK
201 Created
204 No Content
```

---

## 2.2. Client Errors

```text
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Validation Error
```

---

## 2.3. Server Errors

```text
500 Internal Server Error
```

---

# 3. AUTH API

## 3.1. Login

```http
POST /api/v1/auth/login
```

Request:

```json
{
  "email": "sale@example.com",
  "password": "password123"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "access_token": "jwt_access_token",
    "refresh_token": "jwt_refresh_token",
    "token_type": "bearer",
    "user": {
      "id": "uuid",
      "full_name": "Nguyen Van A",
      "email": "sale@example.com",
      "roles": ["sale"]
    }
  }
}
```

---

## 3.2. Refresh Token

```http
POST /api/v1/auth/refresh
```

Request:

```json
{
  "refresh_token": "jwt_refresh_token"
}
```

---

## 3.3. Logout

```http
POST /api/v1/auth/logout
```

---

## 3.4. Get Current User

```http
GET /api/v1/auth/me
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "full_name": "Nguyen Van A",
    "email": "sale@example.com",
    "roles": ["sale"],
    "permissions": ["customers.view.own", "deals.create"],
    "team_id": "uuid"
  }
}
```

---

# 4. USER & TEAM API

## 4.1. List Users

```http
GET /api/v1/users
```

Permission:

```text
users.view
```

Filters:

```text
role
team_id
department_id
status
keyword
```

---

## 4.2. Create User

```http
POST /api/v1/users
```

Permission:

```text
users.create
```

Request:

```json
{
  "full_name": "Nguyen Van A",
  "email": "sale@example.com",
  "phone": "0987654321",
  "password": "Password@123",
  "role_ids": ["uuid"],
  "team_id": "uuid",
  "department_id": "uuid",
  "status": "active"
}
```

---

## 4.3. Update User

```http
PUT /api/v1/users/{user_id}
```

---

## 4.4. Deactivate User

```http
POST /api/v1/users/{user_id}/deactivate
```

---

## 4.5. List Teams

```http
GET /api/v1/teams
```

---

## 4.6. Create Team

```http
POST /api/v1/teams
```

Request:

```json
{
  "name": "Team A",
  "leader_id": "uuid",
  "department_id": "uuid"
}
```

---

# 5. PERMISSION API

## 5.1. List Roles

```http
GET /api/v1/roles
```

---

## 5.2. Create Role

```http
POST /api/v1/roles
```

Request:

```json
{
  "name": "Sale",
  "code": "sale",
  "description": "Nhân viên kinh doanh"
}
```

---

## 5.3. List Permissions

```http
GET /api/v1/permissions
```

---

## 5.4. Assign Permissions To Role

```http
POST /api/v1/roles/{role_id}/permissions
```

Request:

```json
{
  "permission_ids": ["uuid", "uuid"]
}
```

---

## 5.5. Assign Roles To User

```http
POST /api/v1/users/{user_id}/roles
```

Request:

```json
{
  "role_ids": ["uuid"]
}
```

---

# 6. CUSTOMER API

## 6.1. List Customers

```http
GET /api/v1/customers
```

Permission:

```text
customers.view.own/team/department/all
```

Filters:

```text
keyword
status
temperature
owner_user_id
team_id
source
project_id
min_budget
max_budget
bedrooms
province
district
created_from
created_to
```

Response:

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "customer_code": "CUS-000001",
      "full_name": "Nguyen Van A",
      "phone_primary": "0987654321",
      "email": "a@example.com",
      "status": "interested",
      "temperature": "hot",
      "owner_user": {
        "id": "uuid",
        "full_name": "Sale A"
      },
      "created_at": "2026-05-31T10:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

---

## 6.2. Create Customer

```http
POST /api/v1/customers
```

Permission:

```text
customers.create
```

Request:

```json
{
  "full_name": "Nguyen Van A",
  "gender": "male",
  "birthday": "1990-01-01",
  "phone_primary": "0987654321",
  "phone_secondary": "0912345678",
  "email": "a@example.com",
  "zalo": "0987654321",
  "facebook": "https://facebook.com/example",
  "address": "Hai Phong",
  "province": "Hai Phong",
  "district": "Ngo Quyen",
  "occupation": "Business Owner",
  "company": "ABC Company",
  "position": "Director",
  "budget_min": 3000000000,
  "budget_max": 5000000000,
  "cash_available": 1500000000,
  "loan_needed": 2000000000,
  "buying_purpose": "investment",
  "interested_property_types": ["apartment"],
  "interested_project_ids": ["uuid"],
  "preferred_bedrooms": 2,
  "preferred_area_min": 60,
  "preferred_area_max": 80,
  "preferred_direction": "southeast",
  "buying_timeline": "within_3_months",
  "source": "facebook_ads",
  "note": "Khách quan tâm căn 2PN"
}
```

Rules:

* Không cho tạo trùng phone_primary.
* Nếu phone_secondary trùng khách khác thì cảnh báo.
* Nếu user là Sale thì owner_user_id = current_user.id.
* Nếu tạo từ Lead thì phải liên kết lead_id.

---

## 6.3. Get Customer Detail

```http
GET /api/v1/customers/{customer_id}
```

Response includes:

* Basic information
* Financial profile
* Needs
* Owner
* Tags
* Activities
* Deals
* Timeline
* Files
* Related people

---

## 6.4. Update Customer

```http
PUT /api/v1/customers/{customer_id}
```

Permission:

```text
customers.update.own/team/all
```

---

## 6.5. Delete Customer

```http
DELETE /api/v1/customers/{customer_id}
```

Permission:

```text
customers.delete
```

Action:

* Soft delete only.
* Write audit log.

---

## 6.6. Transfer Customer Owner

```http
POST /api/v1/customers/{customer_id}/transfer
```

Request:

```json
{
  "new_owner_user_id": "uuid",
  "reason": "Sale cũ nghỉ việc"
}
```

---

## 6.7. Add Customer Tag

```http
POST /api/v1/customers/{customer_id}/tags
```

Request:

```json
{
  "tag_ids": ["uuid"]
}
```

---

## 6.8. Remove Customer Tag

```http
DELETE /api/v1/customers/{customer_id}/tags/{tag_id}
```

---

## 6.9. Customer Timeline

```http
GET /api/v1/customers/{customer_id}/timeline
```

---

## 6.10. Customer 360 View

```http
GET /api/v1/customers/{customer_id}/360
```

Response includes:

* Customer profile
* Activities
* Appointments
* Deals
* Interested properties
* Suggested properties
* Files
* Notes
* Marketing attribution
* Financial info

---

# 7. RELATED PEOPLE API

## 7.1. List Related People

```http
GET /api/v1/customers/{customer_id}/related-people
```

---

## 7.2. Create Related Person

```http
POST /api/v1/customers/{customer_id}/related-people
```

Request:

```json
{
  "full_name": "Tran Thi B",
  "phone": "0912345678",
  "relationship": "wife",
  "decision_role": "decision_maker",
  "note": "Người quyết định chính"
}
```

---

# 8. LEAD API

## 8.1. List Leads

```http
GET /api/v1/leads
```

Filters:

```text
keyword
status
source
campaign_id
assigned_user_id
team_id
quality
created_from
created_to
is_duplicate
```

---

## 8.2. Create Lead

```http
POST /api/v1/leads
```

Request:

```json
{
  "full_name": "Nguyen Van A",
  "phone": "0987654321",
  "email": "a@example.com",
  "source": "facebook_ads",
  "campaign_id": "uuid",
  "adset_id": "uuid",
  "ad_id": "uuid",
  "interested_project_id": "uuid",
  "raw_data": {}
}
```

Rules:

* Normalize phone.
* Check duplicate.
* Attach marketing attribution.
* Start SLA.
* Auto assign if enabled.

---

## 8.3. Get Lead Detail

```http
GET /api/v1/leads/{lead_id}
```

---

## 8.4. Update Lead

```http
PUT /api/v1/leads/{lead_id}
```

---

## 8.5. Assign Lead

```http
POST /api/v1/leads/{lead_id}/assign
```

Request:

```json
{
  "assigned_user_id": "uuid",
  "reason": "Phân bổ lead mới"
}
```

---

## 8.6. Reclaim Lead

```http
POST /api/v1/leads/{lead_id}/reclaim
```

Request:

```json
{
  "reason": "Sale không xử lý quá SLA",
  "move_to_pool": true
}
```

---

## 8.7. Convert Lead To Customer

```http
POST /api/v1/leads/{lead_id}/convert
```

Request:

```json
{
  "customer_data": {
    "full_name": "Nguyen Van A",
    "phone_primary": "0987654321"
  }
}
```

---

## 8.8. Import Leads From Excel

```http
POST /api/v1/leads/import
```

Content-Type:

```text
multipart/form-data
```

Fields:

```text
file
source
campaign_id
```

---

# 9. PROJECT API

## 9.1. List Projects

```http
GET /api/v1/projects
```

Filters:

```text
keyword
status
province
district
developer
```

---

## 9.2. Create Project

```http
POST /api/v1/projects
```

Request:

```json
{
  "project_code": "PRJ-001",
  "name": "Anzen Hai Phong",
  "developer": "ABC Developer",
  "operator": "ABC Management",
  "address": "Hai Phong",
  "province": "Hai Phong",
  "district": "Le Chan",
  "status": "selling",
  "website": "https://example.com",
  "hotline": "0987654321",
  "description": "Dự án căn hộ cao cấp"
}
```

---

## 9.3. Get Project Detail

```http
GET /api/v1/projects/{project_id}
```

---

## 9.4. Update Project

```http
PUT /api/v1/projects/{project_id}
```

---

## 9.5. Delete Project

```http
DELETE /api/v1/projects/{project_id}
```

Soft delete.

---

# 10. PROPERTY / INVENTORY API

## 10.1. List Properties

```http
GET /api/v1/properties
```

Filters:

```text
keyword
project_id
block
floor
property_type
bedrooms
bathrooms
min_area
max_area
min_price
max_price
direction
balcony_direction
view
status
legal_status
commission_min
commission_max
```

---

## 10.2. Create Property

```http
POST /api/v1/properties
```

Request:

```json
{
  "property_code": "A-1208",
  "project_id": "uuid",
  "block": "A",
  "floor": 12,
  "unit_number": "1208",
  "property_type": "apartment",
  "bedrooms": 2,
  "bathrooms": 2,
  "area_gross": 75.5,
  "area_net": 68.2,
  "balcony_area": 6.5,
  "door_direction": "northwest",
  "balcony_direction": "southeast",
  "view": "sea",
  "listed_price": 3500000000,
  "owner_expected_price": 3400000000,
  "minimum_acceptable_price": 3300000000,
  "commission_type": "percent",
  "commission_value": 2.0,
  "status": "available",
  "legal_status": "sales_contract",
  "owner_name": "Tran Van B",
  "owner_phone": "0912345678",
  "note": "Chủ cần bán nhanh"
}
```

Rules:

* property_code phải unique theo project.
* price_per_m2 tự tính.
* Khi tạo property phải tạo status history.

---

## 10.3. Get Property Detail

```http
GET /api/v1/properties/{property_id}
```

Response includes:

* Basic info
* Project
* Price history
* Status history
* Files
* Related active deals
* Owner info
* Suggested customers

---

## 10.4. Update Property

```http
PUT /api/v1/properties/{property_id}
```

Rules:

* Nếu đổi giá thì ghi price_history.
* Nếu đổi trạng thái thì ghi status_history.
* Nếu property sold thì hạn chế sửa giá/trạng thái nếu không có quyền Admin.

---

## 10.5. Update Property Status

```http
POST /api/v1/properties/{property_id}/status
```

Request:

```json
{
  "status": "reserved",
  "reason": "Khách đang giữ chỗ"
}
```

---

## 10.6. Property Price History

```http
GET /api/v1/properties/{property_id}/price-history
```

---

## 10.7. Property Status History

```http
GET /api/v1/properties/{property_id}/status-history
```

---

## 10.8. Import Properties From Excel

```http
POST /api/v1/properties/import
```

Content-Type:

```text
multipart/form-data
```

---

## 10.9. Match Properties For Customer

```http
GET /api/v1/customers/{customer_id}/matched-properties
```

Query params:

```text
limit=20
```

---

# 11. DEAL API

## 11.1. List Deals

```http
GET /api/v1/deals
```

Filters:

```text
keyword
stage
customer_id
property_id
owner_user_id
team_id
project_id
created_from
created_to
min_value
max_value
```

---

## 11.2. Create Deal

```http
POST /api/v1/deals
```

Request:

```json
{
  "customer_id": "uuid",
  "property_id": "uuid",
  "deal_type": "purchase",
  "expected_price": 3500000000,
  "note": "Khách quan tâm nghiêm túc"
}
```

Rules:

* Customer phải thuộc quyền user.
* Property không được sold/off_market/locked.
* Deal owner mặc định là current_user.
* Deal stage mặc định là lead hoặc negotiation tùy cấu hình.

---

## 11.3. Get Deal Detail

```http
GET /api/v1/deals/{deal_id}
```

Response includes:

* Deal info
* Customer
* Property
* Stage history
* Payments
* Commissions
* Files
* Activities
* Timeline

---

## 11.4. Update Deal

```http
PUT /api/v1/deals/{deal_id}
```

---

## 11.5. Change Deal Stage

```http
POST /api/v1/deals/{deal_id}/stage
```

Request:

```json
{
  "stage": "deposit",
  "note": "Khách đã đặt cọc",
  "extra_data": {
    "deposit_amount": 100000000,
    "deposit_date": "2026-05-31"
  }
}
```

Rules:

* Validate state transition.
* Validate required fields.
* Trigger workflow.
* Write audit log.

---

## 11.6. Close Deal Lost

```http
POST /api/v1/deals/{deal_id}/close-lost
```

Request:

```json
{
  "lost_reason": "price_too_high",
  "lost_note": "Khách chọn dự án khác"
}
```

---

## 11.7. Approve Deal

```http
POST /api/v1/deals/{deal_id}/approve
```

---

## 11.8. Deal Timeline

```http
GET /api/v1/deals/{deal_id}/timeline
```

---

## 11.9. Deal Forecast

```http
GET /api/v1/deals/forecast
```

Filters:

```text
month
quarter
year
team_id
owner_user_id
project_id
```

---

# 12. PAYMENT API

## 12.1. List Payments

```http
GET /api/v1/payments
```

Filters:

```text
deal_id
customer_id
status
due_from
due_to
overdue
```

---

## 12.2. Create Payment Schedule

```http
POST /api/v1/deals/{deal_id}/payments
```

Request:

```json
{
  "payments": [
    {
      "name": "Đợt 1",
      "amount": 100000000,
      "due_date": "2026-06-10"
    },
    {
      "name": "Đợt 2",
      "amount": 500000000,
      "due_date": "2026-07-10"
    }
  ]
}
```

---

## 12.3. Update Payment

```http
PUT /api/v1/payments/{payment_id}
```

Request:

```json
{
  "paid_amount": 100000000,
  "paid_date": "2026-06-10",
  "status": "paid",
  "note": "Đã chuyển khoản"
}
```

---

## 12.4. Mark Payment Paid

```http
POST /api/v1/payments/{payment_id}/mark-paid
```

---

# 13. COMMISSION API

## 13.1. List Commissions

```http
GET /api/v1/commissions
```

Filters:

```text
deal_id
user_id
status
project_id
month
```

---

## 13.2. Get Commission Detail

```http
GET /api/v1/commissions/{commission_id}
```

---

## 13.3. Update Commission

```http
PUT /api/v1/commissions/{commission_id}
```

---

## 13.4. Approve Commission

```http
POST /api/v1/commissions/{commission_id}/approve
```

---

## 13.5. Mark Commission Paid

```http
POST /api/v1/commissions/{commission_id}/mark-paid
```

Request:

```json
{
  "paid_amount": 50000000,
  "paid_date": "2026-06-30",
  "payment_note": "Thanh toán hoa hồng đợt 1"
}
```

---

# 14. ACTIVITY / FOLLOW-UP API

## 14.1. List Activities

```http
GET /api/v1/activities
```

Filters:

```text
customer_id
deal_id
assigned_user_id
activity_type
status
due_from
due_to
overdue
```

---

## 14.2. Create Activity

```http
POST /api/v1/activities
```

Request:

```json
{
  "customer_id": "uuid",
  "deal_id": "uuid",
  "activity_type": "call",
  "title": "Gọi tư vấn khách",
  "description": "Tư vấn căn 2PN",
  "due_at": "2026-06-01T09:00:00Z",
  "assigned_user_id": "uuid"
}
```

---

## 14.3. Update Activity

```http
PUT /api/v1/activities/{activity_id}
```

---

## 14.4. Complete Activity

```http
POST /api/v1/activities/{activity_id}/complete
```

Request:

```json
{
  "result": "Khách quan tâm, hẹn xem nhà",
  "next_follow_up_at": "2026-06-03T09:00:00Z",
  "customer_status": "appointment_scheduled"
}
```

---

## 14.5. Cancel Activity

```http
POST /api/v1/activities/{activity_id}/cancel
```

Request:

```json
{
  "reason": "Khách hủy lịch"
}
```

---

# 15. APPOINTMENT API

## 15.1. List Appointments

```http
GET /api/v1/appointments
```

---

## 15.2. Create Appointment

```http
POST /api/v1/appointments
```

Request:

```json
{
  "customer_id": "uuid",
  "deal_id": "uuid",
  "property_id": "uuid",
  "appointment_type": "site_visit",
  "start_at": "2026-06-02T09:00:00Z",
  "end_at": "2026-06-02T10:00:00Z",
  "location": "Dự án Anzen",
  "note": "Khách đi cùng vợ"
}
```

---

## 15.3. Update Appointment Status

```http
POST /api/v1/appointments/{appointment_id}/status
```

Request:

```json
{
  "status": "completed",
  "result": "Khách thích căn nhưng muốn giảm giá"
}
```

---

# 16. MARKETING API

## 16.1. List Campaigns

```http
GET /api/v1/marketing/campaigns
```

Filters:

```text
platform
status
project_id
date_from
date_to
```

---

## 16.2. Create Campaign

```http
POST /api/v1/marketing/campaigns
```

Request:

```json
{
  "name": "Facebook Lead Gen - Anzen",
  "platform": "facebook",
  "project_id": "uuid",
  "budget": 50000000,
  "start_date": "2026-06-01",
  "end_date": "2026-06-30",
  "status": "running"
}
```

---

## 16.3. Update Campaign

```http
PUT /api/v1/marketing/campaigns/{campaign_id}
```

---

## 16.4. List Adsets

```http
GET /api/v1/marketing/adsets
```

---

## 16.5. Create Adset

```http
POST /api/v1/marketing/adsets
```

---

## 16.6. List Ads

```http
GET /api/v1/marketing/ads
```

---

## 16.7. Create Ad

```http
POST /api/v1/marketing/ads
```

---

## 16.8. Marketing Dashboard

```http
GET /api/v1/marketing/dashboard
```

Response:

```json
{
  "success": true,
  "data": {
    "total_spend": 50000000,
    "total_leads": 1000,
    "cpl": 50000,
    "appointments": 120,
    "deposits": 20,
    "deals": 10,
    "revenue": 30000000000,
    "roi": 5.2
  }
}
```

---

# 17. FILE API

## 17.1. Upload File

```http
POST /api/v1/files/upload
```

Content-Type:

```text
multipart/form-data
```

Fields:

```text
file
entity_type
entity_id
file_category
```

Example categories:

* customer_document
* property_image
* property_video
* legal_document
* deposit_receipt
* contract
* payment_proof

---

## 17.2. List Files By Entity

```http
GET /api/v1/files
```

Filters:

```text
entity_type
entity_id
file_category
```

---

## 17.3. Delete File

```http
DELETE /api/v1/files/{file_id}
```

Soft delete.

---

# 18. NOTE API

## 18.1. List Notes

```http
GET /api/v1/notes
```

Filters:

```text
entity_type
entity_id
```

---

## 18.2. Create Note

```http
POST /api/v1/notes
```

Request:

```json
{
  "entity_type": "customer",
  "entity_id": "uuid",
  "content": "Khách muốn căn view biển, tài chính khoảng 4 tỷ",
  "visibility": "internal"
}
```

---

## 18.3. Delete Note

```http
DELETE /api/v1/notes/{note_id}
```

Rules:

* User chỉ xóa note của mình nếu chưa bị khóa.
* Admin xóa được toàn bộ.

---

# 19. TAG API

## 19.1. List Tags

```http
GET /api/v1/tags
```

---

## 19.2. Create Tag

```http
POST /api/v1/tags
```

Request:

```json
{
  "name": "Khách nóng",
  "color": "#EF4444",
  "entity_type": "customer"
}
```

---

# 20. WORKFLOW API

## 20.1. List Workflows

```http
GET /api/v1/workflows
```

---

## 20.2. Create Workflow

```http
POST /api/v1/workflows
```

Request:

```json
{
  "name": "Auto create call task for new lead",
  "entity_type": "lead",
  "trigger_event": "lead.assigned",
  "is_active": true,
  "priority": 10,
  "rules": [
    {
      "conditions": [
        {
          "field": "status",
          "operator": "equals",
          "value": "assigned"
        }
      ],
      "actions": [
        {
          "type": "create_activity",
          "config": {
            "activity_type": "call",
            "due_in_minutes": 15,
            "title": "Gọi điện cho lead mới"
          }
        }
      ]
    }
  ]
}
```

---

## 20.3. Update Workflow

```http
PUT /api/v1/workflows/{workflow_id}
```

---

## 20.4. Activate Workflow

```http
POST /api/v1/workflows/{workflow_id}/activate
```

---

## 20.5. Deactivate Workflow

```http
POST /api/v1/workflows/{workflow_id}/deactivate
```

---

## 20.6. Test Workflow

```http
POST /api/v1/workflows/{workflow_id}/test
```

---

# 21. STATE MACHINE API

## 21.1. List States

```http
GET /api/v1/states/{entity_type}
```

---

## 21.2. List Transitions

```http
GET /api/v1/states/{entity_type}/transitions
```

---

## 21.3. Create Transition

```http
POST /api/v1/states/{entity_type}/transitions
```

Request:

```json
{
  "from_state": "negotiation",
  "to_state": "deposit",
  "required_fields": ["deposit_amount", "deposit_date"],
  "required_permission": "deals.update_stage"
}
```

---

## 21.4. Transition Entity

```http
POST /api/v1/entities/{entity_type}/{entity_id}/transition
```

Request:

```json
{
  "to_state": "deposit",
  "reason": "Khách đã đặt cọc",
  "data": {
    "deposit_amount": 100000000
  }
}
```

---

# 22. SLA API

## 22.1. List SLA Policies

```http
GET /api/v1/sla-policies
```

---

## 22.2. Create SLA Policy

```http
POST /api/v1/sla-policies
```

Request:

```json
{
  "name": "Lead mới phải gọi trong 15 phút",
  "entity_type": "lead",
  "start_event": "lead.assigned",
  "target_minutes": 15,
  "warning_minutes": 10,
  "escalation_minutes": 30,
  "reclaim_minutes": 60,
  "is_active": true
}
```

---

## 22.3. List SLA Instances

```http
GET /api/v1/sla-instances
```

Filters:

```text
entity_type
status
breached
assigned_user_id
```

---

# 23. NOTIFICATION API

## 23.1. List Notifications

```http
GET /api/v1/notifications
```

Filters:

```text
is_read
priority
type
```

---

## 23.2. Mark Notification Read

```http
POST /api/v1/notifications/{notification_id}/read
```

---

## 23.3. Mark All Read

```http
POST /api/v1/notifications/read-all
```

---

# 24. REPORT API

## 24.1. CEO Dashboard

```http
GET /api/v1/reports/ceo-dashboard
```

Response:

```json
{
  "success": true,
  "data": {
    "total_leads": 1200,
    "new_leads_today": 50,
    "total_customers": 1000,
    "active_deals": 120,
    "closed_won_deals": 30,
    "revenue": 90000000000,
    "commission_total": 1800000000,
    "available_properties": 300,
    "sold_properties": 80
  }
}
```

---

## 24.2. Sales Funnel Report

```http
GET /api/v1/reports/sales-funnel
```

Filters:

```text
date_from
date_to
team_id
owner_user_id
project_id
source
```

---

## 24.3. Sale Performance Report

```http
GET /api/v1/reports/sale-performance
```

---

## 24.4. Team Performance Report

```http
GET /api/v1/reports/team-performance
```

---

## 24.5. Marketing ROI Report

```http
GET /api/v1/reports/marketing-roi
```

---

## 24.6. Inventory Report

```http
GET /api/v1/reports/inventory
```

---

## 24.7. Deal Report

```http
GET /api/v1/reports/deals
```

---

## 24.8. Commission Report

```http
GET /api/v1/reports/commissions
```

---

## 24.9. Overdue Customers Report

```http
GET /api/v1/reports/overdue-customers
```

---

## 24.10. Forecast Report

```http
GET /api/v1/reports/forecast
```

---

# 25. EXPORT API

## 25.1. Export Customers

```http
GET /api/v1/exports/customers
```

Response:

```json
{
  "success": true,
  "data": {
    "download_url": "/api/v1/downloads/export-customers-20260531.xlsx"
  }
}
```

---

## 25.2. Export Properties

```http
GET /api/v1/exports/properties
```

---

## 25.3. Export Deals

```http
GET /api/v1/exports/deals
```

---

## 25.4. Export Reports

```http
GET /api/v1/exports/reports/{report_type}
```

Formats:

```text
xlsx
csv
pdf
```

---

# 26. IMPORT API

## 26.1. Download Customer Import Template

```http
GET /api/v1/import-templates/customers
```

---

## 26.2. Download Property Import Template

```http
GET /api/v1/import-templates/properties
```

---

## 26.3. Preview Import

```http
POST /api/v1/imports/preview
```

Content-Type:

```text
multipart/form-data
```

Fields:

```text
file
entity_type
```

Response:

```json
{
  "success": true,
  "data": {
    "valid_rows": 95,
    "invalid_rows": 5,
    "duplicates": 10,
    "errors": [
      {
        "row": 12,
        "field": "phone_primary",
        "message": "Invalid phone number"
      }
    ]
  }
}
```

---

## 26.4. Confirm Import

```http
POST /api/v1/imports/confirm
```

Request:

```json
{
  "import_session_id": "uuid"
}
```

---

# 27. AUDIT LOG API

## 27.1. List Audit Logs

```http
GET /api/v1/audit-logs
```

Filters:

```text
user_id
action
entity_type
entity_id
created_from
created_to
```

---

## 27.2. Get Audit Log Detail

```http
GET /api/v1/audit-logs/{audit_log_id}
```

---

# 28. MASTER DATA API

## 28.1. List Master Data

```http
GET /api/v1/master-data/{type}
```

Types:

```text
customer_status
lead_status
deal_stage
property_status
payment_status
commission_status
lead_source
lost_reason
property_type
project_status
activity_type
appointment_type
```

---

## 28.2. Create Master Data Item

```http
POST /api/v1/master-data/{type}
```

Request:

```json
{
  "name": "Khách nóng",
  "code": "hot",
  "sort_order": 1,
  "is_active": true
}
```

---

## 28.3. Update Master Data Item

```http
PUT /api/v1/master-data/{type}/{item_id}
```

---

# 29. SEARCH API

## 29.1. Global Search

```http
GET /api/v1/search
```

Query:

```text
?q=0987654321
```

Search in:

* Customers
* Leads
* Properties
* Deals
* Projects

Response:

```json
{
  "success": true,
  "data": {
    "customers": [],
    "leads": [],
    "properties": [],
    "deals": [],
    "projects": []
  }
}
```

---

# 30. DASHBOARD REALTIME API

## 30.1. Realtime Summary

```http
GET /api/v1/dashboard/realtime
```

Response:

```json
{
  "success": true,
  "data": {
    "new_leads_today": 20,
    "calls_today": 150,
    "appointments_today": 15,
    "site_visits_today": 8,
    "deposits_today": 2,
    "overdue_tasks": 30
  }
}
```

---

## 30.2. WebSocket Events

```text
/ws/notifications
/ws/dashboard
```

Events:

```json
{
  "event": "lead.assigned",
  "data": {
    "lead_id": "uuid",
    "assigned_user_id": "uuid"
  }
}
```

---

# 31. API SECURITY REQUIREMENTS

## 31.1. Required Middleware

Backend phải có middleware/dependency:

```python
get_current_user()
require_auth()
require_permission(permission_key)
apply_data_scope(query, entity_type, current_user)
check_object_access(entity_type, entity_id, current_user)
write_audit_log()
```

---

## 31.2. Object Access

Không API detail nào được trả dữ liệu nếu user không có quyền object đó.

Ví dụ:

```http
GET /customers/{id}
```

Nếu Sale không sở hữu customer:

```json
{
  "success": false,
  "message": "Forbidden"
}
```

Status:

```text
403 Forbidden
```

---

## 31.3. Export Security

Export phải có permission riêng.

Không tự động cho export chỉ vì user xem được dữ liệu.

---

## 31.4. Sensitive Data Masking

Nếu user không có quyền xem đầy đủ thông tin:

```json
{
  "phone_primary": "098****321",
  "email": "nguyen***@gmail.com"
}
```

---

# 32. VALIDATION RULES

## 32.1. Phone

* Normalize số điện thoại trước khi lưu.
* Không cho trùng phone_primary.
* Cho phép cảnh báo nếu phone_secondary trùng.

---

## 32.2. Price

* Giá phải >= 0.
* final_price không được nhỏ hơn 0.
* deposit_amount không được lớn hơn final_price.

---

## 32.3. Deal Stage

* Không cho nhảy stage sai.
* Stage quan trọng phải có required fields.

---

## 32.4. Property

* property_code unique trong cùng project.
* Không cho tạo deal active với property sold.
* Không cho 2 deal deposit active trên cùng property.

---

# 33. ACCEPTANCE CRITERIA

## 33.1. Authentication

* User login thành công nhận access_token.
* User không có token bị 401.
* User không đủ quyền bị 403.

---

## 33.2. Customers

* Sale chỉ thấy khách của mình.
* Leader thấy khách team mình.
* Admin thấy toàn bộ khách.
* Không tạo được khách trùng phone_primary.
* Cập nhật customer phải ghi audit log.

---

## 33.3. Leads

* Lead import từ marketing tự kiểm tra trùng.
* Lead mới được tạo SLA.
* Lead có thể assign/reclaim theo quyền.

---

## 33.4. Properties

* Import được bảng hàng.
* Lọc được theo dự án, giá, diện tích, phòng ngủ, trạng thái.
* Đổi giá ghi price history.
* Đổi trạng thái ghi status history.

---

## 33.5. Deals

* Tạo deal từ customer và property.
* Chuyển stage phải đúng workflow.
* Deposit tự đổi property.status = deposited.
* Closed won tự đổi property.status = sold.
* Closed lost bắt buộc có lost_reason.

---

## 33.6. Reports

* Báo cáo tự lọc theo data scope.
* Sale không xem được báo cáo team khác.
* Director/Admin xem được toàn bộ.

---

# 34. IMPLEMENTATION ORDER FOR CODEX

Khuyến nghị triển khai API theo thứ tự:

1. Auth API
2. User/Role/Permission API
3. Customer API
4. Lead API
5. Project API
6. Property API
7. Deal API
8. Activity API
9. Payment API
10. Commission API
11. Marketing API
12. File API
13. Workflow API
14. Report API
15. Export/Import API
16. Audit Log API
17. Realtime/WebSocket API

---

# 35. CONCLUSION

API_SPEC.md là tài liệu định nghĩa toàn bộ cổng giao tiếp giữa frontend và backend.

Khi code, Codex cần đảm bảo:

* API thống nhất format response.
* Có phân trang, filter, sort.
* Có JWT authentication.
* Có RBAC permission.
* Có data scope.
* Có object access control.
* Có audit log.
* Có validation nghiệp vụ.
* Không để frontend quyết định quyền.
* Không trả dữ liệu vượt quyền.

Đây là nền tảng để xây hệ thống CRM bất động sản có thể mở rộng từ 5 sale lên 50–500 sale.

## Sprint 16 Payment Management API

- `GET /api/v1/payment-schedules`: danh sách lịch thanh toán, filter `contract_id`, `deal_id`, `customer_id`, `status`, `overdue`, search `q`.
- `POST /api/v1/payment-schedules`: tạo lịch thanh toán theo Contract.
- `GET /api/v1/payment-schedules/{id}` / `PATCH /api/v1/payment-schedules/{id}` / `POST /api/v1/payment-schedules/{id}/cancel`.
- `POST /api/v1/payment-schedules/{id}/apply-penalty`: áp dụng phí phạt thủ công.
- `POST /api/v1/payment-schedules/{id}/receipts` / `GET /api/v1/payment-schedules/{id}/receipts`.
- `POST /api/v1/receipts/{id}/confirm` / `POST /api/v1/receipts/{id}/cancel`.
- `POST /api/v1/payment-schedules/{id}/invoice`: tạo invoice stub.
- `GET /api/v1/contracts/{id}/payment-schedules` và `GET /api/v1/contracts/{id}/payment-summary`.

## Sprint 17 — Receipt, Invoice & Contract Completion
- Bổ sung quản lý phiếu thu với danh sách/chi tiết, xác nhận, hủy có lý do bắt buộc và bản in bằng trình duyệt.
- Bổ sung quản lý hóa đơn/chứng từ với trạng thái Nháp / Đã phát hành / Đã hủy, tạo từ lịch thanh toán hoặc phiếu thu đã xác nhận, phát hành, hủy có lý do và bản in bằng trình duyệt.
- Hoàn tất hợp đồng chỉ được phép khi tiền cọc cộng tổng phiếu thu đã xác nhận của các lịch thanh toán chưa hủy đạt tối thiểu giá trị hợp đồng; nếu thiếu tiền, API trả lỗi tiếng Việt và không ghi timeline.
- Khi hợp đồng đã hoàn tất hoặc đã hủy, hệ thống chặn tạo mới lịch thanh toán, phiếu thu và hóa đơn; các dữ liệu tài chính cũ vẫn xem và in được.
- Giới hạn hiện tại: bản in phiếu thu/hóa đơn dùng `window.print()` của trình duyệt, chưa sinh PDF binary phía server.

## Sprint 18 — Finance Reports, Receivable Aging & Revenue Dashboard

Sprint 18 thêm hệ thống báo cáo tài chính tại frontend route `/reports/finance`, gồm KPI tổng quan, Công nợ hợp đồng, PMT quá hạn, Dòng tiền đã thu và Hóa đơn.

API mới:
- `GET /api/v1/reports/finance/summary`
- `GET /api/v1/reports/finance/receivables`
- `GET /api/v1/reports/finance/overdue-payments`
- `GET /api/v1/reports/finance/cash-collection`
- `GET /api/v1/reports/finance/invoices`
- `GET /api/v1/reports/finance/receivables/export`
- `GET /api/v1/reports/finance/overdue-payments/export`
- `GET /api/v1/reports/finance/cash-collection/export`
- `GET /api/v1/reports/finance/invoices/export`

Permissions:
- `reports.view.finance`: xem báo cáo tài chính; không có quyền thì backend trả 403 và frontend hiển thị “Bạn không có quyền xem báo cáo tài chính.”
- `reports.export`: xuất CSV báo cáo tài chính; không có quyền thì backend trả 403 và frontend ẩn nút xuất.
- Admin/superuser có toàn quyền xem và export.

Business rules Sprint 18:
- `receipt confirmed` mới tính vào đã thu.
- `receipt cancelled` không tính vào đã thu, KPI dòng tiền hay công nợ.
- `invoice issued` mới tính tổng hóa đơn phát hành.
- `invoice draft/cancelled` không tính vào tổng hóa đơn phát hành.
- `PMT overdue = due_date < today AND remaining > 0`; PMT đã paid không xuất hiện trong báo cáo quá hạn.
- Tổng đã thu hợp đồng = tiền cọc + phiếu thu confirmed; còn phải thu = max(contract_value - deposit_value - confirmed_receipts, 0).

Manual QA checklist:
- Admin mở `/reports/finance` thấy menu, KPI, các tab báo cáo và link detail dùng UUID nội bộ.
- Hủy phiếu thu làm giảm số đã thu và tăng còn phải thu.
- PMT quá hạn còn nợ xuất hiện, PMT paid không xuất hiện.
- Invoice issued được tính; invoice draft/cancelled không được tính.
- CSV tải được, có UTF-8 BOM để Excel đọc tiếng Việt.
- User không có `reports.view.finance` không thấy menu và bị chặn 403 khi gọi API.
- User có quyền xem nhưng không có `reports.export` xem được báo cáo nhưng không thấy nút xuất CSV.

## Sprint 19 — Sales Commission, Revenue Attribution & Performance Report

Sprint 19 adds dynamic reporting for sales commission and revenue attribution without creating payroll, accounting, commission payout, or multi-level approval workflows.

### Business rules
- Default `commission_rate_percent` is `1` (1%). API validates the rate from 0 to 100 and uses it only for report-time calculation.
- `estimated_commission = contract_value × commission_rate`.
- `confirmed_receipts_amount` includes only confirmed receipts; cancelled receipts are excluded.
- `total_collected_with_deposit = deposit_value + confirmed_receipts_amount`.
- `collected_commission = total_collected_with_deposit × commission_rate`.
- `eligible_commission = estimated_commission` only when the contract is completed or collected enough to cover contract value.
- Cancelled contracts are never commission eligible.
- Invoice data does not decide actual collected revenue or commission; invoices are evidence documents only.
- Detail links must use the internal UUID (`contract_id`) and display `contract_code` separately.

### API
- `GET /api/v1/reports/commissions/summary`
- `GET /api/v1/reports/commissions`
- `GET /api/v1/reports/revenue/by-sale`
- `GET /api/v1/reports/revenue/by-source`
- `GET /api/v1/reports/revenue/by-project`
- `GET /api/v1/reports/commissions/export`
- `GET /api/v1/reports/revenue/by-sale/export`
- `GET /api/v1/reports/revenue/by-source/export`
- `GET /api/v1/reports/revenue/by-project/export`

CSV exports use UTF-8 BOM, Vietnamese headers, raw numeric amounts, and filenames for sales commission, revenue by sale, revenue by lead source, and revenue by project/property.

### Permissions
- `reports.view.commissions`: required for commission summary/detail endpoints and `/reports/commissions` UI.
- `reports.view.revenue`: required for revenue attribution endpoints/tabs.
- `reports.export`: reused for all Sprint 19 CSV exports.
- Superuser/admin bypass remains available through the existing permission pattern.

### Frontend
- New route: `/reports/commissions`.
- New sidebar menu: “Báo cáo hoa hồng”.
- Page includes KPI cards, filters, four tabs (Hoa hồng, Doanh thu theo sale, Doanh thu theo nguồn, Doanh thu theo dự án), per-tab CSV export, loading/error/empty states, and “Hướng dẫn sử dụng” modal.

### Manual QA checklist
1. Admin sees menu “Báo cáo hoa hồng” and opens `/reports/commissions`.
2. KPI cards and all four tabs render.
3. Contract value 10,000 + deposit 2,000 + confirmed receipt 3,000 at 1% shows collected 5,000, remaining 5,000, estimated commission 100, collected commission 50, eligible commission 0 unless completed/fully paid.
4. Fully collected or completed contract shows eligible commission equal to contract value × rate.
5. Cancelled receipt reduces collected revenue and collected commission.
6. Cancelled contract shows commission status “Đã hủy” and eligible commission 0.
7. Revenue by sale/source/project matches contract grouping and collected totals.
8. Each CSV opens in Excel with Vietnamese text and numbers matching UI.
9. Users without view/export permissions are blocked or do not see export buttons.
10. Guide modal opens/closes and explains KPIs, tabs, and business rules.

### Known limitations
- This is a temporary/dynamic report, not payroll or an actual payout ledger.
- No commission payment voucher.
- No multi-person commission split.
- No approval/payment workflow for commissions.

## Sprint 20 — Commission Payout, Approval Workflow & Payment Tracking

Sprint 20 bổ sung nghiệp vụ quản lý hoa hồng thật từ hợp đồng đủ điều kiện: tạo bản ghi hoa hồng, duyệt, tạm giữ, hủy có lý do, đánh dấu đã chi trả, theo dõi timeline thao tác và xuất CSV.

### Quy tắc nghiệp vụ
- Chỉ tạo hoa hồng cho hợp đồng không bị hủy và đã hoàn tất hoặc đã thu đủ tiền.
- Tiền đã thu = tiền cọc hợp đồng + tổng phiếu thu trạng thái `confirmed`.
- Phiếu thu đã hủy không được tính vào điều kiện và số tiền hoa hồng.
- Hóa đơn không quyết định doanh thu thực thu hoặc hoa hồng.
- Hoa hồng đủ điều kiện = giá trị hợp đồng × tỷ lệ hoa hồng snapshot tại thời điểm tạo.
- Chỉ `eligible` hoặc `on_hold` được duyệt; số tiền duyệt không âm và không vượt hoa hồng đủ điều kiện.
- Chỉ `approved` được đánh dấu đã chi trả; số tiền chi trả không âm và không vượt số tiền đã duyệt.
- Chỉ `eligible` hoặc `approved` được tạm giữ và bắt buộc nhập lý do.
- Hoa hồng đã chi trả không được hủy; các trạng thái chưa chi trả khi hủy bắt buộc nhập lý do.
- Nếu dữ liệu phiếu thu thay đổi sau khi hoa hồng đã duyệt/chi trả, Sprint 20 giữ snapshot và chưa tự tạo điều chỉnh.

### API mới
- `GET /api/v1/commissions` — danh sách hoa hồng.
- `GET /api/v1/commissions/summary` — KPI tổng hợp hoa hồng.
- `POST /api/v1/commissions/generate` — tạo/cập nhật snapshot hoa hồng từ hợp đồng đủ điều kiện.
- `GET /api/v1/commissions/{id}` — chi tiết hoa hồng và timeline.
- `POST /api/v1/commissions/{id}/approve` — duyệt hoa hồng.
- `POST /api/v1/commissions/{id}/mark-paid` — đánh dấu đã chi trả.
- `POST /api/v1/commissions/{id}/hold` — tạm giữ hoa hồng.
- `POST /api/v1/commissions/{id}/cancel` — hủy hoa hồng.
- `GET /api/v1/commissions/export` — xuất CSV UTF-8 BOM với header tiếng Việt.

### Permissions mới
- `commissions.view`
- `commissions.create`
- `commissions.approve`
- `commissions.mark_paid`
- `commissions.hold`
- `commissions.cancel`
- `commissions.export`

Admin/superuser được bypass theo cơ chế permission hiện có. User thường cần permission tương ứng để xem/tạo/duyệt/tạm giữ/hủy/đánh dấu chi trả/xuất CSV. Row-level visibility của hoa hồng tuân theo các ràng buộc quyền hiện có nếu được mở rộng; hiện tại luồng Sprint 20 tối thiểu guard theo permission.

### Database
- Bảng `sales_commissions`: snapshot hợp đồng, sale, tỷ lệ hoa hồng, các số tiền eligible/approved/paid, trạng thái, người duyệt, người đánh dấu chi trả, lý do giữ/hủy và ghi chú.
- Bảng `sales_commission_events`: timeline thao tác `generated`, `regenerated`, `approved`, `held`, `cancelled`, `paid`.
- Migration mới: `backend/alembic/versions/20260627_0014_sales_commissions.py`.

### Frontend
- Menu “Hoa hồng”.
- Route `/commissions` cho danh sách, filter, KPI, action buttons theo quyền/trạng thái và modal “Hướng dẫn sử dụng”.
- Route `/commissions/:id` cho chi tiết snapshot, hợp đồng, sale/khách hàng, duyệt, chi trả, lý do/ghi chú và timeline.
- UI tiếng Việt, không dùng `window.alert`, `window.confirm`, `window.prompt`.

### Known limitations
- Chưa phải bảng lương.
- Chưa có phiếu chi kế toán.
- Chưa chia hoa hồng nhiều người.
- Chưa có workflow duyệt nhiều cấp.
- Chưa tự động tạo điều chỉnh hoa hồng khi dữ liệu thu tiền thay đổi sau duyệt/chi trả.

### Sprint 20 UX update — Commission contract search

- `GET /api/v1/commissions/eligible-contracts?keyword=` supports the “Tạo hoa hồng từ hợp đồng” modal.
- Search keyword matches contract code, buyer/customer name, and buyer/customer phone when available.
- Response separates `contract_id` (UUID used by generate request) from `contract_code` (human-readable code shown in UI).
- Each row includes eligibility fields: `is_eligible_for_commission`, `reason`, `has_commission`, contract value, collected amount, remaining amount, contract status, and payment status.
- Frontend must pass `contract_id` to `POST /api/v1/commissions/generate`; contract code is never used as route/request id.

## Sprint 21 — Company Commission Receivable

Sprint 21 bổ sung tầng **Hoa hồng công ty** để quản lý khoản công ty môi giới/phân phối BĐS phải thu từ chủ đầu tư, chủ đất, chủ nhà, đối tác phân phối, khách hàng hoặc bên trả hoa hồng khác. Khoản này khác với **Sales Commission Payout** của Sprint 20: Company commission receivable là tiền công ty phải thu; Sales commission payout là tiền công ty chi nội bộ cho sale.

Các hợp đồng có thêm thông tin vai trò công ty, bên bán thực tế, bên trả hoa hồng, mã hợp đồng/chính sách môi giới và ghi chú căn cứ hoa hồng. Module `/company-commissions` có API list, summary, eligible-contracts, generate, detail, approve, receive, hold, cancel và export CSV. Quyền mới gồm `company_commissions.view`, `company_commissions.create`, `company_commissions.approve`, `company_commissions.receive`, `company_commissions.hold`, `company_commissions.cancel`, `company_commissions.export`.

Sprint 21 chưa thay đổi công thức hoa hồng sale của Sprint 20 và chưa bắt buộc chi hoa hồng sale phải phụ thuộc trạng thái đã nhận hoa hồng công ty. Backlog sprint sau: tính hoa hồng sale từ hoa hồng công ty, chặn/kiểm soát chi hoa hồng sale khi hoa hồng công ty chưa nhận, bổ sung báo cáo hoa hồng công ty theo bên trả hoa hồng, báo cáo công nợ hoa hồng công ty và báo cáo chênh lệch công ty nhận so với sale được chi.
