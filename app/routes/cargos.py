from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
# 🌟 Importaciones para PDF
from fastapi.responses import Response
from app.controllers import pdf_controller 
from app.controllers.pdf_controller import PDFColumn 
# -------------------------
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

# 🌟🌟🌟 NUEVA RUTA: Generar PDF de Cargos 🌟🌟🌟
@router.get("/imprimir/pdf", response_class=Response)
async def get_cargos_pdf(
    conn: asyncpg.Connection = Depends(get_connection),
    activo: Optional[bool] = Query(None, description="Filtrar por estado."),
    id_departamento: Optional[str] = Query(None, description="Filtrar por ID de Departamento.")
):
    """
    Genera y devuelve un informe PDF con la lista de cargos, filtrada por estado y/o departamento.
    """
    try:
        # 1. Obtener la lista de cargos
        cargos = await cargos_controller.list_cargos(
            conn, 
            skip=0, 
            limit=1000000, 
            activo=activo, 
            id_departamento=id_departamento
        )
        
        if not cargos:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron cargos con esos filtros.")

        # 2. Convertir los objetos a una lista de diccionarios
        data_to_print = [
            CargoOut.model_validate(cargo).model_dump(mode='json', by_alias=True) 
            for cargo in cargos
        ]
        
        # 3. Definición de las columnas para el reporte (A3 Landscape = ~400mm de ancho útil)
        columns_definition = [
            PDFColumn(key='id_cargo', header='ID Cargo', width=20, align='C'),
            PDFColumn(key='titulo', header='Título del Cargo', width=40, align='L'),
            PDFColumn(key='nombre_departamento', header='Departamento', width=40, align='L'),
            PDFColumn(key='nivel', header='Nivel', width=15, align='C'),
            PDFColumn(key='salario_base', header='Salario Base', width=30, align='R', 
                      formatter=lambda v: f"${v:,.2f}" if v is not None else '$0.00'),
            PDFColumn(key='salario_maximo', header='Salario Máx.', width=30, align='R', 
                      formatter=lambda v: f"${v:,.2f}" if v is not None else '$0.00'),
            PDFColumn(key='competencias', header='Competencias', width=100, align='L', 
                      formatter=lambda v: (v[:40] + '...') if v and len(v) > 40 else str(v)), # Truncar la descripción si es muy larga
            PDFColumn(key='creado', header='F. Creación', width=30, align='C',
                      formatter=lambda v: str(v).split('T')[0] if v else 'N/A'),
            PDFColumn(key='estado', header='Estado.', width=25, align='C',
                      formatter=lambda v: "ACTIVO" if v == 1 else "INACTIVO"),
        ]
        # Suma total de anchos: 20+60+60+15+35+35+100+35+15 = 375 mm. Cabe en A3 (420mm - márgenes)
        
        estado_texto = "ACTIVOS" if activo is True else "INACTIVOS" if activo is False else "TODOS"
        filter_texto = f" | Depto: {id_departamento}" if id_departamento else ""
        report_title = f"LISTADO DE CARGOS ({estado_texto}{filter_texto})"

        # 4. Generar el contenido binario del PDF
        pdf_content = await pdf_controller.generate_generic_pdf(
            data=data_to_print, 
            columns=columns_definition,
            report_title=report_title
        )

        # 5. Devolver el PDF
        filename = "reporte_cargos.pdf"
        
        return Response(
            content=pdf_content, 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error al generar el PDF: {e}"
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