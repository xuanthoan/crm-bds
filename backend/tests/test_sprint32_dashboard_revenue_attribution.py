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

    def test_frontend_boss_dashboard_foundation(self):
        page = self.f("features/dashboard/BossDashboard.tsx")
        filter_component = self.f("features/dashboard/DashboardDateRangeFilter.tsx")
        api = self.f("features/dashboard/api.ts")
        routes = self.f("routes/AppRoutes.tsx")
        layout = self.f("layouts/AppLayout.tsx")
        css = self.f("styles.css")
        for label in ("Tổng quan giám đốc", "Lead mới", "Lead chuyển khách hàng", "Booking", "Khách đã cọc", "Deal", "Hợp đồng ký", "Doanh số", "Hoa hồng công ty", "Hoa hồng sale", "Chi phí quảng cáo", "ROI doanh thu/ads"):
            self.assertIn(label, page)
        for label in ("Hôm nay", "7 ngày qua", "30 ngày qua", "Tháng này", "Tháng trước", "Tùy chọn"):
            self.assertIn(label, filter_component)
        for preset in ("today", "last_7_days", "last_30_days", "this_month", "last_month", "custom"):
            self.assertIn(preset, filter_component + page)
        for label in ("Lead mới theo ngày", "Doanh số theo ngày", "Lead theo nguồn", "Top sale 7 ngày qua", "Top sale 30 ngày qua", "Top team 7 ngày qua", "Top team 30 ngày qua", "Top dự án", "Top nguồn lead", "Funnel Lead → Customer", "Funnel Booking → Cọc → Deal → Hợp đồng"):
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
        self.assertIn("AreaTrendCard", page)
        self.assertIn("dashboard-area-chart", page + css)
        self.assertIn("dashboard-hbar-chart", page + css)
        self.assertIn("table-scroll-wrapper", page + css)
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

    def test_docs_capture_sprint32_rules_and_non_scope(self):
        docs = self.d("BUSINESS_RULES.md") + self.d("PROJECT_HANDOFF.md") + self.d("DEVELOPMENT_ROADMAP.md")
        for snippet in ("Sprint 32", "Dashboard Foundation", "dashboard.boss.view", "GET /api/v1/dashboard/boss", "today", "last_7_days", "last_30_days", "this_month", "last_month", "custom", "không theo first_touch", "không theo người upload lead đầu tiên", "Duplicate re-engagement không tính là lead mới", "export Excel/PDF", "realtime", "multi-touch"):
            self.assertIn(snippet, docs)


if __name__ == "__main__":
    unittest.main()
