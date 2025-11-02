import psycopg2
from psycopg2.extras import RealDictCursor
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env desde la carpeta app/ (mismo nivel que database.py)
BASE_DIR = Path(__file__).resolve().parent  # Esto apunta a la carpeta app/
load_dotenv(BASE_DIR / ".env")

# Verificar que las variables se cargaron correctamente
print("🎯 Ruta del .env:", BASE_DIR / ".env")
print("🔍 Variables cargadas desde app/.env:")
print(f"   DB_HOST: {os.getenv('DB_HOST')}")
print(f"   DB_NAME: {os.getenv('DB_NAME')}")
print(f"   DB_USER: {os.getenv('DB_USER')}")
print(f"   DB_PORT: {os.getenv('DB_PORT')}")

def get_connection():
    # Verificar que todas las variables estén presentes
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Variables de entorno faltantes: {missing_vars}")
        return None

    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT"),
            cursor_factory=RealDictCursor
        )
        print("✅ Conexión exitosa a la base de datos")
        return conn
    except Exception as e:
        print("❌ Error al conectar a la base de datos:", e)
        return None