# UI_UX.md

# REAL ESTATE CRM - UI/UX SPECIFICATION

Version: 1.0
Status: Draft
Frontend Suggested Stack: React + TypeScript + TailwindCSS
Target Users: Admin, Director, Sales Manager, Leader, Sale, Marketing, Accountant, Inventory Manager

---

# 1. MỤC TIÊU UI/UX

Giao diện phần mềm CRM bất động sản cần đạt các mục tiêu:

* Dễ dùng cho sale không rành kỹ thuật.
* Tốc độ thao tác nhanh.
* Tìm kiếm khách hàng/căn hộ/giao dịch nhanh.
* Dữ liệu rõ ràng, dễ lọc, dễ xuất Excel.
* Dashboard giúp lãnh đạo nắm tình hình ngay.
* Mỗi vai trò chỉ nhìn thấy chức năng đúng quyền.
* Sale mở phần mềm là biết hôm nay cần làm gì.
* Leader mở phần mềm là biết sale nào đang yếu.
* Giám đốc mở phần mềm là biết doanh thu, lead, deal, tồn kho, ROI.

---

# 2. NGUYÊN TẮC THIẾT KẾ

## 2.1. Ưu tiên tốc độ thao tác

Các thao tác thường dùng phải nằm ngay trên màn hình:

* Tìm khách
* Thêm khách
* Gọi chăm sóc
* Tạo lịch hẹn
* Tạo deal
* Lọc căn hộ
* Đổi trạng thái deal
* Xem việc quá hạn

---

## 2.2. Dữ liệu phải rõ ràng

Không nhồi quá nhiều thông tin trong một màn hình.

Sử dụng:

* Card
* Table
* Tabs
* Drawer
* Modal
* Badge trạng thái
* Timeline
* Kanban

---

## 2.3. Giao diện theo vai trò

Mỗi role có dashboard riêng:

* Sale Dashboard
* Leader Dashboard
* Marketing Dashboard
* Inventory Dashboard
* Accountant Dashboard
* Director Dashboard
* Admin Dashboard

---

## 2.4. Responsive

Phase 1 ưu tiên Desktop Web.

Kích thước tối ưu:

* 1366px trở lên
* 1920px full HD

Mobile Web chỉ cần xem nhanh:

* Dashboard
* Lead mới
* Nhiệm vụ hôm nay
* Thông báo
* Chi tiết khách

---

# 3. DESIGN SYSTEM

## 3.1. Màu sắc

### Primary

```text
#2563EB
```

Dùng cho:

* Nút chính
* Link
* Active menu
* CTA

---

### Success

```text
#16A34A
```

Dùng cho:

* Đã hoàn thành
* Đã thanh toán
* Đã chốt
* Còn hàng

---

### Warning

```text
#F59E0B
```

Dùng cho:

* Sắp quá hạn
* Cần chú ý
* Đang đàm phán
* Giữ chỗ

---

### Danger

```text
#DC2626
```

Dùng cho:

* Quá hạn
* Hết hàng
* Mất khách
* Hủy deal

---

### Neutral Background

```text
#F5F7FA
```

---

### Card Background

```text
#FFFFFF
```

---

### Border

```text
#E5E7EB
```

---

## 3.2. Typography

Font đề xuất:

```text
Inter hoặc system sans-serif
```

Kích thước:

* Page title: 24px / 28px
* Section title: 18px / 24px
* Body: 14px / 20px
* Small text: 12px / 16px
* Table text: 13px / 18px

---

## 3.3. Spacing

Sử dụng hệ 4px:

* 4px
* 8px
* 12px
* 16px
* 24px
* 32px

---

## 3.4. Border Radius

* Card: 12px
* Button: 8px
* Input: 8px
* Badge: 999px

---

## 3.5. Shadow

Card shadow nhẹ:

```text
0 1px 3px rgba(0,0,0,0.08)
```

---

# 4. LAYOUT TỔNG THỂ

