from typing import List, Dict, Any
import asyncpg
from app.schemas.user import UserCreate
from app.core.security import get_password_hash


async def create_user(conn: asyncpg.Connection, user_in: UserCreate) -> Dict[str, Any]:
    hashed = get_password_hash(user_in.password)
    row = await conn.fetchrow(
        "INSERT INTO users (email, hashed_password) VALUES ($1, $2) RETURNING id, email, is_active, created_at",
        user_in.email,
        hashed,
    )
    return dict(row) if row else {}


async def list_users(conn: asyncpg.Connection) -> List[Dict[str, Any]]:
    rows = await conn.fetch("SELECT id, email, is_active, created_at FROM users ORDER BY id")
    return [dict(r) for r in rows]


async def get_user_by_email(conn: asyncpg.Connection, email: str):
    return await conn.fetchrow("SELECT id, email, hashed_password, is_active FROM users WHERE email = $1", email)
