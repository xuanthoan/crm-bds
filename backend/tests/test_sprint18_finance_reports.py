import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
class Sprint18FinanceReportsSourceTest(unittest.TestCase):
    def read(self,p): return (ROOT/p).read_text(encoding='utf-8')
    def test_backend_routes_and_exports_exist(self):
        api=self.read('backend/app/api/v1/reports.py'); init=self.read('backend/app/api/v1/__init__.py')
        for text in ['/reports/finance','/summary','/receivables','/overdue-payments','/cash-collection','/invoices','/receivables/export','/overdue-payments/export','/cash-collection/export','/invoices/export']:
            self.assertIn(text,api)
        self.assertIn('include_router(reports.router)', init)
        self.assertIn("text/csv; charset=utf-8", api)
        self.assertIn("\\ufeff", self.read('backend/app/services/report_service.py'))
    def test_finance_rules_are_explicit(self):
        service=self.read('backend/app/services/report_service.py')
        self.assertIn("PaymentReceipt.status == 'confirmed'", service)
        self.assertIn("PaymentInvoice.status", service)
        self.assertIn("i.status=='issued'", service)
        self.assertIn("PaymentSchedule.due_date < today", service)
        self.assertIn("PaymentSchedule.remaining_amount > 0", service)
        self.assertIn("PaymentSchedule.status != 'paid'", service)
        self.assertIn("max(value - collected, Decimal('0'))", service)
        self.assertIn("deposit + receipt_total", service)
        self.assertIn("overdue_over_90", service)
    def test_permissions_are_guarded(self):
        service=self.read('backend/app/services/report_service.py')
        constants=self.read('backend/app/permissions/constants.py')
        self.assertIn('reports.view.finance', service)
        self.assertIn('reports.export', service)
        self.assertIn('Bạn không có quyền xem báo cáo tài chính.', service)
        self.assertIn('Bạn không có quyền xuất báo cáo tài chính.', service)
        self.assertIn('reports.view.finance', constants)
        self.assertIn('reports.export', constants)
    def test_frontend_route_menu_uuid_links_and_export(self):
        routes=self.read('frontend/src/routes/AppRoutes.tsx')
        layout=self.read('frontend/src/layouts/AppLayout.tsx')
        page=self.read('frontend/src/features/reports/FinanceReportsPage.tsx')
        api=self.read('frontend/src/features/reports/api.ts')
        self.assertIn('/reports/finance', routes)
        self.assertIn('FinanceReportsPage', routes)
        self.assertIn('Báo cáo tài chính', layout)
        self.assertIn('Bạn không có quyền xem báo cáo tài chính.', page)
        for text in ['`/contracts/${i.contract_id}`','`/payments/${i.payment_id}`','`/receipts/${i.receipt_id}`','`/invoices/${i.invoice_id}`']:
            self.assertIn(text,page)
        self.assertNotIn('contract_code}`)', page)
        self.assertNotIn('payment_code}`)', page)
        self.assertIn('Xuất CSV', page)
        self.assertIn('/export?', api)
    def test_docs_updated(self):
        for path in ['docs/PROJECT_STATUS.md','docs/NEXT_SESSION_HANDOFF.md','docs/BUSINESS_RULES.md','docs/API_SPEC.md','docs/PERMISSION_SYSTEM.md','docs/DEVELOPMENT_PLAN.md','docs/TESTING_CHECKLIST.md']:
            text=self.read(path)
            self.assertIn('Sprint 18', text)
            self.assertIn('reports.view.finance', text)
            self.assertIn('receipt cancelled', text)
            self.assertIn('invoice draft/cancelled', text)
            self.assertIn('PMT overdue = due_date < today AND remaining > 0', text)
if __name__=='__main__': unittest.main()
