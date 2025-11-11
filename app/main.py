# main.py (MODIFICADO para usar lifespan)

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import users as users_router
from app.routes import departamento as departamento_router
from app.db.connection import connect_to_db, disconnect_from_db # Mantener importaciones

# 🌟 1. DEFINIR EL GESTOR DE CONTEXTO ASÍNCRONO (LIFESPAN)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor de contexto para inicializar y apagar recursos.
    El código antes de 'yield' se ejecuta en el 'startup' (inicio).
    El código después de 'yield' se ejecuta en el 'shutdown' (apagado).
    """
    # 🌟 STARTUP (INICIO)
    print("Iniciando la conexión a la base de datos...")
    await connect_to_db(app)
    
    yield # Aquí se inicia la aplicación y maneja las peticiones

    # 🌟 SHUTDOWN (APAGADO)
    print("Cerrando la conexión a la base de datos...")
    await disconnect_from_db(app)
    

# 🌟 2. PASAR LIFESPAN AL CONSTRUCTOR DE FASTAPI
app = FastAPI(
    title=os.getenv("PROJECT_NAME", "Nuevo Backend"),
    lifespan=lifespan # <-- Usa el nuevo parámetro
)

# CORS (se mantiene igual)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers
app.include_router(users_router.router, prefix="/api/v1/users", tags=["users"]) 
app.include_router(departamento_router.router)


@app.get("/")
async def root():
    return {"message": "API (sin ORM) está corriendo"}