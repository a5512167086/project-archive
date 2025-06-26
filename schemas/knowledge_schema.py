from typing import List
from uuid import UUID

from pydantic import BaseModel


class InsertKnowledgeRequest(BaseModel):
    bot_uuid: UUID
    question: str
    answer: str


class DeleteKnowledgeRequest(BaseModel):
    bot_uuid: UUID
    deleted_id_list: List[int]
