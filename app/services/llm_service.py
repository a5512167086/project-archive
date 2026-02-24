from __future__ import annotations

import os
from typing import Any, Dict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.configs.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_ENDPOINT,
    LLM_TEMPERATURE,
    OLLAMA_BASE_URL,
    OLLAMA_LLM_NAME,
)


class LLMService:
    def __init__(self) -> None:
        self._cache: Dict[str, Any] = {}

    def get_llm(self, model_name: str):
        if model_name in self._cache:
            return self._cache[model_name]

        if model_name == "gpt_5_mini":
            llm = ChatOpenAI(
                base_url=f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/v1",
                api_key=AZURE_OPENAI_API_KEY,
                model=AZURE_OPENAI_DEPLOYMENT,
                max_completion_tokens=2048,
                reasoning_effort="low",
            )
        elif model_name == "gemini_2.5_flash":
            if "GOOGLE_API_KEY" not in os.environ:
                raise ValueError("GOOGLE_API_KEY environment variable not set.")
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=float(LLM_TEMPERATURE),
                max_output_tokens=2048,
            )
        elif model_name == "qwen2.5_local":
            llm = ChatOllama(
                base_url=OLLAMA_BASE_URL,
                model=OLLAMA_LLM_NAME,
                temperature=float(LLM_TEMPERATURE),
            )
        else:
            llm = self.get_llm("qwen2.5_local")

        self._cache[model_name] = llm
        return llm
