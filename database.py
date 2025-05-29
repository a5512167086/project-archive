from contextlib import contextmanager

import psycopg2
from psycopg2 import InterfaceError, OperationalError

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
