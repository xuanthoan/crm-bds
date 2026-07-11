
## Sprint 32 — Dashboard Foundation & Revenue Attribution Verification

Hoàn thành nền tảng dashboard giám đốc v1 thay vì rewrite toàn bộ reporting.

- Backend: `GET /api/v1/dashboard/boss`, helper date range presets `today`/`last_7_days`/`last_30_days`/`this_month`/`last_month`/`custom`, response có resolved range và số liệu an toàn 0/[]/null.
- Frontend: route `/dashboard/boss`, component `DashboardDateRangeFilter`, summary cards tiếng Việt, funnel, mini chart CSS, ranking tables top sale/team/project/source, loading/error/empty state.
- Verification: test `backend/tests/test_sprint32_dashboard_revenue_attribution.py` khóa quy tắc doanh số không theo first_touch, không theo người upload lead đầu tiên, không tính draft/cancelled contracts, commission lấy từ workflow hiện có và ROI không divide by zero.
- Backlog sau Sprint 32: dashboard trưởng phòng/team leader/kế toán/admin điều phối, export Excel/PDF dashboard, dashboard realtime, multi-touch marketing attribution, ads cost model chuyên sâu.

## Sprint 32.1 — Boss Dashboard UI/UX Polish & Financial KPIs

- Bổ sung financial KPIs cho boss dashboard: customer paid/outstanding, company commission received/outstanding, sales commission paid/outstanding, gross profit estimates, collection/payment rates và avg contract value.
- UI nâng cấp thành grouped/tinted KPI cards, enlarged trend charts, trapezoid funnel và top 10 rankings.
- Không đổi scope Sprint 32: không export, không realtime, không dashboard toàn bộ role và không đổi rule attribution không theo first_touch.

## Sprint 32.2 — Boss Dashboard visual polish
- Hoàn thiện trải nghiệm Boss Dashboard: modern KPI cards, 30-day trend charts, corrected trapezoid funnel geometry, modern detail tables/ranking details.
- Không thay đổi phạm vi Sprint 32: không realtime dashboard, không export Excel/PDF, không multi-touch attribution, không đổi revenue attribution khỏi hợp đồng/deal owner.

## Sprint 32.3 — Boss Dashboard detail rollback and chart labels
- Sửa UX sau feedback: no-scroll detail ranking lists, chart x-axis labels, full-width Lead trend chart và KPI subtitle cleanup.
- Không thêm dependency chart mới, không đổi API dashboard và không đổi revenue attribution/financial KPI formulas.

## Sprint 32.4 — Boss Dashboard KPI tooltip and axis cleanup
- Final UI cleanup: KPI tooltip help icons instead of subtitles, full 30-day day-number axis labels, and removal of detail-card Top N badges.
- No new dependencies, no API route changes, no revenue attribution changes, and no financial KPI formula changes.

## Sprint 33 — Sales Manager / Leader Dashboard
- Backend: endpoint `/api/v1/dashboard/sales-management`, date preset today/last_7_days/last_30_days/this_month/last_month/custom, scope auto/team/department/all, response summary/time_series/funnel/rankings/alerts.
- Frontend: trang `/dashboard/sales-management`, menu “Tổng quan quản lý sale”, date filter, KPI tooltip, trend charts, funnel summary, rankings top 10 và alert lists.
- Guardrails: không làm lại Boss Dashboard, không tính revenue theo first-touch/lead uploader, không leak dữ liệu team khác, không thêm dependency chart mới.
