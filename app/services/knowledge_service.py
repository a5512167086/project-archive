import logging
from uuid import UUID

from sqlmodel import Session

from app.configs.constans import EntityName, ErrorCode
from app.exception import GlobalErrorException
from app.models.bot_model import BotListView
from app.queries.bot_query import BotQuery
from app.queries.entity_query import EntityQuery
from app.queries.knowledge_query import KnowledgeQuery
from app.services.rag_service import RAGService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


class KnowledgeService:
    def __init__(self, session: Session):
        self.session = session
        self.query = KnowledgeQuery(session)
        self.entity_query = EntityQuery(session)
        self.bot_query = BotQuery(session)

    def validate_line_bot_exists(self, bot_uuid: UUID) -> BotListView | None:
        bot = self.bot_query.get_bot_by_uuid(bot_uuid)
        if not bot:
            raise GlobalErrorException(
                error_code=ErrorCode.BOT_NOT_EXIST,
                error_message="The specified bot does not exist",
            )

        return bot

    def validate_knowledge_class(self, bot_class_id: int) -> int:
        knowledge_entity_id = self.entity_query.get_entity_id_by_name(
            EntityName.KNOWLEDGE
        )
        knowledge_class_id = self.query.get_knowledge_class_id_by_bot_class_id(
            bot_class_id, knowledge_entity_id
        )
        if not knowledge_class_id:
            raise GlobalErrorException(
                error_code=ErrorCode.KNOWLEDGE_CLASS_NOT_FOUND,
                error_message="Knowledge class not found for the given bot class",
            )

        return knowledge_class_id

    def get_all_knowledge_list(self, bot_uuid: UUID):
        bot = self.validate_line_bot_exists(bot_uuid)
        knowledge_class_id = self.validate_knowledge_class(bot.class_id)
        return self.query.get_all_knowledge_items_by_class_id(knowledge_class_id)

    def sync_knowledge_vectors(self, bot_uuid: UUID, rag_service: RAGService) -> dict:
        """
        同步 SQL 資料庫和向量資料庫的知識內容。
        """
        # 1. 從 SQL 獲取最新的完整知識列表
        sql_items = self.get_all_knowledge_list(bot_uuid)
        sql_object_ids = {item.object_id for item in sql_items}
        logger.info(
            f"Found {len(sql_object_ids)} knowledge items in SQL for bot {bot_uuid}."
        )

        # 2. 從 Vector DB 獲取當前儲存的 object_id 列表
        qdrant_object_ids = rag_service.get_object_ids_by_bot_uuid(bot_uuid)

        # 3. 計算需要從 Vector DB 刪除的 ID
        ids_to_delete = list(qdrant_object_ids - sql_object_ids)
        deleted_count = 0
        if ids_to_delete:
            logger.info(f"Found {len(ids_to_delete)} items to delete from Qdrant.")
            rag_service.delete_knowledge_items(bot_uuid, object_ids=ids_to_delete)
            deleted_count = len(ids_to_delete)
        else:
            logger.info("No items need to be deleted from Qdrant.")

        # 4. 將 SQL 中的所有資料 Upsert 到 Vector DB
        # upsert 會自動覆蓋已存在的點，並新增不存在的點
        upserted_count = rag_service.upsert_knowledge_items(bot_uuid, sql_items)

        return {"upserted": upserted_count, "deleted": deleted_count}
