from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class SearchImage(SQLModel, table=True):
    __tablename__ = "search_images"

    search_image_id: UUID = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(foreign_key="objects.object_id")

    image_src: str
    ocr_text: str

    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
