import logging
from datetime import timedelta

from fastapi import status
from sqlmodel import Session

from modules.bot.bot_model import BotListWithCredentialView
from modules.user.auth_service import (
    create_jwt_token,
    generate_token_pair,
    verify_refresh,
    verify_reset,
)
from modules.user.user_command import UserCommand
from modules.user.user_query import UserQuery
from modules.user.user_schema import (
    CustomerLoginRequest,
    ForgotPasswordRequest,
    LoginRequest,
    OAuthBindRequest,
    OAuthLoginRequest,
)
from shared.commands.group_command import insert_group_member
from shared.constants.config import (
    JWT_RESET_SECRET,
)
from shared.constants.error_code import ErrorCode
from shared.exception import GlobalErrorException
from shared.services.mail_service import MailService
from shared.utils.common import (
    authenticate_with_google,
    authenticate_with_line,
    generate_random_password,
    get_line_oauth_info,
    hash_password,
    verify_password,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, session: Session):
        self.session = session
        self.mail_service = MailService()
        self.command = UserCommand(session)
        self.query = UserQuery(session)

    def create_new_user(self, username: str, email: str, password: str) -> str:
        existing_user = self.query.get_user_by_email(email)
        if existing_user:
            raise GlobalErrorException(
                error_code=ErrorCode.USER_ALREADY_EXISTS,
                error_message="User with this email already exists",
            )

        hashed_password = hash_password(password)
        new_user = self.command.create_user(username, email, hashed_password)
        return new_user.user_id

    def get_user_profile(self, user_id: str):
        user = self.query.get_user_by_id(user_id)
        if not user:
            raise GlobalErrorException(
                error_code=ErrorCode.USER_NOT_EXISTS,
                error_message="User not found",
            )
        return {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
        }

    def get_user_info_by_oauth_code(self, provider: str, code: str) -> dict:
        if provider == "google":
            return authenticate_with_google(code)
        elif provider == "line":
            return authenticate_with_line(code)
        else:
            raise GlobalErrorException(
                error_code=ErrorCode.OAUTH_PROVIDER_NOT_SUPPORTED,
                error_message=f"Unsupported OAuth provider: {provider}",
            )

    def login(self, user: LoginRequest):
        db_user = self.query.get_user_by_email(user.email)
        if not db_user or not verify_password(user.password, db_user.password):
            raise GlobalErrorException(
                error_code=ErrorCode.PASSWORD_NOT_MATCH,
                error_message="Invalid email or password",
            )

        return generate_token_pair(db_user.user_id, db_user.email, user.remember)

    def refresh_token(self, refresh_token: str):
        try:
            payload = verify_refresh.decode_token(refresh_token)
        except GlobalErrorException as e:
            if e.error_code == ErrorCode.TOKEN_EXPIRED:
                raise GlobalErrorException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    error_code=ErrorCode.TOKEN_EXPIRED,
                    error_message="Refresh token has expired, please login again",
                )
            raise e

        user = self.query.get_user_by_id(payload["sub"])
        if not user:
            raise GlobalErrorException(
                error_code=ErrorCode.USER_NOT_EXISTS,
                error_message="User not found",
            )

        return generate_token_pair(user.user_id, user.email, True)

    def handle_new_oauth_user(self, oauth_user_info, provider):
        random_password = generate_random_password()
        hashed_password = hash_password(random_password)

        new_user = self.command.create_user(
            oauth_user_info["name"], oauth_user_info["email"], hashed_password
        )

        self.command.create_oauth(new_user.user_id, provider, oauth_user_info["id"])

        token = generate_token_pair(new_user.user_id, new_user.email, True)

        return token

    def handle_existed_oauth_user(self, provider: str, oauth_user_id: str):
        oauth_record = self.query.get_oauth_by_oauth_user_id(provider, oauth_user_id)
        if oauth_record:
            user = self.query.get_user_by_id(oauth_record.user_id)
            return generate_token_pair(user.user_id, user.email, True)
        return "USER_ALREADY_EXISTS"

    def oauth_login(self, oauth: OAuthLoginRequest):
        oauth_user_info = self.get_user_info_by_oauth_code(oauth.provider, oauth.code)

        existing_user = self.query.get_user_by_email(oauth_user_info["email"])
        if not existing_user:
            return self.handle_new_oauth_user(oauth_user_info, oauth.provider)

        token_or_status = self.handle_existed_oauth_user(
            oauth.provider, oauth_user_info["id"]
        )
        if token_or_status == "USER_ALREADY_EXISTS":
            raise GlobalErrorException(
                ErrorCode.USER_ALREADY_EXISTS,
                "User already exists, please login and bind.",
            )

        return token_or_status

    def oauth_bind(self, user_id: str, oauth: OAuthBindRequest):
        oauth_user_info = self.get_user_info_by_oauth_code(oauth.provider, oauth.code)

        existing_oauth = self.query.get_oauth_by_oauth_user_id(
            oauth.provider, oauth_user_info["id"]
        )
        if existing_oauth:
            raise GlobalErrorException(
                ErrorCode.OAUTH_ALREADY_EXISTS,
                "This OAuth account is already bound to another user",
            )

        self.command.create_oauth(user_id, oauth.provider, oauth_user_info["id"])

    def check_oauth_status(self, user_id: str):
        oauth_accounts = self.query.get_oauth_by_user_id(user_id)

        status = {}
        for oauth in oauth_accounts:
            status[oauth.oauth_provider] = True

        return {
            "google": status.get("google", False),
            "line": status.get("line", False),
        }

    def forgot_password(self, forgot_request: ForgotPasswordRequest):
        user = self.query.get_user_by_email(forgot_request.email)
        if not user:
            raise GlobalErrorException(
                error_code=ErrorCode.USER_NOT_EXISTS,
                error_message="User not found with this email",
            )

        reset_token = create_jwt_token(
            {"sub": str(user.user_id), "email": user.email},
            JWT_RESET_SECRET,
            timedelta(minutes=15),
        )
        self.mail_service.send_reset_email(user.email, reset_token)

    def reset_password(self, user_id: str, new_password: str):
        user = self.query.get_user_by_id(user_id)
        if not user:
            raise GlobalErrorException(
                error_code=ErrorCode.USER_NOT_EXISTS,
                error_message="User not found",
            )

        hashed_password = hash_password(new_password)
        self.command.update_user_password(user_id, hashed_password)

    def reset_password_with_token(self, reset_token: str, new_password: str):
        if self.query.is_token_in_blacklist(reset_token):
            raise GlobalErrorException(
                error_code=ErrorCode.TOKEN_INVALID,
                error_message="This reset link has already been used.",
            )
        payload = verify_reset.decode_token(reset_token)
        user_id = payload.get("sub")

        user = self.query.get_user_by_id(user_id)
        if not user:
            raise GlobalErrorException(
                error_code=ErrorCode.USER_NOT_EXISTS,
                error_message="User not found",
            )

        hashed_password = hash_password(new_password)
        self.command.update_user_password(user_id, hashed_password)

        try:
            self.command.add_token_to_blacklist(reset_token, 900)
        except Exception as e:
            logger.error(f"Failed to add token to blacklist: {e}")

    def customer_login(
        self,
        group_id: int,
        customer: CustomerLoginRequest,
        bot: BotListWithCredentialView,
    ):
        user_info = get_line_oauth_info(customer.line_id_token, bot.login_channel_id)
        print(user_info)
        user = self.query.get_user_by_email(user_info["email"])
        if not user:
            random_password = generate_random_password()
            hashed_password = hash_password(random_password)

            new_user = self.command.create_user(
                user_info["name"], user_info["email"], hashed_password
            )

            self.command.create_oauth(new_user.user_id, "line", user_info["id"])

            insert_group_member(self.session, group_id, new_user.user_id, 2, None, True)

            token = generate_token_pair(new_user.user_id, new_user.email, True)
            return token

        oauth_user_info = self.handle_existed_oauth_user("line", user_info["id"])
        if oauth_user_info == "USER_ALREADY_EXISTS":
            raise GlobalErrorException(
                ErrorCode.USER_ALREADY_EXISTS,
                "User already exists, please login and bind.",
            )

        insert_group_member(self.session, group_id, user.user_id, 2, None, True)
        return oauth_user_info

    def change_password(self, email: str, old_password: str, new_password: str):
        user = self.query.get_user_by_email(email)
        if not user:
            raise GlobalErrorException(
                error_code=ErrorCode.USER_NOT_EXISTS,
                error_message="User not found",
            )

        if not verify_password(old_password, user.password):
            raise GlobalErrorException(
                error_code=ErrorCode.PASSWORD_NOT_MATCH,
                error_message="Current password is incorrect",
            )

        hashed_password = hash_password(new_password)
        self.command.update_user_password(user.user_id, hashed_password)
