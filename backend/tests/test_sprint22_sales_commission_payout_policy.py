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

    def test_contracts_page_has_pagination_for_seeded_contracts(self):
        page=self.read('frontend/src/features/contracts/ContractsPage.tsx')
        api=self.read('backend/app/api/v1/contracts.py') + self.read('backend/app/services/contract_service.py')
        for text in ["page:int=Query(1,ge=1)", "page_size:int=Query(20,ge=1,le=100)", "order_by(Contract.created_at.desc())", "\"total_pages\":ceil(total/page_size)"]:
            self.assertIn(text, api)
        for text in ["const [page, setPage]", "setMeta(response.meta", "page_size: '20'", "Trang trước", "Trang sau", "Tổng {Number(meta.total || items.length)} hợp đồng", "className=\"pagination-row\""]:
            self.assertIn(text, page)

    def test_payment_invoice_duplicate_guard_and_frontend_button_state(self):
        service=self.read('backend/app/services/payment_service.py')
        detail=self.read('frontend/src/features/payments/PaymentDetailPage.tsx')
        forms=self.read('frontend/src/features/payments/PaymentForms.tsx')
        for text in ["existing_invoice=db.scalar", "PaymentInvoice.payment_schedule_id==p.id", "PaymentInvoice.status!='cancelled'", "Đợt thanh toán này đã có hóa đơn, không thể tạo thêm hóa đơn nháp."]:
            self.assertIn(text, service)
        self.assertIn("hasActiveInvoice = (item.invoices || []).some((invoice) => invoice.status !== 'cancelled')", detail)
        self.assertIn("disabled={hasActiveInvoice}", detail)
        self.assertIn("disabledMessage={hasActiveInvoice ? invoiceDuplicateMessage : undefined}", detail)
        self.assertIn("disabled?: boolean", forms)
        self.assertIn("return setErrors([disabledMessage || 'Đợt thanh toán này đã có hóa đơn, không thể tạo thêm hóa đơn nháp.'])", forms)

    def test_frontend_localizes_commission_contract_payment_enums_and_timelines(self):
        company_constants=self.read('frontend/src/features/companyCommissions/constants.ts')
        company_detail=self.read('frontend/src/features/companyCommissions/CompanyCommissionDetailPage.tsx')
        company_page=self.read('frontend/src/features/companyCommissions/CompanyCommissionsPage.tsx')
        commission_detail=self.read('frontend/src/features/commissions/CommissionDetailPage.tsx')
        for text in ["our_company:'Công ty của tôi'", "developer:'Chủ đầu tư'", "landlord:'Chủ nhà / chủ đất'", "partner:'Đối tác'", "customer:'Khách hàng'", "investor:'Chủ đầu tư / Nhà đầu tư'", "seller:'Bên bán'", "buyer_representative:'Đại diện bên mua'", "created:'Tạo mới'", "received:'Ghi nhận đã nhận tiền'", "partially_received:'Ghi nhận nhận một phần'", "held:'Tạm giữ'", "marked_paid:'Đánh dấu đã chi trả'"]:
            self.assertIn(text, company_constants)
        for text in ["label(CONTRACT_STATUS_LABELS, item.contract?.status)", "label(COMMISSION_PARTY_LABELS, item.actual_seller_type)", "label(COMMISSION_PARTY_LABELS, item.commission_payer_type)", "label(COMPANY_COMMISSION_EVENT_LABELS, event.event_type)", "dateTime(event.created_at)"]:
            self.assertIn(text, company_detail)
        self.assertIn("COMMISSION_PARTY_LABELS[item.commission_payer_type || '']", company_page)
        self.assertIn("label(CONTRACT_STATUS_LABELS,c.contract_status)", commission_detail)
        self.assertIn("e.title || label(COMMISSION_STATUS_LABELS,e.event_type)", commission_detail)

    def test_approve_amount_defaults_and_boundary_validation_are_safe(self):
        sale_modal=self.read('frontend/src/features/commissions/CommissionModals.tsx')
        company_modal=self.read('frontend/src/features/companyCommissions/CompanyCommissionModals.tsx')
        sale_service=self.read('backend/app/services/commission_service.py')
        company_service=self.read('backend/app/services/company_commission_service.py')
        for text in ['moneyInputValue', 'Math.round(Number(value || 0))', 'approveMaxAmount', "type === 'approve' ? moneyInputValue(approveMaxAmount)"]:
            self.assertIn(text, sale_modal + company_modal)
        self.assertIn('const moneyInputValue = (value: unknown)', company_modal)
        self.assertIn('const moneyLimit = (value: unknown)', company_modal)
        self.assertIn('COMPANY_COMMISSION_STATUS_LABELS', company_modal)
        self.assertIn('COMMISSION_PARTY_LABELS', company_modal)
        self.assertIn('Trạng thái {label(COMPANY_COMMISSION_STATUS_LABELS, item.status)}', company_modal)
        self.assertNotIn('Trạng thái {item.status}', company_modal)
        self.assertIn('if (v <= 0) return setErr(\'Số tiền duyệt phải lớn hơn 0.\')', sale_modal)
        self.assertIn('if (v > approveMaxAmount)', sale_modal)
        self.assertIn('if (v > remainingSalePayout)', sale_modal)
        self.assertIn('if (v > cap)', sale_modal)
        self.assertIn("numericAmount <= 0", company_modal)
        self.assertIn('numericAmount > approveMaxAmount', company_modal)
        self.assertIn('numericAmount > receiveMaxAmount', company_modal)
        for forbidden in ['- 0.01', '-0.01', '- 0.04', '-0.04', '< approveMaxAmount', '< receiveMaxAmount']:
            self.assertNotIn(forbidden, sale_modal + company_modal)
        for text in ['ROUND_HALF_UP', 'def money_limit(v):', 'max_approve=money_limit', 'if amt<=0 or amt>max_approve']:
            self.assertIn(text, sale_service)
        for text in ['ROUND_HALF_UP', 'def money_limit(v):', 'max_approve=money_limit', 'if amt>max_approve']:
            self.assertIn(text, company_service)

