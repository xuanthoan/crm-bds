import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

def read(path): return (ROOT / path).read_text(encoding='utf-8')
class Sprint34SaleDashboardSourceTest(unittest.TestCase):
    def test_route_permission_and_current_user_scope(self):
        api = read('backend/app/api/v1/dashboard.py')
        svc = read('backend/app/services/dashboard_service.py')
        self.assertIn('@router.get("/sale")', api)
        self.assertIn('SALE_DASHBOARD_PERMISSION', api)
        self.assertIn('user_id:str|None=None', api)
        self.assertIn('sale_id:str|None=None', api)
        self.assertIn('get_sale_dashboard(db,user', api)
        self.assertIn('return {"user_ids": {current_user.id}', svc)
        self.assertIn('Deal.owner_id == uid', svc)
        self.assertIn('SalesCommission.sale_id == uid', svc)
    def test_revenue_attribution_and_duplicate_rule_preserved(self):
        svc = read('backend/app/services/dashboard_service.py')
        self.assertIn('join(Deal, Contract.deal_id == Deal.id)', svc)
        self.assertIn('Deal.owner_id == uid', svc)
        self.assertIn('Lead.duplicate_detected.is_(False)', svc)
        self.assertIn('Lead.duplicate_of_customer_id.is_(None)', svc)
    def test_frontend_clickable_kpi_keyboard_tooltip_chart_funnel_priority_urls(self):
        ui = read('frontend/src/features/dashboard/SaleDashboard.tsx')
        self.assertIn('button type="button" role="link"', ui)
        self.assertIn("e.key==='Enter'||e.key===' '", ui)
        self.assertIn('HelpLabel', ui)
        self.assertIn('dashboard-area-chart', ui)
        self.assertIn('trapezoid-funnel', ui)
        self.assertIn('data.priority.map', ui)
        self.assertIn('/tasks/today?scope=mine', ui)
        self.assertIn('/contracts?scope=mine&status=valid', ui)
        self.assertNotIn('sale_id=', ui)
        self.assertNotIn('team_id=', ui)
    def test_route_sidebar_permission_and_regression_routes_present(self):
        routes = read('frontend/src/routes/AppRoutes.tsx')
        layout = read('frontend/src/layouts/AppLayout.tsx')
        perms = read('backend/app/permissions/constants.py')
        self.assertIn("'/dashboard/sale'", routes)
        self.assertIn('Dashboard của tôi', layout)
        for role in ('sale', 'leader', 'sales_manager', 'admin', 'director'):
            self.assertIn(f"'{role}':", perms)
        self.assertGreaterEqual(perms.count('dashboard.sale.view'), 6)
        self.assertIn("'/dashboard/boss'", routes)
        self.assertIn("'/dashboard/sales-management'", routes)
if __name__ == '__main__': unittest.main()
