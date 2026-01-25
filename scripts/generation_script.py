# scripts/generation_script.py
from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple
from uuid import UUID

import httpx
import pandas as pd
import torch
from dotenv import load_dotenv
from langchain_huggingface import (
    ChatHuggingFace,
    HuggingFaceEmbeddings,
    HuggingFacePipeline,
)
from qdrant_client.http.exceptions import ResponseHandlingException

from app.configs.config import (
    CHAT_MODEL,
    EMBEDDING_MODEL,
    MONGODB_CHAT_COLLECTION,
    MONGODB_DB_NAME,
    MONGODB_URI,
    QDRANT_COLLECTION,
    QDRANT_URL,
)
from app.database import get_session
from app.services.knowledge_service import KnowledgeService
from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService
from app.services.rag_service import RAGService
from app.services.reranker_service import RerankerService
from app.services.retrieval_service import RetrievalService
from app.services.rewrite_service import RewriteService
from app.services.summary_service import SummaryService
from app.services.vector_service import VectorService
from app.summary_memory import SummaryMemory

# -----------------------------
# Paths (align with FastAPI)
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent  # repo root
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
    ExpConfig(name="rerank", use_rerank=True, use_rewrite=False),
    ExpConfig(name="rewrite", use_rerank=False, use_rewrite=True),
    ExpConfig(name="rerank_rewrite", use_rerank=True, use_rewrite=True),
]

# retrieval modes to test (align with RetrievalService.search(mode=...))
RETRIEVAL_MODES: List[str] = [
    "hybrid",
    "vector",
    "lexical",
]


# -----------------------------
# Dataset & model configs
# -----------------------------
DATASET_CONFIG: Dict[str, Dict[str, str]] = {
    "wke_opt": {
        "path": "./data/testset/wke_faq_testset.csv",
        "bot_uuid": "b2608f4e-037f-4d33-a222-d7af9d9032d1",
    },
}

MODELS_TO_RUN: List[str] = [
    "gpt_5_mini",
    "gemini_2.5_flash",
    "qwen3_local",
]


# -----------------------------
# IO helpers
# -----------------------------
def load_test_data(faq_dataset_path: str) -> List[Dict[str, str]]:
    df = pd.read_csv(faq_dataset_path)
    test_data: List[Dict[str, str]] = []
    for _, row in df.iterrows():
        q = str(row.get("question", "")).strip()
        a = str(row.get("answer", "")).strip()
        if not q or not a or q.lower() == "nan" or a.lower() == "nan":
            continue
        test_data.append({"question": q, "ground_truth": a})
    print(f"Loaded {len(test_data)} test records from {faq_dataset_path}")
    return test_data


def save_json(results: List[Dict[str, Any]], filename: str) -> None:
    if not results:
        print("No results to save.")
        return
    out_path = Path(filename)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved: {filename} ({len(results)} records)")


def _preview_hit(h: Dict[str, Any], q_max: int = 40, a_max: int = 60) -> str:
    score = h.get("score", 0.0)
    oid = h.get("object_id")
    q = str(h.get("question", "")).strip().replace("\n", " ")
    a = str(h.get("answer", "")).strip().replace("\n", " ")
    if len(q) > q_max:
        q = q[:q_max] + "..."
    if len(a) > a_max:
        a = a[:a_max] + "..."
    return f"- score={float(score):.4f} oid={oid} | Q={q} | A={a}"


def _contexts_for_ragas(hits: List[Dict[str, Any]]) -> List[str]:
    contexts = [
        f"Q: {str(h.get('question', '')).strip()}，A: {str(h.get('answer', '')).strip()}"
        for h in hits
        if (str(h.get("question", "")).strip() or str(h.get("answer", "")).strip())
    ]
    return contexts or ["沒有找到相關的上下文資訊"]


def _score_threshold_for_mode(mode: str) -> float:
    """
    Vector similarity scores often in [0,1], BM25/lexical scores are unbounded and not comparable.
    If you keep 0.7 for lexical, you'll likely filter out everything.
    """
    mode = (mode or "").lower().strip()
    if mode in ("vector", "hybrid"):
        return 0.7
    if mode == "lexical":
        return 0.0
    return 0.0


# -----------------------------
# Qdrant robustness helpers
# -----------------------------
def _is_transient_qdrant_error(e: Exception) -> bool:
    # qdrant_client wraps httpx errors into ResponseHandlingException
    if isinstance(e, ResponseHandlingException):
        return True
    # raw httpx errors (in case they bubble up)
    if isinstance(
        e,
        (
            httpx.RemoteProtocolError,
            httpx.ReadTimeout,
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadError,
        ),
    ):
        return True

    msg = str(e).lower()
    return (
        "server disconnected" in msg
        or "remoteprotocolerror" in msg
        or "connection reset" in msg
        or "broken pipe" in msg
        or "timed out" in msg
    )


def _qdrant_healthcheck(qdrant_url: str, timeout_sec: float = 2.0) -> bool:
    candidates = ["/healthz", "/readyz", "/health"]
    base = qdrant_url.rstrip("/")
    for path in candidates:
        try:
            r = httpx.get(base + path, timeout=timeout_sec)
            if r.status_code == 200:
                return True
        except Exception:
            pass
    return False


