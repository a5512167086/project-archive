import logging
from typing import List

from sqlmodel import Session, select

from modules.ecomm.ecomm_model import BrandListView
from shared.models.class_model import SubClassView
from shared.queries.entity_query import get_entity_id_by_name

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_brand_class_id_by_bot_class_id(
    session: Session, bot_class_id: int
) -> int | None:
    brand_entity_id = get_entity_id_by_name(session, "品牌")
    result = session.exec(
        select(SubClassView.class_id).where(
            SubClassView.parent_class_id == bot_class_id,
            SubClassView.entity_id == brand_entity_id,
        )
    ).first()

    return result


def get_all_brands_by_class_id(session: Session, class_id: int) -> List[BrandListView]:
    statement = select(BrandListView).where(BrandListView.class_id == class_id)
    result = session.exec(statement)
    return result.all()


def check_brand_name_exists(session: Session, class_id: int, brand_name: str) -> bool:
    """檢查指定品牌名稱是否已存在於指定 class_id 中"""
    result = session.exec(
        select(BrandListView).where(
            BrandListView.class_id == class_id,
            BrandListView.brand_name == brand_name,
        )
    ).first()
    return result is not None


def check_brand_name_exists_exclude_self(
    session: Session, class_id: int, brand_name: str, exclude_object_id: int
) -> bool:
    """檢查指定品牌名稱是否已存在於指定 class_id 中，排除指定的 object_id"""
    result = session.exec(
        select(BrandListView).where(
            BrandListView.class_id == class_id,
            BrandListView.brand_name == brand_name,
            BrandListView.object_id != exclude_object_id,
        )
    ).first()
    return result is not None
