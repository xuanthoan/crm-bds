import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class Sprint17ReceiptInvoiceContractCompletionSourceTest(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text(encoding='utf-8')

    def test_receipt_routes_and_rules_exist(self):
        api = self.read('backend/app/api/v1/payments.py')
        service = self.read('backend/app/services/payment_service.py')
        self.assertIn('/payment-receipts', api)
        self.assertIn('/payment-receipts/{receipt_id}', api)
        self.assertIn('/confirm', api)
        self.assertIn('/cancel', api)
        self.assertIn('Số tiền thanh toán phải lớn hơn 0', service)
        self.assertIn('Không thể thanh toán vượt quá số tiền còn lại', service)
        self.assertIn('Ngày thanh toán là bắt buộc khi xác nhận', service)
        self.assertIn('Lý do hủy phiếu thu', self.read('backend/app/schemas/payment.py'))
        self.assertIn('cancel_reason', self.read('backend/app/models/payment_receipt.py'))
        self.assertIn("p.paid_amount=max", service)

    def test_invoice_routes_and_lifecycle_exist(self):
        api = self.read('backend/app/api/v1/payments.py')
        service = self.read('backend/app/services/payment_service.py')
        model = self.read('backend/app/models/payment_invoice.py')
        for text in ['/invoices', '/invoices/{invoice_id}', '/issue', '/cancel']:
            self.assertIn(text, api)
        for text in ['receipt_id', 'deal_id', 'property_unit_id', 'issued_at', 'cancelled_at', 'cancel_reason']:
            self.assertIn(text, model)
        self.assertIn("status='draft'", service)
        self.assertIn("inv.status='issued'", service)
        self.assertIn("inv.status='cancelled'", service)
        self.assertIn('Lý do hủy hóa đơn là bắt buộc', service)

    def test_contract_completion_guard_and_timeline(self):
        service = self.read('backend/app/services/contract_service.py')
        constants = self.read('backend/app/contracts/constants.py')
        self.assertIn('Không thể hoàn tất hợp đồng vì chưa thanh toán đủ', service)
        self.assertIn('paid < (item.contract_value', service)
        self.assertIn('Hợp đồng {item.contract_code} đã hoàn tất sau khi thanh toán đủ', service)
        self.assertIn('payment_invoice_issued', constants)
        self.assertIn('payment_invoice_cancelled', constants)

    def test_frontend_routes_and_print_views_exist(self):
        routes = self.read('frontend/src/routes/AppRoutes.tsx')
        self.assertIn('/receipts', routes)
        self.assertIn('/invoices', routes)
        self.assertIn('ReceiptDetailPage', routes)
        self.assertIn('InvoiceDetailPage', routes)
        self.assertIn('window.print()', self.read('frontend/src/features/receipts/ReceiptDetailPage.tsx'))
        self.assertIn('window.print()', self.read('frontend/src/features/invoices/InvoiceDetailPage.tsx'))
        self.assertNotIn('stub', self.read('frontend/src/features/invoices/InvoiceDetailPage.tsx').lower())

    def test_payment_detail_uses_uuid_routes_and_cancel_modal(self):
        detail = self.read('frontend/src/features/payments/PaymentDetailPage.tsx')
        self.assertIn('navigateTo(`/receipts/${receipt.id}`)', detail)
        self.assertIn('navigateTo(`/invoices/${invoice.id}`)', detail)
        self.assertNotIn('receipt.receipt_code}`)', detail)
        self.assertNotIn('invoice.invoice_code}`)', detail)
        self.assertIn('CancelReasonModal', detail)
        self.assertIn('Vui lòng nhập lý do hủy phiếu thu.', detail)
        self.assertIn('cancel_reason: reason', detail)

    def test_cancel_reason_modals_replace_browser_prompts(self):
        receipt = self.read('frontend/src/features/receipts/ReceiptDetailPage.tsx')
        invoice = self.read('frontend/src/features/invoices/InvoiceDetailPage.tsx')
        modal = self.read('frontend/src/features/payments/CancelReasonModal.tsx')
        self.assertNotIn('window.prompt', receipt)
        self.assertNotIn('window.prompt', invoice)
        self.assertIn('Hủy phiếu thu sẽ trừ lại số tiền đã thu khỏi lịch thanh toán', receipt)
        self.assertIn('Hủy hóa đơn sẽ chuyển hóa đơn sang trạng thái đã hủy', invoice)
        self.assertIn('trim()', modal)
        self.assertIn('Hủy thao tác', modal)
        self.assertIn('Xác nhận hủy', receipt + invoice)

if __name__ == '__main__':
    unittest.main()
