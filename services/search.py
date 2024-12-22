import psycopg2

from commands.search import delete_search_items, insert_search_items
from exception import GlobalErrorException
from queries.search import (
    get_all_search_image_items_by_class_id,
    get_all_search_text_items_by_class_id,
    get_search_class_id_by_bot_class_id,
)
from utils.crawler import get_products_by_url
from utils.image import extract_text_from_image
from utils.search import tfidf_image_search, tfidf_search


def validate_search_class(bot_class_id: int) -> int:
    search_class_id = get_search_class_id_by_bot_class_id(bot_class_id)
    if not search_class_id:
        raise GlobalErrorException(
            error_code="SEARCH_CLASS_NOT_FOUND",
            error_message="Search class not found for the given bot class",
        )
    return search_class_id


def get_combined_search_items(search_text_items, search_image_items):
    combined_items = {}

    for text_item in search_text_items:
        object_id = text_item["object_id"]
        combined_items[object_id] = {**text_item, "images": []}

    for image_item in search_image_items:
        object_id = image_item["object_id"]
        if object_id not in combined_items:
            combined_items[object_id] = {"object_id": object_id, "images": []}
        combined_items[object_id]["images"].append(
            {
                "image_src": image_item.get("image_src", ""),
                "ocr_text": image_item.get("ocr_text", ""),
            }
        )

    return list(combined_items.values())


def handle_database_error(error: psycopg2.Error, bot_class_id: int):
    error_message = error.diag.message_primary
    if f"Error: 找不到 {bot_class_id} 底下的 Search Class" in error_message:
        raise GlobalErrorException(
            error_code="SEARCH_CLASS_NOT_FOUND",
            error_message="Search class not found for the given bot class",
        )
    raise GlobalErrorException(
        error_code="DATABASE_ERROR",
        error_message="Database error occurred",
    )


def get_search_items_by_bot_class_id(bot_class_id: int):
    search_class_id = validate_search_class(bot_class_id)
    search_text_items = get_all_search_text_items_by_class_id(search_class_id)
    search_image_items = get_all_search_image_items_by_class_id(search_class_id)
    return get_combined_search_items(search_text_items, search_image_items)


def add_search_items_by_url(bot_class_id: int, url: str):
    products = get_products_by_url(url)
    if not products:
        raise GlobalErrorException(
            error_code="NO_PRODUCTS_FOUND",
            error_message="No products found in the given URL",
        )
    try:
        insert_search_items(bot_class_id, products)
    except psycopg2.Error as error:
        handle_database_error(error, bot_class_id)


def get_search_items_by_text(bot_class_id: int, query: str):
    search_class_id = validate_search_class(bot_class_id)
    search_items = get_all_search_text_items_by_class_id(search_class_id)
    if not search_items:
        return []

    return tfidf_search(search_items, query)


def get_search_items_by_ocr_text(bot_class_id: int, image_query_src: str):
    search_class_id = validate_search_class(bot_class_id)
    search_items = get_all_search_image_items_by_class_id(search_class_id)
    if not search_items:
        return []
    ocr_query = extract_text_from_image(image_query_src)
    return tfidf_image_search(search_items, ocr_query)


def delete_search_items_by_bot_class_id(bot_class_id: int, deleted_id_list: list):
    if not deleted_id_list:
        raise GlobalErrorException(
            error_code="EMPTY_DELETE_LIST",
            error_message="No items to delete",
        )
    try:
        return delete_search_items(bot_class_id, deleted_id_list)
    except psycopg2.Error as error:
        handle_database_error(error, bot_class_id)
