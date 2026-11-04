from __future__ import annotations

import re
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

        # 簡單判定是否為中文 (若包含中文字元則為中文，否則視為英文)
        is_chinese = bool(re.search(r"[\u4e00-\u9fff]", user_query))

        summary_context = ""
        used_summary = False
        if use_sum and (snapshot.summary or "").strip():
            used_summary = True
            if is_chinese:
                summary_context = f"【長期對話摘要】：{snapshot.summary.strip()}\n"
            else:
                summary_context = f"[Long-term Summary]: {snapshot.summary.strip()}\n"

        # 根據語言動態切換 System Prompt
        if is_chinese:
            system_prompt = (
                "你是一個專業的查詢改寫器 (Query Rewriter)。\n"
                f"{summary_context}"
                "請根據歷史對話，判斷使用者的「最新問題」是否缺少主詞、受詞或上下文。\n"
                "【改寫規則】\n"
                "1. 補全缺失：若問題包含代名詞 (例如：它、這個) 或明顯省略了前文提過的資訊，請用歷史對話將其替換為具體名詞，使其成為獨立且完整的問句。\n"
                "2. 獨立話題不干擾 (極重要)：若最新問題是一個「全新話題」，或本身語意已經非常完整，請【原封不動】輸出原問題，絕對不要強加前文的不相關條件。\n"
                "3. 鎖定關鍵字：必須極度忠於原句的用詞，盡可能保留原問句中的專有名詞與核心動詞，禁止自創同義詞替換。\n"
                "4. 語言一致：改寫後的語言必須與「最新問題」完全相同 (繁體中文)。\n"
                "5. 格式限制：不要回答問題，只准輸出改寫後的單一問句，禁止任何解釋或前言。"
            )
        else:
            system_prompt = (
                "You are a professional Query Rewriter.\n"
                f"{summary_context}"
                "Based on the conversation history, determine if the user's 'latest question' lacks a subject, object, or context.\n"
                "[Rewrite Rules]\n"
                "1. Resolve Coreferences: If the question contains pronouns (e.g., it, they) or omits previously mentioned context, replace them with specific nouns from the history to make it a standalone, complete question.\n"
                "2. Isolate New Topics (Crucial): If the latest question introduces a 'completely new topic' or is already semantically complete, output the original question EXACTLY AS IS. Do not forcefully add irrelevant conditions from the history.\n"
                "3. Lock Keywords: Strictly adhere to the original wording. Retain proper nouns and core verbs. Do not invent synonyms.\n"
                "4. Language Consistency: The output must be in the exact same language as the 'latest question' (English).\n"
                "5. Format Constraint: Do not answer the question. Only output the single rewritten question. No explanations, no conversational filler."
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