## 4.1. App Shell

Giao diện gồm:

```text
Left Sidebar
Top Header
Main Content
Right Drawer / Modal
```

---

## 4.2. Left Sidebar

Chiều rộng:

```text
260px
```

Menu chính:

* Dashboard
* Lead Center
* Khách hàng
* Kho hàng
* Dự án
* Giao dịch
* Chăm sóc
* Lịch hẹn
* Marketing
* Báo cáo
* Nhân sự
* Hoa hồng
* Thanh toán
* File
* Workflow
* Cài đặt

Menu hiển thị theo quyền.

Ví dụ:

Sale không thấy:

* Workflow
* Cài đặt hệ thống
* Phân quyền
* Báo cáo CEO

---

## 4.3. Top Header

Bao gồm:

* Global Search
* Nút Thêm nhanh
* Notification Bell
* User Menu
* Role Switch nếu user có nhiều role

---

## 4.4. Global Search

Cho phép tìm nhanh:

* Số điện thoại khách
* Tên khách
* Email
* Mã căn
* Tên dự án
* Mã deal

Hiển thị kết quả nhóm theo:

* Khách hàng
* Lead
* Căn hộ
* Giao dịch
* Dự án

---

## 4.5. Quick Create

Nút “+ Tạo nhanh” gồm:

* Tạo khách hàng
* Tạo lead
* Tạo lịch chăm sóc
* Tạo lịch hẹn
* Tạo deal
* Tạo căn hộ

Tùy quyền mà hiển thị.

---

# 5. LOGIN SCREEN

## 5.1. Layout

Màn hình đăng nhập gồm:

* Logo CRM
* Tên hệ thống
* Email
* Password
* Remember me
* Forgot password
* Login button

---

## 5.2. Validation

* Email bắt buộc
* Password bắt buộc
* Sai tài khoản/mật khẩu hiển thị lỗi chung
* User inactive không cho login

---

# 6. DASHBOARD

## 6.1. Dashboard theo vai trò

Sau khi đăng nhập, hệ thống điều hướng đến dashboard phù hợp.

---

# 7. SALE DASHBOARD

Mục tiêu:

Sale mở phần mềm là biết hôm nay phải làm gì.

## 7.1. KPI Cards

Hiển thị:

* Lead mới hôm nay
* Khách cần gọi hôm nay
* Khách quá hạn chăm sóc
* Lịch hẹn hôm nay
* Deal đang theo
* Hoa hồng dự kiến

---

## 7.2. Today Tasks

Danh sách việc cần làm:

* Gọi khách
* Nhắn Zalo
* Gửi bảng hàng
* Hẹn xem nhà
* Follow-up sau xem nhà

Cột:

* Thời hạn
* Khách hàng
* Loại việc
* Độ ưu tiên
* Trạng thái
* Nút hoàn thành

---

## 7.3. Hot Customers

Danh sách khách nóng:

* Tên khách
* Số điện thoại
* Nhu cầu
* Ngân sách
* Lần chăm sóc cuối
* Nút gọi
* Nút ghi chú

---

## 7.4. My Pipeline

Kanban deal cá nhân:

* Contacted
* Qualified
* Appointment
* Site Visit
* Negotiation
* Deposit
* Contract
* Closed Won
* Closed Lost

Cho phép kéo thả nếu user có quyền và transition hợp lệ.

---

# 8. LEADER DASHBOARD

Mục tiêu:

Leader biết team mình đang hoạt động thế nào.

## 8.1. KPI Cards

* Lead team hôm nay
* Lead chưa xử lý
* Khách quá hạn chăm sóc
* Số lịch hẹn
* Số khách xem nhà
* Số cọc
* Doanh thu team
* Tỷ lệ chuyển đổi

---

## 8.2. Team Performance Table

Cột:

* Sale
* Lead nhận
* Lead đã gọi
* Khách nóng
* Việc quá hạn
* Lịch hẹn
* Xem nhà
* Cọc
* Deal
* Doanh thu
* Conversion

