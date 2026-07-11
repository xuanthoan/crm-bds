import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class Sprint331SalesManagementDashboardUiSourceTest(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text(encoding='utf-8')

    def test_kpi_labels_use_boss_dashboard_help_label_pattern(self):
        page = self.read('frontend/src/features/dashboard/SalesManagementDashboard.tsx')
        for label in ['Lead mới','Lead đã phân công','Lead chưa phân công','Lead quá hạn','Công việc quá hạn','Booking','Doanh số','HH sale còn phải chi']:
            self.assertIn(f'label="{label}"', page)
        self.assertIn('<HelpLabel content={help}>{label}</HelpLabel>', page)
        self.assertIn('className={`card summary-card kpi-${tone}`}', page)
        self.assertNotIn('helpText=', page)
        self.assertNotIn('function Kpi({label,value,help', page)

    def test_trends_reuse_area_chart_dd_axis_and_empty_state(self):
        page = self.read('frontend/src/features/dashboard/SalesManagementDashboard.tsx')
        self.assertIn('function AreaTrendCard', page)
        self.assertIn('dashboard-area-card', page)
        self.assertIn('area-tick-label', page)
        self.assertIn('formatDayTick', page)
        self.assertIn('formatFullDateTooltip', page)
        self.assertIn('Lead mới theo ngày', page)
        self.assertIn('Doanh số theo ngày', page)
        self.assertIn('Công việc quá hạn theo ngày', page)
        self.assertIn('Không có công việc quá hạn trong khoảng thời gian này.', page)

    def test_funnel_uses_trapezoid_steps_not_only_percentage(self):
        page = self.read('frontend/src/features/dashboard/SalesManagementDashboard.tsx')
        self.assertIn('function TrapezoidFunnel', page)
        self.assertIn('trapezoid-funnel-card', page)
        for text in ['Funnel Lead → Customer', 'Lead', 'Customer', 'Funnel Booking → Cọc → Deal → Hợp đồng', 'Booking', 'Cọc', 'Deal', 'Hợp đồng']:
            self.assertIn(text, page)
        self.assertNotIn('Lead → Customer" value={pct', page)

    def test_rankings_and_sources_use_rank_badges_not_default_ol(self):
        page = self.read('frontend/src/features/dashboard/SalesManagementDashboard.tsx')
        self.assertIn('function RankingCard', page)
        self.assertIn('rank-badge', page)
        self.assertIn('detail-ranking-row', page)
        self.assertIn('ranking-progress', page)
        self.assertNotIn('<ol>', page)
        self.assertNotIn('<li key={`${title}-${i}`}', page)
        for title in ['Top sale theo doanh số','Top sale theo số hợp đồng','Top sale theo hoạt động chăm sóc','Sale có nhiều lead quá hạn','Top nguồn lead theo số lead','Top dự án theo doanh số']:
            self.assertIn(title, page)

    def test_alert_dates_scope_and_overflow_are_polished(self):
        page = self.read('frontend/src/features/dashboard/SalesManagementDashboard.tsx')
        css = self.read('frontend/src/styles.css')
        routes = self.read('frontend/src/routes/AppRoutes.tsx')
        self.assertIn('formatDateTime', page)
        self.assertIn('Intl.DateTimeFormat', page)
        self.assertIn('statusLabel', page)
        self.assertIn('>Mở</a>', page)
        self.assertNotRegex(page, r'T\d{2}:\d{2}:\d{2}\+00:00')
        self.assertIn("scope.scope_type === 'all' ? 'Toàn bộ'", page)
        self.assertIn('scope-badge', page)
        self.assertIn('overflow-x: hidden', css)
        self.assertIn('/dashboard/boss', routes)
        self.assertIn('/dashboard/sales-management', routes)

if __name__ == '__main__':
    unittest.main()
