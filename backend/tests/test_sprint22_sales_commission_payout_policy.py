from pathlib import Path
import unittest

class Sprint22SalesCommissionPayoutPolicySourceTest(unittest.TestCase):
    def read(self,path): return Path(path).read_text()
    def test_backend_policy_helpers_and_vietnamese_errors_exist(self):
        service=self.read('backend/app/services/commission_service.py')
        company=self.read('backend/app/services/company_commission_service.py')
        for text in ['get_company_commission_for_contract', 'get_sales_commission_payout_policy_context', '_paid_for_contract', 'remaining_payable_capacity', 'can_approve_sales_commission', 'can_mark_paid_sales_commission']:
            self.assertIn(text, service + company)
        for text in [
            'Hợp đồng chưa có khoản hoa hồng công ty, chưa thể duyệt hoa hồng sale.',
            'Hợp đồng chưa có khoản hoa hồng công ty, chưa thể chi hoa hồng sale.',
            'Khoản hoa hồng công ty đã hủy, không thể duyệt hoa hồng sale.',
            'Khoản hoa hồng công ty đã hủy, không thể chi hoa hồng sale.',
            'Khoản hoa hồng công ty đang tạm giữ, chưa thể duyệt hoa hồng sale.',
            'Khoản hoa hồng công ty đang tạm giữ, chưa thể chi hoa hồng sale.',
            'Công ty chưa nhận hoa hồng công ty, chưa thể chi hoa hồng sale.',
            'Số tiền chi hoa hồng sale không được vượt số hoa hồng công ty đã nhận.'
        ]:
            self.assertIn(text, service)
    def test_approve_and_mark_paid_policy_status_rules(self):
        service=self.read('backend/app/services/commission_service.py')
        for text in ["ccr.status=='cancelled'", "ccr.status=='on_hold'", "ccr.status not in ('pending','approved','partially_received','received')", "ccr.status not in ('partially_received','received') or received<=0", "if not policy['can_approve_sales_commission']: raise HTTPException(400, policy['approve_block_reason'])", "if not policy['can_mark_paid_sales_commission']: raise HTTPException(400, policy['mark_paid_block_reason'])", "if amt>dec(policy['remaining_payable_capacity']): raise HTTPException(400,'Số tiền chi hoa hồng sale không được vượt số hoa hồng công ty đã nhận.')"]:
            self.assertIn(text, service)
    def test_api_list_detail_include_policy_context(self):
        service=self.read('backend/app/services/commission_service.py')
        for text in ['company_commission_code','company_commission_status','company_commission_received_amount','company_commission_remaining_amount','can_approve_by_company_commission_policy','approve_block_reason','can_mark_paid_by_company_commission_policy','mark_paid_block_reason','payout_policy','company_commission']:
            self.assertIn(text, service)
        for text in ['missing_company_commission_count','blocked_mark_paid_count','total_company_commission_received_linked']:
            self.assertIn(text, service)
    def test_frontend_policy_ui_labels_and_gating(self):
        combined='\n'.join(Path(p).read_text() for p in Path('frontend/src/features/commissions').glob('*.tsx')) + self.read('frontend/src/features/commissions/api.ts')
        for text in ['HH công ty','Chưa có HH công ty','Chính sách chi hoa hồng sale','Hoa hồng công ty đã nhận','Tối đa có thể chi','Hoa hồng sale chỉ được chi trong phạm vi hoa hồng công ty đã nhận.','Đủ điều kiện duyệt','Chưa đủ điều kiện duyệt','Đủ điều kiện chi','Chưa đủ điều kiện chi','can_approve_by_company_commission_policy','can_mark_paid_by_company_commission_policy','remaining_payable_capacity']:
            self.assertIn(text, combined)
        self.assertIn("disabled={!approvePolicyOk}", combined)
        self.assertIn("disabled={!paidPolicyOk}", combined)

if __name__=='__main__': unittest.main()