---

## 8.3. Alerts

Cảnh báo:

* Sale không xử lý lead đúng SLA
* Sale giữ nhiều khách quá hạn
* Deal sắp mất
* Lead cần thu hồi

---

## 8.4. Lead Reclaim Panel

Danh sách lead có thể thu hồi:

* Lead
* Sale hiện tại
* Thời gian quá hạn
* Lý do
* Nút Thu hồi
* Nút Giao lại

---

# 9. DIRECTOR DASHBOARD

Mục tiêu:

Giám đốc nắm toàn cảnh doanh nghiệp.

## 9.1. Executive KPI Cards

* Tổng lead
* Lead mới hôm nay
* Tổng khách hàng
* Tổng deal active
* Tổng doanh thu
* Hoa hồng phải trả
* Tồn kho còn bán
* ROI marketing

---

## 9.2. Charts

Biểu đồ:

* Doanh thu theo tháng
* Lead theo nguồn
* Funnel bán hàng
* Top dự án doanh thu cao
* Top sale
* Marketing ROI

---

## 9.3. Executive Alerts

Cảnh báo:

* Nguồn marketing đang lỗ
* Team KPI thấp
* Tồn kho nhiều
* Sale bỏ quên khách
* Thanh toán quá hạn
* Hoa hồng chờ duyệt

---

# 10. LEAD CENTER SCREEN

Mục tiêu:

Quản lý toàn bộ lead đầu vào.

## 10.1. Tabs

* Lead mới
* Lead đã giao
* Lead trùng
* Lead rác
* Lead chưa xử lý
* Lead quá SLA
* Lead đã thu hồi

---

## 10.2. Lead Table

Cột:

* Thời gian
* Họ tên
* Số điện thoại
* Nguồn
* Campaign
* Dự án quan tâm
* Trạng thái
* Sale phụ trách
* SLA
* Chất lượng
* Hành động

---

## 10.3. Actions

* Giao lead
* Thu hồi
* Chuyển thành khách hàng
* Đánh dấu rác
* Gộp lead trùng
* Tạo lịch gọi

---

## 10.4. SLA Indicator

Màu:

* Xanh: trong hạn
* Vàng: sắp quá hạn
* Đỏ: quá hạn

---

# 11. CUSTOMER LIST SCREEN

## 11.1. Header

* Title: Khách hàng
* Search box
* Button: Thêm khách hàng
* Button: Import Excel
* Button: Export Excel

Button hiển thị theo quyền.

---

## 11.2. Filters

Bộ lọc:

* Trạng thái
* Mức độ nóng
* Sale phụ trách
* Team
* Nguồn
* Dự án quan tâm
* Ngân sách
* Số phòng ngủ
* Timeline mua
* Tỉnh/Huyện
* Ngày tạo
* Tag

---

## 11.3. Customer Table

Cột:

* Mã khách
* Họ tên
* SĐT
* Nhu cầu
* Ngân sách
* Mức độ nóng
* Trạng thái
* Sale
* Lần chăm sóc cuối
* Việc tiếp theo
* Ngày tạo
* Hành động

---

## 11.4. Row Actions

* Xem chi tiết
* Gọi
* Nhắn Zalo
* Tạo chăm sóc
* Tạo lịch hẹn
* Tạo deal
* Chuyển chủ sở hữu
* Xóa mềm

Tùy quyền.

---

# 12. CUSTOMER DETAIL SCREEN

Mục tiêu:

Customer 360 View.

## 12.1. Header

Hiển thị:

* Tên khách
* Số điện thoại
* Trạng thái
* Temperature
* Sale phụ trách
* Tags
* Nút hành động nhanh

Nút:

* Gọi
* Nhắn Zalo
* Thêm ghi chú
* Tạo việc
* Tạo lịch hẹn
* Tạo deal

---

## 12.2. Layout

