# routes/trabajador.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
import asyncpg
from typing import List, Optional
from app.schemas.trabajador import TrabajadorCreate, TrabajadorUpdate, TrabajadorOut
from app.controllers import trabajador_controller
# Asegúrate de que esta ruta sea correcta para tu proyecto:
from app.db.connection import get_connection 

router = APIRouter(prefix="/trabajadores", tags=["Trabajadores"])

# POST /trabajadores
@router.post("/", response_model=TrabajadorOut, status_code=status.HTTP_201_CREATED)
async def create_new_trabajador(trb_in: TrabajadorCreate, conn: asyncpg.Connection = Depends(get_connection)):
    """Crea un nuevo registro de trabajador."""
    try:
        trabajador = await trabajador_controller.create_trabajador(conn, trb_in)
        return trabajador
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {e}")

# GET /trabajadores (CON PAGINACIÓN Y FILTROS)
@router.get("/", response_model=List[TrabajadorOut])
async def list_all_trabajadores(
    conn: asyncpg.Connection = Depends(get_connection),
    skip: int = Query(0, ge=0, description="Número de registros a saltar (offset)."),
    limit: int = Query(100, gt=0, le=500, description="Máximo número de registros a retornar (limit)."),
    activo: Optional[bool] = Query(None, description="Filtrar por estado: True (activos=1), False (inactivos=0), None (todos)."),
    id_departamento: Optional[str] = Query(None, max_length=10, description="Filtrar por ID de Departamento.")
):
    """Obtiene la lista de trabajadores con opciones de paginación y filtros."""
    return await trabajador_controller.list_trabajadores(
        conn, skip=skip, limit=limit, activo=activo, id_departamento=id_departamento
    )

# GET /trabajadores/{id}
@router.get("/{trb_id}", response_model=TrabajadorOut)
async def get_single_trabajador(trb_id: int, conn: asyncpg.Connection = Depends(get_connection)):
    """Obtiene los detalles de un trabajador por su ID."""
    trabajador = await trabajador_controller.get_trabajador_by_id(conn, trb_id)
    if not trabajador:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trabajador no encontrado")
    return trabajador

# PUT /trabajadores/{id}
@router.put("/{trb_id}", response_model=TrabajadorOut)
async def update_existing_trabajador(
    trb_id: int, 
    trb_update: TrabajadorUpdate, 
    conn: asyncpg.Connection = Depends(get_connection)
):
    """Actualiza campos de un trabajador existente."""
    try:
        trabajador = await trabajador_controller.update_trabajador(conn, trb_id, trb_update)
        if not trabajador:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trabajador no encontrado")
        return trabajador
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {e}")

# DELETE /trabajadores/{id} (Eliminación Lógica)
@router.delete("/{trb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_trabajador(trb_id: int, conn: asyncpg.Connection = Depends(get_connection)):
    """Deshabilita lógicamente un trabajador (establece estado a 0)."""
    try:
        trabajador = await trabajador_controller.deactivate_trabajador(conn, trb_id)
        if not trabajador:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trabajador no encontrado")
        return
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al deshabilitar: {e}")