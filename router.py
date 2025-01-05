from fastapi import APIRouter, File, UploadFile

from schemas import InsertFAQRequest
from services.faq import insert_single_faq

router = APIRouter()


@router.get("/faq", tags=["FAQ"])
def get_all_faq():
    return ""


@router.post("/faq", tags=["FAQ"])
def insert_faq(body: InsertFAQRequest):
    insert_single_faq(body)


@router.post("/faq/csv", tags=["FAQ"])
def insert_faq_by_csv(file: UploadFile = File(media_type="text/csv")):
    return ""


@router.delete("/faq", tags=["FAQ"])
def delete_faq():
    return ""


@router.post("/query", tags=["bot"])
def query():
    return ""
