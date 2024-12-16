from fastapi import APIRouter

from schemas import (
    ImageSearchItemsRequest,
    InsertSearchItemsFromUrlRequest,
    TextSearchItemsRequest,
)
from services.search import add_search_items_by_url, get_search_items_by_text

router = APIRouter()


@router.post("/search-items", tags=["search"])
def add_search_items(body: InsertSearchItemsFromUrlRequest):
    add_search_items_by_url(body.bot_class_id, body.url)


@router.post("/text-search", tags=["bot"])
def search_items_by_text(body: TextSearchItemsRequest):
    return get_search_items_by_text(body.bot_class_id, body.query)


@router.post("/image-search", tags=["bot"])
def search_items_by_image(body: ImageSearchItemsRequest):
    return "ok"
