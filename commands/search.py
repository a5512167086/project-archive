import json
from typing import List

import psycopg2
import psycopg2.extras

from database import get_db_connection


def insert_search_items(bot_class_id: int, search_items: List[dict]):
    try:
        search_items_jsonb = json.dumps(search_items)
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "CALL sp_insert_search_items(%s, %s::jsonb);",
                    [bot_class_id, search_items_jsonb],
                )
                connection.commit()
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        print(f"Database error: {error_message}")
        raise
