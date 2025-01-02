import logging
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError

from config import (
    ALGORITHM,
    JWT_SECRET,
)
from exception import GlobalErrorException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_jwt_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    logger.info(f"JWT token created with expiration: {expire}")
    return encoded_jwt


def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    token = credentials.credentials
    logger.info("Starting JWT token verification")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=ALGORITHM)
        logger.debug(f"Decoded payload: {payload}")

        if payload.get("sub") is None:
            logger.warning("Invalid user - 'sub' field is missing")
            raise GlobalErrorException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user",
            )
        logger.info("JWT token verification successful")
        return payload
    except PyJWTError as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token or expired",
        )
