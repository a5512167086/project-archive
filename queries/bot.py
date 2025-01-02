import logging

import psycopg2
import psycopg2.extras

from database import get_db_connection

# 設定 logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def get_all_bots_by_user_id(user_id: str):
    logger.info(f"Fetching all bots for user_id: {user_id}")
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "SELECT class_id, object_id, chinese_name, channel_id, owner_id\
                    FROM vs_bot_list \
                    WHERE owner_id = %s;",
                    [user_id],
                )
                bot_list = cursor.fetchall()
                logger.info(
                    f"Successfully fetched {len(bot_list)} bots for user_id: {user_id}"
                )
                return bot_list
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        logger.error(f"Error fetching bots for user_id {user_id}: {error_message}")
        raise


def get_bot_by_id(bot_id: int):
    logger.info(f"Fetching bot details for bot_id: {bot_id}")
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "SELECT class_id, object_id, chinese_name, owner_id \
                    FROM vs_bot_list \
                    WHERE class_id = %s;",
                    [bot_id],
                )
                bot_data = cursor.fetchone()
                if bot_data:
                    logger.info(
                        f"Successfully fetched bot details for bot_id: {bot_id}"
                    )
                else:
                    logger.warning(f"No bot found for bot_id: {bot_id}")
                return bot_data
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        logger.error(f"Error fetching bot details for bot_id {bot_id}: {error_message}")
        raise


def get_bot_subclass(bot_id: int):
    logger.info(f"Fetching subclasses for bot_id: {bot_id}")
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "SELECT * FROM fs_get_child_class(%s);",
                    [bot_id],
                )
                bot_subclass_list = cursor.fetchall()
                logger.info(
                    f"Successfully fetched {len(bot_subclass_list)} subclasses for bot_id: {bot_id}"
                )
                return bot_subclass_list
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        logger.error(f"Error fetching subclasses for bot_id {bot_id}: {error_message}")
        raise


def get_line_bot_credentials(bot_uuid):
    logger.info(f"Fetching credentials for bot_uuid: {bot_uuid}")
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "SELECT class_id, channel_access_token, channel_secret \
                    FROM vs_bot_list_with_credential \
                    WHERE bot_detail_id = %s;",
                    [bot_uuid],
                )
                bot_credentials = cursor.fetchone()
                if bot_credentials:
                    logger.info(
                        f"Successfully fetched credentials for bot_uuid: {bot_uuid}"
                    )
                else:
                    logger.warning(f"No credentials found for bot_uuid: {bot_uuid}")
                return bot_credentials
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        logger.error(
            f"Error fetching credentials for bot_uuid {bot_uuid}: {error_message}"
        )
        raise
