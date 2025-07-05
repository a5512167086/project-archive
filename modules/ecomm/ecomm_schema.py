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
