import json
from typing import Any

from app.bookings.constants import BOOKING_STATUS_LABELS


def status_label(value: str | None) -> str | None:
    return BOOKING_STATUS_LABELS.get(value, value) if value else None


def is_status_transition(old_value: str | None, new_value: str | None) -> bool:
    return old_value in BOOKING_STATUS_LABELS or new_value in BOOKING_STATUS_LABELS


def decode_activity_context(content: str | None) -> dict[str, Any]:
    if not content:
        return {}
    try:
        value = json.loads(content)
    except (TypeError, json.JSONDecodeError):
        return {"note": content}
    return value if isinstance(value, dict) else {}


def status_activity_content(payload: Any) -> str:
    context: dict[str, Any] = {}
    for field in ("note", "cancel_reason", "refund_reason", "deduction_reason", "refund_amount", "deduction_amount", "booking_amount", "deposit_amount"):
        value = getattr(payload, field, None)
        if value is not None and value != "":
            context[field] = str(value) if field.endswith("_amount") else value
    return json.dumps(context, ensure_ascii=False)
