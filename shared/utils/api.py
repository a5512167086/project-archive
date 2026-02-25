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
        return None
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


def rag_customer_service(
    bot_uuid: str,
    line_id: str,
    query: str,
    model: str = "qwen2.5_local",
    top_k: int = 3,
    fetch_k: int = 15,
    score_threshold: float = 0.3,
    rerank_threshold: float = 0.1,
):
    url = f"{RAG_BACKEND_URL}/query"
    response = requests.post(
        url,
        json={
            "bot_uuid": bot_uuid,
            "line_id": line_id,
            "query": query,
            "top_k": top_k,
            "fetch_k": fetch_k,
            "score_threshold": score_threshold,
            "rerank_threshold": rerank_threshold,
            "model": model,
        },
    )

    if response.status_code != 200:
        response.raise_for_status()

    return response.json()


def rag_vector_ingest(bot_uuid: str):
    url = f"{RAG_BACKEND_URL}/ingest"

    try:
        response = requests.post(url, json={"bot_uuid": bot_uuid}, timeout=300)

        if response.status_code != 200:
            print(f"RAG Ingest failed: {response.text}")
            response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to RAG backend: {e}")
        raise


def rag_vector_purge(bot_uuid: str):
    url = f"{RAG_BACKEND_URL}/purge"

    try:
        response = requests.post(url, json={"bot_uuid": bot_uuid}, timeout=300)

        if response.status_code != 200:
            print(f"RAG Ingest failed: {response.text}")
            response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to RAG backend: {e}")
        raise
