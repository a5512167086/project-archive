# app/services/memory/null.py
# app/services/rag_modules/rewriter/null_rewriter.py
from __future__ import annotations

from app.services.memory.base import (
    MemoryModule,
    MemorySnapshot,
    QueryRewriter,
    RewriteResult,
)


class NullMemory(MemoryModule):
    def load(self, session_key: str, max_messages: int) -> MemorySnapshot:
        return MemorySnapshot(recent_messages=[], summary="")

    def append_turn(self, session_key: str, human: str, ai: str) -> None:
        return

    def clear(self, session_key: str) -> None:
        return


class NullQueryRewriter(QueryRewriter):
    def rewrite(
        self, user_query: str, snapshot: MemorySnapshot, rewrite_model: str
    ) -> RewriteResult:
        return RewriteResult(
            original=user_query,
            rewritten=user_query,
            used_history=False,
            used_summary=False,
            model_name=rewrite_model,
        )
