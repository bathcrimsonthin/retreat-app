import os

import psycopg # PostgreSQL データベースに接続するためのライブラリ
from dotenv import load_dotenv # 機密情報を .env で管理するためのライブラリ 

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# データベースを開く
with psycopg.connect(DATABASE_URL) as conn:
    # データベース操作を実行するためのカーソルを開く
    with conn.cursor() as cur:
        # データベースのバージョンを取得するクエリを実行
        cur.execute("SELECT version();")
        # 結果を取得
        db_version = cur.fetchone()
        print(f"Database version: {db_version[0]}")