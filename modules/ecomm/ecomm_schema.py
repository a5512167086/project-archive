from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class InsertBrandRequest(BaseModel):
    bot_uuid: UUID
    brand_name: str
    brand_description: str


class DeleteBrandRequest(BaseModel):
    bot_uuid: UUID
    deleted_id_list: List[int]


class BrandResponse(BaseModel):
    class_id: int
    object_id: int
    brand_name: str
    brand_description: Optional[str] = None


class UpdateBrandRequest(BaseModel):
    bot_uuid: UUID
    object_id: int
    brand_name: Optional[str] = None
    brand_description: Optional[str] = None


# Category schemas
class InsertCategoryRequest(BaseModel):
    bot_uuid: UUID
    category_name: str
    category_description: str
    parent_category_id: Optional[int] = None


class DeleteCategoryRequest(BaseModel):
    bot_uuid: UUID
    deleted_class_id_list: List[int]


class CategoryResponse(BaseModel):
    parent_class_id: Optional[int] = None
    class_id: int
    category_name: str
    category_description: Optional[str] = None
    children: List["CategoryResponse"] = []


class UpdateCategoryRequest(BaseModel):
    bot_uuid: UUID
    class_id: int
    category_name: Optional[str] = None
    category_description: Optional[str] = None
    parent_category_id: Optional[int] = None


# Product schemas
class ProductImageRequest(BaseModel):
    image_url: str
    display_order: int = 0


class InsertProductWithImagesRequest(BaseModel):
    bot_uuid: UUID
    product_name: str
    product_description: str
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    sku_code: str
    price: int
    stock: int = 0
    is_active: bool = True
    variants: List["ProductVariantRequest"] = []


class ProductVariantRequest(BaseModel):
    variant_name: str
    sku_code: Optional[str] = None
    price: Optional[int] = None
    stock: int = 0


class InsertProductRequest(BaseModel):
    bot_uuid: UUID
    product_name: str
    product_description: str
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    sku_code: str
    price: int
    stock: int = 0
    is_active: bool = True
    images: List[ProductImageRequest] = []
    variants: List[ProductVariantRequest] = []


class ProductImageResponse(BaseModel):
    image_id: int
    image_url: str
    object_id: int
    display_order: int


class ProductVariantResponse(BaseModel):
    variant_id: UUID
    object_id: Optional[int]
    variant_name: str
    sku_code: Optional[str]
    price: Optional[int]
    stock: int
    created_at: datetime
    updated_at: datetime


class ProductResponse(BaseModel):
    product_id: UUID
    object_id: int
    product_name: str
    product_description: Optional[str]
    brand_id: Optional[int]
    category_id: Optional[int]
    sku_code: str
    price: int
    stock: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    images: List[ProductImageResponse] = []
    variants: List[ProductVariantResponse] = []


class UpdateProductRequest(BaseModel):
    bot_uuid: UUID
    product_id: UUID
    product_name: Optional[str] = None
    product_description: Optional[str] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    sku_code: Optional[str] = None
    price: Optional[int] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None


class DeleteProductRequest(BaseModel):
    bot_uuid: UUID
    product_ids: List[UUID]


# Shipping schemas
class ShippingOptionSchema(BaseModel):
    method: Literal["home_delivery", "store_pickup"]
    fee: int = Field(ge=0, description="運費")
    is_enabled: bool = True


class UpdateShippingSettingRequest(BaseModel):
    bot_uuid: UUID
    shipping_options: List[ShippingOptionSchema]


class ShippingSettingResponse(BaseModel):
    bot_uuid: str
    shipping_options: List[ShippingOptionSchema]


class DeleteShippingMethodRequest(BaseModel):
    bot_uuid: UUID
    method: Literal["home_delivery", "store_pickup"]


# Order schemas
class OrderItemSchema(BaseModel):
    variant_id: Optional[UUID] = None
    product_name_snapshot: str
    sku_snapshot: str
    price_snapshot: int
    quantity: int


class InsertOrderRequest(BaseModel):
    bot_uuid: UUID
    total_amount: int
    payment_method: str
    payment_status: str
    shipping_method: str
    shipping_fee: int
    recipient_name: str
    recipient_phone: str
    shipping_address: str
    items: List[OrderItemSchema]


class OrderResponse(BaseModel):
    order_id: UUID
    object_id: int
    total_amount: int
    status: str
    payment_method: Optional[str]
    payment_status: Optional[str]
    shipping_method: Optional[str]
    shipping_fee: int
    tracking_number: Optional[str]
    recipient_name: Optional[str]
    recipient_phone: Optional[str]
    shipping_address: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemSchema] = []


class UpdateOrderRequest(BaseModel):
    bot_uuid: UUID
    order_id: UUID
    status: Optional[str] = None
    payment_status: Optional[str] = None
    tracking_number: Optional[str] = None


class DeleteOrderRequest(BaseModel):
    bot_uuid: UUID
    order_ids: List[UUID]
