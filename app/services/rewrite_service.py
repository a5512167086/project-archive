from __future__ import annotations

import time
from typing import Any, Callable, List, Optional, Protocol

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.logger import logger
from app.schemas import MemorySnapshot, RewriteResult


class SnapshotLoader(Protocol):
    def load(self, session_key: str, max_messages: int) -> MemorySnapshot: ...


class RewriteService:
    def __init__(
        self,
        get_llm: Callable[[str], Any],
        snapshot_loader: SnapshotLoader,
        use_summary: bool = True,
    ) -> None:
        self._get_llm = get_llm
        self._loader = snapshot_loader
        self._use_summary_default = bool(use_summary)

        self._prompt_tpl = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

    def rewrite(
        self,
        session_key: str,
        user_query: str,
        history_rounds: int,
        rewrite_model: str,
        use_summary: Optional[bool] = None,
    ) -> RewriteResult:
        t0 = time.perf_counter()

        snapshot = self._loader.load(
            session_key, max_messages=max(0, int(history_rounds) * 2)
        )
        rr = self.rewrite_with_snapshot(
            user_query=user_query,
            snapshot=snapshot,
            rewrite_model=rewrite_model,
            use_summary=use_summary,
        )

        logger.info(f"[Timer] RewriteService Total: {(time.perf_counter() - t0):.3f}s")
        return rr

    def rewrite_with_snapshot(
        self,
        user_query: str,
        snapshot: MemorySnapshot,
        rewrite_model: str,
        use_summary: Optional[bool] = None,
    ) -> RewriteResult:
        t0 = time.perf_counter()

        t_llm = time.perf_counter()
        llm = self._get_llm(rewrite_model)
        logger.info(f"[Timer] Rewrite Get LLM: {(time.perf_counter() - t_llm):.3f}s")

        t_clean = time.perf_counter()
        clean_history: List[BaseMessage] = [
            m
            for m in (snapshot.recent_messages or [])
            if isinstance(m, (HumanMessage, AIMessage))
        ]
        logger.info(
            f"[Timer] Rewrite Clean History: {(time.perf_counter() - t_clean):.3f}s | Used: {len(clean_history)}"
        )

        use_sum = (
            self._use_summary_default if use_summary is None else bool(use_summary)
        )

        summary_context = ""
        used_summary = False
        if use_sum and (snapshot.summary or "").strip():
            used_summary = True
            summary_context = f"【長期對話摘要】：{snapshot.summary.strip()}\n"

        system_prompt = (
            "你是一個對話上下文解析器。"
            f"{summary_context}"
            "請參考上下文，將「最新使用者問題」補全省略的主詞或受詞，改寫為單一且完整的問句。"
            "【重要約束】"
            "1. 保持原意：不更改使用者問題的原始意圖或意思。"
            "2. 簡潔精確：不要過度解釋名詞定義。"
            "3. 只輸出改寫後的問題，不要回答。"
            "4. 輸出必須使用繁體中文。"
        )

        t_fmt = time.perf_counter()
        messages = self._prompt_tpl.format_messages(
            system_prompt=system_prompt,
            input=user_query,
            chat_history=clean_history,
        )
        logger.info(
            f"[Timer] Rewrite Prompt Format: {(time.perf_counter() - t_fmt):.3f}s"
        )

        t_inv = time.perf_counter()
        response = llm.invoke(messages)
        logger.info(f"[Timer] Rewrite LLM Invoke: {(time.perf_counter() - t_inv):.3f}s")

        rewritten = getattr(response, "content", None)
        if not isinstance(rewritten, str) or not rewritten.strip():
            rewritten = str(response).strip()

        final_q = rewritten.strip() if rewritten.strip() else user_query
        logger.info(f"[Timer] Rewrite Total: {(time.perf_counter() - t0):.3f}s")

        return RewriteResult(
            original=user_query,
            rewritten=final_q,
            used_history=len(clean_history) > 0,
            used_summary=used_summary,
            model_name=rewrite_model,
        )
