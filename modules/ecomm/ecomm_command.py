import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, delete, select, text

from modules.ecomm.ecomm_model import ProductDetail, ProductImage, ProductVariant
from shared.models.class_model import Class
from shared.models.class_object_relation_model import ClassObjectRelation
from shared.models.inheritance_model import Inheritance
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


# Category command functions
def insert_category(
    session: Session,
    category_class_id: int,
    category_name: str,
    category_description: str,
    parent_category_id: Optional[int] = None,
    owner_id: Optional[str] = None,
):
    category_entity_id = get_entity_id_by_name(session, "類別")

    # 決定父類別 ID
    parent_id = parent_category_id if parent_category_id else category_class_id

    # 處理 owner_id 參數
    owner_param = "NULL" if owner_id is None else f"'{owner_id}'"

    # 使用 SQL function 建立新的 class
    sql_query = f"SELECT fs_insert_class({parent_id}, {category_entity_id}, '{category_name}', '{category_description}', {owner_param})"

    result = session.exec(text(sql_query)).first()

    if result is None:
        raise Exception("Failed to create category class")

    return result  # 回傳新建立的 class_id


def delete_categories(
    session: Session, category_class_id: int, delete_categories_class_id: List[int]
):
    for class_id in delete_categories_class_id:
        # 1. 找到要刪除的類別的父類別
        parent_inheritance = session.exec(
            select(Inheritance.parent_class_id).where(
                Inheritance.child_class_id == class_id
            )
        ).first()

        if parent_inheritance:
            # 2. 找到所有子類別
            child_classes = session.exec(
                select(Inheritance.child_class_id).where(
                    Inheritance.parent_class_id == class_id
                )
            ).all()

            # 3. 使用 SQL function 將所有子類別移動到祖父類別
            for child_class_id in child_classes:
                # 呼叫 SQL function 移動子類別
                session.exec(
                    text(
                        f"SELECT * FROM fs_move_class({child_class_id}, {parent_inheritance})"
                    )
                )

        # 4. 刪除該類別的所有繼承關係（作為子類別）
        session.exec(delete(Inheritance).where(Inheritance.child_class_id == class_id))

        # 5. 刪除該類別的所有繼承關係（作為父類別）
        session.exec(delete(Inheritance).where(Inheritance.parent_class_id == class_id))

        # 6. 刪除該類別本身
        session.exec(delete(Class).where(Class.class_id == class_id))


def update_category(
    session: Session,
    category_class_id: int,
    class_id: int,
    category_name: Optional[str] = None,
    category_description: Optional[str] = None,
    parent_category_id: Optional[int] = None,
):
    # 檢查該 class_id 是否存在
    category_class = session.get(Class, class_id)
    if not category_class:
        return False

    # 更新 Class 資料
    if category_name is not None:
        category_class.chinese_name = category_name
        category_class.english_name = category_name
    if category_description is not None:
        category_class.chinese_description = category_description
        category_class.english_description = category_description

    session.add(category_class)

    # 更新父類別關係
    if parent_category_id is not None:
        # 先刪除現有的繼承關係
        session.exec(delete(Inheritance).where(Inheritance.child_class_id == class_id))

        # 建立新的繼承關係
        if parent_category_id != 0:  # 0 表示設為根類別
            inheritance = Inheritance(
                parent_class_id=parent_category_id,
                child_class_id=class_id,
            )
            session.add(inheritance)
        else:
            # 設為根類別，繼承原始的 category_class_id
            inheritance = Inheritance(
                parent_class_id=category_class_id,
                child_class_id=class_id,
            )
            session.add(inheritance)

    return True


# Product command functions
def insert_product(
    session: Session,
    product_class_id: int,
    product_name: str,
    product_description: str,
    brand_id: Optional[int],
    sku_code: str,
    price: int,
    stock: int,
    is_active: bool,
    images: List[dict],
    variants: List[dict],
    owner_id: Optional[str] = None,
) -> int:
    """建立產品"""
    product_entity_id = get_entity_id_by_name(session, "產品")

    # 建立 Object
    new_product_object = Object(
        chinese_name=product_name,
        chinese_description=product_description,
        english_name=product_name,
        english_description=product_description,
        entity_id=product_entity_id,
        owner_id=owner_id,
    )
    session.add(new_product_object)
    session.flush()

    # 建立 ClassObjectRelation
    relation = ClassObjectRelation(
        class_id=product_class_id, object_id=new_product_object.object_id
    )
    session.add(relation)

    # 建立 ProductDetail
    product_detail = ProductDetail(
        brand_id=brand_id,
        object_id=new_product_object.object_id,
        is_active=is_active,
        sku_code=sku_code,
        price=price,
        stock=stock,
    )
    session.add(product_detail)
    session.flush()

    # 建立產品圖片
    for img in images:
        product_image = ProductImage(
            image_url=img["image_url"],
            object_id=new_product_object.object_id,
            display_order=img.get("display_order", 0),
        )
        session.add(product_image)

    # 建立產品變體
    for variant in variants:
        product_variant = ProductVariant(
            object_id=new_product_object.object_id,
            variant_name=variant["variant_name"],
            sku_code=variant.get("sku_code"),
            price=variant.get("price"),
            stock=variant.get("stock", 0),
        )
        session.add(product_variant)

    return new_product_object.object_id


