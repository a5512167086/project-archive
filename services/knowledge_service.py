import pandas as pd
from fastapi import UploadFile
from uuid import UUID

from sqlmodel import Session

from commands.knowledge_command import (
    delete_knowledge_items,
    insert_knowledge_item,
    insert_knowledge_items,
)
from constants.error_code import ErrorCode
from exception import GlobalErrorException
from queries.knowledge_query import (
    get_all_knowledge_items_by_class_id,
    get_knowledge_class_id_by_bot_class_id,
)
from schemas.knowledge_schema import InsertKnowledgeRequest
from services.bot_service import get_bot_credential


def validate_knowledge_class(session: Session, bot_uuid: UUID) -> int:
    bot_credentials = get_bot_credential(session, bot_uuid)
    knowledge_class_id = get_knowledge_class_id_by_bot_class_id(session, bot_credentials.class_id)
    if not knowledge_class_id:
        raise GlobalErrorException(
            error_code=ErrorCode.KNOWLEDGE_CLASS_NOT_FOUND,
            error_message="Knowledge class not found for the given bot class",
        )
    return knowledge_class_id


def validate_csv_file(file: UploadFile):
    if file.content_type != "text/csv":
        raise GlobalErrorException(
            error_code=ErrorCode.INVALID_FILE_TYPE,
            error_message="The uploaded file must be a CSV",
        )
    knowledge_dataframe = pd.read_csv(file.file)
    if (
        "question" not in knowledge_dataframe.columns
        or "answer" not in knowledge_dataframe.columns
    ):
        raise GlobalErrorException(
            error_code=ErrorCode.INVALID_CSV_FORMAT,
            error_message="The CSV file must have columns 'question' and 'answer'",
        )
    knowledge_list = knowledge_dataframe.to_dict(orient="records")
    return knowledge_list


def insert_single_knowledge(session: Session, body: InsertKnowledgeRequest):
    knowledge_class_id = validate_knowledge_class(session, body.bot_uuid)
    insert_knowledge_item(session, knowledge_class_id, body.question, body.answer)


def insert_knowledges_by_csv(session: Session, bot_uuid: UUID, csv_file: UploadFile):
    knowledge_list = validate_csv_file(csv_file)
    knowledge_class_id = validate_knowledge_class(session, bot_uuid)
    insert_knowledge_items(session, knowledge_class_id, knowledge_list)


def get_all_knowledge_list(session: Session, bot_uuid: UUID):
    knowledge_class_id = validate_knowledge_class(session, bot_uuid)
    return get_all_knowledge_items_by_class_id(session, knowledge_class_id)


def delete_knowledges_by_bot_class_id(
    session: Session, bot_uuid: UUID, deleted_id_list: list
):
    knowledge_class_id = validate_knowledge_class(session, bot_uuid)
    if not deleted_id_list:
        raise GlobalErrorException(
            error_code=ErrorCode.EMPTY_DELETE_LIST,
            error_message="No items to delete",
        )
    delete_knowledge_items(session, knowledge_class_id, deleted_id_list)
