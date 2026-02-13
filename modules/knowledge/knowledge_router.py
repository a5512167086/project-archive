from typing import Annotated, List
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import StreamingResponse

from modules.knowledge.knowledge_model import KnowledgeListView
from modules.knowledge.knowledge_schema import (
    DeleteKnowledgeFileRequest,
    DeleteKnowledgeRequest,
    InsertKnowledgeRequest,
    KnowledgeFileResponse,
    KnowledgeSyncStatusResponse,
    TriggerSyncRequest,
    UpdateKnowledgeFileRequest,
    UpdateKnowledgeRequest,
)
from modules.knowledge.knowledge_service import KnowledgeService
from shared.clients.database import SessionDep
from shared.dependencies import BotAccessController, get_bot_access


def get_knowledge_service(session: SessionDep) -> KnowledgeService:
    return KnowledgeService(session)


knowledge_router = APIRouter(prefix="/knowledges", tags=["knowledges"])


@knowledge_router.get("/{bot_uuid}", response_model=List[KnowledgeListView])
def get_all_knowledges(
    bot_uuid: UUID,
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    bot = access.verify(bot_uuid, owner_only=True)
    return knowledge_service.get_all_knowledge_list(bot)


@knowledge_router.post("")
async def insert_knowledge(
    body: InsertKnowledgeRequest,
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    bot = access.verify(body.bot_uuid, owner_only=True)

    knowledge_service.insert_single_knowledge(bot, body)
    knowledge_service.session.commit()

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
    access.verify(bot_uuid, owner_only=True)
    return await knowledge_service.get_sync_status(bot_uuid)


@knowledge_router.post("/sync")
async def trigger_knowledge_sync(
    body: TriggerSyncRequest,
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    bot = access.verify(body.bot_uuid, owner_only=True)
    await knowledge_service.trigger_sync(bot)


@knowledge_router.get("/files/{bot_uuid}", response_model=List[KnowledgeFileResponse])
def get_all_knowledge_files(
    bot_uuid: UUID,
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    bot = access.verify(bot_uuid, owner_only=True)
    return knowledge_service.get_all_knowledge_files(bot)


@knowledge_router.post("/files")
async def upload_knowledge_files(
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
    bot_uuid: UUID = Form(),
    files: List[UploadFile] = File(),
):
    bot = access.verify(bot_uuid, owner_only=True)

    knowledge_service.upload_knowledge_files(bot, files)
    knowledge_service.session.commit()

    await knowledge_service.mark_as_pending(bot.bot_detail_id)


@knowledge_router.patch("/files")
async def update_knowledge_file(
    body: UpdateKnowledgeFileRequest,
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    bot = access.verify(body.bot_uuid, owner_only=True)

    knowledge_service.update_knowledge_file(
        bot=bot,
        file_id=body.file_id,
        display_name=body.display_name,
    )
    knowledge_service.session.commit()

    await knowledge_service.mark_as_pending(bot.bot_detail_id)


@knowledge_router.delete("/files")
async def delete_knowledge_files(
    body: DeleteKnowledgeFileRequest,
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    bot = access.verify(body.bot_uuid, owner_only=True)

    knowledge_service.delete_knowledge_files(bot=bot, file_id_list=body.file_id_list)
    knowledge_service.session.commit()

    await knowledge_service.mark_as_pending(bot.bot_detail_id)


@knowledge_router.get("/{bot_uuid}/files/{file_id}/download")
def download_knowledge_file(
    bot_uuid: UUID,
    file_id: int,
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    bot = access.verify(bot_uuid, owner_only=True)
    row, obj = knowledge_service.open_knowledge_file_stream(bot, file_id)

    def iter_stream():
        try:
            for chunk in obj.stream(1024 * 1024):
                yield chunk
        finally:
            obj.close()
            obj.release_conn()

    filename = row.display_name or row.filename
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"

    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"}
    return StreamingResponse(
        iter_stream(), media_type="application/pdf", headers=headers
    )
