from typing import Any, Dict

from fastapi import Depends

from modules.user.auth_service import verify_auth, verify_reset


def get_current_user(payload: Dict[str, Any] = Depends(verify_auth)) -> Dict[str, str]:

    return {
        "user_id": payload["sub"],
        "email": payload.get("email"),
    }


def get_reset_user(payload: Dict[str, Any] = Depends(verify_reset)) -> Dict[str, str]:

    return {
        "user_id": payload["sub"],
        "email": payload.get("email"),
    }
