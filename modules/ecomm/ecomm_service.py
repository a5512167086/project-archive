from typing import List
from uuid import UUID

from sqlmodel import Session

from modules.bot.bot_service import validate_bot_ownership, validate_line_bot_exists
from modules.ecomm.ecomm_command import (
    delete_brands,
    delete_categories,
    delete_products,
    insert_brand,
    insert_category,
    insert_product,
    update_brand,
    update_category,
    update_product,
)
from modules.ecomm.ecomm_model import BrandListView, CategoryListView
from modules.ecomm.ecomm_query import (
    check_brand_name_exists,
    check_brand_name_exists_exclude_self,
    check_category_hierarchy_valid,
    check_category_name_exists,
    check_category_name_exists_exclude_self,
    check_parent_category_exists,
    check_product_sku_exists,
    check_product_sku_exists_exclude_self,
    get_all_brands_by_class_id,
    get_all_categories_by_class_id,
    get_brand_class_id_by_bot_class_id,
    get_category_class_id_by_bot_class_id,
    get_product_class_id_by_bot_class_id,
    get_products_by_class_id,
)
from modules.ecomm.ecomm_schema import (
    DeleteBrandRequest,
    DeleteCategoryRequest,
    DeleteProductRequest,
    InsertBrandRequest,
    InsertCategoryRequest,
    InsertProductRequest,
    UpdateBrandRequest,
    UpdateCategoryRequest,
    UpdateProductRequest,
)
from shared.constants.error_code import ErrorCode
from shared.exception import GlobalErrorException


def validate_brand_class(session: Session, bot_class_id: int) -> int:
    brand_class_id = get_brand_class_id_by_bot_class_id(session, bot_class_id)
    if not brand_class_id:
        raise GlobalErrorException(
            error_code=ErrorCode.BRAND_CLASS_NOT_FOUND,
            error_message="Brand class not found for the given bot class",
        )
    return brand_class_id


def validate_category_class(session: Session, bot_class_id: int) -> int:
    category_class_id = get_category_class_id_by_bot_class_id(session, bot_class_id)
    if not category_class_id:
        raise GlobalErrorException(
            error_code=ErrorCode.CATEGORY_CLASS_NOT_FOUND,
            error_message="Category class not found for the given bot class",
        )
    return category_class_id


def validate_product_class(session: Session, bot_class_id: int) -> int:
    product_class_id = get_product_class_id_by_bot_class_id(session, bot_class_id)
    if not product_class_id:
        raise GlobalErrorException(
            error_code=ErrorCode.PRODUCT_CLASS_NOT_FOUND,
            error_message="Product class not found for the given bot class",
        )
    return product_class_id


def insert_single_brand(
    session: Session, body: InsertBrandRequest, current_user_id: UUID
):
    bot = validate_line_bot_exists(session, body.bot_uuid)
    validate_bot_ownership(session, current_user_id, bot.bot_detail_id)

    brand_class_id = validate_brand_class(session, bot.class_id)

    # 檢查品牌名稱是否已存在
    if check_brand_name_exists(session, brand_class_id, body.brand_name):
        raise GlobalErrorException(
            error_code=ErrorCode.BRAND_ALREADY_EXISTS,
            error_message=f"Brand name '{body.brand_name}' already exists",
        )

    insert_brand(session, brand_class_id, body.brand_name, body.brand_description)


def get_all_brands(session: Session, bot_uuid: UUID) -> List[BrandListView]:
    bot = validate_line_bot_exists(session, bot_uuid)
    brand_class_id = validate_brand_class(session, bot.class_id)
    return get_all_brands_by_class_id(session, brand_class_id)


def delete_brands_by_ids(
    session: Session, body: DeleteBrandRequest, current_user_id: UUID
):
    bot = validate_line_bot_exists(session, body.bot_uuid)
    validate_bot_ownership(session, current_user_id, bot.bot_detail_id)

    brand_class_id = validate_brand_class(session, bot.class_id)

    if not body.deleted_id_list:
        raise GlobalErrorException(
            error_code=ErrorCode.EMPTY_DELETE_LIST,
            error_message="Delete list cannot be empty",
        )

    delete_brands(session, brand_class_id, body.deleted_id_list)


