import logging

import psycopg2
import psycopg2.extras

from database import get_db_connection

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_knowledge_class_id_by_bot_class_id(bot_class_id: int):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT child_class_id FROM vs_sub_class \
                    WHERE class_id = %s\
                    AND entity_id = 8;",
                    [bot_class_id],
                )
                knowledge_class_id = cursor.fetchone()

                return knowledge_class_id
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        logger.error("Database error: %s", error_message)


def get_all_knowledge_items_by_class_id(class_id: int):
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "SELECT * FROM vs_knowledge_list \
                    WHERE class_id = %s;",
                    [class_id],
                )
                knowledge_items = cursor.fetchall()

                return knowledge_items
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        logger.error("Database error: %s", error_message)
