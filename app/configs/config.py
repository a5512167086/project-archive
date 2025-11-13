import os

from dotenv import load_dotenv

load_dotenv()


DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION")


# Embedding Model（可換成 Qwen3-0.6B 以開發方便）
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE")


# 回答模式
TOP_K = 5

CHAT_MODEL = os.getenv("CHAT_MODEL")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

LLM_TEMPERATURE = os.getenv("LLM_TEMPERATURE")
LLM_MAX_NEW_TOKENS = os.getenv("LLM_MAX_NEW_TOKENS")

AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")