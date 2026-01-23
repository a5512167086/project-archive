from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from langchain_core.messages import BaseMessage
from langchain_huggingface import ChatHuggingFace, HuggingFaceEmbeddings

from app.configs.constans import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_MAX_CONTEXTS_FOR_PROMPT,
    DEFAULT_MAX_HISTORY_MESSAGES,
    DEFAULT_MAX_HISTORY_ROUNDS,
    DEFAULT_RERANK_FACTOR,
    DEFAULT_SCORE_THRESHOLD,
    DEFAULT_TIMEOUT,
    DEFAULT_TOP_K,
)
from app.logger import logger
from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService
from app.services.reranker_service import RerankerService
from app.services.retrieval_service import RetrievalService
from app.services.rewrite_service import RewriteService
from app.services.summary_service import SummaryService


class RAGService:
    DEFAULT_TOP_K = DEFAULT_TOP_K
    DEFAULT_SCORE_THRESHOLD = DEFAULT_SCORE_THRESHOLD
    DEFAULT_TIMEOUT = DEFAULT_TIMEOUT
    DEFAULT_BATCH_SIZE = DEFAULT_BATCH_SIZE
    DEFAULT_MAX_HISTORY_ROUNDS = DEFAULT_MAX_HISTORY_ROUNDS
    DEFAULT_MAX_HISTORY_MESSAGES = DEFAULT_MAX_HISTORY_MESSAGES
    DEFAULT_MAX_CONTEXTS_FOR_PROMPT = DEFAULT_MAX_CONTEXTS_FOR_PROMPT
    DEFAULT_RERANK_FACTOR = DEFAULT_RERANK_FACTOR

    def __init__(
        self,
        embeddings: HuggingFaceEmbeddings,
        preloaded_hf_chat_model: Optional[ChatHuggingFace] = None,
        llm_service: Optional[LLMService] = None,
        prompt_service: Optional[PromptService] = None,
        reranker_service: Optional[RerankerService] = None,
        retrieval_service: Optional[RetrievalService] = None,
        summary_service: Optional[SummaryService] = None,
        rewrite_service: Optional[RewriteService] = None,
        memory: Optional[Any] = None,
    ) -> None:
        self.embeddings = embeddings
        self.llm_service: LLMService = llm_service or LLMService(
            preloaded_hf_chat_model=preloaded_hf_chat_model
        )
        self.prompt_service: PromptService = prompt_service or PromptService(
            max_contexts_for_prompt=self.DEFAULT_MAX_CONTEXTS_FOR_PROMPT
        )
        self.reranker = reranker_service
        self.retrieval_service = retrieval_service
        self.summary_service: SummaryService = summary_service
        self.memory = memory
        self.rewrite_service: RewriteService = rewrite_service or RewriteService(
            get_llm=self.llm_service.get_llm,
            snapshot_loader=self.summary_service,
            use_summary=True,
        )

    def _build_session_key(self, bot_uuid: UUID, line_id: str) -> str:
        return f"{str(bot_uuid)}:{line_id}"

    def search(
        self,
        bot_uuid: UUID,
        query_text: str,
        top_k: int = 3,
        fetch_k: Optional[int] = None,
        score_threshold: Optional[float] = DEFAULT_SCORE_THRESHOLD,
        rerank_threshold: Optional[float] = None,
        retrieval_mode: str = "hybrid",
        use_rerank: bool = True,
    ) -> List[Dict[str, Any]]:
        mode = (retrieval_mode or "hybrid").lower().strip()
        if mode not in {"vector", "lexical", "hybrid"}:
            mode = "hybrid"

        if self.retrieval_service is None:
            raise RuntimeError("retrieval_service is required for RAGService.search().")

        if fetch_k is not None:
            initial_k = int(fetch_k)
        elif self.reranker and use_rerank:
            initial_k = int(top_k) * self.DEFAULT_RERANK_FACTOR
        else:
            initial_k = int(top_k)

        if score_threshold is None:
            initial_threshold = None
        else:
            initial_threshold = max(float(score_threshold) - 0.1, 0.0)

        logger.info(
            f"[RAGService] Step 1: Retrieval(mode={mode}) searching top {initial_k} candidates..."
        )
        hits = self.retrieval_service.search(
            bot_uuid=bot_uuid,
            query_text=query_text,
            top_k=initial_k,
            fetch_k=initial_k,
            score_threshold=initial_threshold,
            mode=mode,
        )

        if hits:
            logger.info(f"--- [Step 1 Result] Retrieved {len(hits)} items ---")
            for i, h in enumerate(hits):
                q_snippet = (h.get("question", "") or "")[:30]
                s = h.get("score", None)
                try:
                    s_fmt = f"{float(s):.4f}" if s is not None else "NA"
                except Exception:
                    s_fmt = "NA"
                logger.info(
                    f"  #{i + 1} Score: {s_fmt} | ID: {h.get('object_id')} | Q: {q_snippet}..."
                )
        else:
            logger.info("--- [Step 1 Result] Retrieved NO items ---")

        if not hits or not self.reranker or (not use_rerank):
            return hits[: int(top_k)]

        logger.info(
            f"[RAGService] Step 2: Reranking {len(hits)} hits -> Top {top_k}..."
        )

        reranked_hits = self.reranker.rerank(
            query=query_text,
            docs=hits,
            top_k=int(top_k),
        )

        if rerank_threshold is not None:
            kept_hits: List[Dict[str, Any]] = []
            dropped_hits: List[Dict[str, Any]] = []

            thr = float(rerank_threshold)
            for h in reranked_hits:
                score = float(h.get("rerank_score", 0.0) or 0.0)
                if score >= thr:
                    kept_hits.append(h)
                else:
                    dropped_hits.append(h)

            reranked_hits = kept_hits

            if dropped_hits:
                logger.info(
                    f"--- [Rerank Filter] Dropped {len(dropped_hits)} items (Score < {thr}) ---"
                )
                for h in dropped_hits:
                    q_snippet = (h.get("question", "") or "")[:30]
                    logger.info(
                        f"  [DROPPED] Score: {float(h.get('rerank_score', 0.0) or 0.0):.4f} "
                        f"| ID: {h.get('object_id')} | Q: {q_snippet}..."
                    )
            else:
                logger.info(f"[Rerank Filter] No items dropped (all >= {thr}).")

        if reranked_hits:
            logger.info(
                f"--- [Step 2 Result] After Reranking & Filtering (Top {len(reranked_hits)}) ---"
            )
            for i, h in enumerate(reranked_hits):
                q_snippet = (h.get("question", "") or "")[:30]
                logger.info(
                    f"  #{i + 1} RerankScore: {float(h.get('rerank_score', 0.0) or 0.0):.4f} "
                    f"| ID: {h.get('object_id')} | Q: {q_snippet}..."
                )
        else:
            logger.info(
                "--- [Step 2 Result] Final list is EMPTY (all filtered out) ---"
            )

        return reranked_hits

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
        use_rewrite: bool = True,
        use_summary_in_rewrite: bool = True,
        retrieval_mode: str = "hybrid",
        use_rerank: bool = True,
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
                retrieval_mode=retrieval_mode,
                use_rerank=use_rerank,
            )
            logger.info(
                f"[Timer] SearchHistoryAware Total (SingleTurn): {(time.perf_counter() - t0):.3f}s"
            )
            return query_text, hits

        session_key = self._build_session_key(bot_uuid, line_id)
        final_query = query_text

        if use_rewrite:
            if self.summary_service is None:
                logger.warning(
                    "[RAGService] summary_service is None; rewrite_with_snapshot will run without snapshot."
                )

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
                use_summary=bool(use_summary_in_rewrite),
            )
            logger.info(
                f"[Timer] Query Rewrite (Wrapper): {(time.perf_counter() - t_rewrite):.3f}s"
            )

            final_query = (rr.rewritten or "").strip() or query_text
            logger.info(
                f"[RAGService] rewritten_query='{final_query}' from '{query_text}'"
            )
        else:
            logger.info("[RAGService] rewrite disabled for this request.")

        t_search = time.perf_counter()
        hits = self.search(
            bot_uuid=bot_uuid,
            query_text=final_query,
            top_k=top_k,
            fetch_k=fetch_k,
            score_threshold=score_threshold,
            rerank_threshold=rerank_threshold,
            retrieval_mode=retrieval_mode,
            use_rerank=use_rerank,
        )
        logger.info(
            f"[Timer] Retrieval Search (Wrapper): {(time.perf_counter() - t_search):.3f}s | Hits: {len(hits)}"
        )

        logger.info(
            f"[Timer] SearchHistoryAware Total: {(time.perf_counter() - t0):.3f}s"
        )
        return final_query, hits

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
            if self.summary_service is None:
                logger.warning(
                    "[RAGService] summary_service is None; cannot load recent messages."
                )
            else:
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
        use_rewrite: bool = True,
        use_summary_in_rewrite: bool = True,
        retrieval_mode: str = "hybrid",
        use_rerank: bool = True,
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
            use_rewrite=use_rewrite,
            use_summary_in_rewrite=use_summary_in_rewrite,
            retrieval_mode=retrieval_mode,
            use_rerank=use_rerank,
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
