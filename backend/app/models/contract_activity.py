import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utcnow(): return datetime.now(timezone.utc)
class ContractActivity(Base):
    __tablename__="contract_activities"
    __table_args__=tuple(Index(f"ix_contract_activities_{c}",c) for c in ("contract_id","actor_id","activity_type","created_at"))
    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); contract_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("contracts.id",ondelete="CASCADE"),nullable=False); actor_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id"),nullable=False); activity_type:Mapped[str]=mapped_column(String(30),nullable=False); title:Mapped[str]=mapped_column(String(255),nullable=False); content:Mapped[str|None]=mapped_column(Text); old_value:Mapped[str|None]=mapped_column(Text); new_value:Mapped[str|None]=mapped_column(Text); metadata_json:Mapped[dict[str,Any]|None]=mapped_column("metadata",JSON); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow,nullable=False)
    contract=relationship("Contract",back_populates="activities"); actor=relationship("User")
