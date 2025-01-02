from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from schemas import TokenRequest, TokenResponse, VerifyResponse
from services.auth import generate_access_token
from utils import verify_jwt_token

router = APIRouter()
security = HTTPBearer()


@router.post("/token", tags=["auth"], response_model=TokenResponse)
async def sign_jwt(data: TokenRequest):
    token_data = generate_access_token(
        user_id=data.user_id, email=data.email, is_remeber=data.is_remeber
    )
    return token_data


@router.get("/verify", tags=["auth"], response_model=VerifyResponse)
async def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = verify_jwt_token(credentials)
        return {
            "X-User-ID": payload["sub"],
            "X-User-Email": payload["email"],
        }
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired token.",
        )
