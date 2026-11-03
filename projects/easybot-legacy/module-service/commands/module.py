import psycopg2
import psycopg2.extras

from database import get_db_connection


def insert_module_setting(bot_class_id: int, module_name: str, is_enabled: bool):
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "CALL sp_insert_module_setting(%s, %s, %s);",
                    [bot_class_id, module_name, is_enabled],
                )
                connection.commit()
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        print(f"Database error: {error_message}")
        raise
