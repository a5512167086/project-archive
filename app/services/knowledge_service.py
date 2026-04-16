import logging
from uuid import UUID

from sqlmodel import Session

from app.configs.constans import EntityName, ErrorCode
from app.exception import GlobalErrorException
from app.models.bot_model import BotListView
from app.models.knowledge_model import KnowledgeFileListView, KnowledgeListView
from app.queries.bot_query import BotQuery
from app.queries.entity_query import EntityQuery
from app.queries.knowledge_query import KnowledgeQuery
from app.services.storage_service import StorageService
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)


class KnowledgeService:
    def __init__(self, session: Session):
        self.session = session
        self.query = KnowledgeQuery(session)
        self.entity_query = EntityQuery(session)
        self.bot_query = BotQuery(session)
        self.storage_service = StorageService()

    def validate_line_bot_exists(self, bot_uuid: UUID) -> BotListView:
        bot = self.bot_query.get_bot_by_uuid(bot_uuid)
        if not bot:
            raise GlobalErrorException(
                error_code=ErrorCode.BOT_NOT_EXIST,
                error_message="The specified bot does not exist",
            )
        return bot

    def _get_class_id(self, bot_class_id: int, entity_name: str) -> int | None:
        entity_id = self.entity_query.get_entity_id_by_name(entity_name)
        if not entity_id:
            return None
        return self.query.get_knowledge_class_id_by_bot_class_id(
            bot_class_id, entity_id
        )

    def get_all_qa_list(self, bot_uuid: UUID) -> list[KnowledgeListView]:
        bot = self.validate_line_bot_exists(bot_uuid)
        class_id = self._get_class_id(bot.class_id, EntityName.KNOWLEDGE)
        if not class_id:
            return []
        return self.query.get_all_knowledge_items_by_class_id(class_id)

    def get_all_file_list(self, bot_uuid: UUID) -> list[KnowledgeFileListView]:
        bot = self.validate_line_bot_exists(bot_uuid)
        class_id = self._get_class_id(bot.class_id, EntityName.KNOWLEDGE)
        if not class_id:
            return []
        return self.query.get_all_knowledge_files_by_class_id(class_id)

    def sync_knowledge_vectors(
        self, bot_uuid: UUID, vector_service: VectorService
    ) -> dict:
        qa_items = self.get_all_qa_list(bot_uuid)
        file_items = self.get_all_file_list(bot_uuid)

        sql_qa_ids = {item.object_id for item in qa_items}
        sql_file_ids = {item.object_id for item in file_items}

        logger.info(
            f"Syncing Bot {bot_uuid}: {len(sql_qa_ids)} QAs, {len(sql_file_ids)} Files."
        )

        # 1. 獨立取得 Qdrant 內的 QA 與 File IDs (不包含 Product)
        qdrant_qa_ids = vector_service.get_object_ids_by_bot_uuid(
            bot_uuid, item_type="qa"
        )
        qdrant_file_ids = vector_service.get_object_ids_by_bot_uuid(
            bot_uuid, item_type="file"
        )

        # 2. 獨立計算需要刪除的過期資料
        qa_ids_to_delete = list(qdrant_qa_ids - sql_qa_ids)
        file_ids_to_delete = list(qdrant_file_ids - sql_file_ids)

        deleted_count = 0

        # 3. 獨立刪除 QA 舊資料，指定 type="qa"
        if qa_ids_to_delete:
            logger.info(
                f"Deleting {len(qa_ids_to_delete)} obsolete QA items from Qdrant."
            )
            vector_service.delete_knowledge_items(
                bot_uuid, qa_ids_to_delete, item_type="qa"
            )
            deleted_count += len(qa_ids_to_delete)

        # 4. 獨立刪除 File 舊資料，指定 type="file"
        if file_ids_to_delete:
            logger.info(
                f"Deleting {len(file_ids_to_delete)} obsolete File items from Qdrant."
            )
            vector_service.delete_knowledge_items(
                bot_uuid, file_ids_to_delete, item_type="file"
            )
            deleted_count += len(file_ids_to_delete)

        upserted_count = 0

        if qa_items:
            upserted_count += vector_service.upsert_qa_items(bot_uuid, qa_items)

        if file_items:
            upserted_count += vector_service.upsert_file_items(
                bot_uuid, file_items, self.storage_service
            )

        return {"upserted": upserted_count, "deleted": deleted_count}
