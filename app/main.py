import asyncio
import time
from contextlib import asynccontextmanager
from typing import Annotated, cast

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
)
from app.database import SessionDep
from app.logger import logger
from app.schemas import IngestRequest, QueryHit, QueryRequest, QueryResponse
from app.services.knowledge_service import KnowledgeService
from app.services.memory.summary import MongoSummaryMemory
from app.services.rag_service import RAGService


@asynccontextmanager
async def lifespan(app: FastAPI):
    device = 0 if torch.cuda.is_available() else -1

    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": device},
        cache_folder="../cache",
    )

    chat_pipeline = HuggingFacePipeline.from_model_id(
        task="text-generation",
        model_id=CHAT_MODEL,
        device=device,
        model_kwargs={"torch_dtype": torch.bfloat16},
        pipeline_kwargs={"max_new_tokens": 512},
    )
    chat_model = ChatHuggingFace(llm=chat_pipeline)

    rag = RAGService(
        embeddings=embedding_model,
        preloaded_hf_chat_model=chat_model,
        ensure_collection_and_indexes=True,
    )

    # Memory: cache-only load + background summary update
    rag.memory = MongoSummaryMemory(
        mongo_uri=MONGODB_URI,
        mongo_db_name=MONGODB_DB_NAME,
        mongo_collection=MONGODB_CHAT_COLLECTION,
        get_llm=rag._get_llm,
        summary_model="gpt_5_mini",
        summary_trigger_threshold=6,
        max_summary_messages=30,
        refresh_min_interval_sec=60,  # 1 分鐘內不重算
        refresh_every_n_new_msgs=4,  # 新增>=4則 human/ai 才重算
    )

    app.state.rag_service = rag
    yield

    app.state.rag_service = None
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


app = FastAPI(root_path="/easybot-rag-api", lifespan=lifespan)


def get_rag_service(request: Request) -> RAGService:
    return request.app.state.rag_service


def get_knowledge_service(session: SessionDep) -> KnowledgeService:
    return KnowledgeService(session)


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
        "collection": rag.collection,
    }


@app.post("/query", response_model=QueryResponse)
async def query(
    req: QueryRequest,
    rag: Annotated[RAGService, Depends(get_rag_service)],
    background_tasks: BackgroundTasks,
):
    start_total = time.perf_counter()

    # 1) Search + Rewrite
    start_search = time.perf_counter()
    final_query, hits = rag.search_history_aware(
        bot_uuid=req.bot_uuid,
        line_id=req.line_id,
        query_text=req.query,
        top_k=req.top_k,
        score_threshold=req.score_threshold,
        history_rounds=5,
        rewrite_model="gpt_5_mini",
    )
    search_duration = time.perf_counter() - start_search
    logger.info(
        f"[Timer] 1. Search & Rewrite: {search_duration:.3f}s | Hits: {len(hits)}"
    )

    if not hits:
        logger.info(
            f"[Timer] Total (No Hits): {time.perf_counter() - start_total:.3f}s"
        )
        return QueryResponse(
            answers={"default": "抱歉，知識庫目前沒有足夠資訊可以回答這個問題。"},
            hits=[],
        )

    # 2) Generate
    start_gen = time.perf_counter()
    answer = await asyncio.to_thread(
        rag.generate,
        req.bot_uuid,
        req.line_id,
        req.query,  # original_query
        final_query,  # rewritten_query
        hits,
        req.model,
    )
    gen_duration = time.perf_counter() - start_gen
    logger.info(f"[Timer] 2. Generation: {gen_duration:.3f}s")

    # 3) Background summary update (NOT in critical path)
    if req.line_id:
        session_key = f"{req.bot_uuid}:{req.line_id}"
        mem = cast(MongoSummaryMemory, rag.memory)
        background_tasks.add_task(mem.maybe_update_summary, session_key)

    total_duration = time.perf_counter() - start_total
    logger.info(f"[Timer] === Total Request: {total_duration:.3f}s ===")

    return QueryResponse(
        answers={req.model: answer},
        hits=[
            QueryHit(**{k: v for k, v in h.items() if k in QueryHit.model_fields})
            for h in hits
        ],
    )