def delete_products(session: Session, product_class_id: int, product_ids: List[UUID]):
    """刪除產品"""
    # 先取得相關的 object_ids
    product_details = session.exec(
        select(ProductDetail).where(ProductDetail.product_id.in_(product_ids))
    ).all()

    object_ids = [pd.object_id for pd in product_details]

    if object_ids:
        # 刪除產品圖片
        session.exec(delete(ProductImage).where(ProductImage.object_id.in_(object_ids)))

        # 刪除產品變體
        session.exec(
            delete(ProductVariant).where(ProductVariant.object_id.in_(object_ids))
        )

        # 刪除產品詳細資訊
        session.exec(
            delete(ProductDetail).where(ProductDetail.product_id.in_(product_ids))
        )

        # 刪除 ClassObjectRelation
        session.exec(
            delete(ClassObjectRelation).where(
                ClassObjectRelation.class_id == product_class_id,
                ClassObjectRelation.object_id.in_(object_ids),
            )
        )

        # 刪除 Object
        session.exec(delete(Object).where(Object.object_id.in_(object_ids)))


def update_product(
    session: Session,
    product_id: UUID,
    product_name: Optional[str] = None,
    product_description: Optional[str] = None,
    brand_id: Optional[int] = None,
    sku_code: Optional[str] = None,
    price: Optional[int] = None,
    stock: Optional[int] = None,
    is_active: Optional[bool] = None,
    images: Optional[List[dict]] = None,
    variants: Optional[List[dict]] = None,
    category_id: Optional[int] = None,
) -> bool:
    """更新產品"""
    # 取得產品詳細資訊
    product_detail = session.get(ProductDetail, product_id)
    if not product_detail:
        return False

    # 更新 Object
    product_object = session.get(Object, product_detail.object_id)
    if product_object:
        if product_name is not None:
            product_object.chinese_name = product_name
            product_object.english_name = product_name
        if product_description is not None:
            product_object.chinese_description = product_description
            product_object.english_description = product_description
        session.add(product_object)

    # 更新 ProductDetail
    if brand_id is not None:
        product_detail.brand_id = brand_id
    if sku_code is not None:
        product_detail.sku_code = sku_code
    if price is not None:
        product_detail.price = price
    if stock is not None:
        product_detail.stock = stock
    if is_active is not None:
        product_detail.is_active = is_active

    product_detail.updated_at = datetime.utcnow()
    session.add(product_detail)

    # 更新類別關係
    if category_id is not None:
        # 刪除現有的類別關係
        session.exec(
            delete(ClassObjectRelation).where(
                ClassObjectRelation.object_id == product_detail.object_id
            )
        )

        # 建立新的類別關係
        new_relation = ClassObjectRelation(
            class_id=category_id, object_id=product_detail.object_id
        )
        session.add(new_relation)

    # 更新圖片
    if images is not None:
        # 刪除現有圖片
        session.exec(
            delete(ProductImage).where(
                ProductImage.object_id == product_detail.object_id
            )
        )

        # 新增新圖片
        for img in images:
            product_image = ProductImage(
                image_url=img["image_url"],
                object_id=product_detail.object_id,
                display_order=img.get("display_order", 0),
            )
            session.add(product_image)

    # 更新變體
    if variants is not None:
        # 刪除現有變體
        session.exec(
            delete(ProductVariant).where(
                ProductVariant.object_id == product_detail.object_id
            )
        )

        # 新增新變體
        for variant in variants:
            product_variant = ProductVariant(
                object_id=product_detail.object_id,
                variant_name=variant["variant_name"],
                sku_code=variant.get("sku_code"),
                price=variant.get("price"),
                stock=variant.get("stock", 0),
            )
            session.add(product_variant)

    return True
