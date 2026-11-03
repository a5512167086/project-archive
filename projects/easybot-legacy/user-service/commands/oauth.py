from database import get_db_connection
from schemas import OAuth
import psycopg2
import psycopg2.extras


def create_oauth(oauth: OAuth):
    try:
        with get_db_connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    "INSERT INTO oauths(user_id, oauth_provider, oauth_user_id) VALUES(%s, %s, %s);",
                    [oauth.user_id, oauth.oauth_provider, oauth.oauth_user_id],
                )
                connection.commit()
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        if error_message and "EMail已存在" in error_message:
               return "DUPLICATE_EMAIL"

        return None
