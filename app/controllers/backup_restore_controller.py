# app/controllers/backup_restore_controller.py

import asyncpg
import io
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from fastapi import HTTPException # Solo si se usa en otras partes, pero es buena práctica mantenerla.

# ======================================================================
# CONFIGURACIÓN DE TABLAS
# ======================================================================

TABLE_CONFIG = {
    # is_manual: True -> IDs que NO son SERIAL.
    # forward_fk: Columna que referencia un ID SERIAL (trabajador) y se actualiza después.
    "departamento": {"id_column": "id_departamento", "is_manual": True, "forward_fk": "jefe_departamento"},
    "cargos": {"id_column": "id_cargo", "is_manual": True},
    "nomina_general": {"id_column": "id_nomina", "is_manual": True},
    "trabajador": {"id_column": "id_trabajador", "is_manual": False, "conflict_target": "documento"},
    "usuario": {"id_column": "id_usuario", "is_manual": False, "conflict_target": "documento", "forward_fk": "id_trabajador"},
}

# ORDEN CRUCIAL DE RESTAURACIÓN
TABLES_ORDER = ["departamento", "cargos", "nomina_general", "trabajador", "usuario"]

# 🟢 MAPA DE TIPOS: Define la función de conversión para cada columna
TYPE_MAP = {
    # Enteros
    "capacidad_empleados": int, "nivel": int, "estado": int, "estado_pago": int, 
    "tipo_contrato": int, "id_trabajador": int, "jefe_departamento": int, "id_usuario": int,
    
    # Flotantes
    "presupuesto_anual": float, "salario_base": float, "salario_maximo": float, 
    "presupuesto_utilizado": float, "impuesto_renta_total": float, 
    "seguro_social_total": float, "salario": float,

    # Fechas y Timestamps
    "creado": lambda v: datetime.fromisoformat(v) if '.' in v else date.fromisoformat(v),
    "periodo": date.fromisoformat, 
    "fecha_pago": date.fromisoformat,
}

# ======================================================================
# FUNCIONES DE AYUDA
# ======================================================================

def cast_value(col: str, value: Any) -> Any:
    """Intenta convertir un valor de cadena al tipo de Python requerido por asyncpg."""
    if value in ('None', 'NULL', ''):
        return None
        
    try:
        converter = TYPE_MAP.get(col)
        if converter:
            return converter(value)
        return value # Si no está en el mapa, es una cadena (VARCHAR/TEXT)
    except Exception:
        # En caso de error de conversión (ej. "abc" a int), devolvemos None
        # para que la DB pueda generar un error de NOT NULL si corresponde.
        return None 


# ======================================================================
## 1. Función de Backup 
# ======================================================================

