from typing import Any


def success_response(data: Any = None, message: str = "Success", meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": True, "message": message, "data": data, "meta": meta or {}}
