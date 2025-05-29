import logging
from datetime import timedelta

from commands.user_command import create_oauth, create_user, update_user_password
from constants.config import ACCESS_TOKEN_EXPIRE_SECONDS, JWT_RESET_SECRET
from constants.error_code import ErrorCode
from exception import GlobalErrorException
from queries.user_query import (
    get_oauth,
    get_oauth_by_oauth_user_id,
    get_oauth_by_user_id,
    get_user_by_email,
    get_user_by_email_and_password,
    get_user_by_id,
)
from schemas.user_schema import (
    ForgotPasswordRequest,
    LoginRequest,
    OAuth,
    OAuthBindRequest,
    OAuthLoginRequest,
    RegisterRequest,
)
from services.auth_service import create_jwt_token, generate_token_pair
from services.mail_service import send_reset_email
from utils import (
    authenticate_with_google,
    authenticate_with_line,
    generate_random_password,
    hash_password,
)

# === Logging ===
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def validate_existence(data, error_code, error_message):
    if data in ["USER_NOT_EXISTS", "OAUTH_NOT_EXISTS"] or data is None:
        raise GlobalErrorException(error_code=error_code, error_message=error_message)


def create_new_user(username: str, email: str, password: str) -> str:
    hashed_password = hash_password(password)
    new_user = RegisterRequest(username=username, email=email, password=hashed_password)
    new_user_id = create_user(new_user)

    if new_user_id == "DUPLICATE_EMAIL":
        raise GlobalErrorException(
            error_code=ErrorCode.USER_ALREADY_EXISTS,
            error_message="The provided email is already registered.",
        )
    if new_user_id is None:
        raise GlobalErrorException(
            error_code=ErrorCode.USER_CREATION_FAILED,
            error_message="An error occurred while creating the user.",
        )
    return new_user_id


def get_user_profile(user_id: str):
    user_profile = get_user_by_id(user_id)
    validate_existence(
        user_profile, ErrorCode.USER_NOT_EXISTS, "Can't find user by ID."
    )
    return user_profile


def login(user: LoginRequest):
    login_user_data = get_user_by_email_and_password(user.email, user.password)

    if login_user_data == "USER_NOT_EXISTS":
        raise GlobalErrorException(
            error_code=ErrorCode.USER_NOT_EXISTS,
            error_message="Can't find user by email.",
        )
    if login_user_data == "PASSWORD_NOT_MATCH":
        raise GlobalErrorException(
            error_code=ErrorCode.PASSWORD_NOT_MATCH,
            error_message="Password is incorrect.",
        )

    return generate_token_pair(
        login_user_data["user_id"], login_user_data["email"], user.remember
    )


def register(user: RegisterRequest):
    new_user_id = create_new_user(user.username, user.email, user.password)
    return {"user_id": new_user_id}


def handle_new_oauth_user(google_user_info, provider):
    random_password = generate_random_password()
    new_user_id = create_new_user(
        google_user_info["name"], google_user_info["email"], random_password
    )
    create_oauth(
        OAuth(
            user_id=new_user_id,
            oauth_provider=provider,
            oauth_user_id=google_user_info["id"],
        )
    )
    return generate_token_pair(new_user_id, google_user_info["email"], is_remember=True)


def handle_existed_oauth_user(provider: str, oauth_user_id: str):
    oauth_data = get_oauth_by_oauth_user_id(provider, oauth_user_id)
    validate_existence(
        oauth_data, ErrorCode.USER_ALREADY_EXISTS, "OAuth data not found for the user."
    )

    user_data = get_user_by_id(oauth_data["user_id"])
    validate_existence(
        user_data, ErrorCode.USER_NOT_EXISTS, "User not found for the given OAuth data."
    )

    return generate_token_pair(
        oauth_data["user_id"], user_data["email"], is_remember=True
    )


def oauth_login(oauth: OAuthLoginRequest):
    if oauth.provider == "google":
        user_info = authenticate_with_google(oauth.code)
    elif oauth.provider == "line":
        user_info = authenticate_with_line(oauth.code)
    else:
        raise GlobalErrorException(
            ErrorCode.OAUTH_PROVIDER_NOT_SUPPORTED,
            f"Provider {oauth.provider} is not supported.",
        )

    user_in_db = get_user_by_email(user_info["email"])
    if user_in_db == "USER_NOT_EXISTS":
        return handle_new_oauth_user(user_info, oauth.provider)

    oauth_user_info = handle_existed_oauth_user(oauth.provider, user_info["id"])
    if oauth_user_info == "USER_ALREADY_EXISTS":
        raise GlobalErrorException(
            ErrorCode.USER_ALREADY_EXISTS, "User already exists, please login."
        )
    return oauth_user_info


def oauth_bind(user_id: str, oauth: OAuthBindRequest):
    user_in_db = get_user_by_id(user_id)
    if user_in_db == "USER_NOT_EXISTS":
        raise GlobalErrorException(
            ErrorCode.USER_NOT_EXISTS, "User not found in database."
        )

    oauth_status = check_oauth_status(user_id)

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

    user_oauths = get_oauth(oauth.provider, user_info["id"])
    if user_oauths:
        raise GlobalErrorException(
            ErrorCode.OAUTH_ALREADY_EXISTS, "OAuth already bound to the user."
        )

    create_oauth(
        OAuth(
            user_id=user_id,
            oauth_provider=oauth.provider,
            oauth_user_id=user_info["id"],
        )
    )


def check_oauth_status(user_id: str):
    oauth_data = get_oauth_by_user_id(user_id)
    oauth_status = {"google": False, "line": False}
    for row in oauth_data:
        provider = row.get("oauth_provider")
        if provider in oauth_status:
            oauth_status[provider] = True
    return oauth_status


def forgot_password(user_email: ForgotPasswordRequest):
    forgot_user_data = get_user_by_email(user_email)
    validate_existence(
        forgot_user_data, ErrorCode.USER_NOT_EXISTS, "Can't find user by email."
    )
    token = create_jwt_token(
        {
            "sub": forgot_user_data["user_id"],
            "email": forgot_user_data["email"],
            "is_remember": False,
        },
        JWT_RESET_SECRET,
        timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS),
    )
    send_reset_email(user_email, token)


def reset_password(user_id: str, new_password: str):
    update_user_data = get_user_by_id(user_id)
    validate_existence(
        update_user_data, ErrorCode.USER_NOT_EXISTS, "Can't find user by ID."
    )
    update_user_password(user_id, hash_password(new_password))


def change_password(user_email: str, old_password: str, new_password: str):
    user_data = get_user_by_email_and_password(user_email, old_password)

    if user_data == "USER_NOT_EXISTS":
        raise GlobalErrorException(
            error_code=ErrorCode.USER_NOT_EXISTS, error_message="Can't find user by id."
        )
    if user_data == "PASSWORD_NOT_MATCH":
        raise GlobalErrorException(
            error_code=ErrorCode.PASSWORD_NOT_MATCH,
            error_message="Password is incorrect.",
        )

    validate_existence(user_data, ErrorCode.USER_NOT_EXISTS, "Can't find user by ID.")
    update_user_password(user_data["user_id"], hash_password(new_password))
