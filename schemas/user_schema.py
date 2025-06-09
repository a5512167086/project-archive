from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    username: str
    email: EmailStr


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    user_id: UUID


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember: bool


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    new_password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class OAuthLoginRequest(BaseModel):
    code: str
    provider: Literal["google", "line"]


class OAuthBindRequest(BaseModel):
    code: str
    provider: Literal["google", "line"]
    action: Literal["bind", "unbind"]


class OAuth(BaseModel):
    user_id: UUID
    oauth_provider: Literal["google", "line"]
    oauth_user_id: str
