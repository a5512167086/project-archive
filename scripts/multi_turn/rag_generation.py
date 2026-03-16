from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
from uuid import UUID

from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings
from pymongo import MongoClient

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
    use_rewrite: bool


EXPERIMENTS: List[ExpConfig] = [
    ExpConfig(name="baseline", use_rerank=False, use_rewrite=False),
    ExpConfig(name="baseline_rewrite", use_rerank=False, use_rewrite=True),
    ExpConfig(name="rerank", use_rerank=True, use_rewrite=False),
    ExpConfig(name="rerank_rewrite", use_rerank=True, use_rewrite=True),
]

RETRIEVAL_MODES: List[str] = [
    "hybrid",
    "vector",
    "lexical",
]

DATASET_CONFIG: Dict[str, Dict[str, str]] = {
    "rag_multiturn": {
        "path": "./data/testset/rag_multiturn_testset.json",
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
    if mode == "vector":
        return 0.4
    if mode == "hybrid":
        return 0.0
    return 0.0


def load_multiturn_data(path: str) -> Dict[str, List[Dict[str, Any]]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


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
        display_text = f"檔案：{source} | 內容：{content}"
    else:
        q = str(h.get("question", "")).replace("\n", " ").strip()
        a = str(h.get("answer", "")).replace("\n", " ").strip()
        display_text = f"FAQ Q: {q} | A: {a}"

    return f"- {score_str} | {display_text}"


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
# Database Cleanup Helper
# -----------------------------
def cleanup_eval_memory(session_keys: List[str]):
    """清理 MongoDB 中測試產生的所有對話歷史與摘要"""
    if not session_keys:
        return

    print(f"\n{'=' * 60}\n🧹 開始清理 MongoDB 測試 Memory...\n{'=' * 60}")
    try:
        client = MongoClient(MONGODB_URI)
        db = client[MONGODB_DB_NAME]
        collection = db[MONGODB_CHAT_COLLECTION]

        # Langchain 的 MongoDBChatMessageHistory 預設使用 SessionId 作為 key
        result = collection.delete_many({"SessionId": {"$in": session_keys}})

        print(f"✅ 成功清理 {result.deleted_count} 筆測試 Memory 紀錄！")
    except Exception as e:
        print(f"❌ 清理 Memory 失敗: {e}")
    finally:
        client.close()


# -----------------------------
# Core Wrapper
# -----------------------------
def _rag_answer_with_retry(rag: RAGService, **kwargs) -> Dict[str, Any]:
    max_attempts = kwargs.pop("max_attempts", 5)
    for attempt in range(1, max_attempts + 1):
        try:
            return rag.answer(rerank_threshold=0.0, **kwargs)
        except Exception as e:
            if attempt == max_attempts:
                raise e
            time.sleep(1.5 * attempt)


def build_services(embeddings):
    llm_service = LLMService()
    prompt_service = PromptService(max_contexts_for_prompt=5)
    vs = VectorService(embeddings, QDRANT_URL, QDRANT_COLLECTION)
    rs = RetrievalService(vs, stopwords_path=STOPWORDS_PATH)
    mem = SummaryMemory(
        MONGODB_URI,
        MONGODB_DB_NAME,
        MONGODB_CHAT_COLLECTION,
        llm_service.get_llm,
        summary_trigger_threshold=6,
        max_summary_messages=30,
        refresh_min_interval_sec=60,
        refresh_every_n_new_msgs=4,
    )
    ss = SummaryService(mem)
    rerank_s = RerankerService()
    rewrite_s = RewriteService(llm_service.get_llm, ss, use_summary=True)

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

    out_dir = Path("./data/eval_dataset/multi_turn")
    out_dir.mkdir(parents=True, exist_ok=True)

    eval_session_keys = set()

    for d_key, cfg in DATASET_CONFIG.items():
        bot_uuid = UUID(cfg["bot_uuid"])
        sessions_dict = load_multiturn_data(cfg["path"])
        rs.refresh_index(bot_uuid)

        for model in MODELS_TO_RUN:
            for mode in RETRIEVAL_MODES:
                for exp in EXPERIMENTS:
                    print(f"\n>>> Running: {mode} | {exp.name} | {model}")
                    results = []
                    log_path = out_dir / f"runlog_{model}_{d_key}_{mode}_{exp.name}.txt"

                    with log_path.open("w", encoding="utf-8") as log_f:
                        for session_id, turns in sessions_dict.items():
                            unique_line_id = f"eval_{session_id}_{int(time.time())}"
                            session_key = f"{bot_uuid}:{unique_line_id}"

                            # 記錄下來以便後續刪除
                            eval_session_keys.add(session_key)

                            log_f.write(
                                f"\n{'=' * 60}\n[Session Start] {session_id} (line_id: {unique_line_id})\n{'=' * 60}\n"
                            )
                            print(f"\n{'=' * 40}\n[Session] {session_id}\n{'=' * 40}")

                            for turn_data in turns:
                                turn_num = turn_data.get("turn")
                                question = turn_data.get("question")
                                gt = turn_data.get("answer")
                                intent = turn_data.get("intent")

                                t0 = time.perf_counter()

                                res = _rag_answer_with_retry(
                                    rag,
                                    bot_uuid=bot_uuid,
                                    line_id=unique_line_id,
                                    query_text=question,
                                    model_name=model,
                                    top_k=5,
                                    fetch_k=(30 if exp.use_rerank else 5),
                                    score_threshold=_score_threshold_for_mode(mode),
                                    retrieval_mode=mode,
                                    use_rerank=exp.use_rerank,
                                    use_rewrite=exp.use_rewrite,
                                    use_summary_in_rewrite=True,
                                    history_rounds=5,
                                    rewrite_model="local_model",
                                )

                                dur = time.perf_counter() - t0
                                hits = res.get("hits", [])
                                ans = str(res.get("answer", "")).strip()

                                rag.summary_service.maybe_update_summary(session_key)

                                results.append({
                                    "session_id": session_id,
                                    "turn": turn_num,
                                    "intent": intent,
                                    "question": question,
                                    "contexts": _contexts_for_ragas(hits),
                                    "answer": ans,
                                    "ground_truth": gt,
                                })

                                msg = f"  -> Turn {turn_num} ({intent}) | {dur:.2f}s | Q: {question}\n"
                                msg += f"     GT: {gt}\n"
                                msg += "     Hits:\n"
                                msg += (
                                    (
                                        "\n".join(
                                            "       " + _preview_hit(h) for h in hits
                                        )
                                        + "\n"
                                    )
                                    if hits
                                    else "       (No hits)\n"
                                )
                                msg += f"     A:  {ans}\n"
                                msg += "  " + "-" * 50

                                print(msg)
                                log_f.write(msg + "\n")
                                log_f.flush()

                    save_json(
                        results,
                        out_dir / f"ragas_eval_{model}_{d_key}_{mode}_{exp.name}.json",
                    )

    # 執行清理腳本，刪除 MongoDB 中的髒資料
    cleanup_eval_memory(list(eval_session_keys))


if __name__ == "__main__":
    main()
