# routes/departamento.py (FINAL)
from fastapi import APIRouter, Depends, HTTPException, status, Query
import asyncpg
from typing import List, Optional
from app.schemas.departamento import DepartamentoCreate, DepartamentoUpdate, DepartamentoOut
from app.controllers import departamento_controller
# Asegúrate de que esta ruta sea correcta para tu proyecto:
from app.db.connection import get_connection 

router = APIRouter(prefix="/departamentos", tags=["Departamentos"])

# POST /departamentos
@router.post("/", response_model=DepartamentoOut, status_code=status.HTTP_201_CREATED)
async def create_new_departamento(dep_in: DepartamentoCreate, conn: asyncpg.Connection = Depends(get_connection)):
    """Crea un nuevo departamento."""
    try:
        departamento = await departamento_controller.create_departamento(conn, dep_in)
        return departamento
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {e}")

# GET /departamentos (CON PAGINACIÓN)
@router.get("/", response_model=List[DepartamentoOut])
async def list_all_departamentos(
    conn: asyncpg.Connection = Depends(get_connection),
    skip: int = Query(0, ge=0, description="Número de registros a saltar (offset)."),
    limit: int = Query(100, gt=0, le=500, description="Máximo número de registros a retornar (limit)."),
    activo: Optional[bool] = Query(None, description="Filtrar por estado: True (activos=1), False (inactivos=0), None (todos).")
):
    """
    Obtiene la lista de departamentos con opciones de paginación y filtro por estado.
    """
    return await departamento_controller.list_departamentos(conn, skip=skip, limit=limit, activo=activo)

# GET /departamentos/{id}
@router.get("/{dep_id}", response_model=DepartamentoOut)
async def get_single_departamento(dep_id: str, conn: asyncpg.Connection = Depends(get_connection)):
    """Obtiene los detalles de un departamento por su ID."""
    departamento = await departamento_controller.get_departamento_by_id(conn, dep_id)
    if not departamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Departamento no encontrado")
    return departamento

# PUT /departamentos/{id}
@router.put("/{dep_id}", response_model=DepartamentoOut)
async def update_existing_departamento(
    dep_id: str, 
    dep_update: DepartamentoUpdate, 
    conn: asyncpg.Connection = Depends(get_connection)
):
    """Actualiza campos de un departamento existente."""
    try:
        departamento = await departamento_controller.update_departamento(conn, dep_id, dep_update)
        if not departamento:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Departamento no encontrado")
        return departamento
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

# DELETE /departamentos/{id} (Eliminación Lógica)
@router.delete("/{dep_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_departamento(dep_id: str, conn: asyncpg.Connection = Depends(get_connection)):
    """Deshabilita lógicamente un departamento (establece estado a 0)."""
    deactivate_data = DepartamentoUpdate(estado=0)
    
    try:
        departamento = await departamento_controller.update_departamento(conn, dep_id, deactivate_data)
        if not departamento:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Departamento no encontrado")
        return
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al deshabilitar: {e}")