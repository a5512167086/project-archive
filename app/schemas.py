from typing import Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

ModelName = Literal["gpt_5_mini", "qwen3_local", "gemini_2.5_flash"]


class IngestRequest(BaseModel):
    bot_uuid: UUID


class QueryRequest(BaseModel):
    bot_uuid: UUID
    line_id: Optional[str] = None
    query: str
    top_k: int = 3
    score_threshold: float = 0.5
    model: ModelName = Field(default="gpt_5_mini")


class QueryHit(BaseModel):
    id: str
    score: float
    rerank_score: Optional[float] = None
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
