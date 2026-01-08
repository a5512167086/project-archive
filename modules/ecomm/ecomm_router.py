import io
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from minio.error import S3Error

from modules.ecomm.ecomm_model import ProductVariant
from modules.ecomm.ecomm_schema import (
    BrandResponse,
    CategoryResponse,
    DeleteBrandRequest,
    DeleteCategoryRequest,
    DeleteOrderRequest,
    DeleteProductImageRequest,
    DeleteProductRequest,
    DeleteProductVariantRequest,
    DeleteShippingMethodRequest,
    InsertBrandRequest,
    InsertCategoryRequest,
    InsertOrderRequest,
    InsertProductVariantRequest,
    OrderResponse,
    ProductResponse,
    ShippingSettingResponse,
    UpdateBrandRequest,
    UpdateCategoryRequest,
    UpdateOrderRequest,
    UpdateProductImageRequest,
    UpdateProductRequest,
    UpdateProductVariantRequest,
    UpdateShippingSettingRequest,
)
from modules.ecomm.ecomm_service import EcommService
from shared.clients.database import SessionDep
from shared.constants.common import ModuleType
from shared.constants.error_code import ErrorCode
from shared.dependencies import BotAccessController, get_bot_access, get_current_user
from shared.exception import GlobalErrorException
from shared.services.minio_service import MinioService


def get_ecomm_service(session: SessionDep) -> EcommService:
    """依賴注入 EcommService"""
    return EcommService(session)


def get_minio_service() -> MinioService:
    """依賴注入 MinioService"""
    return MinioService()


ecomm_router = APIRouter(prefix="/ecomm", tags=["ecomm"])
brand_router = APIRouter(prefix="/brands", tags=["brands"])
category_router = APIRouter(prefix="/categories", tags=["categories"])
product_router = APIRouter(prefix="/products", tags=["products"])
order_router = APIRouter(prefix="/orders", tags=["orders"])


