import re


def normalize_phone(value: str | None) -> str | None:
    """Return a canonical, duplicate-detection friendly phone value.

    Sprint 31 intentionally keeps validation permissive: empty input becomes
    None, separators are stripped, +84/84 Vietnam prefixes are mapped to a
    leading 0, and unknown-but-usable digit strings are returned as-is.
    """
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return None
    if digits.startswith("84") and len(digits) >= 11:
        digits = f"0{digits[2:]}"
    return digits or None
