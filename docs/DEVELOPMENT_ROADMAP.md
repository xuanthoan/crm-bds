
## Sprint 32 — Dashboard Foundation & Revenue Attribution Verification

Hoàn thành nền tảng dashboard giám đốc v1 thay vì rewrite toàn bộ reporting.

- Backend: `GET /api/v1/dashboard/boss`, helper date range presets `today`/`last_7_days`/`last_30_days`/`this_month`/`last_month`/`custom`, response có resolved range và số liệu an toàn 0/[]/null.
- Frontend: route `/dashboard/boss`, component `DashboardDateRangeFilter`, summary cards tiếng Việt, funnel, mini chart CSS, ranking tables top sale/team/project/source, loading/error/empty state.
- Verification: test `backend/tests/test_sprint32_dashboard_revenue_attribution.py` khóa quy tắc doanh số không theo first_touch, không theo người upload lead đầu tiên, không tính draft/cancelled contracts, commission lấy từ workflow hiện có và ROI không divide by zero.
- Backlog sau Sprint 32: dashboard trưởng phòng/team leader/kế toán/admin điều phối, export Excel/PDF dashboard, dashboard realtime, multi-touch marketing attribution, ads cost model chuyên sâu.
