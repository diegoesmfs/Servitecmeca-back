from fastapi import APIRouter, Depends, HTTPException, status, Query
# 🌟 Importación corregida: Usamos Response para el retorno de bytes
from fastapi.responses import Response 
import asyncpg
from typing import List, Optional
from app.schemas.departamento import DepartamentoCreate, DepartamentoUpdate, DepartamentoOut
from app.controllers import departamento_controller
from app.controllers import trabajador_controller
from app.controllers import pdf_controller 
from app.controllers.pdf_controller import PDFColumn 
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


# 🌟🌟🌟 RUTA PDF REUBICADA PARA EVITAR CONFLICTO CON /{dep_id} 🌟🌟🌟
@router.get("/imprimir/pdf", response_class=Response) # Usamos Response
async def get_departamentos_pdf(
    conn: asyncpg.Connection = Depends(get_connection),
    activo: Optional[bool] = Query(None, description="Filtrar por estado: True (activos=1), False (inactivos=0), None (todos).")
):
    """
    Genera y devuelve un informe PDF con la lista de departamentos filtrada por estado.
    """
    try:
        # 1. Obtener la lista de departamentos (Objetos Departamento)
        departamentos = await departamento_controller.list_departamentos(
            conn, 
            skip=0, 
            limit=1000000, 
            activo=activo
        )
        
        if not departamentos:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron departamentos.")

        # 2. Convertir los objetos a una lista de diccionarios
        data_to_print = [
            DepartamentoOut.model_validate(dep).model_dump(mode='json') 
            for dep in departamentos
        ]
        
        # 3. Definición de las columnas para el reporte
        columns_definition = [
            PDFColumn(key='id_departamento', header='ID', width=15, align='C'), 
            PDFColumn(key='nombre', header='Departamento', width=30, align='L'), 
            PDFColumn(key='nombre_jefe_departamento', header='Jefe', width=30, align='L'), 
            # 🌟 CAMPO 'email'
            PDFColumn(key='email', header='Email', width=45, align='L'),
            PDFColumn(key='presupuesto_anual', header='Presupuesto', width=20, align='R', 
                      formatter=lambda v: f"${float(v):,.2f}" if v is not None else '$0.00'), 
            # 🌟 CAMPO 'capacidad_empleados'
            PDFColumn(key='capacidad_empleados', header='Capacidad', width=20, align='C'),
            # 🌟 CAMPO 'ubicacion'
            PDFColumn(key='ubicacion', header='Ubicación', width=25, align='L'),
            # 🌟 CAMPO 'creado'
            PDFColumn(key='creado', header='F. Creación', width=25, align='C',
                      formatter=lambda v: v.split('T')[0] if isinstance(v, str) else 'N/A'),
            PDFColumn(key='estado', header='Estado', width=15, align='C',
                      formatter=lambda v: "ACTIVO" if v == 1 else "INACTIVO"),
        ]
        
        estado_texto = "ACTIVOS" if activo is True else "INACTIVOS" if activo is False else "TODOS"
        report_title = f"LISTADO DE DEPARTAMENTOS ({estado_texto})"

        # 4. Generar el contenido binario del PDF usando la función reutilizable
        pdf_content = await pdf_controller.generate_generic_pdf(
            data=data_to_print, 
            columns=columns_definition,
            report_title=report_title
        )

        # 5. Devolver el PDF
        filename = "reporte_departamentos.pdf"
        
        # 🌟 RETORNO CORREGIDO: Usamos Response para enviar los bytes directamente
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

# patch /departamentos/{id} (Eliminación Lógica)
@router.patch("/{dep_id}", status_code=status.HTTP_204_NO_CONTENT)
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


# GET /departamentos/{id}/trabajadores/count
@router.get("/{dep_id}/trabajadores/count")
async def count_trabajadores(
    dep_id: str,
    conn: asyncpg.Connection = Depends(get_connection),
    include_inactivos: bool = Query(False, description="Si True incluye trabajadores inactivos; por defecto False cuenta solo activos")
):
    """Devuelve la cantidad de trabajadores en el departamento."""
    activo = None if include_inactivos else True
    try:
        # Aquí debería ir la lógica para contar trabajadores.
        return {"id_departamento": dep_id, "total_trabajadores": 0} 
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al contar trabajadores: {e}")