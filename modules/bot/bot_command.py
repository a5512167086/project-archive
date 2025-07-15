import logging
from typing import List

from sqlmodel import Session, delete, select, text

from modules.bot.bot_model import BotDetail
from shared.models.class_object_relation_model import ClassObjectRelation
from shared.models.object_model import Object
from modules.bot.bot_schema import InsertBotRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


class BotCommand:
    def __init__(self, session: Session):
        self.session = session

    def insert_new_bot(self, user_id: str, new_bot: InsertBotRequest, liff_id: str):
        logger.info(f"Inserting new bot for user_id: {user_id} with data: {new_bot}")

        result = self.session.exec(
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
        self,
        delete_bot_id: int,
        bot_object_id: int,
        bot_subclass_id_list: List[int],
    ):
        logger.info(
            f"Deleting bot with delete_bot_id: {delete_bot_id}, bot_object_id: {bot_object_id}, "
            f"bot_subclass_id_list: {bot_subclass_id_list}"
        )
        for bot_subclass_id in bot_subclass_id_list:
            related_objects = self.session.exec(
                select(ClassObjectRelation.object_id).where(
                    ClassObjectRelation.class_id == bot_subclass_id
                )
            ).all()

            if related_objects:
                self.session.exec(
                    delete(ClassObjectRelation).where(
                        ClassObjectRelation.class_id == bot_subclass_id
                    )
                )
                logger.info(
                    f"Deleted class_object_relations for bot_subclass_id: {bot_subclass_id}"
                )

                self.session.exec(delete(Object).where(Object.object_id.in_(related_objects)))
                logger.info(
                    f"Deleted {len(related_objects)} objects for bot_subclass_id: {bot_subclass_id}"
                )

        self.session.exec(
            text("CALL sp_delete_class(:delete_bot_id)").bindparams(
                delete_bot_id=delete_bot_id
            )
        )
        logger.info(f"Deleted bot class with ID: {delete_bot_id}")

        self.session.exec(
            text("CALL sp_delete_object(:bot_object_id)").bindparams(
                bot_object_id=bot_object_id
            )
        )
        logger.info(f"Deleted bot object with ID: {bot_object_id}")

        for bot_subclass_id in bot_subclass_id_list:
            self.session.exec(
                text("CALL sp_delete_class(:bot_subclass_id)").bindparams(
                    bot_subclass_id=bot_subclass_id
                )
            )
            logger.info(f"Deleted bot subclass with ID: {bot_subclass_id}")

        logger.info("All related bot data deleted successfully")

    def update_bot_by_id(self, bot_object_id: int, update_bot: dict):
        logger.info(
            f"Updating bot with bot_object_id: {bot_object_id} and data: {update_bot}"
        )

        if "bot_name" in update_bot:
            stmt = select(Object).where(Object.object_id == bot_object_id)
            obj = self.session.exec(stmt).first()
            if obj:
                obj.chinese_name = update_bot["bot_name"]
                logger.info(f"Updated bot name for object_id: {bot_object_id}")
            update_bot.pop("bot_name")

        if update_bot:
            stmt = select(BotDetail).where(BotDetail.object_id == bot_object_id)
            detail = self.session.exec(stmt).first()
            if detail:
                for key, value in update_bot.items():
                    if hasattr(detail, key):
                        setattr(detail, key, value)
                logger.info(
                    f"Updated bot details for object_id: {bot_object_id} with fields: {list(update_bot.keys())}"
                )

        logger.info(f"Bot with object_id: {bot_object_id} updated successfully")