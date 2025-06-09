from contextlib import contextmanager
from typing import Annotated

import psycopg2
from fastapi import Depends
from psycopg2 import InterfaceError, OperationalError
from sqlmodel import Session, create_engine

from constants.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from exception import GlobalErrorException


@contextmanager
def get_db_connection():
    connection = None
    try:
        connection = psycopg2.connect(
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        yield connection
    except (OperationalError, InterfaceError) as conn_error:
        raise GlobalErrorException(
            error_code="DATABASE_CONNECTION_ERROR",
            error_message=f"Error connecting to database: {str(conn_error)}",
        )
    finally:
        if connection:
            connection.close()


DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=False)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
