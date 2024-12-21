from typing import Optional

from pydantic import UUID4, BaseModel


class Module(BaseModel):
    module_id: UUID4
    class_id: int
    object_id: int
    chinese_name: str
    is_enabled: bool
    version: str
    description: Optional[str] = None


class InsertModuleSettingRequest(BaseModel):
    bot_class_id: int
    module_name: str
    is_enabled: bool


class ErrorResponse(BaseModel):
    error_code: str
    error_message: str