async def generate_backup_csv(conn: asyncpg.Connection) -> bytes:
    """
    Exporta los datos de las tablas configuradas a un único archivo CSV.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([f"## BACKUP_CREATED: {datetime.now().isoformat()} ##"])

    for table_name in TABLES_ORDER:
        config = TABLE_CONFIG[table_name]
        query = f"SELECT * FROM {table_name} ORDER BY {config['id_column']};"
        rows = await conn.fetch(query)

        writer.writerow([f"## TABLE_START: {table_name} ##"])
        
        if not rows:
            continue

        columns = list(rows[0].keys())
        writer.writerow(columns)
        
        for row in rows:
            writer.writerow([str(row[col]) for col in columns])

    return output.getvalue().encode('utf-8')


# ======================================================================
## 2. Función de Restore (FINAL)
# ======================================================================

async def restore_data_from_csv(conn: asyncpg.Connection, csv_content: bytes) -> Dict[str, Any]:
    """
    Lee el contenido CSV y restaura los datos en las tablas, manejando IDs SERIAL, FKs adelantadas y duplicados.
    """
    results = {"restored": {}, "errors": {}}
    content = csv_content.decode('utf-8')
    reader = csv.reader(io.StringIO(content))
    
    current_table = None
    columns = []
    data_to_restore = {t: [] for t in TABLES_ORDER}
    
    # -------------------------------------------------------------
    # ETAPA 1: Lectura y Estructuración de Datos
    # -------------------------------------------------------------
    for row in reader:
        if not row: continue
            
        if row[0].startswith("## TABLE_START: "):
            current_table = row[0].split(": ")[1].split(" ##")[0]
            columns = []
            continue

        if current_table and not columns and current_table in data_to_restore:
            columns = row
            continue
            
        if current_table and columns and current_table in data_to_restore:
            if len(row) == len(columns):
                data_to_restore[current_table].append(dict(zip(columns, row)))

    # -------------------------------------------------------------
    # ETAPA 2: Inserción de Datos (Pass 1: Con Casting y Manejo de Duplicados)
    # -------------------------------------------------------------
    
    for current_table in TABLES_ORDER:
        if current_table not in TABLE_CONFIG: continue
            
        config = TABLE_CONFIG[current_table]
        results["restored"][current_table] = {"success_count": 0, "skipped_duplicates": 0, "total_rows": len(data_to_restore[current_table])}
        
        for record_data in data_to_restore[current_table]:
            
            insert_cols = []
            insert_values = []
            
            for col, value in record_data.items():
                
                # REGLA 1: Omitir la columna de ID si es SERIAL
                if col == config["id_column"] and not config["is_manual"]:
                    continue 

                # REGLA 2: Omitir las FK que referencian un ID SERIAL (jefe_departamento, id_trabajador)
                if col == config.get("forward_fk"): 
                     continue 
                
                # APLICAR CASTING DE TIPO
                final_value = cast_value(col, value)
                
                insert_cols.append(col)
                insert_values.append(final_value)
            
            # Construcción de la consulta INSERT ON CONFLICT
            cols_sql = ", ".join(insert_cols)
            params_sql = ", ".join([f"${i+1}" for i in range(len(insert_values))])

            conflict_target = config["id_column"] if config["is_manual"] else config["conflict_target"]
            
            # El ON CONFLICT solo se aplica a la clave principal/documento
            query = f"""
            INSERT INTO {current_table} ({cols_sql}) 
            VALUES ({params_sql})
            ON CONFLICT ({conflict_target}) 
            DO NOTHING;
            """
            
            try:
                status_result = await conn.execute(query, *insert_values)
                
                if status_result.endswith(" 1"):
                    results["restored"][current_table]["success_count"] += 1
                    
            # 🟢 MANEJO DE VIOLACIÓN DE UNICIDAD (para campos únicos secundarios como 'nombre' o 'correo')
            except asyncpg.exceptions.UniqueViolationError:
                results["restored"][current_table]["skipped_duplicates"] += 1

            except Exception as e:
                # Otros errores (FK, NOT NULL, etc.) se registran en 'errors'
                error_key = f"{current_table}_error"
                results["errors"][error_key] = results["errors"].get(error_key, []) + [{"data": record_data, "error": str(e)}]


    # -------------------------------------------------------------
    # ETAPA 3: Actualización de FKs SERIALES (Pass 2: Mapeo por Documento)
    # -------------------------------------------------------------

    # 3A. Mapeo del ID_antiguo (del CSV) al Documento para buscar el nuevo ID.
    old_worker_map = {}
    for d in data_to_restore.get("trabajador", []):
        try:
            old_id = int(d.get("id_trabajador"))
            documento = d.get("documento")
            if documento:
                 old_worker_map[old_id] = documento
        except (ValueError, TypeError):
             continue 
    
    
    # 3B. Actualizar departamento.jefe_departamento
    dept_to_update = []
    
    for dept_data in data_to_restore.get("departamento", []):
        try:
            old_jefe_id = int(dept_data.get("jefe_departamento"))
        except (ValueError, TypeError):
             continue 
        
        if old_jefe_id:
            documento = old_worker_map.get(old_jefe_id)
            if documento:
                dept_to_update.append((dept_data["id_departamento"], documento))
    
    if dept_to_update:
        update_dept_query = """
        UPDATE departamento AS d
        SET jefe_departamento = t.id_trabajador
        FROM trabajador AS t
        WHERE t.documento = $2 AND d.id_departamento = $1;
        """
        try:
            for dept_id, worker_doc in dept_to_update:
                 await conn.execute(update_dept_query, dept_id, worker_doc)
        except Exception as e:
             error_key = "departamento_update_fk_error"
             results["errors"][error_key] = results["errors"].get(error_key, []) + [{"error": f"Error al actualizar jefe_departamento: {e}"}]


    # 3C. Actualizar usuario.id_trabajador
    
    update_user_fk_query = """
    UPDATE usuario AS u
    SET id_trabajador = t.id_trabajador
    FROM trabajador AS t
    WHERE u.documento = t.documento AND u.id_trabajador IS NULL;
    """
    
    try:
        await conn.execute(update_user_fk_query)
    except Exception as e:
        error_key = "usuario_update_fk_error"
        results["errors"][error_key] = results["errors"].get(error_key, []) + [{"error": f"Error al actualizar id_trabajador en usuario: {e}"}]

    return results