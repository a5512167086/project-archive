from pydantic import BaseModel


class InsertModuleSettingRequest(BaseModel):
    bot_class_id: int
    module_name: str
    is_enabled: bool


class ErrorResponse(BaseModel):
    error_code: str
    error_message: str
