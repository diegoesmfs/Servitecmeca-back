# main.py (MODIFICADO para usar lifespan)

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import departamento as departamento_router
from app.routes import trabajador as Trabajador_router
from app.routes import usuario as Usuario_router
from app.routes import nomina_general as NominaGeneral_router
from app.routes import nominas_detalles as NominaDetalle_router   
from app.routes import cargos as Cargos_router
from app.routes import concepto_nomina as ConceptoNomina_router
from app.routes import dashboard as Dashboard_router  
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
    # 🚨 CAMBIAR ESTA LÍNEA 🚨
    # El asterisco "*" permite todos los dominios.
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "Set-Cookie"],
)



app.include_router(departamento_router.router, prefix="/api/v1", tags=["Departamentos"])
app.include_router(Cargos_router.router, prefix="/api/v1", tags=["Cargos"]) 
app.include_router(Trabajador_router.router, prefix="/api/v1", tags=["Trabajadores"])
app.include_router(Usuario_router.router, prefix="/api/v1", tags=["Usuarios"])    
app.include_router(NominaGeneral_router.router, prefix="/api/v1", tags=["Nóminas Generales"])
app.include_router(NominaDetalle_router.router, prefix="/api/v1", tags=["Nóminas Detalles"]) 
app.include_router(ConceptoNomina_router.router, prefix="/api/v1", tags=["Conceptos Nómina"])   
app.include_router(Dashboard_router.router, prefix="/api/v1", tags=["Dashboard"]) 


