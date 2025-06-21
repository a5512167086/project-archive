from typing import Optional
from uuid import UUID

from sqlmodel import Field, SQLModel


class GroupMember(SQLModel, table=True):
    __tablename__ = "group_members"

    group_id: int = Field(foreign_key="group.group_id", primary_key=True)
    member_id: UUID = Field(primary_key=True)
    role: int = Field(default=2, ge=0, le=2)
    type: Optional[bool] = Field(default=None)
    status: Optional[bool] = Field(default=None)
