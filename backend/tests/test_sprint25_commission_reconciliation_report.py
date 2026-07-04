from pathlib import Path
import unittest

class Sprint25CommissionReconciliationReportSourceTest(unittest.TestCase):
    def read(self,p): return Path(p).read_text()
    def test_backend_api_permissions_and_paid_amount_logic(self):
        service=self.read('backend/app/services/commission_reconciliation_report_service.py')
        api=self.read('backend/app/api/v1/commission_reconciliation_report.py')
        perms=self.read('backend/app/permissions/constants.py')
        routes=self.read('backend/app/api/v1/__init__.py')
        for text in ['/commission-reconciliation-report','/export','reports.commission_reconciliation.view','reports.commission_reconciliation.export']:
            self.assertIn(text, api + perms + routes)
        for text in ['sync_commission_paid_amount_from_vouchers(db,c)','legacy_paid_amount','status==\'paid\'','status==\'draft\'','status==\'cancelled\'','remaining_payable_capacity','blocked_by_policy','over_paid','over_received','draft_voucher_pending']:
            self.assertIn(text, service + self.read('backend/app/services/commission_service.py'))
    def test_summary_filters_and_csv_fields(self):
        service=self.read('backend/app/services/commission_reconciliation_report_service.py')
        for text in ['total_company_commission_confirmed','total_company_commission_received','total_company_commission_remaining','total_sales_commission_approved','total_sales_commission_paid','total_sales_commission_remaining','total_remaining_payable_capacity','draft_voucher_count','paid_voucher_count','cancelled_voucher_count','sale_unpaid_count','sale_partially_paid_count','sale_paid_count','blocked_by_policy_count','over_paid_count','over_received_count']:
            self.assertIn(text, service)
        self.assertIn('def _apply_filters(query, actor=None, **fil):', service)
        self.assertNotIn('def _apply_filters(q, actor=None, **fil):', service)
        for text in ['project_id','sale_id','contract_id','customer_id','company_commission_status','sales_commission_status','voucher_status','reconciliation_status','has_draft_voucher','only_blocked_by_policy','only_has_remaining_sale_payable','Contract.contract_code.ilike','Customer.full_name.ilike','Project.name.ilike','User.full_name.ilike','SalesCommission.commission_code.ilike','CompanyCommissionReceivable.receivable_code.ilike']:
            self.assertIn(text, service)
        for header in ['Mã hợp đồng','Dự án','Khách hàng','Sale','Mã HH công ty','Trạng thái HH công ty','HH công ty xác nhận','HH công ty đã nhận','HH công ty còn phải thu','Mã HH sale','Trạng thái HH sale','HH sale đã duyệt','HH sale đã chi','HH sale còn phải chi','Chính sách chi','Hạn mức còn có thể chi','Phiếu nháp','Phiếu đã chi','Trạng thái đối soát','Cảnh báo']:
            self.assertIn(header, service)
        self.assertIn("export_filters.pop('page', None)", service)
        self.assertIn("export_filters.pop('page_size', None)", service)
    def test_frontend_route_menu_labels_and_no_raw_enums(self):
        combined='\n'.join(Path(p).read_text() for p in ['frontend/src/features/commissionReconciliationReport/api.ts','frontend/src/features/commissionReconciliationReport/CommissionReconciliationReportPage.tsx','frontend/src/layouts/AppLayout.tsx','frontend/src/routes/AppRoutes.tsx','frontend/src/styles.css'])
        for text in ['/commission-reconciliation-report','Đối soát hoa hồng','Báo cáo đối soát hoa hồng','Theo dõi hoa hồng công ty đã thu','Từ ngày','Đến ngày','Dự án','Sale','Trạng thái đối soát','Tìm kiếm','Lọc','Xóa lọc','Xuất CSV','Chưa có dữ liệu đối soát hoa hồng.','Không tải được báo cáo đối soát hoa hồng.','Bị chặn theo chính sách','Công ty chưa thu đủ','Sale đã chi một phần']:
            self.assertIn(text, combined)
        self.assertIn('.then((res)=>res.data)', combined)
        self.assertIn('API_BASE_URL', combined)
        self.assertIn('/api/v1/commission-reconciliation-report/export', combined)
        self.assertIn('Content-Disposition', combined)
        self.assertIn('const items=data?.items ?? [];', combined)
        self.assertIn('(r.reconciliation_flags ?? []).map', combined)
        self.assertIn('items.length===0', combined)
        self.assertIn('commission-reconciliation-scroll', combined)
        self.assertIn('min-width: 140rem', combined)
        self.assertIn('width: 140rem', combined)
        self.assertIn('commission-reconciliation-table', combined)
        self.assertIn('commission-reconciliation-money', combined)
        self.assertNotIn('data?.items.map', combined)
        self.assertNotIn('{r.reconciliation_status}', combined)

if __name__=='__main__': unittest.main()
