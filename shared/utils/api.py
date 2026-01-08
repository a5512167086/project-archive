import requests

from shared.constants.config import RAG_BACKEND_URL


def get_channel_access_token(channel_id: str, channel_secret: str) -> str:
    url = "https://api.line.me/oauth2/v3/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": channel_id,
        "client_secret": channel_secret,
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        return None


def get_all_liff_apps(channel_access_token: str):
    url = "https://api.line.me/liff/v1/apps"
    headers = {
        "Authorization": f"Bearer {channel_access_token}",
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 404:
        return None  # No LIFF apps found
    if response.status_code != 200:
        response.raise_for_status()

    return response.json()["apps"]


def create_liff_app(channel_access_token: str):
    url = "https://api.line.me/liff/v1/apps"
    headers = {
        "Authorization": f"Bearer {channel_access_token}",
        "Content-Type": "application/json",
    }
    data = {
        "view": {
            "type": "full",
            "url": "https://liff-web.onrender.com",
        },
        "description": "Easybot LIFF App",
        "scope": ["openid", "profile", "chat_message.write"],
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        response.raise_for_status()

    return response.json()


def delete_liff_app(channel_access_token: str, liffId: str):
    url = f"https://api.line.me/liff/v1/apps/{liffId}"
    headers = {
        "Authorization": f"Bearer {channel_access_token}",
        "Content-Type": "application/json",
    }
    response = requests.delete(url, headers=headers)
    if response.status_code != 200:
        response.raise_for_status()


def rag_customer_service(bot_uuid: str, query: str, top_k: str, score_threshold: str):
    url = f"{RAG_BACKEND_URL}/query"
    response = requests.post(
        url,
        json={
            "bot_uuid": bot_uuid,
            "query": query,
            "top_k": top_k,
            "score_threshold": score_threshold,
            "models": ["gpt35_azure", "huggingface_local"],
        },
    )
    if response.status_code != 200:
        response.raise_for_status()

    return response.json()
