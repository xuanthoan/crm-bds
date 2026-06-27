# PERMISSION_SYSTEM.md

# REAL ESTATE CRM - PERMISSION SYSTEM

Version: 1.0
Status: Draft
Scope: Authentication, Authorization, RBAC, Data Ownership, Team Permission, Audit Control

---

# 1. MỤC TIÊU

Hệ thống phân quyền được thiết kế để đảm bảo:

* Sale chỉ xem và thao tác dữ liệu được giao.
* Leader xem và quản lý dữ liệu của team mình.
* Admin/Giám đốc xem toàn bộ hệ thống.
* Marketing chỉ quản lý Lead, Campaign, báo cáo marketing.
* Kế toán chỉ xem giao dịch, thanh toán, hoa hồng.
* Kho hàng chỉ quản lý dữ liệu dự án, căn hộ, sản phẩm.
* Mọi thao tác quan trọng phải được ghi Audit Log.
* Không cho người dùng truy cập dữ liệu vượt quyền.

---

# 2. NGUYÊN TẮC PHÂN QUYỀN

## 2.1. Role-Based Access Control - RBAC

Mỗi user có một hoặc nhiều vai trò.

Ví dụ:

* Admin
* Director
* Sales Manager
* Leader
* Sale
* Marketing
* Accountant
* Inventory Manager
* Viewer

---

## 2.2. Data Ownership

Mỗi khách hàng, lead, deal, activity phải có người sở hữu.

Ví dụ:

* customer.owner_user_id
* lead.assigned_user_id
* deal.owner_user_id
* activity.created_by

Sale chỉ được xem dữ liệu mình sở hữu hoặc được giao.

---

## 2.3. Team-Based Permission

Leader được xem dữ liệu của các sale thuộc team mình.

Ví dụ:

Leader A quản lý Sale A1, A2, A3.

Leader A được xem:

* Lead của Sale A1, A2, A3
* Khách hàng của Sale A1, A2, A3
* Deal của Sale A1, A2, A3
* Activity của Sale A1, A2, A3

Leader A không được xem dữ liệu Team B.

---

## 2.4. Admin Override

Admin có toàn quyền:

* Xem toàn bộ
* Tạo mới
* Sửa
* Xóa mềm
* Khôi phục
* Phân quyền
* Cấu hình hệ thống

---

## 2.5. Soft Delete

Không xóa cứng dữ liệu kinh doanh.

Các bảng quan trọng phải có:

* deleted_at
* deleted_by

Chỉ Admin được khôi phục hoặc xóa vĩnh viễn nếu hệ thống cho phép.

---

# 3. DANH SÁCH ROLE

## 3.1. Admin

Quản trị toàn bộ hệ thống.

Quyền:

* Quản lý người dùng
* Quản lý vai trò
* Quản lý team
* Quản lý phân quyền
* Xem toàn bộ dữ liệu
* Sửa toàn bộ dữ liệu
* Xóa mềm dữ liệu
* Khôi phục dữ liệu
* Cấu hình Master Data
* Xem Audit Log
* Export toàn bộ dữ liệu

---

## 3.2. Director

Vai trò dành cho Giám đốc/Ban lãnh đạo.

Quyền:

* Xem toàn bộ dashboard
* Xem toàn bộ báo cáo
* Xem toàn bộ khách hàng
* Xem toàn bộ giao dịch
* Xem toàn bộ kho hàng
* Xem toàn bộ hiệu suất sale/team
* Xem doanh thu, hoa hồng, ROI
* Không mặc định được sửa cấu hình hệ thống
* Không mặc định được xóa dữ liệu

---

## 3.3. Sales Manager

Vai trò dành cho Trưởng phòng kinh doanh.

Quyền:

* Xem dữ liệu các team thuộc phòng mình
* Quản lý leader
* Xem KPI sale
* Xem pipeline giao dịch
* Giao lại lead giữa các leader/team
* Duyệt thu hồi khách
* Xem báo cáo doanh số
* Xem báo cáo chăm sóc khách hàng

---

## 3.4. Leader

Vai trò dành cho trưởng nhóm sale.

Quyền:

