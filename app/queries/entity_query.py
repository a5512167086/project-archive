from sqlmodel import Session, select

from app.configs.constans import EntityName
from app.models.entity_model import Entity


class EntityQuery:
    def __init__(self, session: Session):
        self.session = session

    def get_entity_id_by_name(self, entity_name: EntityName) -> int | None:
        result = self.session.exec(
            select(Entity.entity_id).where(Entity.chinese_name == entity_name)
        ).first()

        return result
