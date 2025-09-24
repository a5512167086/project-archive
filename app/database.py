from typing import Annotated

from fastapi import Depends
from qdrant_client import QdrantClient
from sqlmodel import Session, create_engine

from app.configs.config import (
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
    QDRANT_URL,
)

# RDB
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=False)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

# VectorDB
client = QdrantClient(url=QDRANT_URL)
