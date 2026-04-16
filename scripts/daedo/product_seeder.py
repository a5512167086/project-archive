import argparse
import io
import json
import logging
import re
import uuid
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any
from uuid import UUID

import httpx
from sqlmodel import Session

from modules.bot.bot_query import BotQuery
from modules.ecomm.ecomm_command import EcommCommand
from modules.ecomm.ecomm_query import EcommQuery
from shared.clients.database import engine
from shared.services.minio_service import MinioService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PRODUCTS_JSON_PATH = "data/daedo_products.json"
FIXED_BRAND_NAME = "Daedo"
MINIO_BUCKET_NAME = "product-images"
EUR_TO_TWD_RATE = Decimal(35)


def get_db() -> Session:
    return Session(engine)


def generate_filename(original_filename: str) -> str:
    file_extension = (
        original_filename.split(".")[-1].split("?")[0]
        if "." in original_filename
        else "jpg"
    )
    return f"{uuid.uuid4()}.{file_extension}"


def parse_price(price_value: Any) -> Decimal | None:
    if price_value is None:
        return None

    if isinstance(price_value, (int, float, Decimal)):
        eur_price = Decimal(str(price_value))
    else:
        price_str = str(price_value).strip()
        if not price_str:
            return None

        cleaned = re.sub(r"[^\d,.\-]", "", price_str)

        # 歐洲格式: 1.234,56 -> 1234.56
        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", ".")

        try:
            eur_price = Decimal(cleaned)
        except (InvalidOperation, ValueError):
            logger.warning(f"Unable to parse price: {price_value}")
            return None

    twd_price = (eur_price * EUR_TO_TWD_RATE).quantize(
        Decimal(1),
        rounding=ROUND_HALF_UP,
    )
    return twd_price


