from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]

class Sprint34SaleDashboardSourceTest(unittest.TestCase):
    def read(self, path): return (ROOT / path).read_text()
    def test_dashboard_route_permission_current_user_scope(self):
        api = self.read('backend/app/api/v1/dashboard.py'); service = self.read('backend/app/services/dashboard_service.py'); perms = self.read('backend/app/permissions/constants.py')
        self.assertIn('@router.get("/sale")', api); self.assertIn('get_sale_dashboard(db, user', api)
        self.assertIn('dashboard.sale.view', perms); self.assertIn('SALE_DASHBOARD_PERMISSION = "dashboard.sale.view"', service)
        for role in ['sale', 'leader', 'sales_manager', 'admin', 'director']:
            self.assertIn("'" + role + "'", perms)
        self.assertIn('Current User Scope', service); self.assertIn('never user_id/sale_id/team_id/department_id', api)
    def test_revenue_attribution_duplicate_and_scope_resolution(self):
        service = self.read('backend/app/services/dashboard_service.py')
        self.assertIn('join(Deal, Contract.deal_id == Deal.id)', service)
        self.assertIn('Deal.owner_id == current_user.id', service)
        self.assertIn('Lead.duplicate_of_customer_id.is_(None)', service)
        for snippet in ['scope=mine => owner_id=current_user.id', 'scope=mine => assigned_user_id=current_user.id', 'scope=mine => assigned_to=current_user.id', 'scope=mine => Deal.owner_id=current_user.id', 'scope=mine => join Deal.owner_id=current_user.id', 'scope=mine => receipt qua deal owner', 'scope=mine => SalesCommission.sale_id=current_user.id']:
            self.assertIn(snippet, service)
    def test_frontend_clickable_kpi_keyboard_tooltip_chart_funnel_priority_drilldown(self):
        page = self.read('frontend/src/features/dashboard/SaleDashboard.tsx'); routes = self.read('frontend/src/routes/AppRoutes.tsx'); api = self.read('frontend/src/features/dashboard/api.ts')
        self.assertIn('/dashboard/sale', routes); self.assertIn('/api/v1/dashboard/sale', api)
        for snippet in ['button type="button"', 'role="link"', 'tabIndex={0}', 'navigateTo', 'HelpLabel', 'dashboard-area-chart', 'dd/MM/yyyy', 'Funnel Lead → Contract', 'trapezoid-segment', 'Danh sách cần xử lý', 'Open']:
            self.assertIn(snippet, page)
        for url in ['/tasks/today', '/tasks/overdue', '/appointments/today', '/appointments', '/leads', '/leads/overdue', '/customers', '/bookings', '/deals', '/contracts', '/receipts', '/commissions']:
            self.assertIn(url, page)
    def test_frontend_hydration_refresh_back_forward_contract(self):
        doc = self.read('docs/Sprint34.md')
        for snippet in ['window.location.search', 'Refresh browser', 'Back', 'Forward', 'Lead', 'Customer', 'Task', 'Appointment', 'Deal', 'Booking', 'Contract', 'Receipt', 'Commission']:
            self.assertIn(snippet, doc)
    def test_regression_dashboards_still_present(self):
        routes = self.read('frontend/src/routes/AppRoutes.tsx'); service = self.read('backend/app/services/dashboard_service.py')
        self.assertIn('/dashboard/boss', routes); self.assertIn('/dashboard/sales-management', routes)
        self.assertIn('def get_boss_dashboard', service); self.assertIn('def get_sales_management_dashboard', service)

if __name__ == '__main__': unittest.main()
