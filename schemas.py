from pydantic import BaseModel


class InsertFAQRequest(BaseModel):
    bot_class_id: int
    question: str
    answer: str


class ErrorResponse(BaseModel):
    error_code: str
    error_message: str
