# app/routes/backup_restore.py

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import Response, JSONResponse
import asyncpg
# Asegúrate de tener la conexión correcta
from app.db.connection import get_connection 
from app.controllers import backup_restore_controller
from typing import Dict, Any
from datetime import datetime

router = APIRouter(prefix="/system", tags=["System & Data Management"])

# 1. RUTA DE BACKUP (GET)
@router.get("/backup", response_class=Response)
async def create_backup(conn: asyncpg.Connection = Depends(get_connection)):
    """
    Genera un archivo CSV con los datos de las tablas principales para copia de seguridad.
    """
    try:
        csv_content = await backup_restore_controller.generate_backup_csv(conn)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_nomina_{timestamp}.csv"
        
        return Response(
            content=csv_content, 
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar el archivo de copia de seguridad: {e}"
        )

# 2. RUTA DE RESTORE (POST) - ¡SOLUCIÓN FINAL: SIN TRANSACCIÓN ATÓMICA!
@router.post("/restore/backups", status_code=status.HTTP_207_MULTI_STATUS)
async def restore_from_backup(
    file: UploadFile = File(...), 
    conn: asyncpg.Connection = Depends(get_connection)
) -> Dict[str, Any]:
    """
    Restaura los datos de un archivo CSV de copia de seguridad. 
    Permite que la restauración continúe aunque fallen filas individuales.
    """
    if file.content_type not in ["text/csv", "application/vnd.ms-excel"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se aceptan archivos CSV."
        )

    try:
        csv_content = await file.read()
        
        # ❌ BLOQUE 'async with conn.transaction():' ELIMINADO.
        # Esto permite que la restauración continúe si una sola fila falla (ON CONFLICT).
        results = await backup_restore_controller.restore_data_from_csv(conn, csv_content)
        
        if results.get("errors"):
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "detail": "Hubo errores de validación (Claves Foráneas/Tipos) durante la restauración, pero se restauró la data válida. Revise el campo 'results' para más detalles.",
                    "results": results 
                }
            )
        
        return results

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al procesar el archivo de restauración: {e}"
        )