from typing import Optional

from sqlmodel import Field, SQLModel


class KnowledgeListView(SQLModel, table=True):
    __tablename__ = "vs_knowledge_list"

    class_id: int = Field(primary_key=True)
    object_id: int = Field(primary_key=True)
    question: str
    answer: Optional[str]
