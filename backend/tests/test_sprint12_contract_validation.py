import unittest
from pathlib import Path
from pydantic import ValidationError
from app.schemas.contract import ContractCreate,ContractPaymentCreate
from uuid import uuid4
class Sprint12ValidationTest(unittest.TestCase):
 def test_contract_value_positive(self):
  with self.assertRaises(ValidationError):ContractCreate(deal_id=uuid4(),contract_value=0)
 def test_payment_positive(self):
  with self.assertRaises(ValidationError):ContractPaymentCreate(contract_id=uuid4(),amount=0)
 def test_booking_conversion_guards(self):
  s=Path("backend/app/services/booking_service.py").read_text();self.assertIn("Chỉ booking đã cọc mới được chuyển thành giao dịch.",s);self.assertIn("Booking này đã có giao dịch đang hoạt động.",s);self.assertIn("Bất động sản này đã có giao dịch đang hoạt động.",s);self.assertIn('status="contract_pending"',s)
 def test_contract_guards_and_integrations(self):
  s=Path("backend/app/services/contract_service.py").read_text();self.assertIn("Giao dịch này đã có hợp đồng đang hoạt động",s);self.assertIn('p.status="paid"',s);self.assertIn('prop.inventory_status="sold"',s);self.assertIn("Không thể xóa hợp đồng đã ký hoặc hoàn tất.",s);self.assertIn('{"draft","cancelled"}',s)
 def test_migration(self):
  s=Path("backend/alembic/versions/20260613_0010_deal_closing_contracts.py").read_text();self.assertIn('revision="20260613_0010"',s);self.assertIn('down_revision="20260612_0009"',s)
  for table in ("contracts","contract_payments","contract_activities"):self.assertIn(f'op.create_table("{table}"',s)
if __name__=="__main__":unittest.main()
