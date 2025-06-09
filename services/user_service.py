import logging
from datetime import timedelta

from sqlmodel import Session

from commands.user_command import create_oauth, create_user, update_user_password
from constants.config import ACCESS_TOKEN_EXPIRE_SECONDS, JWT_RESET_SECRET
from constants.error_code import ErrorCode
from exception import GlobalErrorException
from queries.user_query import (
    get_oauth_by_oauth_user_id,
    get_oauth_by_user_id,
    get_user_by_email,
    get_user_by_id,
)
from schemas.user_schema import (
    ForgotPasswordRequest,
    LoginRequest,
    OAuthBindRequest,
    OAuthLoginRequest,
    RegisterRequest,
)
from services.auth_service import create_jwt_token, generate_token_pair
from services.mail_service import send_reset_email
from utils.common import (
    authenticate_with_google,
    authenticate_with_line,
    generate_random_password,
    hash_password,
    verify_password,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_new_user(session: Session, username: str, email: str, password: str) -> str:
    existed_user = get_user_by_email(session, email)
    if existed_user:
        raise GlobalErrorException(
            error_code=ErrorCode.USER_ALREADY_EXISTS,
            error_message="The provided email is already registered.",
        )

    register_data = RegisterRequest(
        username=username, email=email, password=hash_password(password)
    )

    new_user = create_user(session, register_data)
    if not new_user:
        raise GlobalErrorException(
            error_code=ErrorCode.USER_CREATION_FAILED,
            error_message="An error occurred while creating the user.",
        )

    return new_user.user_id


def get_user_profile(session: Session, user_id: str):
    user = get_user_by_id(session, user_id)
    if not user:
        raise GlobalErrorException(
            error_code=ErrorCode.USER_NOT_EXISTS,
            error_message="User not found.",
        )
    print(f"User profile retrieved: {user}")

    return user


def get_user_info_by_oauth_code(provider: str, code: str) -> dict:
    if provider == "google":
        return authenticate_with_google(code)
    elif provider == "line":
        return authenticate_with_line(code)
    else:
        raise GlobalErrorException(
            ErrorCode.OAUTH_PROVIDER_NOT_SUPPORTED,
            f"Provider {provider} is not supported.",
        )


def login(session: Session, user: LoginRequest):
    login_user = get_user_by_email(session, user.email)
    if not login_user:
        raise GlobalErrorException(
            error_code=ErrorCode.USER_NOT_EXISTS,
            error_message="Can't find user by email.",
        )
    if not verify_password(user.password, login_user.password):
        raise GlobalErrorException(
            error_code=ErrorCode.PASSWORD_NOT_MATCH,
            error_message="Password is incorrect.",
        )

    return generate_token_pair(login_user.user_id, login_user.email, user.remember)


def handle_new_oauth_user(session, oauth_user_info, provider):
    random_password = generate_random_password()
    new_user_id = create_new_user(
        session, oauth_user_info["name"], oauth_user_info["email"], random_password
    )
    create_oauth(session, new_user_id, provider, oauth_user_info["id"])

    return generate_token_pair(new_user_id, oauth_user_info["email"], is_remember=True)


def handle_existed_oauth_user(session, provider: str, oauth_user_id: str):
    oauth_data = get_oauth_by_oauth_user_id(session, provider, oauth_user_id)
    if not oauth_data:
        raise GlobalErrorException(
            ErrorCode.USER_ALREADY_EXISTS, "OAuth data not found for the user."
        )
    user_data = get_user_by_id(session, oauth_data.user_id)
    if not user_data:
        raise GlobalErrorException(
            ErrorCode.USER_NOT_EXISTS, "User not found for the given OAuth data."
        )

    return generate_token_pair(oauth_data.user_id, user_data.email, is_remember=True)


def oauth_login(session: Session, oauth: OAuthLoginRequest):
    if oauth.provider == "google":
        user_info = authenticate_with_google(oauth.code)
    elif oauth.provider == "line":
        user_info = authenticate_with_line(oauth.code)
    else:
        raise GlobalErrorException(
            ErrorCode.OAUTH_PROVIDER_NOT_SUPPORTED,
            f"Provider {oauth.provider} is not supported.",
        )

    user = get_user_by_email(session, user_info["email"])
    if not user:
        return handle_new_oauth_user(session, user_info, oauth.provider)

    oauth_user_info = handle_existed_oauth_user(
        session, oauth.provider, user_info["id"]
    )
    if oauth_user_info == "USER_ALREADY_EXISTS":
        raise GlobalErrorException(
            ErrorCode.USER_ALREADY_EXISTS, "User already exists, please login."
        )
    return oauth_user_info


def oauth_bind(session: Session, user_id: str, oauth: OAuthBindRequest):
    user = get_user_by_id(session, user_id)
    if not user:
        raise GlobalErrorException(
            ErrorCode.USER_NOT_EXISTS, "User not found in database."
        )

    oauth_status = check_oauth_status(session, user_id)

    if oauth_status["google"] is True and oauth.provider == "google":
        raise GlobalErrorException(
            ErrorCode.USER_ALREADY_BINDED, "User already binded with Google OAuth."
        )
    if oauth_status["line"] is True and oauth.provider == "line":
        raise GlobalErrorException(
            ErrorCode.USER_ALREADY_BINDED, "User already binded with Line OAuth."
        )

    if oauth.provider == "google":
        user_info = authenticate_with_google(oauth.code)
    elif oauth.provider == "line":
        user_info = authenticate_with_line(oauth.code)
    else:
        raise GlobalErrorException(
            ErrorCode.OAUTH_PROVIDER_NOT_SUPPORTED,
            f"Provider {oauth.provider} is not supported.",
        )

    if not user_info:
        raise GlobalErrorException(
            ErrorCode.USER_LOOKUP_FAILED, "Failed to retrieve user information."
        )

    user_oauths = get_oauth_by_oauth_user_id(session, oauth.provider, user_info["id"])
    if user_oauths:
        raise GlobalErrorException(
            ErrorCode.OAUTH_ALREADY_EXISTS, "OAuth already bound to the user."
        )

    create_oauth(session, user_id, oauth.provider, user_info["id"])


def check_oauth_status(session: Session, user_id: str):
    oauth_data = get_oauth_by_user_id(session, user_id)
    oauth_status = {"google": False, "line": False}
    for oauth in oauth_data:
        provider = oauth.oauth_provider
        if provider in oauth_status:
            oauth_status[provider] = True
    return oauth_status


def forgot_password(session: Session, user_email: ForgotPasswordRequest):
    forgot_user_data = get_user_by_email(session, user_email)
    if not forgot_user_data:
        raise GlobalErrorException(
            error_code=ErrorCode.USER_NOT_EXISTS,
            error_message="Can't find user by email.",
        )

    token = create_jwt_token(
        {
            "sub": str(forgot_user_data.user_id),
            "email": forgot_user_data.email,
            "is_remember": False,
        },
        JWT_RESET_SECRET,
        timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS),
    )
    send_reset_email(user_email, token)


def reset_password(session: Session, user_id: str, new_password: str):
    update_user_data = get_user_by_id(session, user_id)
    if not update_user_data:
        raise GlobalErrorException(
            error_code=ErrorCode.USER_NOT_EXISTS,
            error_message="Can't find user by ID.",
        )

    update_user_password(session, user_id, hash_password(new_password))


def change_password(session, user_email: str, old_password: str, new_password: str):
    user_data = get_user_by_email(session, user_email)

    if user_data == "USER_NOT_EXISTS":
        raise GlobalErrorException(
            error_code=ErrorCode.USER_NOT_EXISTS,
            error_message="Can't find user by email.",
        )
    if not verify_password(old_password, user_data.password):
        raise GlobalErrorException(
            error_code=ErrorCode.PASSWORD_NOT_MATCH,
            error_message="Password is incorrect.",
        )

    update_user_password(session, user_data.user_id, hash_password(new_password))
