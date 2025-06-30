import logging
from typing import List

from sqlmodel import Session, delete, select, text

from models.bot_detail_model import BotDetail
from models.class_object_relation_model import ClassObjectRelation
from models.object_model import Object
from schemas.bot_schema import InsertBotRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def insert_new_bot(
    session: Session, user_id: str, new_bot: InsertBotRequest, liff_id: str
):
    logger.info(f"Inserting new bot for user_id: {user_id} with data: {new_bot}")

    result = session.exec(
        text(
            "SELECT * FROM fs_insert_bot(:bot_name, :bot_channel_id, :bot_channel_access_token, :bot_channel_secret, "
            ":bot_login_channel_id, :bot_login_channel_secret, :liff_id, :user_id)"
        ).bindparams(
            bot_name=new_bot.bot_name,
            bot_channel_id=new_bot.bot_channel_id,
            bot_channel_access_token=new_bot.bot_channel_access_token,
            bot_channel_secret=new_bot.bot_channel_secret,
            bot_login_channel_id=new_bot.bot_login_channel_id,
            bot_login_channel_secret=new_bot.bot_login_channel_secret,
            liff_id=liff_id,
            user_id=user_id,
        )
    ).mappings()
    new_bot_data = result.first()
    logger.info(f"New bot inserted successfully: {new_bot_data}")
    return new_bot_data


def delete_bot_by_id(
    session: Session,
    delete_bot_id: int,
    bot_object_id: int,
    bot_subclass_id_list: List[int],
):
    logger.info(
        f"Deleting bot with delete_bot_id: {delete_bot_id}, bot_object_id: {bot_object_id}, "
        f"bot_subclass_id_list: {bot_subclass_id_list}"
    )
    # Delete objects related to bot subclasses
    for bot_subclass_id in bot_subclass_id_list:
        # Get all object_ids related to this bot_subclass_id
        related_objects = session.exec(
            select(ClassObjectRelation.object_id).where(
                ClassObjectRelation.class_id == bot_subclass_id
            )
        ).all()

        if related_objects:
            # Delete class_object_relations
            session.exec(
                delete(ClassObjectRelation).where(
                    ClassObjectRelation.class_id == bot_subclass_id
                )
            )
            logger.info(
                f"Deleted class_object_relations for bot_subclass_id: {bot_subclass_id}"
            )

            # Delete the objects
            session.exec(delete(Object).where(Object.object_id.in_(related_objects)))
            logger.info(
                f"Deleted {len(related_objects)} objects for bot_subclass_id: {bot_subclass_id}"
            )

    # Delete bot class
    session.exec(
        text("CALL sp_delete_class(:delete_bot_id)").bindparams(
            delete_bot_id=delete_bot_id
        )
    )
    logger.info(f"Deleted bot class with ID: {delete_bot_id}")

    # Delete bot object
    session.exec(
        text("CALL sp_delete_object(:bot_object_id)").bindparams(
            bot_object_id=bot_object_id
        )
    )
    logger.info(f"Deleted bot object with ID: {bot_object_id}")

    # Delete bot subclasses
    for bot_subclass_id in bot_subclass_id_list:
        session.exec(
            text("CALL sp_delete_class(:bot_subclass_id)").bindparams(
                bot_subclass_id=bot_subclass_id
            )
        )
        logger.info(f"Deleted bot subclass with ID: {bot_subclass_id}")

    logger.info("All related bot data deleted successfully")


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
