from typing import Annotated

from fastapi import APIRouter, Depends

from dependencies import get_current_user, get_reset_user
from schemas.user_schema import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    OAuthBindRequest,
    OAuthLoginRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
    User,
)
from services.user_service import (
    change_password,
    check_oauth_status,
    forgot_password,
    get_user_profile,
    login,
    oauth_bind,
    oauth_login,
    register,
    reset_password,
)

router = APIRouter()


@router.post("/user/login", tags=["users"])
async def login_user(user: LoginRequest):
    return login(user)


@router.post("/user/oauth-login", tags=["users"], response_model=TokenResponse)
async def user_oauth_login(body: OAuthLoginRequest):
    return oauth_login(body)


@router.post("/user/oauth-bind", tags=["users"])
async def user_oauth_bind(
    current_user: Annotated[dict, Depends(get_current_user)],
    body: OAuthBindRequest,
):
    user_id = current_user["user_id"]
    oauth_bind(user_id, body)


@router.get("/user/oauth-status", tags=["users"])
async def user_oauth_status(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    return check_oauth_status(user_id)


@router.post("/user/register", tags=["users"], response_model=RegisterResponse)
async def register_user(user: RegisterRequest):
    return register(user)


@router.post("/user/forgot-password", tags=["users"])
async def forgot_user_password(body: ForgotPasswordRequest):
    forgot_password(body.email)


@router.get("/user/me", tags=["users"], response_model=User)
async def get_user(current_user: Annotated[dict, Depends(get_current_user)]):
    return get_user_profile(current_user["user_id"])


@router.post("/user/reset-password", tags=["users"])
async def reset_user_password(
    current_user: Annotated[dict, Depends(get_reset_user)],
    body: ResetPasswordRequest,
):
    reset_password(current_user["user_id"], body.new_password)


@router.post("/user/change-password", tags=["users"])
async def change_user_password(
    current_user: Annotated[dict, Depends(get_current_user)],
    body: ChangePasswordRequest,
):
    change_password(current_user["email"], body.old_password, body.new_password)
