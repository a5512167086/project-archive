from contextlib import contextmanager

import psycopg2

from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
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
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL:", error)
        raise GlobalErrorException(
            error_code="DATABASE_ERROR",
            error_message=" ".join(str(error).split()),
        )
    finally:
        if connection:
            connection.close()
