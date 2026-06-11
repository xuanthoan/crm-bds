import ast
import importlib.util
import unittest
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from pydantic import ValidationError
from app.bookings.activity import decode_activity_context, is_status_transition, status_activity_content, status_label
from app.schemas.booking import BookingCreate, BookingStatusChange

IDS={"customer_id":"00000000-0000-0000-0000-000000000001","property_unit_id":"00000000-0000-0000-0000-000000000002","assigned_user_id":"00000000-0000-0000-0000-000000000003"}
class Sprint11BookingValidationTests(unittest.TestCase):
    def test_draft_create_allows_missing_money_and_rejects_non_positive_values(self):
        for values in ({}, {"booking_amount": None}, {"deposit_amount": None}):
            with self.subTest(values=values):
                booking = BookingCreate(**IDS, **values)
                self.assertIsNone(booking.booking_amount)
        for values, message in (
            ({"booking_amount": Decimal("0")}, "Tiền giữ chỗ phải lớn hơn 0"),
            ({"booking_amount": Decimal("-1")}, "Tiền giữ chỗ phải lớn hơn 0"),
            ({"deposit_amount": Decimal("0")}, "Tiền cọc phải lớn hơn 0"),
            ({"deposit_amount": Decimal("-1")}, "Tiền cọc phải lớn hơn 0"),
        ):
            with self.subTest(values=values):
                with self.assertRaises(ValidationError) as context:
                    BookingCreate(**IDS, **values)
                self.assertIn(message, str(context.exception))
        booking = BookingCreate(**IDS, booking_amount=Decimal("1000000"), deposit_amount=Decimal("5000000"))
        self.assertEqual(Decimal("1000000"), booking.booking_amount)
        self.assertEqual(Decimal("5000000"), booking.deposit_amount)

    def test_status_validation_only_checks_relevant_money_fields(self):
        invalid = [
            ({"status": "deposited"}, "Tiền cọc là bắt buộc khi đặt cọc"),
            ({"status": "deposited", "deposit_amount": 0}, "Tiền cọc phải lớn hơn 0"),
            ({"status": "cancelled"}, "Lý do hủy là bắt buộc"),
            ({"status": "refunded", "refund_reason": "x"}, "Số tiền hoàn là bắt buộc"),
            ({"status": "refunded", "refund_amount": 0, "refund_reason": "x"}, "Số tiền hoàn phải lớn hơn 0"),
        ]
        for payload, message in invalid:
            with self.subTest(payload=payload):
                with self.assertRaises(ValidationError) as context:
                    BookingStatusChange(**payload)
                self.assertIn(message, str(context.exception))

        cancelled = BookingStatusChange(status="cancelled", cancel_reason="Khách đổi ý", deposit_amount=0)
        expired = BookingStatusChange(status="expired", deposit_amount=0)
        refunded = BookingStatusChange(status="refunded", refund_amount=1, refund_reason="Hoàn tiền", deposit_amount=0)
        self.assertEqual("cancelled", cancelled.status)
        self.assertEqual("expired", expired.status)
        self.assertEqual("refunded", refunded.status)

    def test_valid_reserved_deposited_and_refunded_payloads(self):
        reserved = BookingStatusChange(status="reserved", booking_amount=Decimal("1000000"))
        deposited = BookingStatusChange(status="deposited", deposit_amount=Decimal("5000000"))
        refunded = BookingStatusChange(status="refunded", refund_amount=Decimal("1000000"), refund_reason="Khách đổi ý")
        self.assertEqual(Decimal("1000000"), reserved.booking_amount)
        self.assertEqual(Decimal("5000000"), deposited.deposit_amount)
        self.assertEqual(Decimal("1000000"), refunded.refund_amount)

    def test_service_enforces_transition_amounts_and_filters_stale_fields(self):
        source = Path("backend/app/services/booking_service.py").read_text()
        for text in (
            "Bất động sản đã có booking đang hoạt động",
            "Tiền giữ chỗ là bắt buộc khi giữ chỗ",
            "Tiền cọc là bắt buộc khi đặt cọc",
            "_validate_status_amounts(booking, payload)",
            "_status_update_data(payload)",
        ):
            self.assertIn(text, source)
        self.assertNotIn('detail="Tiền giữ chỗ là bắt buộc"', ast.get_source_segment(
            source,
            next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == "create_booking"),
        ))
        self.assertIn('"cancelled": common | {"cancel_reason"}', source)
        self.assertIn('"expired": common', source)
        self.assertIn('"refunded": common | {"refund_amount", "refund_reason"}', source)

    @unittest.skipUnless(importlib.util.find_spec("sqlalchemy"), "SQLAlchemy is not installed")
    def test_status_update_data_drops_irrelevant_stale_money(self):
        from app.services.booking_service import _status_update_data

        cancelled = _status_update_data(BookingStatusChange(
            status="cancelled", cancel_reason="Khách đổi ý", deposit_amount=0,
        ))
        expired = _status_update_data(BookingStatusChange(status="expired", deposit_amount=0))
        refunded = _status_update_data(BookingStatusChange(
            status="refunded", refund_amount=1, refund_reason="Hoàn tiền", deposit_amount=0,
        ))
        self.assertEqual({"cancel_reason": "Khách đổi ý"}, cancelled)
        self.assertEqual({}, expired)
        self.assertEqual({"refund_amount": Decimal("1"), "refund_reason": "Hoàn tiền"}, refunded)

    @unittest.skipUnless(importlib.util.find_spec("sqlalchemy"), "SQLAlchemy is not installed")
    def test_reserved_and_deposited_service_amount_rules(self):
        from fastapi import HTTPException
        from app.services.booking_service import _validate_status_amounts

        booking_without_money = SimpleNamespace(booking_amount=None)
        with self.assertRaisesRegex(HTTPException, "Tiền giữ chỗ là bắt buộc khi giữ chỗ"):
            _validate_status_amounts(booking_without_money, BookingStatusChange(status="reserved"))
        _validate_status_amounts(
            booking_without_money,
            BookingStatusChange(status="reserved", booking_amount=Decimal("1")),
        )
        _validate_status_amounts(
            booking_without_money,
            BookingStatusChange(status="deposited", deposit_amount=Decimal("1")),
        )

    def test_frontend_status_payload_is_status_specific(self):
        source = Path("frontend/src/features/bookings/statusPayload.ts").read_text()
        modal = Path("frontend/src/features/bookings/BookingStatusModal.tsx").read_text()
        self.assertIn("if (status === 'reserved')", source)
        self.assertIn("else if (status === 'deposited')", source)
        self.assertIn("else if (status === 'cancelled')", source)
        self.assertIn("else if (status === 'refunded')", source)
        self.assertNotIn("deposit_amount", source[source.index("else if (status === 'cancelled')"):source.index("else if (status === 'refunded')")])
        self.assertIn("setForm(nextStatus === 'reserved'", modal)
        self.assertIn("buildBookingStatusPayload(status, form)", modal)

    def test_booking_timeline_status_labels_are_vietnamese(self):
        expected = {
            "draft": "Mới tạo",
            "reserved": "Đã giữ chỗ",
            "deposited": "Đã cọc",
            "cancelled": "Đã hủy",
            "expired": "Hết hạn giữ chỗ",
            "refunded": "Đã hoàn tiền",
        }
        for code, label in expected.items():
            with self.subTest(code=code):
                self.assertEqual(label, status_label(code))
        for old_status, new_status in (
            ("draft", "reserved"),
            ("reserved", "deposited"),
            ("deposited", "cancelled"),
            ("deposited", "refunded"),
            ("reserved", "expired"),
        ):
            self.assertTrue(is_status_transition(old_status, new_status))
            self.assertNotEqual(old_status, status_label(old_status))
            self.assertNotEqual(new_status, status_label(new_status))

    def test_status_activity_content_preserves_notes_reasons_and_amounts(self):
        cases = [
            (SimpleNamespace(status="reserved", booking_amount=Decimal("1000000"), deposit_amount=None, refund_amount=None, cancel_reason=None, refund_reason=None, note="Khách đã chuyển tiền giữ chỗ"), {"booking_amount": "1000000", "note": "Khách đã chuyển tiền giữ chỗ"}),
            (SimpleNamespace(status="deposited", booking_amount=None, deposit_amount=Decimal("5000000"), refund_amount=None, cancel_reason=None, refund_reason=None, note="Đã nhận tiền cọc"), {"deposit_amount": "5000000", "note": "Đã nhận tiền cọc"}),
            (SimpleNamespace(status="cancelled", booking_amount=None, deposit_amount=None, refund_amount=None, cancel_reason="Khách đổi ý", refund_reason=None, note="Đã xác nhận hủy"), {"cancel_reason": "Khách đổi ý", "note": "Đã xác nhận hủy"}),
            (SimpleNamespace(status="refunded", booking_amount=None, deposit_amount=None, refund_amount=Decimal("50000000"), cancel_reason=None, refund_reason="Khách đổi ý", note="Đã hoàn tiền qua chuyển khoản"), {"refund_amount": "50000000", "refund_reason": "Khách đổi ý", "note": "Đã hoàn tiền qua chuyển khoản"}),
        ]
        for payload, expected in cases:
            with self.subTest(status=payload.status):
                self.assertEqual(expected, decode_activity_context(status_activity_content(payload)))

    def test_booking_timeline_renderer_separates_transition_actor_and_context(self):
        source = Path("frontend/src/features/bookings/components/BookingTimeline.tsx").read_text()
        self.assertIn("{activity.old_value || '—'} → {activity.new_value || '—'}", source)
        self.assertIn("Người thực hiện: {activity.actor.full_name}", source)
        for label in ("Ghi chú", "Lý do hủy", "Lý do hoàn tiền", "Số tiền hoàn", "Tiền giữ chỗ", "Tiền cọc"):
            self.assertIn(label, source)
        for raw_status in (">draft<", ">reserved<", ">deposited<", ">cancelled<", ">expired<", ">refunded<"):
            self.assertNotIn(raw_status, source)

    def test_status_change_activity_uses_standard_title_and_structured_content(self):
        source = Path("backend/app/services/booking_service.py").read_text()
        self.assertIn('title="Đổi trạng thái booking"', source)
        self.assertIn('activity_content = status_activity_content(payload)', source)
        self.assertIn('content=activity_content', source)
        self.assertIn('"old_value": status_label(item.old_value)', source)
        self.assertIn('"new_value": status_label(item.new_value)', source)
        self.assertIn('"context": context', source)
        self.assertIn('after_data={"status": booking.status, **activity_context}', source)

    def test_delete_only_allows_final_statuses(self):
        source = Path("backend/app/services/booking_service.py").read_text()
        self.assertIn('DELETE_ALLOWED_STATUSES = {"cancelled", "expired", "refunded"}', source)
        self.assertIn("status_code=409", source)
        self.assertIn("Không thể xóa booking đang hoạt động. Vui lòng hủy booking trước.", source)

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
