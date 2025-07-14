from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

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


# Product models
class ProductDetail(SQLModel, table=True):
    __tablename__ = "product_details"

    product_id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    brand_id: Optional[int] = None
    object_id: int = Field(index=True)
    is_active: bool = Field(default=True)
    sku_code: str = Field(max_length=64, unique=True)
    price: int
    stock: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProductImage(SQLModel, table=True):
    __tablename__ = "product_images"

    image_id: Optional[int] = Field(default=None, primary_key=True)
    image_url: str
    object_id: int = Field(index=True)
    display_order: int = Field(default=0)


class ProductVariant(SQLModel, table=True):
    __tablename__ = "product_variants"

    variant_id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    object_id: Optional[int] = None
    variant_name: str = Field(max_length=100)
    sku_code: Optional[str] = Field(default=None, max_length=64, unique=True)
    price: Optional[int] = None
    stock: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