* Xem dữ liệu team mình
* Giao lead cho sale trong team
* Thu hồi lead bỏ quên
* Xem lịch sử chăm sóc của team
* Xem deal của team
* Xem KPI của team
* Tạo ghi chú nội bộ cho khách/deal
* Không được xem dữ liệu team khác

---

## 3.5. Sale

Vai trò dành cho nhân viên kinh doanh.

Quyền:

* Xem lead được giao
* Xem khách hàng được giao
* Tạo khách hàng mới nếu không trùng
* Cập nhật thông tin khách hàng của mình
* Tạo hoạt động chăm sóc
* Tạo lịch hẹn
* Tạo deal cho khách mình phụ trách
* Cập nhật pipeline deal của mình theo rule hợp lệ
* Xem kho hàng được phép công khai nội bộ
* Không được xem khách của sale khác
* Không được sửa chủ sở hữu khách hàng
* Không được xóa khách hàng
* Không được sửa hoa hồng đã duyệt

---

## 3.6. Marketing

Vai trò dành cho bộ phận marketing.

Quyền:

* Tạo campaign
* Cập nhật campaign
* Import lead từ nguồn marketing
* Xem lead source, campaign, adset, ads
* Xem báo cáo CPL, CPA, CPD, ROI
* Xem trạng thái xử lý lead ở mức tổng quan
* Không được xem chi tiết khách nhạy cảm nếu không được cấp quyền
* Không được sửa deal
* Không được sửa hoa hồng

---

## 3.7. Accountant

Vai trò dành cho kế toán.

Quyền:

* Xem deal đã cọc, đã ký, đã hoàn tất
* Xem thông tin thanh toán
* Cập nhật trạng thái thanh toán
* Cập nhật trạng thái hoa hồng
* Upload chứng từ thanh toán
* Export báo cáo công nợ, hoa hồng
* Không được sửa thông tin khách hàng ngoài phần tài chính
* Không được đổi chủ sở hữu deal
* Không được xóa deal

---

## 3.8. Inventory Manager

Vai trò quản lý kho hàng bất động sản.

Quyền:

* Tạo dự án
* Tạo căn hộ/sản phẩm
* Import bảng hàng
* Cập nhật giá
* Cập nhật trạng thái căn
* Upload ảnh, video, pháp lý
* Xem lịch sử trạng thái kho
* Không được sửa khách hàng
* Không được sửa deal nếu không có quyền bổ sung

---

## 3.9. Viewer

Vai trò chỉ xem.

Quyền:

* Chỉ xem dữ liệu được cấp
* Không được tạo
* Không được sửa
* Không được xóa
* Không được export nếu chưa được cấp quyền riêng

---

# 4. PHẠM VI DỮ LIỆU

## 4.1. Own

User chỉ xem dữ liệu của mình.

Áp dụng cho Sale.

Ví dụ:

* Lead được giao cho mình
* Khách hàng mình phụ trách
* Deal mình tạo
* Activity mình tạo

---

## 4.2. Team

User xem dữ liệu của team mình.

Áp dụng cho Leader.

Ví dụ:

* Lead của sale thuộc team
* Khách hàng của sale thuộc team
* Deal của sale thuộc team

---

## 4.3. Department

User xem dữ liệu của phòng ban.

Áp dụng cho Sales Manager.

---

## 4.4. All

User xem toàn bộ dữ liệu.

Áp dụng cho Admin, Director.

---

# 5. MA TRẬN QUYỀN THEO MODULE

## 5.1. Customers

| Role              | View       | Create | Update       | Delete | Assign    | Export  |
| ----------------- | ---------- | ------ | ------------ | ------ | --------- | ------- |
| Admin             | All        | Yes    | Yes          | Yes    | Yes       | Yes     |
| Director          | All        | No     | No           | No     | No        | Yes     |
| Sales Manager     | Department | Yes    | Yes          | No     | Yes       | Yes     |
| Leader            | Team       | Yes    | Yes          | No     | Team only | Yes     |
| Sale              | Own        | Yes    | Own only     | No     | No        | No      |
| Marketing         | Limited    | No     | No           | No     | No        | Limited |
| Accountant        | Limited    | No     | Finance only | No     | No        | Yes     |
| Inventory Manager | No         | No     | No           | No     | No        | No      |
| Viewer            | Assigned   | No     | No           | No     | No        | No      |

