import logging
from typing import List

from sqlmodel import Session, delete, select

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
