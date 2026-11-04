from datetime import datetime, timezone
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


class KnowledgeFile(SQLModel, table=True):
    __tablename__ = "knowledge_files"

    file_id: Optional[int] = Field(default=None, primary_key=True)
    object_id: int = Field(index=True, foreign_key="objects.object_id")
    filename: str = Field(index=True, unique=True)
    display_name: str
    file_type: str = Field(default="pdf")
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class KnowledgeFileListView(SQLModel, table=True):
    __tablename__ = "vs_knowledge_file_list"

    class_id: int = Field(primary_key=True)
    file_id: int = Field(primary_key=True)
    object_id: int
    filename: str
    display_name: str
    file_type: str
    created_at: Optional[datetime] = None


class KnowledgeVectorDBStatus(Document):
    bot_uuid: Annotated[str, Indexed(unique=True)]
    status: SyncStatus = SyncStatus.COMPLETED
    has_pending_changes: bool = False
    last_sync_start_time: Optional[datetime] = None
    last_sync_end_time: Optional[datetime] = None
    last_successful_sync_time: Optional[datetime] = None

    class Settings:
        name = "knowledge_vector_db_status"
