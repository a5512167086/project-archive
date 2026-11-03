from fastapi import APIRouter
from sqlmodel import Session, select

from app.dependencies import get_engine
from app.models.stock import Stock

router = APIRouter()


@router.get("/")
def get_stocks():
    """取得資料庫中所有股票清單"""
    with Session(get_engine()) as session:
        stocks = session.exec(select(Stock)).all()
        return stocks