Chia 2 cột:

### Left Main Content

* Thông tin khách
* Nhu cầu
* Tài chính
* Giao dịch
* Lịch sử chăm sóc
* Timeline

### Right Sidebar

* Owner
* Tags
* Lead source
* Điểm khách hàng
* Việc sắp tới
* Căn gợi ý
* File đính kèm

---

## 12.3. Tabs

* Tổng quan
* Timeline
* Chăm sóc
* Giao dịch
* Căn phù hợp
* Người liên quan
* Tài chính
* File
* Ghi chú
* Audit Log

---

## 12.4. Timeline UI

Mỗi sự kiện hiển thị:

* Icon
* Thời gian
* Người thực hiện
* Nội dung
* Entity liên quan

Ví dụ:

```text
09:30 31/05/2026 - Sale A gọi điện
Kết quả: Khách quan tâm căn 2PN, hẹn xem nhà.
```

---

# 13. CUSTOMER FORM

## 13.1. Sections

Form chia thành các section:

1. Thông tin cơ bản
2. Liên hệ
3. Nhu cầu
4. Tài chính
5. Nguồn khách
6. Người phụ trách
7. Ghi chú

---

## 13.2. Validation

* Họ tên bắt buộc
* Số điện thoại chính bắt buộc
* Số điện thoại phải hợp lệ
* Không cho trùng số điện thoại
* Ngân sách min không được lớn hơn max

---

## 13.3. Duplicate Warning

Nếu số điện thoại trùng, hiển thị modal:

```text
Khách hàng này có thể đã tồn tại.
Tên: Nguyễn Văn A
Sale phụ trách: Sale B
Trạng thái: Đang tư vấn
Bạn không thể tạo mới nếu không có quyền gộp khách.
```

---

# 14. INVENTORY / PROPERTY LIST SCREEN

## 14.1. Header

* Title: Kho hàng
* Search mã căn
* Button: Thêm căn
* Button: Import bảng hàng
* Button: Export

---

## 14.2. Filters

* Dự án
* Tòa
* Tầng
* Loại căn
* Số phòng ngủ
* Diện tích
* Khoảng giá
* Hướng cửa
* Hướng ban công
* View
* Trạng thái
* Pháp lý
* Hoa hồng

---

## 14.3. Property Table

Cột:

* Mã căn
* Dự án
* Tòa
* Tầng
* Loại
* PN
* Diện tích
* Giá
* Giá/m²
* Hướng
* View
* Hoa hồng
* Trạng thái
* Chủ nhà
* Hành động

---

## 14.4. Property Card View

Ngoài table, có thể có card view:

* Ảnh đại diện
* Mã căn
* Dự án
* Giá
* Diện tích
* PN
* View
* Trạng thái

---

## 14.5. Status Badge

Màu:

* Available: Xanh
* Reserved: Vàng
* Negotiating: Cam
* Deposited: Tím
* Sold: Xám
* Locked: Đỏ
* Off Market: Xám đậm

---

# 15. PROPERTY DETAIL SCREEN

## 15.1. Header

* Mã căn
* Dự án
* Giá
* Trạng thái
* Nút cập nhật trạng thái
* Nút tạo deal

---

## 15.2. Sections

* Thông tin căn
* Giá & hoa hồng
* Vị trí
* Pháp lý
* Chủ sở hữu
* Media
* Lịch sử giá
* Lịch sử trạng thái
* Deal liên quan
* Khách phù hợp

---

## 15.3. Price History Chart

Hiển thị biến động giá theo thời gian.

---

## 15.4. Suggested Customers

Danh sách khách phù hợp với căn:

* Tên khách
* Ngân sách
* Nhu cầu
* Điểm phù hợp
* Sale phụ trách

---

# 16. PROJECT SCREEN

## 16.1. Project List

Cột:

* Mã dự án
* Tên dự án
* Chủ đầu tư
* Khu vực
* Số căn
* Còn hàng
* Đã bán
* Trạng thái