---

## 5.2. Leads

| Role          | View                | Create | Update   | Delete | Assign    | Reclaim |
| ------------- | ------------------- | ------ | -------- | ------ | --------- | ------- |
| Admin         | All                 | Yes    | Yes      | Yes    | Yes       | Yes     |
| Director      | All                 | No     | No       | No     | No        | No      |
| Sales Manager | Department          | Yes    | Yes      | No     | Yes       | Yes     |
| Leader        | Team                | Yes    | Yes      | No     | Team only | Yes     |
| Sale          | Own                 | Yes    | Own only | No     | No        | No      |
| Marketing     | All Marketing Leads | Yes    | Yes      | No     | No        | No      |
| Accountant    | No                  | No     | No       | No     | No        | No      |
| Viewer        | Assigned            | No     | No       | No     | No        | No      |

---

## 5.3. Properties / Inventory

| Role              | View           | Create | Update  | Delete      | Import | Export  |
| ----------------- | -------------- | ------ | ------- | ----------- | ------ | ------- |
| Admin             | All            | Yes    | Yes     | Yes         | Yes    | Yes     |
| Director          | All            | No     | No      | No          | No     | Yes     |
| Sales Manager     | All            | No     | Limited | No          | No     | Yes     |
| Leader            | All            | No     | Limited | No          | No     | Yes     |
| Sale              | Available only | No     | No      | No          | No     | No      |
| Marketing         | Limited        | No     | No      | No          | No     | Limited |
| Accountant        | Limited        | No     | No      | No          | No     | Yes     |
| Inventory Manager | All            | Yes    | Yes     | Soft Delete | Yes    | Yes     |
| Viewer            | Assigned       | No     | No      | No          | No     | No      |

---

## 5.4. Deals

| Role              | View                   | Create | Update                | Delete | Approve            |
| ----------------- | ---------------------- | ------ | --------------------- | ------ | ------------------ |
| Admin             | All                    | Yes    | Yes                   | Yes    | Yes                |
| Director          | All                    | No     | No                    | No     | Yes                |
| Sales Manager     | Department             | Yes    | Yes                   | No     | Yes                |
| Leader            | Team                   | Yes    | Yes                   | No     | Team only          |
| Sale              | Own                    | Yes    | Own only              | No     | No                 |
| Marketing         | Summary only           | No     | No                    | No     | No                 |
| Accountant        | Financial deals        | No     | Finance fields only   | No     | Payment/Commission |
| Inventory Manager | Related inventory only | No     | Inventory status only | No     | No                 |
| Viewer            | Assigned               | No     | No                    | No     | No                 |

---

## 5.5. Activities / Follow-up

| Role          | View         | Create | Update   | Delete |
| ------------- | ------------ | ------ | -------- | ------ |
| Admin         | All          | Yes    | Yes      | Yes    |
| Director      | All          | No     | No       | No     |
| Sales Manager | Department   | Yes    | Yes      | No     |
| Leader        | Team         | Yes    | Yes      | No     |
| Sale          | Own          | Yes    | Own only | No     |
| Marketing     | Limited      | No     | No       | No     |
| Accountant    | Related only | No     | No       | No     |
| Viewer        | Assigned     | No     | No       | No     |

---

## 5.6. Marketing

| Role          | View           | Create | Update | Delete      | Export  |
| ------------- | -------------- | ------ | ------ | ----------- | ------- |
| Admin         | All            | Yes    | Yes    | Yes         | Yes     |
| Director      | All            | No     | No     | No          | Yes     |
| Sales Manager | All            | No     | No     | No          | Yes     |
| Leader        | Team result    | No     | No     | No          | Limited |
| Sale          | Own leads only | No     | No     | No          | No      |
| Marketing     | All            | Yes    | Yes    | Soft Delete | Yes     |
| Accountant    | Cost/ROI only  | No     | No     | No          | Yes     |
| Viewer        | Assigned       | No     | No     | No          | No      |

---

## 5.7. Reports

