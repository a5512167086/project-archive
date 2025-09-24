from typing import Optional

from sqlmodel import Field, SQLModel


class Entity(SQLModel, table=True):
    __tablename__ = "entities"

    entity_id: Optional[int] = Field(default=None, primary_key=True)
    chinese_name: str = Field(max_length=50)
    english_name: str = Field(max_length=50)
    is_relational: bool = Field(default=True)
    is_hidable: bool = Field(default=False)
    is_deletable: bool = Field(default=False)
