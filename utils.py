import jwt
import requests
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError

from config import ALGORITHM, COMMAND_SERVICE_API_URL, JWT_SECRET
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


def execute_command(bot_class_id: int, message: str, message_type: str) -> str:
    try:
        response = requests.post(
            f"{COMMAND_SERVICE_API_URL}/execute-command",
            json={
                "bot_class_id": bot_class_id,
                "message": message,
                "message_type": message_type,
            },
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        return f"Request error: {str(exc)}"
    except Exception:
        return "Oops! Something went wrong. Please try again later."


def get_line_image(message_id: str, access_token: str) -> bytes:
    image_url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(image_url, headers=headers, stream=True)

    if response.status_code == 200:
        return response.content