def update_brand_by_id(
    session: Session, body: UpdateBrandRequest, current_user_id: UUID
):
    bot = validate_line_bot_exists(session, body.bot_uuid)
    validate_bot_ownership(session, current_user_id, bot.bot_detail_id)

    brand_class_id = validate_brand_class(session, bot.class_id)

    # 如果有提供 brand_name，檢查是否重複（排除自己）
    if body.brand_name is not None:
        if check_brand_name_exists_exclude_self(
            session, brand_class_id, body.brand_name, body.object_id
        ):
            raise GlobalErrorException(
                error_code=ErrorCode.BRAND_ALREADY_EXISTS,
                error_message=f"Brand name '{body.brand_name}' already exists",
            )

    # 執行更新
    success = update_brand(
        session,
        brand_class_id,
        body.object_id,
        body.brand_name,
        body.brand_description,
    )

    if not success:
        raise GlobalErrorException(
            error_code=ErrorCode.BRAND_CLASS_NOT_FOUND,
            error_message="Brand not found or does not belong to this bot",
        )


# Category service functions
def insert_single_category(
    session: Session, body: InsertCategoryRequest, current_user_id: UUID
):
    bot = validate_line_bot_exists(session, body.bot_uuid)
    validate_bot_ownership(session, current_user_id, bot.bot_detail_id)

    category_class_id = validate_category_class(session, bot.class_id)

    # 檢查類別名稱是否已存在
    if check_category_name_exists(session, category_class_id, body.category_name):
        raise GlobalErrorException(
            error_code=ErrorCode.CATEGORY_ALREADY_EXISTS,
            error_message=f"Category name '{body.category_name}' already exists",
        )

    # 檢查父類別是否存在（如果有提供）
    if body.parent_category_id:
        if not check_parent_category_exists(
            session, category_class_id, body.parent_category_id
        ):
            raise GlobalErrorException(
                error_code=ErrorCode.PARENT_CATEGORY_NOT_FOUND,
                error_message="Parent category not found",
            )

    insert_category(
        session,
        category_class_id,
        body.category_name,
        body.category_description,
        body.parent_category_id,
        str(current_user_id),  # 傳遞 owner_id
    )


def get_all_categories(session: Session, bot_uuid: UUID) -> List[CategoryListView]:
    bot = validate_line_bot_exists(session, bot_uuid)
    category_class_id = validate_category_class(session, bot.class_id)
    return get_all_categories_by_class_id(session, category_class_id)


def delete_categories_by_ids(
    session: Session, body: DeleteCategoryRequest, current_user_id: UUID
):
    bot = validate_line_bot_exists(session, body.bot_uuid)
    validate_bot_ownership(session, current_user_id, bot.bot_detail_id)

    category_class_id = validate_category_class(session, bot.class_id)

    if not body.deleted_class_id_list:
        raise GlobalErrorException(
            error_code=ErrorCode.EMPTY_DELETE_LIST,
            error_message="Delete list cannot be empty",
        )

    delete_categories(session, category_class_id, body.deleted_class_id_list)


def update_category_by_id(
    session: Session, body: UpdateCategoryRequest, current_user_id: UUID
):
    bot = validate_line_bot_exists(session, body.bot_uuid)
    validate_bot_ownership(session, current_user_id, bot.bot_detail_id)

    category_class_id = validate_category_class(
        session, bot.class_id
    )  # 如果有提供 category_name，檢查是否重複（排除自己）
    if body.category_name is not None:
        if check_category_name_exists_exclude_self(
            session, category_class_id, body.category_name, body.class_id
        ):
            raise GlobalErrorException(
                error_code=ErrorCode.CATEGORY_ALREADY_EXISTS,
                error_message=f"Category name '{body.category_name}' already exists",
            )

    # 如果有提供 parent_category_id，進行相關驗證
    if body.parent_category_id is not None:
        # 檢查父類別是否存在（0 表示設為根類別）
        if body.parent_category_id != 0:
            if not check_parent_category_exists(
                session, category_class_id, body.parent_category_id
            ):
                raise GlobalErrorException(
                    error_code=ErrorCode.PARENT_CATEGORY_NOT_FOUND,
                    error_message="Parent category not found",
                )

            # 檢查是否會造成循環引用
            if not check_category_hierarchy_valid(
                session, category_class_id, body.class_id, body.parent_category_id
            ):
                raise GlobalErrorException(
                    error_code=ErrorCode.INVALID_CATEGORY_HIERARCHY,
                    error_message="Invalid category hierarchy: circular reference detected",
                )

    # 執行更新
    success = update_category(
        session,
        category_class_id,
        body.class_id,
        body.category_name,
        body.category_description,
        body.parent_category_id,
    )

    if not success:
        raise GlobalErrorException(
            error_code=ErrorCode.CATEGORY_CLASS_NOT_FOUND,
            error_message="Category not found or does not belong to this bot",
        )


