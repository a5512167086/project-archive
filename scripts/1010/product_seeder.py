import argparse
import io
import json
import logging
import uuid
from uuid import UUID

import httpx
from sqlmodel import Session

from modules.bot.bot_query import BotQuery
from modules.ecomm.ecomm_command import EcommCommand
from modules.ecomm.ecomm_query import EcommQuery
from shared.clients.database import engine
from shared.services.minio_service import MinioService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

PRODUCTS_JSON_PATH = "data/1010_products.json"


def get_db() -> Session:
    return Session(engine)


def generate_filename(original_filename: str) -> str:
    file_extension = (
        original_filename.split(".")[-1] if "." in original_filename else "jpg"
    )
    return f"{uuid.uuid4()}.{file_extension}"


def download_image(url: str) -> bytes | None:
    try:
        with httpx.Client(verify=False) as client:
            response = client.get(url, follow_redirects=True, timeout=20)
            response.raise_for_status()
            return response.content
    except httpx.RequestError as e:
        logger.error(f"Error downloading image {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while downloading {url}: {e}")
        return None


def upload_image_to_minio(
    minio_service: MinioService, image_data: bytes, original_filename: str
) -> str | None:
    try:
        content_type = "image/jpeg"
        if original_filename.lower().endswith(".png"):
            content_type = "image/png"
        elif original_filename.lower().endswith(".gif"):
            content_type = "image/gif"
        elif original_filename.lower().endswith(".webp"):
            content_type = "image/webp"

        new_filename = generate_filename(original_filename)
        minio_service.client.put_object(
            "product-images",
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
        f"Using bot with UUID: {bot.bot_detail_id} and class_id: {bot.class_id}"
    )

    try:
        with open(PRODUCTS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"{PRODUCTS_JSON_PATH} not found.")
        return
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {PRODUCTS_JSON_PATH}.")
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

    logger.info("--- Inserting Brands ---")
    for brand_name in data.get("brands", []):
        if not ecomm_query.check_brand_name_exists(brand_class_id, brand_name):
            try:
                ecomm_command.insert_brand(brand_class_id, brand_name, brand_name)
                logger.info(f"Inserted brand: {brand_name}")
            except Exception as e:
                logger.error(f"Failed to insert brand {brand_name}: {e}")
                db.rollback()
        else:
            logger.info(f"Brand already exists: {brand_name}")
    db.commit()

    all_brands = ecomm_query.get_all_brands_by_class_id(brand_class_id)
    brands_map = {b.brand_name: b.object_id for b in all_brands}
    logger.info(f"Found {len(brands_map)} brands in total.")

    logger.info("--- Inserting Categories and Products ---")
    for main_cat_data in data.get("categories", []):
        main_category_name = main_cat_data["main_category"]

        main_cats = ecomm_query.get_categories_by_class_id([category_root_class_id])
        main_cat_obj = next(
            (c for c in main_cats if c.category_name == main_category_name), None
        )

        if not main_cat_obj:
            try:
                result = ecomm_command.insert_category(
                    category_class_id=category_root_class_id,
                    category_name=main_category_name,
                    category_description=main_category_name,
                    parent_category_id=category_root_class_id,
                )
                db.commit()
                new_main_cat_id = result[0]
                logger.info(
                    f"Inserted main category: '{main_category_name}' with id {new_main_cat_id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to insert main category '{main_category_name}': {e}"
                )
                db.rollback()
                continue
        else:
            new_main_cat_id = main_cat_obj.class_id
            logger.info(
                f"Main category '{main_category_name}' already exists with id {new_main_cat_id}"
            )

        for sub_cat_data in main_cat_data.get("sub_categories", []):
            sub_category_name = sub_cat_data["name"]

            sub_cats = ecomm_query.get_categories_by_class_id([new_main_cat_id])
            sub_cat_obj = next(
                (c for c in sub_cats if c.category_name == sub_category_name), None
            )

            if not sub_cat_obj:
                try:
                    result = ecomm_command.insert_category(
                        category_class_id=category_root_class_id,
                        category_name=sub_category_name,
                        category_description=sub_category_name,
                        parent_category_id=new_main_cat_id,
                    )
                    db.commit()
                    new_sub_cat_id = result[0]
                    logger.info(
                        f"Inserted sub category: '{sub_category_name}' under '{main_category_name}' with id {new_sub_cat_id}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to insert sub category '{sub_category_name}': {e}"
                    )
                    db.rollback()
                    continue
            else:
                new_sub_cat_id = sub_cat_obj.class_id
                logger.info(
                    f"Sub category '{sub_category_name}' already exists with id {new_sub_cat_id}"
                )

            for product_data in sub_cat_data.get("products", []):
                product_name = product_data["name"]

                brand_id = brands_map.get(product_data["brand"])
                if not brand_id:
                    logger.warning(
                        f"Brand '{product_data['brand']}' not found for product '{product_name}'. Skipping brand."
                    )

                uploaded_images = []
                for i, img_url in enumerate(product_data.get("images", [])):
                    image_data = download_image(img_url)
                    if image_data:
                        filename = upload_image_to_minio(
                            minio_service, image_data, img_url.split("/")[-1]
                        )
                        if filename:
                            uploaded_images.append({
                                "filename": filename,
                                "is_primary": i == 0,
                            })

                try:
                    price = product_data.get("price")
                    if price is None:
                        logger.warning(
                            f"Product '{product_name}' has no price, skipping."
                        )
                        continue

                    ecomm_command.insert_product(
                        product_class_id=new_sub_cat_id,
                        product_name=product_name,
                        product_description=product_data.get("description", ""),
                        brand_id=brand_id,
                        sku_code=None,
                        price=price,
                        stock=None,
                        is_active=True,
                        images=uploaded_images,
                        owner_id=None,
                    )
                    logger.info(f"Inserted product: {product_name}")
                except Exception as e:
                    logger.error(f"Failed to insert product '{product_name}': {e}")
                    db.rollback()

            db.commit()

    logger.info("--- Seeding finished ---")
    db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed product data from products.json."
    )
    parser.add_argument(
        "--bot-uuid",
        required=True,
        help="The UUID of the bot to associate the data with.",
    )
    args = parser.parse_args()

    seed_data(args.bot_uuid)
