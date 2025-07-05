from typing import Optional

from sqlmodel import Field, SQLModel


class BrandListView(SQLModel, table=True):
    __tablename__ = "vs_brand_list"

    class_id: int = Field(primary_key=True)
    object_id: int = Field(primary_key=True)
    brand_name: str
    brand_description: Optional[str] = None
