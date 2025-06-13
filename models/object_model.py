from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlmodel import Field, SQLModel


class Object(SQLModel, table=True):
    __tablename__ = "objects"

    object_id: Optional[int] = Field(default=None, primary_key=True)
    entity_id: Optional[int] = Field(default=None, foreign_key="entities.entity_id")

    chinese_name: Optional[str] = Field(default=None, max_length=512)
    chinese_description: Optional[str] = Field(default=None, max_length=4000)
    english_name: Optional[str] = Field(default=None, max_length=512)
    english_description: Optional[str] = Field(default=None, max_length=4000)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    owner_id: Optional[UUID] = Field(default=None, foreign_key="users.user_id")

    click_count: int = Field(default=0)
    outlink_count: Optional[int] = Field(default=None)
    inlink_count: Optional[int] = Field(default=None)

    is_hided: bool = Field(default=False)
    is_deleted: bool = Field(default=False)


class KnowledgeListView(SQLModel, table=True):
    __tablename__ = "vs_knowledge_list"

    class_id: int = Field(primary_key=True)
    object_id: int = Field(primary_key=True)
    question: str
    answer: Optional[str]
