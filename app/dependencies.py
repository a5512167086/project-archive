# app/dependencies.py
import os

from dotenv import load_dotenv
from sqlmodel import create_engine

from app.services.backtest_service import BacktestService

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL 未設定")

engine = create_engine(DATABASE_URL)


def get_engine():
    return engine


def get_backtest_service():
    return BacktestService(engine)
