import unittest
from types import SimpleNamespace
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
 def test_contract_status_helpers_update_deal_and_create_localized_activity(self):
  from app.services.contract_service import _apply_status, _deal_contract_activity
  actor=SimpleNamespace(id=uuid4())
  deal=SimpleNamespace(id=uuid4(),status="contract_pending",pipeline_stage="contract",contract_date=None,closed_at=None,deal_code="DL-000007")
  prop=SimpleNamespace(id=uuid4(),inventory_status="deposited",updated_by_id=None)
  contract=SimpleNamespace(id=uuid4(),deal_id=deal.id,deal=deal,property_unit=prop,contract_code="HD-000001",signed_date=None)
  class FakeDb:
   def __init__(self):self.added=[]
   def add(self,item):self.added.append(item)
  db=FakeDb()
  _apply_status(db,contract,actor,"signed")
  self.assertEqual(deal.pipeline_stage,"contract_signed")
  self.assertEqual(deal.status,"contracted")
  self.assertEqual(prop.inventory_status,"sold")
  activity=_deal_contract_activity(db,contract,actor,"draft","signed","test đã kí")
  self.assertEqual(activity.title,"Hợp đồng đã ký")
  self.assertEqual(activity.old_value,"Bản nháp")
  self.assertEqual(activity.new_value,"Đã ký")
  self.assertIn("Hợp đồng HD-000001 đã chuyển sang trạng thái Đã ký.",activity.content)
  self.assertIn("Ghi chú: test đã kí",activity.content)
 def test_contract_status_syncs_deal_stage_and_vietnamese_timeline(self):
  service=Path("backend/app/services/contract_service.py").read_text()
  backend_constants=Path("backend/app/deals/constants.py").read_text()
  frontend_constants=Path("frontend/src/features/deals/constants.ts").read_text()
  self.assertIn('contract.deal.pipeline_stage = "contract_signed"',service)
  self.assertIn('"contract_signed": "Đã ký hợp đồng"',backend_constants)
  self.assertIn("contract_signed:'Đã ký hợp đồng'",frontend_constants)
  for title in ("Hợp đồng đã ký", "Hợp đồng có hiệu lực", "Hợp đồng hoàn tất", "Hợp đồng đã hủy"):
   self.assertIn(title,service)
  self.assertIn('activity_type="contract_status"',service)
  self.assertIn('old_value=old_label',service)
  self.assertIn('new_value=new_label',service)
  self.assertIn('Ghi chú: {note.strip()}',service)
 def test_payment_activity_uses_structured_metadata_and_vnd_rows(self):
  service=Path("backend/app/services/contract_service.py").read_text()
  timeline=Path("frontend/src/features/contracts/components/ContractTimeline.tsx").read_text()
  self.assertIn('"payment_type_label":PAYMENT_TYPE_LABELS[p.payment_type]',service)
  self.assertIn('"payment_method":p.payment_method',service)
  self.assertIn('"reference_number":p.reference_number',service)
  self.assertIn("Intl.NumberFormat('vi-VN'",timeline)
  self.assertIn("maximumFractionDigits: 0",timeline)
  for label in ("Số tiền", "Loại thanh toán", "Trạng thái", "Phương thức", "Mã tham chiếu"):
   self.assertIn(label,timeline)
  self.assertIn('contract-timeline-details',timeline)
 def test_contract_parties_use_labeled_fields_not_noisy_separators(self):
  detail=Path("frontend/src/features/contracts/ContractDetailPage.tsx").read_text()
  for label in ("Tên", "SĐT", "Email", "CCCD/CMND", "Địa chỉ", "Đại diện"):
   self.assertIn(f"<dt>{label}</dt>",detail)
  self.assertNotIn(" · ",detail)
 def test_migration(self):
  s=Path("backend/alembic/versions/20260613_0010_deal_closing_contracts.py").read_text();self.assertIn('revision="20260613_0010"',s);self.assertIn('down_revision="20260612_0009"',s)
  for table in ("contracts","contract_payments","contract_activities"):self.assertIn(f'op.create_table("{table}"',s)
if __name__=="__main__":unittest.main()
