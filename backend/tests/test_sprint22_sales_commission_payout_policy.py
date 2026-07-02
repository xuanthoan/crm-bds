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
        self.assertIn('get_company_commissions_by_contract_ids', service + self.read('backend/app/services/company_commission_service.py'))
        list_block = service.split('def list_commissions', 1)[1].split('def summary', 1)[0]
        self.assertIn('ccr_by_contract=get_company_commissions_by_contract_ids', list_block)
        self.assertIn('paid_totals=dict', list_block)
        self.assertNotIn('items":[row(c) for c in items]', list_block)
        for text in ['missing_company_commission_count','blocked_mark_paid_count','total_company_commission_received_linked']:
            self.assertIn(text, service)

    def test_partial_sales_commission_payout_regression(self):
        service=self.read('backend/app/services/commission_service.py')
        page=self.read('frontend/src/features/commissions/CommissionsPage.tsx')
        modal=self.read('frontend/src/features/commissions/CommissionModals.tsx')
        api=self.read('frontend/src/features/commissions/api.ts')
        constants=self.read('frontend/src/features/commissions/constants.ts')
        for text in [
            '"partially_paid":"Đã chi một phần"',
            'def _sync_payout_status(c):',
            "elif approved > 0 and paid > 0:",
            "c.status='partially_paid'",
            "if c.status not in ('approved','partially_paid')",
            "c.paid_amount=dec(c.paid_amount)+amt",
            "remaining_sales=max(dec(c.approved_commission)-dec(c.paid_amount), D('0'))",
            "'sales_commission_remaining_amount': float(remaining_sales)",
        ]:
            self.assertIn(text, service)
        self.assertNotIn("c.status='paid'; c.paid_amount=amt", service)
        self.assertIn("max_payable=min(remaining_sales, capacity)", service)
        self.assertIn("['approved', 'partially_paid'].includes(c.status)", page)
        self.assertIn('<option value="partially_paid">Đã chi một phần</option>', page)
        self.assertIn("['Đã chi một phần', summary.partially_paid_count || 0]", page)
        self.assertIn("markPaidDefaultAmount", modal)
        self.assertIn("Math.min(remainingSalePayout", modal)
        self.assertIn("Còn phải chi sale", modal)
        self.assertIn("Tối đa có thể chi lần này", modal)
        self.assertIn("sales_commission_remaining_amount", api)
        self.assertIn("partially_paid: 'Đã chi một phần'", constants)

    def test_frontend_policy_ui_labels_and_gating(self):
        combined='\n'.join(Path(p).read_text() for p in Path('frontend/src/features/commissions').glob('*.tsx')) + self.read('frontend/src/features/commissions/api.ts')
        for text in ['HH công ty','Chưa có HH công ty','Chính sách chi hoa hồng sale','Hoa hồng công ty đã nhận','Tối đa có thể chi','Hoa hồng sale chỉ được chi trong phạm vi hoa hồng công ty đã nhận.','Đủ điều kiện duyệt','Chưa đủ điều kiện duyệt','Đủ điều kiện chi','Chưa đủ điều kiện chi','can_approve_by_company_commission_policy','can_mark_paid_by_company_commission_policy','remaining_payable_capacity']:
            self.assertIn(text, combined)
        self.assertIn("disabled={!approvePolicyOk}", combined)
        self.assertIn("disabled={!paidPolicyOk}", combined)


    def test_commissions_table_layout_regression_for_policy_columns(self):
        page=self.read('frontend/src/features/commissions/CommissionsPage.tsx')
        styles=self.read('frontend/src/styles.css')
        for text in ['commission-table-scroll', 'commission-table-top-scroll', 'commission-table-scroll-spacer', 'syncTableScroll', 'tableScrollRef', 'topScrollRef', 'commission-policy-table', 'commission-company-column', 'commission-company-cell', 'commission-company-missing-badge', 'commission-policy-blocked-caption']:
            self.assertIn(text, page + styles)
        self.assertIn('min-width: 104rem', styles)
        self.assertIn('overflow-x: auto', styles)
        self.assertIn('title={blockedReason}', page)
        self.assertIn("title={policyReason(c, 'approve') || undefined}", page)
        self.assertIn("title={policyReason(c, 'paid') || undefined}", page)
        self.assertNotIn('<small className="muted-text">{policyReason', page)
        self.assertNotIn('className="form-warning">Chưa có HH công ty', page)


    def test_required_marks_and_loading_states_for_commission_modals(self):
        sale_modals=self.read('frontend/src/features/commissions/CommissionModals.tsx')
        sale_page=self.read('frontend/src/features/commissions/CommissionsPage.tsx')
        company_modals=self.read('frontend/src/features/companyCommissions/CompanyCommissionModals.tsx')
        company_page=self.read('frontend/src/features/companyCommissions/CompanyCommissionsPage.tsx')
        styles=self.read('frontend/src/styles.css')
        for text in ['required-mark', 'Số tiền duyệt *', 'Số tiền đã chi trả *', 'Lý do tạm giữ *', 'Lý do hủy *']:
            self.assertIn(text, sale_modals + styles)
        self.assertNotIn('Tìm hợp đồng <RequiredMark />', sale_modals)
        self.assertNotIn('Tỷ lệ hoa hồng (%) <RequiredMark />', sale_modals)
        self.assertNotIn('RequiredMark', sale_modals)
        required_block = styles.split('.required-mark', 1)[1].split('}', 1)[0]
        self.assertIn('color: inherit', required_block)
        self.assertIn('display: inline', required_block)
        self.assertNotIn('display: block', required_block)
        self.assertNotIn('#d92d20', required_block)
        for text in ['Hoa hồng xác nhận *', 'Số tiền nhận lần này *', 'Lý do tạm giữ *', 'Lý do hủy *']:
            self.assertIn(text, company_modals)
        self.assertNotIn('Tìm hợp đồng <RequiredMark />', company_modals)
        self.assertNotIn('Tỷ lệ hoa hồng công ty (%) <RequiredMark />', company_modals)
        self.assertNotIn('RequiredMark', company_modals)
        for text in ['isSubmitting', 'Đang tạo...', 'Đang xử lý...', 'disabled={isSubmitting', 'isSearching', 'Đang tìm...']:
            self.assertIn(text, sale_modals + company_modals)
        for text in ['isFiltering', 'isClearingFilters', 'Đang lọc...', 'Đang xóa...', 'Promise.all']:
            self.assertIn(text, sale_page + company_page)

if __name__=='__main__': unittest.main()
