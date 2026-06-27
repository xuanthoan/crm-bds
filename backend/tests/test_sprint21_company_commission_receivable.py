from pathlib import Path
import unittest

class Sprint21CompanyCommissionReceivableSourceTest(unittest.TestCase):
    def read(self,path): return Path(path).read_text()
    def test_model_migration_api_permissions_exist(self):
        model=self.read('backend/app/models/company_commission.py'); migration=self.read('backend/alembic/versions/20260627_0015_company_commission_receivables.py'); api=self.read('backend/app/api/v1/company_commissions.py'); perms=self.read('backend/app/permissions/constants.py')
        for text in ['__tablename__ = "company_commission_receivables"','receivable_code','expected_commission_amount','confirmed_receivable_amount','received_amount','remaining_amount','__tablename__ = "company_commission_events"']:
            self.assertIn(text, model)
        for text in ['company_commission_receivables','company_commission_events','company_role','brokerage_policy_note','uq_company_commission_receivables_contract_id']:
            self.assertIn(text, migration)
        for route in ["@router.get('')","/summary","/eligible-contracts","/generate","/{id}/approve","/{id}/receive","/{id}/hold","/{id}/cancel","/export"]:
            self.assertIn(route, api)
        for perm in ['company_commissions.view','company_commissions.create','company_commissions.approve','company_commissions.receive','company_commissions.hold','company_commissions.cancel','company_commissions.export']:
            self.assertIn(perm, api+perms)
    def test_business_rules_and_vietnamese_errors(self):
        service=self.read('backend/app/services/company_commission_service.py')
        for text in ["LEGAL={'signed','active','completed'}","Hợp đồng chưa đủ trạng thái pháp lý để tạo hoa hồng công ty.","Hợp đồng đã hủy, không thể tạo hoa hồng công ty.","Hợp đồng này đã có khoản hoa hồng công ty.","exp=dec(expected) if expected is not None else (dec(c.contract_value)*rate/D('100')).quantize(D('0.01'))","Hoa hồng xác nhận không được vượt quá hoa hồng dự kiến.","Số tiền nhận lần này phải lớn hơn 0.","Khoản hoa hồng công ty đã nhận tiền, không thể hủy.","Vui lòng nhập lý do tạm giữ.","Vui lòng nhập lý do hủy.","r.status='received' if r.remaining_amount==0 else 'partially_received'"]:
            self.assertIn(text, service)
    def test_contract_fields_and_frontend_route_menu_modals(self):
        contract=self.read('backend/app/models/contract.py')+self.read('backend/app/schemas/contract.py')+self.read('backend/app/services/contract_service.py')
        routes=self.read('frontend/src/routes/AppRoutes.tsx'); layout=self.read('frontend/src/layouts/AppLayout.tsx'); page=self.read('frontend/src/features/companyCommissions/CompanyCommissionsPage.tsx'); modals=self.read('frontend/src/features/companyCommissions/CompanyCommissionModals.tsx'); detail=self.read('frontend/src/features/companyCommissions/CompanyCommissionDetailPage.tsx')
        for text in ['company_role','actual_seller_type','actual_seller_name','commission_payer_type','commission_payer_name','brokerage_contract_code','brokerage_policy_note']:
            self.assertIn(text, contract)
        for text in ['/company-commissions','CompanyCommissionDetailPage','Hoa hồng công ty','Theo dõi hoa hồng công ty phải thu','Tạo từ hợp đồng','Xuất CSV','Bạn đang thao tác hoa hồng công ty:','Số tiền nhận lần này','Hợp đồng chưa đủ trạng thái pháp lý để tạo hoa hồng công ty.','Quay lại danh sách','Timeline thao tác']:
            self.assertIn(text, routes+layout+page+modals+detail)
    def test_action_gating_source(self):
        page=self.read('frontend/src/features/companyCommissions/CompanyCommissionsPage.tsx')
        self.assertIn("i.status==='pending'||i.status==='on_hold'", page)
        self.assertIn("i.status==='approved'||i.status==='partially_received'", page)
        self.assertIn("i.status==='pending'||i.status==='approved'", page)
        self.assertIn("i.status==='pending'||i.status==='approved'||i.status==='on_hold'", page)
        self.assertNotIn("window.confirm", page)
    def test_export_csv_vietnamese_headers(self):
        service=self.read('backend/app/services/company_commission_service.py')
        for header in ['Mã hoa hồng công ty','Mã hợp đồng','Khách hàng','Sale','Vai trò công ty','Bên bán thực tế','Bên trả hoa hồng','HH dự kiến','HH xác nhận','Đã nhận','Còn phải thu','Trạng thái','Ngày dự kiến nhận','Ngày nhận đủ','Ghi chú']:
            self.assertIn(header, service)

if __name__=='__main__': unittest.main()
