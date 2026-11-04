from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel


class BrandListView(SQLModel, table=True):
    __tablename__ = "vs_brand_list"

    class_id: int = Field(primary_key=True)
    object_id: int = Field(primary_key=True)
    brand_name: str
    brand_description: str | None = None


class CategoryListView(SQLModel, table=True):
    __tablename__ = "vs_category_list"

    parent_class_id: int | None = None
    class_id: int = Field(primary_key=True)
    entity_id: int
    category_name: str
    category_description: str | None = None
    created_at: datetime
    updated_at: datetime


class ProductListView(SQLModel, table=True):
    __tablename__ = "vs_product_list"

    product_id: UUID = Field(primary_key=True)
    object_id: int
    product_name: str
    product_description: str | None = None
    category_id: int
    brand_id: int | None = None
    sku_code: str | None
    price: int
    stock: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
