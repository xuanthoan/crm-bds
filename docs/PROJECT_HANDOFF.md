
## Sprint 32 handoff — Dashboard Foundation & Revenue Attribution Verification

- Boss Dashboard v1 được thêm tại `GET /api/v1/dashboard/boss` và frontend route `/dashboard/boss` với menu “Tổng quan giám đốc” khi user có `dashboard.boss.view`, `dashboard.view.all` hoặc `reports.view.ceo_dashboard`.
- Bộ lọc thời gian dùng chung hỗ trợ `today`, `last_7_days`, `last_30_days`, `this_month`, `last_month`, `custom`; mặc định backend là `last_30_days`.
- Dashboard trả `range`, `summary`, `funnel`, `time_series`, `breakdowns`, `rankings`. UI hiển thị loading/error/empty state an toàn, tiền VND và ROI “—” khi không có ads cost.
- Công thức doanh số: chỉ hợp đồng hợp lệ `signed`/`effective`/`active`/`completed`/`won`, ưu tiên ngày `effective_date`, fallback `signed_date`, rồi `created_at`; attribution theo deal/contract winning owner hiện có, không theo first_touch và không theo người upload lead đầu tiên.
- Hoa hồng sale lấy từ `sales_commissions`; hoa hồng công ty lấy từ `company_commission_receivables`; Duplicate re-engagement không tính là lead mới.
- Cố ý chưa làm: dashboard cho toàn bộ role, export Excel/PDF, realtime phức tạp, multi-touch marketing attribution.

## Sprint 32.1 handoff — Boss Dashboard UI/UX Polish & Financial KPIs

- Boss Dashboard giữ route `GET /api/v1/dashboard/boss` và frontend `/dashboard/boss`.
- Summary có thêm KPI tài chính: tiền khách đã thu, công nợ khách còn phải thu, giá trị HĐ trung bình, HH công ty đã thu/còn phải thu, HH sale đã chi/còn phải chi, lợi nhuận gộp tạm tính và tỷ lệ thu/chi hoa hồng.
- Công thức chính: customer outstanding = max(revenue - customer paid, 0); company commission outstanding = max(receivable - received, 0); sales commission outstanding = max(approved - paid, 0); gross profit received estimate = company commission received - sales commission paid - ads cost.
- UI chia section: Tổng quan vận hành, Doanh số & dòng tiền, Hoa hồng & chi phí, Xu hướng, Funnel chuyển đổi, Nguồn & dự án, Xếp hạng hiệu suất, Bảng chi tiết.
- Funnel chuyển sang dạng hình thang/tầng; top sale/team/project/source giới hạn top 10; revenue attribution không đổi và không dùng first_touch.

## Sprint 32.2 — Boss Dashboard Visual Polish
- Boss Dashboard tiếp tục giữ nguyên route `GET /api/v1/dashboard/boss`, permission `dashboard.boss.view`, revenue attribution theo hợp đồng/deal owner và các KPI tài chính Sprint 32.1.
- UI được polish bằng KPI card có icon badge/subtitle/accent, trend chart lớn hơn, funnel hình thang đúng chiều và bảng chi tiết top 10 hiện đại hơn.
- Time series `last_7_days`/`last_30_days` được kỳ vọng trả đủ ngày trong khoảng; frontend không downsample preset 30 ngày xuống dưới 30 điểm.

## Sprint 32.3 — Boss Dashboard Detail Rollback, Chart Axis Labels & KPI Cleanup
- Bảng chi tiết dashboard được đổi sang ranking list gọn với 3 vùng thông tin trong một hàng, dùng compact currency và không cần kéo ngang trong card.
- Trend charts giữ đủ 7/30 điểm nhưng bổ sung tick labels `dd/MM`, luôn có ngày đầu/cuối và thêm các mốc giữa để boss đọc được thời gian.
- KPI card bỏ subtitle lặp số tiền; subtitle chỉ còn mô tả nguồn/công thức nghiệp vụ. Revenue attribution và financial formulas không đổi.

## Sprint 32.4 — Boss Dashboard KPI Tooltip, Full 30-day Axis & Final UI Cleanup
- KPI cards bỏ toàn bộ subtitle dưới số lớn; ý nghĩa KPI chuyển sang dấu `?` dùng `HelpLabel`/`HelpTooltip` cùng style với commissions và reconciliation.
- Trend charts dùng nhãn trục ngày dạng `dd` cho toàn bộ 7/30 điểm; hover marker vẫn hiển thị ngày đầy đủ hơn.
- Detail ranking bỏ badge `Top N` ở header, vẫn giữ rank trong từng dòng, top 10 và không scroll ngang. Không đổi revenue attribution, duplicate re-engagement rule hoặc financial formulas.

