from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from pymongo import MongoClient

from app.logger import logger
from app.schemas import MemorySnapshot


class SummaryMemory:
    DEFAULT_CACHE_SUFFIX = "_summary_cache"

    def __init__(
        self,
        mongo_uri: str,
        mongo_db_name: str,
        mongo_collection: str,
        get_llm: Callable[[str], Any],
        summary_model: str = "local_model",
        summary_trigger_threshold: int = 6,
        max_summary_messages: int = 30,
        refresh_min_interval_sec: int = 60,
        refresh_every_n_new_msgs: int = 4,
        cache_collection: Optional[str] = None,
    ) -> None:
        self.mongo_uri = mongo_uri
        self.mongo_db_name = mongo_db_name
        self.mongo_collection = mongo_collection
        self._get_llm = get_llm
        self.summary_model = summary_model
        self.summary_trigger_threshold = int(summary_trigger_threshold)
        self.max_summary_messages = int(max_summary_messages)
        self.refresh_min_interval_sec = int(refresh_min_interval_sec)
        self.refresh_every_n_new_msgs = int(refresh_every_n_new_msgs)
        self._history_cache: Dict[str, MongoDBChatMessageHistory] = {}
        self._cache_enabled = MongoClient is not None
        self._cache_col = None

        if self._cache_enabled:
            try:
                client = MongoClient(self.mongo_uri)
                col_name = cache_collection or (
                    self.mongo_collection + self.DEFAULT_CACHE_SUFFIX
                )
                self._cache_col = client[self.mongo_db_name][col_name]
                self._cache_col.create_index("session_key", unique=True)
                self._cache_col.create_index("updated_at")
            except Exception as e:
                logger.warning(f"[SummaryMemory] summary cache init failed: {e}")
                self._cache_enabled = False
                self._cache_col = None
        else:
            logger.warning(
                "[SummaryMemory] pymongo not available; summary cache disabled."
            )

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

    def append_turn(self, session_key: str, *, human: str, ai: str) -> None:
        h = self._get_history(session_key)
        h.add_user_message(human)
        h.add_ai_message(ai)

    def clear(self, session_key: str) -> None:
        h = self._get_history(session_key)
        h.clear()

    def _clean(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        return [m for m in messages if isinstance(m, (HumanMessage, AIMessage))]

    def _get_cached(self, session_key: str) -> Tuple[str, int, float]:
        if not self._cache_enabled or self._cache_col is None:
            return "", 0, 0.0

        t0 = time.perf_counter()
        doc = self._cache_col.find_one(
            {"session_key": session_key},
            {"summary": 1, "msg_count": 1, "updated_at": 1},
        )
        logger.info(f"[Timer] Summary Cache Read: {(time.perf_counter() - t0):.3f}s")

        if not doc:
            return "", 0, 0.0

        summary = (doc.get("summary") or "").strip()
        msg_count = int(doc.get("msg_count") or 0)

        updated_at = doc.get("updated_at")
        if isinstance(updated_at, datetime):
            updated_epoch = updated_at.replace(tzinfo=timezone.utc).timestamp()
        else:
            updated_epoch = 0.0

        return summary, msg_count, updated_epoch

    def _set_cached(self, session_key: str, summary: str, msg_count: int) -> None:
        if not self._cache_enabled or self._cache_col is None:
            return

        t0 = time.perf_counter()
        self._cache_col.update_one(
            {"session_key": session_key},
            {
                "$set": {
                    "summary": summary,
                    "msg_count": int(msg_count),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        logger.info(f"[Timer] Summary Cache Upsert: {(time.perf_counter() - t0):.3f}s")

    def load(self, session_key: str, *, max_messages: int) -> MemorySnapshot:
        t0 = time.perf_counter()

        t_hist = time.perf_counter()
        h = self._get_history(session_key)
        all_msgs = h.messages or []
        logger.info(
            f"[Timer] Memory History Load (Mongo): {(time.perf_counter() - t_hist):.3f}s | Msgs: {len(all_msgs)}"
        )

        recent = all_msgs[-max_messages:] if max_messages > 0 else []

        clean_cnt = len(self._clean(all_msgs))
        cached_summary, cached_cnt, _ = self._get_cached(session_key)
        logger.info(
            f"[Timer] Summary Cache Used: yes | cached_cnt={cached_cnt} | clean_cnt={clean_cnt} | has_summary={bool(cached_summary)}"
        )

        logger.info(
            f"[Timer] Memory Load Total (CacheOnly): {(time.perf_counter() - t0):.3f}s"
        )
        return MemorySnapshot(recent_messages=recent, summary=cached_summary)

    def load_recent_only(
        self, session_key: str, *, max_messages: int
    ) -> MemorySnapshot:
        t0 = time.perf_counter()

        h = self._get_history(session_key)
        all_msgs = h.messages or []
        recent = all_msgs[-max_messages:] if max_messages > 0 else []

        logger.info(
            f"[Timer] Memory Load Total (RecentOnly): {(time.perf_counter() - t0):.3f}s"
        )
        return MemorySnapshot(recent_messages=recent, summary="")

    def _summarize(self, messages: List[BaseMessage]) -> str:
        clean = self._clean(messages)
        if len(clean) < self.summary_trigger_threshold:
            return ""

        clean = clean[-self.max_summary_messages :]
        llm = self._get_llm(self.summary_model)

        # 把近期的對話內容拼接起來，用來偵測語言
        combined_text = " ".join([str(m.content) for m in clean])
        is_chinese = bool(re.search(r"[\u4e00-\u9fff]", combined_text))

        if is_chinese:
            system = (
                "你是專門為「知識問答檢索系統」服務的對話上下文摘要器。\n"
                "請用繁體中文將歷史對話濃縮成高度精煉的長期摘要。\n"
                "【摘要重點（絕對規則）】\n"
                "1. 核心實體（極重要）：必須明確保留對話中討論過的「專有名詞」、「產品名稱」、「系統代號」或「特定概念」。這是為了幫助後續系統還原代名詞（如：它、這個）。\n"
                "2. 討論脈絡：簡短總結使用者關心的主要面向（例如：詢問價格、比較規格、詢問缺點）。\n"
                "3. 排除雜訊：絕對不要記錄寒暄語、不要加標題、不要編造對話中未提及的資訊。\n"
                "請保持摘要極度簡短，以精煉的段落或條列式輸出即可。"
            )
        else:
            system = (
                "You are a conversation context summarizer specifically designed for a 'Knowledge Retrieval-Augmented Generation (RAG) System'.\n"
                "Please condense the conversation history into a highly refined long-term summary in English.\n"
                "[Summary Focus (Absolute Rules)]\n"
                "1. Core Entities (CRUCIAL): You MUST explicitly retain any 'proper nouns', 'product names', 'system codes', or 'specific concepts' discussed in the conversation. This is essential to help downstream systems resolve pronouns (e.g., it, this, they).\n"
                "2. Discussion Context: Briefly summarize the main aspects the user is inquiring about (e.g., asking for price, comparing specs, asking about drawbacks).\n"
                "3. Exclude Noise: ABSOLUTELY DO NOT record greetings/small talk, do not add titles, and do not invent information not mentioned in the conversation.\n"
                "Keep the summary extremely concise, outputting as a refined paragraph or bullet points."
            )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system),
            MessagesPlaceholder("chat_history"),
        ])

        final_messages = prompt.format_messages(chat_history=clean)

        try:
            response = llm.invoke(final_messages)
            content = getattr(response, "content", "")
            if not isinstance(content, str):
                content = str(content)
            return content.strip()
        except Exception as e:
            from app.logger import logger

            logger.error(f"[SummaryMemory] LLM invoke failed during summarize: {e}")
            return ""

    def maybe_update_summary(self, session_key: str, *, force: bool = False) -> bool:
        if not self._cache_enabled:
            return False

        t0 = time.perf_counter()

        h = self._get_history(session_key)
        all_msgs = h.messages or []
        clean_msgs = self._clean(all_msgs)
        clean_cnt = len(clean_msgs)

        if clean_cnt < self.summary_trigger_threshold:
            logger.info("[Summary BG] skipped: below threshold")
            return False

        cached_summary, cached_cnt, cached_updated_epoch = self._get_cached(session_key)

        now_epoch = datetime.now(timezone.utc).timestamp()
        too_soon = (
            (now_epoch - cached_updated_epoch) < self.refresh_min_interval_sec
            if cached_updated_epoch
            else False
        )
        delta = clean_cnt - int(cached_cnt or 0)

        need_update = (
            force or (not cached_summary) or (delta >= self.refresh_every_n_new_msgs)
        )
        if too_soon and not force:
            need_update = False

        logger.info(
            f"[Summary BG] decision need_update={need_update} | delta={delta} | too_soon={too_soon} | cached_cnt={cached_cnt} | clean_cnt={clean_cnt}"
        )

        if not need_update:
            logger.info(
                f"[Timer] Summary BG Total (NoUpdate): {(time.perf_counter() - t0):.3f}s"
            )
            return False

        try:
            summary = self._summarize(all_msgs)
        except Exception as e:
            logger.warning(f"[Summary BG] summarize failed: {e}")
            return False

        self._set_cached(session_key, summary, msg_count=clean_cnt)

        logger.info(
            f"[Timer] Summary BG Total (Updated): {(time.perf_counter() - t0):.3f}s"
        )
        return True
