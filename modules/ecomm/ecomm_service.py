from typing import List, Optional
from uuid import UUID

from fastapi import UploadFile
from sqlmodel import Session

from modules.bot.bot_service import BotService
from modules.ecomm.ecomm_command import EcommCommand
from modules.ecomm.ecomm_model import (
    BrandListView,
    CategoryListView,
    ShippingOption,
    ShippingSetting,
)
from modules.ecomm.ecomm_query import EcommQuery
from modules.ecomm.ecomm_schema import (
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
    ProductImageResponse,
    ProductResponse,
    UpdateBrandRequest,
    UpdateCategoryRequest,
    UpdateOrderRequest,
    UpdateProductImageRequest,
    UpdateProductRequest,
    UpdateProductVariantRequest,
    UpdateShippingSettingRequest,
)
from shared.constants.config import BACKEND_URL
from shared.constants.error_code import ErrorCode
from shared.exception import GlobalErrorException
from shared.queries.group_query import is_user_in_group
from shared.services.group_service import GroupService
from shared.services.minio_service import (
    delete_product_image,
    upload_product_images,
)


class EcommService:
    def __init__(self, session: Session):
        self.session = session
        self.command = EcommCommand(session)
        self.query = EcommQuery(session)
        self.bot_service = BotService(session)
        self.group_service = GroupService(session)

    def get_nested_categories(
        self, category_class_id: int, category_list: List[CategoryListView]
    ):
        category_dict = {}
        for cat in category_list:
            cat_dict = cat.model_dump() if hasattr(cat, "model_dump") else dict(cat)

            if cat_dict.get("parent_class_id") == category_class_id:
                cat_dict["parent_class_id"] = None

            cat_dict["children"] = []
            category_dict[cat_dict["class_id"]] = cat_dict

        root_categories = []
        for cat in category_dict.values():
            parent_id = cat.get("parent_class_id")
            if parent_id and parent_id in category_dict:
                category_dict[parent_id]["children"].append(cat)
            else:
                root_categories.append(cat)
        return root_categories

    def validate_brand_class(self, bot_class_id: int) -> int:
        brand_class_id = self.query.get_brand_class_id_by_bot_class_id(bot_class_id)
        if not brand_class_id:
            raise GlobalErrorException(
                error_code=ErrorCode.BRAND_CLASS_NOT_FOUND,
                error_message="Brand class not found for the given bot class",
            )
        return brand_class_id

    def validate_category_class(self, bot_class_id: int) -> int:
        category_class_id = self.query.get_category_class_id_by_bot_class_id(
            bot_class_id
        )
        if not category_class_id:
            raise GlobalErrorException(
                error_code=ErrorCode.CATEGORY_CLASS_NOT_FOUND,
                error_message="Category class not found for the given bot class",
            )
        return category_class_id

    def insert_single_brand(self, body: InsertBrandRequest, current_user_id: UUID):
        bot = self.bot_service.validate_line_bot_exists(body.bot_uuid)
        self.bot_service.validate_bot_ownership(current_user_id, bot.bot_detail_id)

        brand_class_id = self.validate_brand_class(bot.class_id)

        # 檢查品牌名稱是否已存在
        if self.query.check_brand_name_exists(brand_class_id, body.brand_name):
            raise GlobalErrorException(
                error_code=ErrorCode.BRAND_ALREADY_EXISTS,
                error_message=f"Brand name '{body.brand_name}' already exists",
            )

        self.command.insert_brand(
            brand_class_id, body.brand_name, body.brand_description
        )

    def get_all_brands(self, bot_uuid: UUID) -> List[BrandListView]:
        bot = self.bot_service.validate_line_bot_exists(bot_uuid)
        brand_class_id = self.validate_brand_class(bot.class_id)
        return self.query.get_all_brands_by_class_id(brand_class_id)

    def delete_brands_by_ids(self, body: DeleteBrandRequest, current_user_id: UUID):
        bot = self.bot_service.validate_line_bot_exists(body.bot_uuid)
        self.bot_service.validate_bot_ownership(current_user_id, bot.bot_detail_id)

        brand_class_id = self.validate_brand_class(bot.class_id)

        if not body.deleted_id_list:
            raise GlobalErrorException(
                error_code=ErrorCode.EMPTY_DELETE_LIST,
                error_message="Delete list cannot be empty",
            )

        self.command.delete_brands(brand_class_id, body.deleted_id_list)

    def update_brand_by_id(self, body: UpdateBrandRequest, current_user_id: UUID):
        bot = self.bot_service.validate_line_bot_exists(body.bot_uuid)
        self.bot_service.validate_bot_ownership(current_user_id, bot.bot_detail_id)

        brand_class_id = self.validate_brand_class(bot.class_id)

        # 如果有提供 brand_name，檢查是否重複（排除自己）
        if body.brand_name is not None:
            if self.query.check_brand_name_exists_exclude_self(
                brand_class_id, body.brand_name, body.object_id
            ):
                raise GlobalErrorException(
                    error_code=ErrorCode.BRAND_ALREADY_EXISTS,
                    error_message=f"Brand name '{body.brand_name}' already exists",
                )

        # 執行更新
        success = self.command.update_brand(
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

    # Category service methods
    def insert_single_category(
        self, body: InsertCategoryRequest, current_user_id: UUID
    ):
        bot = self.bot_service.validate_line_bot_exists(body.bot_uuid)
        self.bot_service.validate_bot_ownership(current_user_id, bot.bot_detail_id)

        category_class_id = self.validate_category_class(bot.class_id)

        # 檢查類別名稱是否已存在
        if self.query.check_category_name_exists(category_class_id, body.category_name):
            raise GlobalErrorException(
                error_code=ErrorCode.CATEGORY_ALREADY_EXISTS,
                error_message=f"Category name '{body.category_name}' already exists",
            )

        # 檢查父類別是否存在（如果有提供）
        if body.parent_category_id:
            if not self.query.check_parent_category_exists(body.parent_category_id):
                raise GlobalErrorException(
                    error_code=ErrorCode.PARENT_CATEGORY_NOT_FOUND,
                    error_message="Parent category not found",
                )

        self.command.insert_category(
            category_class_id,
            body.category_name,
            body.category_description,
            body.parent_category_id,
            str(current_user_id),  # 傳遞 owner_id
        )

    def get_all_categories(self, bot_uuid: UUID) -> List[CategoryListView]:
        bot = self.bot_service.validate_line_bot_exists(bot_uuid)
        category_class_id = self.validate_category_class(bot.class_id)
        return self.query.get_all_categories_by_class_id(
            category_class_id
        ), category_class_id

    def delete_categories_by_ids(
        self, body: DeleteCategoryRequest, current_user_id: UUID
    ):
        bot = self.bot_service.validate_line_bot_exists(body.bot_uuid)
        self.bot_service.validate_bot_ownership(current_user_id, bot.bot_detail_id)

        category_class_id = self.validate_category_class(bot.class_id)
        self.command.move_products_to_root_category(
            category_class_id, body.deleted_class_id_list
        )
        if not body.deleted_class_id_list:
            raise GlobalErrorException(
                error_code=ErrorCode.EMPTY_DELETE_LIST,
                error_message="Delete list cannot be empty",
            )
        if category_class_id in body.deleted_class_id_list:
            raise GlobalErrorException(
                error_code=ErrorCode.CATEGORY_INVALID_DELETE_LIST,
                error_message="Root category cannot be deleted",
            )

        self.command.delete_categories(body.deleted_class_id_list)

    def update_category_by_id(self, body: UpdateCategoryRequest, current_user_id: UUID):
        bot = self.bot_service.validate_line_bot_exists(body.bot_uuid)
        self.bot_service.validate_bot_ownership(current_user_id, bot.bot_detail_id)
        category_class_id = self.validate_category_class(bot.class_id)

        if body.category_name is not None:
            if self.query.check_category_name_exists_exclude_self(
                category_class_id, body.category_name, body.class_id
            ):
                raise GlobalErrorException(
                    error_code=ErrorCode.CATEGORY_ALREADY_EXISTS,
                    error_message=f"Category name '{body.category_name}' already exists",
                )

        if body.parent_category_id is not None:
            if body.parent_category_id != 0:
                if not self.query.check_parent_category_exists(body.parent_category_id):
                    raise GlobalErrorException(
                        error_code=ErrorCode.PARENT_CATEGORY_NOT_FOUND,
                        error_message="Parent category not found",
                    )

        self.command.update_category(
            category_class_id,
            body.class_id,
            body.category_name,
            body.category_description,
            body.parent_category_id,
        )

        if not self.query.check_category_hierarchy_valid(
            category_class_id, body.parent_category_id
        ):
            raise GlobalErrorException(
                error_code=ErrorCode.INVALID_CATEGORY_HIERARCHY,
                error_message="Invalid category hierarchy: circular reference detected",
            )

    # Product service methods
    def get_all_products(self, bot_uuid: UUID) -> List[ProductResponse]:
        bot = self.bot_service.validate_line_bot_exists(bot_uuid)
        category_class_id = self.validate_category_class(bot.class_id)
        category_ids = self.query.get_all_categories_by_class_id(category_class_id)
        all_category_ids = [cat.class_id for cat in category_ids]
        all_category_ids.append(category_class_id)
        products_data = self.query.get_all_products_view(all_category_ids)

        if not products_data:
            return []

        object_ids = [p.object_id for p in products_data]
        all_images = self.query.get_product_images_by_object_ids(object_ids)
        all_variants = self.query.get_product_variants_by_object_ids(object_ids)

        images_map = {}
        for img in all_images:
            if img.object_id not in images_map:
                images_map[img.object_id] = []
            images_map[img.object_id].append(
                ProductImageResponse(
                    image_id=img.image_id,
                    filename=img.filename,
                    image_url=f"{BACKEND_URL}/products/images/{img.filename}",
                    is_primary=img.is_primary,
                )
            )

        variants_map = {}
        for var in all_variants:
            if var.object_id not in variants_map:
                variants_map[var.object_id] = []
            variants_map[var.object_id].append(var)

        products = []
        for product_data in products_data:
            images = images_map.get(product_data.object_id, [])
            variants = variants_map.get(product_data.object_id, [])
            products.append(
                ProductResponse(
                    product_id=product_data.product_id,
                    object_id=product_data.object_id,
                    product_name=product_data.product_name,
                    product_description=product_data.product_description,
                    brand_id=product_data.brand_id,
                    category_id=product_data.category_id
                    if product_data.category_id != category_class_id
                    else None,
                    sku_code=product_data.sku_code,
                    price=product_data.price,
                    stock=product_data.stock,
                    is_active=product_data.is_active,
                    created_at=product_data.created_at,
                    updated_at=product_data.updated_at,
                    images=images,
                    variants=variants,
                )
            )

        return products

    def insert_product(
        self,
        bot_uuid: UUID,
        product_name: str,
        product_description: str,
        sku_code: Optional[str],
        price: int,
        stock: Optional[int],
        is_active: bool,
        images: List[UploadFile],
        user_id: str,
        category_id: int = None,
        brand_id: int = None,
    ):
        """建立單一產品並上傳圖片到 MinIO"""
        bot = self.bot_service.validate_line_bot_exists(bot_uuid)
        self.bot_service.validate_bot_ownership(user_id, bot.bot_detail_id)

        # 如果沒有提供 category_id，使用根 Category class
        if category_id is None:
            product_class_id = self.validate_category_class(bot.class_id)
        else:
            # 如果提供了 category_id，使用指定的類別
            product_class_id = category_id

        # 檢查 SKU 是否已存在
        if sku_code and self.query.check_product_sku_exists(sku_code):
            raise GlobalErrorException(
                error_code=ErrorCode.PRODUCT_SKU_ALREADY_EXISTS,
                error_message=f"SKU '{sku_code}' already exists",
            )

        # 在確定要創建產品時，才上傳圖片到 MinIO
        uploaded_images = []
        if images and len(images) > 0:
            # 檢查是否有實際的圖片檔案（不是空檔案）
            valid_images = [img for img in images if img.filename and img.size > 0]
            if valid_images:
                uploaded_images = upload_product_images(valid_images)
                # Set is_primary for the first image
                if uploaded_images:
                    for i, img_data in enumerate(uploaded_images):
                        img_data["is_primary"] = i == 0

        # 建立產品
        self.command.insert_product(
            product_class_id=product_class_id,
            product_name=product_name,
            product_description=product_description,
            brand_id=brand_id,
            sku_code=sku_code,
            price=price,
            stock=stock,
            is_active=is_active,
            images=uploaded_images,
            owner_id=user_id,
        )

    def delete_products_by_ids(self, body: DeleteProductRequest, user_id: str):
        """刪除產品"""
        bot = self.bot_service.validate_line_bot_exists(body.bot_uuid)
        self.bot_service.validate_bot_ownership(user_id, bot.bot_detail_id)
        self.validate_brand_class(bot.class_id)
        self.command.delete_products(body.product_ids)

    def update_product_by_id(self, body: UpdateProductRequest, user_id: str):
        """更新產品"""
        bot = self.bot_service.validate_line_bot_exists(body.bot_uuid)
        self.bot_service.validate_bot_ownership(user_id, bot.bot_detail_id)
        self.validate_brand_class(bot.class_id)

        # 如果更新 SKU，檢查是否重複（排除自己）
        if body.sku_code is not None:
            if self.query.check_product_sku_exists_exclude_self(
                body.sku_code, body.product_id
            ):
                raise GlobalErrorException(
                    error_code=ErrorCode.PRODUCT_SKU_ALREADY_EXISTS,
                    error_message=f"SKU '{body.sku_code}' already exists",
                )
        if body.sku_code == "":
            body.sku_code = None

        category_id_to_use = None
        if body.category_id is None:
            category_id_to_use = self.validate_category_class(bot.class_id)
        else:
            category_id_to_use = body.category_id

        success = self.command.update_product(
            product_id=body.product_id,
            product_name=body.product_name,
            product_description=body.product_description,
            brand_id=body.brand_id,
            sku_code=body.sku_code,
            price=body.price,
            stock=body.stock,
            is_active=body.is_active,
            category_id=category_id_to_use,
        )

        if not success:
            raise GlobalErrorException(
                error_code=ErrorCode.PRODUCT_NOT_FOUND,
                error_message="Product not found",
            )

    # Shipping service methods
    async def get_shipping_setting(self, bot_uuid: UUID) -> ShippingSetting:
        bot = self.bot_service.validate_line_bot_exists(bot_uuid)
        bot_uuid_str = str(bot.bot_detail_id)
        setting = await self.query.get_shipping_setting_by_bot_uuid(bot_uuid_str)
        return setting

    async def update_shipping_setting(
        self, body: UpdateShippingSettingRequest, current_user_id: UUID
    ):
        bot = self.bot_service.validate_line_bot_exists(body.bot_uuid)
        self.bot_service.validate_bot_ownership(current_user_id, bot.bot_detail_id)

        methods = [option.method for option in body.shipping_options]
        if len(methods) != len(set(methods)):
            raise GlobalErrorException(
                error_code=ErrorCode.SHIPPING_SETTING_ALREADY_EXISTS,
                error_message="Duplicate shipping methods are not allowed",
            )

        bot_uuid_str = str(bot.bot_detail_id)
        converted_options = [
            ShippingOption(**option.model_dump()) for option in body.shipping_options
        ]

        await self.command.update_shipping_setting(bot_uuid_str, converted_options)

    async def delete_shipping_setting(
        self, body: DeleteShippingMethodRequest, current_user_id: UUID
    ):
        bot = self.bot_service.validate_line_bot_exists(body.bot_uuid)
        self.bot_service.validate_bot_ownership(current_user_id, bot.bot_detail_id)

        bot_uuid_str = str(bot.bot_detail_id)
        setting = await self.query.get_shipping_setting_by_bot_uuid(bot_uuid_str)
        if not setting:
            raise GlobalErrorException(
                error_code=ErrorCode.SHIPPING_SETTING_NOT_FOUND,
                error_message="Shipping setting not found",
            )

        setting.shipping_options = [
            option
            for option in setting.shipping_options
            if option.method != body.method
        ]

        await self.command.update_shipping_setting(
            bot_uuid_str, setting.shipping_options
        )

    async def delete_all_shipping_settings(self, bot_uuid: UUID, current_user_id: UUID):
        bot = self.bot_service.validate_line_bot_exists(bot_uuid)
        self.bot_service.validate_bot_ownership(current_user_id, bot.bot_detail_id)
        bot_uuid_str = str(bot.bot_detail_id)
        self.command.delete_all_shipping_setting(bot_uuid_str)

    # Order service methods
    def validate_order_class(self, bot_class_id: int) -> int:
        order_class_id = self.query.get_order_class_id_by_bot_class_id(bot_class_id)
        if not order_class_id:
            raise GlobalErrorException(
                error_code=ErrorCode.ORDER_CLASS_NOT_FOUND,
                error_message="Order class not found for the given bot class",
            )
        return order_class_id

    def get_all_orders(self, user_id: UUID, bot_uuid: UUID) -> List[OrderResponse]:
        bot = self.bot_service.validate_line_bot_exists(bot_uuid)
        self.bot_service.validate_bot_ownership(user_id, bot.bot_detail_id)
        order_class_id = self.validate_order_class(bot.class_id)
        orders_data = self.query.get_all_orders_view(order_class_id)
        orders = []
        for order_data in orders_data:
            order_items_data = self.query.get_order_items_by_object_id(
                order_data.object_id
            )
            order_items_schema = []
            for item_data in order_items_data:
                order_items_schema.append({
                    "product_id": item_data.product_id,
                    "variant_id": item_data.variant_id,
                    "quantity": item_data.quantity,
                    "unit_price": item_data.unit_price,
                    "subtotal": item_data.subtotal,
                })
            orders.append(
                OrderResponse(
                    **order_data.model_dump(),
                    items=order_items_schema,
                )
            )
        return orders

    def get_all_user_orders(self, user_id: UUID, bot_uuid: UUID) -> List[OrderResponse]:
        bot = self.bot_service.validate_line_bot_exists(bot_uuid)
        bot_group = self.group_service.validate_group_exist_in_bot(
            bot.class_id, "Users"
        )
        if not is_user_in_group(self.session, bot_group.group_id, user_id):
            raise GlobalErrorException(
                error_code=ErrorCode.USER_NOT_IN_BOT_GROUP,
                error_message="User is not a member of this bot's group.",
            )
        order_class_id = self.validate_order_class(bot.class_id)
        orders_data = self.query.get_all_user_orders_view(user_id, order_class_id)
        orders = []
        for order_data in orders_data:
            order_items_data = self.query.get_order_items_by_object_id(
                order_data.object_id
            )
            order_items_schema = []
            for item_data in order_items_data:
                order_items_schema.append({
                    "product_id": item_data.product_id,
                    "variant_id": item_data.variant_id,
                    "quantity": item_data.quantity,
                    "unit_price": item_data.unit_price,
                    "subtotal": item_data.subtotal,
                })
            orders.append(
                OrderResponse(
                    **order_data.model_dump(),
                    items=order_items_schema,
                )
            )
        return orders

    async def insert_order(self, body: InsertOrderRequest, user_id: str):
        bot = self.bot_service.validate_line_bot_exists(body.bot_uuid)
        bot_group = self.group_service.validate_group_exist_in_bot(
            bot.class_id, "Users"
        )
        if not is_user_in_group(self.session, bot_group.group_id, user_id):
            raise GlobalErrorException(
                error_code=ErrorCode.USER_NOT_IN_BOT_GROUP,
                error_message="User is not a member of this bot's group.",
            )

        order_class_id = self.validate_order_class(bot.class_id)

        # Get shipping setting and fee
        shipping_setting = await self.query.get_shipping_setting_by_bot_uuid(
            str(body.bot_uuid)
        )
        if not shipping_setting:
            raise GlobalErrorException(
                error_code=ErrorCode.SHIPPING_SETTING_NOT_FOUND,
                error_message="Shipping settings not found for this bot.",
            )

        shipping_fee = 0
        found_shipping_method = False
        for option in shipping_setting.shipping_options:
            if option.method == body.shipping_method:
                shipping_fee = option.fee
                found_shipping_method = True
                break

        if not found_shipping_method:
            raise GlobalErrorException(
                error_code=ErrorCode.INVALID_INPUT,
                error_message=f"Shipping method '{body.shipping_method}' is not valid or enabled.",
            )

        # Fetch product details for each item to get unit_price and subtotal
        processed_items = []
        for item in body.items:
            product_detail = self.query.get_product_by_id(item.product_id)
            if not product_detail:
                raise GlobalErrorException(
                    error_code=ErrorCode.PRODUCT_NOT_FOUND,
                    error_message=f"Product with ID {item.product_id} not found",
                )

            unit_price = product_detail.price
            subtotal = unit_price * item.quantity

            processed_items.append({
                "product_id": item.product_id,
                "variant_id": item.variant_id,
                "quantity": item.quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
            })

        # Calculate total_amount based on processed_items
        total_amount = sum(item["subtotal"] for item in processed_items) + shipping_fee

        self.command.insert_order(
            order_class_id=order_class_id,
            total_amount=total_amount,
            payment_method=body.payment_method,
            payment_status="unpaid",
            shipping_method=body.shipping_method,
            shipping_fee=shipping_fee,
            recipient_name=body.recipient_name,
            recipient_phone=body.recipient_phone,
            shipping_address=body.shipping_address,
            items=processed_items,
            owner_id=user_id,
            notes=body.notes,
        )

    def update_order_by_id(self, body: UpdateOrderRequest, user_id: str):
        bot = self.bot_service.validate_line_bot_exists(body.bot_uuid)
        self.bot_service.validate_bot_ownership(user_id, bot.bot_detail_id)
        self.validate_order_class(bot.class_id)

        success = self.command.update_order(
            order_id=body.order_id,
            status=body.status,
            payment_status=body.payment_status,
            tracking_number=body.tracking_number,
        )

        if not success:
            raise GlobalErrorException(
                error_code=ErrorCode.ORDER_NOT_FOUND,
                error_message="Order not found",
            )

    def delete_orders_by_ids(self, body: DeleteOrderRequest, user_id: str):
        bot = self.bot_service.validate_line_bot_exists(body.bot_uuid)
        self.bot_service.validate_bot_ownership(user_id, bot.bot_detail_id)
        self.validate_order_class(bot.class_id)
        self.command.delete_orders(body.order_ids)

    # Product Variant service methods
    def insert_product_variant(self, body: InsertProductVariantRequest, user_id: str):
        """建立產品變體"""
        bot = self.bot_service.validate_line_bot_exists(body.bot_uuid)
        self.bot_service.validate_bot_ownership(user_id, bot.bot_detail_id)

        # 驗證產品是否存在
        product = self.query.get_product_by_id(body.product_id)
        if not product:
            raise GlobalErrorException(
                error_code=ErrorCode.PRODUCT_NOT_FOUND,
                error_message="Product not found",
            )

        # 檢查 SKU 是否重複
        if body.sku_code:
            if self.query.check_product_sku_exists(
                body.sku_code
            ) or self.query.check_variant_sku_exists(body.sku_code):
                raise GlobalErrorException(
                    error_code=ErrorCode.PRODUCT_SKU_ALREADY_EXISTS,
                    error_message=f"SKU '{body.sku_code}' already exists",
                )

        return self.command.insert_product_variant(
            object_id=product.object_id,
            variant_name=body.variant_name,
            sku_code=body.sku_code,
            price=body.price,
            stock=body.stock,
        )

    def update_product_variant(self, body: UpdateProductVariantRequest, user_id: str):
        """更新產品變體"""
        bot = self.bot_service.validate_line_bot_exists(body.bot_uuid)
        self.bot_service.validate_bot_ownership(user_id, bot.bot_detail_id)

        # 驗證變體是否存在
        variant = self.query.get_variant_by_id(body.variant_id)
        if not variant:
            raise GlobalErrorException(
                error_code=ErrorCode.PRODUCT_VARIANT_NOT_FOUND,
                error_message="Product variant not found",
            )

        # 檢查 SKU 是否重複
        if body.sku_code:
            if self.query.check_variant_sku_exists_exclude_self(
                body.sku_code, body.variant_id
            ) or (body.sku_code and self.query.check_product_sku_exists(body.sku_code)):
                raise GlobalErrorException(
                    error_code=ErrorCode.PRODUCT_SKU_ALREADY_EXISTS,
                    error_message=f"SKU '{body.sku_code}' already exists",
                )
        if body.sku_code == "":
            body.sku_code = None

        success = self.command.update_product_variant(
            variant_id=body.variant_id,
            variant_name=body.variant_name,
            sku_code=body.sku_code,
            price=body.price,
            stock=body.stock,
        )

        if not success:
            raise GlobalErrorException(
                error_code=ErrorCode.PRODUCT_VARIANT_NOT_FOUND,
                error_message="Product variant not found",
            )

    def delete_product_variants(self, body: DeleteProductVariantRequest, user_id: str):
        """刪除產品變體"""
        bot = self.bot_service.validate_line_bot_exists(body.bot_uuid)
        self.bot_service.validate_bot_ownership(user_id, bot.bot_detail_id)
        self.command.delete_product_variants(body.variant_ids)

    def upload_product_image(
        self, bot_uuid: UUID, product_id: UUID, user_id: str, images: List[UploadFile]
    ):
        """Uploads new product images."""
        product = self.query.get_product_by_id(product_id)
        if not product:
            raise GlobalErrorException(
                error_code=ErrorCode.PRODUCT_NOT_FOUND,
                error_message="Product not found",
            )

        self.bot_service.validate_bot_ownership(user_id, bot_uuid)

        if not images:
            raise GlobalErrorException(
                error_code=ErrorCode.INVALID_INPUT,
                error_message="Image list cannot be empty",
            )

        uploaded_images = upload_product_images(images)

        for img_data in uploaded_images:
            self.command.insert_product_image(
                product.object_id, img_data["filename"], is_primary=False
            )

    def update_product_image(self, body: UpdateProductImageRequest, user_id: str):
        """更新產品圖片資訊"""
        bot = self.bot_service.validate_line_bot_exists(body.bot_uuid)
        self.bot_service.validate_bot_ownership(user_id, bot.bot_detail_id)

        # 驗證圖片是否存在
        image = self.query.get_product_image_by_id(body.image_id)
        if not image:
            raise GlobalErrorException(
                error_code=ErrorCode.PRODUCT_IMAGE_NOT_FOUND,
                error_message="Product image not found",
            )

        success = self.command.update_product_image(
            image_id=body.image_id, is_primary=body.is_primary
        )

        if not success:
            raise GlobalErrorException(
                error_code=ErrorCode.PRODUCT_IMAGE_NOT_FOUND,
                error_message="Product image not found",
            )

    def delete_product_image(self, body: DeleteProductImageRequest, user_id: str):
        """刪除產品圖片"""
        bot = self.bot_service.validate_line_bot_exists(body.bot_uuid)
        self.bot_service.validate_bot_ownership(user_id, bot.bot_detail_id)

        # 驗證圖片是否存在
        image = self.query.get_product_image_by_id(body.image_id)
        if not image:
            raise GlobalErrorException(
                error_code=ErrorCode.PRODUCT_IMAGE_NOT_FOUND,
                error_message="Product image not found",
            )

        # 從 MinIO 刪除
        delete_product_image(image.filename)

        # 從資料庫刪除
        self.command.delete_product_image(body.image_id)
