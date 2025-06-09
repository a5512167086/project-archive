from datetime import date
from uuid import UUID

from sqlmodel import Field, SQLModel


class Customer(SQLModel, table=True):
    __tablename__ = "customers"

    user_id: UUID = Field(foreign_key="users.user_id", primary_key=True)

    full_name: str = Field(max_length=255)
    gender: bool
    birthday: date
    address: str = Field(max_length=255)
    phone_number: str = Field(max_length=255)
