from pydantic import BaseModel


class InsertSearchItemFromUrlRequest(BaseModel):
    bot_class_id: int
    url: str


class ErrorResponse(BaseModel):
    error_code: str
    error_message: str
