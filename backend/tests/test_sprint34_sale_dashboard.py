import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]

class Sprint34SaleDashboardSourceTest(unittest.TestCase):
    def read(self, path): return (ROOT / path).read_text(encoding='utf-8')

    def test_endpoint_exists_and_uses_current_user_without_foreign_scope_params(self):
        api = self.read('backend/app/api/v1/dashboard.py')
        self.assertIn('@router.get("/sale")', api)
        signature = re.search(r'def sale_dashboard\((.*?)\):', api, re.S).group(1)
        for forbidden in ('user_id', 'sale_id', 'team_id', 'department_id'):
            self.assertNotIn(forbidden, signature)
        self.assertIn('user:User=Depends(require_auth)', signature)
        self.assertIn('get_sale_dashboard(db,user,preset', api)

    def test_permission_allows_personal_sale_not_boss_manager_only(self):
        service = self.read('backend/app/services/dashboard_service.py')
        constants = self.read('backend/app/permissions/constants.py')
        self.assertIn('SALE_DASHBOARD_PERMISSION = "dashboard.sale.view"', service)
        self.assertIn('can_view_sale_dashboard', service)
        self.assertIn('dashboard.view.own', service)
        self.assertIn('SALE_DASHBOARD_ROLES = {"sale", "leader", "sales_manager", "admin", "director"}', service)
        self.assertIn('"dashboard.sale.view"', constants)
        self.assertIn('ROLE_PERMISSION_MAP[_role].append("dashboard.sale.view")', constants)

    def test_own_scope_no_leak_and_revenue_rule(self):
        service = self.read('backend/app/services/dashboard_service.py')
        sale = service.split('def get_sale_dashboard', 1)[1]
        for snippet in ('Lead.owner_id.__eq__(uid)', 'LeadTask.assigned_to_id == uid', 'LeadAppointment.assigned_to_id == uid', 'Booking.assigned_user_id == uid', 'Deal.owner_id == uid', 'SalesCommission.sale_id == uid'):
            self.assertIn(snippet, sale)
        self.assertIn('join(Deal, Contract.deal_id == Deal.id)', sale)
        self.assertIn('Deal.owner_id == uid', sale)
        self.assertIn('*_valid_contracts(start, end)', sale)
        for forbidden in ('first_touch', 'created_by_id == uid', 'source_type == "uploader"'):
            self.assertNotIn(forbidden, sale)

    def test_duplicate_overdue_tasks_commission_json_and_date_range_rules(self):
        service = self.read('backend/app/services/dashboard_service.py')
        sale = service.split('def get_sale_dashboard', 1)[1]
        self.assertIn('Lead.duplicate_detected.is_(False)', sale)
        self.assertIn('Lead.duplicate_of_customer_id.is_(None)', sale)
        self.assertIn('Lead.next_follow_up_at < stamp', sale)
        self.assertIn('Lead.status.notin_(CLOSED_LEAD_STATUSES)', sale)
        self.assertIn('LeadTask.status.in_(ACTIVE_TASK_STATUSES)', sale)
        self.assertIn('LeadTask.completed_at >= start', sale)
        self.assertIn('max(sc_approved - sc_paid, 0)', sale)
        self.assertIn('"today"', sale)
        self.assertIn('_range_public(r)', sale)
        self.assertIn('.isoformat()', sale)

    def test_frontend_route_menu_labels_tooltips_charts_funnel_actions_and_errors(self):
        page = self.read('frontend/src/features/dashboard/SaleDashboard.tsx')
        routes = self.read('frontend/src/routes/AppRoutes.tsx')
        layout = self.read('frontend/src/layouts/AppLayout.tsx')
        api = self.read('frontend/src/features/dashboard/api.ts')
        self.assertIn('/dashboard/sale', routes)
        self.assertIn('Dashboard của tôi', layout + page)
        self.assertIn('/api/v1/dashboard/sale', api)
        for text in ['Theo dõi khách cần chăm sóc, công việc, lịch hẹn, pipeline và doanh số cá nhân.', 'Việc cần làm hôm nay', 'Ưu tiên xử lý', 'Lead & khách của tôi', 'Pipeline & doanh số của tôi', 'Hoa hồng của tôi', 'Xu hướng cá nhân', 'Funnel cá nhân']:
            self.assertIn(text, page)
        for label in ['Công việc hôm nay','Công việc quá hạn','Lịch hẹn hôm nay','Lịch hẹn quá hạn','Lead cần chăm sóc hôm nay','Lead quá hạn chăm sóc','Lead mới','Lead đang chăm sóc','Lead chưa có hoạt động','Khách hàng','Khách lâu chưa tương tác','Tỷ lệ Lead → Khách','Booking','Khách đã cọc','Deal','Hợp đồng ký','Doanh số','Tiền khách đã thu','HH đã duyệt','HH đã chi','HH còn phải chi','Tỷ lệ chi HH']:
            self.assertIn(label, page)
        self.assertIn('HelpLabel', page)
        self.assertIn('Các lead cần chăm sóc nhưng đã bị trễ hạn.', page)
        self.assertNotIn('Lead chưa phân công', page)
        for chart in ['Hoạt động chăm sóc theo ngày','Lead mới theo ngày','Doanh số theo ngày','Công việc hoàn thành theo ngày']:
            self.assertIn(chart, page)
        self.assertIn('TrapezoidFunnel', page)
        self.assertIn('Khách hàng', page)
        self.assertIn('Hợp đồng', page)
        for action in ['Công việc quá hạn','Công việc hôm nay','Lịch hẹn hôm nay','Lead quá hạn chăm sóc','Mở']:
            self.assertIn(action, page)
        self.assertIn('Bạn không có quyền xem dashboard cá nhân.', page)
        self.assertIn('Không tải được dashboard cá nhân. Vui lòng thử lại hoặc kiểm tra quyền truy cập.', page)
        self.assertIn('/dashboard/boss', routes)
        self.assertIn('/dashboard/sales-management', routes)

if __name__ == '__main__':
    unittest.main()
