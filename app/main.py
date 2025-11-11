import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import users as users_router
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


# Routers
app.include_router(users_router.router, prefix="/api/v1/users", tags=["users"]) 


@app.get("/")
async def root():
    return {"message": "API (sin ORM) está corriendo"}
