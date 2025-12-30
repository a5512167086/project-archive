# app/services/rag_modules/memory/mongo_buffer.py
from __future__ import annotations

from typing import Dict, List

from langchain_core.messages import BaseMessage
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory

from app.services.memory.base import MemoryModule, MemorySnapshot


class BufferMemory(MemoryModule):
    def __init__(
        self, mongo_uri: str, mongo_db_name: str, mongo_collection: str
    ) -> None:
        self.mongo_uri = mongo_uri
        self.mongo_db_name = mongo_db_name
        self.mongo_collection = mongo_collection
        self._history_cache: Dict[str, MongoDBChatMessageHistory] = {}

    def _get_history(self, session_key: str) -> MongoDBChatMessageHistory:
        if session_key in self._history_cache:
            return self._history_cache[session_key]
        h = MongoDBChatMessageHistory(
            connection_string=self.mongo_uri,
            session_id=session_key,
            database_name=self.mongo_db_name,
            collection_name=self.mongo_collection,
        )
        self._history_cache[session_key] = h
        return h

    def load(self, session_key: str, max_messages: int) -> MemorySnapshot:
        h = self._get_history(session_key)
        msgs: List[BaseMessage] = h.messages or []
        if max_messages > 0:
            msgs = msgs[-max_messages:]
        else:
            msgs = []
        return MemorySnapshot(recent_messages=msgs, summary="")

    def append_turn(self, session_key: str, human: str, ai: str) -> None:
        h = self._get_history(session_key)
        h.add_user_message(human)
        h.add_ai_message(ai)

    def clear(self, session_key: str) -> None:
        h = self._get_history(session_key)
        h.clear()
