import datetime

from sqlmodel import Field, SQLModel


class DailyPrice(SQLModel, table=True):
    __tablename__ = "daily_price"

    stock_id: int = Field(foreign_key="stock.id", primary_key=True, ondelete="CASCADE")
    date: datetime.date = Field(primary_key=True, index=True)
    open_price: float | None = Field(default=None)
    high_price: float | None = Field(default=None)
    low_price: float | None = Field(default=None)
    close_price: float
    volume: int | None = Field(default=None)
