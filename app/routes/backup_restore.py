# app/routes/backup_restore.py

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import Response
import asyncpg
from app.db.connection import get_connection 
from app.controllers import backup_restore_controller
from typing import Dict, Any
from datetime import datetime

router = APIRouter(prefix="/system", tags=["System & Data Management"])

# 1. RUTA DE BACKUP (GET)
@router.get("/backup", response_class=Response)
async def create_backup(conn: asyncpg.Connection = Depends(get_connection)):
    """
    Genera un archivo CSV con los datos de las tablas principales (departamento, cargos, 
    nomina_general, trabajador, usuario) para copia de seguridad.
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
                # Necesario para que el navegador pueda acceder al nombre del archivo
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar el archivo de copia de seguridad: {e}"
        )

# 2. RUTA DE RESTORE (POST)
@router.post("/restore/backups", status_code=status.HTTP_207_MULTI_STATUS)
async def restore_from_backup(
    file: UploadFile = File(...), 
    conn: asyncpg.Connection = Depends(get_connection)
) -> Dict[str, Any]:
    """
    Restaura los datos de un archivo CSV de copia de seguridad. 
    Inserta nuevas filas si no existen (por ID manual o clave única); salta si es duplicado.
    """
    if file.content_type not in ["text/csv", "application/vnd.ms-excel"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se aceptan archivos CSV."
        )

    try:
        csv_content = await file.read()
        
        # Inicia la restauración
        results = await conn.transaction(backup_restore_controller.restore_data_from_csv, csv_content)
        # conn.transaction asegura que si hay un error en cualquier tabla, se revierte todo (ROLLBACK)

        # Chequear si hubo errores de inserción
        if results.get("errors"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Hubo errores de validación de datos (Claves Foráneas, Tipos) durante la restauración.",
                headers={"X-Restore-Errors": "Ver cuerpo de respuesta para detalles."}
            )
        
        return results

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al procesar el archivo de restauración: {e}"
        )