from fastapi import APIRouter

from commands.search import insert_search_items
from queries.search import get_all_search_items
from schemas import InsertSearchItemFromUrlRequest, TextSearchItemRequest
from utils.crawler import get_products_by_url
from utils.search import tfidf_search

router = APIRouter()


@router.post("/search-items", tags=["search"])
def add_search_items(body: InsertSearchItemFromUrlRequest):
    products = get_products_by_url(body.url)
    insert_search_items(body.bot_class_id, products)
    return products


@router.post("/text-search", tags=["bot"])
def search_items_by_text(body: TextSearchItemRequest):
    search_items = get_all_search_items()
    match_items = tfidf_search(search_items, body.query)
    return match_items


@router.post("/image-search", tags=["bot"])
def search_items_by_image():
    return "ok"
