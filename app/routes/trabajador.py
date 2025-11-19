from fastapi import APIRouter, Depends, HTTPException, status, Query
# 🌟 Importaciones necesarias para PDF
from fastapi.responses import Response 
from app.controllers import pdf_controller 
from app.controllers.pdf_controller import PDFColumn 
# ------------------------------------
import asyncpg
from typing import List, Optional
from app.schemas.trabajador import TrabajadorCreate, TrabajadorUpdate, TrabajadorOut
from app.controllers import trabajador_controller
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

# 🌟🌟🌟 NUEVA RUTA: Generar PDF de Trabajadores 🌟🌟🌟
@router.get("/imprimir/pdf", response_class=Response)
async def get_trabajadores_pdf(
    conn: asyncpg.Connection = Depends(get_connection),
    activo: Optional[bool] = Query(None, description="Filtrar por estado."),
    id_departamento: Optional[str] = Query(None, description="Filtrar por ID de Departamento.")
):
    """
    Genera y devuelve un informe PDF con la lista de trabajadores, filtrada por estado y/o departamento.
    """
    try:
        # 1. Obtener la lista de trabajadores
        trabajadores = await trabajador_controller.list_trabajadores(
            conn, 
            skip=0, 
            limit=1000000, 
            activo=activo, 
            id_departamento=id_departamento
        )
        
        if not trabajadores:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron trabajadores con esos filtros.")

        # 2. Convertir los objetos a una lista de diccionarios
        data_to_print = [
            TrabajadorOut.model_validate(trb).model_dump(mode='json', by_alias=True) 
            for trb in trabajadores
        ]
        
        # 3. Definición de las columnas para el reporte (A3 Landscape = ~400mm de ancho útil)
        columns_definition = [
            PDFColumn(key='id_trabajador', header='ID', width=15, align='C'),
            PDFColumn(key='documento', header='Doc.', width=25, align='L'),
            PDFColumn(key='nombre', header='Nombre', width=20, align='L'),
            PDFColumn(key='apellido', header='Apellido', width=20, align='L'),
            PDFColumn(key='nombre_departamento', header='Departamento', width=25, align='L'),
            PDFColumn(key='titulo_cargo', header='Cargo', width=25, align='L'),
            PDFColumn(key='correo', header='Email', width=40, align='L'),
            PDFColumn(key='telefono', header='Teléfono', width=30, align='L'),
            PDFColumn(key='salario', header='Salario', width=30, align='R', 
                      formatter=lambda v: f"${v:,.2f}" if v is not None else '$0.00'), # Salario es Decimal
            PDFColumn(key='creado', header='F. Ingreso', width=25, align='C',
                      formatter=lambda v: str(v).split('T')[0] if v else 'N/A'), # Creado es date
            PDFColumn(key='estado', header='Est.', width=15, align='C',
                      formatter=lambda v: "ACTIVO" if v == 1 else "INACTIVO"),
        ]
        # Suma total de anchos: 15+25+40+40+45+35+50+30+30+25+15 = 350 mm. Cabe en A3 (420mm - márgenes)
        
        estado_texto = "ACTIVOS" if activo is True else "INACTIVOS" if activo is False else "TODOS"
        filter_texto = f" | Depto: {id_departamento}" if id_departamento else ""
        report_title = f"LISTADO DE TRABAJADORES ({estado_texto}{filter_texto})"

        # 4. Generar el contenido binario del PDF
        pdf_content = await pdf_controller.generate_generic_pdf(
            data=data_to_print, 
            columns=columns_definition,
            report_title=report_title
        )

        # 5. Devolver el PDF
        filename = "reporte_trabajadores.pdf"
        
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
@router.patch("/{trb_id}", status_code=status.HTTP_204_NO_CONTENT)
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