import psycopg2
import psycopg2.extras

from database import get_db_connection


def get_all_search_items():
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "SELECT * FROM vs_search_item_text_list;",
                )
                search_items = cursor.fetchall()

                return search_items
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        print(f"Database error: {error_message}")
