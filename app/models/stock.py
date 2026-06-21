from sqlmodel import Field, SQLModel


class Stock(SQLModel, table=True):
    __tablename__ = "stock"

    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True, unique=True, max_length=20)
    name: str | None = Field(default=None, max_length=100)
    market: str = Field(max_length=10)
    currency: str = Field(max_length=5)
