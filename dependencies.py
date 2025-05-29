# auth/dependencies.py

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from constants.config import JWT_RESET_SECRET, JWT_SECRET
from services.auth_service import verify_jwt_token

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    payload = verify_jwt_token(JWT_SECRET, credentials)
    return {
        "user_id": payload["sub"],
        "email": payload["email"],
    }


def get_reset_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_jwt_token(JWT_RESET_SECRET, credentials)
    return {
        "user_id": payload["sub"],
        "email": payload["email"],
    }
