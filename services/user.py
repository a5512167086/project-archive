from commands.oauth import create_oauth
from commands.user import create_user, update_user_password
from exception import GlobalErrorException
from queries.oauth import get_oauth_by_oauth_user_id
from queries.user import (
    get_user_by_email,
    get_user_by_email_and_password,
    get_user_by_id,
)
from schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    OAuth,
    OAuthLoginRequest,
    RegisterRequest,
)
from services.mail import send_reset_email
from utils import (
    authenticate_with_google,
    create_jwt_token,
    generate_random_password,
    hash_password,
)

# Error constants
ERROR_USER_NOT_EXISTS = "USER_NOT_EXISTS"
ERROR_USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
ERROR_PASSWORD_NOT_MATCH = "PASSWORD_NOT_MATCH"
ERROR_USER_LOOKUP_FAILED = "USER_LOOKUP_FAILED"
ERROR_USER_CREATION_FAILED = "USER_CREATION_FAILED"


def validate_existence(data, error_code, error_message):
    if data in ["USER_NOT_EXISTS", "OAUTH_NOT_EXISTS"] or data is None:
        raise GlobalErrorException(error_code=error_code, error_message=error_message)


def generate_access_token(
    user_id: str, email: str, is_remember: bool = False, extra_data=None
):
    data = {"user_id": user_id, "email": email, "is_remember": is_remember}
    if extra_data:
        data.update(extra_data)
    access_token = create_jwt_token(data)
    return access_token


def create_new_user(username: str, email: str, password: str) -> str:
    hashed_password = hash_password(password)
    new_user = RegisterRequest(username=username, email=email, password=hashed_password)
    new_user_id = create_user(new_user)

    if new_user_id == "DUPLICATE_EMAIL":
        raise GlobalErrorException(
            error_code=ERROR_USER_ALREADY_EXISTS,
            error_message="The provided email is already registered.",
        )
    if new_user_id is None:
        raise GlobalErrorException(
            error_code=ERROR_USER_CREATION_FAILED,
            error_message="An error occurred while creating the user.",
        )
    return new_user_id


def get_user_profile(user_id: str):
    user_profile = get_user_by_id(user_id)
    validate_existence(user_profile, ERROR_USER_NOT_EXISTS, "Can't find user by ID.")
    return user_profile


def login(user: LoginRequest):
    login_user_data = get_user_by_email_and_password(user)

    if login_user_data == "USER_NOT_EXISTS":
        raise GlobalErrorException(
            error_code=ERROR_USER_NOT_EXISTS, error_message="Can't find user by email."
        )
    if login_user_data == "PASSWORD_NOT_MATCH":
        raise GlobalErrorException(
            error_code=ERROR_PASSWORD_NOT_MATCH, error_message="Password is incorrect."
        )

    return generate_access_token(login_user_data["user_id"], login_user_data["email"])


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
    return generate_access_token(new_user_id, google_user_info["email"])


def handle_existed_oauth_user(provider: str, oauth_user_id: str):
    oauth_data = get_oauth_by_oauth_user_id(provider, oauth_user_id)
    validate_existence(
        oauth_data, ERROR_USER_ALREADY_EXISTS, "OAuth data not found for the user."
    )

    user_data = get_user_by_id(oauth_data["user_id"])
    validate_existence(
        user_data, ERROR_USER_NOT_EXISTS, "User not found for the given OAuth data."
    )

    return generate_access_token(oauth_data["user_id"], user_data["email"])


def oauth_login(oauth: OAuthLoginRequest):
    google_user_info = authenticate_with_google(oauth.code)
    user_info = get_user_by_email(google_user_info["email"])

    if user_info == "USER_NOT_EXISTS":
        return handle_new_oauth_user(google_user_info, oauth.provider)

    if user_info:
        oauth_user_info = handle_existed_oauth_user(
            oauth.provider, google_user_info["id"]
        )
        if oauth_user_info == "USER_ALREADY_EXISTS":
            raise GlobalErrorException(
                ERROR_USER_ALREADY_EXISTS, "User already exists, please login."
            )
        return oauth_user_info

    raise GlobalErrorException(
        ERROR_USER_LOOKUP_FAILED, "Failed to retrieve user information."
    )


def forgot_password(user_email: ForgotPasswordRequest):
    forgot_user_data = get_user_by_email(user_email)
    validate_existence(
        forgot_user_data, ERROR_USER_NOT_EXISTS, "Can't find user by email."
    )
    token = create_jwt_token(
        data={
            "user_id": forgot_user_data["user_id"],
            "email": forgot_user_data["email"],
            "is_remember": False,
        },
    )
    send_reset_email(user_email, token['token'])


def reset_password(user_id: str, new_password: str):
    update_user_data = get_user_by_id(user_id)
    validate_existence(
        update_user_data, ERROR_USER_NOT_EXISTS, "Can't find user by ID."
    )

    update_user_password(user_id, hash_password(new_password))
