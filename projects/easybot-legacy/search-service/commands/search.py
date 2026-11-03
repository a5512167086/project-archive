import json
from typing import List

import psycopg2
import psycopg2.extras
from schemas import NewSearchItem
from database import get_db_connection


def insert_search_item(bot_class_id: int, search_item: NewSearchItem):
    try:
        search_item_jsonb = search_item.model_dump_json()
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "CALL sp_insert_search_item(%s, %s::jsonb);",
                    [bot_class_id, search_item_jsonb],
                )
                connection.commit()
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        print(f"Database error: {error_message}")
        raise


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


def delete_search_items(bot_class_id: int, delete_items_id: List[int]):
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "SELECT * FROM fs_delete_search_items(%s, %s);",
                    [bot_class_id, delete_items_id],
                )
                delete_result = cursor.fetchall()
                connection.commit()
                success_ids = [
                    row["_object_id"] for row in delete_result if row["_is_deleted"]
                ]
                failed_ids = [
                    row["_object_id"] for row in delete_result if not row["_is_deleted"]
                ]

                return {"success_ids": success_ids, "failed_ids": failed_ids}
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        print(f"Database error: {error_message}")
        raise