---

## 16.2. Project Detail

Tabs:

* Tổng quan
* Bảng hàng
* Chính sách
* Pháp lý
* Media
* Báo cáo

---

# 17. DEAL PIPELINE SCREEN

## 17.1. Kanban View

Các cột:

* Lead
* Contacted
* Qualified
* Appointment
* Site Visit
* Negotiation
* Booking
* Deposit
* Contract
* Payment
* Closed Won
* Closed Lost

---

## 17.2. Deal Card

Hiển thị:

* Tên khách
* Mã căn
* Dự án
* Giá trị deal
* Sale phụ trách
* Ngày cập nhật cuối
* Nhiệm vụ tiếp theo
* Mức độ nóng

---

## 17.3. Drag & Drop

Cho phép kéo deal sang stage khác nếu:

* User có quyền
* Transition hợp lệ
* Đủ required fields

Nếu thiếu dữ liệu, mở modal yêu cầu nhập.

Ví dụ:

Kéo sang Deposit:

Bắt buộc nhập:

* Số tiền cọc
* Ngày cọc
* File phiếu cọc nếu có

---

# 18. DEAL DETAIL SCREEN

## 18.1. Header

* Mã deal
* Tên khách
* Căn hộ
* Stage
* Giá trị
* Sale
* Nút đổi stage

---

## 18.2. Tabs

* Tổng quan
* Timeline
* Báo giá
* Đàm phán
* Cọc
* Hợp đồng
* Thanh toán
* Hoa hồng
* File
* Ghi chú
* Audit Log

---

## 18.3. Deal Timeline

Hiển thị:

* Tạo deal
* Đổi stage
* Gửi báo giá
* Đặt cọc
* Ký hợp đồng
* Thanh toán
* Chốt thắng/thua

---

## 18.4. Close Lost Modal

Bắt buộc chọn:

* Lý do mất deal
* Ghi chú

---

# 19. ACTIVITY / FOLLOW-UP SCREEN

## 19.1. My Tasks

Tabs:

* Hôm nay
* Sắp tới
* Quá hạn
* Đã hoàn thành

---

## 19.2. Task Table

Cột:

* Thời hạn
* Khách hàng
* Loại việc
* Nội dung
* Deal liên quan
* Trạng thái
* Hành động

---

## 19.3. Complete Task Modal

Fields:

* Kết quả
* Cập nhật trạng thái khách
* Tạo việc tiếp theo
* Ghi chú

---

# 20. APPOINTMENT CALENDAR

## 20.1. Views

* Day
* Week
* Month
* List

---

## 20.2. Appointment Card

Hiển thị:

* Thời gian
* Khách hàng
* Loại lịch hẹn
* Địa điểm
* Sale phụ trách
* Trạng thái

---

## 20.3. Status

* Scheduled
* Confirmed
* Completed
* Rescheduled
* Cancelled
* No Show

---

# 21. MARKETING SCREEN

## 21.1. Marketing Dashboard

Cards:

* Tổng chi phí
* Tổng lead
* CPL
* Appointment
* Deposit
* Deal
* Revenue
* ROI

---

## 21.2. Campaign List

Cột:

* Campaign
* Platform
* Project
* Budget
* Spend
* Lead
* CPL
* Deposit
* Deal
* ROI
* Status

---

## 21.3. Campaign Detail

Tabs:

* Tổng quan
* Adsets
* Ads
* Leads
* Funnel
* ROI

---

# 22. REPORT SCREEN

## 22.1. Report Center

Danh sách báo cáo:

* CEO Dashboard
* Sales Funnel
* Sale Performance
* Team Performance
* Marketing ROI
* Inventory Report
* Deal Report
* Commission Report
* Overdue Customers
* Forecast

---

## 22.2. Report Filter

Filter chung:

* Date range
* Project
* Team
* Sale
* Source
* Campaign

---

## 22.3. Export

Nút export:

* Excel
* CSV
* PDF

Chỉ hiện nếu user có quyền.

---

# 23. COMMISSION SCREEN

## 23.1. Commission List

Cột:

* Deal
* Khách hàng
* Căn hộ
* Sale
* Hoa hồng dự kiến
* Hoa hồng duyệt
* Đã trả
* Còn lại
* Trạng thái

---

## 23.2. Commission Detail

Tabs:

* Tổng quan
* Người hưởng
* Lịch sử thanh toán
* File chứng từ
* Audit Log

---

# 24. PAYMENT SCREEN

## 24.1. Payment List

Cột:

* Deal
* Khách hàng
* Đợt thanh toán
* Số tiền
* Hạn thanh toán
* Đã thanh toán
* Trạng thái
* Quá hạn

---

## 24.2. Payment Detail

Actions:

* Đánh dấu đã thanh toán
* Upload chứng từ
* Ghi chú

---

# 25. FILE MANAGER

## 25.1. File List

Cột:

* Tên file
* Loại
* Entity liên quan
* Người upload
* Ngày upload
* Hành động

---

## 25.2. File Categories

* Customer Document
* Property Image
* Property Video
* Legal Document
* Deposit Receipt
* Contract
* Payment Proof
* Brochure

---

# 26. WORKFLOW BUILDER SCREEN

Chỉ Admin được dùng.

## 26.1. Workflow List

Cột:

* Tên workflow
* Entity
* Trigger
* Trạng thái
* Lần chạy gần nhất
* Hành động

---

## 26.2. Workflow Form

Sections:

* Basic Info
* Trigger
* Conditions
* Actions
* Priority
* Active/Inactive

---

## 26.3. Condition Builder

UI dạng:

```text
IF field operator value
AND field operator value
```

---

## 26.4. Action Builder

Chọn action:

* Create Activity
* Send Notification
* Update Status
* Assign Lead
* Reclaim Lead
* Create Commission
* Call Webhook

---

# 27. SETTINGS SCREEN

Chỉ Admin.

## 27.1. Settings Menu

* Users
* Teams
* Roles
* Permissions
* Master Data
* Status
* Workflow
* SLA
* Import Templates
* Integrations
* System Logs

---

## 27.2. Master Data

Quản lý:

* Customer Status
* Lead Status
* Deal Stage
* Property Status
* Payment Status
* Commission Status
* Lead Source
* Lost Reason
* Property Type
* Activity Type
* Appointment Type

---

# 28. IMPORT UX

## 28.1. Import Flow

Các bước:

1. Tải file mẫu
2. Upload Excel
3. Preview dữ liệu
4. Hiển thị lỗi/trùng
5. Xác nhận import
6. Hiển thị kết quả

---

## 28.2. Import Preview Table

Cột:

* Row number
* Data preview
* Status
* Error message

Màu:

* Xanh: hợp lệ
* Vàng: cảnh báo
* Đỏ: lỗi

---

# 29. EXPORT UX

## 29.1. Export Modal

Fields:

* Loại dữ liệu
* Filter hiện tại
* Định dạng: Excel, CSV, PDF
* Include hidden columns
* Export button

---

## 29.2. Export Permission

Nếu user không có quyền:

* Ẩn nút export
* Nếu gọi API trực tiếp thì backend trả 403

---

# 30. NOTIFICATION CENTER

## 30.1. Notification Bell

Hiển thị số thông báo chưa đọc.

---

## 30.2. Notification Dropdown

Nhóm theo:

* Lead
* Task
* Deal
* Payment
* System

---

## 30.3. Notification List

Fields:

* Title
* Message
* Time
* Priority
* Link

---

# 31. EMPTY STATE

Mỗi màn hình cần có empty state rõ ràng.

Ví dụ:

```text
Chưa có khách hàng nào.
Hãy bấm "Thêm khách hàng" để tạo khách đầu tiên.
```

---

# 32. LOADING STATE

