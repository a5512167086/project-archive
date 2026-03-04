from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.logger import logger


class PromptService:
    def __init__(self, max_contexts_for_prompt: int = 3) -> None:
        self.max_contexts_for_prompt = int(max_contexts_for_prompt)

    def _is_english_query(self, query: str) -> bool:
        """偵測使用者提問是否主要是英文"""
        chinese_chars = re.findall(r"[\u4e00-\u9fa5]", query)
        return len(chinese_chars) < 1

    def build_messages(
        self,
        original_query: str,
        rewritten_query: str,
        contexts: List[Dict[str, Any]],
        history: Optional[List[BaseMessage]] = None,
    ) -> List[BaseMessage]:
        ctx = contexts[: self.max_contexts_for_prompt]

        context_lines: List[str] = []
        for i, c in enumerate(ctx, 1):
            item_type = c.get("type", "qa")
            if item_type == "file":
                content = str(c.get("content") or "").strip()
                if content:
                    context_lines.append(f"━━━ Source {i} ━━━\n{content}")
            else:
                q = str(c.get("question", "")).strip()
                a = str(c.get("answer", "")).strip()
                if q or a:
                    context_lines.append(f"━━━ Source {i} ━━━\nQ: {q}\nA: {a}")

        context_block = (
            "\n\n".join(context_lines) if context_lines else "(No relevant data found)"
        )

        is_eng = self._is_english_query(original_query)

        if is_eng:
            # 英文 System Prompt：對齊 Testset 的「語意完整」與「格式化」規則
            system = (
                "You are a strict database retrieval assistant. You can only output the provided content.\n\n"
                "【Output Rules (Absolute Hard Rules)】\n"
                "1) You MUST extract the answer from the provided content and format it as a grammatically correct sentence (e.g., capitalize the first letter, add proper ending punctuation).\n"
                "2) The answer MUST be a meaningful, standalone clause or the shortest complete sentence that directly answers the question. Do NOT output long paragraphs, and do NOT cut it down to just a few disconnected words. It must make sense on its own.\n"
                "3) ABSOLUTELY NO summarizing, paraphrasing, or rewriting the facts in your own words. Use the original terminology.\n"
                "4) ABSOLUTELY NO introductory remarks, conversational fillers, or concluding remarks.\n"
                "5) ABSOLUTELY NO references to source indices (e.g., 'Source 1').\n"
                "6) If the answer is not found, output ONLY: 'Information not available in current records.'\n"
                "7) You MUST reply in ENGLISH."
            )
            user_label = "USER QUESTION"
            rewritten_label = "REWRITTEN QUERY"
            context_label = "AVAILABLE CONTEXT"
            instruction = "Strictly follow the system rules to output the answer."
        else:
            # 中文 System Prompt：對齊 Testset 的「語意完整」與「格式化」規則
            system = (
                "你是嚴格的資料庫查詢助理，只能輸出提供的內容。\n\n"
                "【輸出格式（絕對硬性規則）】\n"
                "1) 你必須從原文中擷取答案，並將其格式化為符合一般文法規範的句子（例如：加上適當的句尾標點符號）。\n"
                "2) 答案必須是一個「具備完整語意的獨立子句」或「最短的完整句子」。請保持精簡，不要輸出長篇大論，但也絕對不要縮減到只剩幾個缺乏上下文的單字。答案本身必須讀起來通順且合理。\n"
                "3) 絕對禁止使用你自己的話進行總結、改寫或縮減原文，必須保留原始術語。\n"
                "4) 絕對禁止寫出任何「破題句」、開場白、結尾語或解釋性文字。\n"
                "5) 嚴禁在回答中出現任何指涉來源的字眼（如：來源 1、根據文件）。\n"
                "6) 若提供的內容不足以直接回答，請只輸出唯一的一句話：「目前資料未提供此資訊」，並立刻停止作答。\n"
                "7) 使用繁體中文回答。"
            )
            user_label = "使用者問題"
            rewritten_label = "語意理解"
            context_label = "可用內容"
            instruction = "請嚴格遵守系統規範輸出。"

        user = (
            f"【{user_label}】\n{original_query}\n\n"
            f"【{rewritten_label}】\n{rewritten_query}\n\n"
            f"【{context_label}】\n{context_block}\n\n"
            f"{instruction}"
        )

        msgs: List[BaseMessage] = [SystemMessage(content=system)]

        if history:
            for m in history:
                if isinstance(m, (HumanMessage, AIMessage)):
                    msgs.append(m)

        logger.info(
            f"[PromptService] Detected Language: {'English' if is_eng else 'Traditional Chinese'}"
        )
        logger.info("[PromptService] ===== SYSTEM PROMPT =====")
        logger.info(system)
        logger.info("[PromptService] ===== USER PROMPT =====")
        logger.info(user)

        msgs.append(HumanMessage(content=user))
        return msgs
