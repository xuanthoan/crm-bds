from pathlib import Path
import unittest

class Sprint24SalesCommissionPaymentVoucherSourceTest(unittest.TestCase):
    def read(self,p): return Path(p).read_text()
    def test_backend_model_migration_permissions_api(self):
        model=self.read('backend/app/models/commission_payment_voucher.py'); migration=self.read('backend/alembic/versions/20260703_0018_sales_commission_payment_vouchers.py'); api=self.read('backend/app/api/v1/commission_payment_vouchers.py'); perms=self.read('backend/app/permissions/constants.py')
        for text in ['__tablename__ = "sales_commission_payment_vouchers"','sales_commission_id','contract_id','sale_id','payment_method','payment_reference','cancel_reason','attachment_url','ck_sales_commission_payment_vouchers_amount_positive']:
            self.assertIn(text, model)
        for text in ['legacy_paid_amount','UPDATE sales_commissions SET legacy_paid_amount = COALESCE(paid_amount, 0)','sales_commission_payment_vouchers','uq_sales_commission_payment_vouchers_code']:
            self.assertIn(text, migration)
        for perm in ['commissions.payment_vouchers.view','commissions.payment_vouchers.create','commissions.payment_vouchers.update','commissions.payment_vouchers.mark_paid','commissions.payment_vouchers.cancel','commissions.payment_vouchers.cancel_paid','commissions.payment_vouchers.export']:
            self.assertIn(perm, perms + api)
    def test_service_business_rules(self):
        service=self.read('backend/app/services/commission_payment_voucher_service.py') + self.read('backend/app/services/commission_service.py')
        for text in ['recalculate_sales_commission_paid_amount','sync_commission_paid_amount_from_vouchers','legacy_paid_amount','status==\'paid\'','remaining_payable_capacity','Số tiền chi không được vượt quá hạn mức có thể chi.','Hoa hồng này chưa được duyệt.','Phiếu chi đã hủy nên không thể thao tác.','Vui lòng nhập lý do hủy phiếu chi.','commissions.payment_vouchers.cancel_paid','payment_voucher_paid','payment_voucher_cancelled']:
            self.assertIn(text, service)
    def test_frontend_routes_labels_and_modal_terms(self):
        combined='\n'.join(Path(p).read_text() for p in ['frontend/src/features/commissionPaymentVouchers/api.ts','frontend/src/features/commissionPaymentVouchers/CommissionPaymentVouchersPage.tsx','frontend/src/features/commissionPaymentVouchers/CommissionPaymentVoucherDetailPage.tsx','frontend/src/layouts/AppLayout.tsx','frontend/src/routes/AppRoutes.tsx'])
        for text in ['/commission-payment-vouchers','Phiếu chi hoa hồng','Nháp','Đã chi','Đã hủy','Tiền mặt','Chuyển khoản','Khác','Mã giao dịch/chứng từ','Xác nhận đã chi', "Number(c.paid_amount || 0) < Number(c.approved_commission || 0)"]:
            self.assertIn(text, combined + self.read('frontend/src/features/commissions/CommissionsPage.tsx'))
        self.assertNotIn('{v.status}</td>', combined)
        self.assertNotIn('{v.payment_method}</td>', combined)

if __name__=='__main__': unittest.main()
