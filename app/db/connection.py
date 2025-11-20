import os
import asyncpg
from typing import Optional
from fastapi import FastAPI, Request
from dotenv import load_dotenv


DB_DSN = os.getenv("DATABASE_URL") 
async def connect_to_db(app: FastAPI):
    """Crea un pool de conexiones asyncpg y lo guarda en app.state.db_pool"""
    app.state.db_pool = await asyncpg.create_pool(dsn=DB_DSN)

async def disconnect_from_db(app: FastAPI):
    pool = getattr(app.state, "db_pool", None)
    if pool:
        await pool.close()


async def get_connection(request: Request):
    """Dependencia: adquiere una conexión del pool y la cede al endpoint."""
    pool: Optional[asyncpg.pool.Pool] = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise RuntimeError("Database pool is not initialized")
    async with pool.acquire() as conn:
        yield conn