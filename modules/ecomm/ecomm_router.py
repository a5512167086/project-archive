import io
from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from minio.error import S3Error

from modules.ecomm.ecomm_schema import (
    BrandResponse,
    CategoryResponse,
    DeleteBrandRequest,
    DeleteCategoryRequest,
    DeleteProductRequest,
    InsertBrandRequest,
    InsertCategoryRequest,
    ProductResponse,
    UpdateBrandRequest,
    UpdateCategoryRequest,
    UpdateProductRequest,
)
from modules.ecomm.ecomm_service import EcommService
from shared.clients.database import SessionDep
from shared.constants.error_code import ErrorCode
from shared.dependencies import get_current_user
from shared.exception import GlobalErrorException
from shared.services.minio_service import MinioService


def get_ecomm_service(session: SessionDep) -> EcommService:
    """依賴注入 EcommService"""
    return EcommService(session)


def get_minio_service() -> MinioService:
    """依賴注入 MinioService"""
    return MinioService()


brand_router = APIRouter(prefix="/brands", tags=["brands"])
category_router = APIRouter(prefix="/categories", tags=["categories"])
product_router = APIRouter(prefix="/products", tags=["products"])
# 產品圖片代理路由
product_image_router = APIRouter(prefix="/product-images", tags=["product-images"])


@brand_router.get("/{bot_uuid}", response_model=List[BrandResponse])
def list_brands(
    bot_uuid: UUID, ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)]
):
    return ecomm_service.get_all_brands(bot_uuid)


@brand_router.post("")
def create_brand(
    brand: InsertBrandRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
):
    user_id = current_user["user_id"]
    ecomm_service.insert_single_brand(brand, user_id)
    ecomm_service.session.commit()


@brand_router.delete("")
def delete_brands(
    delete_request: DeleteBrandRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
):
    user_id = current_user["user_id"]
    ecomm_service.delete_brands_by_ids(delete_request, user_id)
    ecomm_service.session.commit()


@brand_router.patch("")
def update_brand(
    update_request: UpdateBrandRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
):
    user_id = current_user["user_id"]
    ecomm_service.update_brand_by_id(update_request, user_id)
    ecomm_service.session.commit()


# Category endpoints
@category_router.get("/{bot_uuid}", response_model=List[CategoryResponse])
def list_categories(
    bot_uuid: UUID, ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)]
):
    category_list, category_class_id = ecomm_service.get_all_categories(bot_uuid)
    return ecomm_service.get_nested_categories(category_class_id, category_list)


@category_router.post("")
def create_category(
    category: InsertCategoryRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
):
    user_id = current_user["user_id"]
    ecomm_service.insert_single_category(category, user_id)
    ecomm_service.session.commit()


@category_router.delete("")
def delete_categories(
    delete_request: DeleteCategoryRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
):
    user_id = current_user["user_id"]
    ecomm_service.delete_categories_by_ids(delete_request, user_id)
    ecomm_service.session.commit()


@category_router.patch("")
def update_category(
    update_request: UpdateCategoryRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
):
    user_id = current_user["user_id"]
    ecomm_service.update_category_by_id(update_request, user_id)
    ecomm_service.session.commit()


# Product endpoints
@product_router.get("/{bot_uuid}", response_model=List[ProductResponse])
def list_products(
    bot_uuid: UUID, ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)]
):
    return ecomm_service.get_all_products(bot_uuid)


