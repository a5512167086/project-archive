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
from app.services.llm_service import LLMFactory
from app.services.vector_service import VectorService


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup: Loading models...")

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

    app.state.embedding_model = embedding_model
    app.state.chat_model = chat_model
    print(f"Embedding model '{EMBEDDING_MODEL}' loaded successfully on {device}.")
    print(f"Chat model '{CHAT_MODEL}' loaded successfully on {device}.")

    # 初始化工廠時，傳入預載的 chat_model
    llm_factory = LLMFactory(chat_model=app.state.chat_model)
    app.state.llm_factory = llm_factory
    print("LLMFactory initialized.")

    # 預載指定的 LLM 服務 (已移除 ollama_local)
    await asyncio.to_thread(llm_factory.get_service, "gpt_o4_azure")
    print("Pre-loaded LLM services: gpt_o4_azure.")
    print("--- Models loaded. Application is ready. ---")

    yield

    print("Application shutdown: Clearing resources.")
    app.state.embedding_model = None
    app.state.llm_factory = None
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


app = FastAPI(root_path="/easybot-rag-api", lifespan=lifespan)


def get_sentence_transformer_model(request: Request) -> HuggingFaceEmbeddings:
    return request.app.state.embedding_model


def get_llm_factory(request: Request) -> LLMFactory:
    return request.app.state.llm_factory


def get_vector_service_singleton(
    model: Annotated[HuggingFaceEmbeddings, Depends(get_sentence_transformer_model)],
) -> VectorService:
    print("Initializing VectorService singleton...")
    return VectorService(model=model)


def get_knowledge_service(session: SessionDep) -> KnowledgeService:
    return KnowledgeService(session)


@app.post("/ingest")
def ingest(
    req: IngestRequest,
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    vector_service: Annotated[VectorService, Depends(get_vector_service_singleton)],
):
    sync_results = knowledge_service.sync_knowledge_vectors(
        req.bot_uuid, vector_service
    )

    return {
        "bot_uuid": str(req.bot_uuid),
        "upserted": sync_results["upserted"],
        "deleted": sync_results["deleted"],
        "collection": vector_service.collection,
    }


@app.post("/query", response_model=QueryResponse)
async def query(
    req: QueryRequest,
    vector_service: Annotated[VectorService, Depends(get_vector_service_singleton)],
    llm_factory: Annotated[LLMFactory, Depends(get_llm_factory)],
):
    hits = vector_service.search_faq(
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

    tasks = []
    for model_name in req.models:
        llm_service = llm_factory.get_service(model_name)
        task = asyncio.to_thread(
            llm_service.generate, user_query=req.query, contexts=hits
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    answers_dict = {
        model_name: result for model_name, result in zip(req.models, results)
    }

    return QueryResponse(
        answers=answers_dict,
        hits=[
            QueryHit(**{k: v for k, v in h.items() if k in QueryHit.model_fields})
            for h in hits
        ],
    )