def _rag_answer_with_retry(
    rag: RAGService,
    *,
    bot_uuid: UUID,
    question: str,
    model_name: str,
    top_k: int,
    fetch_k: int,
    score_threshold: float,
    retrieval_mode: str,
    use_rerank: bool,
    use_rewrite: bool,
    rewrite_model: str = "gpt_5_mini",
    max_attempts: int = 5,
    base_sleep: float = 1.5,
) -> Dict[str, Any]:
    """
    Retry rag.answer() on transient Qdrant disconnects.
    This prevents the whole script from crashing mid-run.
    """
    last_exc: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return rag.answer(
                bot_uuid=bot_uuid,
                line_id=None,
                query_text=question,
                model_name=model_name,
                top_k=top_k,
                fetch_k=fetch_k,
                score_threshold=score_threshold,
                rerank_threshold=0.0,
                history_rounds=0,
                rewrite_model=rewrite_model,
                max_history_messages=0,
                use_rewrite=use_rewrite,
                use_summary_in_rewrite=False,
                retrieval_mode=retrieval_mode,
                use_rerank=use_rerank,
            )
        except Exception as e:
            last_exc = e
            if (not _is_transient_qdrant_error(e)) or (attempt == max_attempts):
                print(
                    f"[Qdrant] ERROR (non-retriable or max attempts reached) "
                    f"attempt={attempt}/{max_attempts}: {e}"
                )
                raise

            alive = _qdrant_healthcheck(QDRANT_URL)
            sleep_s = base_sleep * (2 ** (attempt - 1)) + random.uniform(0, 0.6)
            if not alive:
                sleep_s = max(sleep_s, 5.0)

            print(
                f"[Qdrant] transient error attempt={attempt}/{max_attempts}: {e} | "
                f"health={alive} | sleep={sleep_s:.1f}s then retry..."
            )
            time.sleep(sleep_s)

    # defensive
    assert last_exc is not None
    raise last_exc


# -----------------------------
# Service builders (match FastAPI)
# -----------------------------
def get_device() -> int:
    return 0 if torch.cuda.is_available() else -1


def build_embeddings(device: int) -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": device},
        cache_folder="./cache",
    )


def build_chat_model(device: int) -> ChatHuggingFace:
    chat_pipeline = HuggingFacePipeline.from_model_id(
        task="text-generation",
        model_id=CHAT_MODEL,
        device=device,
        model_kwargs={"torch_dtype": torch.bfloat16} if device == 0 else {},
        pipeline_kwargs=dict(
            max_new_tokens=1024,
            do_sample=False,
            repetition_penalty=1.03,
            return_full_text=False,
        ),
    )
    return ChatHuggingFace(llm=chat_pipeline)


def build_vector_service(embeddings: HuggingFaceEmbeddings) -> VectorService:
    return VectorService(
        embeddings=embeddings,
        qdrant_url=QDRANT_URL,
        collection_name=QDRANT_COLLECTION,
        timeout=RAGService.DEFAULT_TIMEOUT,
        ensure_collection_and_indexes=True,
    )


def build_summary_memory(llm_service: LLMService) -> SummaryMemory:
    # For offline eval (single-turn), we keep it injected but effectively disabled
    return SummaryMemory(
        mongo_uri=MONGODB_URI,
        mongo_db_name=MONGODB_DB_NAME,
        mongo_collection=MONGODB_CHAT_COLLECTION,
        get_llm=llm_service.get_llm,
        summary_model="gpt_5_mini",
        summary_trigger_threshold=999999,  # disable
        max_summary_messages=30,
        refresh_min_interval_sec=60,
        refresh_every_n_new_msgs=999999,  # disable
    )


def build_services(
    embeddings: HuggingFaceEmbeddings,
    chat_model: ChatHuggingFace,
) -> Tuple[RAGService, RetrievalService]:
    llm_service = LLMService(preloaded_hf_chat_model=chat_model)

    prompt_service = PromptService(
        max_contexts_for_prompt=RAGService.DEFAULT_MAX_CONTEXTS_FOR_PROMPT
    )

    vector_service = build_vector_service(embeddings)
    reranker_service = RerankerService()

    summary_memory = build_summary_memory(llm_service)
    summary_service = SummaryService(summary_memory)

    rewrite_service = RewriteService(
        get_llm=llm_service.get_llm,
        snapshot_loader=summary_service,
        use_summary=True,  # FastAPI is True; single-turn eval will still set use_summary_in_rewrite=False at call-site
    )

    retrieval_service = RetrievalService(
        vector_service=vector_service,
        load_docs=None,
        bm25_enabled=True,
        bm25_refresh_ttl_sec=300,
        stopwords_path=STOPWORDS_PATH,
        debug_log_hits=True,
        debug_log_top_n=30,
    )

    rag_service = RAGService(
        embeddings=embeddings,
        preloaded_hf_chat_model=chat_model,
        llm_service=llm_service,
        prompt_service=prompt_service,
        reranker_service=reranker_service,
        summary_service=summary_service,
        rewrite_service=rewrite_service,
        retrieval_service=retrieval_service,
        memory=summary_memory,
    )

    return rag_service, retrieval_service


