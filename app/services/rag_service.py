# app/services/rag_service.py
from __future__ import annotations

import time
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from uuid import UUID

from langchain_core.messages import BaseMessage
from langchain_huggingface import ChatHuggingFace, HuggingFaceEmbeddings

from app.configs.config import QDRANT_COLLECTION, QDRANT_URL
from app.logger import logger
from app.schemas import KnowledgeItem
from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService
from app.services.reranker_service import RerankerService
from app.services.rewrite_service import RewriteService
from app.services.summary_service import SummaryService
from app.services.vector_service import VectorService


class RAGService:
    DEFAULT_TOP_K = 5
    DEFAULT_SCORE_THRESHOLD = 0.7
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_BATCH_SIZE = 250
    DEFAULT_MAX_HISTORY_ROUNDS = 5
    DEFAULT_MAX_HISTORY_MESSAGES = 10
    DEFAULT_MAX_CONTEXTS_FOR_PROMPT = 3
    DEFAULT_RERANK_FACTOR = 4

    def __init__(
        self,
        embeddings: HuggingFaceEmbeddings,
        preloaded_hf_chat_model: Optional[ChatHuggingFace] = None,
        qdrant_url: str = QDRANT_URL,
        collection_name: str = QDRANT_COLLECTION,
        timeout: float = DEFAULT_TIMEOUT,
        ensure_collection_and_indexes: bool = True,
        llm_service: Optional[LLMService] = None,
        prompt_service: Optional[PromptService] = None,
        vector_service: Optional[VectorService] = None,
        reranker_service: Optional[RerankerService] = None,
        summary_service: Optional[SummaryService] = None,
        rewrite_service: Optional[RewriteService] = None,
        memory: Optional[Any] = None,
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

        self.reranker = reranker_service

        # ---- required facade services ----
        if summary_service is None:
            raise ValueError("summary_service is required (no default memory module).")
        self.summary_service: SummaryService = summary_service

        # ---- persistence memory (append_turn) ----
        self.memory = memory

        # ---- rewrite service ----
        self.rewrite_service: RewriteService = rewrite_service or RewriteService(
            get_llm=self.llm_service.get_llm,
            snapshot_loader=self.summary_service,
            use_summary=True,
        )

    # =====================
    # Session Key
    # =====================
    def _build_session_key(self, bot_uuid: UUID, line_id: str) -> str:
        return f"{str(bot_uuid)}:{line_id}"

    # =====================
    # Vector wrappers
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
    # Search
    # =====================
    def search(
        self,
        bot_uuid: UUID,
        query_text: str,
        top_k: int = 3,
        fetch_k: Optional[int] = None,
        score_threshold: Optional[float] = DEFAULT_SCORE_THRESHOLD,
        rerank_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:

        if fetch_k is not None:
            initial_k = fetch_k
        elif self.reranker:
            initial_k = top_k * self.DEFAULT_RERANK_FACTOR
        else:
            initial_k = top_k

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

        if not hits or not self.reranker:
            return hits[:top_k]

        logger.info(
            f"[RAGService] Step 2: Reranking {len(hits)} hits -> Top {top_k}..."
        )

        reranked_hits = self.reranker.rerank(
            query=query_text,
            docs=hits,
            top_k=top_k,
        )

        if rerank_threshold is not None:
            kept_hits = []
            dropped_hits = []

            for h in reranked_hits:
                score = h.get("rerank_score", 0.0)
                if score >= rerank_threshold:
                    kept_hits.append(h)
                else:
                    dropped_hits.append(h)

            reranked_hits = kept_hits

            if dropped_hits:
                logger.info(
                    f"--- [Rerank Filter] Dropped {len(dropped_hits)} items (Score < {rerank_threshold}) ---"
                )
                for h in dropped_hits:
                    q_snippet = (h.get("question", "") or "")[:30]
                    logger.info(
                        f"  [DROPPED] Score: {h.get('rerank_score', 0.0):.4f} | ID: {h.get('object_id')} | Q: {q_snippet}..."
                    )
            else:
                logger.info(
                    f"[Rerank Filter] No items dropped (all >= {rerank_threshold})."
                )

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

        t_mem = time.perf_counter()
        snapshot = self.summary_service.load(
            session_key, max_messages=max(0, history_rounds * 2)
        )
        logger.info(
            f"[Timer] Memory Load (Summary Included): {(time.perf_counter() - t_mem):.3f}s"
        )

        if snapshot.summary:
            logger.info(
                f"[RAGService] conversation_summary(session={session_key}): {snapshot.summary}"
            )

        t_rewrite = time.perf_counter()
        rr = self.rewrite_service.rewrite_with_snapshot(
            user_query=query_text,
            snapshot=snapshot,
            rewrite_model=rewrite_model,
        )
        logger.info(
            f"[Timer] Query Rewrite (Wrapper): {(time.perf_counter() - t_rewrite):.3f}s"
        )

        final_query = (rr.rewritten or "").strip() or query_text
        logger.info(f"[RAGService] rewritten_query='{final_query}' from '{query_text}'")

        t_search = time.perf_counter()
        hits = self.search(
            bot_uuid=bot_uuid,
            query_text=final_query,
            top_k=top_k,
            fetch_k=fetch_k,
            score_threshold=score_threshold,
            rerank_threshold=rerank_threshold,
        )
        logger.info(
            f"[Timer] Vector Search (Wrapper): {(time.perf_counter() - t_search):.3f}s | Hits: {len(hits)}"
        )

        logger.info(
            f"[Timer] SearchHistoryAware Total: {(time.perf_counter() - t0):.3f}s"
        )
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

        if use_memory and line_id:
            session_key = self._build_session_key(bot_uuid, line_id)

            t_mem = time.perf_counter()
            snapshot = self.summary_service.load_recent_only(
                session_key, max_messages=max_history_messages
            )
            logger.info(
                f"[Timer] Generate Memory Load: {(time.perf_counter() - t_mem):.3f}s"
            )
            history = snapshot.recent_messages

        t_prompt = time.perf_counter()
        messages = self.prompt_service.build_messages(
            original_query=original_query,
            rewritten_query=rewritten_query,
            contexts=contexts,
            use_no_think=(model_name == "qwen3_local"),
            history=history,
        )
        logger.info(
            f"[Timer] Generate Build Prompt: {(time.perf_counter() - t_prompt):.3f}s | Msgs: {len(messages)}"
        )

        t_inv = time.perf_counter()
        try:
            resp = llm.invoke(messages)
        except Exception as e:
            logger.exception(f"[RAGService] LLM invoke failed: {e}")
            return "系統目前無法產生回覆，請稍後再試。"
        logger.info(
            f"[Timer] Answer Generation (LLM): {(time.perf_counter() - t_inv):.3f}s"
        )

        text = getattr(resp, "content", None) if hasattr(resp, "content") else None
        if not isinstance(text, str) or not text:
            text = getattr(resp, "text", None) if hasattr(resp, "text") else None
        if not isinstance(text, str) or not text:
            text = str(resp)

        if model_name == "qwen3_local":
            text = self.prompt_service.clean_hf_output(text)

        answer = (text or "").strip()

        # ---- persistence append_turn ----
        if use_memory and session_key:
            if self.memory is not None and hasattr(self.memory, "append_turn"):
                try:
                    self.memory.append_turn(
                        session_key, human=original_query, ai=answer
                    )
                except Exception as e:
                    logger.warning(f"[RAGService] memory.append_turn failed: {e}")
            else:
                logger.warning(
                    "[RAGService] No persistence memory injected (append_turn skipped)."
                )

        logger.info(f"[Timer] Generate Total: {(time.perf_counter() - t0):.3f}s")
        return answer

    # =====================
    # One-shot Use Case
    # =====================
    def answer(
        self,
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
