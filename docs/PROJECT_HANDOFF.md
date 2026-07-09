
## Sprint 32 handoff — Dashboard Foundation & Revenue Attribution Verification

- Boss Dashboard v1 được thêm tại `GET /api/v1/dashboard/boss` và frontend route `/dashboard/boss` với menu “Tổng quan giám đốc” khi user có `dashboard.boss.view`, `dashboard.view.all` hoặc `reports.view.ceo_dashboard`.
- Bộ lọc thời gian dùng chung hỗ trợ `today`, `last_7_days`, `last_30_days`, `this_month`, `last_month`, `custom`; mặc định backend là `last_30_days`.
- Dashboard trả `range`, `summary`, `funnel`, `time_series`, `breakdowns`, `rankings`. UI hiển thị loading/error/empty state an toàn, tiền VND và ROI “—” khi không có ads cost.
- Công thức doanh số: chỉ hợp đồng hợp lệ `signed`/`effective`/`active`/`completed`/`won`, ưu tiên ngày `effective_date`, fallback `signed_date`, rồi `created_at`; attribution theo deal/contract winning owner hiện có, không theo first_touch và không theo người upload lead đầu tiên.
- Hoa hồng sale lấy từ `sales_commissions`; hoa hồng công ty lấy từ `company_commission_receivables`; Duplicate re-engagement không tính là lead mới.
- Cố ý chưa làm: dashboard cho toàn bộ role, export Excel/PDF, realtime phức tạp, multi-touch marketing attribution.
