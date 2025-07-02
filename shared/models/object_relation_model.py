from typing import Optional

from sqlmodel import Field, SQLModel


class ObjectRelation(SQLModel, table=True):
    __tablename__ = "object_relations"

    first_object_id: int = Field(foreign_key="objects.object_id", primary_key=True)
    second_object_id: int = Field(foreign_key="objects.object_id", primary_key=True)

    rank: Optional[int] = Field(default=None)
    relation_description: Optional[str] = Field(default=None, max_length=900)
