
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
