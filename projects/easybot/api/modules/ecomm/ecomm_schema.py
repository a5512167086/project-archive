from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from modules.ecomm.ecomm_model import ProductVariant
from shared.constants.common import (
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    ShippingMethod,
)


class InsertBrandRequest(BaseModel):
    bot_uuid: UUID
    brand_name: str
    brand_description: str


class DeleteBrandRequest(BaseModel):
    bot_uuid: UUID
    deleted_id_list: list[int]


class BrandResponse(BaseModel):
    class_id: int
    object_id: int
    brand_name: str
    brand_description: str | None = None


class UpdateBrandRequest(BaseModel):
    bot_uuid: UUID
    object_id: int
    brand_name: str | None = None
    brand_description: str | None = None


class InsertCategoryRequest(BaseModel):
    bot_uuid: UUID
    category_name: str
    category_description: str
    parent_category_id: int | None = None


class DeleteCategoryRequest(BaseModel):
    bot_uuid: UUID
    deleted_class_id_list: list[int]


class CategoryResponse(BaseModel):
    parent_class_id: int | None = None
    class_id: int
    category_name: str
    category_description: str | None = None
    children: list["CategoryResponse"] = Field(default_factory=list)


class UpdateCategoryRequest(BaseModel):
    bot_uuid: UUID
    class_id: int
    category_name: str | None = None
    category_description: str | None = None
    parent_category_id: int | None = None


class ProductVariantRequest(BaseModel):
    variant_name: str
    sku_code: str | None = None
    price: int | None = None
    stock: int | None = 0


class InsertProductVariantRequest(BaseModel):
    bot_uuid: UUID
    product_id: UUID
    variant_name: str
    sku_code: str | None = None
    price: int | None = None
    stock: int | None = 0


class UpdateProductVariantRequest(BaseModel):
    bot_uuid: UUID
    variant_id: UUID
    variant_name: str | None = None
    sku_code: str | None = None
    price: int | None = None
    stock: int | None = None


class DeleteProductVariantRequest(BaseModel):
    bot_uuid: UUID
    variant_ids: list[UUID]


class InsertProductWithImagesRequest(BaseModel):
    bot_uuid: UUID
    product_name: str
    product_description: str
    category_id: int | None = None
    brand_id: int | None = None
    sku_code: str | None = None
    price: int
    stock: int | None = 0
    is_active: bool = True
    variants: list[ProductVariantRequest] = []


class ProductImageRequest(BaseModel):
    filename: str
    is_primary: bool = False


class InsertProductRequest(BaseModel):
    bot_uuid: UUID
    product_name: str
    product_description: str
    category_id: int | None = None
    brand_id: int | None = None
    sku_code: str | None = None
    price: int
    stock: int | None = 0
    is_active: bool = True
    images: list[ProductImageRequest] = []
    variants: list[ProductVariantRequest] = []


class ProductImageResponse(BaseModel):
    image_id: int
    filename: str
    image_url: str
    is_primary: bool


class ProductResponse(BaseModel):
    product_id: UUID
    object_id: int
    product_name: str
    product_description: str | None
    brand_id: int | None
    category_id: int | None
    sku_code: str | None
    price: int
    stock: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    images: list[ProductImageResponse] = []
    variants: list[ProductVariant] = []


class UpdateProductRequest(BaseModel):
    bot_uuid: UUID
    product_id: UUID
    product_name: str | None = None
    product_description: str | None = None
    category_id: int | None = None
    brand_id: int | None = None
    sku_code: str | None = None
    price: int | None = None
    stock: int | None = None
    is_active: bool | None = None


class DeleteProductRequest(BaseModel):
    bot_uuid: UUID
    product_ids: list[UUID]


class UpdateProductImageRequest(BaseModel):
    bot_uuid: UUID
    image_id: int
    is_primary: bool | None = None


class DeleteProductImageRequest(BaseModel):
    bot_uuid: UUID
    image_id: int


class ShippingOptionSchema(BaseModel):
    method: Literal["home_delivery", "store_pickup"]
    fee: int = Field(ge=0, description="運費")
    is_enabled: bool = True


class UpdateShippingSettingRequest(BaseModel):
    bot_uuid: UUID
    shipping_options: list[ShippingOptionSchema]


class ShippingSettingResponse(BaseModel):
    bot_uuid: str
    shipping_options: list[ShippingOptionSchema]


class DeleteShippingMethodRequest(BaseModel):
    bot_uuid: UUID
    method: Literal["home_delivery", "store_pickup"]


class OrderItemSchema(BaseModel):
    product_id: UUID
    variant_id: UUID | None = None
    quantity: int


class InsertOrderRequest(BaseModel):
    bot_uuid: UUID
    payment_method: PaymentMethod
    shipping_method: ShippingMethod
    recipient_name: str
    recipient_phone: str
    shipping_address: str | None = None
    notes: str | None = None
    items: list[OrderItemSchema]


class OrderResponse(BaseModel):
    order_id: UUID
    object_id: int
    total_amount: int
    status: str
    payment_method: str | None
    payment_status: str | None
    shipping_method: str | None
    shipping_fee: int
    tracking_number: str | None
    recipient_name: str | None
    recipient_phone: str | None
    shipping_address: str | None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemSchema] = []
    notes: str | None = None


class UpdateOrderRequest(BaseModel):
    bot_uuid: UUID
    order_id: UUID
    status: OrderStatus | None = None
    payment_status: PaymentStatus | None = None
    tracking_number: str | None = None


class DeleteOrderRequest(BaseModel):
    bot_uuid: UUID
    order_ids: list[UUID]
