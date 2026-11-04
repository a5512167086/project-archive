from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class KnowledgeListView(SQLModel, table=True):
    __tablename__ = "vs_knowledge_list"

    class_id: int = Field(primary_key=True)
    object_id: int = Field(primary_key=True)
    question: str
    answer: Optional[str]


class KnowledgeFileListView(SQLModel, table=True):
    __tablename__ = "vs_knowledge_file_list"

    class_id: int = Field(primary_key=True)
    file_id: int = Field(primary_key=True)
    object_id: int
    filename: str
    display_name: str
    file_type: str
    created_at: Optional[datetime] = None
