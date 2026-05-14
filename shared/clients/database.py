from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlmodel import Session

from shared.constants.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


engine = create_engine(
    DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
