# Database schema hiện tại

Nguồn chuẩn của tài liệu này là `backend/alembic/versions/` và `backend/app/models/`. Schema hiện tại kết thúc tại revision `20260613_0010`.

## 1. Chuỗi migration

| Revision | Nội dung |
|---|---|
| `20260603_0001` | Auth, RBAC, refresh token, audit log |
| `20260605_0002` | Lead và lead activity |
| `20260606_0003` | Department, team, membership |
| `20260607_0004` | Lead task và appointment |
| `20260608_0005` | Customer 360 và Lead conversion |
| `20260609_0006` | Deal pipeline |
| `20260610_0007` | Customer profile nâng cao, related people |
| `20260611_0008` | Project và Property inventory |
| `20260612_0009` | Booking/reservation/deposit |
| `20260613_0010` | Deal linkage, Contract và Contract Payment |

## 2. Danh sách toàn bộ 28 bảng

### 2.1 Auth và RBAC

1. `roles`: role code/name, timestamps.
2. `permissions`: permission code/module/description.
3. `users`: tài khoản, mật khẩu hash, thông tin cá nhân, trạng thái, superuser và soft delete.
4. `user_roles`: bảng nối User–Role.
5. `role_permissions`: bảng nối Role–Permission.
6. `refresh_tokens`: token hash, thời hạn, thu hồi, thiết bị/IP.
7. `audit_logs`: actor, action, entity, before/after JSON, request metadata.

### 2.2 Lead và hoạt động bán hàng

8. `leads`: hồ sơ Lead, nguồn, nhu cầu, ngân sách, owner/assignment, status/priority, conversion và soft delete.
9. `lead_activities`: timeline Lead.
10. `lead_tasks`: công việc gắn Lead, assignee, due/completion và priority/status.
11. `lead_appointments`: lịch hẹn gắn Lead, assignee, thời gian/địa điểm và completion.

### 2.3 Organization

12. `departments`: phòng ban, manager, trạng thái.
13. `teams`: nhóm, department, leader, trạng thái.
14. `user_organization_memberships`: membership User–Department–Team, cờ primary và hiệu lực.

### 2.4 Customer

15. `customers`: Customer 360, nguồn Lead, owner, contact, profile, finance, scoring, timestamps và soft delete.
16. `customer_activities`: timeline Customer.
17. `customer_related_people`: người liên quan của Customer.

### 2.5 Deal

18. `deals`: Deal pipeline, Customer/Lead/Booking/Property/Project, owner, giá trị, milestone dates, close/lost và soft delete.
19. `deal_activities`: timeline Deal với old/new value và JSON metadata.

### 2.6 Inventory

20. `projects`: dự án, mã/tên/chủ đầu tư/vị trí/status, timestamps và soft delete.
21. `property_units`: sản phẩm BĐS, project tùy chọn, vị trí trong dự án, diện tích, giá, inventory status, owner metadata và soft delete.
22. `property_price_history`: lịch sử đổi trường giá của Property.
23. `property_status_history`: lịch sử đổi inventory status của Property.

### 2.7 Booking

24. `bookings`: Customer–Property booking, nguồn Lead/Deal, assigned user, tiền giữ chỗ/cọc/hoàn, lifecycle và soft delete.
25. `booking_activities`: timeline Booking với context JSON.

### 2.8 Contract và payment

26. `contracts`: Contract liên kết Deal/Booking/Customer/Property/Project, loại/trạng thái, giá trị, ngày, buyer/seller và soft delete.
27. `contract_payments`: khoản thanh toán của Contract, đồng thời lưu Deal/Customer/Property, loại/trạng thái/số tiền/ngày và soft delete.
28. `contract_activities`: timeline Contract với old/new value và metadata JSON.

## 3. Khóa ngoại

### Auth/RBAC

- `users.deleted_by -> users.id`
- `user_roles.user_id -> users.id` (`CASCADE`)
- `user_roles.role_id -> roles.id` (`CASCADE`)
- `role_permissions.role_id -> roles.id` (`CASCADE`)
- `role_permissions.permission_id -> permissions.id` (`CASCADE`)
- `refresh_tokens.user_id -> users.id` (`CASCADE`)
- `audit_logs.user_id -> users.id`

### Organization

- `departments.manager_id -> users.id`
- `teams.department_id -> departments.id`
- `teams.leader_id -> users.id`
- `user_organization_memberships.user_id -> users.id` (`CASCADE`)
- `user_organization_memberships.department_id -> departments.id`
- `user_organization_memberships.team_id -> teams.id`

### Lead/task/appointment

- `leads.owner_id`, `created_by_id`, `assigned_by_id`, `deleted_by -> users.id`
- `leads.converted_customer_id -> customers.id` (được tạo sau khi có bảng Customer)
- `leads.converted_by_id -> users.id`
- `lead_activities.lead_id -> leads.id` (`CASCADE`)
- `lead_activities.user_id -> users.id`
- `lead_tasks.lead_id -> leads.id`
- `lead_tasks.assigned_to_id`, `created_by_id`, `completed_by_id -> users.id`
- `lead_appointments.lead_id -> leads.id`
- `lead_appointments.assigned_to_id`, `created_by_id`, `completed_by_id -> users.id`

### Customer

- `customers.source_lead_id -> leads.id`
- `customers.owner_id`, `created_by_id`, `updated_by_id`, `deleted_by_id -> users.id`
- `customer_activities.customer_id -> customers.id` (`CASCADE`)
- `customer_activities.user_id -> users.id`
- `customer_related_people.customer_id -> customers.id` (`CASCADE`)
- `customer_related_people.created_by_id -> users.id`

