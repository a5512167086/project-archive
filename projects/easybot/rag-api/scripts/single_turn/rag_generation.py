# scripts/generation_script.py
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings

from app.configs.config import (
    MONGODB_CHAT_COLLECTION,
    MONGODB_DB_NAME,
    MONGODB_URI,
    OLLAMA_BASE_URL,
    OLLAMA_EMBED_NAME,
    QDRANT_COLLECTION,
    QDRANT_URL,
)
from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService
from app.services.rag_service import RAGService
from app.services.reranker_service import RerankerService
from app.services.retrieval_service import RetrievalService
from app.services.rewrite_service import RewriteService
from app.services.summary_service import SummaryService
from app.services.vector_service import VectorService
from app.utils.summary_memory import SummaryMemory

# -----------------------------
# Paths (repo root)
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
STOPWORDS_PATH = str(BASE_DIR / "data" / "stopwords.txt")


# -----------------------------
# Experiment configs
# -----------------------------
@dataclass(frozen=True)
class ExpConfig:
    name: str
    use_rerank: bool


EXPERIMENTS: list[ExpConfig] = [
    ExpConfig(name="baseline", use_rerank=False),
    ExpConfig(name="rerank", use_rerank=True),
]

RETRIEVAL_MODES: list[str] = [
    "hybrid",
    "vector",
    "lexical",
]

DATASET_CONFIG: dict[str, dict[str, str]] = {
    "rag_testset": {
        "path": "./data/testset/rag_testset.json",
        "bot_uuid": "a6e042eb-7889-4bcb-996c-1845d2215fc2",
    },
    "wke_rag_testset": {
        "path": "./data/testset/wke_rag_testset.json",
        "bot_uuid": "22a78f31-6b25-419e-af63-848a4463caf2",
    },
}

MODELS_TO_RUN: list[str] = [
    "local_model",
]


# -----------------------------
# Helpers
# -----------------------------
def _score_threshold_for_mode(mode: str) -> float:
    mode = (mode or "").lower().strip()
    if mode in ("vector", "hybrid"):
        return 0.4
    return 0.0


