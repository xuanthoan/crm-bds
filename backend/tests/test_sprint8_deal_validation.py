import ast
import unittest
from pathlib import Path
from pydantic import ValidationError
from app.schemas.deal import DealCreate, DealStageUpdate, DealStatusUpdate

IDS={'customer_id':'11111111-1111-1111-1111-111111111111','owner_id':'22222222-2222-2222-2222-222222222222'}
class Sprint8DealValidationTests(unittest.TestCase):
    def make(self,**kwargs): return DealCreate(**IDS,title='Căn hộ A',**kwargs)
    def test_defaults_and_blank_normalization(self):
        deal=self.make(description='',expected_value=''); self.assertEqual('new',deal.pipeline_stage); self.assertEqual('open',deal.status); self.assertIsNone(deal.description); self.assertIsNone(deal.expected_value)
    def test_non_negative_money(self):
        for value in ('abc','-1','NaN'):
            with self.subTest(value=value),self.assertRaisesRegex(ValidationError,'Giá trị tiền không hợp lệ'): self.make(expected_value=value)
    def test_contract_not_less_than_deposit(self):
        with self.assertRaisesRegex(ValidationError,'Giá trị hợp đồng phải lớn hơn hoặc bằng tiền đặt cọc'): self.make(deposit_amount=100,contract_value=99)
    def test_enums(self):
        with self.assertRaisesRegex(ValidationError,'Giai đoạn giao dịch không hợp lệ'): self.make(pipeline_stage='bad')
        with self.assertRaisesRegex(ValidationError,'Trạng thái giao dịch không hợp lệ'): self.make(status='bad')
        with self.assertRaisesRegex(ValidationError,'Ưu tiên không hợp lệ'): self.make(priority='bad')
    def test_soft_delete_writes_customer_timeline_and_keeps_active_filter(self):
        service_path = Path("backend/app/services/deal_service.py")
        source = service_path.read_text()
        tree = ast.parse(source)
        delete_function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "soft_delete_deal"
        )
        delete_source = ast.get_source_segment(source, delete_function) or ""

        self.assertIn("Deal.deleted_at.is_(None)", source)
        self.assertIn("deal.deleted_at = deleted_at", delete_source)
        self.assertIn("CustomerActivity(", delete_source)
        self.assertIn('title="Xóa giao dịch"', delete_source)
        self.assertIn("Mã giao dịch: {deal.deal_code}", delete_source)
        self.assertIn("Tên giao dịch: {deal.title}", delete_source)
        self.assertIn("Giá trị dự kiến: {expected_value}", delete_source)
        self.assertIn("Người xóa: {actor.full_name}", delete_source)
        self.assertIn("Thời gian xóa:", delete_source)
        self.assertNotIn("str(deal.id)", delete_source.split("write_audit_log", 1)[0])


    def test_active_deal_conflict_ignores_cancelled_contracts(self):
        from app.services.deal_service import _active_deal_conflict_exists

        class FakeScalars(list):
            def unique(self):
                return self

        class FakeDb:
            def __init__(self, deals, scalar_results):
                self.deals = FakeScalars(deals)
                self.scalar_results = list(scalar_results)
            def scalars(self, statement):
                return self.deals
            def scalar(self, statement):
                return self.scalar_results.pop(0) if self.scalar_results else None

        deal = type("DealRow", (), {"id": "deal-1"})()
        self.assertFalse(_active_deal_conflict_exists(FakeDb([deal], ["contract-1", None]), property_unit_id="property-1"))
        self.assertTrue(_active_deal_conflict_exists(FakeDb([deal], [None, None]), property_unit_id="property-1"))
        self.assertTrue(_active_deal_conflict_exists(FakeDb([deal], ["contract-1", "contract-1"]), property_unit_id="property-1"))

    def test_create_deal_uses_active_deal_conflict_guard(self):
        source = Path("backend/app/services/deal_service.py").read_text()
        self.assertIn("def _active_deal_conflict_exists", source)
        self.assertIn('Contract.status != "cancelled"', source)
        self.assertIn("has_contract and not has_non_cancelled_contract", source)
        self.assertIn('_active_deal_conflict_exists(db, property_unit_id=data["property_unit_id"])', source)
        booking_service = Path("backend/app/services/booking_service.py").read_text()
        self.assertIn("_active_deal_conflict_exists(db, booking_id=booking.id)", booking_service)
        self.assertIn("_active_deal_conflict_exists(db, property_unit_id=prop.id)", booking_service)

    def test_lost_requires_reason(self):
        with self.assertRaisesRegex(ValidationError,'Vui lòng nhập lý do thất bại/hủy giao dịch'): DealStatusUpdate(status='lost')
        with self.assertRaisesRegex(ValidationError,'Vui lòng nhập lý do thất bại/hủy giao dịch'): DealStageUpdate(pipeline_stage='lost')
if __name__=='__main__': unittest.main()
