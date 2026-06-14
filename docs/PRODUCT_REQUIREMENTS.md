# Product requirements đã được hiện thực hóa

Tài liệu này là mô tả ngược từ code, không phải backlog giả định.

## 1. Mục tiêu sản phẩm hiện tại

CRM hỗ trợ đội bán hàng BĐS quản lý:

1. Lead và lịch sử tương tác.
2. Chuyển Lead đủ điều kiện thành Customer.
3. Hồ sơ Customer và người liên quan.
4. Deal pipeline và người phụ trách.
5. Project/Property inventory.
6. Booking giữ chỗ/đặt cọc.
7. Contract và các khoản thanh toán.
8. Phân quyền theo vai trò và phạm vi tổ chức.

## 2. Persona/role được code hỗ trợ

Role seed/permission map gồm:

- `admin`
- `director`
- `sales_manager`
- `leader`
- `sale`
- `marketing`
- `inventory_manager`
- `viewer`

Quyền thực tế phụ thuộc permission rows và role mappings, không chỉ tên role.

## 3. Yêu cầu chức năng theo module

### Auth và quản trị

- Login bằng email/password.
- Refresh và revoke token.
- Xem/cập nhật profile, đổi mật khẩu.
- CRUD/quản trị users, roles, permissions.
- Quản trị department/team/membership.

### Lead

- Tạo, tìm kiếm, lọc, sửa, soft delete.
- Gán owner theo permission scope.
- Ghi activity.
- Quản lý task và appointment gắn Lead.
- Chuyển Lead thành Customer đúng một lần.

### Customer

- Tạo trực tiếp hoặc từ Lead.
- Quản lý contact/profile/finance/preference.
- Quản lý related people.
- Tính và lưu customer score/tier.
- Hiển thị related Deals/Bookings/Contracts qua service/detail integrations hiện có.

### Deal

- Tạo thủ công từ Customer hoặc tạo từ Booking đã cọc.
- Theo dõi pipeline stage, status, owner, giá trị và timeline.
- Chọn Project/Property có thật từ inventory.
- Tự dẫn xuất thông tin Project/Property từ `property_unit_id`.
- Liên kết Contract và hiển thị Booking/Property/Project.

### Inventory

- CRUD Project.
- CRUD Property.
- Project là tùy chọn đối với Property.
- Theo dõi inventory status và lịch sử thay đổi giá/trạng thái.
- Bảo vệ xóa Project đang còn Property chưa xóa.

### Booking

- Tạo Booking cho Customer + Property + assigned user.
- Chuyển trạng thái giữ chỗ, đặt cọc, hủy, hết hạn, hoàn tiền.
- Đồng bộ inventory status.
- Lưu timeline tiếng Việt.
- Tạo Deal từ Booking đã cọc.

### Contract và Payment

- Tạo Contract từ Deal có Property.
- Dẫn xuất Booking/Customer/Property/Project từ Deal.
- Thay đổi Contract status.
- Đồng bộ signed/active/completed sang Deal/Property.
- Tạo, cập nhật, xác nhận và soft-delete Contract Payment.
- Tính `total_paid`, `total_planned`, `remaining_amount`.
- Lưu Contract timeline và Deal activity khi Contract đổi trạng thái quan trọng.

## 4. Yêu cầu phi chức năng có implementation

- UUID primary keys.
- Soft delete cho các aggregate chính.
- Timestamps có timezone.
- Scoped RBAC.
- Audit log cho các thao tác nghiệp vụ chính.
- Vietnamese labels/messages ở các module nghiệp vụ mới.
- Pagination cho các list API chính.
- Dockerized local environment.

## 5. Ngoài phạm vi code hiện tại

Không có implementation hoàn chỉnh cho invoice, tax/VAT, commission payout, e-signature, payment gateway, file upload contract, workflow engine, background notifications hoặc advanced revenue reporting.

## 6. Nguồn kiểm chứng

- `backend/app/api/v1/`
- `backend/app/services/`
- `backend/app/schemas/`
- `backend/app/permissions/constants.py`
- `frontend/src/routes/AppRoutes.tsx`
- `frontend/src/features/`
- `backend/alembic/versions/`
