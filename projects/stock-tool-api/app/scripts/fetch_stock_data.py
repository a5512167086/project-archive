import concurrent.futures
import logging
import os
import random
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import yfinance as yf
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from sqlmodel import Session, create_engine
from urllib3.util.retry import Retry

from app.models.stock import Stock
from app.repositories.daily_price_repository import DailyPriceRepository
from app.repositories.stock_repository import StockRepository

# --- 0. 日誌設定 ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# --- 1. 初始化設定 ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("找不到 DATABASE_URL，請確認 .env 檔案設定！")

engine = create_engine(DATABASE_URL)


# --- 2. 爬蟲防禦設定 ---
def get_robust_session() -> requests.Session:
    """建立帶有自動重試與偽裝機制的 HTTP Session"""
    session = requests.Session()

    # 設定重試機制：遇到 429 流量限制或 5xx 伺服器錯誤時，進行指數退避重試
    retry = Retry(
        total=5,  # 最多重試 5 次
        backoff_factor=1,  # 退避時間：1s, 2s, 4s, 8s, 16s
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # 偽裝成正常的 Chrome 瀏覽器
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    return session


# --- 3. 獲取「上市」股票名單 (TWSE) ---
def get_all_tw_stocks() -> dict:
    stocks = {}
    logger.info("正在從證交所獲取「上市」股票名單...")

    try:
        # 政府 API 通常不需要特別的 session，直接 request 即可
        res_twse = requests.get(
            "https://openapi.twse.com.tw/v1/opendata/t187ap03_L", timeout=10
        )
        res_twse.raise_for_status()

        for item in res_twse.json():
            ticker = item["公司代號"]
            if len(ticker) == 4 and ticker.isdigit():
                stocks[f"{ticker}.TW"] = {
                    "name": item["公司簡稱"],
                    "market": "TW",
                    "currency": "TWD",
                }

    except requests.exceptions.RequestException as e:
        logger.error(f"獲取上市名單網路連線失敗: {e}")
    except ValueError:
        logger.error("解析上市名單 JSON 失敗")

    logger.info(f"成功獲取全市場(上市)名單，共計 {len(stocks)} 檔股票。")
    return stocks


# --- 4. 業務邏輯 ---
def sync_stock_metadata(target_stocks: dict) -> dict:
    logger.info("階段一：同步上市股票基本資料至資料庫 (批量優化版)...")

    with Session(engine) as session:
        stock_repo = StockRepository(session)
        existing_stocks = {stock.ticker: stock.id for stock in stock_repo.get_all()}

        new_stocks_to_insert = []
        for ticker, info in target_stocks.items():
            if ticker not in existing_stocks:
                new_stocks_to_insert.append(
                    Stock(
                        ticker=ticker,
                        name=info["name"],
                        market=info["market"],
                        currency=info["currency"],
                    )
                )

        if new_stocks_to_insert:
            logger.info(f"偵測到 {len(new_stocks_to_insert)} 檔新股票，準備批量寫入...")
            stock_repo.bulk_add(new_stocks_to_insert)
            existing_stocks = {stock.ticker: stock.id for stock in stock_repo.get_all()}
            logger.info("批量寫入完成！")
        else:
            logger.info("沒有偵測到新股票，無需更新基本資料。")

    return existing_stocks


def process_batch(
    batch_tickers: list,
    ticker_to_id: dict,
    yf_kwargs: dict,
    batch_name: str,
    session: requests.Session,
) -> pd.DataFrame | None:
    """獨立的 Worker 函式，專責下載與清洗單一批次資料"""

    # 核心防禦：加入隨機延遲 (Jitter)，打亂多執行緒的請求頻率，避免瞬間併發量過高
    time.sleep(random.uniform(5, 10))  # 隨機延遲 5~10 秒
    logger.info(f"執行緒啟動：開始下載批次 {batch_name} ...")

    try:
        # 將自訂的強健 session 傳給 yfinance
        df = yf.download(batch_tickers, progress=False, session=session, **yf_kwargs)

        if df.empty:
            return None

        if len(batch_tickers) > 1 and isinstance(df.columns, pd.MultiIndex):
            if "Adj Close" in df.columns.levels[0]:
                df = df.drop(columns=["Adj Close"], level=0)
            df_stacked = df.stack(level=1, future_stack=True).reset_index()
        else:
            return None

        df_stacked.rename(
            columns={
                "Date": "date",
                "Ticker": "ticker",
                "Open": "open_price",
                "High": "high_price",
                "Low": "low_price",
                "Close": "close_price",
                "Volume": "volume",
            },
            inplace=True,
        )

        df_clean = df_stacked.dropna(subset=["close_price"]).copy()
        df_clean["stock_id"] = df_clean["ticker"].map(ticker_to_id)
        df_clean = df_clean.dropna(subset=["stock_id"])

        return df_clean[
            [
                "stock_id",
                "date",
                "open_price",
                "high_price",
                "low_price",
                "close_price",
                "volume",
            ]
        ]

    except Exception:
        logger.exception(f"批次 {batch_name} 處理失敗！錯誤: ")
        return None


def fetch_and_store_all_data(
    ticker_to_id: dict, batch_size: int = 15, max_workers: int = 3
):
    tickers = list(ticker_to_id.keys())
    price_repo = DailyPriceRepository(engine)
    yf_session = get_robust_session()

    latest_date = price_repo.get_latest_date()
    tw_tz = ZoneInfo("Asia/Taipei")
    today = datetime.now(tw_tz).date()

    # 除權息校正與增量更新邏輯
    if latest_date and latest_date >= today:
        logger.info(
            "資料庫日期已是最新，將抓取近半年資料進行「除權息/分割」歷史校正..."
        )
        yf_kwargs = {"period": "6mo"}
    elif latest_date:
        logger.info("偵測到既有資料，將抓取近 1 年資料進行更新與歷史校正...")
        yf_kwargs = {"period": "1y"}
    else:
        logger.info("資料庫無歷史資料，將完整抓取近 10 年資料...")
        yf_kwargs = {"period": "10y"}

    batches = [tickers[i : i + batch_size] for i in range(0, len(tickers), batch_size)]

    # 建議使用 max_workers=3，在速度與安全性之間取得最佳平衡
    logger.info(
        f"共計 {len(batches)} 個批次，啟動 {max_workers} 個 Worker 進行併發下載..."
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_batch = {
            executor.submit(
                process_batch,
                batch,
                ticker_to_id,
                yf_kwargs,
                f"{idx + 1}/{len(batches)}",
                yf_session,
            ): idx
            for idx, batch in enumerate(batches)
        }

        for future in concurrent.futures.as_completed(future_to_batch):
            batch_idx = future_to_batch[future]
            batch_name = f"{batch_idx + 1}/{len(batches)}"

            try:
                df_final = future.result()
                if df_final is not None and not df_final.empty:
                    price_repo.bulk_upsert_from_dataframe(df_final)
                    logger.info(
                        f"✅ 批次 {batch_name} 處理成功：寫入/更新 {len(df_final)} 筆資料。"
                    )
                else:
                    logger.warning(f"⚠️ 批次 {batch_name} 下載為空，已跳過。")
            except Exception:
                logger.exception(f"❌ 批次 {batch_name} 寫入資料庫失敗: ")

    logger.info("🎉 恭喜！歷史數據更新與除權息校正完畢！")


if __name__ == "__main__":
    all_stocks = get_all_tw_stocks()

    if all_stocks:
        mapping = sync_stock_metadata(all_stocks)
        # 安全參數：15檔一包，3個執行緒併發
        fetch_and_store_all_data(mapping, batch_size=15, max_workers=3)
    else:
        logger.error("無法獲取股票名單，程式中止。")
