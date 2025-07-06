from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class BrandListView(SQLModel, table=True):
    __tablename__ = "vs_brand_list"

    class_id: int = Field(primary_key=True)
    object_id: int = Field(primary_key=True)
    brand_name: str
    brand_description: Optional[str] = None


class CategoryListView(SQLModel, table=True):
    __tablename__ = "vs_category_list"

    parent_class_id: Optional[int] = None
    class_id: int = Field(primary_key=True)
    entity_id: int
    category_name: str
    category_description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
