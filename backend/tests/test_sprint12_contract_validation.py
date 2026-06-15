import unittest
import importlib.util
from decimal import Decimal
from types import SimpleNamespace
from pathlib import Path
from fastapi import HTTPException
from pydantic import ValidationError
from app.schemas.contract import ContractCreate,ContractPaymentConfirm,ContractPaymentCreate,ContractPaymentUpdate
from uuid import uuid4
HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None
class Sprint12ValidationTest(unittest.TestCase):
 def test_contract_value_positive(self):
  with self.assertRaises(ValidationError):ContractCreate(deal_id=uuid4(),contract_value=0)
 def test_payment_positive(self):
  with self.assertRaises(ValidationError):ContractPaymentCreate(contract_id=uuid4(),amount=0)
  with self.assertRaises(ValidationError):ContractPaymentCreate(contract_id=uuid4(),amount=-1)
  with self.assertRaises(ValidationError):ContractPaymentUpdate(amount=0)
  with self.assertRaises(ValidationError):ContractPaymentUpdate(amount=-1)
 def test_payment_method_vocabulary(self):
  self.assertEqual(ContractPaymentConfirm(payment_method="bank_transfer").payment_method,"bank_transfer")
  with self.assertRaises(ValidationError):ContractPaymentConfirm(payment_method="free text")
 @unittest.skipUnless(HAS_SQLALCHEMY, "SQLAlchemy is not installed")
 def test_contract_totals_deduct_booking_deposit_and_paid_payments(self):
  from app.services.contract_service import totals
  contract=SimpleNamespace(
   contract_value=Decimal("1000"),deposit_value=Decimal("200"),
   payments=[
    SimpleNamespace(amount=Decimal("300"),status="paid",deleted_at=None),
    SimpleNamespace(amount=Decimal("100"),status="planned",deleted_at=None),
    SimpleNamespace(amount=Decimal("50"),status="paid",deleted_at=object()),
   ],
  )
  paid,planned,remaining=totals(contract)
  self.assertEqual(paid,Decimal("300"))
  self.assertEqual(planned,Decimal("100"))
  self.assertEqual(remaining,Decimal("500"))
 @unittest.skipUnless(HAS_SQLALCHEMY, "SQLAlchemy is not installed")
 def test_contract_remaining_never_negative(self):
  from app.services.contract_service import totals
  contract=SimpleNamespace(
   contract_value=Decimal("1000"),deposit_value=Decimal("800"),
   payments=[SimpleNamespace(amount=Decimal("300"),status="paid",deleted_at=None)],
  )
  self.assertEqual(totals(contract)[2],Decimal("0"))
 @unittest.skipUnless(HAS_SQLALCHEMY, "SQLAlchemy is not installed")
 def test_payment_capacity_blocks_planned_or_paid_overpayment(self):
  from app.services.contract_service import _validate_payment_capacity
  contract=SimpleNamespace(id=uuid4(),contract_value=Decimal("1000"),deposit_value=Decimal("200"))
  db=SimpleNamespace(scalar=lambda _query:Decimal("700"))
  with self.assertRaisesRegex(HTTPException,"Số tiền thanh toán vượt quá số tiền còn phải thu của hợp đồng"):
   _validate_payment_capacity(db,contract,Decimal("101"))
  _validate_payment_capacity(db,contract,Decimal("100"))
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
 @unittest.skipUnless(HAS_SQLALCHEMY, "SQLAlchemy is not installed")
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
 def test_cancelled_contract_rolls_back_deal_property_and_histories(self):
  service=Path("backend/app/services/contract_service.py").read_text()
  self.assertIn("def _rollback_cancelled_contract",service)
  self.assertIn('deal.pipeline_stage = "contract"',service)
  self.assertIn('deal.status = "contract_pending"',service)
  self.assertIn('Booking.status == "deposited"',service)
  self.assertIn('target_property_status = "deposited" if active_deposit_booking else "available"',service)
  self.assertIn('title="Khôi phục giao dịch do hủy hợp đồng"',service)
  self.assertIn("PropertyStatusHistory(",service)
  self.assertIn('"rollback_property_status"',service)
  self.assertIn('if payload.status == "cancelled"',service)
 @unittest.skipUnless(HAS_SQLALCHEMY, "SQLAlchemy is not installed")
 def test_cancelled_signed_contract_with_deposit_booking_restores_deposited(self):
  from app.models.deal_activity import DealActivity
  from app.models.property_status_history import PropertyStatusHistory
  from app.services.contract_service import _rollback_cancelled_contract
  actor=SimpleNamespace(id=uuid4())
  deal=SimpleNamespace(id=uuid4(),deal_code="DL-000007",pipeline_stage="contract_signed",status="contracted",closed_at=None)
  prop=SimpleNamespace(id=uuid4(),inventory_status="sold",updated_by_id=None)
  contract=SimpleNamespace(id=uuid4(),property_unit_id=prop.id,deal=deal,property_unit=prop,contract_code="HD-000001")
  class FakeDb:
   def __init__(self):self.results=iter([None,uuid4()]);self.added=[]
   def scalar(self,_query):return next(self.results)
   def add(self,item):self.added.append(item)
  db=FakeDb()
  activity=_rollback_cancelled_contract(db,contract,actor,"signed","Khách hủy")
  self.assertEqual(deal.pipeline_stage,"contract")
  self.assertEqual(deal.status,"contract_pending")
  self.assertEqual(prop.inventory_status,"deposited")
  self.assertIsInstance(activity,DealActivity)
  self.assertTrue(any(isinstance(item,PropertyStatusHistory) and item.new_status=="deposited" for item in db.added))
 @unittest.skipUnless(HAS_SQLALCHEMY, "SQLAlchemy is not installed")
 def test_cancelled_signed_contract_without_deposit_booking_restores_available(self):
  from app.models.property_status_history import PropertyStatusHistory
  from app.services.contract_service import _rollback_cancelled_contract
  actor=SimpleNamespace(id=uuid4())
  deal=SimpleNamespace(id=uuid4(),deal_code="DL-000008",pipeline_stage="contract_signed",status="contracted",closed_at=None)
  prop=SimpleNamespace(id=uuid4(),inventory_status="sold",updated_by_id=None)
  contract=SimpleNamespace(id=uuid4(),property_unit_id=prop.id,deal=deal,property_unit=prop,contract_code="HD-000002")
  class FakeDb:
   def __init__(self):self.results=iter([None,None]);self.added=[]
   def scalar(self,_query):return next(self.results)
   def add(self,item):self.added.append(item)
  db=FakeDb()
  _rollback_cancelled_contract(db,contract,actor,"signed")
  self.assertEqual(deal.pipeline_stage,"contract")
  self.assertEqual(deal.status,"contract_pending")
  self.assertEqual(prop.inventory_status,"available")
  self.assertTrue(any(isinstance(item,PropertyStatusHistory) and item.new_status=="available" for item in db.added))
 def test_payment_activity_uses_structured_metadata_and_vnd_rows(self):
  service=Path("backend/app/services/contract_service.py").read_text()
  timeline=Path("frontend/src/features/contracts/components/ContractTimeline.tsx").read_text()
  self.assertIn('"payment_type_label":PAYMENT_TYPE_LABELS[p.payment_type]',service)
  self.assertIn('"payment_method":p.payment_method',service)
  self.assertIn('"reference_number":p.reference_number',service)
  self.assertIn('"paid_date":p.paid_date.isoformat()',service)
  self.assertIn('"payment_method_label":PAYMENT_METHOD_LABELS.get(p.payment_method)',service)
  self.assertIn("Intl.NumberFormat('vi-VN'",timeline)
  self.assertIn("maximumFractionDigits: 0",timeline)
  for label in ("Số tiền", "Loại thanh toán", "Trạng thái", "Phương thức", "Mã tham chiếu", "Ngày thanh toán"):
   self.assertIn(label,timeline)
  self.assertIn('contract-timeline-details',timeline)
 def test_contract_inherits_booking_deposit_and_payment_ui_is_structured(self):
  service=Path("backend/app/services/contract_service.py").read_text()
  modal=Path("frontend/src/features/contracts/ContractPaymentModal.tsx").read_text()
  table=Path("frontend/src/features/contracts/components/ContractPaymentTable.tsx").read_text()
  summary=Path("frontend/src/features/contracts/components/ContractSummaryCard.tsx").read_text()
  styles=Path("frontend/src/styles.css").read_text()
  self.assertIn("deal.booking.deposit_amount",service)
  self.assertIn('"inherited_deposit_amount"',service)
  self.assertIn('"deposit_amount":item.deposit_value or Decimal("0")',service)
  self.assertIn("contract.contract_value - deposit - paid",service)
  self.assertIn("Số tiền thanh toán vượt quá số tiền còn phải thu của hợp đồng.",service)
  self.assertIn("<select required value={method}",modal)
  self.assertNotIn('placeholder="Phương thức thanh toán"',modal)
  for label in ("Mã tham chiếu / mã giao dịch","Ngày thanh toán","Hạn thanh toán","Ghi chú"):
   self.assertIn(label,modal)
  self.assertIn("payment_method_label",table)
  self.assertIn("payment.paid_date",table)
  self.assertIn("c.deposit_amount",summary)
  self.assertIn("Số tiền thanh toán phải lớn hơn 0.",modal)
  self.assertIn("Ngày thanh toán là bắt buộc.",modal)
  self.assertIn(".contract-payment-form {",styles)
  self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr))",styles)
  self.assertIn(".contract-payment-form textarea",styles)
 def test_contract_parties_use_labeled_fields_not_noisy_separators(self):
  detail=Path("frontend/src/features/contracts/ContractDetailPage.tsx").read_text()
  for label in ("Tên", "SĐT", "Email", "CCCD/CMND", "Địa chỉ", "Đại diện"):
   self.assertIn(f"<dt>{label}</dt>",detail)
  self.assertNotIn(" · ",detail)
 @unittest.skipUnless(HAS_SQLALCHEMY, "SQLAlchemy is not installed")
 def test_deal_property_link_derives_inventory_fields(self):
  from app.services.deal_service import _property_link_data
  project_id=uuid4()
  project=SimpleNamespace(id=project_id,name="Hồng Hạc City",status="paused")
  property_unit=SimpleNamespace(
   id=uuid4(),deleted_at=None,inventory_status="available",project_id=project_id,project=project,
   property_code="PROP-000015",property_type="apartment",area_net=Decimal("68.5"),
   area_gross=Decimal("72"),listed_price=Decimal("1000"),
  )
  db=SimpleNamespace(scalar=lambda _query:property_unit)
  result=_property_link_data(db,property_unit.id,project_id,reject_sold=True)
  self.assertEqual(result["property_unit_id"],property_unit.id)
  self.assertEqual(result["property_code"],"PROP-000015")
  self.assertEqual(result["property_type"],"apartment")
  self.assertEqual(result["project_id"],project_id)
  self.assertEqual(result["project_name"],"Hồng Hạc City")
  self.assertEqual(result["area"],"68.5")
  self.assertEqual(result["_listed_price"],Decimal("1000"))
 @unittest.skipUnless(HAS_SQLALCHEMY, "SQLAlchemy is not installed")
 def test_deal_property_link_rejects_conflicting_deleted_and_sold_inventory(self):
  from app.services.deal_service import _property_link_data
  project_id=uuid4()
  base=dict(id=uuid4(),deleted_at=None,inventory_status="available",project_id=project_id,
   project=SimpleNamespace(id=project_id,name="Hồng Hạc City"),property_code="PROP-000015",
   property_type="apartment",area_net=None,area_gross=None,listed_price=None)
  with self.assertRaisesRegex(HTTPException,"Dự án không khớp với bất động sản đã chọn"):
   _property_link_data(SimpleNamespace(scalar=lambda _query:SimpleNamespace(**base)),base["id"],uuid4(),reject_sold=True)
  deleted={**base,"deleted_at":object()}
  with self.assertRaisesRegex(HTTPException,"Bất động sản đã bị xóa"):
   _property_link_data(SimpleNamespace(scalar=lambda _query:SimpleNamespace(**deleted)),base["id"],project_id,reject_sold=True)
  sold={**base,"inventory_status":"sold"}
  with self.assertRaisesRegex(HTTPException,"Bất động sản đã bán không thể tạo giao dịch mới"):
   _property_link_data(SimpleNamespace(scalar=lambda _query:SimpleNamespace(**sold)),base["id"],project_id,reject_sold=True)
 def test_deal_form_uses_inventory_dropdowns_and_preserves_legacy_warning(self):
  form=Path("frontend/src/features/deals/DealFormModal.tsx").read_text()
  combobox=Path("frontend/src/features/deals/components/SearchableCombobox.tsx").read_text()
  detail=Path("frontend/src/features/deals/DealDetailPage.tsx").read_text()
  for source in ("listProjects({page_size: 100})","listProperties({page_size: 100})",'ariaLabel="Dự án"','ariaLabel="Bất động sản"'):
   self.assertIn(source,form)
  self.assertNotIn("ACTIVE_PROJECT_STATUSES",form)
  self.assertNotIn("<label>Dự án<select",form)
  self.assertNotIn("<label>Bất động sản<select",form)
  self.assertNotIn("value={form.project_name}",form)
  self.assertNotIn("value={form.property_code}",form)
  self.assertIn("Không thuộc dự án",form)
  self.assertIn("Không chọn / Tất cả dự án",form)
  self.assertIn("Không tìm thấy dự án phù hợp",form)
  self.assertIn("Không tìm thấy bất động sản phù hợp",form)
  self.assertIn("PROJECT_STATUS_LABELS[project.status]",form)
  self.assertIn("property.inventory_status === 'sold' && !isCurrent",form)
  for search_field in ("property.property_code","property.project?.name","property.block","property.tower","property.floor","property.unit_number"):
   self.assertIn(search_field,form)
  self.assertIn(".normalize('NFD')",combobox)
  self.assertIn("role=\"combobox\"",combobox)
  self.assertIn("event.key === 'ArrowDown'",combobox)
  self.assertIn("event.key === 'Escape'",combobox)
  self.assertIn("Mã BĐS cũ",form)
  self.assertIn("BĐS này hiện đã bán nhưng đang được liên kết với giao dịch này.",form)
  self.assertIn("deal-property-preview",form)
  self.assertIn("property_unit_id: preserveUnmatchedLegacyProperty ? undefined : form.property_unit_id || null",form)
  self.assertIn("project_id: preserveUnmatchedLegacyProperty ? undefined : form.project_id && form.project_id !== NO_PROJECT",form)
  self.assertIn("navigateTo(`/properties/${deal.property!.id}`)",detail)
  self.assertIn("navigateTo(`/projects/${deal.project!.id}`)",detail)
 def test_property_list_exposes_location_fields_for_deal_combobox_search(self):
  service=Path("backend/app/services/property_service.py").read_text()
  for field in ('"block":item.block','"tower":item.tower','"floor":item.floor','"unit_number":item.unit_number','"area_gross":item.area_gross'):
   self.assertIn(field,service)
 def test_migration(self):
  s=Path("backend/alembic/versions/20260613_0010_deal_closing_contracts.py").read_text();self.assertIn('revision="20260613_0010"',s);self.assertIn('down_revision="20260612_0009"',s)
  for table in ("contracts","contract_payments","contract_activities"):self.assertIn(f'op.create_table("{table}"',s)
if __name__=="__main__":unittest.main()