# Product service functions
def get_all_products(session: Session, bot_uuid: UUID) -> List[dict]:
    """取得所有產品"""
    bot = validate_line_bot_exists(session, bot_uuid)
    product_class_id = validate_product_class(session, bot.class_id)
    return get_products_by_class_id(session, product_class_id)


def insert_single_product(session: Session, body: InsertProductRequest, user_id: str):
    """建立單一產品"""
    bot = validate_line_bot_exists(session, body.bot_uuid)
    validate_bot_ownership(session, user_id, bot.bot_detail_id)

    # 如果沒有提供 category_id，使用主 Category class
    if body.category_id is None:
        product_class_id = validate_category_class(session, bot.class_id)
    else:
        # 如果提供了 category_id，使用指定的類別
        product_class_id = body.category_id

    # 檢查 SKU 是否已存在
    if check_product_sku_exists(session, body.sku_code):
        raise GlobalErrorException(
            error_code=ErrorCode.PRODUCT_SKU_ALREADY_EXISTS,
            error_message=f"SKU '{body.sku_code}' already exists",
        )

    # 建立產品
    insert_product(
        session=session,
        product_class_id=product_class_id,
        product_name=body.product_name,
        product_description=body.product_description,
        brand_id=body.brand_id,
        sku_code=body.sku_code,
        price=body.price,
        stock=body.stock,
        is_active=body.is_active,
        images=[img.dict() for img in body.images],
        variants=[variant.dict() for variant in body.variants],
        owner_id=user_id,
    )


def delete_products_by_ids(session: Session, body: DeleteProductRequest, user_id: str):
    """刪除產品"""
    bot = validate_line_bot_exists(session, body.bot_uuid)
    validate_bot_ownership(session, user_id, bot.bot_detail_id)
    product_class_id = validate_product_class(session, bot.class_id)

    delete_products(session, product_class_id, body.product_ids)


def update_product_by_id(session: Session, body: UpdateProductRequest, user_id: str):
    """更新產品"""
    bot = validate_line_bot_exists(session, body.bot_uuid)
    validate_bot_ownership(session, user_id, bot.bot_detail_id)
    validate_product_class(session, bot.class_id)

    # 如果更新 SKU，檢查是否重複（排除自己）
    if body.sku_code is not None:
        if check_product_sku_exists_exclude_self(
            session, body.sku_code, body.product_id
        ):
            raise GlobalErrorException(
                error_code=ErrorCode.PRODUCT_SKU_ALREADY_EXISTS,
                error_message=f"SKU '{body.sku_code}' already exists",
            )

    # 執行更新
    images_dict = None
    variants_dict = None

    if body.images is not None:
        images_dict = [img.dict() for img in body.images]

    if body.variants is not None:
        variants_dict = [variant.dict() for variant in body.variants]

    # 處理 category_id，如果是 None 則使用主 Category class
    category_id_to_use = None
    if body.category_id is not None:
        if body.category_id == 0:
            # 如果 category_id 是 0，使用主 Category class
            category_id_to_use = validate_category_class(session, bot.class_id)
        else:
            # 使用指定的類別
            category_id_to_use = body.category_id

    success = update_product(
        session=session,
        product_id=body.product_id,
        product_name=body.product_name,
        product_description=body.product_description,
        brand_id=body.brand_id,
        sku_code=body.sku_code,
        price=body.price,
        stock=body.stock,
        is_active=body.is_active,
        images=images_dict,
        variants=variants_dict,
        category_id=category_id_to_use,
    )

    if not success:
        raise GlobalErrorException(
            error_code=ErrorCode.PRODUCT_NOT_FOUND,
            error_message="Product not found",
        )