def download_image(url: str) -> bytes | None:
    try:
        with httpx.Client(verify=False, timeout=20, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.content
    except httpx.RequestError as e:
        logger.error(f"Error downloading image {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while downloading {url}: {e}")
        return None


def upload_image_to_minio(
    minio_service: MinioService,
    image_data: bytes,
    original_filename: str,
) -> str | None:
    try:
        original_filename_lower = original_filename.lower()
        content_type = "image/jpeg"

        if (
            original_filename_lower.endswith(".png")
            or ".png?" in original_filename_lower
        ):
            content_type = "image/png"
        elif (
            original_filename_lower.endswith(".gif")
            or ".gif?" in original_filename_lower
        ):
            content_type = "image/gif"
        elif (
            original_filename_lower.endswith(".webp")
            or ".webp?" in original_filename_lower
        ):
            content_type = "image/webp"
        elif original_filename_lower.endswith(
            ".jpg"
        ) or original_filename_lower.endswith(".jpeg"):
            content_type = "image/jpeg"

        new_filename = generate_filename(original_filename)
        minio_service._ensure_bucket(MINIO_BUCKET_NAME)
        minio_service.client.put_object(
            MINIO_BUCKET_NAME,
            new_filename,
            data=io.BytesIO(image_data),
            length=len(image_data),
            content_type=content_type,
        )

        logger.info(f"Uploaded image {original_filename} as {new_filename}")
        return new_filename
    except Exception as e:
        logger.error(f"Failed to upload image to MinIO: {e}")
        return None


def ensure_brand(
    db: Session,
    ecomm_command: EcommCommand,
    ecomm_query: EcommQuery,
    brand_class_id: int,
    brand_name: str,
) -> int | None:
    if not ecomm_query.check_brand_name_exists(brand_class_id, brand_name):
        try:
            ecomm_command.insert_brand(
                brand_class_id=brand_class_id,
                brand_name=brand_name,
                brand_description=brand_name,
            )
            db.commit()
            logger.info(f"Inserted brand: {brand_name}")
        except Exception as e:
            logger.error(f"Failed to insert brand '{brand_name}': {e}")
            db.rollback()
            return None
    else:
        logger.info(f"Brand already exists: {brand_name}")

    all_brands = ecomm_query.get_all_brands_by_class_id(brand_class_id)
    brand_obj = next((b for b in all_brands if b.brand_name == brand_name), None)

    if not brand_obj:
        logger.error(f"Brand '{brand_name}' not found after insert/check.")
        return None

    return brand_obj.object_id


def ensure_category(
    db: Session,
    ecomm_command: EcommCommand,
    ecomm_query: EcommQuery,
    category_root_class_id: int,
    parent_category_id: int,
    category_name: str,
) -> int | None:
    existing_categories = ecomm_query.get_categories_by_class_id([parent_category_id])
    existing_obj = next(
        (c for c in existing_categories if c.category_name == category_name),
        None,
    )

    if existing_obj:
        logger.info(
            f"Category '{category_name}' already exists under parent {parent_category_id}, class_id={existing_obj.class_id}"
        )
        return existing_obj.class_id

    try:
        result = ecomm_command.insert_category(
            category_class_id=category_root_class_id,
            category_name=category_name,
            category_description=category_name,
            parent_category_id=parent_category_id,
        )
        db.commit()

        new_category_id = result[0]
        logger.info(
            f"Inserted category '{category_name}' under parent {parent_category_id}, class_id={new_category_id}"
        )
        return new_category_id
    except Exception as e:
        logger.error(f"Failed to insert category '{category_name}': {e}")
        db.rollback()
        return None


def seed_data(bot_uuid_str: str):
    db = get_db()
    ecomm_command = EcommCommand(db)
    ecomm_query = EcommQuery(db)
    bot_query = BotQuery(db)
    minio_service = MinioService()

    try:
        bot_uuid = UUID(bot_uuid_str)
    except ValueError:
        logger.error("Invalid BOT_UUID format.")
        return

    logger.info(f"--- Fetching Bot with UUID: {bot_uuid} ---")
    bot = bot_query.get_bot_by_uuid(bot_uuid)
    if not bot:
        logger.error(f"Bot with UUID {bot_uuid} not found.")
        return

    logger.info(
        f"Using bot with bot_detail_id={bot.bot_detail_id}, class_id={bot.class_id}"
    )

    try:
        with open(PRODUCTS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"{PRODUCTS_JSON_PATH} not found.")
        return
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {PRODUCTS_JSON_PATH}: {e}")
        return

    brand_class_id = ecomm_query.get_brand_class_id_by_bot_class_id(bot.class_id)
    if not brand_class_id:
        logger.error("Brand class not found for the bot.")
        return

    category_root_class_id = ecomm_query.get_category_class_id_by_bot_class_id(
        bot.class_id
    )
    if not category_root_class_id:
        logger.error("Category class not found for the bot.")
        return

    brand_id = ensure_brand(
        db=db,
        ecomm_command=ecomm_command,
        ecomm_query=ecomm_query,
        brand_class_id=brand_class_id,
        brand_name=FIXED_BRAND_NAME,
    )
    if not brand_id:
        logger.error("Unable to resolve fixed brand id.")
        return

    logger.info("--- Seeding Categories and Products ---")

    seen_product_urls: set[str] = set()

    total_inserted = 0
    total_skipped_duplicate = 0
    total_skipped_no_price = 0
    total_failed = 0

    for main_category_data in data:
        main_category_name = main_category_data.get("category_name")
        if not main_category_name:
            logger.warning("Found category without category_name, skipped.")
            continue

        main_category_id = ensure_category(
            db=db,
            ecomm_command=ecomm_command,
            ecomm_query=ecomm_query,
            category_root_class_id=category_root_class_id,
            parent_category_id=category_root_class_id,
            category_name=main_category_name,
        )
        if not main_category_id:
            continue

        for sub_category_data in main_category_data.get("sub_categories", []):
            sub_category_name = sub_category_data.get("sub_category_name")
            if not sub_category_name:
                logger.warning(
                    f"Found sub-category without name under '{main_category_name}', skipped."
                )
                continue

            sub_category_id = ensure_category(
                db=db,
                ecomm_command=ecomm_command,
                ecomm_query=ecomm_query,
                category_root_class_id=category_root_class_id,
                parent_category_id=main_category_id,
                category_name=sub_category_name,
            )
            if not sub_category_id:
                continue

            for product_data in sub_category_data.get("products", []):
                product_name = product_data.get("name")
                product_url = product_data.get("url")
                product_desc = product_data.get("description") or ""

                if not product_name:
                    logger.warning(
                        f"Found product without name under '{main_category_name} > {sub_category_name}', skipped."
                    )
                    total_failed += 1
                    continue

                if product_url and product_url in seen_product_urls:
                    logger.info(
                        f"Duplicate product url skipped: {product_name} ({product_url})"
                    )
                    total_skipped_duplicate += 1
                    continue

                price = parse_price(product_data.get("price"))
                if price is None:
                    logger.warning(
                        f"Product '{product_name}' has no valid price, skipped. raw_price={product_data.get('price')}"
                    )
                    total_skipped_no_price += 1
                    continue

                uploaded_images = []
                for i, img_url in enumerate(product_data.get("images", [])):
                    image_data = download_image(img_url)
                    if not image_data:
                        continue

                    uploaded_filename = upload_image_to_minio(
                        minio_service=minio_service,
                        image_data=image_data,
                        original_filename=img_url.split("/")[-1],
                    )
                    if uploaded_filename:
                        uploaded_images.append({
                            "filename": uploaded_filename,
                            "is_primary": i == 0,
                        })

                try:
                    object_id = ecomm_command.insert_product(
                        product_class_id=sub_category_id,
                        product_name=product_name,
                        product_description=product_desc,
                        brand_id=brand_id,
                        sku_code=None,
                        price=price,
                        stock=None,
                        is_active=True,
                        images=uploaded_images,
                        owner_id=None,
                    )

                    for variant_name in product_data.get("variants", []):
                        if not variant_name:
                            continue

                        ecomm_command.insert_product_variant(
                            object_id=object_id,
                            variant_name=str(variant_name),
                            sku_code=None,
                            price=None,
                            stock=None,
                        )

                    db.commit()

                    if product_url:
                        seen_product_urls.add(product_url)

                    total_inserted += 1
                    logger.info(
                        f"Inserted product: {product_name} | variants={len(product_data.get('variants', []))} | category={main_category_name} > {sub_category_name}"
                    )
                except Exception as e:
                    logger.error(f"Failed to insert product '{product_name}': {e}")
                    db.rollback()
                    total_failed += 1

    logger.info("--- Seeding finished ---")
    logger.info(
        f"Inserted={total_inserted}, "
        f"SkippedDuplicate={total_skipped_duplicate}, "
        f"SkippedNoPrice={total_skipped_no_price}, "
        f"Failed={total_failed}"
    )

    db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Daedo product data from JSON.")
    parser.add_argument(
        "--bot-uuid",
        required=True,
        help="The UUID of the bot to associate the data with.",
    )
    args = parser.parse_args()

    seed_data(args.bot_uuid)
