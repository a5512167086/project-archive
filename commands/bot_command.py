import logging
from typing import List

import psycopg2
import psycopg2.extras
from sqlmodel import Session, select

from database import get_db_connection
from models.bot_detail_model import BotDetail
from models.object_model import Object
from schemas.bot_schema import InsertBotRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def insert_new_bot(user_id: str, new_bot: InsertBotRequest, liff_id: str):
    logger.info(f"Inserting new bot for user_id: {user_id} with data: {new_bot}")
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "SELECT * FROM fs_insert_bot(%s, %s, %s, %s, %s, %s, %s, %s);",
                    [
                        new_bot.bot_name,
                        new_bot.bot_channel_id,
                        new_bot.bot_channel_access_token,
                        new_bot.bot_channel_secret,
                        new_bot.bot_login_channel_id,
                        new_bot.bot_login_channel_secret,
                        liff_id,
                        user_id,
                    ],
                )
                new_bot_data = cursor.fetchone()
                connection.commit()
                logger.info(f"New bot inserted successfully: {new_bot_data}")
                return new_bot_data
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        logger.error(f"Error inserting new bot: {error_message}")
        raise


def delete_bot_by_id(
    delete_bot_id: int, bot_object_id: int, bot_subclass_id_list: List[int]
):
    logger.info(
        f"Deleting bot with delete_bot_id: {delete_bot_id}, bot_object_id: {bot_object_id}, "
        f"bot_subclass_id_list: {bot_subclass_id_list}"
    )
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute("CALL sp_delete_class(%s);", [delete_bot_id])
                logger.info(f"Deleted bot class with ID: {delete_bot_id}")

                cursor.execute("CALL sp_delete_object(%s);", [bot_object_id])
                logger.info(f"Deleted bot object with ID: {bot_object_id}")

                for bot_subclass_id in bot_subclass_id_list:
                    cursor.execute("CALL sp_delete_class(%s);", [bot_subclass_id])
                    logger.info(f"Deleted bot subclass with ID: {bot_subclass_id}")

                connection.commit()
                logger.info("All related bot data deleted successfully")
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        logger.error(f"Error deleting bot: {error_message}")
        raise


def update_bot_by_id(session: Session, bot_object_id: int, update_bot: dict):
    logger.info(
        f"Updating bot with bot_object_id: {bot_object_id} and data: {update_bot}"
    )

    if "bot_name" in update_bot:
        stmt = select(Object).where(Object.object_id == bot_object_id)
        obj = session.exec(stmt).first()
        if obj:
            obj.chinese_name = update_bot["bot_name"]
            logger.info(f"Updated bot name for object_id: {bot_object_id}")
        update_bot.pop("bot_name")

    if update_bot:
        stmt = select(BotDetail).where(BotDetail.object_id == bot_object_id)
        detail = session.exec(stmt).first()
        if detail:
            for key, value in update_bot.items():
                if hasattr(detail, key):
                    setattr(detail, key, value)
            logger.info(
                f"Updated bot details for object_id: {bot_object_id} with fields: {list(update_bot.keys())}"
            )

    logger.info(f"Bot with object_id: {bot_object_id} updated successfully")
