# app/services/memory/summary.py
from __future__ import annotations

from typing import Any, Callable, List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.logger import logger
from app.services.memory.base import MemorySnapshot
from app.services.memory.buffer import MongoBufferMemory


class MongoSummaryMemory(MongoBufferMemory):
    """
    On-demand summary over full history, plus returning a recent buffer.
    """

    def __init__(
        self,
        mongo_uri: str,
        mongo_db_name: str,
        mongo_collection: str,
        get_llm: Callable[[str], Any],
        summary_model: str = "gpt_5_mini",
        summary_trigger_threshold: int = 6,
        max_summary_messages: int = 60,
    ) -> None:
        super().__init__(
            mongo_uri=mongo_uri,
            mongo_db_name=mongo_db_name,
            mongo_collection=mongo_collection,
        )
        self._get_llm = get_llm
        self.summary_model = summary_model
        self.summary_trigger_threshold = summary_trigger_threshold
        self.max_summary_messages = max_summary_messages

    def _clean(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        return [m for m in messages if isinstance(m, (HumanMessage, AIMessage))]

    def _summarize(self, messages: List[BaseMessage]) -> str:
        clean = self._clean(messages)
        if len(clean) < self.summary_trigger_threshold:
            return ""

        # 避免太長：最多用最後 N 則訊息做摘要
        clean = clean[-self.max_summary_messages :]

        llm = self._get_llm(self.summary_model)

        system = (
            "你是對話摘要器。"
            "請用繁體中文把對話濃縮為長期摘要。"
            "摘要必須包含：人物/角色、已確認事實、目前目標、已做決策、未解問題。"
            "只輸出摘要內容，不要加標題、不要寒暄。"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system),
            MessagesPlaceholder("chat_history"),
        ])

        chain = prompt | llm | StrOutputParser()
        return chain.invoke({"chat_history": clean}).strip()

    def load(self, session_key: str, max_messages: int) -> MemorySnapshot:
        h = self._get_history(session_key)
        all_msgs = h.messages or []

        recent = all_msgs[-max_messages:] if max_messages > 0 else []

        try:
            summary = self._summarize(all_msgs)
        except Exception as e:
            logger.warning(f"[MongoSummaryMemory] summarize failed: {e}")
            summary = ""

        return MemorySnapshot(recent_messages=recent, summary=summary)
