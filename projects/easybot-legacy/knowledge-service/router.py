from fastapi import APIRouter, File, Form, UploadFile

from schemas import DeleteKnowledgeRequest, InsertKnowledgeRequest
from services.knowledge import (
    delete_knowledges_by_bot_class_id,
    get_all_knowledge_list,
    insert_knowledge_by_csv,
    insert_single_knowledge,
)

router = APIRouter()


@router.get("/knowledge/{bot_class_id}", tags=["knowledge"])
def get_all_knowledges(bot_class_id: int):
    return get_all_knowledge_list(bot_class_id)


@router.post("/knowledge", tags=["knowledge"])
def insert_knowledge(body: InsertKnowledgeRequest):
    insert_single_knowledge(body)


@router.post("/knowledge/upload", tags=["knowledge"])
def insert_knowledge_by_file(bot_class_id: int = Form(), csv_file: UploadFile = File()):
    insert_knowledge_by_csv(bot_class_id, csv_file)


@router.delete("/knowledge", tags=["knowledge"])
def delete_knowledges(body: DeleteKnowledgeRequest):
    return delete_knowledges_by_bot_class_id(body.bot_class_id, body.deleted_id_list)


@router.post("/knowledge/query", tags=["bot"])
def knowledge_query():
    return ""
