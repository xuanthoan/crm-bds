from __future__ import annotations

import unicodedata

from app.audit_constants import ACTION_LABELS, MODULE_LABELS


EXTRA_ACTION_LABELS = {
    'auth.login': 'Đăng nhập',
    'auth.logout': 'Đăng xuất',
    'contracts.create': 'Tạo hợp đồng',
    'contracts.update': 'Cập nhật hợp đồng',
    'contracts.status_change': 'Đổi trạng thái hợp đồng',
    'contracts.delete': 'Xóa hợp đồng',
    'bookings.create': 'Tạo booking',
    'bookings.update': 'Cập nhật booking',
    'bookings.status_change': 'Đổi trạng thái booking',
    'deals.create': 'Tạo giao dịch',
    'deals.create_from_booking': 'Tạo giao dịch từ booking',
    'deals.status_change': 'Đổi trạng thái giao dịch',
    'inventory.properties.create': 'Tạo bất động sản',
}

EXTRA_MODULE_LABELS = {
    'auth': 'Xác thực',
    'audit_log': 'Lịch sử thao tác',
    'system': 'Hệ thống',
    'contracts': 'Hợp đồng',
    'contract': 'Hợp đồng',
    'bookings': 'Booking / Giữ chỗ',
    'booking': 'Booking / Giữ chỗ',
    'deals': 'Giao dịch',
    'deal': 'Giao dịch',
    'customers': 'Khách hàng',
    'customer': 'Khách hàng',
    'leads': 'Khách tiềm năng',
    'lead': 'Khách tiềm năng',
    'inventory.properties': 'Bất động sản',
    'property_unit': 'Bất động sản',
    'property_units': 'Bất động sản',
    'users': 'Người dùng',
    'user': 'Người dùng',
}

ENTITY_TYPE_ALIASES = {
    'contract': {'contract', 'contracts', 'hợp đồng', 'hop dong'},
    'contracts': {'contract', 'contracts', 'hợp đồng', 'hop dong'},
    'booking': {'booking', 'bookings', 'giữ chỗ', 'giu cho'},
    'bookings': {'booking', 'bookings', 'giữ chỗ', 'giu cho'},
    'deal': {'deal', 'deals', 'giao dịch', 'giao dich'},
    'deals': {'deal', 'deals', 'giao dịch', 'giao dich'},
    'customer': {'customer', 'customers', 'khách hàng', 'khach hang'},
    'customers': {'customer', 'customers', 'khách hàng', 'khach hang'},
    'lead': {'lead', 'leads', 'khách tiềm năng', 'khach tiem nang'},
    'leads': {'lead', 'leads', 'khách tiềm năng', 'khach tiem nang'},
    'property_unit': {'property', 'property_unit', 'property_units', 'bất động sản', 'bat dong san'},
    'property_units': {'property', 'property_unit', 'property_units', 'bất động sản', 'bat dong san'},
    'inventory.properties': {'property', 'property_unit', 'property_units', 'inventory.properties', 'bất động sản', 'bat dong san'},
    'user': {'user', 'users', 'người dùng', 'nguoi dung'},
    'users': {'user', 'users', 'người dùng', 'nguoi dung'},
    'auth': {'auth', 'xác thực', 'xac thuc'},
}

ACTION_ALIASES = {
    'auth.login': {'đăng nhập', 'dang nhap'},
    'auth.logout': {'đăng xuất', 'dang xuat'},
    'bookings.status_change': {'đổi trạng thái booking', 'doi trang thai booking'},
    'bookings.create': {'tạo booking', 'tao booking'},
    'contracts.status_change': {'đổi trạng thái hợp đồng', 'doi trang thai hop dong'},
    'contracts.create': {'tạo hợp đồng', 'tao hop dong'},
    'deals.create_from_booking': {'tạo giao dịch từ booking', 'tao giao dich tu booking'},
}


def normalize_audit_search_text(value) -> str:
    if value is None:
        return ''
    text = unicodedata.normalize('NFD', str(value)).lower()
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    return ' '.join(text.replace('đ', 'd').split())


def label_action(value: str | None) -> str | None:
    return EXTRA_ACTION_LABELS.get(value or '') or ACTION_LABELS.get(value or '') or value


def label_module(value: str | None) -> str | None:
    return EXTRA_MODULE_LABELS.get(value or '') or MODULE_LABELS.get(value or '') or value


def matching_alias_values(keyword: str, aliases_by_raw: dict[str, set[str]], labels_by_raw: dict[str, str] | None = None) -> set[str]:
    normalized = normalize_audit_search_text(keyword)
    if not normalized:
        return set()
    labels_by_raw = labels_by_raw or {}
    matches: set[str] = set()
    for raw, aliases in aliases_by_raw.items():
        candidates = {raw, *aliases}
        if raw in labels_by_raw:
            candidates.add(labels_by_raw[raw])
        if any(normalized in normalize_audit_search_text(candidate) or normalize_audit_search_text(candidate) in normalized for candidate in candidates):
            matches.add(raw)
    return matches


def matching_entity_types(keyword: str) -> set[str]:
    return matching_alias_values(keyword, ENTITY_TYPE_ALIASES) or {str(keyword).strip()}


def matching_action_values(keyword: str) -> set[str]:
    labels = {**ACTION_LABELS, **EXTRA_ACTION_LABELS}
    aliases = {raw: set() for raw in labels}
    for raw, values in ACTION_ALIASES.items():
        aliases.setdefault(raw, set()).update(values)
    return matching_alias_values(keyword, aliases, labels)


def matching_module_values(keyword: str) -> set[str]:
    labels = {**MODULE_LABELS, **EXTRA_MODULE_LABELS}
    aliases = {raw: set() for raw in labels}
    return matching_alias_values(keyword, aliases, labels)
