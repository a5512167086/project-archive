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
    english_name: str
    type: str
    description: Optional[str]
    price: Optional[str]
    instruction: Optional[str]
    ingredient: Optional[str]
    url: HttpUrl
    images: List[Image]


class DeleteSearchItemsReponse(BaseModel):
    success_ids: List[int]
    failed_ids: List[int]


class InsertSearchItemsFromUrlRequest(BaseModel):
    bot_class_id: int
    url: str


class DeleteSearchItemsRequest(BaseModel):
    bot_class_id: int
    deleted_id_list: List[int]


class TextSearchItemsRequest(BaseModel):
    bot_class_id: int
    query: str


class ImageSearchItemsRequest(BaseModel):
    bot_class_id: int
    image_query_src: HttpUrl


class SearchItemsResponse(BaseModel):
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
    url: Optional[str]


class ErrorResponse(BaseModel):
    error_code: str
    error_message: str
