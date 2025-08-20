import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import DecodeError, ExpiredSignatureError, InvalidTokenError

from shared.constants.config import JWT_REFRESH_SECRET, JWT_SECRET
from shared.constants.error_code import ErrorCode
from shared.exception import GlobalErrorException

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

ACCESS_TOKEN_EXPIRE = timedelta(days=1)
REFRESH_TOKEN_EXPIRE = timedelta(days=14)


def create_jwt_token(
    data: Dict[str, Any], secret: str, expires_delta: timedelta
) -> str:
    """建立 JWT Token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})

    token = jwt.encode(to_encode, secret, algorithm="HS256")
    logger.info(f"JWT created with exp: {expire}")
    return token


def generate_token_pair(
    user_id: str, email: str, is_remember: bool = False
) -> Dict[str, str]:
    """產生 access/refresh token pair"""
    payload = {"sub": str(user_id), "email": email}
    access_exp = timedelta(days=7) if is_remember else ACCESS_TOKEN_EXPIRE

    access_token = create_jwt_token(payload, JWT_SECRET, access_exp)
    refresh_token = create_jwt_token(payload, JWT_REFRESH_SECRET, REFRESH_TOKEN_EXPIRE)

    logger.info(f"Generated token pair for user: {user_id}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def _verify_jwt_token(
    token: str,
    secret: str,
) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id or not email:
            raise GlobalErrorException(
                status_code=status.HTTP_403_FORBIDDEN,
                error_code=ErrorCode.TOKEN_PAYLOAD_INVALID,
                error_message="Invalid user payload",
            )

        return payload

    except ExpiredSignatureError:
        raise GlobalErrorException(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=ErrorCode.TOKEN_EXPIRED,
            error_message="Token has expired",
        )
    except (DecodeError, InvalidTokenError):
        raise GlobalErrorException(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=ErrorCode.TOKEN_INVALID,
            error_message="Invalid token",
        )


# For dependency
def verify_jwt_token(
    secret: str,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> Dict[str, Any]:
    token = credentials.credentials
    return _verify_jwt_token(token, secret)
