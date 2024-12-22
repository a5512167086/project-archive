import psycopg2
import psycopg2.extras

from database import get_db_connection


def get_all_bots_by_user_id(user_id: str):
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "SELECT class_id, object_id, chinese_name, channel_id, owner_id\
                    FROM vs_bot_list \
                    WHERE owner_id = %s;",
                    [user_id],
                )
                bot_list = cursor.fetchall()
                return bot_list
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        print(error_message)


def get_bot_by_id(bot_id: int):
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "SELECT class_id, object_id, chinese_name, owner_id \
                    FROM vs_bot_list \
                    WHERE class_id = %s;",
                    [bot_id],
                )
                bot_data = cursor.fetchone()
                return bot_data
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        print(error_message)


def get_bot_subclass(bot_id: int):
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "SELECT * FROM fs_get_child_class(%s);",
                    [bot_id],
                )
                bot_subclass_list = cursor.fetchall()
                return bot_subclass_list
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        print(error_message)


def get_line_bot_credentials(bot_uuid):
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "SELECT class_id, channel_access_token, channel_secret \
                    FROM vs_bot_list_with_credential \
                    WHERE bot_detail_id = %s;",
                    [bot_uuid],
                )
                bot_credentials = cursor.fetchone()
                return bot_credentials
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        print(error_message)
