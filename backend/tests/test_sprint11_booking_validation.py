import unittest
from decimal import Decimal
from pathlib import Path
from pydantic import ValidationError
from app.schemas.booking import BookingCreate, BookingStatusChange

IDS={"customer_id":"00000000-0000-0000-0000-000000000001","property_unit_id":"00000000-0000-0000-0000-000000000002","assigned_user_id":"00000000-0000-0000-0000-000000000003"}
class Sprint11BookingValidationTests(unittest.TestCase):
    def test_amount_validation(self):
        with self.assertRaises(ValidationError) as context: BookingCreate(**IDS,booking_amount=Decimal("-1"))
        self.assertIn("Số tiền không hợp lệ",str(context.exception))
    def test_deposit_cancel_and_refund_requirements(self):
        cases=[({"status":"deposited"},"Số tiền cọc là bắt buộc"),({"status":"cancelled"},"Lý do hủy là bắt buộc"),({"status":"refunded","refund_reason":"x"},"Số tiền hoàn là bắt buộc"),({"status":"refunded","refund_amount":0},"Lý do hoàn tiền là bắt buộc")]
        for payload,message in cases:
            with self.subTest(payload=payload):
                with self.assertRaises(ValidationError) as context: BookingStatusChange(**payload)
                self.assertIn(message,str(context.exception))
    def test_valid_status_payloads(self):
        self.assertEqual("deposited",BookingStatusChange(status="deposited",deposit_amount=0).status)
        self.assertEqual("refunded",BookingStatusChange(status="refunded",refund_amount=0,refund_reason="Khách đổi ý").status)
    def test_service_contains_inventory_duplicate_and_delete_guards(self):
        source=Path("backend/app/services/booking_service.py").read_text()
        for text in ("Khách hàng không tồn tại","Bất động sản không tồn tại","Bất động sản hiện không khả dụng để giữ chỗ","Bất động sản đã có booking đang hoạt động","_change_property_status","Không thể xóa booking đang giữ chỗ hoặc đã cọc"):
            self.assertIn(text,source)
        self.assertIn('DELETE_ALLOWED_STATUSES = {"draft", "cancelled", "expired", "refunded"}',source)
    def test_migration_enforces_single_active_property_booking(self):
        migration=Path("backend/alembic/versions/20260612_0009_booking_reservation.py").read_text()
        self.assertIn("uq_bookings_active_property",migration); self.assertIn("deleted_at IS NULL AND status IN",migration)
if __name__=="__main__": unittest.main()
