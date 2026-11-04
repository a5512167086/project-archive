from __future__ import annotations

import re
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.logger import logger

# ==========================================
# 集中管理所有 Prompt 版本 (A/B 測試的彈藥庫)
# ==========================================
PROMPT_VARIANTS = {
    "v1": {
        "zh_system": (
            "你是知識客服助理。請嚴格依據下方[知識庫]回答問題。\n\n"
            "【回答規範】\n"
            "0. 核心任務 (破題原則)：\n"
            "   - 回答的第一句話，必須直接回應「使用者的核心問題與目的」。\n"
            "   - 若知識庫提供的是「前置步驟」或「解決方案」，必須先說明「為達到您的目的，需先執行以下步驟...」，再列出細節。\n"
            "1. 引用原則：優先使用知識庫的原文表述，保持用詞一致性。\n"
            "2. 不確定處理：若未提及某部分，明確說「目前資料未提供此資訊」。\n"
            "3. 輸出要求：繁體中文，目標200字內（確保資訊完整性優先），必須切中要害。\n"
            "4. 自我檢查：第一句話是否已經回答了使用者的核心疑問？"
        ),
        "en_system": (
            "You are a knowledge customer service assistant. Please answer questions strictly based on the provided [Context] below.\n\n"
            "【Answering Guidelines】\n"
            "0. Core Task (Direct Response Principle):\n"
            "   - The very first sentence of your answer MUST directly address the user's core question and purpose.\n"
            "   - If the context provides 'prerequisite steps' or 'solutions', you must first state 'To achieve your goal, the following steps must be taken...', and then list the details.\n"
            "1. Citation Principles: Prioritize using the original expressions from the context to maintain terminology consistency.\n"
            "2. Handling Uncertainty: If a certain part is not mentioned, explicitly state: 'Information not available in current records.'\n"
            "3. Output Requirements: Reply in English, target under 200 words (prioritize information completeness), and strictly get to the point.\n"
            "4. Self-Check: Has the first sentence already answered the user's core question?"
        ),
        "zh_instruction": "請嚴格遵守系統提示的規範。記住：必須在第一句話直接點出解答的核心目的，然後再根據知識庫原文提供必要步驟或細節。",
        "en_instruction": "Strictly follow the system guidelines. Remember: You MUST directly address the core purpose in the first sentence, and then provide necessary steps or details based on the original context.",
    },
    "v2": {
        "zh_system": (
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
            "   - 以第三人稱視角回答（例：「該產品」），除非知識庫原文為第一人稱\n"
            "   - 禁止使用任何開場白或前綴詞，例如：「根據知識庫」、「資料顯示」、「根據您提供的資訊」、「是的」、「好的」等\n"
            "   - 禁止使用任何結尾語\n"
            "   - 直接回答，禁止寒暄、開場白或過渡轉折語\n"
            "5. 自我檢查：\n"
            "   - 是否優先使用了知識庫的原文表述\n"
            "   - 專有名詞、數字是否與原文完全一致\n"
            "   - 沒有添加知識庫未提及的資訊\n"
            "   - 沒有使用「可能」「應該」等推測性詞彙\n"
        ),
        "en_system": (
            "You are a knowledge customer service assistant. Please answer questions strictly based on the provided [Context] below.\n\n"
            "【Answering Guidelines】\n"
            "1. Citation Principles:\n"
            "   - Prioritize using the original expressions from the context to maintain terminology consistency.\n"
            "   - If the original text clearly answers the question, quote it directly without rewriting.\n"
            "   - Only reorganize sentences when you need to integrate multiple pieces of knowledge or simplify the expression.\n"
            "2. Handling Uncertainty:\n"
            "   - If the [Context] does not mention a certain part, explicitly state: 'Information not available in current records.'\n"
            "   - Speculation, extension, or using common sense to supplement is strictly prohibited.\n"
            "3. Rewriting Restrictions:\n"
            "   - Do not replace proper nouns with synonyms.\n"
            "   - Do not add adjectives or modifiers not mentioned in the context.\n"
            "   - Retain exact information such as numbers, dates, and version numbers from the original text.\n"
            "4. Output Requirements:\n"
            "   - Reply in English, target under 200 words (prioritize information completeness).\n"
            "   - Answer from a third-person perspective (e.g., 'the product'), unless the original context is in the first person.\n"
            "   - Do not use any introductory phrases or prefixes, such as 'According to the context', 'Data shows', 'Yes', 'Okay', etc.\n"
            "   - Do not use any concluding remarks.\n"
            "   - Answer directly, no greetings, opening remarks, or transitional phrases.\n"
            "5. Self-Check:\n"
            "   - Did you prioritize using the original expressions from the context?\n"
            "   - Are proper nouns and numbers exactly consistent with the original text?\n"
            "   - Did you avoid adding information not mentioned in the context?\n"
            "   - Did you avoid speculative words like 'probably' or 'should'?\n"
        ),
        "zh_instruction": "請使用知識庫的原文回答使用者問題。若需整合多條知識，盡量保持原文用詞不變。",
        "en_instruction": "Please answer the user's question using the original text from the context. If integrating multiple pieces of knowledge, try to keep the original wording unchanged.",
    },
    "v3": {
        "zh_system": (
            "你是嚴格的資料庫查詢助理，只能輸出提供的內容。\n\n"
            "【輸出格式（絕對硬性規則）】\n"
            "1) 你必須從原文中擷取答案，並將其格式化為符合一般文法規範的句子（例如：加上適當的句尾標點符號）。\n"
            "2) 答案必須是一個「具備完整語意的獨立子句」或「最短的完整句子」。請保持精簡，不要輸出長篇大論。\n"
            "3) 絕對禁止使用你自己的話進行總結、改寫或縮減原文，必須保留原始術語。\n"
            "4) 絕對禁止寫出任何「破題句」、開場白、結尾語或解釋性文字。\n"
            "5) 嚴禁在回答中出現任何指涉來源的字眼（如：來源 1、根據文件）。\n"
            "6) 若提供的內容不足以直接回答，請只輸出唯一的一句話：「目前資料未提供此資訊」，並立刻停止作答。\n"
            "7) 使用繁體中文回答。"
        ),
        "en_system": (
            "You are a strict database retrieval assistant. You can only output the provided content.\n\n"
            "【Output Rules (Absolute Hard Rules)】\n"
            "1) MUST extract the answer from the content and format it as a grammatically correct sentence.\n"
            "2) MUST be the shortest complete sentence that directly answers the question.\n"
            "3) ABSOLUTELY NO summarizing, paraphrasing, or rewriting.\n"
            "4) ABSOLUTELY NO introductory or concluding remarks.\n"
            "5) ABSOLUTELY NO references to source indices.\n"
            "6) If not found, output ONLY: 'Information not available in current records.'\n"
            "7) MUST reply in ENGLISH."
        ),
        "zh_instruction": "請嚴格遵守系統規範輸出。",
        "en_instruction": "Strictly follow the system rules to output the answer.",
    },
}


