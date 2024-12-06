from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
JWT_SECRET = os.getenv("JWT_SECRET")
LINE_BOT_WEBHOOK_SIGNATURE_KEY = os.getenv('LINE_BOT_WEBHOOK_SIGNATURE_KEY')
ALGORITHM = "HS256"
