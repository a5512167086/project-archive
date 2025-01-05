import logging

import psycopg2
import psycopg2.extras

from database import get_db_connection

# 設定 logging 配置
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def insert_faq_item(bot_class_id: int, question: str, answer: str):
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "CALL sp_insert_faq_item(%s, %s, %s);",
                    [bot_class_id, question, answer],
                )
                connection.commit()
                logger.info(
                    "FAQ item inserted successfully for bot_class_id: %s", bot_class_id
                )
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        logger.error("Database error: %s", error_message)
        raise
