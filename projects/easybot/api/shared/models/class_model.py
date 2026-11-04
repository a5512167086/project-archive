from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlmodel import Field, SQLModel


class Class(SQLModel, table=True):
    __tablename__ = "classes"

    class_id: Optional[int] = Field(default=None, primary_key=True)
    entity_id: Optional[int] = Field(default=None, index=True)

    chinese_name: str = Field(max_length=256)
    chinese_description: Optional[str] = Field(default=None, max_length=4000)
    english_name: Optional[str] = Field(default=None, max_length=256)
    english_description: Optional[str] = Field(default=None, max_length=4000)

    id_path: Optional[str] = Field(default=None, max_length=900, unique=True)
    name_path: Optional[str] = Field(default=None, max_length=450, unique=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class_rank: int = Field(default=0)
    object_rank: int = Field(default=0)
    hierarchy_level: Optional[int] = None
    keywords: str = Field(default="", max_length=512)

    owner_id: Optional[UUID] = Field(default=None, foreign_key="users.user_id")

    is_hided: bool = Field(default=False)
    is_deleted: bool = Field(default=False)


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
