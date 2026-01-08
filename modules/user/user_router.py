from typing import Annotated

from fastapi import APIRouter, Depends

from modules.bot.bot_service import BotService
from modules.user.user_schema import (
    ChangePasswordRequest,
    CustomerLoginRequest,
    ForgotPasswordRequest,
    LoginRequest,
    OAuthBindRequest,
    OAuthLoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from modules.user.user_service import UserService
from shared.clients.database import SessionDep
from shared.dependencies import get_current_user
from shared.services.group_service import GroupService


def get_user_service(session: SessionDep) -> UserService:
    """依賴注入 UserService"""
    return UserService(session)


def get_bot_service(session: SessionDep) -> BotService:
    """依賴注入 BotService"""
    return BotService(session)


def get_group_service(session: SessionDep) -> GroupService:
    """依賴注入 GroupService"""
    return GroupService(session)


user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.post("/login")
async def login_user(
    user: LoginRequest, user_service: Annotated[UserService, Depends(get_user_service)]
):
    return user_service.login(user)


@user_router.post("/token-refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshTokenRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    token = user_service.refresh_token(body.refresh_token)
    user_service.session.commit()
    return token


@user_router.post("/oauth-login", response_model=TokenResponse)
async def user_oauth_login(
    body: OAuthLoginRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    token = user_service.oauth_login(body)
    user_service.session.commit()
    return token


@user_router.post("/oauth-bind")
async def user_oauth_bind(
    current_user: Annotated[dict, Depends(get_current_user)],
    body: OAuthBindRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    user_id = current_user["user_id"]
    user_service.oauth_bind(user_id, body)
    user_service.session.commit()


@user_router.get("/oauth-status")
async def user_oauth_status(
    current_user: Annotated[dict, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    user_id = current_user["user_id"]
    return user_service.check_oauth_status(user_id)


@user_router.post("/register", response_model=RegisterResponse)
async def register_user(
    user: RegisterRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    user_uuid = user_service.create_new_user(user.username, user.email, user.password)
    user_service.session.commit()
    return {"user_id": user_uuid}


@user_router.post("/forgot-password")
async def forgot_user_password(
    body: ForgotPasswordRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    user_service.forgot_password(body)


@user_router.get("/me", response_model=UserResponse)
async def get_user(
    current_user: Annotated[dict, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    return user_service.get_user_profile(current_user["user_id"])


@user_router.post("/reset-password")
async def reset_user_password(
    body: ResetPasswordRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    user_service.reset_password_with_token(body.token, body.new_password)
    user_service.session.commit()


@user_router.post("/change-password")
async def change_user_password(
    current_user: Annotated[dict, Depends(get_current_user)],
    body: ChangePasswordRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    user_service.change_password(
        current_user["email"], body.old_password, body.new_password
    )
    user_service.session.commit()


@user_router.post("/customer-login", response_model=TokenResponse)
async def user_customer_login(
    body: CustomerLoginRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
    group_service: Annotated[GroupService, Depends(get_group_service)],
):
    bot = bot_service.validate_line_bot_exists(body.bot_id)
    bot_group = group_service.validate_group_exist_in_bot(bot.class_id, "Users")
    token_response = user_service.customer_login(bot_group.group_id, body, bot)
    user_service.session.commit()
    return token_response
