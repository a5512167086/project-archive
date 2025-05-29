import psycopg2
import psycopg2.extras

from database import get_db_connection
from schemas.command_schema import CommandType


def insert_feature_command(
    bot_class_id: int,
    command_name: str,
    command_keyword: str,
    command_type: CommandType,
):
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "CALL sp_insert_feature_command(%s, %s, %s, %s);",
                    [bot_class_id, command_name, command_keyword, command_type],
                )
                connection.commit()
    except psycopg2.Error:
        raise
