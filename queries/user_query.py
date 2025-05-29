import bcrypt
import psycopg2
import psycopg2.extras

from database import get_db_connection


def get_oauth(provider: str, oauth_user_id: str):
    with get_db_connection() as connection:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                "SELECT user_id, oauth_provider, oauth_user_id FROM oauths WHERE oauth_provider = %s AND oauth_user_id = %s",
                [provider, oauth_user_id],
            )
            oauth_data = cursor.fetchone()

            return oauth_data


def get_oauth_by_oauth_user_id(provider: str, user_id: str):
    with get_db_connection() as connection:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                "SELECT user_id, oauth_provider, oauth_user_id FROM oauths WHERE oauth_provider = %s AND oauth_user_id = %s",
                [provider, user_id],
            )
            oauth_data = cursor.fetchone()
            if not oauth_data:
                return "OAUTH_NOT_EXISTS"

            return oauth_data


def get_oauth_by_user_id(user_id: str):
    with get_db_connection() as connection:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                "SELECT user_id, oauth_provider, oauth_user_id FROM oauths WHERE user_id = %s",
                [user_id],
            )
            oauth_data = cursor.fetchall()

            return oauth_data


def get_user_by_id(user_id: str):
    with get_db_connection() as connection:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                "SELECT username, email FROM users WHERE user_id = %s", [user_id]
            )
            user_data = cursor.fetchone()
            if not user_data:
                return "USER_NOT_EXISTS"

            return user_data


def get_user_by_email(user_email: str):
    with get_db_connection() as connection:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                "SELECT user_id, username, email FROM users WHERE email = %s",
                [user_email],
            )
            user_data = cursor.fetchone()
            if not user_data:
                return "USER_NOT_EXISTS"

            return user_data


def get_user_by_email_and_password(user_email: str, user_password: str):
    with get_db_connection() as connection:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                "SELECT user_id, email, password FROM users WHERE email = %s",
                [user_email],
            )
            user_data = cursor.fetchone()

            if not user_data:
                return "USER_NOT_EXISTS"

            hashed_password = user_data["password"]

            if not bcrypt.checkpw(
                user_password.encode("utf-8"), hashed_password.encode("utf-8")
            ):
                return "PASSWORD_NOT_MATCH"
            return user_data
