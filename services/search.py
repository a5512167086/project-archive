import psycopg2

from commands.search import insert_search_items
from exception import GlobalErrorException
from queries.search import (
    get_all_search_image_items_by_class_id,
    get_all_search_text_items_by_class_id,
    get_search_class_id_by_bot_class_id,
)
from utils.crawler import get_products_by_url
from utils.image import extract_text_from_image
from utils.search import tfidf_image_search, tfidf_search


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
        error_message = error.diag.message_primary
        if "Error: 找不到 {bot_class_id} 底下的 Search Class" in error_message:
            raise GlobalErrorException(
                error_code="SEARCH_CLASS_NOT_FOUND",
                error_message="Search class not found for the given bot class",
            )
        else:
            raise GlobalErrorException(
                error_code="DATABASE_ERROR",
                error_message="Database error occurred",
            )


def get_search_items_by_text(bot_class_id: int, query: str):
    search_class_id = get_search_class_id_by_bot_class_id(bot_class_id)
    if not search_class_id:
        raise GlobalErrorException(
            error_code="SEARCH_CLASS_NOT_FOUND",
            error_message="Search class not found for the given bot class",
        )
    search_items = get_all_search_text_items_by_class_id(search_class_id)
    match_items = tfidf_search(search_items, query)
    return match_items


def get_search_items_by_ocr_text(bot_class_id: int, image_query_src: str):
    search_class_id = get_search_class_id_by_bot_class_id(bot_class_id)
    if not search_class_id:
        raise GlobalErrorException(
            error_code="SEARCH_CLASS_NOT_FOUND",
            error_message="Search class not found for the given bot class",
        )
    ocr_query = extract_text_from_image(image_query_src)
    search_items = get_all_search_image_items_by_class_id(search_class_id)
    match_items = tfidf_image_search(search_items, ocr_query)
    return match_items
