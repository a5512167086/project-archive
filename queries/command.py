import psycopg2
import psycopg2.extras

from database import get_db_connection
from schemas import CommandType


def get_command_class_id_by_bot_class_id(bot_class_id: int):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT child_class_id FROM vs_sub_class \
                    WHERE class_id = %s\
                    AND entity_id = 4;",
                    [bot_class_id],
                )
                command_class_id = cursor.fetchone()

                return command_class_id
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        print(f"Database error: {error_message}")


def get_all_feature_commands_by_bot_class_id(command_class_id: int):
    try:
        valid_types = tuple(item.value for item in CommandType)

        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                # 使用 IN 子句动态过滤
                cursor.execute(
                    "SELECT command_name, command_keyword, type \
                     FROM vs_command_list \
                     WHERE class_id = %s \
                     AND type IN %s;",
                    [command_class_id, valid_types],
                )
                command_list = cursor.fetchall()
                return command_list
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        print(f"Database error: {error_message}")
