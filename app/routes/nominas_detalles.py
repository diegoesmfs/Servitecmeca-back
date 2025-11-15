# routes/nomina_detalle.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
import asyncpg
from typing import List, Optional
from app.schemas.nomina_detalle import NominaDetalleUpdate, NominaDetalleOut, NominaDetalleList
from app.controllers import nomina_detalle_controller
from app.db.connection import get_connection 

router = APIRouter(prefix="/nominas-detalles", tags=["Nóminas Detalles"])

# GET /nominas-detalles/{id}
@router.get("/{detalle_id}", response_model=NominaDetalleOut)
async def get_single_nomina_detalle(detalle_id: str, conn: asyncpg.Connection = Depends(get_connection)):
    """Obtiene los detalles de un pago individual por su ID."""
    detalle = await nomina_detalle_controller.get_nomina_detalle_by_id(conn, detalle_id)
    if not detalle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detalle de Nómina no encontrado")
    return detalle

# GET /nominas-detalles/nomina/{nomina_id}
@router.get("/nomina/{nomina_id}", response_model=NominaDetalleList)
async def list_detalles_by_nomina(nomina_id: str, conn: asyncpg.Connection = Depends(get_connection)):
    """Lista todos los detalles de pago de una nómina general específica."""
    detalles = await nomina_detalle_controller.list_nomina_detalles_by_nomina(conn, nomina_id)
    return NominaDetalleList(detalles=detalles, count=len(detalles))

# PUT /nominas-detalles/{id}
@router.put("/{detalle_id}", response_model=NominaDetalleOut)
async def update_existing_nomina_detalle(
    detalle_id: str, 
    detalle_update: NominaDetalleUpdate, 
    conn: asyncpg.Connection = Depends(get_connection)
):
    """Actualiza remuneraciones/deducciones de un detalle de pago existente."""
    try:
        detalle = await nomina_detalle_controller.update_nomina_detalle(conn, detalle_id, detalle_update)
        if not detalle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detalle de Nómina no encontrado")
        return detalle
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))