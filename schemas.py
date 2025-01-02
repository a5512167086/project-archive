from pydantic import BaseModel, EmailStr, Field


class ErrorResponse(BaseModel):
    error_code: str
    error_message: str


class TokenRequest(BaseModel):
    user_id: str
    email: EmailStr
    is_remeber: bool


class TokenResponse(BaseModel):
    token: str
    token_type: str


class VerifyResponse(BaseModel):
    x_user_id: str = Field(alias="X-User-ID")
    x_user_email: str = Field(alias="X-User-Email")

    class Config:
        allow_population_by_field_name = True
