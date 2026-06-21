from sqlmodel import Session, select

from app.models.stock import Stock


class StockRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_ticker(self, ticker: str) -> Stock | None:
        """根據股票代號查詢股票"""
        statement = select(Stock).where(Stock.ticker == ticker)

        return self.session.exec(statement).first()

    def create(self, ticker: str, name: str, market: str, currency: str) -> Stock:
        """新增一檔股票並回傳完整的 Model (包含自動產生的 ID)"""
        stock = Stock(ticker=ticker, name=name, market=market, currency=currency)
        self.session.add(stock)
        self.session.commit()
        self.session.refresh(stock)

        return stock

    def get_all(self) -> list[Stock]:
        """一次性撈取資料庫中所有的股票"""
        statement = select(Stock)
        return self.session.exec(statement).all()

    def bulk_add(self, stocks: list[Stock]) -> None:
        """批量寫入多筆股票資料，並只 Commit 一次"""
        self.session.add_all(stocks)
        self.session.commit()
