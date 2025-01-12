from typing import Literal

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    username: str
    email: EmailStr


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    user_id: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember: bool


class TokenResponse(BaseModel):
    token: str
    token_type: str


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
    user_id: str
    oauth_provider: Literal["google", "line"]
    oauth_user_id: str


class ErrorResponse(BaseModel):
    error_code: str
    error_message: str
