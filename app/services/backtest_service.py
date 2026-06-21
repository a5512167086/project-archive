import pandas as pd
import pandas_ta as ta
import vectorbt as vbt
from sqlalchemy import Engine
from sqlmodel import Session, select

from app.models.daily_price import DailyPrice  # 假設你的 model 叫這個
from app.repositories.stock_repository import StockRepository


class BacktestService:
    def __init__(self, engine: Engine):
        self.engine = engine

    def get_stock_data_as_dataframe(self, ticker: str) -> pd.DataFrame | None:
        """從資料庫撈取股價並轉換為時間序列 DataFrame"""
        with Session(self.engine) as session:
            stock_repo = StockRepository(session)
            stock = stock_repo.get_by_ticker(ticker)
            if not stock:
                return None

            # 使用 pandas 直接讀取 SQL 查詢，效能極高
            query = (
                select(DailyPrice)
                .where(DailyPrice.stock_id == stock.id)
                .order_by(DailyPrice.date)
            )
            df = pd.read_sql(query, con=session.connection())

            if df.empty:
                return None

            # 將 date 設為 index，這是 vectorbt 與 pandas-ta 的必要格式
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
            return df

    def run_sma_crossover_strategy(
        self, ticker: str, fast_period: int = 20, slow_period: int = 60
    ) -> dict:
        """執行雙均線交叉策略回測 (預設 20日 與 60日)"""
        df = self.get_stock_data_as_dataframe(ticker)
        if df is None:
            return {"error": f"找不到股票 {ticker} 的歷史資料"}

        close_price = df["close_price"]

        # 1. 使用 pandas-ta 計算技術指標
        df["SMA_Fast"] = ta.sma(close_price, length=fast_period)
        df["SMA_Slow"] = ta.sma(close_price, length=slow_period)

        # 2. 產生買賣訊號 (布林值陣列)
        # 買入：快線往上穿過慢線 (黃金交叉)
        # 賣出：快線往下穿過慢線 (死亡交叉)
        entries = (df["SMA_Fast"] > df["SMA_Slow"]) & (
            df["SMA_Fast"].shift(1) <= df["SMA_Slow"].shift(1)
        )
        exits = (df["SMA_Fast"] < df["SMA_Slow"]) & (
            df["SMA_Fast"].shift(1) >= df["SMA_Slow"].shift(1)
        )

        # 3. 丟入 vectorbt 進行高效回測 (假設初始資金 100,000，每次全倉買入)
        portfolio = vbt.Portfolio.from_signals(
            close=close_price,
            entries=entries,
            exits=exits,
            init_cash=100000,
            fees=0.001425,  # 模擬台股手續費
            direction="longonly",
            freq="D",
        )

        # 4. 提取關鍵回測績效指標
        stats = portfolio.stats()

        return {
            "ticker": ticker,
            "strategy": f"SMA({fast_period}, {slow_period}) Crossover",
            "total_return_pct": round(stats["Total Return [%]"], 2),
            "win_rate_pct": round(stats["Win Rate [%]"], 2),
            "max_drawdown_pct": round(stats["Max Drawdown [%]"], 2),
            "total_trades": int(stats["Total Trades"]),
            "start_date": df.index.min().strftime("%Y-%m-%d"),
            "end_date": df.index.max().strftime("%Y-%m-%d"),
        }
