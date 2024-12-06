from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from exception import GlobalErrorException
from config import FRONTEND_URL, EMAIL, EMAIL_APP_PASSWORD
from jinja2 import Template
import smtplib
import os


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
    except Exception as e:
        raise GlobalErrorException(
            error_code="EMAIL_SERVICE_FAILED",
            error_message="Can't send email.",
        )
