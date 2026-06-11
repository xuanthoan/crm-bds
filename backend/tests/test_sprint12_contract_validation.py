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
 def test_deal_contract_modal_prefills_and_locks_deal_context(self):
  deal_detail=Path("frontend/src/features/deals/DealDetailPage.tsx").read_text()
  modal=Path("frontend/src/features/contracts/ContractFormModal.tsx").read_text()
  contracts_page=Path("frontend/src/features/contracts/ContractsPage.tsx").read_text()
  self.assertIn("setModal('contract')",deal_detail)
  self.assertIn("initialDeal={deal} lockDeal",deal_detail)
  self.assertIn("const dealIsLocked = isEditing || lockDeal",modal)
  self.assertIn("disabled={dealIsLocked || loadingDeals}",modal)
  self.assertIn("initialDeal?.id ?? contract?.deal_id ?? ''",modal)
  for label in ("Giao dịch", "Khách hàng", "Bất động sản", "Dự án"):
   self.assertIn(label,modal)
  self.assertIn("<ContractFormModal",contracts_page)
  self.assertNotIn("lockDeal",contracts_page)
 def test_contract_form_has_responsive_two_column_layout(self):
  styles=Path("frontend/src/styles.css").read_text()
  self.assertIn(".contract-form-grid {",styles)
  self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr))",styles)
  self.assertIn("@media (max-width: 640px)",styles)
  self.assertIn("grid-template-columns: 1fr",styles)
 def test_migration(self):
  s=Path("backend/alembic/versions/20260613_0010_deal_closing_contracts.py").read_text();self.assertIn('revision="20260613_0010"',s);self.assertIn('down_revision="20260612_0009"',s)
  for table in ("contracts","contract_payments","contract_activities"):self.assertIn(f'op.create_table("{table}"',s)
if __name__=="__main__":unittest.main()
