from uuid import UUID

from sqlmodel import Session, select

from app.logger import logger
from app.models.bot_model import BotListView


class BotQuery:
    def __init__(self, session: Session):
        self.session = session

    def get_bot_by_uuid(self, bot_uuid: UUID) -> BotListView | None:
        logger.info(f"Fetching bot details for bot_id: {bot_uuid}")
        statement = select(BotListView).where(BotListView.bot_detail_id == bot_uuid)
        bot_data = self.session.exec(statement).first()
        if not bot_data:
            return None

        return bot_data
