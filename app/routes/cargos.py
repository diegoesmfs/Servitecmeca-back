from fastapi import APIRouter, Depends, HTTPException, status
from asyncpg import Connection
from app.schemas.cargos import CargoCreate, CargoOut, CargoUpdate
from app.controllers import cargos_controller as cargo_controller
# NOTA: Ajusta esta importación a donde tengas tu conexión
from app.db.connection import get_connection 
from typing import List

# Definimos el router
router = APIRouter(
    prefix="/cargos",
    tags=["Cargos"]
)

# ----------------------------------------------------------------------
# C R E A T E (POST /cargos)
# ----------------------------------------------------------------------
@router.post("/", response_model=CargoOut, status_code=status.HTTP_201_CREATED)
async def create_new_cargo(
    cargo_data: CargoCreate, 
    conn: Connection = Depends(get_connection)
):
    """
    Crea un nuevo cargo en el sistema.
    """
    return await cargo_controller.create_cargo(cargo_data, conn)

# ----------------------------------------------------------------------
# R E A D (Listar todos - GET /cargos)
# ----------------------------------------------------------------------
@router.get("/", response_model=List[CargoOut])
async def list_all_cargos(
    conn: Connection = Depends(get_connection)
):
    """
    Lista todos los cargos activos (estado = 1) del sistema.
    """
    return await cargo_controller.list_cargos(conn)

# ----------------------------------------------------------------------
# R E A D (Por ID - GET /cargos/{cargo_id})
# ----------------------------------------------------------------------
@router.get("/{cargo_id}", response_model=CargoOut)
async def read_cargo(
    cargo_id: str, 
    conn: Connection = Depends(get_connection)
):
    """
    Obtiene los detalles de un cargo específico usando su ID.
    """
    return await cargo_controller.get_cargo_by_id(cargo_id, conn)

# ----------------------------------------------------------------------
# U P D A T E (PUT /cargos/{cargo_id})
# ----------------------------------------------------------------------
@router.put("/{cargo_id}", response_model=CargoOut)
async def update_existing_cargo(
    cargo_id: str,
    cargo_data: CargoUpdate,
    conn: Connection = Depends(get_connection)
):
    """
    Actualiza la información de un cargo existente.
    """
    return await cargo_controller.update_cargo(cargo_id, cargo_data, conn)


# PARTIAL UPDATE (PATCH) - permite enviar solo los campos que quieras cambiar
@router.patch("/{cargo_id}", response_model=CargoOut)
async def patch_cargo(
    cargo_id: str,
    cargo_data: CargoUpdate,
    conn: Connection = Depends(get_connection)
):
    """
    Actualiza parcialmente un cargo: solo se aplican los campos enviados.
    """
    return await cargo_controller.update_cargo(cargo_id.upper(), cargo_data, conn)

# ----------------------------------------------------------------------
# D E L E T E (Desactivar - DELETE /cargos/{cargo_id})
# ----------------------------------------------------------------------
@router.patch("/{cargo_id}", response_model=dict)
async def disable_cargo(
    cargo_id: str, 
    conn: Connection = Depends(get_connection)
):
    """
    Desactiva un cargo (establece su estado a 0).
    """
    return await cargo_controller.delete_cargo(cargo_id, conn)