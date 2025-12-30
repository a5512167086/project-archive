from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable, List, Optional, Tuple

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.logger import logger
from app.services.memory.base import MemorySnapshot
from app.services.memory.buffer import MongoBufferMemory

try:
    from pymongo import MongoClient
except Exception:  # pragma: no cover
    MongoClient = None  # type: ignore


class MongoSummaryMemory(MongoBufferMemory):
    """
    Summary is moved out of critical path:
    - load(): returns recent buffer + cached summary (no LLM)
    - maybe_update_summary(): compute summary via LLM and upsert cache (call in background)
    """

    DEFAULT_CACHE_SUFFIX = "_summary_cache"

    def __init__(
        self,
        mongo_uri: str,
        mongo_db_name: str,
        mongo_collection: str,
        get_llm: Callable[[str], Any],
        summary_model: str = "gpt_5_mini",
        summary_trigger_threshold: int = 6,
        max_summary_messages: int = 30,
        # refresh policy
        refresh_min_interval_sec: int = 60,
        refresh_every_n_new_msgs: int = 4,
        cache_collection: Optional[str] = None,
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

        self.refresh_min_interval_sec = int(refresh_min_interval_sec)
        self.refresh_every_n_new_msgs = int(refresh_every_n_new_msgs)

        self._cache_enabled = MongoClient is not None
        self._cache_col = None

        if self._cache_enabled:
            try:
                client = MongoClient(mongo_uri)
                col_name = cache_collection or (
                    mongo_collection + self.DEFAULT_CACHE_SUFFIX
                )
                self._cache_col = client[mongo_db_name][col_name]
                # recommended indexes (safe to call multiple times)
                self._cache_col.create_index("session_key", unique=True)
                self._cache_col.create_index("updated_at")
            except Exception as e:
                logger.warning(f"[MongoSummaryMemory] summary cache init failed: {e}")
                self._cache_enabled = False
                self._cache_col = None
        else:
            logger.warning(
                "[MongoSummaryMemory] pymongo not available; summary cache disabled."
            )

    # ---------------------
    # Helpers
    # ---------------------
    def _clean(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        return [m for m in messages if isinstance(m, (HumanMessage, AIMessage))]

    def _get_cached(self, session_key: str) -> Tuple[str, int, float]:
        """
        Returns: (summary, msg_count, updated_at_epoch)
        """
        if not self._cache_enabled or self._cache_col is None:
            return "", 0, 0.0

        t0 = time.perf_counter()
        doc = self._cache_col.find_one(
            {"session_key": session_key},
            {"summary": 1, "msg_count": 1, "updated_at": 1},
        )
        dur = time.perf_counter() - t0
        logger.info(f"[Timer] Summary Cache Read: {dur:.3f}s")

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
        dur = time.perf_counter() - t0
        logger.info(f"[Timer] Summary Cache Upsert: {dur:.3f}s")

    def _summarize(self, messages: List[BaseMessage]) -> str:
        """
        Heavy path (LLM). Do NOT call this in load().
        """
        t0 = time.perf_counter()

        clean = self._clean(messages)
        if len(clean) < self.summary_trigger_threshold:
            logger.info(
                f"[Timer] Summary Skipped (<threshold): {(time.perf_counter() - t0):.3f}s"
            )
            return ""

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

        t_fmt = time.perf_counter()
        final_messages = prompt.format_messages(chat_history=clean)
        fmt_dur = time.perf_counter() - t_fmt
        logger.info(
            f"[Timer] Summary Prompt Format: {fmt_dur:.3f}s | Msgs: {len(clean)}"
        )

        t_invoke = time.perf_counter()
        response = llm.invoke(final_messages)
        invoke_dur = time.perf_counter() - t_invoke
        logger.info(f"[Timer] Summary LLM Invoke: {invoke_dur:.3f}s")

        content = getattr(response, "content", "")
        if not isinstance(content, str):
            content = str(content)

        total = time.perf_counter() - t0
        logger.info(f"[Timer] Summary Total: {total:.3f}s")
        return content.strip()

    # ---------------------
    # Public APIs
    # ---------------------
    def load(self, session_key: str, max_messages: int) -> MemorySnapshot:
        """
        Critical path: load history + recent; summary is READ FROM CACHE ONLY.
        """
        t0 = time.perf_counter()

        # 1) Mongo 讀取歷史
        t_hist = time.perf_counter()
        h = self._get_history(session_key)
        all_msgs = h.messages or []
        hist_dur = time.perf_counter() - t_hist
        logger.info(
            f"[Timer] Memory History Load (Mongo): {hist_dur:.3f}s | Msgs: {len(all_msgs)}"
        )

        # 2) recent slice
        t_recent = time.perf_counter()
        recent = all_msgs[-max_messages:] if max_messages > 0 else []
        recent_dur = time.perf_counter() - t_recent
        logger.info(
            f"[Timer] Memory Recent Slice: {recent_dur:.3f}s | Recent: {len(recent)}"
        )

        # 3) summary from cache (fast)
        clean_cnt = len(self._clean(all_msgs))
        cached_summary, cached_cnt, _ = self._get_cached(session_key)

        logger.info(
            f"[Timer] Summary Cache Used: yes | cached_cnt={cached_cnt} | clean_cnt={clean_cnt} | has_summary={bool(cached_summary)}"
        )

        total = time.perf_counter() - t0
        logger.info(f"[Timer] Memory Load Total (CacheOnly): {total:.3f}s")

        return MemorySnapshot(recent_messages=recent, summary=cached_summary)

    def load_recent_only(self, session_key: str, max_messages: int) -> MemorySnapshot:
        """
        Optimization A: load recent messages only (no summary, no cache access needed).
        """
        t0 = time.perf_counter()

        t_hist = time.perf_counter()
        h = self._get_history(session_key)
        all_msgs = h.messages or []
        hist_dur = time.perf_counter() - t_hist
        logger.info(
            f"[Timer] Memory History Load (Mongo, RecentOnly): {hist_dur:.3f}s | Msgs: {len(all_msgs)}"
        )

        t_recent = time.perf_counter()
        recent = all_msgs[-max_messages:] if max_messages > 0 else []
        recent_dur = time.perf_counter() - t_recent
        logger.info(
            f"[Timer] Memory Recent Slice (RecentOnly): {recent_dur:.3f}s | Recent: {len(recent)}"
        )

        total = time.perf_counter() - t0
        logger.info(f"[Timer] Memory Load Total (RecentOnly): {total:.3f}s")

        return MemorySnapshot(recent_messages=recent, summary="")

    def maybe_update_summary(self, session_key: str, *, force: bool = False) -> bool:
        """
        Background task:
        - Checks cache freshness based on msg_count and updated_at.
        - If needed, computes summary via LLM and updates cache.
        Returns True if updated.
        """
        if not self._cache_enabled:
            return False

        t0 = time.perf_counter()

        # Read current history (cheap)
        t_hist = time.perf_counter()
        h = self._get_history(session_key)
        all_msgs = h.messages or []
        clean_msgs = self._clean(all_msgs)
        clean_cnt = len(clean_msgs)
        hist_dur = time.perf_counter() - t_hist
        logger.info(
            f"[Timer] Summary BG History Load: {hist_dur:.3f}s | CleanMsgs: {clean_cnt}"
        )

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

        need_update = force or (
            (not cached_summary) or (delta >= self.refresh_every_n_new_msgs)
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

        # Heavy path: LLM summarize
        summary = ""
        try:
            summary = self._summarize(all_msgs)
        except Exception as e:
            logger.warning(f"[Summary BG] summarize failed: {e}")
            return False

        self._set_cached(session_key, summary, msg_count=clean_cnt)

        total = time.perf_counter() - t0
        logger.info(f"[Timer] Summary BG Total (Updated): {total:.3f}s")
        return True
