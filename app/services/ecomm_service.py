import logging
from uuid import UUID

from sqlmodel import Session

from app.configs.constans import EntityName, ErrorCode
from app.exception import GlobalErrorException
from app.models.bot_model import BotListView
from app.models.ecomm_model import (
    BrandListView,
    CategoryListView,
    ProductListView,
)
from app.queries.bot_query import BotQuery
from app.queries.ecomm_query import EcommQuery
from app.queries.entity_query import EntityQuery
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)


class EcommService:
    def __init__(self, session: Session):
        self.session = session
        self.query = EcommQuery(session)
        self.entity_query = EntityQuery(session)
        self.bot_query = BotQuery(session)

    def validate_line_bot_exists(self, bot_uuid: UUID) -> BotListView:
        """驗證 Bot 是否存在"""
        bot = self.bot_query.get_bot_by_uuid(bot_uuid)
        if not bot:
            raise GlobalErrorException(
                error_code=ErrorCode.BOT_NOT_EXIST,
                error_message="The specified bot does not exist",
            )
        return bot

    def _get_class_id(self, bot_class_id: int, entity_name: str) -> int | None:
        """取得對應 Entity 的 class_id"""
        entity_id = self.entity_query.get_entity_id_by_name(entity_name)
        if not entity_id:
            return None
        return self.query.get_ecomm_subclass_id(bot_class_id, entity_id)

    def get_all_brands(self, bot_uuid: UUID) -> list[BrandListView]:
        """取得該 Bot 的所有品牌"""
        bot = self.validate_line_bot_exists(bot_uuid)

        # 假設你的常數檔中有定義 EntityName.BRAND
        class_id = self._get_class_id(bot.class_id, EntityName.BRAND)
        if not class_id:
            return []

        return self.query.get_brands_by_class_id(class_id)

    def get_all_categories(self, bot_uuid: UUID) -> list[CategoryListView]:
        """取得該 Bot 底下的所有商品分類"""
        bot = self.validate_line_bot_exists(bot_uuid)
        return self.query.get_all_categories_by_class_id(bot.class_id)

    def get_all_products(self, bot_uuid: UUID) -> list[ProductListView]:
        """取得該 Bot 底下的所有商品"""
        categories = self.get_all_categories(bot_uuid)
        category_ids = [cat.class_id for cat in categories]
        if not category_ids:
            return []

        return self.query.get_products_by_category_ids(category_ids)

    def sync_product_vectors(
        self, bot_uuid: UUID, vector_service: VectorService
    ) -> dict:
        products = self.get_all_products(bot_uuid)
        categories = self.get_all_categories(bot_uuid)
        brands = self.get_all_brands(bot_uuid)
        category_map = {cat.class_id: cat.category_name for cat in categories}
        brand_map = {brand.object_id: brand.brand_name for brand in brands}

        sql_product_ids = set()
        product_vector_payloads = []

        for prod in products:
            sql_product_ids.add(prod.object_id)

            cat_name = category_map.get(prod.category_id, "未分類")
            brand_name = (
                brand_map.get(prod.brand_id, "無品牌") if prod.brand_id else "無品牌"
            )

            content_parts = [
                f"商品名稱: {prod.product_name}",
                f"分類: {cat_name}",
                f"品牌: {brand_name}",
                f"價格: {prod.price}元",
                f"庫存狀態: {'充足' if prod.stock and prod.stock > 0 else '缺貨'}",
            ]
            if prod.product_description:
                content_parts.append(f"商品描述: {prod.product_description}")
            if prod.sku_code:
                content_parts.append(f"SKU: {prod.sku_code}")

            rag_content = "\n".join(content_parts)

            product_vector_payloads.append({
                "object_id": prod.object_id,
                "content": rag_content,
                "metadata": {
                    "product_name": prod.product_name,
                    "category": cat_name,
                    "brand": brand_name,
                    "price": prod.price,
                },
            })

        logger.info(
            f"Syncing Ecomm Bot {bot_uuid}: {len(sql_product_ids)} Active Products."
        )

        # ✨ 新增：1. 加上 item_type="product"，取得 Qdrant 中現有的商品 ID
        qdrant_product_ids = vector_service.get_object_ids_by_bot_uuid(
            bot_uuid, item_type="product"
        )

        # ✨ 新增：2. 比對並找出已經在 SQL 被刪除的商品 ID
        ids_to_delete = list(qdrant_product_ids - sql_product_ids)
        deleted_count = 0

        # ✨ 新增：3. 執行刪除
        if ids_to_delete:
            logger.info(
                f"Deleting {len(ids_to_delete)} obsolete Product items from Qdrant."
            )
            vector_service.delete_knowledge_items(
                bot_uuid, ids_to_delete, item_type="product"
            )
            deleted_count = len(ids_to_delete)

        upserted_count = 0
        if product_vector_payloads:
            upserted_count += vector_service.upsert_product_items(
                bot_uuid, product_vector_payloads
            )

        # 把刪除數量也回傳（就算 Router 沒用到，留作 Debug 也很方便）
        return {"upserted": upserted_count, "deleted": deleted_count}
