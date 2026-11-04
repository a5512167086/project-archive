from uuid import UUID

from sqlmodel import Field, SQLModel


class BotListView(SQLModel, table=True):
    __tablename__ = "vs_bot_list"
    bot_detail_id: UUID = Field(default=None, primary_key=True)
    class_id: int
    object_id: int
    chinese_name: str
    channel_id: str
    owner_id: str
