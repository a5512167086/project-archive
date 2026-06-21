from dotenv import load_dotenv
from fastapi import FastAPI

from app.apis.v1 import backtest, stocks

load_dotenv()
app = FastAPI(title="Quant Data API")

# 掛載路由
app.include_router(stocks.router, prefix="/api/v1/stocks", tags=["stocks"])
app.include_router(backtest.router, prefix="/api/v1/backtest", tags=["backtest"])


@app.get("/")
def health_check():
    return {"message": "Quant API Server is running!"}
