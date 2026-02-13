from datetime import datetime, timezone
from typing import Annotated, List, Literal, Optional
from uuid import UUID, uuid4

from beanie import Document, Indexed
from pydantic import BaseModel
from pydantic import Field as PydanticField
from sqlmodel import Field, SQLModel, UniqueConstraint

from shared.constants.common import (
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    ShippingMethod,
)


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


class ProductDetail(SQLModel, table=True):
    __tablename__ = "product_details"

    product_id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    brand_id: Optional[int] = None
    object_id: int = Field(index=True)
    is_active: bool = Field(default=True)
    sku_code: Optional[str] = Field(default=None, max_length=64, unique=True)
    price: int
    stock: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProductImage(SQLModel, table=True):
    __tablename__ = "product_images"
    __table_args__ = (UniqueConstraint("object_id", "filename"),)

    image_id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    object_id: int = Field(index=True)
    is_primary: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProductVariant(SQLModel, table=True):
    __tablename__ = "product_variants"

    variant_id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    object_id: Optional[int] = None
    variant_name: str = Field(max_length=100)
    sku_code: Optional[str] = Field(default=None, max_length=64)
    price: Optional[int] = Field(default=None)
    stock: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProductListView(SQLModel, table=True):
    __tablename__ = "vs_product_list"

    product_id: UUID = Field(primary_key=True)
    object_id: int
    product_name: str
    product_description: Optional[str] = None
    category_id: int
    brand_id: Optional[int] = None
    sku_code: Optional[str]
    price: int
    stock: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ShippingOption(BaseModel):
    method: Literal["home_delivery", "store_pickup"]
    fee: int = PydanticField(ge=0, description="運費")
    is_enabled: bool = True


class ShippingSetting(Document):
    bot_uuid: Annotated[str, Indexed(unique=True)]
    shipping_options: List[ShippingOption] = PydanticField(default_factory=list)

    class Settings:
        name = "shipping_settings"


class OrderDetail(SQLModel, table=True):
    __tablename__ = "order_details"

    order_id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(index=True)
    total_amount: int
    status: OrderStatus = Field(default=OrderStatus.pending, max_length=16)
    payment_method: Optional[PaymentMethod] = Field(default=None, max_length=32)
    payment_status: Optional[PaymentStatus] = Field(default=None, max_length=16)
    shipping_method: Optional[ShippingMethod] = Field(default=None, max_length=32)
    shipping_fee: int = Field(default=0)
    tracking_number: Optional[str] = Field(default=None, max_length=128)
    recipient_name: Optional[str] = Field(default=None, max_length=128)
    recipient_phone: Optional[str] = Field(default=None, max_length=32)
    shipping_address: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    order_item_id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(index=True)
    product_id: UUID
    variant_id: Optional[UUID] = Field(default=None, index=True)
    quantity: int
    unit_price: int
    subtotal: int


class OrderListView(SQLModel, table=True):
    __tablename__ = "vs_order_list"
    class_id: int
    order_id: UUID = Field(primary_key=True)
    object_id: int
    total_amount: int
    status: str
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None
    shipping_method: Optional[str] = None
    shipping_fee: int
    tracking_number: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_phone: Optional[str] = None
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
