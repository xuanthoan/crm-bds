from pathlib import Path
import unittest

class Sprint19CommissionRevenueReportsSourceTest(unittest.TestCase):
    def read(self, path): return Path(path).read_text()
    def test_backend_endpoints_and_permissions(self):
        api=self.read('backend/app/api/v1/reports.py'); service=self.read('backend/app/services/report_service.py'); constants=self.read('backend/app/permissions/constants.py')
        for text in ['/commissions/summary','/commissions','/revenue/by-sale','/revenue/by-source','/revenue/by-project','/commissions/export','/revenue/by-sale/export','/revenue/by-source/export','/revenue/by-project/export']:
            self.assertIn(text, api)
        for perm in ['reports.view.commissions','reports.view.revenue','reports.export']:
            self.assertIn(perm, service + api + constants)
    def test_commission_rules_are_explicit(self):
        service=self.read('backend/app/services/report_service.py')
        self.assertIn("PaymentReceipt.status == 'confirmed'", service)
        self.assertIn("deposit + receipt_total", service)
        self.assertIn("c.status == 'completed' or collected >= value", service)
        self.assertIn("c.status == 'cancelled'", service)
        self.assertIn("estimated = value * ratio", service)
        self.assertIn("collected_commission = collected * ratio", service)
    def test_csv_and_uuid_contract_route_fields(self):
        api=self.read('backend/app/api/v1/reports.py'); service=self.read('backend/app/services/report_service.py')
        self.assertIn("buf.write('\\ufeff')", service)
        self.assertIn('bao-cao-hoa-hong-sale', api)
        self.assertIn('doanh-thu-theo-sale', api)
        self.assertIn("'contract_id': str(c.id)", service)
        self.assertIn("'contract_code': c.contract_code", service)
    def test_frontend_route_menu_guide_and_export(self):
        routes=self.read('frontend/src/routes/AppRoutes.tsx'); layout=self.read('frontend/src/layouts/AppLayout.tsx'); page=self.read('frontend/src/features/reports/CommissionRevenueReportsPage.tsx'); guide=self.read('frontend/src/features/reports/CommissionRevenueGuideModal.tsx')
        self.assertIn('/reports/commissions', routes)
        self.assertIn('Báo cáo hoa hồng', layout)
        for text in ['Báo cáo hoa hồng & doanh thu','Hướng dẫn sử dụng','Tỷ lệ hoa hồng (%)','Hoa hồng','Doanh thu theo sale','Doanh thu theo nguồn','Doanh thu theo dự án','downloadCommissionRevenueCsv','/contracts/${i.contract_id}']:
            self.assertIn(text, page)
        for text in ['Phiếu thu đã hủy không được tính', 'Hóa đơn không quyết định hoa hồng', 'Đây là báo cáo tạm tính']:
            self.assertIn(text, guide)

if __name__ == '__main__':
    unittest.main()
