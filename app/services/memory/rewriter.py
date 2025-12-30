from __future__ import annotations

import time
from typing import Any, Callable, List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.logger import logger
from app.services.memory.base import MemorySnapshot, QueryRewriter, RewriteResult


class HistoryQueryRewriter(QueryRewriter):
    """
    Uses recent chat history (and optionally summary from snapshot) to rewrite
    the latest user query into a standalone question.
    """

    def __init__(
        self,
        get_llm: Callable[[str], Any],
        *,
        use_summary: bool = True,
    ) -> None:
        self.get_llm = get_llm
        self.use_summary = use_summary

    def rewrite(
        self, user_query: str, snapshot: MemorySnapshot, rewrite_model: str
    ) -> RewriteResult:
        t0 = time.perf_counter()

        # 1) get llm
        t_llm = time.perf_counter()
        llm = self.get_llm(rewrite_model)
        llm_dur = time.perf_counter() - t_llm
        logger.info(f"[Timer] Rewrite Get LLM: {llm_dur:.3f}s")

        # 2) clean history
        t_clean = time.perf_counter()
        clean_history: List[BaseMessage] = [
            m
            for m in snapshot.recent_messages
            if isinstance(m, (HumanMessage, AIMessage))
        ]
        clean_dur = time.perf_counter() - t_clean
        logger.info(
            f"[Timer] Rewrite Clean History: {clean_dur:.3f}s | Used: {len(clean_history)}"
        )

        summary_context = ""
        used_summary = False
        if self.use_summary and (snapshot.summary or "").strip():
            used_summary = True
            summary_context = f"【長期對話摘要】：{snapshot.summary.strip()}\n"

        system_prompt = (
            "你是一個對話上下文解析器。"
            f"{summary_context}"
            "請把「最新使用者問題」改寫成「完整、可獨立理解」的問題。"
            "只輸出改寫後的問題，不要回答。"
            "輸出必須使用繁體中文，不得使用簡體中文。"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

        # 3) format messages
        t_fmt = time.perf_counter()
        messages = prompt.format_messages(input=user_query, chat_history=clean_history)
        fmt_dur = time.perf_counter() - t_fmt
        logger.info(f"[Timer] Rewrite Prompt Format: {fmt_dur:.3f}s")

        # 4) invoke
        t_inv = time.perf_counter()
        response = llm.invoke(messages)
        inv_dur = time.perf_counter() - t_inv
        logger.info(f"[Timer] Rewrite LLM Invoke: {inv_dur:.3f}s")

        rewritten = response.content if hasattr(response, "content") else str(response)
        rewritten = rewritten.strip()
        final_q = rewritten if rewritten else user_query

        total = time.perf_counter() - t0
        logger.info(f"[Timer] Rewrite Total: {total:.3f}s")

        return RewriteResult(
            original=user_query,
            rewritten=final_q,
            used_history=len(clean_history) > 0,
            used_summary=used_summary,
            model_name=rewrite_model,
        )
