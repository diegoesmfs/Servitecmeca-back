# routes/cargos.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
import asyncpg
from typing import List, Optional
from app.schemas.cargos import CargoCreate, CargoUpdate, CargoOut
# 🌟 Importando el controlador con el nombre corregido
from app.controllers import cargos_controller
# Supón que esta función existe:
from app.db.connection import get_connection 

router = APIRouter(prefix="/cargos", tags=["Cargos"])

# POST /cargos
@router.post("/", response_model=CargoOut, status_code=status.HTTP_201_CREATED)
async def create_new_cargo(cargo_in: CargoCreate, conn: asyncpg.Connection = Depends(get_connection)):
    """Crea un nuevo registro de cargo y retorna el objeto con el nombre del departamento."""
    try:
        cargo = await cargos_controller.create_cargo(conn, cargo_in)
        if not cargo:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo crear el cargo.")
        return cargo
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {e}")

# GET /cargos
@router.get("/", response_model=List[CargoOut])
async def list_all_cargos(
    conn: asyncpg.Connection = Depends(get_connection),
    skip: int = Query(0, ge=0, description="Offset."),
    limit: int = Query(100, gt=0, le=500, description="Limit."),
    activo: Optional[bool] = Query(None, description="Filtrar por estado."),
    id_departamento: Optional[str] = Query(None, max_length=10, description="Filtrar por ID de Departamento.")
):
    """Obtiene la lista de cargos con paginación y filtros, incluyendo el nombre del departamento."""
    return await cargos_controller.list_cargos(
        conn, skip=skip, limit=limit, activo=activo, id_departamento=id_departamento
    )

# 🌟 NUEVA RUTA: GET /cargos/departamento/{id_departamento}
@router.get("/departamento/{id_departamento}", response_model=List[CargoOut])
async def get_cargos_by_departamento_endpoint(
    id_departamento: str = Path(..., max_length=10, description="ID del Departamento para listar los cargos."),
    activo: Optional[bool] = Query(None, description="Filtrar por estado: True (activos=1), False (inactivos=0), None (todos)."),
    conn: asyncpg.Connection = Depends(get_connection)
):
    """
    Obtiene la lista de cargos (con el nombre del departamento) que pertenecen a un ID de departamento específico.
    """
    return await cargos_controller.get_cargos_by_departamento(
        conn, id_departamento=id_departamento, activo=activo
    )

# GET /cargos/{id}
@router.get("/{cargo_id}", response_model=CargoOut)
async def get_single_cargo(cargo_id: str, conn: asyncpg.Connection = Depends(get_connection)):
    """Obtiene los detalles de un cargo por su ID, incluyendo el nombre del departamento."""
    cargo = await cargos_controller.get_cargo_by_id(conn, cargo_id)
    if not cargo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cargo no encontrado")
    return cargo

# PUT /cargos/{id}
@router.put("/{cargo_id}", response_model=CargoOut)
async def update_existing_cargo(
    cargo_id: str, 
    cargo_update: CargoUpdate, 
    conn: asyncpg.Connection = Depends(get_connection)
):
    """Actualiza campos de un cargo existente y retorna el objeto completo."""
    try:
        cargo = await cargos_controller.update_cargo(conn, cargo_id, cargo_update)
        if not cargo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cargo no encontrado")
        return cargo
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {e}")

# PATCH /cargos/{id} (Eliminación Lógica)
@router.patch("/{cargo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_cargo_endpoint(cargo_id: str, conn: asyncpg.Connection = Depends(get_connection)):
    """Deshabilita lógicamente un cargo (establece estado a 0)."""
    try:
        cargo = await cargos_controller.deactivate_cargo(conn, cargo_id)
        if not cargo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cargo no encontrado")
        return
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al deshabilitar: {e}")