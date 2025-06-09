from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class CommandDetail(SQLModel, table=True):
    __tablename__ = "command_details"

    command_detail_id: UUID = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(foreign_key="objects.object_id")

    command_keyword: str = Field(max_length=50)
    type: str = Field(max_length=50)
