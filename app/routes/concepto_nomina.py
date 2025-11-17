# routes/concepto_nomina.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
import asyncpg
from typing import List
from app.schemas.concepto_nomina import ConceptoNominaCreate, ConceptoNominaUpdate, ConceptoNominaOut
from app.controllers import concepto_nomina_controller
from app.db.connection import get_connection 

router = APIRouter(prefix="/conceptos-nomina", tags=["Conceptos Nómina"])

# POST /conceptos-nomina
@router.post("/", response_model=ConceptoNominaOut, status_code=status.HTTP_201_CREATED)
async def create_new_concepto_nomina(concepto_in: ConceptoNominaCreate, conn: asyncpg.Connection = Depends(get_connection)):
    """
    Crea un nuevo concepto de nómina y actualiza automáticamente los totales 
    (remuneraciones/deducciones) y el salario neto en la tabla nomina_detalle.
    """
    try:
        concepto = await concepto_nomina_controller.create_concepto_nomina(conn, concepto_in)
        return concepto
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {e}")

# GET /conceptos-nomina/{id}
@router.get("/{concepto_id}", response_model=ConceptoNominaOut)
async def get_single_concepto_nomina(concepto_id: int, conn: asyncpg.Connection = Depends(get_connection)):
    """Obtiene los detalles de un concepto por su ID."""
    concepto = await concepto_nomina_controller.get_concepto_by_id(conn, concepto_id)
    if not concepto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concepto de Nómina no encontrado")
    return concepto

# GET /conceptos-nomina/detalle/{id_detalle}
@router.get("/detalle/{id_detalle}", response_model=List[ConceptoNominaOut])
async def list_conceptos_by_detalle(id_detalle: str, conn: asyncpg.Connection = Depends(get_connection)):
    """Lista todos los conceptos asociados a un ID de detalle de nómina."""
    return await concepto_nomina_controller.list_conceptos_by_detalle(conn, id_detalle)

# PUT /conceptos-nomina/{id}
@router.put("/{concepto_id}", response_model=ConceptoNominaOut)
async def update_existing_concepto_nomina(
    concepto_id: int, 
    concepto_update: ConceptoNominaUpdate, 
    conn: asyncpg.Connection = Depends(get_connection)
):
    """
    Actualiza un concepto de nómina, revirtiendo el impacto anterior y aplicando 
    el nuevo monto/tipo al detalle de nómina asociado.
    """
    try:
        concepto = await concepto_nomina_controller.update_concepto_nomina(conn, concepto_id, concepto_update)
        if not concepto:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concepto de Nómina no encontrado")
        return concepto
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

# NOTA: Se recomienda añadir un endpoint DELETE que también revierta el impacto en nomina_detalle.