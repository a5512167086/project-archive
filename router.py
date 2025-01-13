from typing import Annotated

from fastapi import APIRouter, Depends

from dependencies import get_auth_response_headers
from schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    OAuthLoginRequest,
    OAuthBindRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ChangePasswordRequest,
    TokenResponse,
    User,
)
from services.user import (
    forgot_password,
    get_user_profile,
    login,
    oauth_login,
    oauth_bind,
    register,
    reset_password,
    change_password,
    check_oauth_status,
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


@router.post("/user/oauth-login", tags=["users"], response_model=TokenResponse)
async def user_oauth_login(body: OAuthLoginRequest):
    return oauth_login(body)


@router.post("/user/oauth-bind", tags=["users"])
async def user_oauth_bind(
    auth_headers: Annotated[dict, Depends(get_auth_response_headers)],
    body: OAuthBindRequest,
):
    user_id = auth_headers["X-User-ID"]
    oauth_bind(user_id, body)


@router.get("/user/oauth-status", tags=["users"])
async def user_oauth_status(
    auth_headers: Annotated[dict, Depends(get_auth_response_headers)],
):
    user_id = auth_headers["X-User-ID"]
    return check_oauth_status(user_id)


@router.post("/user/register", tags=["users"], response_model=RegisterResponse)
async def register_user(user: RegisterRequest):
    new_user_id = register(user)
    return new_user_id


@router.post("/user/forgot-password", tags=["users"])
async def forgot_user_password(body: ForgotPasswordRequest):
    user_email = body.email
    forgot_password(user_email)


@router.get("/user/me", tags=["users"], response_model=User)
async def get_user(auth_headers: Annotated[dict, Depends(get_auth_response_headers)]):
    user_id = auth_headers["X-User-ID"]
    user_profile = get_user_profile(user_id)
    return user_profile


@router.post("/user/reset-password", tags=["users"])
async def reset_user_password(
    auth_headers: Annotated[dict, Depends(get_auth_response_headers)],
    body: ResetPasswordRequest,
):
    update_user_id = auth_headers["X-User-ID"]
    new_password = body.new_password
    reset_password(update_user_id, new_password)


@router.post("/user/change-password", tags=["users"])
async def change_user_password(
    auth_headers: Annotated[dict, Depends(get_auth_response_headers)],
    body: ChangePasswordRequest,
):
    update_user_email = auth_headers["X-User-Email"]
    old_password = body.old_password
    new_password = body.new_password
    change_password(update_user_email, old_password, new_password)
