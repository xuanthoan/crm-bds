import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class Sprint33SalesManagementDashboardSourceTest(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text(encoding='utf-8')

    def test_backend_endpoint_permissions_scope_and_response(self):
        api = self.read('backend/app/api/v1/dashboard.py')
        service = self.read('backend/app/services/dashboard_service.py')
        perms = self.read('backend/app/permissions/constants.py')
        self.assertIn('/sales-management', api)
        for code in ['dashboard.sales_manager.view','dashboard.leader.view','dashboard.team.view','dashboard.sales.view.all']:
            self.assertIn(code, perms)
        self.assertIn('def resolve_sales_management_scope', service)
        self.assertIn('Bạn không có quyền xem dashboard quản lý sale', service)
        self.assertIn('Department.manager_id', service)
        self.assertIn('Team.leader_id', service)
        self.assertIn('lead_new_count', service)
        self.assertIn('duplicate_reengagement', service)
        self.assertIn('Lead.duplicate_detected.is_(False)', service)
        self.assertIn('time_series', service)
        self.assertIn('rankings', service)
        self.assertIn('alerts', service)

    def test_date_revenue_alerts_and_rankings_rules(self):
        service = self.read('backend/app/services/dashboard_service.py')
        self.assertIn('preset or "last_7_days"', service)
        self.assertIn('resolve_dashboard_date_range', service)
        self.assertIn('Deal.owner_id.in_(ids)', service)
        self.assertNotIn('Lead.created_by_id.in_(ids), Deal', service)
        self.assertIn('VALID_CONTRACT_REVENUE_STATUSES', service)
        self.assertIn('LeadTask.due_at < stamp', service)
        self.assertIn('LeadAppointment.start_at >= today_start', service)
        for key in ['top_sales_by_revenue','top_sales_by_contract_count','top_sales_by_activity_count','top_sales_with_overdue_leads','top_projects_by_revenue','top_sources_by_lead_count']:
            self.assertIn(key, service)
        self.assertIn('[:10]', service)

    def test_frontend_route_menu_api_labels_tooltips(self):
        routes = self.read('frontend/src/routes/AppRoutes.tsx')
        layout = self.read('frontend/src/layouts/AppLayout.tsx')
        api = self.read('frontend/src/features/dashboard/api.ts')
        page = self.read('frontend/src/features/dashboard/SalesManagementDashboard.tsx')
        css = self.read('frontend/src/styles.css')
        self.assertIn('/dashboard/sales-management', routes)
        self.assertIn('Tổng quan quản lý sale', layout)
        self.assertIn('getSalesManagementDashboard', api)
        self.assertIn('/api/v1/dashboard/sales-management', api)
        for label in ['Tổng quan quản lý sale','Tổng quan team','Cảnh báo cần xử lý','Pipeline & doanh số','Xu hướng','Funnel chuyển đổi','Hiệu suất sale','Nguồn & dự án','Danh sách cần xử lý']:
            self.assertIn(label, page)
        for label in ['Sale trong phạm vi','Lead mới','Lead đã phân công','Lead chưa phân công','Lead quá hạn','Lead chưa có hoạt động','Khách lâu chưa tương tác','Công việc hôm nay','Công việc quá hạn','Lịch hẹn hôm nay','Booking','Khách đã cọc','Deal','Hợp đồng ký','Doanh số','HH sale còn phải chi']:
            self.assertIn(label, page)
        self.assertIn('HelpLabel', page)
        self.assertNotIn('first_touch', page)
        self.assertNotIn('uploader', page)
        self.assertIn('overflow-x:hidden', css)

if __name__ == '__main__':
    unittest.main()