| Role          | CEO Dashboard  | Sale Report | Team Report | Marketing ROI | Finance  | Export  |
| ------------- | -------------- | ----------- | ----------- | ------------- | -------- | ------- |
| Admin         | Yes            | Yes         | Yes         | Yes           | Yes      | Yes     |
| Director      | Yes            | Yes         | Yes         | Yes           | Yes      | Yes     |
| Sales Manager | Department     | Yes         | Yes         | Yes           | Limited  | Yes     |
| Leader        | No             | Team only   | Team only   | Limited       | No       | Limited |
| Sale          | No             | Own only    | No          | No            | No       | No      |
| Marketing     | Marketing only | No          | No          | Yes           | No       | Yes     |
| Accountant    | Finance only   | No          | No          | Limited       | Yes      | Yes     |
| Viewer        | Assigned       | Assigned    | Assigned    | Assigned      | Assigned | No      |

---

# 6. QUYỀN THEO HÀNH ĐỘNG

## 6.1. Customer Actions

### create_customer

Cho phép:

* Admin
* Sales Manager
* Leader
* Sale

Điều kiện:

* Không trùng số điện thoại.
* Nếu trùng thì không tạo mới, hiển thị cảnh báo.
* Nếu user là Sale thì customer.owner_user_id = current_user.id.

---

### update_customer

Cho phép:

* Admin: mọi khách
* Sales Manager: khách thuộc phòng
* Leader: khách thuộc team
* Sale: khách của mình

Không cho Sale sửa:

* owner_user_id
* assigned_team_id
* source_campaign_id nếu lead đã được marketing ghi nhận
* created_by
* created_at

---

### delete_customer

Cho phép:

* Admin only

Cơ chế:

* Soft delete
* Ghi audit log

---

### transfer_customer_owner

Cho phép:

* Admin
* Sales Manager
* Leader trong team

Không cho Sale tự chuyển khách cho người khác.

---

## 6.2. Lead Actions

### create_lead

Cho phép:

* Admin
* Marketing
* Sales Manager
* Leader
* Sale

---

### assign_lead

Cho phép:

* Admin
* Sales Manager
* Leader

Điều kiện:

* Leader chỉ giao lead cho sale thuộc team mình.
* Sales Manager chỉ giao trong phòng mình.

---

### reclaim_lead

Cho phép:

* Admin
* Sales Manager
* Leader

Điều kiện thu hồi:

* Lead quá hạn SLA.
* Sale không chăm sóc sau số ngày cấu hình.
* Lead bị bỏ quên.
* Leader/Admin thao tác thủ công.

---

## 6.3. Deal Actions

### create_deal

Cho phép:

* Admin
* Sales Manager
* Leader
* Sale

Điều kiện:

* Customer phải thuộc quyền xem của user.
* Property phải ở trạng thái có thể giao dịch.
* Một property không được có nhiều deal active ở trạng thái Deposit/Contract/Sold.

---

### update_deal_stage

Cho phép:

* Admin
* Sales Manager
* Leader
* Sale sở hữu deal

Điều kiện:

* Phải tuân thủ State Transition Control.
* Không cho nhảy trực tiếp từ Lead sang Contract.
* Nếu chuyển sang Deposit thì bắt buộc có số tiền cọc.
* Nếu chuyển sang Contract thì bắt buộc có thông tin hợp đồng.
* Nếu chuyển sang Closed Lost thì bắt buộc chọn lý do mất deal.

---

### approve_deal

Cho phép:

* Admin
* Director
* Sales Manager
* Leader nếu deal thuộc team

---

## 6.4. Inventory Actions

### create_property

Cho phép:

* Admin
* Inventory Manager

---

### update_property_status

Cho phép:

* Admin
* Inventory Manager
* Accountant trong trường hợp liên quan thanh toán
* Leader/Sales Manager chỉ được đề xuất thay đổi, không tự quyết nếu cấu hình yêu cầu duyệt

---

### import_inventory_excel

Cho phép:

* Admin
* Inventory Manager

---

## 6.5. Payment & Commission Actions

### update_payment_status

Cho phép:

* Admin
* Accountant

---

### update_commission_status

Cho phép:

* Admin
* Accountant

---

### view_commission

Cho phép:

* Admin: toàn bộ
* Director: toàn bộ
* Sales Manager: phòng mình
* Leader: team mình
* Sale: hoa hồng của mình
* Accountant: toàn bộ phần tài chính

---

# 7. FIELD-LEVEL PERMISSION

