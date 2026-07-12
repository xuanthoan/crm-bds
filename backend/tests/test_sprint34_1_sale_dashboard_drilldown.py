import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]

class Sprint341SaleDashboardDrilldownSourceTest(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text(encoding='utf-8')

    def test_sale_dashboard_cards_have_safe_drilldown_routes(self):
        page = self.read('frontend/src/features/dashboard/SaleDashboard.tsx')
        expected = {
            'Công việc hôm nay': '/tasks/today?',
            'Công việc quá hạn': '/tasks/overdue?',
            'Lịch hẹn hôm nay': '/appointments/today?',
            'Lịch hẹn quá hạn': '/appointments?',
            'Lead cần chăm sóc hôm nay': '/leads?',
            'Lead quá hạn chăm sóc': '/leads/overdue?',
            'Lead mới': '/leads?',
            'Lead đang chăm sóc': '/leads?',
            'Lead chưa có hoạt động': '/leads?',
            'Khách hàng': '/customers?',
            'Khách lâu chưa tương tác': '/leads?',
            'Booking': '/bookings?',
            'Khách đã cọc': '/deals?',
            'Deal': '/deals?',
            'Hợp đồng ký': '/contracts?',
            'Doanh số': '/contracts?',
            'Tiền khách đã thu': '/receipts?',
            'HH đã duyệt': '/commissions?',
            'HH đã chi': '/commissions?',
            'HH còn phải chi': '/commissions?',
        }
        for label, route in expected.items():
            self.assertIn(label, page)
            self.assertIn(route, page)
        self.assertIn('scope: \'mine\'', page)
        self.assertIn('created_from: startDate', page)
        self.assertIn('created_to: endDate', page)
        self.assertIn('start_date: startDate', page)
        self.assertIn('end_date: endDate', page)
        self.assertIn("status:'active'", page)
        self.assertIn("care_status:'overdue'", page)
        self.assertIn("activity_status:'none'", page)
        self.assertIn("stale:'true'", page)

    def test_drilldown_urls_do_not_contain_forbidden_cross_scope_params(self):
        page = self.read('frontend/src/features/dashboard/SaleDashboard.tsx')
        for forbidden in ('user_id', 'sale_id', 'team_id', 'department_id', 'owner_id'):
            self.assertNotIn(forbidden, page)
        self.assertIn('scope', page)
        self.assertNotRegex(page, r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')

    def test_clickable_kpi_accessibility_and_tooltip_preserved(self):
        page = self.read('frontend/src/features/dashboard/SaleDashboard.tsx')
        css = self.read('frontend/src/styles.css')
        self.assertIn('drilldownUrl', page)
        self.assertIn('role="link"', page)
        self.assertIn('<button type="button"', page)
        self.assertIn('tabIndex={0}', page)
        self.assertIn('aria-label', page)
        self.assertIn('onDrilldownKey', page)
        self.assertIn("event.key === 'Enter'", page)
        self.assertIn("event.key === ' '", page)
        self.assertIn('HelpLabel', page)
        self.assertIn('Xem chi tiết', page)
        self.assertIn('.sale-dashboard button.summary-card.drilldown-card', css)
        self.assertIn('cursor: pointer', css)
        self.assertIn(':focus-visible', css)

    def test_non_clickable_ratio_cards_and_route_regression(self):
        page = self.read('frontend/src/features/dashboard/SaleDashboard.tsx')
        routes = self.read('frontend/src/routes/AppRoutes.tsx')
        self.assertIn('/dashboard/sale', routes)
        self.assertIn('/dashboard/boss', routes)
        self.assertIn('/dashboard/sales-management', routes)
        lead_rate = re.search(r'<KpiCard label="Tỷ lệ Lead → Khách"[^>]+/>', page).group(0)
        commission_rate = re.search(r'<KpiCard label="Tỷ lệ chi HH"[^>]+/>', page).group(0)
        self.assertNotIn('drilldownUrl', lead_rate)
        self.assertNotIn('drilldownUrl', commission_rate)
        self.assertNotIn('Lead chưa phân công', page)

if __name__ == '__main__':
    unittest.main()
