from pydantic import BaseModel, EmailStr


class ErrorResponse(BaseModel):
    error_code: str
    error_message: str


class TokenRequest(BaseModel):
    user_id: str
    email: EmailStr


class TokenResponse(BaseModel):
    token: str
    token_type: str
