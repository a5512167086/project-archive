from pydantic import BaseModel


class InsertSearchItemFromUrlRequest(BaseModel):
    url: str


class ErrorResponse(BaseModel):
    error_code: str
    error_message: str
