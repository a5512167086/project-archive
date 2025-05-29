from typing import List, Optional

from pydantic import UUID4, BaseModel, HttpUrl


class Image(BaseModel):
    image_src: HttpUrl
    ocr_text: str


class SearchItem(BaseModel):
    search_text_id: UUID4
    class_id: int
    object_id: int
    chinese_name: str
    english_name: Optional[str]
    type: Optional[str]
    description: Optional[str]
    price: Optional[str]
    instruction: Optional[str]
    ingredient: Optional[str]
    url: Optional[HttpUrl]
    images: List[Image]


class DeleteSearchItemsReponse(BaseModel):
    success_ids: List[int]
    failed_ids: List[int]


class InsertSearchItemsFromUrlRequest(BaseModel):
    bot_class_id: int
    url: str


class InsertSearchItemRequest(BaseModel):
    bot_class_id: int
    item_name: str
    item_english_name: Optional[str] = None
    item_type: Optional[str] = None
    item_description: Optional[str] = None
    item_price: Optional[str] = None
    item_instruction: Optional[str] = None
    item_ingredient: Optional[str] = None
    item_url: Optional[HttpUrl] = None


class NewSearchItem(BaseModel):
    item_name: str
    item_english_name: Optional[str] = None
    item_type: Optional[str] = None
    item_description: Optional[str] = None
    item_price: Optional[str] = None
    item_instruction: Optional[str] = None
    item_ingredient: Optional[str] = None
    item_url: Optional[HttpUrl] = None


class DeleteSearchItemsRequest(BaseModel):
    bot_class_id: int
    deleted_id_list: List[int]


class TextSearchItemsRequest(BaseModel):
    bot_class_id: int
    query: str


class ImageSearchItemsRequest(BaseModel):
    bot_class_id: int
    image_query_src: HttpUrl


class LineImageSearchItemsRequest(BaseModel):
    bot_class_id: int
    image_base64: str


class SearchImageItemsResponse(BaseModel):
    search_image_id: str
    class_id: int
    object_id: int
    chinese_name: str
    english_name: str
    image_src: HttpUrl
    url: HttpUrl


class SearchTextItemsResponse(BaseModel):
    search_text_id: UUID4
    class_id: int
    object_id: int
    chinese_name: str
    english_name: Optional[str]
    type: Optional[str]
    description: Optional[str]
    price: Optional[str]
    instruction: Optional[str]
    ingredient: Optional[str]
    url: Optional[HttpUrl]
