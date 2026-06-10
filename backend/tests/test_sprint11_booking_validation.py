import ast
import importlib.util
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
    def test_property_lock_query_targets_only_the_base_table(self):
        source = Path("backend/app/services/booking_service.py").read_text()
        tree = ast.parse(source)
        functions = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
        }
        lock_source = ast.get_source_segment(source, functions["_lock_property_row"])
        self.assertIn("select(PropertyUnit.id)", lock_source)
        self.assertIn("with_for_update(of=PropertyUnit)", lock_source)
        self.assertNotIn("select(PropertyUnit)", lock_source)
        self.assertNotIn("joinedload", lock_source)
        self.assertNotIn("selectinload", lock_source)
        self.assertNotIn("outerjoin", lock_source)
        self.assertNotIn("join(", lock_source)

    @unittest.skipUnless(importlib.util.find_spec("sqlalchemy"), "SQLAlchemy is not installed")
    def test_property_lock_sql_has_no_outer_join(self):
        from sqlalchemy import select
        from sqlalchemy.dialects import postgresql
        from app.models.property_unit import PropertyUnit

        statement = (
            select(PropertyUnit.id)
            .where(PropertyUnit.id == IDS["property_unit_id"], PropertyUnit.deleted_at.is_(None))
            .with_for_update(of=PropertyUnit)
        )
        sql = str(statement.compile(dialect=postgresql.dialect())).upper()
        self.assertIn("FROM PROPERTY_UNITS", sql)
        self.assertIn("FOR UPDATE OF PROPERTY_UNITS", sql)
        self.assertNotIn(" JOIN ", sql)
        self.assertNotIn("PROJECTS", sql)
        self.assertNotIn("USERS", sql)

    def test_create_booking_locks_then_reloads_property_without_for_update(self):
        source = Path("backend/app/services/booking_service.py").read_text()
        tree = ast.parse(source)
        functions = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
        }
        create_source = ast.get_source_segment(source, functions["create_booking"])
        validate_source = ast.get_source_segment(source, functions["_validate_property"])
        self.assertLess(
            create_source.index("_lock_property_row(db, payload.property_unit_id)"),
            create_source.index("prop = _validate_property(db, payload.property_unit_id)"),
        )
        self.assertIn("Booking(**data", create_source)
        self.assertIn("db.commit()", create_source)
        self.assertNotIn("with_for_update", validate_source)
        self.assertIn("populate_existing=True", validate_source)

    def test_status_changes_lock_and_reload_property_before_inventory_update(self):
        source = Path("backend/app/services/booking_service.py").read_text()
        tree = ast.parse(source)
        function = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "change_booking_status"
        )
        status_source = ast.get_source_segment(source, function)
        self.assertLess(
            status_source.index("_lock_property_row(db, booking.property_unit_id)"),
            status_source.index("_change_property_status"),
        )
        self.assertIn(
            "booking.property_unit = _validate_property(db, booking.property_unit_id)",
            status_source,
        )
        self.assertIn('"reserved"', status_source)
        self.assertIn('"deposited"', status_source)

    def test_migration_enforces_single_active_property_booking(self):
        migration=Path("backend/alembic/versions/20260612_0009_booking_reservation.py").read_text()
        self.assertIn("uq_bookings_active_property",migration); self.assertIn("deleted_at IS NULL AND status IN",migration)
if __name__=="__main__": unittest.main()
