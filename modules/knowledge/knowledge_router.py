from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile

from modules.knowledge.knowledge_model import KnowledgeListView
from modules.knowledge.knowledge_schema import (
    DeleteKnowledgeRequest,
    InsertKnowledgeRequest,
    KnowledgeSyncStatusResponse,
    TriggerSyncRequest,
    UpdateKnowledgeRequest,
)
from modules.knowledge.knowledge_service import KnowledgeService
from shared.clients.database import SessionDep
from shared.dependencies import BotAccessController, get_bot_access


def get_knowledge_service(session: SessionDep) -> KnowledgeService:
    """依賴注入 KnowledgeService"""
    return KnowledgeService(session)


knowledge_router = APIRouter(prefix="/knowledges", tags=["knowledges"])


@knowledge_router.get("/{bot_uuid}", response_model=List[KnowledgeListView])
def get_all_knowledges(
    bot_uuid: UUID,
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 僅限 Owner，不檢查 Module
    bot = access.verify(bot_uuid, owner_only=True)
    return knowledge_service.get_all_knowledge_list(bot)


# --- 變更為 async 以支援 Mongo 更新 ---


@knowledge_router.post("")
async def insert_knowledge(
    body: InsertKnowledgeRequest,
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 1. 驗證權限
    bot = access.verify(body.bot_uuid, owner_only=True)

    # 2. 執行 SQL 寫入
    knowledge_service.insert_single_knowledge(bot, body)
    knowledge_service.session.commit()

    # 3. 更新 Sync Status (MongoDB)
    await knowledge_service.mark_as_pending(bot.bot_detail_id)


@knowledge_router.post("/upload")
async def insert_knowledge_by_file(
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
    bot_uuid: UUID = Form(),
    csv_file: UploadFile = File(),
):
    bot = access.verify(bot_uuid, owner_only=True)

    knowledge_service.insert_knowledges_by_csv(bot, csv_file)
    knowledge_service.session.commit()

    await knowledge_service.mark_as_pending(bot.bot_detail_id)


@knowledge_router.delete("")
async def delete_knowledges(
    body: DeleteKnowledgeRequest,
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    bot = access.verify(body.bot_uuid, owner_only=True)

    knowledge_service.delete_knowledges_by_bot_class_id(bot, body.deleted_id_list)
    knowledge_service.session.commit()

    await knowledge_service.mark_as_pending(bot.bot_detail_id)


@knowledge_router.patch("")
async def update_knowledge(
    body: UpdateKnowledgeRequest,
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    bot = access.verify(body.bot_uuid, owner_only=True)

    knowledge_service.update_knowledge(bot, body)
    knowledge_service.session.commit()

    await knowledge_service.mark_as_pending(bot.bot_detail_id)


@knowledge_router.get(
    "/{bot_uuid}/sync-status", response_model=KnowledgeSyncStatusResponse
)
async def get_knowledge_sync_status(
    bot_uuid: UUID,
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 讀取權限即可
    access.verify(bot_uuid, owner_only=True)
    return await knowledge_service.get_sync_status(bot_uuid)


@knowledge_router.post("/sync")
async def trigger_knowledge_sync(
    body: TriggerSyncRequest,
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 僅限 Owner
    bot = access.verify(body.bot_uuid, owner_only=True)
    await knowledge_service.trigger_sync(bot)
