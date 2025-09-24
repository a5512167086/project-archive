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
    models: List[str] = Field(
        default=["gpt35_azure", "huggingface_local"],
        description="要使用的 LLM 模型列表 (例如: ['gpt35_azure', 'huggingface_local'])",
    )


class QueryHit(BaseModel):
    id: str
    score: float
    object_id: int | None = None
    question: Optional[str] = None
    answer: Optional[str] = None


class QueryResponse(BaseModel):
    answers: Dict[str, str]
    hits: List[QueryHit]
