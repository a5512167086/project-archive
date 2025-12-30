from __future__ import annotations

import os
from typing import Any, Dict, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import ChatHuggingFace
from langchain_openai import ChatOpenAI

from app.configs.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_ENDPOINT,
    LLM_TEMPERATURE,
)


class LLMService:
    """Factory + cache for chat models used by RAG."""

    def __init__(
        self, preloaded_hf_chat_model: Optional[ChatHuggingFace] = None
    ) -> None:
        self._preloaded_hf = preloaded_hf_chat_model
        self._cache: Dict[str, Any] = {}

    def get_llm(self, model_name: str):
        if model_name in self._cache:
            return self._cache[model_name]

        if model_name == "gpt_5_mini":
            llm = ChatOpenAI(
                base_url=f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/v1",
                api_key=AZURE_OPENAI_API_KEY,
                model=AZURE_OPENAI_DEPLOYMENT,
                max_completion_tokens=512,
                reasoning_effort="low",
            )
        elif model_name == "gemini_2.5_flash":
            if "GOOGLE_API_KEY" not in os.environ:
                raise ValueError("GOOGLE_API_KEY environment variable not set.")
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=float(LLM_TEMPERATURE),
                max_output_tokens=512,
            )
        elif model_name == "qwen3_local":
            if not self._preloaded_hf:
                raise ValueError("HuggingFace model not pre-loaded.")
            llm = self._preloaded_hf
        else:
            llm = self.get_llm("gpt_5_mini")

        self._cache[model_name] = llm
        return llm