def bind_bm25_loader_once(rs: RetrievalService) -> None:
    """
    Bind KnowledgeService.export_knowledge_docs as the BM25 docs loader ONCE.
    This avoids repeatedly opening sessions inside loops.
    """
    gen = get_session()
    session = next(gen)
    try:
        ks = KnowledgeService(session)
        rs.bind_docs_loader(ks.export_knowledge_docs)
    finally:
        # close generator to exit the dependency generator cleanly
        try:
            next(gen)
        except StopIteration:
            pass


# -----------------------------
# Main
# -----------------------------
def main() -> None:
    load_dotenv()

    device = get_device()
    print(f"Device: {'cuda' if device == 0 else 'cpu'}")

    embeddings = build_embeddings(device)
    chat_model = build_chat_model(device)
    rag, rs = build_services(embeddings=embeddings, chat_model=chat_model)

    # Bind BM25 loader once (so lexical/hybrid can build BM25 index)
    bind_bm25_loader_once(rs)

    out_dir = Path("./data/eval_dataset")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Optional pre-run qdrant healthcheck (won't block; just prints)
    is_alive = _qdrant_healthcheck(QDRANT_URL)
    print(f"[Qdrant] health={is_alive} url={QDRANT_URL}")

    for dataset_key, cfg in DATASET_CONFIG.items():
        bot_uuid = UUID(cfg["bot_uuid"])
        test_data = load_test_data(cfg["path"])

        # Optional: Force rebuild BM25 once per bot (ensures index exists before lexical/hybrid)
        rs.refresh_index(bot_uuid)

        for model_name in MODELS_TO_RUN:
            for retrieval_mode in RETRIEVAL_MODES:
                for exp in EXPERIMENTS:
                    print("=" * 80)
                    print(
                        f"Dataset={dataset_key} Bot={bot_uuid} Model={model_name} "
                        f"Retrieval={retrieval_mode} EXP={exp.name}"
                    )
                    print("=" * 80)

                    results: List[Dict[str, Any]] = []

                    runlog_path = out_dir / (
                        f"runlog_{model_name}_{dataset_key}_{retrieval_mode}_{exp.name}.txt"
                    )

                    with runlog_path.open("w", encoding="utf-8") as log_f:
                        for idx, item in enumerate(test_data):
                            question = item["question"]
                            ground_truth = item["ground_truth"]

                            # For rerank experiments, give more candidates to reranker
                            top_k = 3
                            fetch_k = 15 if exp.use_rerank else top_k

                            score_threshold = _score_threshold_for_mode(retrieval_mode)

                            t0 = time.perf_counter()

                            # Robust call (retry on qdrant disconnect)
                            result = _rag_answer_with_retry(
                                rag,
                                bot_uuid=bot_uuid,
                                question=question,
                                model_name=model_name,
                                top_k=top_k,
                                fetch_k=fetch_k,
                                score_threshold=score_threshold,
                                retrieval_mode=retrieval_mode,
                                use_rerank=exp.use_rerank,
                                use_rewrite=exp.use_rewrite,
                                rewrite_model="gpt_5_mini",
                                max_attempts=5,
                                base_sleep=1.5,
                            )

                            elapsed = time.perf_counter() - t0

                            hits = result.get("hits", []) or []
                            answer = (
                                result.get("answer", "") or ""
                            ).strip() or "無法生成回答"

                            contexts_for_ragas = _contexts_for_ragas(hits)

                            top_hits_preview = (
                                "\n".join(_preview_hit(h) for h in hits[:3])
                                or "(no hits)"
                            )

                            msg = (
                                "\n" + "-" * 80 + "\n"
                                f"[{idx + 1}/{len(test_data)}] mode={retrieval_mode} exp={exp.name} "
                                f"model={model_name} time={elapsed:.2f}s\n"
                                f"Q: {question}\n"
                                f"Top hits:\n{top_hits_preview}\n"
                                f"A: {answer}\n"
                                f"GT: {ground_truth}\n" + "-" * 80 + "\n"
                            )

                            print(msg)
                            log_f.write(msg)
                            log_f.flush()

                            # Keep JSON strictly compatible with your RAGAS input
                            results.append({
                                "question": question,
                                "contexts": contexts_for_ragas,
                                "answer": answer,
                                "ground_truth": ground_truth,
                            })

                            if (idx + 1) % 10 == 0:
                                print(f"Processed {idx + 1}/{len(test_data)}")

                            # Avoid Gemini rate limit if enabled later
                            if model_name == "gemini_2.5_flash":
                                time.sleep(6.5)

                    print(f"Saved run log: {runlog_path}")

                    out_json = out_dir / (
                        f"ragas_eval_{model_name}_{dataset_key}_{retrieval_mode}_{exp.name}.json"
                    )
                    save_json(results, str(out_json))

    print("Done.")
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
