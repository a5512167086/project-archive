import secrets
import string
from typing import Any, Dict, List

import bcrypt
import requests

from shared.constants.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    LINE_CLIENT_ID,
    LINE_CLIENT_SECRET,
    LINE_REDIRECT_URI,
)
from shared.constants.error_code import ErrorCode
from shared.exception import GlobalErrorException


def get_line_image(message_id: str, access_token: str) -> bytes:
    image_url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(image_url, headers=headers, stream=True)

    if response.status_code == 200:
        return response.content


def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def google_code_to_token(code: str):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": GOOGLE_REDIRECT_URI,
    }

    response = requests.post(token_url, data=data)

    if response.status_code != 200:
        raise GlobalErrorException(
            ErrorCode.OAUTH_FAILED, "Failed to authenticate with Google OAuth."
        )

    token_info = response.json()
    access_token = token_info.get("access_token")
    id_token = token_info.get("id_token")
    return {"access_token": access_token, "id_token": id_token}


def get_google_oauth_info(access_token):
    user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(user_info_url, headers=headers)

    if response.status_code != 200:
        raise GlobalErrorException(
            ErrorCode.OAUTH_FAILED, "Failed to retrieve user info from Google."
        )

    user_info = response.json()
    return user_info


def authenticate_with_google(oauth_code):
    google_oauth_response = google_code_to_token(oauth_code)

    google_user_info = get_google_oauth_info(google_oauth_response["access_token"])

    return google_user_info


def line_code_to_token(auth_code: str):
    token_url = "https://api.line.me/oauth2/v2.1/token"

    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": LINE_CLIENT_ID,
        "client_secret": LINE_CLIENT_SECRET,
        "redirect_uri": LINE_REDIRECT_URI,
    }

    response = requests.post(token_url, data=data)

    if response.status_code != 200:
        raise GlobalErrorException(
            ErrorCode.OAUTH_FAILED, "Failed to authenticate with LINE OAuth."
        )

    token_info = response.json()
    id_token = token_info.get("id_token")
    access_token = token_info.get("access_token")
    return {"id_token": id_token, "access_token": access_token}


def get_line_oauth_info(id_token: str, login_channel_id: str = ""):
    verify_url = "https://api.line.me/oauth2/v2.1/verify"
    client_id = login_channel_id if login_channel_id else LINE_CLIENT_ID

    data = {
        "id_token": id_token,
        "client_id": client_id,
    }

    response = requests.post(verify_url, data=data)

    if response.status_code != 200:
        raise GlobalErrorException(
            ErrorCode.OAUTH_FAILED, "Failed to retrieve user info from LINE."
        )

    user_info = response.json()
    return {
        "id": user_info.get("sub"),
        "name": user_info.get("name"),
        "email": user_info.get("email"),
    }


def authenticate_with_line(auth_code: str):
    line_oauth_response = line_code_to_token(auth_code)

    user_info = get_line_oauth_info(line_oauth_response["id_token"])

    return user_info


def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = "".join(secrets.choice(characters) for _ in range(length))
    return password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def get_enabled_commands(
    command_list: List[Dict[str, Any]], module_list: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    enabled_commands = []

    for command in command_list:
        if command["type"] == "Custom":
            continue

        matched_module = next(
            (
                module
                for module in module_list
                if module["chinese_name"]
                == command["chinese_name"].replace(" Command", "")
            ),
            None,
        )

        if matched_module and matched_module["is_enabled"]:
            enabled_commands.append({
                "command_keyword": command["command_keyword"],
                "type": command["type"],
                "status": True,
            })

    return enabled_commands


def get_full_commands(
    command_list: List[Dict[str, Any]], module_list: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    full_commands = []
    for command in command_list:
        status = False

        for module in module_list:
            if module["chinese_name"] == command["type"]:
                status = module["is_enabled"]
                break

        full_commands.append({
            "command_keyword": command["command_keyword"],
            "type": command["type"],
            "status": status,
        })

    return full_commands
