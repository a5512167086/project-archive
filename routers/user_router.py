from typing import Annotated

from fastapi import APIRouter, Depends

from database import SessionDep
from dependencies import get_current_user, get_reset_user
from schemas.user_schema import (
    ChangePasswordRequest,
    CustomerLoginRequest,
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
    customer_login,
    forgot_password,
    get_user_profile,
    login,
    oauth_bind,
    oauth_login,
    reset_password,
)

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.post("/login")
async def login_user(session: SessionDep, user: LoginRequest):
    return login(session, user)


@user_router.post("/oauth-login", response_model=TokenResponse)
async def user_oauth_login(session: SessionDep, body: OAuthLoginRequest):
    token = oauth_login(session, body)
    session.commit()
    return token


@user_router.post("/oauth-bind")
async def user_oauth_bind(
    session: SessionDep,
    current_user: Annotated[dict, Depends(get_current_user)],
    body: OAuthBindRequest,
):
    user_id = current_user["user_id"]
    oauth_bind(session, user_id, body)
    session.commit()


@user_router.get("/oauth-status")
async def user_oauth_status(
    session: SessionDep, current_user: Annotated[dict, Depends(get_current_user)]
):
    user_id = current_user["user_id"]
    return check_oauth_status(session, user_id)


@user_router.post("/register", response_model=RegisterResponse)
async def register_user(session: SessionDep, user: RegisterRequest):
    user_uuid = create_new_user(session, user.username, user.email, user.password)
    session.commit()
    return {"user_id": user_uuid}


@user_router.post("/forgot-password")
async def forgot_user_password(session: SessionDep, body: ForgotPasswordRequest):
    forgot_password(session, body.email)


@user_router.get("/me", response_model=UserResponse)
async def get_user(
    session: SessionDep, current_user: Annotated[dict, Depends(get_current_user)]
):
    return get_user_profile(session, current_user["user_id"])


@user_router.post("/reset-password")
async def reset_user_password(
    session: SessionDep,
    current_user: Annotated[dict, Depends(get_reset_user)],
    body: ResetPasswordRequest,
):
    reset_password(session, current_user["user_id"], body.new_password)
    session.commit()


@user_router.post("/change-password")
async def change_user_password(
    session: SessionDep,
    current_user: Annotated[dict, Depends(get_current_user)],
    body: ChangePasswordRequest,
):
    change_password(
        session, current_user["email"], body.old_password, body.new_password
    )
    session.commit()


@user_router.post("/customer-login", response_model=TokenResponse)
async def user_customer_login(session: SessionDep, body: CustomerLoginRequest):
    token_response = customer_login(session, body)
    session.commit()
    return token_response
