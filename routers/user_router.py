from typing import Annotated

from fastapi import APIRouter, Depends

from database import SessionDep
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
    UserResponse,
)
from services.user_service import (
    change_password,
    check_oauth_status,
    create_new_user,
    forgot_password,
    get_user_profile,
    login,
    oauth_bind,
    oauth_login,
    reset_password,
)

user_router = APIRouter()


@user_router.post("/user/login", tags=["users"])
async def login_user(session: SessionDep, user: LoginRequest):
    return login(session, user)


@user_router.post("/user/oauth-login", tags=["users"], response_model=TokenResponse)
async def user_oauth_login(session: SessionDep, body: OAuthLoginRequest):
    token = oauth_login(session, body)
    session.commit()
    return token


@user_router.post("/user/oauth-bind", tags=["users"])
async def user_oauth_bind(
    session: SessionDep,
    current_user: Annotated[dict, Depends(get_current_user)],
    body: OAuthBindRequest,
):
    user_id = current_user["user_id"]
    oauth_bind(session, user_id, body)
    session.commit()


@user_router.get("/user/oauth-status", tags=["users"])
async def user_oauth_status(
    session: SessionDep, current_user: Annotated[dict, Depends(get_current_user)]
):
    user_id = current_user["user_id"]
    return check_oauth_status(session, user_id)


@user_router.post("/user/register", tags=["users"], response_model=RegisterResponse)
async def register_user(session: SessionDep, user: RegisterRequest):
    user_uuid = create_new_user(session, user.username, user.email, user.password)
    session.commit()
    return {"user_id": user_uuid}


@user_router.post("/user/forgot-password", tags=["users"])
async def forgot_user_password(session: SessionDep, body: ForgotPasswordRequest):
    forgot_password(session, body.email)


@user_router.get("/user/me", tags=["users"], response_model=UserResponse)
async def get_user(
    session: SessionDep, current_user: Annotated[dict, Depends(get_current_user)]
):
    return get_user_profile(session, current_user["user_id"])


@user_router.post("/user/reset-password", tags=["users"])
async def reset_user_password(
    session: SessionDep,
    current_user: Annotated[dict, Depends(get_reset_user)],
    body: ResetPasswordRequest,
):
    reset_password(session, current_user["user_id"], body.new_password)
    session.commit()


@user_router.post("/user/change-password", tags=["users"])
async def change_user_password(
    session: SessionDep,
    current_user: Annotated[dict, Depends(get_current_user)],
    body: ChangePasswordRequest,
):
    change_password(
        session, current_user["email"], body.old_password, body.new_password
    )
    session.commit()
