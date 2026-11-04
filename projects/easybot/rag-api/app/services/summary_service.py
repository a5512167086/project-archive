from __future__ import annotations

from typing import Any

from app.schemas import MemorySnapshot


class SummaryService:
    def __init__(self, summary_memory: Any) -> None:
        self.mem = summary_memory

    def load(self, session_key: str, max_messages: int) -> MemorySnapshot:
        return self.mem.load(session_key, max_messages=max_messages)

    def load_recent_only(self, session_key: str, max_messages: int) -> MemorySnapshot:
        load_recent_only = getattr(self.mem, "load_recent_only", None)
        if callable(load_recent_only):
            return load_recent_only(session_key, max_messages=max_messages)
        return self.mem.load(session_key, max_messages=max_messages)

    def maybe_update_summary(self, session_key: str, *, force: bool = False) -> bool:
        fn = getattr(self.mem, "maybe_update_summary", None)
        if callable(fn):
            return bool(fn(session_key, force=force))
        return False

    def append_turn(self, session_key: str, human: str, ai: str) -> None:
        fn = getattr(self.mem, "append_turn", None)
        if callable(fn):
            fn(session_key, human=human, ai=ai)
