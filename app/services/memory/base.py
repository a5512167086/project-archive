# app/services/rag_modules/base.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol

from langchain_core.messages import BaseMessage


@dataclass(frozen=True)
class MemorySnapshot:
    """Data loaded from memory for the current session."""

    recent_messages: List[BaseMessage]
    summary: str = ""  # optional; empty if not supported


class MemoryModule(Protocol):
    def load(self, session_key: str, max_messages: int) -> MemorySnapshot: ...

    def append_turn(self, session_key: str, human: str, ai: str) -> None: ...

    def clear(self, session_key: str) -> None: ...


@dataclass(frozen=True)
class RewriteResult:
    """Rewrite output + debug info for ablation."""

    original: str
    rewritten: str
    used_history: bool = False
    used_summary: bool = False
    model_name: Optional[str] = None


class QueryRewriter(Protocol):
    def rewrite(
        self,
        user_query: str,
        snapshot: MemorySnapshot,
        rewrite_model: str,
    ) -> RewriteResult:
        pass
