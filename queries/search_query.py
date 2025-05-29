import psycopg2
import psycopg2.extras

from database import get_db_connection


def get_search_class_id_by_bot_class_id(bot_class_id: int):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT child_class_id FROM vs_sub_class \
                    WHERE class_id = %s\
                    AND entity_id = 11;",
                    [bot_class_id],
                )
                search_class_id = cursor.fetchone()

                return search_class_id
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        print(f"Database error: {error_message}")


def get_all_search_text_items_by_class_id(class_id: int):
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "SELECT * FROM vs_search_item_text_list \
                    WHERE class_id = %s;",
                    [class_id],
                )
                search_items = cursor.fetchall()

                return search_items
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        print(f"Database error: {error_message}")


def get_all_search_image_items_by_class_id(class_id: int):
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "SELECT * FROM vs_search_item_image_list \
                    WHERE class_id = %s;",
                    [class_id],
                )
                search_items = cursor.fetchall()

                return search_items
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        print(f"Database error: {error_message}")