### Deal

- `deals.customer_id -> customers.id`
- `deals.source_lead_id -> leads.id`
- `deals.owner_id`, `created_by_id`, `assigned_by_id`, `deleted_by_id -> users.id`
- `deals.booking_id -> bookings.id`
- `deals.property_unit_id -> property_units.id`
- `deals.project_id -> projects.id`
- `deal_activities.deal_id -> deals.id` (`CASCADE`)
- `deal_activities.user_id -> users.id`

### Inventory

- `projects.created_by_id`, `updated_by_id`, `deleted_by_id -> users.id`
- `property_units.project_id -> projects.id`
- `property_units.created_by_id`, `updated_by_id`, `deleted_by_id -> users.id`
- `property_price_history.property_unit_id -> property_units.id` (`CASCADE`)
- `property_price_history.changed_by_id -> users.id`
- `property_status_history.property_unit_id -> property_units.id` (`CASCADE`)
- `property_status_history.changed_by_id -> users.id`

### Booking

- `bookings.customer_id -> customers.id`
- `bookings.property_unit_id -> property_units.id`
- `bookings.source_lead_id -> leads.id`
- `bookings.source_deal_id -> deals.id`
- `bookings.assigned_user_id`, `created_by_id`, `updated_by_id`, `deleted_by_id -> users.id`
- `booking_activities.booking_id -> bookings.id` (`CASCADE`)
- `booking_activities.actor_id -> users.id`

### Contract/payment

- `contracts.deal_id -> deals.id`
- `contracts.booking_id -> bookings.id`
- `contracts.customer_id -> customers.id`
- `contracts.property_unit_id -> property_units.id`
- `contracts.project_id -> projects.id`
- `contracts.created_by_id`, `updated_by_id`, `deleted_by_id -> users.id`
- `contract_payments.contract_id -> contracts.id`
- `contract_payments.deal_id -> deals.id`
- `contract_payments.customer_id -> customers.id`
- `contract_payments.property_unit_id -> property_units.id`
- `contract_payments.created_by_id`, `updated_by_id`, `deleted_by_id -> users.id`
- `contract_activities.contract_id -> contracts.id` (`CASCADE`)
- `contract_activities.actor_id -> users.id`

## 4. Quan hệ nghiệp vụ chính

```text
Lead 0..1 -> Customer
Customer 1 -> many Deals
Customer 1 -> many Bookings
Project 0..1 -> many PropertyUnits
PropertyUnit 1 -> many Bookings
Booking 0..1 -> many Deals (application chặn nhiều active Deal)
Deal 1 -> many Contracts (application chặn nhiều active Contract)
Contract 1 -> many ContractPayments

Lead/Customer/Deal/Booking/Contract/Property
  -> các bảng activity/history tương ứng
```

## 5. Ràng buộc và index đáng chú ý

- Các mã nghiệp vụ là unique: Lead code, Customer code, Deal code, Project code, Property code, Booking code, Contract code, Payment code.
- Booking có partial unique index cho một booking active trên mỗi Property với các trạng thái `draft`, `reserved`, `deposited`.
- Deals có index theo `booking_id`, `property_unit_id`, `project_id`; có composite index phục vụ active Deal theo Booking/Property và soft delete.
- Contracts và payments có index theo các FK, status, ngày nghiệp vụ và `deleted_at`.
- Activity/history có index theo aggregate, actor/type và `created_at`.
- Nhiều aggregate sử dụng soft delete; query service phải lọc `deleted_at IS NULL`.

## 6. Lưu ý hiện trạng

- Migration `0010` không tạo database sequence cho mã Contract/Payment; service tự sinh mã.
- Không có bảng invoice, tax/VAT, commission, file attachment, e-signature hay generic accounting ledger.
- `remaining_value` được lưu trên Contract lúc tạo, trong khi response totals cũng tính động từ các payment chưa bị xóa.

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

## Sprint 21 — Company Commission Receivable

Sprint 21 bổ sung tầng **Hoa hồng công ty** để quản lý khoản công ty môi giới/phân phối BĐS phải thu từ chủ đầu tư, chủ đất, chủ nhà, đối tác phân phối, khách hàng hoặc bên trả hoa hồng khác. Khoản này khác với **Sales Commission Payout** của Sprint 20: Company commission receivable là tiền công ty phải thu; Sales commission payout là tiền công ty chi nội bộ cho sale.

Các hợp đồng có thêm thông tin vai trò công ty, bên bán thực tế, bên trả hoa hồng, mã hợp đồng/chính sách môi giới và ghi chú căn cứ hoa hồng. Module `/company-commissions` có API list, summary, eligible-contracts, generate, detail, approve, receive, hold, cancel và export CSV. Quyền mới gồm `company_commissions.view`, `company_commissions.create`, `company_commissions.approve`, `company_commissions.receive`, `company_commissions.hold`, `company_commissions.cancel`, `company_commissions.export`.

Sprint 21 chưa thay đổi công thức hoa hồng sale của Sprint 20 và chưa bắt buộc chi hoa hồng sale phải phụ thuộc trạng thái đã nhận hoa hồng công ty. Backlog sprint sau: tính hoa hồng sale từ hoa hồng công ty, chặn/kiểm soát chi hoa hồng sale khi hoa hồng công ty chưa nhận, bổ sung báo cáo hoa hồng công ty theo bên trả hoa hồng, báo cáo công nợ hoa hồng công ty và báo cáo chênh lệch công ty nhận so với sale được chi.
