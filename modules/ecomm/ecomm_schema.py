from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


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
    entity_id: int
    category_name: str
    category_description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class UpdateCategoryRequest(BaseModel):
    bot_uuid: UUID
    class_id: int
    category_name: Optional[str] = None
    category_description: Optional[str] = None
    parent_category_id: Optional[int] = None
