import os
import sys
import psycopg2
import glob
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

print(f"DB_HOST={DB_HOST}")
print(f"DB_PORT={DB_PORT}")
print(f"DB_NAME={DB_NAME}")
print(f"DB_USER={DB_USER}")
print(f"DB_PASSWORD={DB_PASSWORD}")

conn = None
try:
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    conn.autocommit = True
    cursor = conn.cursor()

    tables_folder = "./database/tables/"
    sql_files = glob.glob(f"{tables_folder}*.sql")
    for file in sql_files:
        print(f"Running SQL file: {file} ...")
        try:
            with open(file, "r", encoding="utf-8") as sql_file:
                sql_commands = sql_file.read()
                cursor.execute(sql.SQL(sql_commands))
            print(f"Successfully executed {file}")
        except Exception as e:
            print(f"Error occurred while executing {file}: {e}")
            sys.exit(1)

    extra_tables_folder = "./database/extra_tables/"
    sql_files = glob.glob(f"{extra_tables_folder}*.sql")
    for file in sql_files:
        print(f"Running SQL file: {file} ...")
        try:
            with open(file, "r", encoding="utf-8") as sql_file:
                sql_commands = sql_file.read()
                cursor.execute(sql.SQL(sql_commands))
            print(f"Successfully executed {file}")
        except Exception as e:
            print(f"Error occurred while executing {file}: {e}")
            sys.exit(1)

    scripts_folder = "./database/scripts/"
    sql_files = glob.glob(f"{scripts_folder}*.sql")
    for file in sql_files:
        print(f"Running SQL file: {file} ...")
        try:
            with open(file, "r", encoding="utf-8") as sql_file:
                sql_commands = sql_file.read()
                cursor.execute(sql.SQL(sql_commands))
            print(f"Successfully executed {file}")
        except Exception as e:
            print(f"Error occurred while executing {file}: {e}")
            sys.exit(1)

    view_folder = "./database/views/"
    sql_files = glob.glob(f"{view_folder}*.sql")
    for file in sql_files:
        print(f"Running SQL file: {file} ...")
        try:
            with open(file, "r", encoding="utf-8") as sql_file:
                sql_commands = sql_file.read()
                cursor.execute(sql.SQL(sql_commands))
            print(f"Successfully executed {file}")
        except Exception as e:
            print(f"Error occurred while executing {file}: {e}")
            sys.exit(1)

    extra_view_folder = "./database/extra_views/"
    sql_files = glob.glob(f"{extra_view_folder}*.sql")
    for file in sql_files:
        print(f"Running SQL file: {file} ...")
        try:
            with open(file, "r", encoding="utf-8") as sql_file:
                sql_commands = sql_file.read()
                cursor.execute(sql.SQL(sql_commands))
            print(f"Successfully executed {file}")
        except Exception as e:
            print(f"Error occurred while executing {file}: {e}")
            sys.exit(1)

    functions_folder = "./database/functions/"
    sql_files = glob.glob(f"{functions_folder}*.sql")
    for file in sql_files:
        print(f"Running SQL file: {file} ...")
        try:
            with open(file, "r", encoding="utf-8") as sql_file:
                sql_commands = sql_file.read()
                cursor.execute(sql.SQL(sql_commands))
            print(f"Successfully executed {file}")
        except Exception as e:
            print(f"Error occurred while executing {file}: {e}")
            sys.exit(1)

    extra_functions_folder = "./database/extra_functions/"
    sql_files = glob.glob(f"{extra_functions_folder}*.sql")
    for file in sql_files:
        print(f"Running SQL file: {file} ...")
        try:
            with open(file, "r", encoding="utf-8") as sql_file:
                sql_commands = sql_file.read()
                cursor.execute(sql.SQL(sql_commands))
            print(f"Successfully executed {file}")
        except Exception as e:
            print(f"Error occurred while executing {file}: {e}")
            sys.exit(1)

    store_procedures_folder = "./database/store_procedures/"
    sql_files = glob.glob(f"{store_procedures_folder}*.sql")
    for file in sql_files:
        print(f"Running SQL file: {file} ...")
        try:
            with open(file, "r", encoding="utf-8") as sql_file:
                sql_commands = sql_file.read()
                cursor.execute(sql.SQL(sql_commands))
            print(f"Successfully executed {file}")
        except Exception as e:
            print(f"Error occurred while executing {file}: {e}")
            sys.exit(1)

    tuples_folder = "./database/tuples/"
    sql_files = glob.glob(f"{tuples_folder}*.sql")
    for file in sql_files:
        print(f"Running SQL file: {file} ...")
        try:
            with open(file, "r", encoding="utf-8") as sql_file:
                sql_commands = sql_file.read()
                cursor.execute(sql.SQL(sql_commands))
            print(f"Successfully executed {file}")
        except Exception as e:
            print(f"Error occurred while executing {file}: {e}")
            sys.exit(1)

    extra_tuples_folder = "./database/extra_tuples/"
    sql_files = glob.glob(f"{extra_tuples_folder}*.sql")
    for file in sql_files:
        print(f"Running SQL file: {file} ...")
        try:
            with open(file, "r", encoding="utf-8") as sql_file:
                sql_commands = sql_file.read()
                cursor.execute(sql.SQL(sql_commands))
            print(f"Successfully executed {file}")
        except Exception as e:
            print(f"Error occurred while executing {file}: {e}")
            sys.exit(1)

    print("All SQL files executed successfully.")

except psycopg2.Error as e:
    print(f"Database connection error: {e}")
    sys.exit(1)

finally:
    if conn:
        cursor.close()
        conn.close()
