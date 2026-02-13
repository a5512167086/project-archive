import logging
from typing import List
from uuid import UUID

from sqlmodel import Session, select

from modules.ecomm.ecomm_model import (
    BrandListView,
    CategoryListView,
    OrderDetail,
    OrderItem,
    OrderListView,
    ProductDetail,
    ProductImage,
    ProductListView,
    ProductVariant,
    ShippingSetting,
)
from shared.models.class_model import SubClassView
from shared.models.object_model import Object
from shared.queries.entity_query import get_entity_id_by_name

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EcommQuery:
    def __init__(self, session: Session):
        self.session = session

    def get_brand_class_id_by_bot_class_id(self, bot_class_id: int) -> int | None:
        brand_entity_id = get_entity_id_by_name(self.session, "品牌")
        result = self.session.exec(
            select(SubClassView.class_id).where(
                SubClassView.parent_class_id == bot_class_id,
                SubClassView.entity_id == brand_entity_id,
            )
        ).first()

        return result

    def get_all_brands_by_class_id(self, class_id: int) -> List[BrandListView]:
        statement = select(BrandListView).where(BrandListView.class_id == class_id)
        result = self.session.exec(statement)
        return result.all()

    def check_brand_name_exists(self, class_id: int, brand_name: str) -> bool:
        result = self.session.exec(
            select(BrandListView).where(
                BrandListView.class_id == class_id,
                BrandListView.brand_name == brand_name,
            )
        ).first()
        return result is not None

    def check_brand_name_exists_exclude_self(
        self, class_id: int, brand_name: str, exclude_object_id: int
    ) -> bool:
        result = self.session.exec(
            select(BrandListView).where(
                BrandListView.class_id == class_id,
                BrandListView.brand_name == brand_name,
                BrandListView.object_id != exclude_object_id,
            )
        ).first()
        return result is not None

    def get_category_class_id_by_bot_class_id(self, bot_class_id: int) -> int | None:
        category_entity_id = get_entity_id_by_name(self.session, "類別")
        result = self.session.exec(
            select(SubClassView.class_id).where(
                SubClassView.parent_class_id == bot_class_id,
                SubClassView.entity_id == category_entity_id,
            )
        ).first()

        return result

    def get_categories_by_class_id(
        self, category_id_list: List[int]
    ) -> List[CategoryListView]:
        statement = select(CategoryListView).where(
            CategoryListView.parent_class_id.in_(category_id_list)
        )
        result = self.session.exec(statement).all()
        return result

    def get_all_categories_by_class_id(
        self, parent_class_id: int
    ) -> List[CategoryListView]:
        result = []
        queue = [parent_class_id]
        while queue:
            pid = queue.pop(0)
            statement = select(CategoryListView).where(
                CategoryListView.parent_class_id == pid
            )
            children = self.session.exec(statement).all()
            result.extend(children)
            queue.extend([child.class_id for child in children])
        return result

    def check_category_name_exists(
        self, parent_class_id: int, category_name: str
    ) -> bool:
        result = self.session.exec(
            select(CategoryListView).where(
                CategoryListView.parent_class_id == parent_class_id,
                CategoryListView.category_name == category_name,
            )
        ).first()
        return result is not None

    def check_category_name_exists_exclude_self(
        self, parent_class_id: int, category_name: str, exclude_class_id: int
    ) -> bool:
        result = self.session.exec(
            select(CategoryListView).where(
                CategoryListView.parent_class_id == parent_class_id,
                CategoryListView.category_name == category_name,
                CategoryListView.class_id != exclude_class_id,
            )
        ).first()
        return result is not None

    def check_parent_category_exists(self, parent_category_class_id: int) -> bool:
        result = self.session.exec(
            select(CategoryListView).where(
                CategoryListView.class_id == parent_category_class_id,
            )
        ).first()
        return result is not None

    def check_category_hierarchy_valid(
        self, category_class_id: int, parent_category_class_id: int
    ) -> bool:
        if category_class_id == parent_category_class_id:
            return False

        current_parent = parent_category_class_id
        visited = set()

        while current_parent is not None:
            if current_parent in visited:
                return False
            visited.add(current_parent)

            parent_result = self.session.exec(
                select(CategoryListView.parent_class_id).where(
                    CategoryListView.class_id == current_parent,
                )
            ).first()
            current_parent = parent_result if parent_result else None

        return True

    def get_product_class_id_by_bot_class_id(self, bot_class_id: int) -> int | None:
        product_entity_id = get_entity_id_by_name(self.session, "產品")
        result = self.session.exec(
            select(SubClassView.class_id).where(
                SubClassView.parent_class_id == bot_class_id,
                SubClassView.entity_id == product_entity_id,
            )
        ).first()

        return result

    def get_product_by_id(self, product_id: UUID) -> ProductDetail | None:
        return self.session.get(ProductDetail, product_id)

    def get_product_by_object_id(self, object_id: int) -> ProductDetail | None:
        return self.session.exec(
            select(ProductDetail).where(ProductDetail.object_id == object_id)
        ).first()

    def get_product_images_by_object_id(self, object_id: int) -> List[ProductImage]:
        return self.session.exec(
            select(ProductImage)
            .where(ProductImage.object_id == object_id)
            .order_by(ProductImage.created_at)
        ).all()

    def get_product_images_by_object_ids(self, object_ids: List[int]) -> List[ProductImage]:
        if not object_ids:
            return []
        return self.session.exec(
            select(ProductImage)
            .where(ProductImage.object_id.in_(object_ids))
            .order_by(ProductImage.created_at)
        ).all()

    def get_product_image_by_id(self, image_id: int) -> ProductImage | None:
        return self.session.get(ProductImage, image_id)

    def get_product_variants_by_object_id(self, object_id: int) -> List[ProductVariant]:
        return self.session.exec(
            select(ProductVariant).where(ProductVariant.object_id == object_id)
        ).all()

    def get_product_variants_by_object_ids(
        self, object_ids: List[int]
    ) -> List[ProductVariant]:
        if not object_ids:
            return []
        return self.session.exec(
            select(ProductVariant).where(ProductVariant.object_id.in_(object_ids))
        ).all()

    def get_variant_by_id(self, variant_id: UUID) -> ProductVariant | None:
        return self.session.get(ProductVariant, variant_id)

    def check_variant_sku_exists(self, sku_code: str) -> bool:
        if not sku_code:
            return False
        result = self.session.exec(
            select(ProductVariant).where(ProductVariant.sku_code == sku_code)
        ).first()
        return result is not None

    def check_variant_sku_exists_exclude_self(
        self, sku_code: str, exclude_variant_id: UUID
    ) -> bool:
        if not sku_code:
            return False
        result = self.session.exec(
            select(ProductVariant).where(
                ProductVariant.sku_code == sku_code,
                ProductVariant.variant_id != exclude_variant_id,
            )
        ).first()
        return result is not None

    def check_product_sku_exists(self, sku_code: str) -> bool:
        result = self.session.exec(
            select(ProductDetail).where(ProductDetail.sku_code == sku_code)
        ).first()
        return result is not None

    def check_product_sku_exists_exclude_self(
        self, sku_code: str, exclude_product_id: UUID
    ) -> bool:
        result = self.session.exec(
            select(ProductDetail).where(
                ProductDetail.sku_code == sku_code,
                ProductDetail.product_id != exclude_product_id,
            )
        ).first()
        return result is not None

    def get_products_by_class_id(self, class_id: int) -> List[dict]:
        objects = self.session.exec(
            select(Object)
            .join(SubClassView, Object.entity_id == SubClassView.entity_id)
            .where(SubClassView.class_id == class_id)
        ).all()

        products = []
        for obj in objects:
            product_detail = self.get_product_by_object_id(obj.object_id)
            if product_detail:
                products.append({
                    "product_detail": product_detail,
                    "object": obj,
                })

        return products

    def get_all_products_view(self, category_ids: List[int]) -> List[ProductListView]:
        statement = select(ProductListView).where(
            ProductListView.category_id.in_(category_ids)
        )
        return self.session.exec(statement).all()

    async def get_shipping_setting_by_bot_uuid(
        self, bot_uuid: str
    ) -> ShippingSetting | None:
        return await ShippingSetting.find_one(ShippingSetting.bot_uuid == bot_uuid)

    def get_order_class_id_by_bot_class_id(self, bot_class_id: int) -> int | None:
        order_entity_id = get_entity_id_by_name(self.session, "訂單")
        result = self.session.exec(
            select(SubClassView.class_id).where(
                SubClassView.parent_class_id == bot_class_id,
                SubClassView.entity_id == order_entity_id,
            )
        ).first()

        return result

    def get_all_orders_view(self, class_id: int) -> List[OrderListView]:
        statement = select(OrderListView).where(OrderListView.class_id == class_id)
        return self.session.exec(statement).all()

    def get_all_user_orders_view(
        self, user_id: UUID, class_id: int
    ) -> List[OrderListView]:
        user_order_object_ids = self.session.exec(
            select(Object.object_id).where(Object.owner_id == str(user_id))
        ).all()

        if not user_order_object_ids:
            return []

        statement = select(OrderListView).where(
            OrderListView.class_id == class_id,
            OrderListView.object_id.in_(user_order_object_ids),
        )
        return self.session.exec(statement).all()

    def get_order_by_id(self, order_id: UUID) -> OrderDetail | None:
        return self.session.get(OrderDetail, order_id)

    def get_order_items_by_object_id(self, object_id: int) -> List[OrderItem]:
        return self.session.exec(
            select(OrderItem).where(OrderItem.object_id == object_id)
        ).all()
