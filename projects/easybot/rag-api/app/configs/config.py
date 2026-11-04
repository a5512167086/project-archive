import os

from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Qdrant Configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION")

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME")
MONGODB_CHAT_COLLECTION = os.getenv("MONGODB_CHAT_COLLECTION")

# Ollama Configuration
OLLAMA_LLM_NAME = os.getenv("OLLAMA_LLM_NAME")
OLLAMA_EMBED_NAME = os.getenv("OLLAMA_EMBED_NAME")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")

# Google API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# LLM Configuration
LLM_TEMPERATURE = os.getenv("LLM_TEMPERATURE")
LLM_MAX_NEW_TOKENS = os.getenv("LLM_MAX_NEW_TOKENS")

# Azure OpenAI Configuration
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

# MinIO Configuration
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
