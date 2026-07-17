# Sprint 34 Production — Sale Dashboard

## Permission
- Added `dashboard.sale.view` for Sale, Leader, Sales Manager, Admin and Director.
- Frontend route: `/dashboard/sale`. Backend route: `GET /api/v1/dashboard/sale`.

## Scope and Security
- Sale Dashboard always uses authenticated `current_user`.
- Query params such as `user_id`, `sale_id`, `team_id`, and `department_id` are accepted only to ignore them safely; they are not trusted.
- Drilldown URLs use `scope=mine` and never embed user UUID, email, username, team, department or sale IDs.

## Revenue Attribution
- Revenue continues to be calculated from valid contracts joined to `Deal.owner_id`.
- No revenue attribution is based on lead creator, uploader or first touch.

## Duplicate Rule
- Duplicate re-engagement is excluded from new-lead counts by keeping `duplicate_detected=false` and `duplicate_of_customer_id is null` filters.

## KPI
- Sections: Việc cần làm hôm nay, Lead & Khách, Pipeline, Hoa hồng, Trend, Funnel and Priority.
- KPI cards reuse the Boss Dashboard `summary-card` styling, gradients, hover effects, icon badge and `HelpLabel` tooltips.
- Ratio KPIs `Tỷ lệ Lead → Khách` and `Tỷ lệ chi HH` are informational and not clickable.

## Chart and Funnel
- Trend charts use existing self-built SVG area chart primitives.
- Funnel uses the existing trapezoid funnel style: Lead → Customer → Booking → Deposit → Deal → Contract.
- No chart dependency was added.

## Priority
- Priority actions include task overdue, task today, appointment today, lead overdue, lead hot, lead stale and stale customers.

## Drilldown
- Clickable KPI cards are real `<button type="button" role="link">` controls.
- They support mouse, focus-visible, Enter and Space; navigation uses SPA `navigateTo()`.
- Drilldown URLs include `scope=mine` for backend scope resolution.

## Frontend Hydration
- Sprint 34 dashboard emits URL query strings as the filter state, so target pages can hydrate from `window.location.search` and preserve Refresh/Back/Forward behavior.

## Backend Scope Resolution
- Dashboard scope is resolved to the authenticated user only.
- List endpoints are expected to resolve `scope=mine` as: Lead owner, Task assigned user, Appointment assigned user, Booking assigned/owner, Deal owner, Contract/Receipt via Deal owner, Commission sale, Customer owner.

## Regression
- Boss Dashboard and Sales Management Dashboard routes remain unchanged.
- Sprint 32 revenue attribution and duplicate lead rules are preserved.
