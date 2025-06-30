from typing import Annotated

from constants.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from fastapi import Depends
from sqlmodel import Session, create_engine

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=False)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
