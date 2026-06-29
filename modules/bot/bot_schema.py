from uuid import UUID

from pydantic import BaseModel, model_validator


class BotHeaders(BaseModel):
    x_line_signature: str


class Bot(BaseModel):
    class_id: int
    object_id: int
    bot_name: str
    channel_id: str
    owner_id: UUID

    @model_validator(mode="before")
    def map_fields(cls, values):
        if "bot_name" not in values and "chinese_name" in values:
            values["bot_name"] = values["chinese_name"]

        return values


class InsertBotRequest(BaseModel):
    bot_name: str
    bot_channel_id: str
    bot_channel_access_token: str
    bot_channel_secret: str
    bot_login_channel_id: str
    bot_login_channel_secret: str

    @model_validator(mode="before")
    def prevent_empty_strings(cls, values):
        empty_fields = []
        for key, value in values.items():
            if value is not None and isinstance(value, str) and value.strip() == "":
                empty_fields.append(key)

        if empty_fields:
            raise ValueError(
                f"The following fields cannot be empty strings: {', '.join(empty_fields)}"
            )

        return values


class InsertBotResponse(BaseModel):
    webhook_url: str


class UpdateBotRequest(BaseModel):
    bot_name: str | None = None
    channel_id: str | None = None
    channel_access_token: str | None = None
    channel_secret: str | None = None
    login_channel_id: str | None = None
    login_channel_secret: str | None = None

    @model_validator(mode="before")
    def prevent_empty_strings(cls, values):
        empty_fields = []
        for key, value in values.items():
            if value is not None and isinstance(value, str) and value.strip() == "":
                empty_fields.append(key)

        if empty_fields:
            raise ValueError(
                f"The following fields cannot be empty strings: {', '.join(empty_fields)}"
            )

        return values


class ErrorResponse(BaseModel):
    error_code: str
    error_message: str


class BotWithPublicCredential(BaseModel):
    bot_detail_id: UUID
    class_id: int
    object_id: int
    chinese_name: str
    channel_id: str
    login_channel_id: str
    liff_id: str
    owner_id: UUID
