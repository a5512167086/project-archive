from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile

from modules.knowledge.knowledge_model import KnowledgeListView
from modules.knowledge.knowledge_schema import (
    DeleteKnowledgeRequest,
    InsertKnowledgeRequest,
)
from modules.knowledge.knowledge_service import (
    delete_knowledges_by_bot_class_id,
    get_all_knowledge_list,
    insert_knowledges_by_csv,
    insert_single_knowledge,
)
from shared.database import SessionDep
from shared.dependencies import get_current_user

knowledge_router = APIRouter(prefix="/knowledges", tags=["knowledges"])


@knowledge_router.get("/{bot_uuid}", response_model=List[KnowledgeListView])
def get_all_knowledges(session: SessionDep, bot_uuid: UUID):
    return get_all_knowledge_list(session, bot_uuid)


@knowledge_router.post("")
def insert_knowledge(
    session: SessionDep,
    body: InsertKnowledgeRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    insert_single_knowledge(session, body, user_id)
    session.commit()


@knowledge_router.post("/upload")
def insert_knowledge_by_file(
    session: SessionDep,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_uuid: UUID = Form(),
    csv_file: UploadFile = File(),
):
    user_id = current_user["user_id"]
    insert_knowledges_by_csv(session, bot_uuid, csv_file, user_id)
    session.commit()


@knowledge_router.delete("")
def delete_knowledges(
    session: SessionDep,
    body: DeleteKnowledgeRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    delete_knowledges_by_bot_class_id(
        session, body.bot_uuid, body.deleted_id_list, user_id
    )
    session.commit()
