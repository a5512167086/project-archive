from typing import Optional

from sqlmodel import Field, SQLModel


class Inheritance(SQLModel, table=True):
    __tablename__ = "inheritances"

    parent_class_id: int = Field(primary_key=True, foreign_key="classes.class_id")
    child_class_id: int = Field(primary_key=True, foreign_key="classes.class_id")

    rank: Optional[int] = Field(default=None)
    membership_grade: Optional[int] = Field(default=None)
