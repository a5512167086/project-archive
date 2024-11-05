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

# 設定資料庫連接
conn = None
try:
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # 指定SQL檔案的目錄
    tables_folder = "./database/tables/"

    # 使用 glob 來取得所有 SQL 檔案
    sql_files = glob.glob(f"{tables_folder}*.sql")

    # 執行每個 SQL 檔案
    for file in sql_files:
        print(f"Running SQL file: {file} ...")
        try:
            with open(file, "r", encoding="utf-8") as sql_file:
                sql_commands = sql_file.read()
                cursor.execute(sql.SQL(sql_commands))
            print(f"Successfully executed {file}")
        except Exception as e:
            print(f"Error occurred while executing {file}: {e}")
            sys.exit(1)  # 結束腳本，因為出錯了

    # 指定SQL檔案的目錄
    scripts_folder = "./database/scripts/"

    # 使用 glob 來取得所有 SQL 檔案
    sql_files = glob.glob(f"{scripts_folder}*.sql")

    # 執行每個 SQL 檔案
    for file in sql_files:
        print(f"Running SQL file: {file} ...")
        try:
            with open(file, "r", encoding="utf-8") as sql_file:
                sql_commands = sql_file.read()
                cursor.execute(sql.SQL(sql_commands))
            print(f"Successfully executed {file}")
        except Exception as e:
            print(f"Error occurred while executing {file}: {e}")
            sys.exit(1)  # 結束腳本，因為出錯了

    # 指定SQL檔案的目錄
    view_folder = "./database/views/"

    # 使用 glob 來取得所有 SQL 檔案
    sql_files = glob.glob(f"{view_folder}*.sql")

    # 執行每個 SQL 檔案
    for file in sql_files:
        print(f"Running SQL file: {file} ...")
        try:
            with open(file, "r", encoding="utf-8") as sql_file:
                sql_commands = sql_file.read()
                cursor.execute(sql.SQL(sql_commands))
            print(f"Successfully executed {file}")
        except Exception as e:
            print(f"Error occurred while executing {file}: {e}")
            sys.exit(1)  # 結束腳本，因為出錯了

    # 指定SQL檔案的目錄
    functions_folder = "./database/functions/"

    # 使用 glob 來取得所有 SQL 檔案
    sql_files = glob.glob(f"{functions_folder}*.sql")

    # 執行每個 SQL 檔案
    for file in sql_files:
        print(f"Running SQL file: {file} ...")
        try:
            with open(file, "r", encoding="utf-8") as sql_file:
                sql_commands = sql_file.read()
                cursor.execute(sql.SQL(sql_commands))
            print(f"Successfully executed {file}")
        except Exception as e:
            print(f"Error occurred while executing {file}: {e}")
            sys.exit(1)  # 結束腳本，因為出錯了

    # 指定SQL檔案的目錄
    store_procedures_folder = "./database/store_procedures/"

    # 使用 glob 來取得所有 SQL 檔案
    sql_files = glob.glob(f"{store_procedures_folder}*.sql")

    # 執行每個 SQL 檔案
    for file in sql_files:
        print(f"Running SQL file: {file} ...")
        try:
            with open(file, "r", encoding="utf-8") as sql_file:
                sql_commands = sql_file.read()
                cursor.execute(sql.SQL(sql_commands))
            print(f"Successfully executed {file}")
        except Exception as e:
            print(f"Error occurred while executing {file}: {e}")
            sys.exit(1)  # 結束腳本，因為出錯了

    print("All SQL files executed successfully.")

    # 指定SQL檔案的目錄
    tuples_folder = "./database/tuples/"

    # 使用 glob 來取得所有 SQL 檔案
    sql_files = glob.glob(f"{tuples_folder}*.sql")

    # 執行每個 SQL 檔案
    for file in sql_files:
        print(f"Running SQL file: {file} ...")
        try:
            with open(file, "r", encoding="utf-8") as sql_file:
                sql_commands = sql_file.read()
                cursor.execute(sql.SQL(sql_commands))
            print(f"Successfully executed {file}")
        except Exception as e:
            print(f"Error occurred while executing {file}: {e}")
            sys.exit(1)  # 結束腳本，因為出錯了

    try:
        with open('./database/init_classes.sql', "r", encoding="utf-8") as sql_file:
            sql_commands = sql_file.read()
            cursor.execute(sql.SQL(sql_commands))
            print(f"Successfully executed ./database/init_classes.sql")
    except Exception as e:
        print(f"Error occurred while executing ./database/init_classes.sql: {e}")
        sys.exit(1)  # 結束腳本，因為出錯了

    print("All SQL files executed successfully.")

except psycopg2.Error as e:
    print(f"Database connection error: {e}")
    sys.exit(1)

finally:
    if conn:
        cursor.close()
        conn.close()
