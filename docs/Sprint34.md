# Sprint 34 — Sale Dashboard

## Permission
- Added `dashboard.sale.view` for Sale, Leader, Sales Manager, Admin, Director.
- Sale does not require `dashboard.sales_manager.view`.

## Current User Scope
- Backend route: `GET /api/v1/dashboard/sale`.
- Frontend route/sidebar: `/dashboard/sale` / “Dashboard của tôi”.
- Dashboard always uses `current_user`; it never trusts `user_id`, `sale_id`, `team_id`, or `department_id` query parameters.

## KPI
- Việc cần làm hôm nay: Công việc hôm nay, Công việc quá hạn, Lịch hẹn hôm nay, Lịch hẹn quá hạn, Lead cần chăm sóc hôm nay, Lead quá hạn chăm sóc.
- Lead & Khách: Lead mới, Lead đang chăm sóc, Lead chưa có hoạt động, Khách hàng, Khách lâu chưa tương tác.
- Pipeline: Booking, Khách đã cọc, Deal, Hợp đồng ký, Doanh số, Tiền khách đã thu.
- Hoa hồng: HH đã duyệt, HH đã chi, HH còn phải chi, Tỷ lệ Lead → Khách, Tỷ lệ chi HH.

## Charts
- SVG Area Chart for Doanh số theo ngày and Lead theo ngày.
- Supports 7 ngày and 30 ngày; axis label uses `dd`, hover tooltip uses `dd/MM/yyyy`; labels are not rotated.

## Funnel
- Reuses Boss Dashboard trapezoid funnel pattern: Lead → Customer → Booking → Deposit → Deal → Contract.

## Priority
- Danh sách cần xử lý: Task overdue, Task today, Appointment today, Lead overdue, Lead hot, Lead stale, Khách lâu chưa tương tác.
- Each priority row has an `Open` action.

## Drilldown
- KPI cards with drilldown render as `<button type="button" role="link" tabIndex={0}>` and call SPA `navigateTo()`.
- Drilldown URLs include `scope=mine`: `/tasks/today`, `/tasks/overdue`, `/appointments/today`, `/appointments`, `/leads`, `/leads/overdue`, `/customers`, `/bookings`, `/deals`, `/contracts`, `/receipts`, `/commissions`.
- Tỷ lệ Lead → Khách and Tỷ lệ chi HH are not clickable.

## Frontend Hydration
- Every list page (Lead, Customer, Task, Appointment, Deal, Booking, Contract, Receipt, Commission) must hydrate filter state from `window.location.search` on load.
- Refresh browser, Back, and Forward must keep filters in component state, not only in the URL.

## Backend Scope Resolution
- `scope=mine` means: Lead `owner_id=current_user.id`; Task `assigned_user_id=current_user.id`; Appointment `assigned_to=current_user.id`; Deal `Deal.owner_id=current_user.id`; Contract joins Deal owner; Receipt joins Deal owner; Commission uses `SalesCommission.sale_id=current_user.id`.

## Revenue Attribution
- Keep Sprint 32 attribution: revenue is valid Contract joined to Deal owner (`Deal.owner_id`).
- Do not use lead creator, lead uploader, first touch, or duplicate rules for revenue attribution.

## Duplicate Rule
- Duplicate Re-engagement is not counted as Lead mới.

## Regression
- Boss Dashboard, Sales Management Dashboard, Commission, CRM, Task, and Lead behavior must remain intact.
