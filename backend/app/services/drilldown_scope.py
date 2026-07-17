from __future__ import annotations

from fastapi import HTTPException

DRILLDOWN_SCOPES = {"mine", "own", "all"}


def normalize_drilldown_scope(scope: str | None) -> str | None:
    if scope is None or scope == "":
        return None
    normalized = scope.strip().lower()
    if normalized not in DRILLDOWN_SCOPES:
        raise HTTPException(status_code=400, detail="Phạm vi lọc không hợp lệ")
    return "mine" if normalized == "own" else normalized


def mine_only(scope: str | None) -> bool:
    return normalize_drilldown_scope(scope) == "mine"

