from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from modules.ecomm.ecomm_model import ShippingSetting
from modules.knowledge.knowledge_model import KnowledgeVectorDBStatus
from shared.constants.config import (
    MONGODB_DB_NAME,
    MONGODB_HOST,
    MONGODB_PASSWORD,
    MONGODB_PORT,
    MONGODB_USER,
)

uri = f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DB_NAME}?authSource=admin"
mongodb_client = AsyncIOMotorClient(uri)
db = mongodb_client[MONGODB_DB_NAME]


async def init_monogo_db():
    await init_beanie(
        database=db, document_models=[ShippingSetting, KnowledgeVectorDBStatus]
    )