# 讀取測試資料的邏輯改為解析 JSON
def load_test_data(path: str) -> list[dict[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    test_data = []
    for row in data:
        q = str(row.get("question", "")).strip()
        a = str(row.get("answer", "")).strip()
        if q and a and q.lower() != "nan":
            test_data.append({"question": q, "ground_truth": a})
    return test_data


def save_json(results, filename):
    out_path = Path(filename)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def _preview_hit(h: dict[str, Any]) -> str:
    """與 PromptService 邏輯同步的 Log 顯示"""
    score_str = f"score={h.get('score', 0):.4f}"
    if h.get("rerank_score"):
        score_str += f" | rerank={h['rerank_score']:.4f}"

    item_type = h.get("type", "qa")

    if item_type in ["file", "product"]:
        prefix = "檔案" if item_type == "file" else "商品"
        source = (
            h.get("display_name")
            or h.get("filename")
            or h.get("product_name")
            or "未知來源"
        )
        content = str(h.get("content", "")).replace("\n", " ").strip()
        display_text = f"{prefix}：{source} | 內容：{content}"
    else:
        q = str(h.get("question", "")).replace("\n", " ").strip()
        a = str(h.get("answer", "")).replace("\n", " ").strip()
        display_text = f"問題：{q}\n答案：{a}"

    preview = (display_text[:120] + "...") if len(display_text) > 120 else display_text
    return f"- {score_str} | {preview}"


def _contexts_for_ragas(hits: list[dict[str, Any]]) -> list[str]:
    contexts = []
    for h in hits:
        item_type = h.get("type", "qa")

        # 產品與檔案都統一從 content 欄位抓取完整描述
        if item_type in ["file", "product"]:
            prefix = "檔案名稱" if item_type == "file" else "商品名稱"
            source = (
                h.get("display_name")
                or h.get("filename")
                or h.get("product_name")
                or "未命名"
            )
            content = str(h.get("content", "")).strip()
            if content:
                contexts.append(f"{prefix}：{source}\n內容：{content}")
        else:
            # FAQ 格式
            q = str(h.get("question", "")).strip()
            a = str(h.get("answer", "")).strip()
            if q or a:
                contexts.append(f"問題：{q}\n答案：{a}")
    return contexts


# -----------------------------
# Core Wrapper
# -----------------------------
def _rag_answer_with_retry(rag: RAGService, **kwargs) -> dict[str, Any]:
    max_attempts = kwargs.pop("max_attempts", 5)
    for attempt in range(1, max_attempts + 1):
        try:
            return rag.answer(line_id=None, **kwargs)
        except Exception as e:
            if attempt == max_attempts:
                raise e
            time.sleep(1.5 * attempt)


def build_services(embeddings):
    llm_service = LLMService()
    prompt_service = PromptService()
    vs = VectorService(embeddings, QDRANT_URL, QDRANT_COLLECTION)
    rs = RetrievalService(vs, stopwords_path=STOPWORDS_PATH)
    mem = SummaryMemory(
        MONGODB_URI,
        MONGODB_DB_NAME,
        MONGODB_CHAT_COLLECTION,
        llm_service.get_llm,
        summary_trigger_threshold=999999,
    )
    ss = SummaryService(mem)
    rerank_s = RerankerService()
    rewrite_s = RewriteService(llm_service.get_llm, ss)

    rag_service = RAGService(
        embeddings=embeddings,
        llm_service=llm_service,
        prompt_service=prompt_service,
        reranker_service=rerank_s,
        summary_service=ss,
        rewrite_service=rewrite_s,
        retrieval_service=rs,
        memory=mem,
    )
    return rag_service, rs


def main():
    load_dotenv()
    embeddings = OllamaEmbeddings(model=OLLAMA_EMBED_NAME, base_url=OLLAMA_BASE_URL)
    rag, rs = build_services(embeddings)

    # 輸出資料夾改為 single_turn
    out_dir = Path("./data/eval_dataset/single_turn")
    out_dir.mkdir(parents=True, exist_ok=True)

    for d_key, cfg in DATASET_CONFIG.items():
        bot_uuid = UUID(cfg["bot_uuid"])
        test_data = load_test_data(cfg["path"])
        rs.refresh_index(bot_uuid)

        for model in MODELS_TO_RUN:
            for mode in RETRIEVAL_MODES:
                for exp in EXPERIMENTS:
                    print(f"\n>>> Running: {mode} | {exp.name} | {model}")
                    results = []

                    # 重新加回 TXT log 檔案的邏輯
                    log_path = out_dir / f"runlog_{model}_{d_key}_{mode}_{exp.name}.txt"

                    with log_path.open("w", encoding="utf-8") as log_f:
                        for idx, item in enumerate(test_data):
                            t0 = time.perf_counter()

                            # 執行 RAG 生成回答
                            res = _rag_answer_with_retry(
                                rag,
                                bot_uuid=bot_uuid,
                                query_text=item["question"],
                                model_name=model,
                                top_k=3,
                                fetch_k=(15 if exp.use_rerank else 3),
                                score_threshold=_score_threshold_for_mode(mode),
                                retrieval_mode=mode,
                                use_rerank=exp.use_rerank,
                                use_rewrite=False,
                                use_summary_in_rewrite=False,
                            )

                            dur = time.perf_counter() - t0
                            hits = res.get("hits", [])
                            ans = str(res.get("answer", "")).strip()
                            gt = item["ground_truth"]

                            # 儲存到結果列表 (JSON 結構)
                            results.append({
                                "question": item["question"],
                                "contexts": _contexts_for_ragas(hits),
                                "answer": ans,
                                "ground_truth": gt,
                            })

                            # 組合即時 Log 訊息並輸出到終端機
                            msg = f"[{idx + 1}/{len(test_data)}] {dur:.2f}s | Q: {item['question']}\n"
                            msg += f"GT: {gt}\n"
                            msg += "Hits:\n"
                            msg += (
                                "\n".join(_preview_hit(h) for h in hits[:3])
                                + f"\nA: {ans}\n"
                                + "-" * 50
                                + "\n"
                            )
                            print(msg)

                            # 寫入 Log 檔案並強制 Flush (邊跑邊寫)
                            log_f.write(msg + "\n")
                            log_f.flush()

                    # 跑完該實驗組後儲存 JSON 給 Ragas 評測
                    save_json(
                        results,
                        out_dir / f"ragas_eval_{model}_{d_key}_{mode}_{exp.name}.json",
                    )


if __name__ == "__main__":
    main()
