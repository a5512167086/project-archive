from langchain_openai import ChatOpenAI
from openai import OpenAI

from app.configs.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_ENDPOINT,
)


def get_raw_openai_client() -> OpenAI:
    """原生 OpenAI client（適合給 RAGAS llm_factory 等用）"""
    endpoint = f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/v1"
    return OpenAI(base_url=endpoint, api_key=AZURE_OPENAI_API_KEY)


def get_langchain_llm() -> ChatOpenAI:
    """用 LangChain 的 ChatOpenAI 呼叫 Azure GPT-5 mini（走 v1 相容模式）"""
    return ChatOpenAI(
        base_url=f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/v1",
        api_key=AZURE_OPENAI_API_KEY,
        model=AZURE_OPENAI_DEPLOYMENT,  # 這裡一樣填「部署名稱」 gpt-5-mini
        temperature=0,
        max_tokens=256,
    )


if __name__ == "__main__":
    # 1) 直接用 OpenAI client 呼叫
    client = get_raw_openai_client()
    completion = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[{"role": "user", "content": "What is the capital of France?"}],
    )
    print("[raw openai]", completion.choices[0].message)

    # 2) 用 LangChain LLM 呼叫
    llm = get_langchain_llm()
    resp = llm.invoke("What is the capital of France?")
    print("[langchain]", resp.content)
