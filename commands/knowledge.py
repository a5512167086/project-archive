import json
import logging
from typing import List

import psycopg2
import psycopg2.extras

from database import get_db_connection

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def insert_knowledge_item(bot_class_id: int, question: str, answer: str):
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "CALL sp_insert_knowledge_item(%s, %s, %s);",
                    [bot_class_id, question, answer],
                )
                connection.commit()
                logger.info(
                    "Knowledge item inserted successfully for bot_class_id: %s",
                    bot_class_id,
                )
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        logger.error("Database error: %s", error_message)
        raise


def insert_knowledge_items(bot_class_id: int, knowledge_items: List[dict]):
    try:
        knowledge_items_jsonb = json.dumps(knowledge_items)
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "CALL sp_insert_knowledge_items(%s, %s::jsonb);",
                    [bot_class_id, knowledge_items_jsonb],
                )
                connection.commit()
                logger.info(
                    "Knowledge items inserted successfully for bot_class_id: %s",
                    bot_class_id,
                )
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        logger.error("Database error: %s", error_message)
        raise
