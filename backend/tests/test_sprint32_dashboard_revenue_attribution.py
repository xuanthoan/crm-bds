from datetime import date
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend" / "src"
DOCS = ROOT / "docs"


class Sprint32DashboardRevenueAttributionSourceTests(unittest.TestCase):
    def b(self, rel): return (BACKEND / rel).read_text(encoding="utf-8")
    def f(self, rel): return (FRONTEND / rel).read_text(encoding="utf-8")
    def d(self, rel): return (DOCS / rel).read_text(encoding="utf-8")

    def test_time_range_presets_and_inclusive_end_day(self):
        service = self.b("app/services/dashboard_service.py")
        for snippet in (
            'DEFAULT_DASHBOARD_PRESET = "last_30_days"',
            'preset == "today"',
            'preset == "last_7_days"',
            'today - timedelta(days=6)',
            'preset == "last_30_days"',
            'today - timedelta(days=29)',
            'preset == "this_month"',
            'preset == "last_month"',
            'preset == "custom"',
            'end_day + timedelta(days=1)',
            'start_datetime',
            'end_datetime',
        ):
            self.assertIn(snippet, service)

    def test_backend_boss_dashboard_contract_and_permission(self):
        api = self.b("app/api/v1/dashboard.py")
        service = self.b("app/services/dashboard_service.py")
        permissions = self.b("app/permissions/constants.py")
        self.assertIn('@router.get("/boss")', api)
        self.assertIn("BOSS_DASHBOARD_PERMISSION", service + api)
        self.assertIn("dashboard.boss.view", permissions + service)
        self.assertIn("dashboard.view.all", api)
        self.assertIn("reports.view.ceo_dashboard", api)

    def test_revenue_uses_valid_contract_and_deal_owner_not_first_touch_or_lead_creator(self):
        service = self.b("app/services/dashboard_service.py")
        self.assertIn("VALID_CONTRACT_REVENUE_STATUSES", service)
        for status in ("signed", "effective", "active", "completed", "won"):
            self.assertIn(status, service)
        self.assertIn("Deal.owner_id == User.id", service)
        self.assertIn("Contract.contract_value", service)
        self.assertIn("Deal.deleted_at.is_(None)", service)
        boss_service = service.split("def get_boss_dashboard", 1)[1]
        forbidden = ["first_touch_user_id", "first_touch_team_id", "Lead.created_by_id", "Lead.owner_id==", "Lead.owner_id =="]
        for snippet in forbidden:
            self.assertNotIn(snippet, boss_service)

    def test_rankings_duplicate_customer_multiple_contracts_and_cancelled_draft_exclusion_are_source_locked(self):
        service = self.b("app/services/dashboard_service.py")
        self.assertIn("_leaderboards", service)
        self.assertIn("top_sales_7_days", service)
        self.assertIn("top_sales_30_days", service)
        self.assertIn("top_teams_7_days", service)
        self.assertIn("top_teams_30_days", service)
        self.assertIn("top_projects", service)
        self.assertIn("limit=10", service)
        self.assertIn("reverse=True)[:limit]", service)
        self.assertIn(".order_by(func.count().desc())", service)
        self.assertIn(".limit(10)", service)
        self.assertIn("Contract.status.in_(VALID_CONTRACT_REVENUE_STATUSES)", service)
        self.assertNotIn('"draft"', service.split("VALID_CONTRACT_REVENUE_STATUSES", 1)[1].split("}\n", 1)[0])
        self.assertNotIn('"cancelled"', service.split("VALID_CONTRACT_REVENUE_STATUSES", 1)[1].split("}\n", 1)[0])

    def test_commission_ads_roi_and_duplicate_reengagement_are_safe(self):
        service = self.b("app/services/dashboard_service.py")
        for snippet in ("SalesCommission", "approved_commission", "paid_amount", "CompanyCommissionReceivable", "confirmed_receivable_amount", "received_amount"):
            self.assertIn(snippet, service)
        self.assertIn("ads_cost = 0.0", service)
        self.assertIn("roi_ratio = revenue / ads_cost if ads_cost else None", service)
        self.assertIn('activity_type == "duplicate_reengagement"', service)
        self.assertIn("lead_new_count", service)
        self.assertIn("duplicate_reengagement_count", service)
        for field in ("customer_paid_total", "customer_outstanding_total", "avg_contract_value", "company_commission_outstanding_total", "sales_commission_approved_total", "sales_commission_paid_total", "sales_commission_outstanding_total", "gross_profit_received_estimate", "gross_profit_receivable_estimate", "company_commission_collection_rate", "sales_commission_payment_rate"):
            self.assertIn(field, service)
        self.assertIn("max(revenue - customer_paid, 0)", service)
        self.assertIn("max(company_commission_receivable - company_commission_received, 0)", service)
        self.assertIn("max(sales_commission_approved - sales_commission_paid, 0)", service)
        self.assertIn("company_commission_received - sales_commission_paid - ads_cost", service)

    def test_frontend_boss_dashboard_foundation(self):
        page = self.f("features/dashboard/BossDashboard.tsx")
        filter_component = self.f("features/dashboard/DashboardDateRangeFilter.tsx")
        api = self.f("features/dashboard/api.ts")
        routes = self.f("routes/AppRoutes.tsx")
        layout = self.f("layouts/AppLayout.tsx")
        css = self.f("styles.css")
        for label in ("Tổng quan giám đốc", "Lead mới", "Lead chuyển khách hàng", "Booking", "Khách đã cọc", "Deal", "Hợp đồng ký", "Doanh số", "Chi phí quảng cáo", "ROI doanh thu/ads"):
            self.assertIn(label, page)
        for section in ("Tổng quan vận hành", "Doanh số & dòng tiền", "Hoa hồng & chi phí", "Xu hướng", "Funnel chuyển đổi", "Nguồn & dự án", "Xếp hạng hiệu suất", "Bảng chi tiết"):
            self.assertIn(section, page)
        for label in ("Tiền khách đã thu", "Công nợ khách còn phải thu", "HH công ty đã thu", "HH công ty còn phải thu", "HH sale đã chi", "HH sale còn phải chi", "Lợi nhuận gộp tạm tính", "Tỷ lệ thu HH công ty", "Tỷ lệ chi HH sale"):
            self.assertIn(label, page)
        for label in ("Hôm nay", "7 ngày qua", "30 ngày qua", "Tháng này", "Tháng trước", "Tùy chọn"):
            self.assertIn(label, filter_component)
        for preset in ("today", "last_7_days", "last_30_days", "this_month", "last_month", "custom"):
            self.assertIn(preset, filter_component + page)
        for label in ("Lead mới theo ngày", "Doanh số theo ngày", "Top sale 7 ngày qua", "Top sale 30 ngày qua", "Top team 7 ngày qua", "Top team 30 ngày qua", "Top dự án theo doanh số", "Top nguồn lead", "Funnel Lead → Customer", "Funnel Booking → Cọc → Deal → Hợp đồng"):
            self.assertIn(label, page)
        self.assertIn("/api/v1/dashboard/boss", api)
        self.assertIn("/dashboard/boss", routes + layout)
        self.assertIn("Đang tải dashboard", page)
        self.assertIn("Không tải được dữ liệu dashboard", page)
        self.assertIn("Chưa có dữ liệu trong khoảng thời gian này", page)
        self.assertIn("Chưa xác định", page)
        self.assertIn("Chưa có dự án", page)
        self.assertIn("Chưa có team", page)
        self.assertIn("Chưa có sale", page)
        self.assertIn("formatNumber", page)
        self.assertIn("formatCurrencyVnd", page)
        self.assertIn("formatCompactCurrencyVnd", page)
        self.assertIn("formatPercent", page)
        self.assertIn("formatCurrencyTooltip", page)
        self.assertIn("slice(0, 10)", page)
        self.assertIn("AreaTrendCard", page)
        self.assertIn("TrapezoidFunnel", page)
        self.assertIn("trapezoid-segment", page + css)
        self.assertIn("kpi-ops", page + css)
        self.assertIn("kpi-cash", page + css)
        self.assertIn("kpi-commission", page + css)
        self.assertIn("dashboard-area-chart", page + css)
        self.assertIn("dashboard-hbar-chart", page + css)
        self.assertIn("detail-ranking-list", page + css)
        self.assertIn("Chưa có phòng ban", page)
        self.assertNotIn("lead đầu tiên", page.lower())
        self.assertNotIn("lead_new_count</", page)
        self.assertNotIn("revenue_total</", page)

    def test_frontend_boss_dashboard_css_prevents_white_filter_text_and_page_overflow(self):
        css = self.f("styles.css")
        dashboard_css = css.split(".dashboard-page", 1)[1]
        self.assertIn("overflow-x: hidden", dashboard_css)
        self.assertIn("max-width: 100%", dashboard_css)
        self.assertIn("min-width: 0", dashboard_css)
        self.assertIn(".filter-pills button", dashboard_css)
        self.assertIn("color: #1f2937", dashboard_css)
        self.assertIn(".filter-pills button.active", dashboard_css)
        self.assertIn("color: #ffffff", dashboard_css)
        self.assertIn("grid-template-columns: repeat(auto-fit, minmax(180px, 1fr))", dashboard_css)
        self.assertIn("grid-template-columns: repeat(auto-fit, minmax(min(100%, 360px), 1fr))", dashboard_css)
        self.assertIn("flex-wrap: wrap", dashboard_css)
        self.assertIn("overflow-x: auto", dashboard_css)
        self.assertNotIn("width: 100vw", dashboard_css)
        self.assertNotIn("min-width: 1200px", dashboard_css)
        self.assertNotIn("grid-template-columns: repeat(6, 1fr)", dashboard_css)


    def test_sprint32_2_visual_polish_and_30_day_chart_contract(self):
        page = self.f("features/dashboard/BossDashboard.tsx")
        css = self.f("styles.css")
        service = self.b("app/services/dashboard_service.py")
        docs = self.d("BUSINESS_RULES.md") + self.d("PROJECT_HANDOFF.md") + self.d("DEVELOPMENT_ROADMAP.md")
        for snippet in ("normalizeDailySeries", "if (rows.length <= maxPoints) return rows", "const visibleRows = normalizeDailySeries(rows, 30)"):
            self.assertIn(snippet, page)
        for snippet in ("today - timedelta(days=6)", "today - timedelta(days=29)", "day_map = {d:", "revenue_day = {d:", "for d in _dates(start, end)"):
            self.assertIn(snippet, service)
        self.assertIn("clip-path: polygon(0 0, 100% 0, 92% 100%, 8% 100%)", css)
        self.assertNotIn("clip-path: polygon(7% 0, 93% 0, 100% 100%, 0 100%)", css)
        for snippet in ("detail-list-header", "detail-ranking-list", "detail-ranking-row", "detail-row-metrics", "rank-badge", "gold", "silver", "bronze"):
            self.assertIn(snippet, page + css)
        for snippet in ("box-shadow: 0 20px 44px", "transform: translateY(-1px)", "linear-gradient(135deg", "kpi-icon"):
            self.assertIn(snippet, css)
        self.assertIn("rows.slice(0, 10)", page)
        self.assertIn("overflow-x: auto", css)
        self.assertNotIn("width: 100vw", css.split(".dashboard-page", 1)[1])
        for snippet in ("Sprint 32.2", "30-day trend charts", "hình thang đúng chiều", "Modern KPI cards"):
            self.assertIn(snippet, docs)

    def test_sprint32_3_dashboard_ui_cleanup_contract(self):
        page = self.f("features/dashboard/BossDashboard.tsx")
        css = self.f("styles.css")
        docs = self.d("BUSINESS_RULES.md") + self.d("PROJECT_HANDOFF.md") + self.d("DEVELOPMENT_ROADMAP.md")
        for snippet in ("getXAxisTicks", "formatDayTick", "formatFullDateTooltip", "area-tick-label", "area-tick-line", "fullLabel", "tick.label"):
            self.assertIn(snippet, page + css)
        self.assertIn("rows.length <= 30", page)
        self.assertIn("return rows.map((row, index)", page)
        self.assertIn("index === 0 || index === rows.length - 1", page)
        self.assertIn("grid-template-columns: 1fr", css.split("/* Sprint 32.3 cleanup", 1)[1])
        self.assertIn("dashboard-area-card.featured", css)
        for tooltip in ("Tổng giá trị hợp đồng hợp lệ trong khoảng thời gian đã chọn.", "Tổng số tiền khách đã thanh toán hoặc phiếu thu đã xác nhận trong kỳ.", "Phần doanh số hợp lệ còn lại sau khi trừ tiền khách đã thu."):
            self.assertIn(tooltip, page)
        self.assertNotIn("formatCurrencyTooltip(data.summary.customer_paid_total)", page)
        self.assertNotIn("formatCurrencyTooltip(data.summary.customer_outstanding_total)", page)
        self.assertNotIn("formatCurrencyTooltip(data.summary.sales_commission_paid_total)", page)
        self.assertIn("detail-list-card", page + css)
        self.assertIn("detail-ranking-list", page + css)
        self.assertIn("grid-template-columns: minmax(0, 1fr) auto", css)
        self.assertIn("formatCompactCurrencyVnd(row.revenue)", page)
        self.assertNotIn("table-scroll-wrapper", page)
        self.assertIn("clip-path: polygon(0 0, 100% 0, 92% 100%, 8% 100%)", css)
        self.assertNotIn("width: 100vw", css.split(".dashboard-page", 1)[1])
        self.assertIn("Sprint 32.3", docs)


    def test_sprint32_4_dashboard_tooltip_axis_cleanup_contract(self):
        page = self.f("features/dashboard/BossDashboard.tsx")
        css = self.f("styles.css")
        docs = self.d("PROJECT_HANDOFF.md") + self.d("DEVELOPMENT_ROADMAP.md")
        self.assertIn("HelpLabel", page)
        self.assertIn("kpi-label-row", page + css)
        self.assertNotIn("{subtitle ? <small>", page)
        self.assertIn("Tổng giá trị hợp đồng hợp lệ trong khoảng thời gian đã chọn.", page)
        dashboard_ui = page.split("export function BossDashboard", 1)[1]
        self.assertNotIn("first_touch", dashboard_ui)
        self.assertNotIn("người upload lead đầu tiên", dashboard_ui)
        self.assertIn("function formatDayTick", page)
        self.assertIn("parts[2]", page)
        self.assertIn("function formatFullDateTooltip", page)
        self.assertIn("if (rows.length <= 30) return rows.map", page)
        self.assertIn("rotate(-55", page)
        self.assertIn("dominant-baseline: hanging", css)
        self.assertNotIn("formatDateLabel", page)
        self.assertNotIn("<span>Top {visibleRows.length}</span>", page)
        self.assertIn("rank-badge", page)
        self.assertIn("rows.slice(0, 10)", page)
        self.assertIn("clip-path: polygon(0 0, 100% 0, 92% 100%, 8% 100%)", css)
        self.assertIn("Sprint 32.4", docs)

    def test_docs_capture_sprint32_rules_and_non_scope(self):
        docs = self.d("BUSINESS_RULES.md") + self.d("PROJECT_HANDOFF.md") + self.d("DEVELOPMENT_ROADMAP.md")
        for snippet in ("Sprint 32", "Dashboard Foundation", "dashboard.boss.view", "GET /api/v1/dashboard/boss", "today", "last_7_days", "last_30_days", "this_month", "last_month", "custom", "không theo first_touch", "không theo người upload lead đầu tiên", "Duplicate re-engagement không tính là lead mới", "export Excel/PDF", "realtime", "multi-touch", "Sprint 32.1", "customer_outstanding_total", "gross_profit_received_estimate", "Sprint 32.2", "Sprint 32.3", "Sprint 32.4"):
            self.assertIn(snippet, docs)


if __name__ == "__main__":
    unittest.main()
