from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ModuleSetting(SQLModel, table=True):
    __tablename__ = "module_settings"

    module_id: UUID = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(foreign_key="objects.object_id")

    is_enabled: bool = Field(default=False)
    version: str = Field(default="1.0.0", max_length=20)
    description: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ModuleSettingView(SQLModel, table=True):
    __tablename__ = "vs_module_settings"

    module_id: int
    class_id: int
    object_id: int = Field(primary_key=True)
    chinese_name: str
    is_enabled: bool
    version: Optional[str] = None
    description: Optional[str] = None