@product_router.post("")
def create_product(
    current_user: Annotated[dict, Depends(get_current_user)],
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    bot_uuid: UUID = Form(...),
    product_name: str = Form(...),
    product_description: str = Form(...),
    sku_code: str = Form(...),
    price: int = Form(...),
    stock: str = Form("", description="庫存數量，留空則預設為0"),
    is_active: bool = Form(True, description="是否啟用產品"),
    category_id: str = Form("", description="分類ID，留空則使用根分類"),
    brand_id: str = Form("", description="品牌ID，可選"),
    images: List[UploadFile] = File([], description="產品圖片檔案"),
):
    """創建產品並上傳圖片到 MinIO"""
    user_id = current_user["user_id"]

    # 處理可選的整數參數
    parsed_category_id = None
    parsed_brand_id = None
    parsed_stock = 0  # 預設庫存為 0

    if category_id and category_id.strip():
        try:
            parsed_category_id = int(category_id)
        except ValueError:
            raise GlobalErrorException(
                error_code=ErrorCode.INVALID_INPUT,
                error_message="Invalid category_id format",
            )

    if brand_id and brand_id.strip():
        try:
            parsed_brand_id = int(brand_id)
        except ValueError:
            raise GlobalErrorException(
                error_code=ErrorCode.INVALID_INPUT,
                error_message="Invalid brand_id format",
            )

    if stock and stock.strip():
        try:
            parsed_stock = int(stock)
        except ValueError:
            raise GlobalErrorException(
                error_code=ErrorCode.INVALID_INPUT,
                error_message="Invalid stock format",
            )

    # 使用新的 service 函數來處理產品創建和圖片上傳
    ecomm_service.insert_product(
        bot_uuid=bot_uuid,
        product_name=product_name,
        product_description=product_description,
        category_id=parsed_category_id,
        brand_id=parsed_brand_id,
        sku_code=sku_code,
        price=price,
        stock=parsed_stock,
        is_active=is_active,
        images=images,
        user_id=user_id,
    )
    ecomm_service.session.commit()


@product_router.delete("")
def delete_products(
    delete_request: DeleteProductRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
):
    user_id = current_user["user_id"]
    ecomm_service.delete_products_by_ids(delete_request, user_id)
    ecomm_service.session.commit()


@product_router.patch("")
def update_product(
    update_request: UpdateProductRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
):
    user_id = current_user["user_id"]
    ecomm_service.update_product_by_id(update_request, user_id)
    ecomm_service.session.commit()


# Product Image proxy endpoints
@product_image_router.get("/{bucket_name}/{file_name}")
async def get_product_image(
    bucket_name: str,
    file_name: str,
    minio_service: Annotated[MinioService, Depends(get_minio_service)],
):
    """
    代理 MinIO 產品圖片請求

    Args:
        bucket_name: MinIO bucket 名稱
        file_name: 圖片檔案名稱

    Returns:
        StreamingResponse: 圖片內容
    """
    try:
        # 從 MinIO 獲取圖片
        response = minio_service.client.get_object(bucket_name, file_name)

        # 讀取圖片內容
        image_data = response.read()

        # 獲取內容類型
        content_type = response.headers.get("Content-Type", "application/octet-stream")

        # 如果沒有 Content-Type，根據檔案副檔名推測
        if content_type == "application/octet-stream":
            file_extension = file_name.lower().split(".")[-1]
            content_type_map = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "gif": "image/gif",
                "webp": "image/webp",
                "bmp": "image/bmp",
                "svg": "image/svg+xml",
            }
            content_type = content_type_map.get(file_extension, "image/jpeg")

        # 返回圖片內容
        return StreamingResponse(
            io.BytesIO(image_data),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600",  # 快取 1 小時
                "Content-Length": str(len(image_data)),
            },
        )

    except S3Error as e:
        if e.code == "NoSuchKey":
            raise HTTPException(status_code=404, detail="Product image not found")
        elif e.code == "NoSuchBucket":
            raise HTTPException(status_code=404, detail="Bucket not found")
        else:
            raise HTTPException(status_code=500, detail=f"MinIO error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@product_image_router.get("/product/{bucket_name}/{file_name}")
async def get_product_image_legacy(
    bucket_name: str,
    file_name: str,
    minio_service: Annotated[MinioService, Depends(get_minio_service)],
):
    """
    代理 MinIO 產品圖片請求 (舊版 URL 兼容)

    Args:
        bucket_name: MinIO bucket 名稱
        file_name: 圖片檔案名稱

    Returns:
        StreamingResponse: 圖片內容
    """
    return await get_product_image(bucket_name, file_name, minio_service)
