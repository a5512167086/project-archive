from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, create_engine

from shared.constants.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=240,
    pool_pre_ping=True,
)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
