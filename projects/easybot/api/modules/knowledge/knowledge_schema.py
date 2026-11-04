from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from shared.constants.common import SyncStatus


class InsertKnowledgeRequest(BaseModel):
    bot_uuid: UUID
    question: str
    answer: str


class DeleteKnowledgeRequest(BaseModel):
    bot_uuid: UUID
    deleted_id_list: List[int]


class UpdateKnowledgeRequest(BaseModel):
    bot_uuid: UUID
    object_id: int
    question: str | None = None
    answer: str | None = None


class CreateOrUpdateKnowledgeVectorDBStatus(BaseModel):
    bot_uuid: str
    status: SyncStatus = SyncStatus.COMPLETED
    has_pending_changes: bool = False
    last_sync_start_time: Optional[datetime] = None
    last_sync_end_time: Optional[datetime] = None
    last_successful_sync_time: Optional[datetime] = None


class KnowledgeSyncStatusResponse(BaseModel):
    bot_uuid: str
    status: SyncStatus
    has_pending_changes: bool
    last_sync_start_time: Optional[datetime] = None
    last_sync_end_time: Optional[datetime] = None
    last_successful_sync_time: Optional[datetime] = None


class UploadKnowledgeFileRequest(BaseModel):
    bot_uuid: UUID


class UpdateKnowledgeFileRequest(BaseModel):
    bot_uuid: UUID
    file_id: int
    display_name: Optional[str] = None


class DeleteKnowledgeFileRequest(BaseModel):
    bot_uuid: UUID
    file_id_list: List[int]


class KnowledgeFileResponse(BaseModel):
    class_id: int
    object_id: int
    file_id: int
    filename: str
    display_name: str
    file_type: str
    created_at: Optional[datetime] = None


class TriggerSyncRequest(BaseModel):
    bot_uuid: UUID