Một số trường nhạy cảm cần phân quyền riêng.

## 7.1. Customer Sensitive Fields

Các trường:

* phone_primary
* phone_secondary
* email
* address
* facebook
* zalo

Quy tắc:

* Sale chỉ thấy đầy đủ thông tin khách của mình.
* Leader thấy đầy đủ thông tin khách team mình.
* Marketing có thể chỉ thấy masked phone nếu chưa được cấp quyền.
* Viewer mặc định thấy dữ liệu bị ẩn một phần.

Ví dụ masked:

* 098****321
* nguyenvan***@gmail.com

---

## 7.2. Financial Fields

Các trường:

* final_price
* deposit_amount
* payment_amount
* commission_amount
* commission_rate

Quy tắc:

* Sale chỉ thấy hoa hồng của mình.
* Leader thấy hoa hồng team mình nếu được cấu hình.
* Accountant/Admin/Director thấy toàn bộ.
* Marketing không thấy thông tin hoa hồng chi tiết.

---

## 7.3. System Fields

Không cho user thường sửa:

* id
* created_at
* created_by
* updated_at
* updated_by
* deleted_at
* deleted_by

---

# 8. DATA ACCESS RULES

## 8.1. Customer Access Rule

User được xem customer nếu:

* user.role = Admin
* hoặc user.role = Director
* hoặc customer.owner_user_id = current_user.id
* hoặc customer.assigned_user_id = current_user.id
* hoặc customer.team_id thuộc team do current_user quản lý
* hoặc current_user có quyền view_all_customers

---

## 8.2. Deal Access Rule

User được xem deal nếu:

* Admin/Director
* hoặc deal.owner_user_id = current_user.id
* hoặc deal.team_id thuộc team user quản lý
* hoặc deal.department_id thuộc phòng user quản lý
* hoặc user là Accountant và deal.stage thuộc nhóm financial

---

## 8.3. Inventory Access Rule

User được xem property nếu:

* property.visibility = public_internal
* hoặc user có quyền inventory.view_all
* hoặc property.created_by = current_user.id
* hoặc property.assigned_team_id = team của user

---

## 8.4. Report Access Rule

Báo cáo phải lọc dữ liệu theo data scope:

* Sale: own
* Leader: team
* Sales Manager: department
* Director/Admin: all

Không được query báo cáo trực tiếp bỏ qua permission scope.

---

# 9. PERMISSION CODE FORMAT

Backend nên dùng permission key dạng:

module.action.scope

Ví dụ:

* customers.view.own
* customers.view.team
* customers.view.all
* customers.create
* customers.update.own
* customers.update.team
* customers.delete
* leads.assign.team
* leads.assign.all
* deals.update_stage.own
* deals.approve.team
* inventory.import
* reports.view.ceo
* reports.export
* settings.manage
* audit_logs.view

---

# 10. DANH SÁCH PERMISSION KEY

## Customers

* customers.view.own
* customers.view.team
* customers.view.department
* customers.view.all
* customers.create
* customers.update.own
* customers.update.team
* customers.update.all
* customers.delete
* customers.transfer_owner
* customers.export

---

## Leads

* leads.view.own
* leads.view.team
* leads.view.department
* leads.view.all
* leads.create
* leads.import
* leads.update.own
* leads.update.team
* leads.update.all
* leads.assign.team
* leads.assign.all
* leads.reclaim.team
* leads.reclaim.all
* leads.delete
* leads.export

---

## Properties / Inventory

* inventory.view.available
* inventory.view.all
* inventory.create_project
* inventory.create_property
* inventory.update_project
* inventory.update_property
* inventory.update_status
* inventory.import
* inventory.export
* inventory.delete

---

## Deals

* deals.view.own
* deals.view.team
* deals.view.department
* deals.view.all
* deals.create
* deals.update.own
* deals.update.team
* deals.update.all
* deals.update_stage
* deals.approve
* deals.delete
* deals.export

---

## Activities

* activities.view.own
* activities.view.team
* activities.view.all
* activities.create
* activities.update.own
* activities.update.team
* activities.delete

---

## Marketing

* marketing.view
* marketing.create_campaign
* marketing.update_campaign
* marketing.delete_campaign
* marketing.import_leads
* marketing.view_roi
* marketing.export

