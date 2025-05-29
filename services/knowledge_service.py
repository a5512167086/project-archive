import pandas as pd
import psycopg2
from fastapi import UploadFile

from commands.knowledge_command import (
    delete_knowledge_items,
    insert_knowledge_item,
    insert_knowledge_items,
)
from exception import GlobalErrorException
from queries.knowledge_query import (
    get_all_knowledge_items_by_class_id,
    get_knowledge_class_id_by_bot_class_id,
)
from schemas.knowledge_schema import InsertKnowledgeRequest


def handle_database_error(error: psycopg2.Error, bot_class_id: int):
    error_message = error.diag.message_primary
    if f"Error: 找不到 {bot_class_id} 底下的 Knowledge Class" in error_message:
        raise GlobalErrorException(
            error_code="KNOWLEDGE_CLASS_NOT_FOUND",
            error_message="Knowledge class not found for the given bot class",
        )
    raise GlobalErrorException(
        error_code="DATABASE_ERROR",
        error_message="Database error occurred",
    )


def validate_knowledge_class(bot_class_id: int) -> int:
    knowledge_class_id = get_knowledge_class_id_by_bot_class_id(bot_class_id)
    if not knowledge_class_id:
        raise GlobalErrorException(
            error_code="KNOWLEDGE_CLASS_NOT_FOUND",
            error_message="Knowledge class not found for the given bot class",
        )
    return knowledge_class_id


def validate_csv_file(file: UploadFile):
    if file.content_type != "text/csv":
        raise GlobalErrorException(
            error_code="INVALID_FILE_TYPE",
            error_message="The uploaded file must be a CSV",
        )
    knowledge_dataframe = pd.read_csv(file.file)
    if (
        "question" not in knowledge_dataframe.columns
        or "answer" not in knowledge_dataframe.columns
    ):
        raise GlobalErrorException(
            error_code="INVALID_CSV_FORMAT",
            error_message="The CSV file must have columns 'question' and 'answer'",
        )
    knowledge_list = knowledge_dataframe.to_dict(orient="records")
    return knowledge_list


def insert_single_knowledge(body: InsertKnowledgeRequest):
    validate_knowledge_class(body.bot_class_id)
    try:
        insert_knowledge_item(body.bot_class_id, body.question, body.answer)
    except psycopg2.Error as error:
        handle_database_error(error, body.bot_class_id)


def insert_knowledge_by_csv(bot_class_id: int, csv_file: UploadFile):
    knowledge_list = validate_csv_file(csv_file)
    validate_knowledge_class(bot_class_id)
    try:
        insert_knowledge_items(bot_class_id, knowledge_list)
    except psycopg2.Error as error:
        handle_database_error(error, bot_class_id)


def get_all_knowledge_list(bot_class_id: int):
    knowledge_class_id = validate_knowledge_class(bot_class_id)
    return get_all_knowledge_items_by_class_id(knowledge_class_id)


def delete_knowledges_by_bot_class_id(bot_class_id: int, deleted_id_list: list):
    if not deleted_id_list:
        raise GlobalErrorException(
            error_code="EMPTY_DELETE_LIST",
            error_message="No items to delete",
        )
    try:
        return delete_knowledge_items(bot_class_id, deleted_id_list)
    except psycopg2.Error as error:
        handle_database_error(error, bot_class_id)
