from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class BotDetail(SQLModel, table=True):
    __tablename__ = "bot_details"

    bot_detail_id: UUID = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(foreign_key="objects.object_id")

    channel_id: str = Field(max_length=256)
    channel_access_token: str = Field(max_length=256)
    channel_secret: str = Field(max_length=256)
    liff_id: str = Field(max_length=256)
