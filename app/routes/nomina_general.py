# routes/nomina_general.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
import asyncpg
from typing import List, Optional
from app.schemas.nomina_general import NominaGeneralCreate, NominaGeneralUpdate, NominaGeneralOut
from app.controllers import nomina_general_controller
from app.db.connection import get_connection 

router = APIRouter(prefix="/nominas-generales", tags=["Nóminas Generales"])

# POST /nominas-generales
@router.post("/", response_model=NominaGeneralOut, status_code=status.HTTP_201_CREATED)
async def create_new_nomina_general(nomina_in: NominaGeneralCreate, conn: asyncpg.Connection = Depends(get_connection)):
    """
    Crea un nuevo registro de nómina general y, automáticamente, 
    todos los detalles de nómina para los trabajadores activos del departamento.
    """
    try:
        nomina = await nomina_general_controller.create_nomina_general(conn, nomina_in)
        return nomina
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {e}")

# GET /nominas-generales (CON PAGINACIÓN Y FILTROS)
@router.get("/", response_model=List[NominaGeneralOut])
async def list_all_nominas_generales(
    conn: asyncpg.Connection = Depends(get_connection),
    skip: int = Query(0, ge=0, description="Número de registros a saltar (offset)."),
    limit: int = Query(100, gt=0, le=500, description="Máximo número de registros a retornar (limit)."),
    id_departamento: Optional[str] = Query(None, max_length=10, description="Filtrar por ID de Departamento."),
    estado_pago: Optional[int] = Query(None, ge=0, le=3, description="Filtrar por estado de pago.")
):
    """
    Obtiene la lista de nóminas generales con opciones de paginación y filtro.
    """
    return await nomina_general_controller.list_nominas_generales(
        conn, 
        skip=skip, 
        limit=limit, 
        id_departamento=id_departamento, 
        estado_pago=estado_pago
    )

# GET /nominas-generales/{id}
@router.get("/{nomina_id}", response_model=NominaGeneralOut)
async def get_single_nomina_general(nomina_id: str, conn: asyncpg.Connection = Depends(get_connection)):
    """Obtiene los detalles de una nómina general por su ID."""
    nomina = await nomina_general_controller.get_nomina_general_by_id(conn, nomina_id)
    if not nomina:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nómina General no encontrada")
    return nomina

# PUT /nominas-generales/{id}
@router.put("/{nomina_id}", response_model=NominaGeneralOut)
async def update_existing_nomina_general(
    nomina_id: str, 
    nomina_update: NominaGeneralUpdate, 
    conn: asyncpg.Connection = Depends(get_connection)
):
    """Actualiza campos de un registro de nómina general existente."""
    try:
        nomina = await nomina_general_controller.update_nomina_general(conn, nomina_id, nomina_update)
        if not nomina:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nómina General no encontrada")
        return nomina
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

# PATCH /nominas-generales/{id}/estado (Deshabilita Lógicamente)
@router.patch("/{nomina_id}/estado", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_nomina_general(nomina_id: str, conn: asyncpg.Connection = Depends(get_connection)):
    """Deshabilita lógicamente un registro de nómina general (establece estado a 0)."""
    deactivate_data = NominaGeneralUpdate(estado=0)
    
    try:
        nomina = await nomina_general_controller.update_nomina_general(conn, nomina_id, deactivate_data)
        if not nomina:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nómina General no encontrada")
        return
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al deshabilitar: {e}")