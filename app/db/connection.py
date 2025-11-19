import os
import asyncpg
from typing import Optional
from fastapi import FastAPI, Request
# NO necesitamos load_dotenv() aquí porque Railway inyecta las variables

# 1. Obtener la URL de conexión del ENTORNO.
# Si está en Railway, esta será la URL de la red privada.
# Si está localmente, usará el valor 'postgresql://postgres:2005@localhost:5432/nominas'
# que es el valor que tienes actualmente en tu .env local.
# app/db/connection.py
DB_DSN = os.getenv("DATABASE_URL") 

if not DB_DSN:
    # Esto forzará un error si la variable no existe, 
    # para que sepas que Railway no la está inyectando.
    raise EnvironmentError("La variable de entorno DATABASE_URL no está configurada.")

# El resto del código se queda igual...
async def connect_to_db(app: FastAPI):
    """Crea un pool de conexiones asyncpg y lo guarda en app.state.db_pool"""
    print(f"Conectando a la base de datos con DSN: {DB_DSN.split('@')[-1]}")
    try:
        # asyncpg.create_pool lee el DSN y establece la conexión
        app.state.db_pool = await asyncpg.create_pool(dsn=DB_DSN)
        print("Conexión a la base de datos establecida con éxito.")
    except Exception as e:
        print(f"ERROR: Fallo al conectar con la base de datos. Detalle: {e}")
        # En caso de fallo, la aplicación fallará al inicio (lo cual es correcto)
        raise

async def disconnect_from_db(app: FastAPI):
    pool = getattr(app.state, "db_pool", None)
    if pool:
        await pool.close()


async def get_connection(request: Request):
    """Dependencia: adquiere una conexión del pool y la cede al endpoint."""
    pool: Optional[asyncpg.pool.Pool] = getattr(request.app.state, "db_pool", None)
    if pool is None:
        # Esto no debería pasar si la conexión en lifespan fue exitosa
        raise RuntimeError("El pool de la base de datos no está inicializado.")
    async with pool.acquire() as conn:
        yield conn