Dùng:

* Skeleton loading cho bảng/card
* Spinner cho nút đang xử lý
* Progress cho import/export

---

# 33. ERROR STATE

Hiển thị lỗi thân thiện.

Ví dụ:

```text
Không thể tải danh sách khách hàng.
Vui lòng thử lại.
```

Có nút:

* Thử lại
* Liên hệ Admin

---

# 34. FORM VALIDATION UX

## 34.1. Inline Error

Hiển thị lỗi dưới input.

Ví dụ:

```text
Số điện thoại không hợp lệ.
```

---

## 34.2. Required Fields

Dấu `*` cho trường bắt buộc.

---

## 34.3. Dirty Form Warning

Nếu user đang sửa form mà rời trang:

```text
Bạn có thay đổi chưa lưu. Bạn có chắc muốn rời khỏi trang?
```

---

# 35. PERMISSION UX

## 35.1. Hide Unauthorized Actions

Nếu không có quyền:

* Ẩn nút
* Ẩn menu
* Ẩn tab nhạy cảm

---

## 35.2. Disabled With Tooltip

Với một số action nên disable và giải thích:

```text
Bạn không có quyền chuyển khách này.
```

---

## 35.3. 403 Page

Nếu truy cập URL không có quyền:

```text
Bạn không có quyền truy cập trang này.
```

---

# 36. STATUS COLOR SYSTEM

## 36.1. Customer Temperature

* Cold: Xám
* Warm: Xanh dương
* Hot: Cam
* Super Hot: Đỏ

---

## 36.2. Deal Stage

* Lead: Xám
* Contacted: Xanh dương nhạt
* Qualified: Xanh dương
* Appointment: Tím
* Site Visit: Indigo
* Negotiation: Cam
* Booking: Vàng
* Deposit: Đỏ nhạt
* Contract: Xanh lá
* Closed Won: Xanh lá đậm
* Closed Lost: Xám đậm

---

## 36.3. SLA

* On Time: Xanh
* Warning: Vàng
* Overdue: Đỏ

---

## 36.4. Payment

* Unpaid: Xám
* Partial: Vàng
* Paid: Xanh
* Overdue: Đỏ

---

# 37. COMPONENT LIBRARY

Frontend nên tạo component dùng chung:

## Layout

* AppShell
* Sidebar
* Header
* PageHeader
* ContentCard

---

## Data

* DataTable
* FilterBar
* SearchInput
* Pagination
* SortableColumn

---

## Feedback

* StatusBadge
* TemperatureBadge
* SLAIndicator
* Toast
* Alert
* EmptyState
* LoadingSkeleton

---

## Forms

* TextInput
* SelectInput
* MultiSelect
* DatePicker
* CurrencyInput
* PhoneInput
* FileUpload
* FormSection

---

## Business Components

* CustomerCard
* PropertyCard
* DealCard
* Timeline
* KanbanBoard
* ActivityItem
* NotificationItem
* KPIStatCard

---

# 38. ACCESSIBILITY

Yêu cầu:

* Button có aria-label nếu chỉ có icon.
* Input có label.
* Màu trạng thái không là thông tin duy nhất, phải có text.
* Có focus state rõ ràng.
* Hỗ trợ keyboard navigation cơ bản.

---

# 39. PERFORMANCE UX

## 39.1. Table

Với dữ liệu lớn:

* Server-side pagination
* Server-side filter
* Server-side sort
* Debounce search 300ms

---

## 39.2. Detail Page

Load theo tab.

Không cần load toàn bộ dữ liệu một lần.

Ví dụ:

* Customer detail load tổng quan trước
* Khi bấm Timeline mới gọi timeline API
* Khi bấm File mới gọi file API

---

## 39.3. Cache

Frontend nên cache:

* Master data
* Current user
* Permissions
* Sidebar menu

---

# 40. ROUTES

## Public Routes

```text
/login
/forgot-password
/reset-password
```

