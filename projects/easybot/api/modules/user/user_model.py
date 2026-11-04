from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    user_id: UUID = Field(default_factory=uuid4, primary_key=True)
    username: Optional[str] = Field(default=None, max_length=100)
    password: Optional[str] = Field(default=None, max_length=300)
    is_valid: bool = Field(default=False)
    email: Optional[str] = Field(default=None, max_length=100, unique=True, index=True)
    status: Optional[int] = Field(default=None)
    login_count: int = Field(default=0)
    last_login_datetime: Optional[datetime] = Field(default=None)
    login_error_count: int = Field(default=0)
    email_verify_code: Optional[str] = Field(default=None, max_length=300)
    class_id: Optional[int] = Field(default=None, foreign_key="classes.class_id")
    is_send_email: bool = Field(default=False)
