import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class Sprint332SalesManagementDashboardCleanupSourceTest(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text(encoding='utf-8')

    def test_unassigned_lead_removed_from_sales_management_ui_only(self):
        page = self.read('frontend/src/features/dashboard/SalesManagementDashboard.tsx')
        service = self.read('backend/app/services/dashboard_service.py')
        self.assertNotIn('Lead chưa phân công', page)
        self.assertNotIn('unassigned_leads ??', page)
        self.assertIn('lead_unassigned_count', service)  # response kept backward-compatible
        self.assertIn('unassigned_leads', service)

    def test_overdue_lead_label_is_care_specific(self):
        page = self.read('frontend/src/features/dashboard/SalesManagementDashboard.tsx')
        docs = self.read('docs/BUSINESS_RULES.md')
        self.assertIn('Lead quá hạn chăm sóc', page)
        self.assertIn('Các lead cần chăm sóc nhưng đã bị trễ hạn.', page)
        self.assertIn('Lead quá hạn chăm sóc', docs)
        self.assertIn('next_follow_up_at', self.read('backend/app/services/dashboard_service.py'))

    def test_top_projects_by_revenue_uses_valid_contract_deal_owner_scope_and_project_fallback(self):
        service = self.read('backend/app/services/dashboard_service.py')
        self.assertIn('def _resolve_sales_management_project', service)
        for fallback in ['contract.project_id', 'deal.project_id', 'booking.property_unit.project_id', 'contract.property_unit.project_id', 'deal.property_unit.project_id', 'lead.project_interest']:
            self.assertIn(fallback, service)
        self.assertIn('VALID_CONTRACT_REVENUE_STATUSES', service)
        self.assertIn('Deal.owner_id.in_(ids)', service)
        self.assertIn('top_projects_by_revenue', service)
        self.assertIn('sorted(projects.values(), key=lambda x: x["revenue"], reverse=True)[:10]', service)
        self.assertIn('contract_count', service)
        self.assertIn('lead_count', service)
        self.assertNotIn('first_touch', service)
        self.assertNotIn('first_uploaded', service)

    def test_top_projects_ui_supports_name_value_and_no_joined_text(self):
        page = self.read('frontend/src/features/dashboard/SalesManagementDashboard.tsx')
        self.assertIn('Top dự án theo doanh số', page)
        self.assertIn('RankingCard title="Top dự án theo doanh số"', page)
        self.assertIn('name: safeText(r.project_name || r.name', page)
        self.assertIn('value: formatCompactCurrencyVnd(r.revenue)', page)
        self.assertIn('detail-row-metrics', page)
        self.assertNotIn('Chưa xác định8', page)
        self.assertNotIn('Him Lam Green Park1.000', page)

if __name__ == '__main__':
    unittest.main()
