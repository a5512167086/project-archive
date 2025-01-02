import logging

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

ERROR_USER_NOT_EXISTS = "USER_NOT_EXISTS"
ERROR_USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
ERROR_PASSWORD_NOT_MATCH = "PASSWORD_NOT_MATCH"
ERROR_USER_LOOKUP_FAILED = "USER_LOOKUP_FAILED"
ERROR_USER_CREATION_FAILED = "USER_CREATION_FAILED"


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def validate_existence(data, error_code, error_message):
    logging.debug("Validating existence: data=%s, error_code=%s", data, error_code)
    if data in ["USER_NOT_EXISTS", "OAUTH_NOT_EXISTS"] or data is None:
        logging.error("Validation failed: %s, %s", error_code, error_message)
        raise GlobalErrorException(error_code=error_code, error_message=error_message)


def generate_access_token(
    user_id: str, email: str, is_remember: bool = False, extra_data=None
):
    logging.info("Generating access token for user_id=%s, email=%s", user_id, email)
    data = {"user_id": user_id, "email": email, "is_remember": is_remember}
    if extra_data:
        logging.debug("Adding extra_data to token: %s", extra_data)
        data.update(extra_data)
    access_token = create_jwt_token(data)
    logging.info("Access token generated for user_id=%s", user_id)
    return access_token


def create_new_user(username: str, email: str, password: str) -> str:
    logging.info("Creating new user: username=%s, email=%s", username, email)
    hashed_password = hash_password(password)
    new_user = RegisterRequest(username=username, email=email, password=hashed_password)
    new_user_id = create_user(new_user)

    if new_user_id == "DUPLICATE_EMAIL":
        logging.error("Email already registered: %s", email)
        raise GlobalErrorException(
            error_code=ERROR_USER_ALREADY_EXISTS,
            error_message="The provided email is already registered.",
        )
    if new_user_id is None:
        logging.error("Failed to create user: email=%s", email)
        raise GlobalErrorException(
            error_code=ERROR_USER_CREATION_FAILED,
            error_message="An error occurred while creating the user.",
        )
    logging.info("User created successfully: user_id=%s", new_user_id)
    return new_user_id


def get_user_profile(user_id: str):
    logging.info("Fetching user profile for user_id=%s", user_id)
    user_profile = get_user_by_id(user_id)
    validate_existence(user_profile, ERROR_USER_NOT_EXISTS, "Can't find user by ID.")
    logging.debug("User profile fetched: %s", user_profile)
    return user_profile


def login(user: LoginRequest):
    logging.info("User login attempt: email=%s", user.email)
    login_user_data = get_user_by_email_and_password(user)

    if login_user_data == "USER_NOT_EXISTS":
        logging.error("Login failed: User not found with email=%s", user.email)
        raise GlobalErrorException(
            error_code=ERROR_USER_NOT_EXISTS, error_message="Can't find user by email."
        )
    if login_user_data == "PASSWORD_NOT_MATCH":
        logging.error("Login failed: Password mismatch for email=%s", user.email)
        raise GlobalErrorException(
            error_code=ERROR_PASSWORD_NOT_MATCH, error_message="Password is incorrect."
        )

    token = generate_access_token(
        login_user_data["user_id"], login_user_data["email"], user.remember
    )
    logging.info("Login successful: user_id=%s", login_user_data["user_id"])
    return token


def register(user: RegisterRequest):
    logging.info(
        "Registering new user: username=%s, email=%s", user.username, user.email
    )
    new_user_id = create_new_user(user.username, user.email, user.password)
    logging.info("Registration successful: user_id=%s", new_user_id)
    return {"user_id": new_user_id}


def handle_new_oauth_user(google_user_info, provider):
    logging.info(
        "Handling new OAuth user: email=%s, provider=%s",
        google_user_info["email"],
        provider,
    )
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
    token = generate_access_token(new_user_id, google_user_info["email"], True)
    logging.info("New OAuth user created successfully: user_id=%s", new_user_id)
    return token


def handle_existed_oauth_user(provider: str, oauth_user_id: str):
    logging.info(
        "Handling existing OAuth user: provider=%s, oauth_user_id=%s",
        provider,
        oauth_user_id,
    )
    oauth_data = get_oauth_by_oauth_user_id(provider, oauth_user_id)
    validate_existence(
        oauth_data, ERROR_USER_ALREADY_EXISTS, "OAuth data not found for the user."
    )

    user_data = get_user_by_id(oauth_data["user_id"])
    validate_existence(
        user_data, ERROR_USER_NOT_EXISTS, "User not found for the given OAuth data."
    )

    token = generate_access_token(oauth_data["user_id"], user_data["email"])
    logging.info("OAuth login successful: user_id=%s", oauth_data["user_id"])
    return token


def oauth_login(oauth: OAuthLoginRequest):
    logging.info("OAuth login attempt: provider=%s", oauth.provider)
    google_user_info = authenticate_with_google(oauth.code)
    user_info = get_user_by_email(google_user_info["email"])

    if user_info == "USER_NOT_EXISTS":
        logging.info("New user detected via OAuth: email=%s", google_user_info["email"])
        return handle_new_oauth_user(google_user_info, oauth.provider)

    if user_info:
        oauth_user_info = handle_existed_oauth_user(
            oauth.provider, google_user_info["id"]
        )
        if oauth_user_info == "USER_ALREADY_EXISTS":
            logging.warning(
                "User already exists for OAuth: email=%s", google_user_info["email"]
            )
            raise GlobalErrorException(
                ERROR_USER_ALREADY_EXISTS, "User already exists, please login."
            )
        return oauth_user_info

    logging.error("Failed to retrieve user information via OAuth.")
    raise GlobalErrorException(
        ERROR_USER_LOOKUP_FAILED, "Failed to retrieve user information."
    )


def forgot_password(user_email: ForgotPasswordRequest):
    logging.info("Processing forgot password request for email=%s", user_email)
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
    send_reset_email(user_email, token["token"])
    logging.info("Reset email sent successfully to email=%s", user_email)


def reset_password(user_id: str, new_password: str):
    logging.info("Resetting password for user_id=%s", user_id)
    update_user_data = get_user_by_id(user_id)
    validate_existence(
        update_user_data, ERROR_USER_NOT_EXISTS, "Can't find user by ID."
    )

    update_user_password(user_id, hash_password(new_password))
    logging.info("Password reset successful for user_id=%s", user_id)
