from collections.abc import Mapping
from typing import Any


def collect_price_changes(
    item: Any,
    data: Mapping[str, Any],
    price_fields: tuple[str, ...],
) -> list[tuple[str, Any, Any]]:
    """Return stable (field, old value, new value) tuples for changed prices only."""
    return [
        (field, getattr(item, field), data[field])
        for field in price_fields
        if field in data and getattr(item, field) != data[field]
    ]
