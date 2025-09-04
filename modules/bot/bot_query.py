import logging
from typing import List
from uuid import UUID

from sqlmodel import Session, select

from modules.bot.bot_model import BotListView, BotListWithCredentialView
from shared.models.inheritance_model import Inheritance

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


class BotQuery:
    def __init__(self, session: Session):
        self.session = session

    def get_all_bots_by_user_id(self, user_id: UUID) -> List[BotListView]:
        logger.info(f"Fetching all bots for user_id: {user_id}")
        statement = select(BotListView).where(BotListView.owner_id == user_id)
        bot_list = self.session.exec(statement).all()
        logger.info(f"Successfully fetched {len(bot_list)} bots for user_id: {user_id}")
        return bot_list

    def get_bot_by_uuid(self, bot_uuid: UUID) -> BotListWithCredentialView | None:
        logger.info(f"Fetching bot details for bot_id: {bot_uuid}")
        statement = select(BotListWithCredentialView).where(
            BotListWithCredentialView.bot_detail_id == bot_uuid
        )
        bot_data = self.session.exec(statement).first()
        if not bot_data:
            return None

        return bot_data

    def get_all_bot_subclasses(self, parent_class_id: int) -> List[int]:
        stmt = select(Inheritance.parent_class_id, Inheritance.child_class_id)
        rows = self.session.exec(stmt).all()

        parent_to_children = {}
        for parent_id, child_id in rows:
            parent_to_children.setdefault(parent_id, []).append(child_id)

        visited = set()
        result = []

        def dfs(current_id: int):
            if current_id in visited:
                return
            visited.add(current_id)

            for child_id in parent_to_children.get(current_id, []):
                result.append(child_id)
                dfs(child_id)

        dfs(parent_class_id)

        return result

    def get_line_bot_credentials(
        self, bot_uuid: UUID
    ) -> BotListWithCredentialView | None:
        logger.info(f"Fetching credentials for bot_uuid: {bot_uuid}")
        stmt = select(BotListWithCredentialView).where(
            BotListWithCredentialView.bot_detail_id == bot_uuid
        )
        result = self.session.exec(stmt).first()

        if result:
            logger.info(
                f"Successfully fetched credentials for bot_uuid: {str(bot_uuid)}"
            )
        else:
            logger.warning(f"No credentials found for bot_uuid: {bot_uuid}")

        return result
