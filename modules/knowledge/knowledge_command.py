import logging
from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, delete, select

from modules.knowledge.knowledge_model import KnowledgeFile, KnowledgeVectorDBStatus
from shared.constants.common import SyncStatus
from shared.models.class_object_relation_model import ClassObjectRelation
from shared.models.object_model import Object
from shared.queries.entity_query import get_entity_id_by_name

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class KnowledgeCommand:
    def __init__(self, session: Session):
        self.session = session

    def insert_knowledge_item(
        self, knowledge_class_id: int, question: str, answer: str
    ):
        knowledge_entity_id = get_entity_id_by_name(self.session, "知識")

        new_knowledge = Object(
            chinese_name=question, english_name=answer, entity_id=knowledge_entity_id
        )
        self.session.add(new_knowledge)
        self.session.flush()
        relation = ClassObjectRelation(
            class_id=knowledge_class_id, object_id=new_knowledge.object_id
        )
        self.session.add(relation)

    def insert_knowledge_items(
        self, knowledge_class_id: int, knowledge_items: List[dict]
    ):
        knowledge_entity_id = get_entity_id_by_name(self.session, "知識")

        knowledges: List[Object] = []
        new_relations = []

        for item in knowledge_items:
            question = item.get("question")
            answer = item.get("answer")
            if not question or not answer:
                continue

            knowledge = Object(
                chinese_name=question,
                english_name=answer,
                entity_id=knowledge_entity_id,
            )
            knowledges.append(knowledge)

        self.session.add_all(knowledges)
        self.session.flush()

        for knowledge in knowledges:
            rel = ClassObjectRelation(
                class_id=knowledge_class_id,
                object_id=knowledge.object_id,
            )
            new_relations.append(rel)

        self.session.add_all(new_relations)

    def delete_knowledge_items(
        self, knowledge_class_id: int, delete_items_id: List[int]
    ):
        relation_stmt = select(ClassObjectRelation).where(
            ClassObjectRelation.class_id == knowledge_class_id,
            ClassObjectRelation.object_id.in_(delete_items_id),
        )
        relations = self.session.exec(relation_stmt).all()
        found_ids = [r.object_id for r in relations]

        self.session.exec(
            delete(ClassObjectRelation).where(
                ClassObjectRelation.class_id == knowledge_class_id,
                ClassObjectRelation.object_id.in_(found_ids),
            )
        )

        self.session.exec(delete(Object).where(Object.object_id.in_(found_ids)))

    def update_knowledge_item(
        self, object_id: int, question: str | None, answer: str | None
    ):
        knowledge = self.session.get(Object, object_id)
        if knowledge:
            if question is not None:
                knowledge.chinese_name = question
            if answer is not None:
                knowledge.english_name = answer

    def insert_knowledge_file(
        self,
        knowledge_class_id: int,
        display_name: str,
        filename: str,
        file_type: str = "pdf",
    ) -> KnowledgeFile:
        knowledge_entity_id = get_entity_id_by_name(self.session, "知識")

        new_obj = Object(
            chinese_name=display_name,
            english_name="",
            entity_id=knowledge_entity_id,
        )
        self.session.add(new_obj)
        self.session.flush()

        rel = ClassObjectRelation(
            class_id=knowledge_class_id,
            object_id=new_obj.object_id,
        )
        self.session.add(rel)

        kf = KnowledgeFile(
            object_id=new_obj.object_id,
            filename=filename,
            display_name=display_name,
            file_type=file_type,
            created_at=None,
        )
        self.session.add(kf)
        self.session.flush()
        return kf

    def update_knowledge_file_display_name(
        self,
        object_id: int,
        file_id: int,
        display_name: str,
    ) -> None:
        kf = self.session.get(KnowledgeFile, file_id)
        if kf:
            kf.display_name = display_name

        obj = self.session.get(Object, object_id)
        if obj:
            obj.chinese_name = display_name

    def delete_knowledge_files_by_objects(
        self, knowledge_class_id: int, object_ids: List[int]
    ) -> None:
        if not object_ids:
            return

        self.session.exec(
            delete(ClassObjectRelation).where(
                ClassObjectRelation.class_id == knowledge_class_id,
                ClassObjectRelation.object_id.in_(object_ids),
            )
        )
        self.session.exec(delete(Object).where(Object.object_id.in_(object_ids)))

    async def update_knowledge_vector_db_status(
        self,
        bot_uuid: str,
        status: Optional[SyncStatus] = None,
        has_pending_changes: Optional[bool] = None,
        last_sync_start_time: Optional[datetime] = None,
        last_sync_end_time: Optional[datetime] = None,
        last_successful_sync_time: Optional[datetime] = None,
    ):
        status_doc = await KnowledgeVectorDBStatus.find_one(
            KnowledgeVectorDBStatus.bot_uuid == bot_uuid
        )

        update_data = {
            "status": status,
            "has_pending_changes": has_pending_changes,
            "last_sync_start_time": last_sync_start_time,
            "last_sync_end_time": last_sync_end_time,
            "last_successful_sync_time": last_successful_sync_time,
        }
        update_data = {k: v for k, v in update_data.items() if v is not None}

        if status_doc:
            if update_data:
                await status_doc.set(update_data)
                await status_doc.save()
        else:
            status_doc = KnowledgeVectorDBStatus(bot_uuid=bot_uuid, **update_data)
            await status_doc.insert()
