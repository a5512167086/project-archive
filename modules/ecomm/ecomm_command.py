import logging
from typing import List, Optional

from sqlmodel import Session, delete, select

from shared.models.class_object_relation_model import ClassObjectRelation
from shared.models.object_model import Object
from shared.queries.entity_query import get_entity_id_by_name

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def insert_brand(
    session: Session, brand_class_id: int, brand_name: str, brand_description: str
):
    brand_entity_id = get_entity_id_by_name(session, "品牌")

    new_brand = Object(
        chinese_name=brand_name,
        english_name=brand_description,
        entity_id=brand_entity_id,
    )
    session.add(new_brand)
    session.flush()
    relation = ClassObjectRelation(
        class_id=brand_class_id, object_id=new_brand.object_id
    )
    session.add(relation)


def delete_brands(
    session: Session, brand_class_id: int, delete_brands_object_id: List[int]
):
    relation_stmt = select(ClassObjectRelation).where(
        ClassObjectRelation.class_id == brand_class_id,
        ClassObjectRelation.object_id.in_(delete_brands_object_id),
    )
    relations = session.exec(relation_stmt).all()
    found_ids = [r.object_id for r in relations]

    session.exec(
        delete(ClassObjectRelation).where(
            ClassObjectRelation.class_id == brand_class_id,
            ClassObjectRelation.object_id.in_(found_ids),
        )
    )

    session.exec(delete(Object).where(Object.object_id.in_(found_ids)))


def update_brand(
    session: Session,
    brand_class_id: int,
    object_id: int,
    brand_name: Optional[str] = None,
    brand_description: Optional[str] = None,
):
    # 檢查該 object_id 是否存在於指定的 brand_class_id 中
    relation = session.exec(
        select(ClassObjectRelation).where(
            ClassObjectRelation.class_id == brand_class_id,
            ClassObjectRelation.object_id == object_id,
        )
    ).first()

    if not relation:
        return False

    # 更新 Object 資料
    brand_object = session.get(Object, object_id)
    if brand_object:
        # 只更新有提供的欄位
        if brand_name is not None:
            brand_object.chinese_name = brand_name
        if brand_description is not None:
            brand_object.english_name = brand_description
        session.add(brand_object)
        return True

    return False
