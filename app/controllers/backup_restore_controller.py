# app/controllers/backup_restore_controller.py

from typing import List, Dict, Any, Tuple
import asyncpg
import io
import csv
from datetime import datetime

# Definición de las tablas y sus IDs
# is_manual: True -> El ID viene en el CSV y debe usarse para ON CONFLICT.
# is_manual: False -> El ID es SERIAL y debe ser omitido en el INSERT, el conflicto se basa en 'documento' o 'correo'.
TABLE_CONFIG = {
    "departamento": {"id_column": "id_departamento", "is_manual": True},
    "cargos": {"id_column": "id_cargo", "is_manual": True},
    "nomina_general": {"id_column": "id_nomina", "is_manual": True},
    "trabajador": {"id_column": "id_trabajador", "is_manual": False, "conflict_target": "documento"},
    "usuario": {"id_column": "id_usuario", "is_manual": False, "conflict_target": "documento"},
    # Omitimos detalle y concepto por ahora para simplificar el backup base
}

# La lista debe estar en el orden de las dependencias FK
TABLES_ORDER = ["departamento", "cargos", "nomina_general", "trabajador", "usuario"]


# ======================================================================
## 1. Función de Backup (Exportación a CSV)
# ======================================================================

async def generate_backup_csv(conn: asyncpg.Connection) -> bytes:
    """
    Exporta los datos de las tablas configuradas a un único archivo CSV.
    Cada tabla se separa por una línea de metadatos.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([f"## BACKUP_CREATED: {datetime.now().isoformat()} ##"])

    for table_name in TABLES_ORDER:
        # 1. Traer todos los datos de la tabla
        config = TABLE_CONFIG[table_name]
        query = f"SELECT * FROM {table_name} ORDER BY {config['id_column']};"
        rows = await conn.fetch(query)

        # 2. Escribir el encabezado de la sección
        writer.writerow([f"## TABLE_START: {table_name} ##"])
        
        if not rows:
            continue

        # 3. Escribir los nombres de las columnas
        columns = list(rows[0].keys())
        writer.writerow(columns)
        
        # 4. Escribir las filas de datos
        for row in rows:
            # Convertir todos los valores a cadenas para CSV
            writer.writerow([str(row[col]) for col in columns])

    # Devolver el contenido como bytes codificado en UTF-8
    return output.getvalue().encode('utf-8')


# ======================================================================
## 2. Función de Restore (Importación desde CSV)
# ======================================================================

async def restore_data_from_csv(conn: asyncpg.Connection, csv_content: bytes) -> Dict[str, Any]:
    """
    Lee el contenido CSV y restaura los datos en las tablas, omitiendo duplicados.
    """
    results = {"restored": {}, "errors": {}}
    
    # 1. Decodificar y configurar el lector CSV
    content = csv_content.decode('utf-8')
    reader = csv.reader(io.StringIO(content))
    
    current_table = None
    columns = []
    
    # 2. Iterar sobre las filas
    for row in reader:
        if not row:
            continue
            
        # Detección del inicio de una nueva tabla
        if row[0].startswith("## TABLE_START: "):
            current_table = row[0].split(": ")[1].split(" ##")[0]
            columns = []
            results["restored"][current_table] = {"success_count": 0, "skipped_duplicates": 0, "total_rows": 0}
            continue

        if current_table and not columns and row[0] != f"## TABLE_START: {current_table} ##":
            # La siguiente fila después de TABLE_START es la de las columnas
            columns = row
            continue
            
        if current_table and columns:
            # Procesar fila de datos
            if current_table not in TABLE_CONFIG: continue

            results["restored"][current_table]["total_rows"] += 1
            
            record_data = dict(zip(columns, row))
            config = TABLE_CONFIG[current_table]
            
            insert_cols = []
            insert_values = []
            
            # --- Preparación de Columnas y Valores ---
            for col, value in record_data.items():
                # Omitir la columna de ID si es SERIAL (automática)
                if col == config["id_column"] and not config["is_manual"]:
                    continue 

                # Reemplazar valores vacíos/None con None (para NULL en DB)
                final_value = None if value in ('None', 'NULL', '') else value
                
                insert_cols.append(col)
                insert_values.append(final_value)
            
            # --- Construcción de la consulta INSERT ON CONFLICT ---
            cols_sql = ", ".join(insert_cols)
            params_sql = ", ".join([f"${i+1}" for i in range(len(insert_values))])

            # Determinar el objetivo del conflicto: ID manual o columna única (documento/correo)
            if config["is_manual"]:
                 # Usa el ID manual como objetivo de conflicto
                 conflict_target = config["id_column"]
            else:
                 # Usa la columna única definida en la configuración (documento)
                 conflict_target = config["conflict_target"]
            
            query = f"""
            INSERT INTO {current_table} ({cols_sql}) 
            VALUES ({params_sql})
            ON CONFLICT ({conflict_target}) 
            DO NOTHING;
            """
            
            try:
                # Ejecutar la consulta
                status = await conn.execute(query, *insert_values)
                
                if status.endswith(" 1"):
                    results["restored"][current_table]["success_count"] += 1
                else:
                    results["restored"][current_table]["skipped_duplicates"] += 1
                    
            except Exception as e:
                # Loggear errores detallados
                error_key = f"{current_table}_error"
                if error_key not in results["errors"]:
                    results["errors"][error_key] = []
                results["errors"][error_key].append({
                    "data": record_data, 
                    "error": str(e)
                })

    return results