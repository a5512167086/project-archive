from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends

from modules.ecomm.ecomm_schema import (
    BrandResponse,
    CategoryResponse,
    DeleteBrandRequest,
    DeleteCategoryRequest,
    DeleteProductRequest,
    InsertBrandRequest,
    InsertCategoryRequest,
    InsertProductRequest,
    ProductResponse,
    UpdateBrandRequest,
    UpdateCategoryRequest,
    UpdateProductRequest,
)
from modules.ecomm.ecomm_service import (
    delete_brands_by_ids,
    delete_categories_by_ids,
    delete_products_by_ids,
    get_all_brands,
    get_all_categories,
    get_all_products,
    insert_single_brand,
    insert_single_category,
    insert_single_product,
    update_brand_by_id,
    update_category_by_id,
    update_product_by_id,
)
from shared.clients.database import SessionDep
from shared.dependencies import get_current_user

brand_router = APIRouter(prefix="/brands", tags=["brands"])
category_router = APIRouter(prefix="/categories", tags=["categories"])
product_router = APIRouter(prefix="/products", tags=["products"])


@brand_router.get("/{bot_uuid}", response_model=List[BrandResponse])
def list_brands(session: SessionDep, bot_uuid: UUID):
    return get_all_brands(session, bot_uuid)


@brand_router.post("")
def create_brand(
    session: SessionDep,
    brand: InsertBrandRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    insert_single_brand(session, brand, user_id)
    session.commit()


@brand_router.delete("")
def delete_brands(
    session: SessionDep,
    delete_request: DeleteBrandRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    delete_brands_by_ids(session, delete_request, user_id)
    session.commit()


@brand_router.patch("")
def update_brand(
    session: SessionDep,
    update_request: UpdateBrandRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    update_brand_by_id(session, update_request, user_id)
    session.commit()


# Category endpoints
@category_router.get("/{bot_uuid}", response_model=List[CategoryResponse])
def list_categories(session: SessionDep, bot_uuid: UUID):
    return get_all_categories(session, bot_uuid)


@category_router.post("")
def create_category(
    session: SessionDep,
    category: InsertCategoryRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    insert_single_category(session, category, user_id)
    session.commit()


@category_router.delete("")
def delete_categories(
    session: SessionDep,
    delete_request: DeleteCategoryRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    delete_categories_by_ids(session, delete_request, user_id)
    session.commit()


@category_router.patch("")
def update_category(
    session: SessionDep,
    update_request: UpdateCategoryRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    update_category_by_id(session, update_request, user_id)
    session.commit()


# Product endpoints
@product_router.get("/{bot_uuid}", response_model=List[ProductResponse])
def list_products(session: SessionDep, bot_uuid: UUID):
    products_data = get_all_products(session, bot_uuid)
    products = []
    for product_data in products_data:
        product_detail = product_data["product_detail"]
        obj = product_data["object"]
        images = product_data["images"]
        variants = product_data["variants"]

        products.append(
            ProductResponse(
                product_id=product_detail.product_id,
                object_id=product_detail.object_id,
                product_name=obj.chinese_name,
                product_description=obj.chinese_description,
                brand_id=product_detail.brand_id,
                sku_code=product_detail.sku_code,
                price=product_detail.price,
                stock=product_detail.stock,
                is_active=product_detail.is_active,
                created_at=product_detail.created_at,
                updated_at=product_detail.updated_at,
                images=[
                    {
                        "image_id": img.image_id,
                        "image_url": img.image_url,
                        "object_id": img.object_id,
                        "display_order": img.display_order,
                    }
                    for img in images
                ],
                variants=[
                    {
                        "variant_id": variant.variant_id,
                        "object_id": variant.object_id,
                        "variant_name": variant.variant_name,
                        "sku_code": variant.sku_code,
                        "price": variant.price,
                        "stock": variant.stock,
                        "created_at": variant.created_at,
                        "updated_at": variant.updated_at,
                    }
                    for variant in variants
                ],
            )
        )

    return products


@product_router.post("")
def create_product(
    session: SessionDep,
    product: InsertProductRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    insert_single_product(session, product, user_id)
    session.commit()


@product_router.delete("")
def delete_products(
    session: SessionDep,
    delete_request: DeleteProductRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    delete_products_by_ids(session, delete_request, user_id)
    session.commit()


@product_router.patch("")
def update_product(
    session: SessionDep,
    update_request: UpdateProductRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    update_product_by_id(session, update_request, user_id)
    session.commit()
