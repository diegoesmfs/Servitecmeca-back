from fastapi import FastAPI
from app.routes import usuarios
from app.routes import trabajador
from app.routes import cargos
from app.routes import departamento
from app.routes import contratos


from dotenv import load_dotenv
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent 
load_dotenv(BASE_DIR / ".env")

# Verificar carga
print("✅ main.py - Variables cargadas:")
print(f"   DB_HOST: {os.getenv('DB_HOST')}")

app = FastAPI()
app.include_router(usuarios.router, prefix="/api", tags=["Usuarios"])
app.include_router(trabajador.router, prefix="/api", tags=["Trabajadores"])
app.include_router(cargos.router, prefix="/api", tags=["Cargos"])
app.include_router(departamento.router, prefix="/api", tags=["departamentos"])
app.include_router(contratos.router, prefix="/api", tags=["Contratos"])

