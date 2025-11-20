from fastapi import APIRouter, Depends, HTTPException, status, Query
# 🌟 Importaciones para PDF
from fastapi.responses import Response
from app.controllers import pdf_controller 
from app.controllers.pdf_controller import PDFColumn 
# -------------------------
import asyncpg
from typing import List, Optional
from app.schemas.nomina_general import NominaGeneralCreate, NominaGeneralUpdate, NominaGeneralOut
from app.schemas.nomina_detalle import NominaDetalleOut # Necesaria para la ruta detallada
from app.controllers import nomina_general_controller
from app.controllers import nomina_detalle_controller # Necesaria para la ruta detallada
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

# 🌟🌟🌟 RUTA PDF 1: LISTADO DE NÓMINAS GENERALES 🌟🌟🌟
@router.get("/imprimir/pdf", response_class=Response)
async def get_nominas_generales_pdf(
    conn: asyncpg.Connection = Depends(get_connection),
    id_departamento: Optional[str] = Query(None, description="Filtrar por ID de Departamento."),
    estado_pago: Optional[int] = Query(None, ge=0, le=3, description="Filtrar por estado de pago.")
):
    """
    Genera y devuelve un informe PDF con el listado de todas las Nóminas Generales.
    """
    try:
        nominas = await nomina_general_controller.list_nominas_generales(
            conn, 
            skip=0, 
            limit=1000000, 
            id_departamento=id_departamento, 
            estado_pago=estado_pago
        )
        
        if not nominas:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron nóminas generales con esos filtros.")

        data_to_print = [
            NominaGeneralOut.model_validate(n).model_dump(mode='json', by_alias=True) 
            for n in nominas
        ]
        
        # Definición de las columnas para A3 Landscape (~400mm de ancho)
        columns_definition = [
            PDFColumn(key='id_nomina', header='ID Nómina', width=35, align='C'),
            PDFColumn(key='periodo', header='Período', width=30, align='C',
                      formatter=lambda v: str(v).split('T')[0] if v else 'N/A'),
            PDFColumn(key='nombre_departamento', header='Departamento', width=60, align='L'),
            PDFColumn(key='fecha_pago', header='F. Pago', width=30, align='C',
                      formatter=lambda v: str(v).split('T')[0] if v else 'N/A'),
            PDFColumn(key='presupuesto_utilizado', header='Presupuesto Utilizado', width=45, align='R', 
                      formatter=lambda v: f"${float(v):,.2f}"),
            PDFColumn(key='impuesto_renta_total', header='Impuesto Renta', width=35, align='R', 
                      formatter=lambda v: f"${float(v):,.2f}"),
            PDFColumn(key='seguro_social_total', header='Seguro Social', width=35, align='R', 
                      formatter=lambda v: f"${float(v):,.2f}"),
            PDFColumn(key='estado_pago', header='Est. Pago', width=30, align='C',
                      formatter=lambda v: ["PENDIENTE", "PARCIAL", "PAGADO", "ANULADO"][v]), # Asumiendo 0-3
            PDFColumn(key='estado', header='Est.', width=15, align='C',
                      formatter=lambda v: "ACTIVO" if v == 1 else "INACTIVO"),
        ]
        # Suma de anchos: 35+30+60+30+45+35+35+30+15 = 315 mm. OK para A3.
        
        estado_texto = ["PENDIENTE", "PARCIAL", "PAGADO", "ANULADO"][estado_pago] if estado_pago is not None else "TODAS"
        report_title = f"REPORTE DE NÓMINAS GENERALES ({estado_texto})"

        pdf_content = await pdf_controller.generate_generic_pdf(
            data=data_to_print, 
            columns=columns_definition,
            report_title=report_title
        )
        
        return Response(content=pdf_content, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=reporte_nominas_generales.pdf"})
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al generar el PDF: {e}")


# 🌟🌟🌟 RUTA PDF 2: NÓMINA GENERAL DETALLADA POR ID 🌟🌟🌟
@router.get("/{nomina_id}/imprimir/pdf", response_class=Response)
async def get_single_nomina_detailed_pdf(nomina_id: str, conn: asyncpg.Connection = Depends(get_connection)):
    """
    Genera un informe PDF detallado para una Nómina General específica, incluyendo
    una tabla con todos sus detalles de nómina (pagos individuales a trabajadores).
    """
    try:
        # 1. Obtener la Nómina General (Header data)
        nomina_general = await nomina_general_controller.get_nomina_general_by_id(conn, nomina_id)
        if not nomina_general:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nómina General no encontrada")

        # 2. Obtener los Detalles de Nómina (Table data)
        detalles_nomina = await nomina_detalle_controller.list_nomina_detalles_by_nomina(conn, nomina_id)
        
        if not detalles_nomina:
             # Se podría generar el PDF solo con el encabezado, pero si no hay detalles, algo puede estar mal.
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron detalles de nómina para esta Nómina General.")


        # 3. Serializar a diccionarios
        nomina_general_data = NominaGeneralOut.model_validate(nomina_general).model_dump(mode='json', by_alias=True)
        detalles_data = [
            NominaDetalleOut.model_validate(d).model_dump(mode='json', by_alias=True) 
            for d in detalles_nomina
        ]

        # 4. Generar el PDF detallado (Usando la nueva función en el controller)
        pdf_content = await pdf_controller.generate_nomina_detailed_report(
            nomina_general_data=nomina_general_data, 
            detalles_data=detalles_data
        )

        filename = f"nomina_detalle_{nomina_id}.pdf"
        
        return Response(content=pdf_content, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al generar el PDF: {e}")


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