## Sprint 33 — Sales Manager / Leader Dashboard
- Thêm dashboard vận hành sale tại `GET /api/v1/dashboard/sales-management` và route frontend `/dashboard/sales-management` cho Sales Manager/Leader; Admin/Director hoặc user có quyền view-all được xem toàn phạm vi.
- Scope dữ liệu: Sales Manager dùng phòng ban do `Department.manager_id` quản lý hoặc department membership hiện có; Leader dùng team do `Team.leader_id` quản lý hoặc team membership hiện có; sale/marketing/accountant/inventory/viewer không có permission sẽ bị 403.
- KPI chính gồm lead mới/đã phân công/chưa phân công/trùng tiếp cận lại, cảnh báo lead-task-appointment, pipeline, hợp đồng, doanh số và hoa hồng sale.
- Revenue attribution tiếp tục theo owner của deal/hợp đồng hợp lệ Sprint 32, không theo lead creator/uploader/first touch. Duplicate re-engagement được đếm riêng và không tăng lead mới.
- Sprint này không thêm dashboard cho Sale/Marketing/Accountant/Inventory và không thay đổi Boss Dashboard.

## Sprint 33.1 — Sales Management Dashboard UI polish
- Trang `/dashboard/sales-management` được polish lại để dùng cùng ngôn ngữ UI với Boss Dashboard Sprint 32.4: KPI card có label + `HelpLabel`, area trend chart, trapezoid funnel, ranking row có rank badge và alert list gọn.
- UI đã Việt hóa scope (`all` → `Toàn bộ`, `team` → nhóm/team, `department` → phòng ban), format ngày giờ alert bằng `Intl.DateTimeFormat('vi-VN')` và giữ link “Mở”.
- Sprint 33.1 không đổi backend permission/scope, duplicate re-engagement rule hay revenue attribution Sprint 32.

## Sprint 33.2 — Sales Management alert cleanup & project revenue verification
- Bỏ “Lead chưa phân công” khỏi UI `/dashboard/sales-management`; backend vẫn giữ field tương ứng để không phá client/test cũ.
- Đổi nhãn/tooltip thành “Lead quá hạn chăm sóc” để làm rõ lead đã đến hạn follow-up nhưng trễ xử lý.
- Top dự án theo doanh số dùng hợp đồng hợp lệ trong scope Sales Manager/Leader/Admin, group theo project với fallback contract/deal/booking-property/contract-property/deal-property/lead project interest và vẫn theo deal owner, không theo first-touch/uploader.

## Sprint 34 — Sale Dashboard
- Added personal Sale Dashboard at `/dashboard/sale` focused on “hôm nay cần làm gì” for the authenticated current user only.
- Backend endpoint `GET /api/v1/dashboard/sale` does not accept `user_id`, `sale_id`, `team_id`, or `department_id`; all lead/task/appointment/deal/contract/commission data is scoped to `current_user`.
- Permission uses `dashboard.sale.view` with personal dashboard access for sale/leader/sales_manager/admin/director roles without requiring Boss or Sales Management dashboard permissions.
- Sale Dashboard intentionally does not show “Lead chưa phân công”. Duplicate re-engagement leads are excluded from new lead counts.
- Lead overdue care follows Sprint 33.2 `CLOSED_LEAD_STATUSES` and `next_follow_up_at < now` rule.
- Personal revenue keeps Sprint 32 attribution: valid contracts joined through Deal owner/current user, never first-touch/uploader/lead creator.
- Boss Dashboard and Sales Management Dashboard remain separate routes and scopes.

## Sprint 34.1 — Sale Dashboard drilldown links
- KPI cards on `/dashboard/sale` now act as action shortcuts when a safe destination exists.
- Drilldown URLs are built on the frontend with `scope=mine` and date range params; they never include `user_id`, `sale_id`, `team_id`, or `department_id`.
- Linked cards include today/overdue tasks, today/overdue appointments, follow-up lead cards, lead/customer cards, booking/deal/contract/revenue/receipt cards, and personal commission amount cards.
- Ratio cards remain non-clickable because they represent derived metrics rather than a single safe list destination.
- Sprint 34.1 does not change Boss Dashboard, Sales Management Dashboard, duplicate lead ownership, or Sprint 32 revenue attribution.
