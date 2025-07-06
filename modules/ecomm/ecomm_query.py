import logging
from typing import List

from sqlmodel import Session, select

from modules.ecomm.ecomm_model import BrandListView, CategoryListView
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


# Category query functions
def get_category_class_id_by_bot_class_id(
    session: Session, bot_class_id: int
) -> int | None:
    category_entity_id = get_entity_id_by_name(session, "類別")
    result = session.exec(
        select(SubClassView.class_id).where(
            SubClassView.parent_class_id == bot_class_id,
            SubClassView.entity_id == category_entity_id,
        )
    ).first()

    return result


def get_all_categories_by_class_id(
    session: Session, parent_class_id: int
) -> List[CategoryListView]:
    # 根據 parent_class_id 來取得所有子類別
    statement = select(CategoryListView).where(
        CategoryListView.parent_class_id == parent_class_id
    )
    result = session.exec(statement)
    return result.all()


def check_category_name_exists(
    session: Session, parent_class_id: int, category_name: str
) -> bool:
    """檢查指定類別名稱是否已存在於指定 parent_class_id 中"""
    result = session.exec(
        select(CategoryListView).where(
            CategoryListView.parent_class_id == parent_class_id,
            CategoryListView.category_name == category_name,
        )
    ).first()
    return result is not None


def check_category_name_exists_exclude_self(
    session: Session, parent_class_id: int, category_name: str, exclude_class_id: int
) -> bool:
    """檢查指定類別名稱是否已存在於指定 parent_class_id 中，排除指定的 class_id"""
    result = session.exec(
        select(CategoryListView).where(
            CategoryListView.parent_class_id == parent_class_id,
            CategoryListView.category_name == category_name,
            CategoryListView.class_id != exclude_class_id,
        )
    ).first()
    return result is not None


def check_parent_category_exists(
    session: Session, base_category_class_id: int, parent_category_class_id: int
) -> bool:
    """檢查指定的父類別是否存在"""
    result = session.exec(
        select(CategoryListView).where(
            CategoryListView.class_id == parent_category_class_id,
        )
    ).first()
    return result is not None


def check_category_hierarchy_valid(
    session: Session,
    base_category_class_id: int,
    category_class_id: int,
    parent_category_class_id: int,
) -> bool:
    """檢查類別階層是否有效（避免循環引用）"""
    # 如果父類別就是自己，則無效
    if category_class_id == parent_category_class_id:
        return False

    # 檢查是否會造成循環引用
    current_parent = parent_category_class_id
    visited = set()

    while current_parent is not None:
        if current_parent in visited or current_parent == category_class_id:
            return False
        visited.add(current_parent)

        # 查找當前父類別的父類別
        parent_result = session.exec(
            select(CategoryListView.parent_class_id).where(
                CategoryListView.class_id == current_parent,
            )
        ).first()
        current_parent = parent_result

    return True
