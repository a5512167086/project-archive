import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError

from config import ALGORITHM, JWT_SECRET
from exception import GlobalErrorException


def verify_jwt_token(
    request: Request, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=ALGORITHM)

        if payload.get("sub") is None:
            raise GlobalErrorException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user",
            )
        request.state.payload = payload
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token or expired",
        )
