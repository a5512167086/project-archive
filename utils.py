from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import JWT_SECRET, LINE_BOT_WEBHOOK_SIGNATURE_KEY, ALGORITHM
from jwt import PyJWTError
from exception import GlobalErrorException
import jwt


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
