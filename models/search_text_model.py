from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class SearchText(SQLModel, table=True):
    __tablename__ = "search_texts"

    search_text_id: UUID = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(foreign_key="objects.object_id")

    type: Optional[str] = None
    description: Optional[str] = None
    price: Optional[str] = None
    instruction: Optional[str] = None
    ingredient: Optional[str] = None
    url: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
