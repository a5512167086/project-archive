from typing import Annotated

from fastapi import APIRouter, Depends

from dependencies import get_auth_response_headers
from schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    OAuthLoginRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
    User,
)
from services.user import (
    forgot_password,
    get_user_profile,
    login,
    oauth_login,
    register,
    reset_password,
)

router = APIRouter()


@router.post(
    "/user/login",
    tags=["users"],
    response_model=TokenResponse,
)
async def login_user(user: LoginRequest):
    jwt = login(user)
    return jwt


@router.post("/user/oauth_login", tags=["users"], response_model=TokenResponse)
async def user_oauth_login(body: OAuthLoginRequest):
    return oauth_login(body)


@router.post("/user/register", tags=["users"], response_model=RegisterResponse)
async def register_user(user: RegisterRequest):
    new_user_id = register(user)
    return new_user_id


@router.post("/user/forgot_password", tags=["users"])
async def forgot_user_password(body: ForgotPasswordRequest):
    user_email = body.email
    forgot_password(user_email)


@router.get("/user/me", tags=["users"], response_model=User)
async def get_user(auth_headers: Annotated[dict, Depends(get_auth_response_headers)]):
    user_id = auth_headers["X-User-ID"]
    user_profile = get_user_profile(user_id)
    return user_profile


@router.post("/user/reset_password", tags=["users"])
async def reset_user_password(
    auth_headers: Annotated[dict, Depends(get_auth_response_headers)],
    body: ResetPasswordRequest,
):
    update_user_id = auth_headers["X-User-ID"]
    new_password = body.new_password
    reset_password(update_user_id, new_password)
