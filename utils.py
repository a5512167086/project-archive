import secrets
import string

import bcrypt
import requests
from fastapi import HTTPException
from requests.exceptions import RequestException

from config import (
    AUTH_SERVICE_API_URL,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
)
from exception import GlobalErrorException


def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def create_jwt_token(data: dict):
    try:
        response = requests.post(f"{AUTH_SERVICE_API_URL}/token", json=data)
        return response.json()
    except RequestException:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate JWT token",
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
