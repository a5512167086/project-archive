import glob
import os
import sys

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

load_dotenv()

# 讀取環境變數
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

print(f"DB_HOST={DB_HOST}")
print(f"DB_PORT={DB_PORT}")
print(f"DB_NAME={DB_NAME}")
print(f"DB_USER={DB_USER}")

if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD]):
    print("❌ 環境變數未完全設置，請確認 .env 檔案")
    sys.exit(1)


# 執行某資料夾下的所有 SQL（已排序）
def run_sql_folder(cursor, folder_path: str):
    sql_files = sorted(glob.glob(os.path.join(folder_path, "*.sql")))
    for file in sql_files:
        print(f"🔹 Running SQL file: {file} ...")
        try:
            with open(file, "r", encoding="utf-8") as sql_file:
                sql_commands = sql_file.read()
                cursor.execute(sql.SQL(sql_commands))
            print(f"✅ Successfully executed {file}")
        except Exception as e:
            print(f"❌ Error occurred while executing {file}: {e}")
            sys.exit(1)


conn = None
try:
    # 連線資料庫
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # 定義要執行的資料夾路徑（依執行順序）
    folders = [
        "./database/tables/",
        "./database/extra_tables/",
        "./database/functions/",
        "./database/extra_functions/",
        "./database/store_procedures/",
        "./database/views/",
        "./database/extra_views/",
        "./database/scripts/",
        "./database/tuples/",
    ]

    for folder in folders:
        run_sql_folder(cursor, folder)

    print("🎉 All SQL files executed successfully.")

except psycopg2.Error as e:
    print(f"❌ Database connection error: {e}")
    sys.exit(1)

finally:
    if conn:
        cursor.close()
        conn.close()
