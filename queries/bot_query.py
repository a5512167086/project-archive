import logging
from typing import List
from uuid import UUID

from sqlmodel import Session, select

from models.bot_detail_model import BotListView, BotListWithCredentialView
from models.inheritance_model import Inheritance

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def get_all_bots_by_user_id(session: Session, user_id: str) -> List[BotListView]:
    logger.info(f"Fetching all bots for user_id: {user_id}")
    statement = select(BotListView).where(BotListView.owner_id == user_id)
    bot_list = session.exec(statement).all()
    logger.info(f"Successfully fetched {len(bot_list)} bots for user_id: {user_id}")
    return bot_list


def get_bot_by_uuid(
    session: Session, bot_uuid: UUID
) -> BotListWithCredentialView | None:
    logger.info(f"Fetching bot details for bot_id: {bot_uuid}")
    statement = select(BotListWithCredentialView).where(
        BotListWithCredentialView.bot_detail_id == bot_uuid
    )
    bot_data = session.exec(statement).first()
    if not bot_data:
        return None

    return bot_data


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
