from __future__ import annotations

from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.logger import logger


class PromptService:
    def __init__(self, *, max_contexts_for_prompt: int = 3) -> None:
        self.max_contexts_for_prompt = int(max_contexts_for_prompt)

    def build_messages(
        self,
        *,
        original_query: str,
        rewritten_query: str,
        contexts: List[Dict[str, Any]],
        use_no_think: bool,
        history: Optional[List[BaseMessage]] = None,
    ) -> List[BaseMessage]:
        ctx = contexts[: self.max_contexts_for_prompt]
        context_lines = [
            f"{i}. Q: {(c.get('question', '') or '').strip()}，A: {(c.get('answer', '') or '').strip()}"
            for i, c in enumerate(ctx, 1)
        ]
        context_block = "\n".join(context_lines) if context_lines else "無"

        no_think_prefix = "/no_think \n" if use_no_think else ""

        system = (
            f"{no_think_prefix}"
            "你是指南客服助理。請依據下方[知識庫]回答問題。\n"
            "【核心原則】\n"
            "1. 絕對忠實：答案必須來自[知識庫]，嚴禁使用外部知識。若無答案請直說。\n"
            "2. 最高權重：若[知識庫]與歷史對話衝突，以[知識庫]為準。\n"
            "3. 格式限制：繁體中文，100字內。直接回答，免寒暄，禁輸出思考標籤(<think>)。\n"
            "4. 語氣轉換：將通用資訊轉化為針對使用者的回答(如處理第一人稱提問)。"
        )

        user = (
            f"原始提問：{original_query}\n"
            f"語意參照：{rewritten_query}\n\n"
            f"[知識庫]：\n{context_block}\n\n"
            "請依據[知識庫]回答原始提問。"
        )

        msgs: List[BaseMessage] = [SystemMessage(content=system)]

        if history:
            for m in history:
                if isinstance(m, (HumanMessage, AIMessage)):
                    msgs.append(m)

        logger.info("[PromptService] prompt")
        logger.info(system)
        logger.info(user)

        msgs.append(HumanMessage(content=user))
        return msgs

    def clean_hf_output(self, raw: str) -> str:
        """Clean local HF chat template artifacts (qwen, etc.)."""
        if "<|im_start|>assistant" in raw:
            raw = raw.split("<|im_start|>assistant", 1)[-1]
        if "</think>" in raw:
            raw = raw.split("</think>", 1)[-1]
        if "<|im_end|>" in raw:
            raw = raw.split("<|im_end|>", 1)[0]
        return raw.strip()