---

## Protected Routes

```text
/dashboard
/leads
/customers
/customers/:id
/properties
/properties/:id
/projects
/projects/:id
/deals
/deals/:id
/activities
/appointments
/marketing
/reports
/payments
/commissions
/files
/workflows
/settings
/settings/users
/settings/roles
/settings/master-data
/settings/sla
```

---

# 41. ROLE-BASED DEFAULT ROUTE

## Sale

```text
/dashboard/sale
```

---

## Leader

```text
/dashboard/leader
```

---

## Director

```text
/dashboard/director
```

---

## Marketing

```text
/dashboard/marketing
```

---

## Accountant

```text
/dashboard/accountant
```

---

## Inventory Manager

```text
/dashboard/inventory
```

---

## Admin

```text
/dashboard/admin
```

---

# 42. ACCEPTANCE CRITERIA

## 42.1. Dashboard

* Sale thấy việc cần làm hôm nay.
* Leader thấy hiệu suất team.
* Director thấy báo cáo tổng quan.
* Dashboard không hiển thị dữ liệu vượt quyền.

---

## 42.2. Customer

* Tìm khách theo số điện thoại nhanh.
* Tạo khách có kiểm tra trùng.
* Customer detail có Customer 360.
* Timeline hiển thị đầy đủ lịch sử.

---

## 42.3. Inventory

* Lọc căn theo dự án, giá, diện tích, phòng ngủ, trạng thái.
* Property detail có lịch sử giá.
* Property detail có lịch sử trạng thái.
* Có danh sách khách phù hợp.

---

## 42.4. Deal

* Kanban kéo thả được nếu hợp lệ.
* Khi chuyển stage thiếu dữ liệu, modal yêu cầu nhập.
* Closed Lost bắt buộc chọn lý do.
* Deal detail có timeline, thanh toán, hoa hồng.

---

## 42.5. Follow-up

* Sale thấy việc hôm nay/quá hạn.
* Hoàn thành task có thể tạo việc tiếp theo.
* Khách nóng quá hạn hiển thị cảnh báo.

---

## 42.6. Permission

* Menu ẩn theo quyền.
* Button ẩn theo quyền.
* API vẫn kiểm tra quyền ở backend.
* Trang 403 hiển thị nếu truy cập sai quyền.

---

# 43. IMPLEMENTATION NOTES FOR CODEX

Khi code frontend, Codex cần ưu tiên:

1. Tạo AppShell chuẩn.
2. Tạo hệ thống route bảo vệ bằng auth.
3. Tạo Sidebar động theo permissions.
4. Tạo DataTable dùng chung.
5. Tạo FilterBar dùng chung.
6. Tạo StatusBadge dùng chung.
7. Tạo Customer List + Customer Detail trước.
8. Tạo Property List + Property Detail.
9. Tạo Deal Kanban + Deal Detail.
10. Tạo Dashboard theo role.
11. Tạo Import/Export UX.
12. Tạo Settings và Workflow Builder sau.

---

# 44. KẾT LUẬN

UI/UX của CRM bất động sản không chỉ để đẹp mà phải giúp doanh nghiệp vận hành tốt hơn.

Giao diện cần tập trung vào:

* Sale làm việc nhanh hơn.
* Leader kiểm soát team tốt hơn.
* Giám đốc ra quyết định nhanh hơn.
* Marketing biết nguồn nào hiệu quả.
* Kế toán kiểm soát thanh toán, hoa hồng.
* Kho hàng luôn chính xác.

Các màn hình quan trọng nhất trong Phase 1:

* Sale Dashboard
* Lead Center
* Customer List
* Customer Detail 360
* Property List
* Property Detail
* Deal Kanban
* Deal Detail
* Activity / Follow-up
* Report Dashboard

Nếu các màn hình này được làm tốt, hệ thống CRM sẽ có giá trị thực tế ngay cả khi chưa có AI hoặc automation nâng cao.
