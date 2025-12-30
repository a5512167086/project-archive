from __future__ import annotations

import time
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from uuid import UUID

from langchain_core.messages import BaseMessage
from langchain_huggingface import ChatHuggingFace, HuggingFaceEmbeddings

from app.configs.config import (
    MONGODB_CHAT_COLLECTION,
    MONGODB_DB_NAME,
    MONGODB_URI,
    QDRANT_COLLECTION,
    QDRANT_URL,
)
from app.logger import logger
from app.schemas import KnowledgeItem
from app.services.llm_service import LLMService
from app.services.memory.base import MemoryModule
from app.services.memory.buffer import BufferMemory
from app.services.memory.rewriter import QueryRewriter
from app.services.prompt_service import PromptService
from app.services.vector_service import VectorService


class RAGService:
    DEFAULT_TOP_K = 5
    DEFAULT_SCORE_THRESHOLD = 0.7
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_BATCH_SIZE = 250

    # Memory behavior
    DEFAULT_MAX_HISTORY_ROUNDS = 5  # keep last 5 rounds
    DEFAULT_MAX_HISTORY_MESSAGES = 10  # 5 rounds = 10 messages (Human+AI)
    DEFAULT_MAX_CONTEXTS_FOR_PROMPT = 3

    def __init__(
        self,
        *,
        embeddings: HuggingFaceEmbeddings,
        preloaded_hf_chat_model: Optional[ChatHuggingFace] = None,
        qdrant_url: str = QDRANT_URL,
        collection_name: str = QDRANT_COLLECTION,
        timeout: float = DEFAULT_TIMEOUT,
        ensure_collection_and_indexes: bool = True,
        # MongoDB (default memory)
        mongo_uri: str = MONGODB_URI,
        mongo_db_name: str = MONGODB_DB_NAME,
        mongo_collection: str = MONGODB_CHAT_COLLECTION,
        # Pluggable modules
        memory: Optional[MemoryModule] = None,
        rewriter: Optional[QueryRewriter] = None,
        # Extracted services (optional injection)
        llm_service: Optional[LLMService] = None,
        prompt_service: Optional[PromptService] = None,
        vector_service: Optional[VectorService] = None,
    ) -> None:
        self.embeddings = embeddings

        # ---- extracted services ----
        self.llm_service: LLMService = llm_service or LLMService(
            preloaded_hf_chat_model=preloaded_hf_chat_model
        )

        self.prompt_service: PromptService = prompt_service or PromptService(
            max_contexts_for_prompt=self.DEFAULT_MAX_CONTEXTS_FOR_PROMPT
        )

        self.vector_service: VectorService = vector_service or VectorService(
            embeddings=embeddings,
            qdrant_url=qdrant_url,
            collection_name=collection_name,
            timeout=timeout,
            ensure_collection_and_indexes=ensure_collection_and_indexes,
        )

        # ---- memory / rewriter ----
        self.mongo_uri = mongo_uri
        self.mongo_db_name = mongo_db_name
        self.mongo_collection = mongo_collection

        self.memory: MemoryModule = memory or BufferMemory(
            mongo_uri=mongo_uri,
            mongo_db_name=mongo_db_name,
            mongo_collection=mongo_collection,
        )

        self.rewriter: QueryRewriter = rewriter or QueryRewriter(
            self.llm_service.get_llm
        )

    # =====================
    # Session Key
    # =====================
    def _build_session_key(self, bot_uuid: UUID, line_id: str) -> str:
        return f"{str(bot_uuid)}:{line_id}"

    # =====================
    # Vector wrappers (compatibility)
    # =====================
    def get_object_ids_by_bot_uuid(
        self, bot_uuid: UUID, batch_size: int = DEFAULT_BATCH_SIZE
    ) -> Set[int]:
        return self.vector_service.get_object_ids_by_bot_uuid(
            bot_uuid=bot_uuid, batch_size=batch_size
        )

    def upsert_knowledge_items(
        self, bot_uuid: UUID, items: Iterable[KnowledgeItem]
    ) -> int:
        return self.vector_service.upsert_knowledge_items(
            bot_uuid=bot_uuid, items=items
        )

    def delete_knowledge_items(
        self, bot_uuid: UUID, object_ids: Optional[List[int]] = None
    ) -> bool:
        return self.vector_service.delete_knowledge_items(
            bot_uuid=bot_uuid, object_ids=object_ids
        )

    def search(
        self,
        bot_uuid: UUID,
        query_text: str,
        top_k: int = DEFAULT_TOP_K,
        score_threshold: Optional[float] = DEFAULT_SCORE_THRESHOLD,
    ) -> List[Dict[str, Any]]:
        return self.vector_service.search(
            bot_uuid=bot_uuid,
            query_text=query_text,
            top_k=top_k,
            score_threshold=score_threshold,
        )

    # =====================
    # History-aware search
    # =====================
    def search_history_aware(
        self,
        bot_uuid: UUID,
        line_id: Optional[str],
        query_text: str,
        top_k: int = DEFAULT_TOP_K,
        score_threshold: Optional[float] = DEFAULT_SCORE_THRESHOLD,
        history_rounds: int = DEFAULT_MAX_HISTORY_ROUNDS,
        rewrite_model: str = "gpt_5_mini",
    ) -> Tuple[str, List[Dict[str, Any]]]:
        t0 = time.perf_counter()

        # single-turn：不 rewrite、不讀 memory
        if not line_id:
            hits = self.search(
                bot_uuid=bot_uuid,
                query_text=query_text,
                top_k=top_k,
                score_threshold=score_threshold,
            )
            logger.info(
                f"[Timer] SearchHistoryAware Total (SingleTurn): {(time.perf_counter() - t0):.3f}s"
            )
            return query_text, hits

        session_key = self._build_session_key(bot_uuid, line_id)

        # 1) memory load (may include cached summary)
        t_mem = time.perf_counter()
        snapshot = self.memory.load(
            session_key, max_messages=max(0, history_rounds * 2)
        )
        mem_dur = time.perf_counter() - t_mem
        logger.info(f"[Timer] Memory Load (Summary Included): {mem_dur:.3f}s")

        if snapshot.summary:
            logger.info(
                f"[RAGService] conversation_summary(session={session_key}): {snapshot.summary}"
            )

        # 2) rewrite
        t_rewrite = time.perf_counter()
        rr = self.rewriter.rewrite(
            user_query=query_text,
            snapshot=snapshot,
            rewrite_model=rewrite_model,
        )
        rewrite_dur = time.perf_counter() - t_rewrite
        logger.info(f"[Timer] Query Rewrite (Wrapper): {rewrite_dur:.3f}s")

        final_query = (rr.rewritten or "").strip() or query_text
        logger.info(f"[RAGService] rewritten_query='{final_query}' from '{query_text}'")

        # 3) vector search
        t_search = time.perf_counter()
        hits = self.search(
            bot_uuid=bot_uuid,
            query_text=final_query,
            top_k=top_k,
            score_threshold=score_threshold,
        )
        search_dur = time.perf_counter() - t_search
        logger.info(
            f"[Timer] Vector Search (Wrapper): {search_dur:.3f}s | Hits: {len(hits)}"
        )

        total = time.perf_counter() - t0
        logger.info(f"[Timer] SearchHistoryAware Total: {total:.3f}s")

        return final_query, hits

    # =====================
    # Generate
    # =====================
    def generate(
        self,
        bot_uuid: UUID,
        line_id: Optional[str],
        original_query: str,
        rewritten_query: str,
        contexts: List[Dict[str, Any]],
        model_name: str,
        max_history_messages: int = DEFAULT_MAX_HISTORY_MESSAGES,
    ) -> str:
        t0 = time.perf_counter()

        llm = self.llm_service.get_llm(model_name)
        use_memory = bool(line_id)

        history: Optional[List[BaseMessage]] = None
        session_key: Optional[str] = None

        # 1) memory load for generation history
        # IMPORTANT: if memory provides load_recent_only, prefer it (avoid summary path)
        if use_memory and line_id:
            session_key = self._build_session_key(bot_uuid, line_id)

            t_mem = time.perf_counter()
            if hasattr(self.memory, "load_recent_only"):
                snapshot = self.memory.load_recent_only(
                    session_key, max_messages=max_history_messages
                )
                mem_dur = time.perf_counter() - t_mem
                logger.info(
                    f"[Timer] Generate Memory Load (RecentOnly): {mem_dur:.3f}s | Hist: {len(snapshot.recent_messages)}"
                )
            else:
                snapshot = self.memory.load(
                    session_key, max_messages=max_history_messages
                )
                mem_dur = time.perf_counter() - t_mem
                logger.info(
                    f"[Timer] Generate Memory Load: {mem_dur:.3f}s | Hist: {len(snapshot.recent_messages)}"
                )

            history = snapshot.recent_messages

        # 2) build prompt
        t_prompt = time.perf_counter()
        messages = self.prompt_service.build_messages(
            original_query=original_query,
            rewritten_query=rewritten_query,
            contexts=contexts,
            use_no_think=(model_name == "qwen3_local"),
            history=history,
        )
        prompt_dur = time.perf_counter() - t_prompt
        logger.info(
            f"[Timer] Generate Build Prompt: {prompt_dur:.3f}s | Msgs: {len(messages)}"
        )

        # 3) invoke
        t_inv = time.perf_counter()
        try:
            resp = llm.invoke(messages)
        except Exception as e:
            logger.exception(f"[RAGService] LLM invoke failed: {e}")
            return "系統目前無法產生回覆，請稍後再試。"
        inv_dur = time.perf_counter() - t_inv
        logger.info(f"[Timer] Answer Generation (LLM): {inv_dur:.3f}s")

        # 4) parse output
        t_parse = time.perf_counter()
        text = getattr(resp, "content", None) if hasattr(resp, "content") else None
        if not isinstance(text, str) or not text:
            text = getattr(resp, "text", None) if hasattr(resp, "text") else None
        if not isinstance(text, str) or not text:
            text = str(resp)

        if model_name == "qwen3_local":
            text = self.prompt_service.clean_hf_output(text)

        answer = (text or "").strip()
        parse_dur = time.perf_counter() - t_parse
        logger.info(f"[Timer] Generate Parse Output: {parse_dur:.3f}s")

        # 5) append turn
        if use_memory and session_key:
            t_app = time.perf_counter()
            self.memory.append_turn(session_key, human=original_query, ai=answer)
            app_dur = time.perf_counter() - t_app
            logger.info(f"[Timer] Generate Append Turn: {app_dur:.3f}s")

        total = time.perf_counter() - t0
        logger.info(f"[Timer] Generate Total: {total:.3f}s")

        return answer

    # =====================
    # One-shot Use Case
    # =====================
    def answer(
        self,
        *,
        bot_uuid: UUID,
        line_id: Optional[str],
        query_text: str,
        model_name: str,
        top_k: int = DEFAULT_TOP_K,
        score_threshold: Optional[float] = DEFAULT_SCORE_THRESHOLD,
        history_rounds: int = DEFAULT_MAX_HISTORY_ROUNDS,
        rewrite_model: str = "gpt_5_mini",
        max_history_messages: int = DEFAULT_MAX_HISTORY_MESSAGES,
    ) -> Dict[str, Any]:
        rewritten, hits = self.search_history_aware(
            bot_uuid=bot_uuid,
            line_id=line_id,
            query_text=query_text,
            top_k=top_k,
            score_threshold=score_threshold,
            history_rounds=history_rounds,
            rewrite_model=rewrite_model,
        )

        ans = self.generate(
            bot_uuid=bot_uuid,
            line_id=line_id,
            original_query=query_text,
            rewritten_query=rewritten,
            contexts=hits,
            model_name=model_name,
            max_history_messages=max_history_messages,
        )

        return {
            "rewritten_query": rewritten,
            "hits": hits,
            "answer": ans,
        }
