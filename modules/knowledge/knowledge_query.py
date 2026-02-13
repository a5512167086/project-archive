import logging
from typing import List, Optional

from sqlmodel import Session, select

from modules.knowledge.knowledge_model import KnowledgeFileListView, KnowledgeListView
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
        self, knowledge_class_id: int
    ) -> List[KnowledgeListView]:
        statement = select(KnowledgeListView).where(
            KnowledgeListView.class_id == knowledge_class_id
        )
        result = self.session.exec(statement)
        return result.all()

    def get_knowledge_item_by_id(
        self, knowledge_class_id, knowledge_id: int
    ) -> KnowledgeListView | None:
        statement = select(KnowledgeListView).where(
            KnowledgeListView.object_id == knowledge_id,
            KnowledgeListView.class_id == knowledge_class_id,
        )
        result = self.session.exec(statement)
        return result.one_or_none()

    def get_all_knowledge_files_by_class_id(
        self, class_id: int
    ) -> List[KnowledgeFileListView]:
        stmt = select(KnowledgeFileListView).where(
            KnowledgeFileListView.class_id == class_id
        )
        return self.session.exec(stmt).all()

    def get_knowledge_file_view_by_id(
        self, class_id: int, file_id: int
    ) -> Optional[KnowledgeFileListView]:
        stmt = select(KnowledgeFileListView).where(
            KnowledgeFileListView.class_id == class_id,
            KnowledgeFileListView.file_id == file_id,
        )
        return self.session.exec(stmt).one_or_none()

    def get_knowledge_file_views_by_ids(
        self, class_id: int, file_ids: List[int]
    ) -> List[KnowledgeFileListView]:
        stmt = select(KnowledgeFileListView).where(
            KnowledgeFileListView.class_id == class_id,
            KnowledgeFileListView.file_id.in_(file_ids),
        )
        return self.session.exec(stmt).all()
