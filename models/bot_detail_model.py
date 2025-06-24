from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class BotDetail(SQLModel, table=True):
    __tablename__ = "bot_details"

    bot_detail_id: UUID = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(foreign_key="objects.object_id")

    channel_id: str = Field(max_length=256)
    channel_access_token: str = Field(max_length=256)
    channel_secret: str = Field(max_length=256)
    login_channel_id: str = Field(max_length=256)
    login_channel_secret: str = Field(max_length=256)
    liff_id: str = Field(max_length=256)


class BotListView(SQLModel, table=True):
    __tablename__ = "vs_bot_list"
    bot_detail_id: UUID = Field(default=None, primary_key=True)
    class_id: int
    object_id: int
    chinese_name: str
    channel_id: str
    owner_id: str


class BotListWithCredentialView(SQLModel, table=True):
    __tablename__ = "vs_bot_list_with_credential"

    bot_detail_id: UUID = Field(primary_key=True)
    class_id: int
    object_id: int
    chinese_name: str
    channel_id: str
    channel_access_token: str
    channel_secret: str
    login_channel_id: str
    login_channel_secret: str
    liff_id: str
    owner_id: UUID
