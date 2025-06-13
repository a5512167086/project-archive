from sqlmodel import Session, select

from models.entity_model import Entity


def get_entity_id_by_name(session: Session, entity_name: str) -> int | None:
    result = session.exec(
        select(Entity.entity_id).where(Entity.chinese_name == entity_name)
    ).first()

    return result
