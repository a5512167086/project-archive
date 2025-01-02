import requests

from config import COMMAND_SERVICE_API_URL


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
