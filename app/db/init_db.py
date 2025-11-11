async def create_tables(pool):
    """Ejemplo simple para crear la tabla users si no existe."""
    create_users = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
    );
    """
    async with pool.acquire() as conn:
        await conn.execute(create_users)
