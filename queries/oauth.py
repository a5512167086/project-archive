from database import get_db_connection
import psycopg2
import psycopg2.extras


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
