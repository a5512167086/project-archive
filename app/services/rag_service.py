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
from app.services.reranker_service import RerankerService
from app.services.vector_service import VectorService


class RAGService:
    DEFAULT_TOP_K = 5
    DEFAULT_SCORE_THRESHOLD = 0.7
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_BATCH_SIZE = 250
    DEFAULT_MAX_HISTORY_ROUNDS = 5
    DEFAULT_MAX_HISTORY_MESSAGES = 10
    DEFAULT_MAX_CONTEXTS_FOR_PROMPT = 3
    DEFAULT_RERANK_FACTOR = 4  # 如果沒有指定 fetch_k，預設抓取 4 倍數量

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
        reranker_service: Optional[RerankerService] = None,
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
        self.reranker = reranker_service

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

    # =====================
    # Search (核心修改：詳細 Log 被過濾的項目)
    # =====================
    def search(
        self,
        bot_uuid: UUID,
        query_text: str,
        top_k: int = 3,  # 最後只留 3 筆 (預設)
        fetch_k: Optional[int] = None,  # 第一階段抓取數量
        score_threshold: Optional[float] = DEFAULT_SCORE_THRESHOLD,  # Vector 門檻
        rerank_threshold: Optional[float] = None,  # Rerank 門檻
    ) -> List[Dict[str, Any]]:

        # 1. 決定第一階段抓取數量 (initial_k)
        if fetch_k is not None:
            initial_k = fetch_k
        elif self.reranker:
            initial_k = top_k * self.DEFAULT_RERANK_FACTOR
        else:
            initial_k = top_k

        # 稍微放寬向量檢索的閾值，確保 Recall
        initial_threshold = (score_threshold - 0.1) if score_threshold else None

        logger.info(
            f"[RAGService] Step 1: Vector searching top {initial_k} candidates..."
        )

        hits = self.vector_service.search(
            bot_uuid=bot_uuid,
            query_text=query_text,
            top_k=initial_k,
            score_threshold=initial_threshold,
        )

        # --- LOGGING: 初始檢索結果 ---
        if hits:
            logger.info(
                f"--- [Step 1 Result] Vector Search found {len(hits)} items ---"
            )
            for i, h in enumerate(hits):
                q_snippet = (h.get("question", "") or "")[:30]
                logger.info(
                    f"  #{i + 1} Score: {h.get('score', 0.0):.4f} | ID: {h.get('object_id')} | Q: {q_snippet}..."
                )
        else:
            logger.info("--- [Step 1 Result] Vector Search found NO items ---")

        # 如果沒有抓到資料，或沒有設定 reranker，直接回傳
        if not hits or not self.reranker:
            return hits[:top_k]

        logger.info(
            f"[RAGService] Step 2: Reranking {len(hits)} hits -> Top {top_k}..."
        )

        # 2. Rerank 重排序
        reranked_hits = self.reranker.rerank(
            query=query_text,
            docs=hits,
            top_k=top_k,
        )

        # 3. Rerank 門檻過濾 (詳細 Log 版)
        if rerank_threshold is not None:
            kept_hits = []
            dropped_hits = []

            for h in reranked_hits:
                score = h.get("rerank_score", 0.0)
                if score >= rerank_threshold:
                    kept_hits.append(h)
                else:
                    dropped_hits.append(h)

            # 更新結果為保留的項目
            reranked_hits = kept_hits

            # Log 被丟棄的項目
            if dropped_hits:
                logger.info(
                    f"--- [Rerank Filter] Dropped {len(dropped_hits)} items (Score < {rerank_threshold}) ---"
                )
                for i, h in enumerate(dropped_hits):
                    q_snippet = (h.get("question", "") or "")[:30]
                    logger.info(
                        f"  [DROPPED] Score: {h.get('rerank_score', 0.0):.4f} | ID: {h.get('object_id')} | Q: {q_snippet}..."
                    )
            else:
                logger.info(
                    f"[Rerank Filter] No items dropped (all >= {rerank_threshold})."
                )

        # --- LOGGING: 最終保留結果 ---
        if reranked_hits:
            logger.info(
                f"--- [Step 2 Result] After Reranking & Filtering (Top {len(reranked_hits)}) ---"
            )
            for i, h in enumerate(reranked_hits):
                q_snippet = (h.get("question", "") or "")[:30]
                logger.info(
                    f"  #{i + 1} RerankScore: {h.get('rerank_score', 0.0):.4f} | ID: {h.get('object_id')} | Q: {q_snippet}..."
                )
        else:
            logger.info(
                "--- [Step 2 Result] Final list is EMPTY (all filtered out) ---"
            )

        return reranked_hits

    # =====================
    # History-aware search
    # =====================
    def search_history_aware(
        self,
        bot_uuid: UUID,
        line_id: Optional[str],
        query_text: str,
        top_k: int = DEFAULT_TOP_K,
        fetch_k: Optional[int] = None,
        score_threshold: Optional[float] = DEFAULT_SCORE_THRESHOLD,
        rerank_threshold: Optional[float] = None,
        history_rounds: int = DEFAULT_MAX_HISTORY_ROUNDS,
        rewrite_model: str = "gpt_5_mini",
    ) -> Tuple[str, List[Dict[str, Any]]]:
        t0 = time.perf_counter()

        # single-turn
        if not line_id:
            hits = self.search(
                bot_uuid=bot_uuid,
                query_text=query_text,
                top_k=top_k,
                fetch_k=fetch_k,
                score_threshold=score_threshold,
                rerank_threshold=rerank_threshold,
            )
            logger.info(
                f"[Timer] SearchHistoryAware Total (SingleTurn): {(time.perf_counter() - t0):.3f}s"
            )
            return query_text, hits

        session_key = self._build_session_key(bot_uuid, line_id)

        # 1) memory load
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
            fetch_k=fetch_k,
            score_threshold=score_threshold,
            rerank_threshold=rerank_threshold,
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
        if use_memory and line_id:
            session_key = self._build_session_key(bot_uuid, line_id)

            t_mem = time.perf_counter()
            if hasattr(self.memory, "load_recent_only"):
                snapshot = self.memory.load_recent_only(
                    session_key, max_messages=max_history_messages
                )
            else:
                snapshot = self.memory.load(
                    session_key, max_messages=max_history_messages
                )
            mem_dur = time.perf_counter() - t_mem
            logger.info(f"[Timer] Generate Memory Load: {mem_dur:.3f}s")

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
        text = getattr(resp, "content", None) if hasattr(resp, "content") else None
        if not isinstance(text, str) or not text:
            text = getattr(resp, "text", None) if hasattr(resp, "text") else None
        if not isinstance(text, str) or not text:
            text = str(resp)

        if model_name == "qwen3_local":
            text = self.prompt_service.clean_hf_output(text)

        answer = (text or "").strip()

        # 5) append turn
        if use_memory and session_key:
            self.memory.append_turn(session_key, human=original_query, ai=answer)

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
        fetch_k: Optional[int] = None,
        score_threshold: Optional[float] = DEFAULT_SCORE_THRESHOLD,
        rerank_threshold: Optional[float] = None,
        history_rounds: int = DEFAULT_MAX_HISTORY_ROUNDS,
        rewrite_model: str = "gpt_5_mini",
        max_history_messages: int = DEFAULT_MAX_HISTORY_MESSAGES,
    ) -> Dict[str, Any]:

        rewritten, hits = self.search_history_aware(
            bot_uuid=bot_uuid,
            line_id=line_id,
            query_text=query_text,
            top_k=top_k,
            fetch_k=fetch_k,
            score_threshold=score_threshold,
            rerank_threshold=rerank_threshold,
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
