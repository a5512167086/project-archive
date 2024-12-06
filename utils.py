from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta, timezone
from config import (
    JWT_SECRET,
    ALGORITHM,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_CLIENT_ID,
    GOOGLE_REDIRECT_URI,
)
from jwt import PyJWTError
from exception import GlobalErrorException
import bcrypt
import jwt
import requests
import secrets
import string


def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def create_jwt_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


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


def google_code_to_token(code):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": GOOGLE_REDIRECT_URI,
    }

    response = requests.post(token_url, data=data)

    if response.status_code == 200:
        token_info = response.json()
        access_token = token_info.get("access_token")
        id_token = token_info.get("id_token")
        return {"access_token": access_token, "id_token": id_token}
    else:
        return "OAUTH_FAILED"


def get_google_oauth_info(access_token):
    user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(user_info_url, headers=headers)

    if response.status_code == 200:
        user_info = response.json()
        return user_info
    else:
        return "USER_INFO_REQUEST_FAILED"


def authenticate_with_google(oauth_code):
    google_oauth_response = google_code_to_token(oauth_code)
    if google_oauth_response == "OAUTH_FAILED":
        raise GlobalErrorException(
            "OAUTH_FAILED", "Failed to authenticate with Google OAuth."
        )

    google_user_info = get_google_oauth_info(google_oauth_response["access_token"])
    if google_user_info == "USER_INFO_REQUEST_FAILED":
        raise GlobalErrorException(
            "OAUTH_FAILED", "Failed to retrieve user info from Google."
        )

    return google_user_info


def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = "".join(secrets.choice(characters) for _ in range(length))
    return password