---

## Payments

* payments.view
* payments.create
* payments.update
* payments.approve
* payments.export

---

## Commissions

* commissions.view.own
* commissions.view.team
* commissions.view.all
* commissions.update
* commissions.approve
* commissions.mark_paid
* commissions.export

---

## Reports

* reports.view.own
* reports.view.team
* reports.view.department
* reports.view.all
* reports.view.ceo_dashboard
* reports.view.marketing_roi
* reports.view.finance
* reports.export

---

## Settings

* settings.manage_master_data
* settings.manage_status
* settings.manage_workflow
* settings.manage_permissions
* settings.manage_integrations

---

## Audit Logs

* audit_logs.view
* audit_logs.export

---

# 11. DEFAULT ROLE PERMISSIONS

## Admin

Có toàn bộ permissions.

---

## Director

* customers.view.all
* leads.view.all
* inventory.view.all
* deals.view.all
* activities.view.all
* marketing.view
* marketing.view_roi
* payments.view
* commissions.view.all
* reports.view.all
* reports.view.ceo_dashboard
* reports.view.marketing_roi
* reports.view.finance
* reports.export
* audit_logs.view

---

## Sales Manager

* customers.view.department
* customers.create
* customers.update.department
* customers.transfer_owner
* leads.view.department
* leads.create
* leads.update.department
* leads.assign.all
* leads.reclaim.all
* inventory.view.all
* deals.view.department
* deals.create
* deals.update.department
* deals.update_stage
* deals.approve
* activities.view.department
* activities.create
* reports.view.department
* reports.export

---

## Leader

* customers.view.team
* customers.create
* customers.update.team
* leads.view.team
* leads.create
* leads.update.team
* leads.assign.team
* leads.reclaim.team
* inventory.view.available
* deals.view.team
* deals.create
* deals.update.team
* deals.update_stage
* activities.view.team
* activities.create
* reports.view.team

---

## Sale

* customers.view.own
* customers.create
* customers.update.own
* leads.view.own
* leads.create
* leads.update.own
* inventory.view.available
* deals.view.own
* deals.create
* deals.update.own
* deals.update_stage
* activities.view.own
* activities.create
* reports.view.own
* commissions.view.own

---

## Marketing

* leads.view.all
* leads.create
* leads.import
* marketing.view
* marketing.create_campaign
* marketing.update_campaign
* marketing.import_leads
* marketing.view_roi
* marketing.export
* reports.view.marketing_roi
* reports.export

---

## Accountant

* deals.view.all
* payments.view
* payments.create
* payments.update
* payments.approve
* payments.export
* commissions.view.all
* commissions.update
* commissions.approve
* commissions.mark_paid
* commissions.export
* reports.view.finance
* reports.export

---

## Inventory Manager

* inventory.view.all
* inventory.create_project
* inventory.create_property
* inventory.update_project
* inventory.update_property
* inventory.update_status
* inventory.import
* inventory.export
* inventory.delete

---

# 12. LOGIN & AUTHENTICATION

## 12.1. Authentication

Hệ thống sử dụng:

* Email + Password
* JWT Access Token
* Refresh Token

---

## 12.2. Password Policy

Mật khẩu tối thiểu:

* 8 ký tự
* Có chữ hoa
* Có chữ thường
* Có số
* Có ký tự đặc biệt

---

## 12.3. Account Status

User có trạng thái:

* active
* inactive
* suspended
* resigned

User inactive/suspended/resigned không được đăng nhập.

---

## 12.4. Session

* Access token hết hạn ngắn.
* Refresh token hết hạn dài hơn.
* Cho phép logout một thiết bị.
* Cho phép logout toàn bộ thiết bị.

---

# 13. SECURITY RULES

## 13.1. Không tin dữ liệu từ frontend

Backend luôn phải kiểm tra:

* User là ai
* Role là gì
* Permission gì
* Data scope gì
* Object có thuộc quyền user không

---

## 13.2. API bắt buộc kiểm tra quyền

Mọi API quan trọng đều phải qua middleware hoặc dependency:

* require_permission()
* apply_data_scope()
* check_object_access()

---

## 13.3. Không trả dữ liệu vượt quyền

