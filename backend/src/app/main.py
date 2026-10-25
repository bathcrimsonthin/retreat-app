from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

import os
import psycopg # PostgreSQL データベースに接続するためのライブラリ
from dotenv import load_dotenv # 機密情報を .env で管理するためのライブラリ 


from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from jwt.exceptions import InvalidTokenError

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.environ["SECRET_KEY"]
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)

password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer()

app = FastAPI()

# 受け取るJSON構造
class DataModel(BaseModel):
    title: str
    minutes: int

# 認証リクエストJSON構造
class AuthRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)

@app.post("/api/auth/register", status_code=201)
def register(data: AuthRequest):
    email = data.email.strip().lower()
    hashed = password_hash.hash(data.password)

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (email, password_hash)
                    VALUES (%s, %s)
                    RETURNING id, email
                    """,
                    (email, hashed),
                )
                user = cur.fetchone()

    except psycopg.errors.UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="このメールアドレスは登録済みです",
        )

    return {"id": user[0], "email": user[1]}

@app.post("/api/auth/login")
def login(data: AuthRequest):
    email = data.email.strip().lower()

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, password_hash
                FROM users
                WHERE email = %s
                """,
                (email,),
            )
            user = cur.fetchone()

    if user is None or not password_hash.verify(
        data.password, user[1]
    ):
        raise HTTPException(
            status_code=401,
            detail="メールアドレスまたはパスワードが正しくありません",
        )

    expires = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    token = jwt.encode(
        {"sub": str(user[0]), "exp": expires},
        SECRET_KEY,
        algorithm="HS256",
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"],
        )
        user_id = int(payload["sub"])

    except (InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="認証が必要です",
            headers={"WWW-Authenticate": "Bearer"},
        )

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email FROM users WHERE id = %s",
                (user_id,),
            )
            user = cur.fetchone()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="ユーザーが存在しません",
        )

    return {"id": user[0], "email": user[1]}

@app.get("/api/auth/me")
def get_me(
    current_user: dict = Depends(get_current_user),
):
    return current_user

@app.post("/api/sessions")
def create_session(
    data: DataModel,
    current_user: dict = Depends(get_current_user),
):
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sessions (title, minutes, user_id)
                VALUES (%s, %s, %s)
                RETURNING id, title, minutes, user_id
                """,
                (data.title, data.minutes, current_user["id"]),
            )
            row = cur.fetchone()

    return {
        "id": row[0],
        "title": row[1],
        "minutes": row[2],
        "user_id": row[3],
    }

@app.get("/api/sessions")
def get_sessions(
    current_user: dict = Depends(get_current_user),
):
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, minutes, created_at
                FROM sessions
                WHERE user_id = %s
                ORDER BY created_at DESC;
                """,
                (current_user["id"],)
            )
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "title": row[1],
            "minutes": row[2],
            "created_at": row[3],
        }
        for row in rows
    ]

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}