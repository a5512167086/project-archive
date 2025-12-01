import os
from abc import ABC, abstractmethod

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import ChatHuggingFace
from langchain_openai import ChatOpenAI

from app.configs.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_ENDPOINT,
    LLM_TEMPERATURE,
)


class BaseLLMService(ABC):
    # 預設不加 /no_think
    USE_NO_THINK: bool = False

    def _build_messages(self, user_query: str, contexts: list[dict]) -> list[dict]:
        ctx = contexts[:3]
        answers = [
            c.get("answer", "").strip() for c in ctx if c.get("answer", "").strip()
        ]
        if not answers:
            context_block = "無"
        else:
            context_block = "\n".join(f"{i}. {ans}" for i, ans in enumerate(answers, 1))

        no_think_prefix = "/no_think \n" if self.USE_NO_THINK else ""

        system = (
            f"{no_think_prefix}"
            "你是一位專業的客服知識庫助理，請嚴格遵守以下規則：\n\n"
            "1. 必須根據提供的[知識片段]回覆，並確保回覆能直接解答使用者的問題。\n"
            "2. 當使用者使用第一人稱（如「我」、「我的」）提問，而知識片段提供的是通用性資訊時，請自然地將通用資訊套用到使用者問題中。\n"
            "3. 回答時，請優先聚焦在與問題最相關的知識片段，與問題不相關的知識片段則應忽略。\n"
            "4. 如果知識片段沒有提供明確答案，但有相關條件或方向，請整理並提供給使用者。\n"
            "5. 關鍵性的事實需逐字複製片段原文，確保答案的正確性。\n"
            "6. 在知識片段完全沒有任何相關內容時，才回答：「目前知識庫中沒有找到與此問題相關的資訊。」\n"
            "7. 回答必須使用清晰、簡潔的繁體中文，避免任何前言、結語或寒暄，並將回答字數限制在100字內。\n"
            "8. 嚴禁輸出任何思考過程、推理文字或 XML 標籤（如 <think>）\n"
            "---"
        )

        user = (
            f"使用者問題：\n"
            f"「{user_query}」\n\n"
            f"以下是與使用者問題相關的知識片段：\n"
            f"```\n{context_block}\n```\n\n"
            f"請根據上述資訊，直接提供最終答案的一段文字，不要描述分析過程。"
        )

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    def _to_langchain_messages(self, messages: list[dict]):
        langchain_messages = []
        for msg in messages:
            if msg["role"] == "system":
                langchain_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
        return langchain_messages

    @abstractmethod
    def generate(self, user_query: str, contexts: list[dict]) -> str:
        pass


class GeminiLLMService(BaseLLMService):
    """对应 Google Gemini (透过 Google AI API)"""

    USE_NO_THINK = False

    def __init__(self) -> None:
        if "GOOGLE_API_KEY" not in os.environ:
            raise ValueError("GOOGLE_API_KEY environment variable not set.")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=float(LLM_TEMPERATURE),
            max_output_tokens=2048,
        )

    def generate(self, user_query: str, contexts: list[dict]) -> str:
        messages = self._build_messages(user_query, contexts)
        langchain_messages = self._to_langchain_messages(messages)
        response = self.llm.invoke(langchain_messages)
        return response.text


class AzureLLMService(BaseLLMService):
    """對應 ChatGPT o4 mini (透過 Azure API)"""

    USE_NO_THINK = False

    def __init__(self) -> None:
        self.llm = ChatOpenAI(
            base_url=f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/v1",
            api_key=AZURE_OPENAI_API_KEY,
            model=AZURE_OPENAI_DEPLOYMENT,
            temperature=float(LLM_TEMPERATURE),
            max_tokens=4096,
            reasoning_effort="low",
        )

    def generate(self, user_query: str, contexts: list[dict]) -> str:
        messages = self._build_messages(user_query, contexts)
        langchain_messages = self._to_langchain_messages(messages)
        response = self.llm.invoke(langchain_messages)
        print(response)
        return response.content


class HuggingFaceLLMService(BaseLLMService):
    """對應預先載入的本地 HuggingFace 模型"""

    USE_NO_THINK = True

    def __init__(self, chat_model: ChatHuggingFace):
        print("Initializing HuggingFace service with pre-loaded model...")
        self.llm = chat_model

    def generate(self, user_query: str, contexts: list[dict]) -> str:
        messages = self._build_messages(user_query, contexts)
        langchain_messages = self._to_langchain_messages(messages)

        # 獲取模型的原始輸出
        raw_response = self.llm.invoke(langchain_messages).content

        # <<< 新增：更強健的輸出清理邏輯 --- >>>

        # 1. 嘗試定位到 assistant 的真正回答開頭
        assistant_marker = "<|im_start|>assistant"
        if assistant_marker in raw_response:
            # 取 assistant 標籤之後的所有內容
            raw_response = raw_response.split(assistant_marker, 1)[-1]

        # 2. 移除思考過程的 <think> 區塊
        if "</think>" in raw_response:
            raw_response = raw_response.split("</think>", 1)[-1]

        # 3. 移除結尾的特殊標籤
        if "<|im_end|>" in raw_response:
            raw_response = raw_response.split("<|im_end|>")[0]

        # <<< --- 清理結束 --- >>>

        return raw_response.strip()


class LLMFactory:
    def __init__(self, chat_model: ChatHuggingFace = None):
        self._instances = {}
        self.preloaded_chat_model = chat_model

    def get_service(self, model_name: str) -> BaseLLMService:
        if model_name in self._instances:
            return self._instances[model_name]

        print(f"Initializing service for model: '{model_name}'")
        if model_name == "gpt_5_mini":
            service = AzureLLMService()
        elif model_name == "gemini_2.5_flash":
            service = GeminiLLMService()
        elif model_name == "qwen3_local":
            if self.preloaded_chat_model:
                service = HuggingFaceLLMService(self.preloaded_chat_model)
            else:
                raise ValueError(
                    "HuggingFace model not pre-loaded or passed to factory."
                )
        else:
            print(
                f"Warning: Model '{model_name}' not found. Defaulting to 'gpt_5_mini'."
            )
            service = AzureLLMService()
            model_name = "gpt_5_mini"

        self._instances[model_name] = service
        return service
