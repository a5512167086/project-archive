from __future__ import annotations

from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.logger import logger


class PromptService:
    def __init__(self, max_contexts_for_prompt: int = 3) -> None:
        self.max_contexts_for_prompt = int(max_contexts_for_prompt)

    def build_messages(
        self,
        original_query: str,
        rewritten_query: str,
        contexts: List[Dict[str, Any]],
        history: Optional[List[BaseMessage]] = None,
    ) -> List[BaseMessage]:
        ctx = contexts[: self.max_contexts_for_prompt]

        context_lines = []
        for i, c in enumerate(ctx, 1):
            q = (c.get("question", "") or "").strip()
            a = (c.get("answer", "") or "").strip()
            context_lines.append(f"━━━ 知識條目 {i} ━━━\n問題：{q}\n答案：{a}")

        context_block = "\n\n".join(context_lines) if context_lines else "無相關知識"

        system = (
            "你是知識客服助理。請嚴格依據下方[知識庫]回答問題。\n\n"
            "【回答規範】\n"
            "1. 引用原則：\n"
            "   - 優先使用知識庫的原文表述，保持用詞一致性\n"
            "   - 若原文已清楚回答問題，直接引用，不要改寫\n"
            "   - 僅在需要整合多條知識或簡化表達時才重新組織語句\n"
            "2. 不確定處理：\n"
            "   - 若[知識庫]未提及某部分，明確說「目前資料未提供此資訊」\n"
            "   - 嚴禁推測、延伸或使用常識補充\n"
            "3. 改寫限制：\n"
            "   - 禁止用同義詞替換專有名詞（如「雲端」→「雲端運算」）\n"
            "   - 禁止添加知識庫未提及的形容詞或修飾語\n"
            "   - 保留原文的數字、日期、版本號等精確資訊\n"
            "4. 輸出要求：\n"
            "   - 繁體中文，目標200字內（確保資訊完整性優先）\n"
            "   - 第三人稱視角（例：「該產品」），除非知識庫原文為第一人稱\n"
            "   - 直接回答，禁止寒暄、開場白或過渡轉折語\n"
            "5. 自我檢查：\n"
            "   - 是否優先使用了知識庫的原文表述\n"
            "   - 專有名詞、數字是否與原文完全一致\n"
            "   - 沒有添加知識庫未提及的資訊\n"
            "   - 沒有使用「可能」「應該」等推測性詞彙\n\n"
        )

        user = (
            f"【使用者問題】\n{original_query}\n\n"
            f"【語意理解】\n{rewritten_query}\n\n"
            f"【知識庫】\n{context_block}\n\n"
            "請使用知識庫的原文回答使用者問題。"
            "若需整合多條知識，盡量保持原文用詞不變。"
        )

        msgs: List[BaseMessage] = [SystemMessage(content=system)]

        if history:
            for m in history:
                if isinstance(m, (HumanMessage, AIMessage)):
                    msgs.append(m)

        logger.info("[PromptService] ===== SYSTEM PROMPT =====")
        logger.info(system)
        logger.info("[PromptService] ===== USER PROMPT =====")
        logger.info(user)

        msgs.append(HumanMessage(content=user))
        return msgs