@ecomm_router.get("/{bot_uuid}", response_model=ShippingSettingResponse | None)
async def get_shipping_settings(
    bot_uuid: UUID,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 查看設定：User/Owner 皆可
    bot = access.verify(bot_uuid, owner_only=False)
    return await ecomm_service.get_shipping_setting(bot)


@ecomm_router.patch("")
async def update_shipping_settings(
    update_request: UpdateShippingSettingRequest,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 更新設定：僅限 Owner
    bot = access.verify(
        update_request.bot_uuid, module_name=ModuleType.Ecomm, owner_only=True
    )
    await ecomm_service.update_shipping_setting(bot.bot_detail_id, update_request)


@ecomm_router.delete("")
async def delete_shipping_settings(
    body: DeleteShippingMethodRequest,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 刪除設定：僅限 Owner
    bot = access.verify(body.bot_uuid, module_name=ModuleType.Ecomm, owner_only=True)
    await ecomm_service.delete_shipping_setting(bot, body)


@brand_router.get("/{bot_uuid}", response_model=List[BrandResponse])
def list_brands(
    bot_uuid: UUID,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 列表：User/Owner 皆可
    bot = access.verify(bot_uuid, owner_only=False)
    return ecomm_service.get_all_brands(bot)


@brand_router.post("")
def create_brand(
    brand: InsertBrandRequest,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 建立：僅限 Owner
    bot = access.verify(brand.bot_uuid, module_name=ModuleType.Ecomm, owner_only=True)
    ecomm_service.insert_single_brand(bot, brand)
    ecomm_service.session.commit()


@brand_router.delete("")
def delete_brands(
    delete_request: DeleteBrandRequest,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 刪除：僅限 Owner
    bot = access.verify(
        delete_request.bot_uuid, module_name=ModuleType.Ecomm, owner_only=True
    )
    ecomm_service.delete_brands_by_ids(bot, delete_request)
    ecomm_service.session.commit()


@brand_router.patch("")
def update_brand(
    update_request: UpdateBrandRequest,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 更新：僅限 Owner
    bot = access.verify(
        update_request.bot_uuid, module_name=ModuleType.Ecomm, owner_only=True
    )
    ecomm_service.update_brand_by_id(bot, update_request)
    ecomm_service.session.commit()


@category_router.get("/{bot_uuid}", response_model=List[CategoryResponse])
def list_categories(
    bot_uuid: UUID,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 列表：User/Owner 皆可
    bot = access.verify(bot_uuid, owner_only=False)
    category_list, category_class_id = ecomm_service.get_all_categories(bot)
    return ecomm_service.get_nested_categories(category_class_id, category_list)


@category_router.post("")
def create_category(
    category: InsertCategoryRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 建立：僅限 Owner
    bot = access.verify(
        category.bot_uuid, module_name=ModuleType.Ecomm, owner_only=True
    )
    user_id = current_user["user_id"]
    ecomm_service.insert_single_category(bot, category, user_id)
    ecomm_service.session.commit()


@category_router.delete("")
def delete_categories(
    delete_request: DeleteCategoryRequest,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 刪除：僅限 Owner
    bot = access.verify(
        delete_request.bot_uuid, module_name=ModuleType.Ecomm, owner_only=True
    )
    ecomm_service.delete_categories_by_ids(bot, delete_request)
    ecomm_service.session.commit()


@category_router.patch("")
def update_category(
    update_request: UpdateCategoryRequest,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 更新：僅限 Owner
    bot = access.verify(
        update_request.bot_uuid, module_name=ModuleType.Ecomm, owner_only=True
    )
    ecomm_service.update_category_by_id(bot, update_request)
    ecomm_service.session.commit()


@product_router.get("/{bot_uuid}", response_model=List[ProductResponse])
def list_products(
    bot_uuid: UUID,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 列表：User/Owner 皆可
    bot = access.verify(bot_uuid, owner_only=False)
    return ecomm_service.get_all_products(bot)


@product_router.post("")
def create_product(
    current_user: Annotated[dict, Depends(get_current_user)],
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
    bot_uuid: UUID = Form(...),
    product_name: str = Form(...),
    product_description: str = Form(...),
    price: int = Form(...),
    sku_code: Optional[str] = Form(None),
    stock: Optional[str] = Form(None, description="庫存數量，留空則為無限"),
    is_active: bool = Form(True, description="是否啟用產品"),
    category_id: str = Form("", description="分類ID，留空則使用根分類"),
    brand_id: str = Form("", description="品牌ID，可選"),
    images: List[UploadFile] = File([], description="產品圖片檔案"),
):
    # 建立：僅限 Owner
    bot = access.verify(bot_uuid, module_name=ModuleType.Ecomm, owner_only=True)
    user_id = current_user["user_id"]

    parsed_category_id = None
    if category_id and category_id.strip():
        try:
            parsed_category_id = int(category_id)
        except ValueError:
            raise GlobalErrorException(
                error_code=ErrorCode.INVALID_INPUT,
                error_message="Invalid category_id format",
            )

    parsed_brand_id = None
    if brand_id and brand_id.strip():
        try:
            parsed_brand_id = int(brand_id)
        except ValueError:
            raise GlobalErrorException(
                error_code=ErrorCode.INVALID_INPUT,
                error_message="Invalid brand_id format",
            )

    parsed_stock: Optional[int] = None
    if stock and stock.strip():
        try:
            parsed_stock = int(stock)
        except ValueError:
            raise GlobalErrorException(
                error_code=ErrorCode.INVALID_INPUT, error_message="Invalid stock format"
            )

    ecomm_service.insert_product(
        bot=bot,
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
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 刪除：僅限 Owner
    bot = access.verify(
        delete_request.bot_uuid, module_name=ModuleType.Ecomm, owner_only=True
    )
    ecomm_service.delete_products_by_ids(bot, delete_request)
    ecomm_service.session.commit()


@product_router.patch("")
def update_product(
    update_request: UpdateProductRequest,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 更新：僅限 Owner
    bot = access.verify(
        update_request.bot_uuid, module_name=ModuleType.Ecomm, owner_only=True
    )
    ecomm_service.update_product_by_id(bot, update_request)
    ecomm_service.session.commit()


@product_router.post("/variants", response_model=ProductVariant)
def create_product_variant(
    variant: InsertProductVariantRequest,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 建立變體：僅限 Owner
    bot = access.verify(variant.bot_uuid, module_name=ModuleType.Ecomm, owner_only=True)
    new_variant = ecomm_service.insert_product_variant(bot, variant)
    ecomm_service.session.commit()
    return new_variant


@product_router.patch("/variants")
def update_product_variant(
    update_request: UpdateProductVariantRequest,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 更新變體：僅限 Owner
    bot = access.verify(
        update_request.bot_uuid, module_name=ModuleType.Ecomm, owner_only=True
    )
    ecomm_service.update_product_variant(bot, update_request)
    ecomm_service.session.commit()


@product_router.delete("/variants")
def delete_product_variants(
    delete_request: DeleteProductVariantRequest,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 刪除變體：僅限 Owner
    bot = access.verify(
        delete_request.bot_uuid, module_name=ModuleType.Ecomm, owner_only=True
    )
    ecomm_service.delete_product_variants(bot, delete_request)
    ecomm_service.session.commit()


@product_router.get("/images/{file_name}")
async def get_product_image(
    file_name: str,
    minio_service: Annotated[MinioService, Depends(get_minio_service)],
):
    # 公開資源，無需驗證
    try:
        response = minio_service.client.get_object("product-images", file_name)
        image_data = response.read()
        content_type = response.headers.get("Content-Type", "application/octet-stream")

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

        return StreamingResponse(
            io.BytesIO(image_data),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600",
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


@product_router.post("/images/upload")
def upload_product_image(
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
    bot_uuid: UUID = Form(...),
    product_id: UUID = Form(...),
    images: List[UploadFile] = File(...),
):
    # 上傳圖片：僅限 Owner
    bot = access.verify(bot_uuid, module_name=ModuleType.Ecomm, owner_only=True)
    ecomm_service.upload_product_image(bot, product_id, images)
    ecomm_service.session.commit()


@product_router.patch("/images")
def update_product_image(
    update_request: UpdateProductImageRequest,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 更新圖片：僅限 Owner
    bot = access.verify(
        update_request.bot_uuid, module_name=ModuleType.Ecomm, owner_only=True
    )
    ecomm_service.update_product_image(bot, update_request)
    ecomm_service.session.commit()


@product_router.delete("/images")
def delete_product_image(
    delete_request: DeleteProductImageRequest,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 刪除圖片：僅限 Owner
    bot = access.verify(
        delete_request.bot_uuid, module_name=ModuleType.Ecomm, owner_only=True
    )
    ecomm_service.delete_product_image(bot, delete_request)
    ecomm_service.session.commit()


@order_router.get("/{bot_uuid}", response_model=List[OrderResponse])
def list_bot_orders(
    bot_uuid: UUID,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 查詢所有訂單 (後台)：僅限 Owner
    bot = access.verify(bot_uuid, module_name=ModuleType.Ecomm, owner_only=True)
    return ecomm_service.get_all_orders(bot)


@order_router.get("/user/{bot_uuid}", response_model=List[OrderResponse])
def list_user_orders(
    bot_uuid: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 查詢個人訂單：User 可用
    bot = access.verify(bot_uuid, owner_only=False)
    user_id = current_user["user_id"]

    return ecomm_service.get_all_user_orders(bot, user_id)


@order_router.post("")
async def create_order(
    order: InsertOrderRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 建立訂單：User 可用
    bot = access.verify(order.bot_uuid, module_name=ModuleType.Ecomm, owner_only=False)
    user_id = current_user["user_id"]

    await ecomm_service.insert_order(bot, order, user_id)
    ecomm_service.session.commit()


@order_router.patch("")
def update_order(
    update_request: UpdateOrderRequest,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 修改訂單狀態：僅限 Owner
    bot = access.verify(
        update_request.bot_uuid, module_name=ModuleType.Ecomm, owner_only=True
    )
    ecomm_service.update_order_by_id(bot, update_request)
    ecomm_service.session.commit()


@order_router.delete("")
def delete_orders(
    delete_request: DeleteOrderRequest,
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    # 刪除訂單：僅限 Owner
    bot = access.verify(
        delete_request.bot_uuid, module_name=ModuleType.Ecomm, owner_only=True
    )
    ecomm_service.delete_orders_by_ids(bot, delete_request)
    ecomm_service.session.commit()
