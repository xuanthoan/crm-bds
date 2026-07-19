"""Regression guards for Finance Dashboard drilldown semantics.

These source-level checks protect the public query contract shared by the
dashboard and list pages.  The underlying services have broader integration
coverage in the payment and commission sprint suites.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class Sprint35FinanceDashboardSourceTest(unittest.TestCase):
    def setUp(self):
        self.dashboard = (ROOT / "backend/app/services/dashboard_service.py").read_text()
        self.payments = (ROOT / "backend/app/services/payment_service.py").read_text()
        self.payments_api = (ROOT / "backend/app/api/v1/payments.py").read_text()
        self.finance_ui = (ROOT / "frontend/src/features/dashboard/FinanceDashboard.tsx").read_text()

    def test_balance_drilldowns_use_as_of_not_created_at_range(self):
        self.assertIn("as_of = (end - timedelta(days=1)).date()", self.dashboard)
        self.assertIn("/payments?outstanding=true&${asOf}", self.finance_ui)
        self.assertIn("/payments?overdue=true&${asOf}", self.finance_ui)
        self.assertIn("PaymentSchedule.due_date < (as_of or date.today())", self.payments)

    def test_due_and_outstanding_filters_share_live_schedule_rules(self):
        self.assertIn("due:bool|None=None,outstanding:bool|None=None,as_of:date|None=None", self.payments_api)
        self.assertIn("if due is True:", self.payments)
        self.assertIn("if outstanding is True:", self.payments)
        self.assertIn("PaymentSchedule.remaining_amount > 0", self.payments)
        self.assertIn("Contract.status.in_(['signed', 'active', 'completed'])", self.payments)

    def test_period_metrics_keep_matching_filter_fields(self):
        self.assertIn("PaymentReceipt.created_at >= start, PaymentReceipt.created_at < end", self.dashboard)
        self.assertIn("/invoices?invoice_status=draft&${period}", self.finance_ui)
        self.assertIn("approved_from=${data.range.from_date}", self.finance_ui)
        self.assertIn("paid_from=${data.range.from_date}", self.finance_ui)

    def test_alert_cards_are_clickable_and_keep_shared_card_style(self):
        self.assertIn('className="card summary-card kpi-ops dashboard-kpi-button"', self.finance_ui)
        self.assertIn("<HelpLabel content={help}", self.finance_ui)
        self.assertNotIn("Xem chi tiết", self.finance_ui)


if __name__ == "__main__":
    unittest.main()
