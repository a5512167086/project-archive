# app/main.py
from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Annotated

import torch
from fastapi import BackgroundTasks, Depends, FastAPI, Request
from langchain_huggingface import (
    ChatHuggingFace,
    HuggingFaceEmbeddings,
    HuggingFacePipeline,
)

from app.configs.config import (
    CHAT_MODEL,
    EMBEDDING_MODEL,
    MONGODB_CHAT_COLLECTION,
    MONGODB_DB_NAME,
    MONGODB_URI,
    QDRANT_COLLECTION,
    QDRANT_URL,
)
from app.database import SessionDep
from app.logger import logger
from app.schemas import IngestRequest, QueryHit, QueryRequest, QueryResponse
from app.services.knowledge_service import KnowledgeService
from app.services.llm_service import LLMService

# ---- RAG services ----
from app.services.prompt_service import PromptService
from app.services.rag_service import RAGService
from app.services.reranker_service import RerankerService
from app.services.rewrite_service import RewriteService
from app.services.summary_service import SummaryService
from app.services.vector_service import VectorService

# ---- Memory / Services ----
from app.summary_memory import SummaryMemory


# =========================
# Lifespan: init singletons
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    device = 0 if torch.cuda.is_available() else -1

    # 1) Embeddings (singleton)
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": device},
        cache_folder="../cache",
    )

    # 2) Local HF chat model (optional)
    chat_pipeline = HuggingFacePipeline.from_model_id(
        task="text-generation",
        model_id=CHAT_MODEL,
        device=device,
        model_kwargs={"torch_dtype": torch.bfloat16},
        pipeline_kwargs={"max_new_tokens": 512},
    )
    chat_model = ChatHuggingFace(llm=chat_pipeline)

    # 3) Extracted services (singleton)
    llm_service = LLMService(preloaded_hf_chat_model=chat_model)

    prompt_service = PromptService(
        max_contexts_for_prompt=RAGService.DEFAULT_MAX_CONTEXTS_FOR_PROMPT
    )

    vector_service = VectorService(
        embeddings=embedding_model,
        qdrant_url=QDRANT_URL,
        collection_name=QDRANT_COLLECTION,
        timeout=RAGService.DEFAULT_TIMEOUT,
        ensure_collection_and_indexes=True,
    )

    reranker_service = RerankerService()

    # 4) Memory backend (SummaryMemory: cache-only load + background update)
    #    這個物件同時具備：
    #    - load()/load_recent_only(): 快速讀 recent + cached summary
    #    - append_turn(): 寫入對話
    #    - maybe_update_summary(): 背景更新 summary cache
    summary_memory = SummaryMemory(
        mongo_uri=MONGODB_URI,
        mongo_db_name=MONGODB_DB_NAME,
        mongo_collection=MONGODB_CHAT_COLLECTION,
        get_llm=llm_service.get_llm,
        summary_model="gpt_5_mini",
        summary_trigger_threshold=6,
        max_summary_messages=30,
        refresh_min_interval_sec=60,
        refresh_every_n_new_msgs=4,
    )

    # 5) SummaryService facade
    summary_service = SummaryService(summary_memory)

    # 6) RewriteService
    rewrite_service = RewriteService(
        get_llm=llm_service.get_llm,
        snapshot_loader=summary_service,  # RewriteService 只需要 load()
        use_summary=True,
    )

    # 7) RAG service (singleton)
    #    注意：不要再 rag.memory = xxx 外掛，改成建構時注入
    rag = RAGService(
        embeddings=embedding_model,
        preloaded_hf_chat_model=chat_model,
        llm_service=llm_service,
        prompt_service=prompt_service,
        vector_service=vector_service,
        reranker_service=reranker_service,
        ensure_collection_and_indexes=False,
        summary_service=summary_service,
        rewrite_service=rewrite_service,
        memory=summary_memory,
    )

    app.state.rag_service = rag
    yield

    app.state.rag_service = None
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


app = FastAPI(root_path="/easybot-rag-api", lifespan=lifespan)


# =========================
# Dependencies
# =========================
def get_rag_service(request: Request) -> RAGService:
    rag = request.app.state.rag_service
    if rag is None:
        raise RuntimeError("RAG service not initialized.")
    return rag


def get_knowledge_service(session: SessionDep) -> KnowledgeService:
    return KnowledgeService(session)


# =========================
# Routers in MAIN
# =========================
@app.post("/ingest")
def ingest(
    req: IngestRequest,
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    rag: Annotated[RAGService, Depends(get_rag_service)],
):
    sync_results = knowledge_service.sync_knowledge_vectors(req.bot_uuid, rag)
    return {
        "bot_uuid": str(req.bot_uuid),
        "upserted": sync_results["upserted"],
        "deleted": sync_results["deleted"],
        "collection": rag.vector_service.collection,
    }


@app.post("/query", response_model=QueryResponse)
async def query(
    req: QueryRequest,
    rag: Annotated[RAGService, Depends(get_rag_service)],
    background_tasks: BackgroundTasks,
):
    start_total = time.perf_counter()

    # 把整個 RAG 用例放到 thread，避免阻塞 event loop
    start_answer = time.perf_counter()
    result = await asyncio.to_thread(
        rag.answer,
        bot_uuid=req.bot_uuid,
        line_id=req.line_id,
        query_text=req.query,
        model_name=req.model,
        top_k=req.top_k,
        fetch_k=req.fetch_k,
        score_threshold=req.score_threshold,
        rerank_threshold=req.rerank_threshold,
        history_rounds=5,
        rewrite_model="gpt_5_mini",
        max_history_messages=rag.DEFAULT_MAX_HISTORY_MESSAGES,
    )
    answer_duration = time.perf_counter() - start_answer

    hits = result.get("hits", []) or []
    answer = result.get("answer", "") or ""
    logger.info(
        f"[Timer] 1. Answer(use-case): {answer_duration:.3f}s | Hits: {len(hits)}"
    )

    if not hits:
        logger.info(
            f"[Timer] Total (No Hits): {time.perf_counter() - start_total:.3f}s"
        )
        return QueryResponse(
            answers={"default": "抱歉，知識庫目前沒有足夠資訊可以回答這個問題。"},
            hits=[],
        )

    # Background summary update (改成走 summary_service)
    if req.line_id:
        session_key = f"{req.bot_uuid}:{req.line_id}"
        background_tasks.add_task(rag.summary_service.maybe_update_summary, session_key)

    total_duration = time.perf_counter() - start_total
    logger.info(f"[Timer] === Total Request: {total_duration:.3f}s ===")

    return QueryResponse(
        answers={req.model: answer},
        hits=[
            QueryHit(**{k: v for k, v in h.items() if k in QueryHit.model_fields})
            for h in hits
        ],
    )
