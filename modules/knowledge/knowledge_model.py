from datetime import datetime
from typing import Annotated, Optional

from beanie import Document, Indexed
from sqlmodel import Field, SQLModel

from shared.constants.common import SyncStatus


class KnowledgeListView(SQLModel, table=True):
    __tablename__ = "vs_knowledge_list"

    class_id: int = Field(primary_key=True)
    object_id: int = Field(primary_key=True)
    question: str
    answer: Optional[str]


class KnowledgeVectorDBStatus(Document):
    bot_uuid: Annotated[str, Indexed(unique=True)]
    status: SyncStatus = SyncStatus.COMPLETED
    has_pending_changes: bool = False
    last_sync_start_time: Optional[datetime] = None
    last_sync_end_time: Optional[datetime] = None
    last_successful_sync_time: Optional[datetime] = None

    class Settings:
        name = "knowledge_vector_db_status"
