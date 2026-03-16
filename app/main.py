from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Tuple

from fastapi import BackgroundTasks, Depends, FastAPI, Request
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
from app.database import SessionDep
from app.exception import add_global_exception_handler
from app.logger import logger
from app.schemas import (
    IngestRequest,
    PurgeRequest,
    PurgeResponse,
    QueryHit,
    QueryRequest,
    QueryResponse,
)
from app.services.knowledge_service import KnowledgeService
from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService
from app.services.rag_service import RAGService
from app.services.reranker_service import RerankerService
from app.services.retrieval_service import RetrievalService
from app.services.rewrite_service import RewriteService
from app.services.summary_service import SummaryService
from app.services.vector_service import VectorService
from app.utils.summary_memory import SummaryMemory

BASE_DIR = Path(__file__).resolve().parent.parent
STOPWORDS_PATH = f"{BASE_DIR}/data/stopwords.txt"


def build_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model=OLLAMA_EMBED_NAME,
        base_url=OLLAMA_BASE_URL,
    )


def build_vector_service(embeddings: OllamaEmbeddings) -> VectorService:
    return VectorService(
        embeddings=embeddings,
        qdrant_url=QDRANT_URL,
        collection_name=QDRANT_COLLECTION,
        timeout=RAGService.DEFAULT_TIMEOUT,
        ensure_collection_and_indexes=True,
    )


def build_summary_memory(llm_service: LLMService) -> SummaryMemory:
    return SummaryMemory(
        mongo_uri=MONGODB_URI,
        mongo_db_name=MONGODB_DB_NAME,
        mongo_collection=MONGODB_CHAT_COLLECTION,
        get_llm=llm_service.get_llm,
        summary_model="local_model",
        summary_trigger_threshold=6,
        max_summary_messages=30,
        refresh_min_interval_sec=60,
        refresh_every_n_new_msgs=4,
    )


def build_services(
    embeddings: OllamaEmbeddings,
) -> Tuple[RAGService, RetrievalService, VectorService]:
    llm_service = LLMService()
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
        use_summary=True,
    )
    retrieval_service = RetrievalService(
        vector_service=vector_service,
        bm25_enabled=True,
        bm25_refresh_ttl_sec=300,
        stopwords_path=STOPWORDS_PATH,
        debug_log_hits=True,
        debug_log_top_n=30,
    )
    rag_service = RAGService(
        embeddings=embeddings,
        llm_service=llm_service,
        prompt_service=prompt_service,
        reranker_service=reranker_service,
        summary_service=summary_service,
        rewrite_service=rewrite_service,
        retrieval_service=retrieval_service,
        memory=summary_memory,
    )

    return rag_service, retrieval_service, vector_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    embeddings = build_embeddings()

    rag_service, retrieval_service, vector_service = build_services(
        embeddings=embeddings,
    )

    app.state.rag_service = rag_service
    app.state.retrieval_service = retrieval_service
    app.state.vector_service = vector_service

    try:
        yield
    finally:
        app.state.rag_service = None
        app.state.retrieval_service = None
        app.state.vector_service = None


def get_rag_service(request: Request) -> RAGService:
    rag = request.app.state.rag_service
    if rag is None:
        raise RuntimeError("RAG service not initialized.")
    return rag


def get_vector_service(request: Request) -> VectorService:
    vs = request.app.state.vector_service
    if vs is None:
        raise RuntimeError("Vector service not initialized.")
    return vs


def get_retrieval_service(request: Request) -> RetrievalService:
    rs = request.app.state.retrieval_service
    if rs is None:
        raise RuntimeError("Retrieval service not initialized.")
    return rs


def get_knowledge_service(session: SessionDep) -> KnowledgeService:
    return KnowledgeService(session)


app = FastAPI(root_path="/easybot-rag-api", lifespan=lifespan)
add_global_exception_handler(app)


@app.post("/ingest")
def ingest(
    req: IngestRequest,
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    vector_service: Annotated[VectorService, Depends(get_vector_service)],
    retrieval_service: Annotated[RetrievalService, Depends(get_retrieval_service)],
):
    sync_results = knowledge_service.sync_knowledge_vectors(
        req.bot_uuid, vector_service
    )

    retrieval_service.refresh_index(req.bot_uuid)

    return {
        "bot_uuid": str(req.bot_uuid),
        "upserted": sync_results["upserted"],
        "deleted": sync_results["deleted"],
        "collection": vector_service.collection,
    }


@app.post("/query", response_model=QueryResponse)
async def query(
    req: QueryRequest,
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
    background_tasks: BackgroundTasks,
):
    start_total = time.perf_counter()

    result = await asyncio.to_thread(
        rag_service.answer,
        bot_uuid=req.bot_uuid,
        line_id=req.line_id,
        query_text=req.query,
        model_name=req.model,
        top_k=req.top_k,
        fetch_k=req.fetch_k,
        score_threshold=req.score_threshold,
        history_rounds=5,
        rewrite_model="local_model",
        max_history_messages=rag_service.DEFAULT_MAX_HISTORY_MESSAGES,
        use_rewrite=True,
        use_summary_in_rewrite=True,
        retrieval_mode="hybrid",
        use_rerank=True,
    )

    hits = result.get("hits", []) or []
    final_answer = result.get("answer", "") or ""

    logger.info(
        f"[Timer] Total Request: {(time.perf_counter() - start_total):.3f}s | Hits={len(hits)}"
    )

    if not hits:
        return QueryResponse(
            answer="很抱歉，目前無法找到相關的回答",
            hits=[],
        )

    if req.line_id:
        session_key = f"{req.bot_uuid}:{req.line_id}"
        background_tasks.add_task(
            rag_service.summary_service.maybe_update_summary, session_key
        )
    clean_hits = []
    for h in hits:
        item_type = h.get("type", "qa")

        if item_type == "file":
            final_content = str(h.get("content") or "").strip()
        else:
            q = str(h.get("question") or "").strip()
            a = str(h.get("answer") or "").strip()
            final_content = f"Q: {q}\nA: {a}".strip() if a else f"Q: {q}"

        if not final_content:
            continue

        clean_hits.append(
            QueryHit(
                id=str(h.get("id", "")),
                score=float(h.get("score", 0.0)),
                rerank_score=h.get("rerank_score"),
                content=final_content,
            )
        )

    return QueryResponse(
        answer=final_answer,
        hits=clean_hits,
    )


@app.post("/purge", response_model=PurgeResponse)
def purge_bot_vectors(
    req: PurgeRequest,
    vector_service: Annotated[VectorService, Depends(get_vector_service)],
    retrieval_service: Annotated[RetrievalService, Depends(get_retrieval_service)],
):
    ok = vector_service.delete_all_by_bot_uuid(req.bot_uuid)
    retrieval_service.refresh_index(req.bot_uuid)

    return PurgeResponse(
        bot_uuid=req.bot_uuid,
        collection=vector_service.collection,
        deleted=bool(ok),
    )
