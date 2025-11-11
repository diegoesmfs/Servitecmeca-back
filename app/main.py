import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import users as users_router
# EJEMPLO: En tu main.py o app.py
from fastapi import FastAPI
from app.routes import cargo # Asegúrate de que esta ruta sea correcta

app = FastAPI()

# Esto registra las rutas de /cargos
app.include_router(cargo.router)
from app.db.connection import connect_to_db, disconnect_from_db


app = FastAPI(title=os.getenv("PROJECT_NAME", "Nuevo Backend"))

# CORS (ajusta orígenes en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await connect_to_db(app)

@app.on_event("shutdown")
async def shutdown_event():
    await disconnect_from_db(app)

# Routers
app.include_router(users_router.router, prefix="/api/v1/users", tags=["users"]) 
app.include_router(cargo.router, prefix="/api/v1/cargos", tags=["cargos"])


@app.get("/")
async def root():
    return {"message": "API (sin ORM) está corriendo"}
