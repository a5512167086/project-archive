from typing import List
from database import get_db_connection
from schemas import InsertBotRequest
import psycopg2
import psycopg2.extras


def insert_new_bot(user_id: str, new_bot: InsertBotRequest):
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "SELECT * FROM fs_insert_bot(%s, %s, %s, %s, %s);",
                    [new_bot.bot_name, new_bot.bot_channel_id,
                        new_bot.bot_channel_access_token, new_bot.bot_channel_secret, user_id],
                )
                new_bot_data = cursor.fetchone()
                connection.commit()
                return new_bot_data
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        print(error_message)


def delete_bot_by_id(delete_bot_id: int, bot_object_id: int, bot_subclass_id_list: List[int]):
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute("CALL sp_delete_class(%s);",
                               [delete_bot_id])
                cursor.execute('CALL sp_delete_object(%s);', [bot_object_id])

                for bot_subclass_id in bot_subclass_id_list:
                    cursor.execute("CALL sp_delete_class(%s);",
                                   [bot_subclass_id])
                connection.commit()
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        print(error_message)


def update_bot_boy_id(bot_object_id: int, update_bot: dict):
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                if update_bot.get('bot_name'):
                    cursor.execute("Update objects SET chinese_name = %s WHERE object_id = %s;",
                                   [update_bot['bot_name'], bot_object_id])
                    update_bot.pop('bot_name')

                if isinstance(update_bot, dict) and update_bot:
                    set_clause = ", ".join(
                        [f"{key} = %s" for key in update_bot.keys()])
                    parameters = list(update_bot.values()) + [bot_object_id]
                    cursor.execute(f"""
                        UPDATE bot_details
                        SET {set_clause}
                        WHERE object_id = %s
                    """, parameters)

                connection.commit()
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        print(error_message)
