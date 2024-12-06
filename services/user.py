from schemas import (
    RegisterRequest,
    LoginRequest,
    ForgotPasswordRequest,
    OAuthLoginRequest,
    OAuth,
)
from utils import (
    hash_password,
    create_jwt_token,
    authenticate_with_google,
    generate_random_password,
)
from commands.user import create_user, update_user_password
from commands.oauth import create_oauth
from queries.user import (
    get_user_by_email_and_password,
    get_user_by_id,
    get_user_by_email,
)
from queries.oauth import get_oauth_by_oauth_user_id
from services.mail import send_reset_email
from exception import GlobalErrorException
from datetime import timedelta


def get_user_profile(user_id: str):
    user_profile = get_user_by_id(user_id)
    if user_profile == "USER_NOT_EXISTS":
        raise GlobalErrorException(
            error_code="USER_NOT_EXISTS",
            error_message="Can't found user by email.",
        )

    return user_profile


def login(user: LoginRequest):
    login_user_data = get_user_by_email_and_password(user)

    if login_user_data == "USER_NOT_EXISTS":
        raise GlobalErrorException(
            error_code="USER_NOT_EXISTS",
            error_message="Can't found user by email.",
        )
    if login_user_data == "PASSWORD_NOT_MATCH":
        raise GlobalErrorException(
            error_code="PASSWORD_NOT_MATCH",
            error_message="Password is incorrect.",
        )

    login_user_id, login_user_email = (
        login_user_data["user_id"],
        login_user_data["email"],
    )

    access_token = create_jwt_token(
        data={"sub": login_user_id, "email": login_user_email}
    )

    return {"token": access_token, "token_type": "bearer"}


def handle_new_oauth_user(google_user_info, provider):
    random_password = generate_random_password()
    hashed_password = hash_password(random_password)
    new_user = RegisterRequest(
        username=google_user_info["name"],
        email=google_user_info["email"],
        password=hashed_password,
    )
    new_user_id = create_user(new_user)
    oauth_data = OAuth(
        user_id=new_user_id,
        oauth_provider=provider,
        oauth_user_id=google_user_info["id"],
    )
    create_oauth(oauth_data)
    access_token = create_jwt_token(
        data={"sub": new_user_id, "email": google_user_info["email"]}
    )
    return {"token": access_token, "token_type": "bearer"}


def handle_existed_oauth_user(provider: str, oauth_user_id: str):
    oauth_data = get_oauth_by_oauth_user_id(provider, oauth_user_id)

    if oauth_data != "OAUTH_NOT_EXISTS" and oauth_data is not None:
        user_data = get_user_by_id(oauth_data["user_id"])
        if user_data != "USER_NOT_EXISTS":
            access_token = create_jwt_token(
                data={"sub": oauth_data["user_id"], "email": user_data["email"]}
            )
            return {"token": access_token, "token_type": "bearer"}
    return "USER_ALREADY_EXISTS"


def oauth_login(oauth: OAuthLoginRequest):
    google_user_info = authenticate_with_google(oauth.code)
    google_email = google_user_info["email"]
    user_info = get_user_by_email(google_email)

    if user_info == "USER_NOT_EXISTS":
        return handle_new_oauth_user(google_user_info, oauth.provider)
    elif user_info:
        oauth_user_info = handle_existed_oauth_user(
            oauth.provider, google_user_info["id"]
        )
        if oauth_user_info == "USER_ALREADY_EXISTS":
            raise GlobalErrorException(
                "USER_ALREADY_EXISTS", "User already exists, please login."
            )
        return oauth_user_info
    else:
        raise GlobalErrorException(
            "USER_LOOKUP_FAILED", "Failed to retrieve user information."
        )


def register(user: RegisterRequest):
    new_user = RegisterRequest(
        **{
            "username": user.username,
            "email": user.email,
            "password": hash_password(user.password),
        }
    )

    new_user_id = create_user(new_user)

    if new_user_id == "DUPLICATE_EMAIL":
        raise GlobalErrorException(
            error_code="USER_ALREADY_EXISTS",
            error_message="The provided email is already registered.",
        )
    elif new_user_id is None:
        raise GlobalErrorException(
            error_code="USER_CREATION_FAILED",
            error_message="An error occurred while creating the user.",
        )

    return {"user_id": new_user_id}


def forgot_password(user_email: ForgotPasswordRequest):
    forgot_user_data = get_user_by_email(user_email)
    if forgot_user_data == "USER_NOT_EXISTS":
        raise GlobalErrorException(
            error_code="USER_NOT_EXISTS",
            error_message="Can't found user by email.",
        )
    forgot_user_id = forgot_user_data["user_id"]
    forgot_user_email = forgot_user_data["email"]
    token = create_jwt_token(
        data={"sub": forgot_user_id, "email": forgot_user_email},
        expires_delta=timedelta(minutes=15),
    )
    send_reset_email(user_email, token)


def reset_password(user_id: str, new_password: str):
    update_user_data = get_user_by_id(user_id)
    if update_user_data == "USER_NOT_EXISTS":
        raise GlobalErrorException(
            error_code="USER_NOT_EXISTS",
            error_message="Can't found user by email.",
        )

    hashed_password = hash_password(new_password)
    update_user_password(user_id, hashed_password)