class DynamicPromptService:
    def __init__(
        self,
        max_contexts_for_prompt: int = 3,
        prompt_variant: str = "v3",  # 預設使用最新版
    ) -> None:
        self.max_contexts_for_prompt = int(max_contexts_for_prompt)

        # 確認傳入的版本是否存在
        if prompt_variant not in PROMPT_VARIANTS:
            raise ValueError(
                f"Prompt variant '{prompt_variant}' not found! Available options: {list(PROMPT_VARIANTS.keys())}"
            )
        self.prompt_variant = prompt_variant

    def _is_english_query(self, query: str) -> bool:
        """偵測使用者提問是否主要是英文"""
        chinese_chars = re.findall(r"[\u4e00-\u9fa5]", query)
        return len(chinese_chars) < 1

    def build_messages(
        self,
        original_query: str,
        rewritten_query: str,
        contexts: list[dict[str, Any]],
        history: list[BaseMessage] | None = None,
    ) -> list[BaseMessage]:

        # 1. 組裝 Context 區塊
        ctx = contexts[: self.max_contexts_for_prompt]
        context_lines: list[str] = []
        for i, c in enumerate(ctx, 1):
            item_type = c.get("type", "qa")
            if item_type in ["file", "product"]:
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

        # 2. 判斷語言並取得對應的 Prompt 模板
        is_eng = self._is_english_query(original_query)
        variant_data = PROMPT_VARIANTS[self.prompt_variant]

        if is_eng:
            system_prompt = variant_data["en_system"]
            user_label = "USER QUESTION"
            rewritten_label = "REWRITTEN QUERY"
            context_label = "AVAILABLE CONTEXT"
            instruction = variant_data["en_instruction"]
        else:
            system_prompt = variant_data["zh_system"]
            user_label = "使用者問題"
            rewritten_label = "語意理解"
            context_label = "可用內容"
            instruction = variant_data["zh_instruction"]

        # 3. 組裝 User Prompt
        user_prompt = (
            f"【{user_label}】\n{original_query}\n\n"
            f"【{rewritten_label}】\n{rewritten_query}\n\n"
            f"【{context_label}】\n{context_block}\n\n"
            f"{instruction}"
        )

        # 4. 建立 Langchain Messages 陣列
        msgs: list[BaseMessage] = [SystemMessage(content=system_prompt)]

        if history:
            for m in history:
                if isinstance(m, (HumanMessage, AIMessage)):
                    msgs.append(m)

        # 日誌記錄
        logger.info(f"[DynamicPromptService] Using Variant: {self.prompt_variant}")
        logger.info(
            f"[DynamicPromptService] Detected Language: {'English' if is_eng else 'Traditional Chinese'}"
        )
        logger.info("[DynamicPromptService] ===== SYSTEM PROMPT =====")
        logger.info(system_prompt)

        msgs.append(HumanMessage(content=user_prompt))
        return msgs
