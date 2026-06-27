from pathlib import Path
import unittest

class Sprint20CommissionPayoutWorkflowSourceTest(unittest.TestCase):
    def read(self,path): return Path(path).read_text()
    def test_backend_model_migration_and_api_exist(self):
        model=self.read('backend/app/models/sales_commission.py'); migration=self.read('backend/alembic/versions/20260627_0014_sales_commissions.py'); api=self.read('backend/app/api/v1/commissions.py')
        for text in ['__tablename__ = "sales_commissions"','commission_code','contract_id','eligible_commission','approved_commission','paid_amount','__tablename__ = "sales_commission_events"']:
            self.assertIn(text, model)
        for text in ['sales_commissions','sales_commission_events','uq_sales_commissions_contract_id']:
            self.assertIn(text, migration)
        for route in ["@router.get('')","/summary","/export","/generate","/eligible-contracts","/{id}/approve","/{id}/mark-paid","/{id}/hold","/{id}/cancel"]:
            self.assertIn(route, api)
    def test_business_rules_are_explicit(self):
        service=self.read('backend/app/services/commission_service.py')
        for text in ["PaymentReceipt.status=='confirmed'","contract.status=='cancelled'","contract.status == 'completed' or total >= cv","estimated_commission=(cv*ratio)","Hoa hồng đã chi trả, không thể hủy.","Vui lòng nhập lý do tạm giữ.","Vui lòng nhập lý do hủy.","c.status in ('approved','paid')"]:
            self.assertIn(text, service)
    def test_permissions_and_frontend_routes(self):
        api=self.read('backend/app/api/v1/commissions.py'); constants=self.read('backend/app/permissions/constants.py'); routes=self.read('frontend/src/routes/AppRoutes.tsx'); layout=self.read('frontend/src/layouts/AppLayout.tsx')
        for perm in ['commissions.view','commissions.create','commissions.approve','commissions.mark_paid','commissions.hold','commissions.cancel','commissions.export']:
            self.assertIn(perm, api + constants)
        self.assertIn('/commissions', routes)
        self.assertIn('CommissionDetailPage', routes)
        self.assertIn('Hoa hồng', layout)
    def test_eligible_contract_search_returns_uuid_code_eligibility_and_duplicate_reason(self):
        api=self.read('backend/app/api/v1/commissions.py'); service=self.read('backend/app/services/commission_service.py'); frontend_api=self.read('frontend/src/features/commissions/api.ts'); modal=self.read('frontend/src/features/commissions/CommissionModals.tsx')
        for text in ["@router.get('/eligible-contracts')", 'search_eligible_contracts', "'contract_id': str(contract.id)", "'contract_code': contract.contract_code", "'is_eligible_for_commission': is_eligible", "Hợp đồng chưa hoàn tất hoặc chưa thu đủ tiền.", "Hợp đồng này đã có hoa hồng."]:
            self.assertIn(text, api + service)
        for text in ['searchEligibleContracts', 'Tìm hợp đồng', 'Nhập mã hợp đồng, tên khách hàng hoặc số điện thoại', 'selected.contract_id', 'contract_id: selected.contract_id', 'UUID nội bộ']:
            self.assertIn(text, frontend_api + modal)

    def test_frontend_vietnamese_ui_and_no_browser_prompts(self):
        combined='\n'.join(Path(p).read_text() for p in Path('frontend/src/features/commissions').glob('*.tsx'))
        for text in ['Quản lý hoa hồng','Hướng dẫn sử dụng','Tạo từ hợp đồng','Xuất CSV','Duyệt hoa hồng','Tạm giữ hoa hồng','Hủy hoa hồng','Đánh dấu đã chi trả','Phiếu thu đã hủy không được tính','Hóa đơn không quyết định hoa hồng']:
            self.assertIn(text, combined)
        styles=self.read('frontend/src/styles.css')
        for text in ['commission-kpi-grid', 'commission-guide-body', 'commission-modal-form', 'commission-contract-option', 'commission-table-card', 'commission-timeline-list']:
            self.assertIn(text, styles)
        self.assertIn('Modal title="Hướng dẫn sử dụng Quản lý hoa hồng"', combined)
        self.assertIn('Modal title="Tạo hoa hồng từ hợp đồng"', combined)
        for forbidden in ['window.alert','window.confirm','window.prompt']:
            self.assertNotIn(forbidden, combined)

if __name__=='__main__': unittest.main()
