from fastapi import FastAPI

from app.routes import usuarios
from app.routes import trabajador
from app.routes import cargos
from app.routes import departamento

from fastapi import Depends
from app.utils.security import verify_token
from app.routes import auth



from dotenv import load_dotenv
from pathlib import Path
import os

# Cargar .env desde la carpeta app/
BASE_DIR = Path(__file__).resolve().parent  # Carpeta app/
load_dotenv(BASE_DIR / ".env")

# Verificar carga
print("✅ main.py - Variables cargadas:")
print(f"   DB_HOST: {os.getenv('DB_HOST')}")

app = FastAPI()
app.include_router(usuarios.router, prefix="/api", tags=["Usuarios"])
app.include_router(trabajador.router, prefix="/api", tags=["Trabajadores"])
app.include_router(cargos.router, prefix="/api", tags=["Cargos"])
app.include_router(departamento.router, prefix="/api", tags=["departamentos"])
app.include_router(auth.router, prefix="/auth", tags=["Autenticación"])

