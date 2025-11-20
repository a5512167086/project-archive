from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    bot_uuid: UUID


class QueryRequest(BaseModel):
    bot_uuid: UUID
    query: str
    top_k: int = 5
    score_threshold: float = 0.3
    models: List[str] = Field(default=["gpt_5_mini", "qwen3_local", "gemini_2.5_flash"])


class QueryHit(BaseModel):
    id: str
    score: float
    object_id: int | None = None
    question: Optional[str] = None
    answer: Optional[str] = None


class QueryResponse(BaseModel):
    answers: Dict[str, str]
    hits: List[QueryHit]


class KnowledgeItem(BaseModel):
    object_id: int
    question: str
    answer: Optional[str] = None
