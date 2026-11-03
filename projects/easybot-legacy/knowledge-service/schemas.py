from typing import List

from pydantic import BaseModel


class InsertKnowledgeRequest(BaseModel):
    bot_class_id: int
    question: str
    answer: str


class DeleteKnowledgeRequest(BaseModel):
    bot_class_id: int
    deleted_id_list: List[int]


class ErrorResponse(BaseModel):
    error_code: str
    error_message: str
