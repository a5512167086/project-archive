import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import DecodeError, ExpiredSignatureError, InvalidTokenError

from shared.constants.config import JWT_REFRESH_SECRET, JWT_RESET_SECRET, JWT_SECRET
from shared.constants.error_code import ErrorCode
from shared.exception import GlobalErrorException

logger = logging.getLogger(__name__)


ACCESS_TOKEN_EXPIRE = timedelta(days=1)
REFRESH_TOKEN_EXPIRE = timedelta(days=7)
REFRESH_TOKEN_REMEMBER_EXPIRE = timedelta(days=30)


def create_jwt_token(
    data: Dict[str, Any], secret: str, expires_delta: timedelta
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    to_encode.update({"iat": datetime.now(timezone.utc)})

    token = jwt.encode(to_encode, secret, algorithm="HS256")
    return token


def generate_token_pair(
    user_id: str, email: str, is_remember: bool = False
) -> Dict[str, str]:
    access_payload = {"sub": str(user_id), "email": email, "type": "access"}
    refresh_payload = {"sub": str(user_id), "email": email, "type": "refresh"}

    access_exp = ACCESS_TOKEN_EXPIRE
    refresh_exp = REFRESH_TOKEN_REMEMBER_EXPIRE if is_remember else REFRESH_TOKEN_EXPIRE

    access_token = create_jwt_token(access_payload, JWT_SECRET, access_exp)
    refresh_token = create_jwt_token(refresh_payload, JWT_REFRESH_SECRET, refresh_exp)

    logger.info(f"Generated token pair for user: {user_id}, remember: {is_remember}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


class JWTValidator:
    def __init__(self, secret: str, token_type: str = "access"):
        self.secret = secret
        self.token_type = token_type
        self.security = HTTPBearer()

    def decode_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.secret, algorithms=["HS256"])

            if payload.get("type") and payload.get("type") != self.token_type:
                raise GlobalErrorException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    error_code=ErrorCode.TOKEN_INVALID,
                    error_message=f"Invalid token type. Expected {self.token_type}",
                )

            user_id = payload.get("sub")

            if not user_id:
                raise GlobalErrorException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    error_code=ErrorCode.TOKEN_PAYLOAD_INVALID,
                    error_message="Invalid user payload",
                )

            return payload

        except ExpiredSignatureError:
            msg = "Token has expired"
            if self.token_type == "refresh":
                msg = "Refresh token has expired, please login again"

            raise GlobalErrorException(
                status_code=status.HTTP_403_FORBIDDEN,
                error_code=ErrorCode.TOKEN_EXPIRED,
                error_message=msg,
            )
        except (DecodeError, InvalidTokenError):
            raise GlobalErrorException(
                status_code=status.HTTP_403_FORBIDDEN,
                error_code=ErrorCode.TOKEN_INVALID,
                error_message="Invalid token",
            )

    def __call__(
        self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> Dict[str, Any]:
        return self.decode_token(credentials.credentials)


verify_auth = JWTValidator(secret=JWT_SECRET, token_type="access")
verify_refresh = JWTValidator(secret=JWT_REFRESH_SECRET, token_type="refresh")
verify_reset = JWTValidator(secret=JWT_RESET_SECRET, token_type="reset")
