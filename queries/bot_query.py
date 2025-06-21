import logging
from typing import List
from uuid import UUID

from sqlmodel import Session, select

from models.bot_detail_model import BotListView, BotListWithCredentialView
from models.inheritance_model import Inheritance
from schemas.bot_schema import Bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def get_all_bots_by_user_id(session: Session, user_id: str) -> List[Bot]:
    logger.info(f"Fetching all bots for user_id: {user_id}")
    statement = select(BotListView).where(BotListView.owner_id == user_id)
    bot_list = session.exec(statement).all()
    logger.info(f"Successfully fetched {len(bot_list)} bots for user_id: {user_id}")
    return [
        Bot(
            bot_detail_id=bot.bot_detail_id,
            class_id=bot.class_id,
            object_id=bot.object_id,
            bot_name=bot.chinese_name,
            channel_id=bot.channel_id,
            owner_id=bot.owner_id,
        )
        for bot in bot_list
    ]


def get_bot_by_uuid(
    session: Session, bot_uuid: int
) -> BotListWithCredentialView | None:
    logger.info(f"Fetching bot details for bot_id: {bot_uuid}")
    statement = select(BotListWithCredentialView).where(
        BotListWithCredentialView.bot_detail_id == bot_uuid
    )
    bot_data = session.exec(statement).first()
    if not bot_data:
        return None

    return bot_data


def get_bot_by_id(session: Session, bot_id: int) -> Bot | None:
    logger.info(f"Fetching bot details for bot_id: {bot_id}")
    statement = select(BotListView).where(BotListView.class_id == bot_id)
    bot_data = session.exec(statement).first()
    if bot_data:
        logger.info(f"Successfully fetched bot details for bot_id: {bot_id}")
    else:
        logger.warning(f"No bot found for bot_id: {bot_id}")
    return Bot(
        bot_detail_id=bot_data.bot_detail_id,
        class_id=bot_data.class_id,
        object_id=bot_data.object_id,
        bot_name=bot_data.chinese_name,
        channel_id=bot_data.channel_id,
        owner_id=bot_data.owner_id,
    )


def get_bot_subclass(session: Session, bot_class_id: int) -> List[int]:
    logger.info(
        f"Fetching child_class_id from Inheritance for parent_class_id: {bot_class_id}"
    )
    statement = select(Inheritance.child_class_id).where(
        Inheritance.parent_class_id == bot_class_id
    )
    result = session.exec(statement).all()

    logger.info(
        f"Successfully fetched {len(result)} subclasses for parent_class_id: {bot_class_id}"
    )
    return result


def get_line_bot_credentials(
    session: Session, bot_uuid: UUID
) -> BotListWithCredentialView | None:
    logger.info(f"Fetching credentials for bot_uuid: {bot_uuid}")
    stmt = select(BotListWithCredentialView).where(
        BotListWithCredentialView.bot_detail_id == bot_uuid
    )
    result = session.exec(stmt).first()

    if result:
        logger.info(f"Successfully fetched credentials for bot_uuid: {bot_uuid}")
    else:
        logger.warning(f"No credentials found for bot_uuid: {bot_uuid}")

    return result
