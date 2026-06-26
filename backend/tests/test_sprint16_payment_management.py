import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def read(path): return (ROOT/path).read_text(encoding='utf-8')

class Sprint16PaymentManagementSourceTest(unittest.TestCase):
    def test_models_and_migration_define_required_tables_and_indexes(self):
        migration=read('backend/alembic/versions/20260625_0012_payment_management.py')
        for table in ('payment_schedules','payment_receipts','payment_invoices'):
            self.assertIn(table,migration)
        for index in ('ix_payment_schedules_contract_id','ix_payment_schedules_deal_id','ix_payment_schedules_customer_id','ix_payment_schedules_status','ix_payment_schedules_due_date','ix_payment_schedules_payment_code','ix_payment_receipts_payment_schedule_id','ix_payment_receipts_receipt_code'):
            self.assertIn(index,migration)
        self.assertIn('uq_payment_schedules_contract_sequence', migration)
    def test_schedule_validation_rules(self):
        schema=read('backend/app/schemas/payment.py'); service=read('backend/app/services/payment_service.py')
        self.assertIn('Số tiền phải thu phải lớn hơn 0.', schema)
        self.assertIn("c.status=='cancelled'", service)
        self.assertIn('Không thể tạo lịch thanh toán cho hợp đồng đã hủy.', service)
        self.assertIn('Số thứ tự đợt thanh toán đã tồn tại', service)
    def test_receipt_business_rules(self):
        schema=read('backend/app/schemas/payment.py'); service=read('backend/app/services/payment_service.py')
        self.assertIn('Số tiền thanh toán phải lớn hơn 0.', schema)
        self.assertIn('Ngày thanh toán là bắt buộc khi xác nhận.', schema+service)
        self.assertIn('Không thể thanh toán vượt quá số tiền còn lại.', service)
        self.assertIn("if r.status=='confirmed': p.paid_amount=max", service)
        self.assertIn("payload.status=='confirmed'", service)
        self.assertIn("p.status='partial'", service)
        self.assertIn("p.status='paid'", service)
    def test_penalty_and_overdue_rules(self):
        schema=read('backend/app/schemas/payment.py'); service=read('backend/app/services/payment_service.py')
        self.assertIn('Phí phạt không được âm.', schema)
        self.assertIn('Phí phạt phải có lý do.', schema)
        self.assertIn("p.expected_amount or Decimal('0')", service)
        self.assertIn("p.due_date < date.today()", service)
        self.assertIn("p.status not in {'paid','cancelled'}", service)
    def test_timeline_notification_task_vietnamese_copy(self):
        service=read('backend/app/services/payment_service.py')
        for text in ('Tạo lịch thanh toán','Xác nhận thanh toán','đã được thanh toán đủ','đã quá hạn','Áp dụng phí phạt','Đợt thanh toán đã quá hạn','Khách hàng đã thanh toán một phần','Khách hàng đã thanh toán đủ'):
            self.assertIn(text, service)
        self.assertIn('create_auto_task_if_not_exists', service)
    def test_query_safety_uses_selectinload_not_joinedload(self):
        service=read('backend/app/services/payment_service.py')
        self.assertIn('selectinload', service)
        self.assertNotIn('joinedload', service)
        self.assertIn('load_only', service)

    def test_schedule_total_cannot_exceed_contract_value(self):
        service=read('backend/app/services/payment_service.py')
        self.assertIn('Hợp đồng chưa có giá trị hợp đồng hợp lệ.', service)
        self.assertIn('Tổng lịch thanh toán không được vượt quá số tiền còn phải thu sau cọc.', service)
        self.assertIn("PaymentSchedule.status != 'cancelled'", service)
        self.assertIn('exclude_schedule_id=p.id', service)
        self.assertIn('schedulable_amount', service)
        self.assertIn('contract.deposit_value or Decimal', service)

    def test_payments_page_contract_selector_is_friendly(self):
        form=read('frontend/src/features/payments/PaymentForms.tsx')
        self.assertIn('Tìm hợp đồng theo mã HD, SĐT khách hàng hoặc mã deal', form)
        self.assertIn('Chọn hợp đồng', form)
        self.assertIn('Vui lòng chọn hợp đồng.', form)
        self.assertIn('Giá trị hợp đồng', form)
        self.assertIn('Tổng đã lập lịch', form)
        self.assertIn('Tiền cọc đã ghi nhận', form)
        self.assertIn('Còn phải lập lịch', form)
        self.assertIn('Còn có thể lập lịch', form)

    def test_frontend_vietnamese_labels_complete(self):
        constants=read('frontend/src/features/payments/constants.ts')
        for status in ('pending','partial','paid','overdue','cancelled'):
            self.assertIn(status, constants)
        for label in ('Chưa thanh toán','Thanh toán một phần','Đã thanh toán','Quá hạn','Đã hủy'):
            self.assertIn(label, constants)

if __name__=='__main__': unittest.main()
