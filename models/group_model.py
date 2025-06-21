from typing import Optional

from sqlmodel import Field, SQLModel


class Group(SQLModel, table=True):
    group_id: Optional[int] = Field(default=None, primary_key=True)
    group_name: str = Field(max_length=50, nullable=False)
    group_description: Optional[str] = Field(default=None, max_length=1024)
    status: Optional[int] = None
    group_type: Optional[int] = None
    is_hidden: bool = Field(default=False)
    is_deleted: bool = Field(default=False)


class GroupPermissionView(SQLModel, table=True):
    __tablename__ = "vs_group_permissions"

    class_id: int = Field(primary_key=True)
    group_id: int = Field(primary_key=True)
    group_name: str
    group_description: Optional[str]
    group_status: Optional[bool]
    permission_bits: int