if __name__=='__main__': unittest.main()

class Sprint23CommissionPayoutPolicyConfigurationSourceTest(unittest.TestCase):
    def read(self,path): return Path(path).read_text()
    def test_backend_policy_configuration_api_and_storage(self):
        combined = '\n'.join(self.read(path) for path in [
            'backend/app/models/system_setting.py',
            'backend/app/services/settings_service.py',
            'backend/app/api/v1/settings.py',
            'backend/app/api/v1/__init__.py',
            'backend/alembic/versions/20260703_0016_system_settings_commission_payout_policy.py',
        ])
        for text in ['system_settings', 'sales_commission_payout_policy', 'received_amount_capacity', 'received_ratio', "'/settings'", "'/commission-payout-policy'", 'settings.manage_master_data']:
            self.assertIn(text, combined)

    def test_backend_ratio_policy_formula_and_mark_paid_guard(self):
        service = self.read('backend/app/services/commission_service.py')
        for text in ['policy_code=get_sales_commission_payout_policy_code', 'received_ratio=(received/confirmed) if confirmed > 0 else D(\'0\')', 'max_total_sales_commission_payable=money_limit(approved * received_ratio)', 'capacity=max(max_total_sales_commission_payable-current_paid, D(\'0\'))', 'max_payable=min(remaining_sales, capacity)', 'company_commission_received_ratio', 'payout_policy_label', 'Số tiền chi hoa hồng sale vượt tối đa có thể chi theo chính sách hiện tại.']:
            self.assertIn(text, service)

    def test_frontend_policy_settings_and_vietnamese_labels(self):
        combined='\n'.join(self.read(path) for path in [
            'frontend/src/features/settings/CommissionPayoutPolicySettingsPage.tsx',
            'frontend/src/features/settings/api.ts',
            'frontend/src/features/commissions/CommissionModals.tsx',
            'frontend/src/features/commissions/CommissionDetailPage.tsx',
            'frontend/src/features/commissions/CommissionsPage.tsx',
            'frontend/src/routes/AppRoutes.tsx',
            'frontend/src/layouts/AppLayout.tsx',
        ])
        for text in ['Cài đặt chính sách chi hoa hồng sale', 'Chi theo hạn mức tiền hoa hồng công ty đã nhận', 'Chi theo tỷ lệ hoa hồng công ty đã thu', 'Tỷ lệ đã thu', 'Tối đa có thể chi lần này', 'payout_policy_label']:
            self.assertIn(text, combined)
        self.assertNotIn('{commission.payout_policy?.payout_policy_code}', combined)
