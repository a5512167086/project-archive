from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import Field, SQLModel


class SubClassView(SQLModel, table=True):
    __tablename__ = "vs_sub_class"

    parent_class_id: int
    rank: Optional[int] = None

    class_id: int = Field(primary_key=True)
    entity_id: Optional[int] = None
    chinese_name: str
    chinese_description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    keywords: Optional[str] = None
    owner_id: Optional[UUID] = None
    is_hided: bool
    is_deleted: bool
