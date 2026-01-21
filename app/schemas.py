from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, ConfigDict, Field

ModelName = Literal["gpt_5_mini", "qwen3_local", "gemini_2.5_flash"]


class IngestRequest(BaseModel):
    bot_uuid: UUID


class QueryRequest(BaseModel):
    bot_uuid: UUID
    line_id: Optional[str] = None
    query: str
    top_k: int = 3
    fetch_k: Optional[int] = Field(default=15)
    score_threshold: float = 0.3
    rerank_threshold: float = Field(default=0.5)
    model: str = Field(default="gpt_5_mini")


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


class MemorySnapshot(BaseModel):
    recent_messages: List[BaseMessage]
    summary: str = ""
    model_config = ConfigDict(arbitrary_types_allowed=True)


class RewriteResult(BaseModel):
    original: str
    rewritten: str
    used_history: bool = False
    used_summary: bool = False
    model_name: Optional[str] = None


@dataclass
class BM25Index:
    bm25: Any
    docs: List[Dict[str, Any]]
    built_at: float
    size: int
