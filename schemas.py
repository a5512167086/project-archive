from pydantic import BaseModel


class InsertSearchItemsFromUrlRequest(BaseModel):
    bot_class_id: int
    url: str


class TextSearchItemsRequest(BaseModel):
    bot_class_id: int
    query: str


class ImageSearchItemsRequest(BaseModel):
    bot_class_id: int
    image_query_src: str


class ErrorResponse(BaseModel):
    error_code: str
    error_message: str
