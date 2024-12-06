from database import get_db_connection
from schemas import RegisterRequest
import psycopg2
import psycopg2.extras


def create_user(user: RegisterRequest):
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "SELECT fs_insert_user(%s, %s, %s);",
                    [user.username, user.email, user.password],
                )
                user_data = cursor.fetchone()
                connection.commit()
                return user_data["fs_insert_user"]
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        if "EMail已存在" in error_message:
            return "DUPLICATE_EMAIL"

        return None


def update_user_password(update_user_id: str, new_password: str):
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "UPDATE users SET password = %s WHERE user_id = %s;",
                    [new_password, update_user_id],
                )
                connection.commit()
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        if "EMail已存在" in error_message:
            return "DUPLICATE_EMAIL"

        return None
