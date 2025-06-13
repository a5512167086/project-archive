from typing import List

from fastapi import APIRouter, File, Form, UploadFile

from database import SessionDep
from models.object_model import KnowledgeListView
from schemas.knowledge_schema import DeleteKnowledgeRequest, InsertKnowledgeRequest
from services.knowledge_service import (
    delete_knowledges_by_bot_class_id,
    get_all_knowledge_list,
    insert_knowledges_by_csv,
    insert_single_knowledge,
)

knowledge_router = APIRouter(prefix="/knowledges", tags=["knowledges"])


@knowledge_router.get("/{bot_class_id}", response_model=List[KnowledgeListView])
def get_all_knowledges(session: SessionDep, bot_class_id: int):
    return get_all_knowledge_list(session, bot_class_id)


@knowledge_router.post("")
def insert_knowledge(session: SessionDep, body: InsertKnowledgeRequest):
    insert_single_knowledge(session, body)
    session.commit()


@knowledge_router.post("/upload")
def insert_knowledge_by_file(
    session: SessionDep, bot_class_id: int = Form(), csv_file: UploadFile = File()
):
    insert_knowledges_by_csv(session, bot_class_id, csv_file)


@knowledge_router.delete("")
def delete_knowledges(session: SessionDep, body: DeleteKnowledgeRequest):
    delete_knowledges_by_bot_class_id(session, body.bot_class_id, body.deleted_id_list)
    session.commit()
