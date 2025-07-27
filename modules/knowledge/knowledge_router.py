from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile

from modules.knowledge.knowledge_model import KnowledgeListView
from modules.knowledge.knowledge_schema import (
    DeleteKnowledgeRequest,
    InsertKnowledgeRequest,
    UpdateKnowledgeRequest,
)
from modules.knowledge.knowledge_service import KnowledgeService
from shared.clients.database import SessionDep
from shared.dependencies import get_current_user


def get_knowledge_service(session: SessionDep) -> KnowledgeService:
    """依賴注入 KnowledgeService"""
    return KnowledgeService(session)


knowledge_router = APIRouter(prefix="/knowledges", tags=["knowledges"])


@knowledge_router.get("/{bot_uuid}", response_model=List[KnowledgeListView])
def get_all_knowledges(
    bot_uuid: UUID,
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
):
    return knowledge_service.get_all_knowledge_list(bot_uuid)


@knowledge_router.post("")
def insert_knowledge(
    body: InsertKnowledgeRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
):
    user_id = current_user["user_id"]
    knowledge_service.insert_single_knowledge(body, user_id)
    knowledge_service.session.commit()


@knowledge_router.post("/upload")
def insert_knowledge_by_file(
    current_user: Annotated[dict, Depends(get_current_user)],
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    bot_uuid: UUID = Form(),
    csv_file: UploadFile = File(),
):
    user_id = current_user["user_id"]
    knowledge_service.insert_knowledges_by_csv(bot_uuid, csv_file, user_id)
    knowledge_service.session.commit()


@knowledge_router.delete("")
def delete_knowledges(
    body: DeleteKnowledgeRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
):
    user_id = current_user["user_id"]
    knowledge_service.delete_knowledges_by_bot_class_id(
        body.bot_uuid, body.deleted_id_list, user_id
    )
    knowledge_service.session.commit()


@knowledge_router.patch("")
def update_knowledge(
    body: UpdateKnowledgeRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
):
    user_id = current_user["user_id"]
    knowledge_service.update_knowledge(body, user_id)
    knowledge_service.session.commit()
