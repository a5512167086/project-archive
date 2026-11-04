from sqlmodel import Session, select, text

from app.models.class_model import SubClassView
from app.models.ecomm_model import (
    BrandListView,
    CategoryListView,
    ProductListView,
)


class EcommQuery:
    def __init__(self, session: Session):
        self.session = session

    def get_ecomm_subclass_id(
        self, bot_class_id: int, target_entity_id: int
    ) -> int | None:
        """取得特定 Entity (如 Brand) 的子分類 ID"""
        result = self.session.exec(
            select(SubClassView.class_id).where(
                SubClassView.parent_class_id == bot_class_id,
                SubClassView.entity_id == target_entity_id,
            )
        ).first()
        return result

    def get_all_categories_by_class_id(
        self, parent_class_id: int
    ) -> list[CategoryListView]:
        stmt = text("""
            WITH RECURSIVE category_tree AS (
                SELECT
                    i.parent_class_id,
                    i.child_class_id,
                    ARRAY[i.parent_class_id, i.child_class_id]::int[] AS path,
                    1 AS depth
                FROM inheritances i
                WHERE i.parent_class_id = :parent_class_id

                UNION ALL

                SELECT
                    i.parent_class_id,
                    i.child_class_id,
                    (ct.path || i.child_class_id)::int[] AS path,
                    ct.depth + 1 AS depth
                FROM inheritances i
                JOIN category_tree ct
                  ON i.parent_class_id = ct.child_class_id
                WHERE NOT i.child_class_id = ANY(ct.path)
            )
            SELECT
                ct.parent_class_id,
                c.class_id,
                c.entity_id,
                c.chinese_name AS category_name,
                c.chinese_description AS category_description,
                c.created_at,
                c.updated_at
            FROM category_tree ct
            JOIN classes c
              ON c.class_id = ct.child_class_id
            JOIN entities e
              ON e.entity_id = c.entity_id
            WHERE e.chinese_name = '類別'
            ORDER BY ct.depth, c.class_id
        """)

        result = self.session.exec(
            stmt.bindparams(parent_class_id=parent_class_id)
        ).all()

        return [
            CategoryListView(
                parent_class_id=row.parent_class_id,
                class_id=row.class_id,
                entity_id=row.entity_id,
                category_name=row.category_name,
                category_description=row.category_description,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in result
        ]

    def get_products_by_category_ids(
        self, category_ids: list[int]
    ) -> list[ProductListView]:
        """根據分類 ID 列表取得所有商品"""
        if not category_ids:
            return []
        statement = select(ProductListView).where(
            ProductListView.category_id.in_(category_ids)
        )
        return self.session.exec(statement).all()

    def get_brands_by_class_id(self, class_id: int) -> list[BrandListView]:
        """根據 class_id 取得所有品牌"""
        statement = select(BrandListView).where(BrandListView.class_id == class_id)
        return self.session.exec(statement).all()
