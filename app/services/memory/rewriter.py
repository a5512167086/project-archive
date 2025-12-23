# app/services/rag_modules/rewriter/history_rewriter.py
from __future__ import annotations

from typing import Any, Callable, List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

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
        llm = self.get_llm(rewrite_model)

        # 只保留 Human/AI，避免 system 混入
        clean_history: List[BaseMessage] = []
        for m in snapshot.recent_messages:
            if isinstance(m, HumanMessage) or isinstance(m, AIMessage):
                clean_history.append(m)

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

        chain = prompt | llm | StrOutputParser()
        rewritten = chain.invoke({
            "input": user_query,
            "chat_history": clean_history,
        }).strip()

        final_q = rewritten if rewritten else user_query

        return RewriteResult(
            original=user_query,
            rewritten=final_q,
            used_history=len(clean_history) > 0,
            used_summary=used_summary,
            model_name=rewrite_model,
        )
