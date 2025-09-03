from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile

from modules.bot.bot_service import BotService
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


def get_bot_service(session: SessionDep) -> BotService:
    """依賴注入 BotService"""
    return BotService(session)


knowledge_router = APIRouter(prefix="/knowledges", tags=["knowledges"])


@knowledge_router.get("/{bot_uuid}", response_model=List[KnowledgeListView])
def get_all_knowledges(
    bot_uuid: UUID,
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    bot = bot_service.validate_line_bot_exists(bot_uuid)
    return knowledge_service.get_all_knowledge_list(bot)


@knowledge_router.post("")
def insert_knowledge(
    body: InsertKnowledgeRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    user_id = current_user["user_id"]
    bot = bot_service.validate_line_bot_exists(body.bot_uuid)
    bot_service.validate_bot_ownership(user_id, bot.bot_detail_id)
    knowledge_service.insert_single_knowledge(bot, body)
    knowledge_service.session.commit()


@knowledge_router.post("/upload")
def insert_knowledge_by_file(
    current_user: Annotated[dict, Depends(get_current_user)],
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
    bot_uuid: UUID = Form(),
    csv_file: UploadFile = File(),
):
    user_id = current_user["user_id"]
    bot = bot_service.validate_line_bot_exists(bot_uuid)
    bot_service.validate_bot_ownership(user_id, bot.bot_detail_id)
    knowledge_service.insert_knowledges_by_csv(bot, csv_file)
    knowledge_service.session.commit()


@knowledge_router.delete("")
def delete_knowledges(
    body: DeleteKnowledgeRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    user_id = current_user["user_id"]
    bot = bot_service.validate_line_bot_exists(body.bot_uuid)
    bot_service.validate_bot_ownership(user_id, bot.bot_detail_id)
    knowledge_service.delete_knowledges_by_bot_class_id(bot, body.deleted_id_list)
    knowledge_service.session.commit()


@knowledge_router.patch("")
def update_knowledge(
    body: UpdateKnowledgeRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    user_id = current_user["user_id"]
    bot = bot_service.validate_line_bot_exists(body.bot_uuid)
    bot_service.validate_bot_ownership(user_id, bot.bot_detail_id)
    knowledge_service.update_knowledge(bot, body)
    knowledge_service.session.commit()