Ngay cả khi frontend ẩn nút, backend vẫn phải chặn.

---

## 13.4. Export phải kiểm tra quyền riêng

Không tự động cho export chỉ vì user xem được dữ liệu.

---

# 14. AUDIT LOG

Các hành động bắt buộc ghi log:

* Login
* Logout
* Tạo khách hàng
* Sửa khách hàng
* Xóa khách hàng
* Chuyển chủ sở hữu khách hàng
* Import dữ liệu
* Export dữ liệu
* Tạo deal
* Đổi trạng thái deal
* Sửa giá
* Sửa tiền cọc
* Sửa hoa hồng
* Đổi trạng thái kho hàng
* Đổi phân quyền
* Đổi cấu hình workflow

Thông tin log:

* user_id
* action
* entity_type
* entity_id
* before_data
* after_data
* ip_address
* user_agent
* created_at

---

# 15. UI PERMISSION RULES

Frontend phải ẩn hoặc disable nút theo quyền.

Ví dụ:

Sale không thấy:

* Nút xóa khách
* Nút chuyển khách
* Nút export toàn bộ
* Nút sửa hoa hồng
* Nút cấu hình hệ thống

Leader thấy:

* Nút giao lead trong team
* Nút thu hồi lead team
* Báo cáo team

Admin thấy toàn bộ.

Lưu ý:

Frontend chỉ hỗ trợ trải nghiệm người dùng. Backend vẫn là nơi quyết định quyền cuối cùng.

---

# 16. ACCEPTANCE CRITERIA

## 16.1. Sale

* Sale đăng nhập chỉ thấy khách của mình.
* Sale không truy cập được URL khách của sale khác.
* Sale không export được toàn bộ khách hàng.
* Sale không sửa được owner_user_id.
* Sale không xóa được khách hàng.

---

## 16.2. Leader

* Leader thấy toàn bộ khách của team mình.
* Leader không thấy dữ liệu team khác.
* Leader giao lead được cho sale thuộc team.
* Leader không giao lead cho sale ngoài team.

---

## 16.3. Admin

* Admin thấy toàn bộ dữ liệu.
* Admin phân quyền được user.
* Admin xem được audit log.
* Admin khôi phục dữ liệu bị xóa mềm.

---

## 16.4. Marketing

* Marketing import lead được.
* Marketing xem báo cáo ROI được.
* Marketing không sửa deal.
* Marketing không sửa hoa hồng.

---

## 16.5. Accountant

* Kế toán cập nhật thanh toán được.
* Kế toán cập nhật hoa hồng được.
* Kế toán không chuyển chủ sở hữu khách hàng.
* Kế toán không xóa deal.

---

# 17. IMPLEMENTATION NOTES FOR CODEX

## Backend

Khi code backend cần tạo:

* users
* roles
* permissions
* role_permissions
* user_roles
* teams
* team_members
* departments
* user_sessions
* audit_logs

---

## Permission Middleware

Cần xây:

* get_current_user()
* require_auth()
* require_permission(permission_key)
* get_user_data_scope(user)
* apply_scope_filter(query, entity, user)
* check_object_access(entity, object_id, user)

---

## Data Scope

Mọi query danh sách phải tự động lọc theo scope.

Ví dụ:

Sale gọi GET /customers

Kết quả chỉ trả customers.owner_user_id = current_user.id.

---

## Object Access

Mọi API xem chi tiết phải kiểm tra quyền.

Ví dụ:

Sale gọi GET /customers/{id}

Nếu customer.owner_user_id khác current_user.id thì trả:

403 Forbidden

---

## Audit

Mọi thay đổi quan trọng phải gọi:

create_audit_log()

---

# 18. KẾT LUẬN

Permission System là nền tảng bảo mật và quản trị của CRM bất động sản.

Hệ thống bắt buộc phải đảm bảo:

* Đúng người
* Đúng quyền
* Đúng dữ liệu
* Đúng phạm vi
* Có lịch sử kiểm tra
* Không thất thoát dữ liệu khách hàng
* Không để sale xem chéo khách của nhau
* Không để người không có quyền sửa dữ liệu quan trọng

Đây là điều kiện bắt buộc trước khi triển khai các module CRM, Lead, Deal, Inventory, Marketing và Reporting.

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
