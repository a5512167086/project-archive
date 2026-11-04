from typing import Optional

from sqlmodel import Field, SQLModel


class ClassObjectRelation(SQLModel, table=True):
    __tablename__ = "class_object_relations"

    class_id: int = Field(primary_key=True, foreign_key="classes.class_id")
    object_id: int = Field(primary_key=True, foreign_key="objects.object_id")

    rank: Optional[int] = Field(default=None)
    membership_grade: Optional[int] = Field(default=None)
    relation_description: Optional[str] = Field(default=None, max_length=900)
