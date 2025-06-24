import requests


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
        print("❌ 無法取得 access token")
        print(response.status_code, response.text)
        return None


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
            "scope": "openid profile email chat_message.write",
        },
        "description": "Easybot LIFF App",
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        print("❌ LIFF 建立失敗")
        print("Status Code:", response.status_code)
        print("Response Body:", response.text)
        response.raise_for_status()

    return response.json()
