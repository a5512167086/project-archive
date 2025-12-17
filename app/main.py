import asyncio
from contextlib import asynccontextmanager
from typing import Annotated

import torch
from fastapi import Depends, FastAPI, Request
from langchain_huggingface import (
    ChatHuggingFace,
    HuggingFaceEmbeddings,
    HuggingFacePipeline,
)

from app.configs.config import CHAT_MODEL, EMBEDDING_MODEL
from app.database import SessionDep
from app.schemas import IngestRequest, QueryHit, QueryRequest, QueryResponse
from app.services.knowledge_service import KnowledgeService
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

    app.state.rag_service = RAGService(
        embeddings=embedding_model,
        preloaded_hf_chat_model=chat_model,
        ensure_collection_and_indexes=True,
    )

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
):
    # 檢索只做一次
    hits = rag.search_faq(
        bot_uuid=req.bot_uuid,
        query_text=req.query,
        top_k=req.top_k,
        score_threshold=req.score_threshold,
    )

    if not hits:
        return QueryResponse(
            answers={"default": "抱歉，知識庫目前沒有足夠資訊可以回答這個問題。"},
            hits=[],
        )

    # 多模型並行生成（不重跑檢索）
    tasks = [
        asyncio.to_thread(rag.generate, req.query, hits, model_name=model_name)
        for model_name in req.models
    ]
    results = await asyncio.gather(*tasks)

    answers_dict = {m: r for m, r in zip(req.models, results)}

    return QueryResponse(
        answers=answers_dict,
        hits=[
            QueryHit(**{k: v for k, v in h.items() if k in QueryHit.model_fields})
            for h in hits
        ],
    )
