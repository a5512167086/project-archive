from uuid import UUID

from sqlmodel import Field, SQLModel


class OAuth(SQLModel, table=True):
    __tablename__ = "oauths"

    user_id: UUID = Field(foreign_key="users.user_id", primary_key=True)

    oauth_provider: str = Field(max_length=300, primary_key=True)
    oauth_user_id: str = Field(max_length=100)
