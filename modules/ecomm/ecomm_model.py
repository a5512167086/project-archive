from datetime import UTC, datetime
from typing import Annotated, Literal
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


class ProductDetail(SQLModel, table=True):
    __tablename__ = "product_details"

    product_id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    brand_id: int | None = None
    object_id: int = Field(index=True)
    is_active: bool = Field(default=True)
    sku_code: str | None = Field(default=None, max_length=64, unique=True)
    price: int
    stock: int | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProductImage(SQLModel, table=True):
    __tablename__ = "product_images"
    __table_args__ = (UniqueConstraint("object_id", "filename"),)

    image_id: int | None = Field(default=None, primary_key=True)
    filename: str
    object_id: int = Field(index=True)
    is_primary: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProductVariant(SQLModel, table=True):
    __tablename__ = "product_variants"

    variant_id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    object_id: int | None = None
    variant_name: str = Field(max_length=100)
    sku_code: str | None = Field(default=None, max_length=64)
    price: int | None = Field(default=None)
    stock: int | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


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


class ShippingOption(BaseModel):
    method: Literal["home_delivery", "store_pickup"]
    fee: int = PydanticField(ge=0, description="運費")
    is_enabled: bool = True


class ShippingSetting(Document):
    bot_uuid: Annotated[str, Indexed(unique=True)]
    shipping_options: list[ShippingOption] = PydanticField(default_factory=list)

    class Settings:
        name = "shipping_settings"


class OrderDetail(SQLModel, table=True):
    __tablename__ = "order_details"

    order_id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(index=True)
    total_amount: int
    status: OrderStatus = Field(default=OrderStatus.pending, max_length=16)
    payment_method: PaymentMethod | None = Field(default=None, max_length=32)
    payment_status: PaymentStatus | None = Field(default=None, max_length=16)
    shipping_method: ShippingMethod | None = Field(default=None, max_length=32)
    shipping_fee: int = Field(default=0)
    tracking_number: str | None = Field(default=None, max_length=128)
    recipient_name: str | None = Field(default=None, max_length=128)
    recipient_phone: str | None = Field(default=None, max_length=32)
    shipping_address: str | None = Field(default=None)
    notes: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    order_item_id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(index=True)
    product_id: UUID
    variant_id: UUID | None = Field(default=None, index=True)
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
    payment_method: str | None = None
    payment_status: str | None = None
    shipping_method: str | None = None
    shipping_fee: int
    tracking_number: str | None = None
    recipient_name: str | None = None
    recipient_phone: str | None = None
    shipping_address: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
