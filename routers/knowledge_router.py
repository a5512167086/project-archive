from fastapi import APIRouter, File, Form, UploadFile

from schemas.knowledge_schema import DeleteKnowledgeRequest, InsertKnowledgeRequest
from services.knowledge_service import (
    delete_knowledges_by_bot_class_id,
    get_all_knowledge_list,
    insert_knowledge_by_csv,
    insert_single_knowledge,
)

knowledge_router = APIRouter()


@knowledge_router.get("/knowledge/{bot_class_id}", tags=["knowledges"])
def get_all_knowledges(bot_class_id: int):
    return get_all_knowledge_list(bot_class_id)


@knowledge_router.post("/knowledge", tags=["knowledges"])
def insert_knowledge(body: InsertKnowledgeRequest):
    insert_single_knowledge(body)


@knowledge_router.post("/knowledge/upload", tags=["knowledges"])
def insert_knowledge_by_file(bot_class_id: int = Form(), csv_file: UploadFile = File()):
    insert_knowledge_by_csv(bot_class_id, csv_file)


@knowledge_router.delete("/knowledge", tags=["knowledges"])
def delete_knowledges(body: DeleteKnowledgeRequest):
    return delete_knowledges_by_bot_class_id(body.bot_class_id, body.deleted_id_list)
