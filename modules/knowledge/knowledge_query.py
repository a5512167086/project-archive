import logging
from typing import List

from sqlmodel import Session, select

from modules.knowledge.knowledge_model import KnowledgeListView
from shared.models.class_model import SubClassView
from shared.queries.entity_query import get_entity_id_by_name

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class KnowledgeQuery:
    def __init__(self, session: Session):
        self.session = session

    def get_knowledge_class_id_by_bot_class_id(self, bot_class_id: int) -> int | None:
        knowledge_entity_id = get_entity_id_by_name(self.session, "知識")
        result = self.session.exec(
            select(SubClassView.class_id).where(
                SubClassView.parent_class_id == bot_class_id,
                SubClassView.entity_id == knowledge_entity_id,
            )
        ).first()
        return result

    def get_all_knowledge_items_by_class_id(
        self, class_id: int
    ) -> List[KnowledgeListView]:
        statement = select(KnowledgeListView).where(
            KnowledgeListView.class_id == class_id
        )
        result = self.session.exec(statement)
        return result.all()
