from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
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
from app.services.dynamic_prompt_service import DynamicPromptService
from app.services.llm_service import LLMService
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


EXPERIMENTS: List[ExpConfig] = [
    ExpConfig(name="rerank", use_rerank=True),
]

RETRIEVAL_MODES: List[str] = [
    "hybrid",
]

PROMPTS_TO_TEST: List[str] = ["v1", "v2", "v3"]

DATASET_CONFIG: Dict[str, Dict[str, str]] = {
    "rag_testset": {
        "path": "./data/testset/rag_testset.json",
        "bot_uuid": "a6e042eb-7889-4bcb-996c-1845d2215fc2",
    },
}

MODELS_TO_RUN: List[str] = [
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


def load_test_data(path: str) -> List[Dict[str, str]]:
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


def _preview_hit(h: Dict[str, Any]) -> str:
    score_str = f"score={h.get('score', 0):.4f}"
    if h.get("rerank_score"):
        score_str += f" | rerank={h['rerank_score']:.4f}"

    item_type = h.get("type", "qa")
    if item_type == "file":
        source = h.get("display_name") or h.get("filename") or "未知檔案"
        content = str(h.get("content", "")).replace("\n", " ").strip()
        display_text = f"檔案名稱：{source}\n內容：{content}"
    else:
        q = str(h.get("question", "")).replace("\n", " ").strip()
        a = str(h.get("answer", "")).replace("\n", " ").strip()
        display_text = f"問題：{q}\n答案：{a}"

    preview = (display_text[:120] + "...") if len(display_text) > 120 else display_text
    return f"- {score_str} | {preview}"


def _contexts_for_ragas(hits: List[Dict[str, Any]]) -> List[str]:
    contexts = []
    for h in hits:
        item_type = h.get("type", "qa")
        if item_type == "file":
            source = h.get("display_name") or h.get("filename") or "未知檔案"
            content = str(h.get("content", "")).strip()
            if content:
                contexts.append(f"檔案名稱：{source}\n內容：{content}")
        else:
            q = str(h.get("question", "")).strip()
            a = str(h.get("answer", "")).strip()
            if q or a:
                contexts.append(f"問題：{q}\n答案：{a}")
    return contexts


# -----------------------------
# Core Wrapper
# -----------------------------
def _rag_answer_with_retry(rag: RAGService, **kwargs) -> Dict[str, Any]:
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
    # 先隨便給個預設的 PromptService，我們在迴圈內會動態抽換
    prompt_service = DynamicPromptService(prompt_variant="v3")
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

    out_dir = Path("./data/eval_dataset/ab_test")
    out_dir.mkdir(parents=True, exist_ok=True)

    for d_key, cfg in DATASET_CONFIG.items():
        bot_uuid = UUID(cfg["bot_uuid"])
        test_data = load_test_data(cfg["path"])
        rs.refresh_index(bot_uuid)

        for model in MODELS_TO_RUN:
            for mode in RETRIEVAL_MODES:
                for exp in EXPERIMENTS:
                    # 🎯 新增一層迴圈：測試不同的 Prompt
                    for prompt_ver in PROMPTS_TO_TEST:
                        print(
                            f"\n>>> Running: {mode} | {exp.name} | Prompt: {prompt_ver} | {model}"
                        )

                        # ✨ 熱抽換 (Hot-swap) RAG 系統內的 Prompt 服務
                        rag.prompt_service = DynamicPromptService(
                            prompt_variant=prompt_ver
                        )

                        results = []

                        # 檔名加上 prompt_ver 區別
                        log_path = (
                            out_dir
                            / f"runlog_{model}_{d_key}_{mode}_{exp.name}_{prompt_ver}.txt"
                        )

                        with log_path.open("w", encoding="utf-8") as log_f:
                            for idx, item in enumerate(test_data):
                                t0 = time.perf_counter()

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

                                results.append({
                                    "question": item["question"],
                                    "contexts": _contexts_for_ragas(hits),
                                    "answer": ans,
                                    "ground_truth": gt,
                                })

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
                                log_f.write(msg + "\n")
                                log_f.flush()

                        # 儲存 JSON 給 Ragas 評測，檔名包含 prompt_ver
                        save_json(
                            results,
                            out_dir
                            / f"ragas_eval_{model}_{d_key}_{mode}_{exp.name}_{prompt_ver}.json",
                        )


if __name__ == "__main__":
    main()
