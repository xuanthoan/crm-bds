from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.lead import Lead
from app.models.user import User
from app.services.phone_service import normalize_phone


@dataclass
class DuplicateLeadResult:
    is_duplicate: bool
    matched_customer_id: UUID | None = None
    matched_lead_ids: list[UUID] | None = None
    matched_phone: str | None = None
    match_reason: str | None = None
    can_view_common_profile: bool = True
    can_view_other_journeys: bool = False
    safe_summary: str | None = None

    def to_dict(self) -> dict:
        return {
            "is_duplicate": self.is_duplicate,
            "customer_id": self.matched_customer_id,
            "matched_customer_id": self.matched_customer_id,
            "matched_lead_ids": self.matched_lead_ids or [],
            "matched_phone": self.matched_phone,
            "match_reason": self.match_reason,
            "action": "existing_customer_reengaged" if self.is_duplicate else None,
            "can_view_common_profile": self.can_view_common_profile,
            "can_view_other_journeys": self.can_view_other_journeys,
            "safe_summary": self.safe_summary,
            "message": "Lead/khách hàng này đã có trong hệ thống. Bạn có thể mở hồ sơ hiện có để tiếp tục chăm sóc." if self.is_duplicate else None,
        }


def _phone_pairs(primary: str | None, secondary: str | None) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    if primary:
        items.append(("phone_primary", primary))
    if secondary:
        items.append(("phone_secondary", secondary))
    return items


def detect_duplicate_customer(db: Session, phone_primary: str | None, phone_secondary: str | None, *, exclude_customer_id: UUID | None = None, exclude_lead_id: UUID | None = None, current_user: User | None = None) -> DuplicateLeadResult:
    new_primary = normalize_phone(phone_primary)
    new_secondary = normalize_phone(phone_secondary)
    incoming = _phone_pairs(new_primary, new_secondary)
    if not incoming:
        return DuplicateLeadResult(is_duplicate=False, matched_lead_ids=[])
    phones = {value for _, value in incoming if value}
    customer_query = select(Customer).where(
        Customer.deleted_at.is_(None),
        or_(Customer.phone_primary_normalized.in_(phones), Customer.phone_secondary_normalized.in_(phones), Customer.primary_phone.in_(phones), Customer.secondary_phone.in_(phones)),
    )
    if exclude_customer_id:
        customer_query = customer_query.where(Customer.id != exclude_customer_id)
    customer = db.scalar(customer_query.order_by(Customer.created_at.asc()).limit(1))
    matched_leads: list[Lead] = []
    if customer:
        matched_leads = list(db.scalars(select(Lead).where(Lead.deleted_at.is_(None), or_(Lead.customer_id == customer.id, Lead.converted_customer_id == customer.id))).unique())
        for new_name, new_value in incoming:
            for old_name, old_value in (("phone_primary", normalize_phone(customer.primary_phone) or customer.phone_primary_normalized), ("phone_secondary", normalize_phone(customer.secondary_phone) or customer.phone_secondary_normalized)):
                if new_value and old_value and new_value == old_value:
                    return DuplicateLeadResult(True, customer.id, [lead.id for lead in matched_leads], new_value, f"{new_name}_to_{old_name}", True, bool(current_user and current_user.is_superuser), "Customer profile chung được phép xem; journey khác team bị ẩn nếu không có quyền.")
    lead_query = select(Lead).where(
        Lead.deleted_at.is_(None),
        or_(Lead.phone_primary_normalized.in_(phones), Lead.phone_secondary_normalized.in_(phones), Lead.phone_primary.in_(phones), Lead.phone_secondary.in_(phones)),
    )
    if exclude_lead_id:
        lead_query = lead_query.where(Lead.id != exclude_lead_id)
    matched_leads = list(db.scalars(lead_query.order_by(Lead.created_at.asc())).unique())
    if matched_leads:
        lead = matched_leads[0]
        matched_customer_id = lead.customer_id or lead.converted_customer_id
        for new_name, new_value in incoming:
            for old_name, old_value in (("phone_primary", normalize_phone(lead.phone_primary) or lead.phone_primary_normalized), ("phone_secondary", normalize_phone(lead.phone_secondary) or lead.phone_secondary_normalized)):
                if new_value and old_value and new_value == old_value:
                    return DuplicateLeadResult(True, matched_customer_id, [item.id for item in matched_leads], new_value, f"{new_name}_to_{old_name}", True, bool(current_user and current_user.is_superuser), "Duplicate chỉ theo phone chính/phụ đã chuẩn hóa; Email/Zalo/Facebook không dùng làm match chắc chắn.")
    return DuplicateLeadResult(is_duplicate=False, matched_lead_ids=[])
