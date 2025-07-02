import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Template

from exception import GlobalErrorException
from shared.constants.config import EMAIL, EMAIL_APP_PASSWORD, FRONTEND_URL
from shared.constants.error_code import ErrorCode


def send_reset_email(email: str, token: str):
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"

    file_path = os.path.join(
        os.path.dirname(__file__), "..", "templates", "password-reset.html"
    )
    with open(file_path, "r", encoding="utf-8") as file:
        template = Template(file.read())
        email_content = template.render(action_url=reset_link)

    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL
    msg["To"] = email
    msg["Subject"] = "Easybot - 重設您的使用者密碼"
    msg.attach(MIMEText(email_content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL, email, msg.as_string())
    except Exception:
        raise GlobalErrorException(
            error_code=ErrorCode.EMAIL_SERVICE_FAILED,
            error_message="Can't send email.",
        )
