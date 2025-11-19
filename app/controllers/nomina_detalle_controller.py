# controllers/nomina_detalle_controller.py (COMPLETO Y CORREGIDO)
from typing import List, Optional
import asyncpg
from asyncpg.exceptions import UniqueViolationError, ForeignKeyViolationError, CheckViolationError
from app.schemas.nomina_detalle import NominaDetalleCreate, NominaDetalleUpdate, NominaDetalleOut
from app.models.nomina_detalle import NominaDetalle
from decimal import Decimal
import uuid 

# --- Función de Creación Múltiple (Se mantiene sin JOIN para eficiencia) ---
async def create_detalles_for_nomina(
    conn: asyncpg.Connection, 
    id_nomina: str, 
    id_departamento: str
) -> List[NominaDetalle]:
    """
    Inserta registros de NominaDetalle para todos los trabajadores activos 
    del departamento especificado, usando su salario base actual.
    """
    query_trabajadores = """
    SELECT 
        id_trabajador, salario AS salario_base_actual
    FROM 
        trabajador 
    WHERE 
        id_departamento = $1 AND estado = 1;
    """
    trabajadores = await conn.fetch(query_trabajadores, id_departamento)

    if not trabajadores:
        return []

    detalles_creados = []
    
    async with conn.transaction():
        for i, t in enumerate(trabajadores):
            salario_base = t["salario_base_actual"]
            salario_neto = salario_base 
            id_detalle = f"{id_nomina}-{i+1}" 

            query_insert = """
            INSERT INTO nomina_detalle (
                id_detalle_nomina, id_nomina, id_trabajador, salario_base, 
                total_remuneraciones, total_deducciones, salario_neto, estado, estado_pago
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *;
            """
            
            values = (
                id_detalle, 
                id_nomina, 
                t["id_trabajador"], 
                salario_base, 
                Decimal('0.00'), 
                Decimal('0.00'), 
                salario_neto, 
                1, 
                0 
            )

            try:
                record = await conn.fetchrow(query_insert, *values)
                if record:
                    # Devolvemos el modelo base. Si la ruta requiere el modelo enriquecido,
                    # debe hacer una llamada posterior a list_nomina_detalles_by_nomina.
                    detalles_creados.append(NominaDetalle.from_record(record))
            except (UniqueViolationError, ForeignKeyViolationError, CheckViolationError) as e:
                print(f"Error al crear detalle para trabajador {t['id_trabajador']}: {e}")
                raise ValueError(f"Error al crear detalles de nómina: {e}") 

    return detalles_creados


# --- CRUD Básico para Nomina Detalle (MODIFICADO) ---

async def get_nomina_detalle_by_id(conn: asyncpg.Connection, detalle_id: str) -> Optional[NominaDetalle]:
    """Obtiene un detalle de nómina por ID, incluyendo nombre y apellido del trabajador."""
    query = """
    SELECT 
        nd.*, 
        t.nombre AS nombre_trabajador, 
        t.apellido AS apellido_trabajador
    FROM nomina_detalle nd
    JOIN trabajador t ON nd.id_trabajador = t.id_trabajador
    WHERE nd.id_detalle_nomina = $1;
    """
    record = await conn.fetchrow(query, detalle_id)
    return NominaDetalle.from_record(record) if record else None

async def list_nomina_detalles_by_nomina(
    conn: asyncpg.Connection, 
    id_nomina: str
) -> List[NominaDetalle]:
    """Lista todos los detalles asociados a una nómina general específica, incluyendo datos del trabajador."""
    query = """
    SELECT 
        nd.*, 
        t.nombre AS nombre_trabajador, 
        t.apellido AS apellido_trabajador
    FROM nomina_detalle nd
    JOIN trabajador t ON nd.id_trabajador = t.id_trabajador
    WHERE nd.id_nomina = $1 
    ORDER BY t.apellido, t.nombre;
    """
    rows = await conn.fetch(query, id_nomina)
    return [NominaDetalle.from_record(r) for r in rows]

async def update_nomina_detalle(conn: asyncpg.Connection, detalle_id: str, detalle_in: NominaDetalleUpdate) -> Optional[NominaDetalle]:
    update_data = detalle_in.model_dump(exclude_unset=True)
    if not update_data:
        # Devuelve la versión enriquecida
        return await get_nomina_detalle_by_id(conn, detalle_id)
        
    set_clauses = []
    values = []
    param_index = 1
    
    recalculate_neto = False
    if 'total_remuneraciones' in update_data or 'total_deducciones' in update_data:
        recalculate_neto = True
        
    for key, value in update_data.items():
        set_clauses.append(f"{key} = ${param_index}")
        values.append(value)
        param_index += 1

    if recalculate_neto:
        set_clauses.append(f"salario_neto = salario_base + COALESCE(total_remuneraciones, 0) - COALESCE(total_deducciones, 0)")

    values.append(detalle_id)
    
    query = f"""
    UPDATE nomina_detalle 
    SET {', '.join(set_clauses)}
    WHERE id_detalle_nomina = ${param_index}
    RETURNING *;
    """

    try:
        record = await conn.fetchrow(query, *values)
        if record:
            # Retorna la versión enriquecida (con JOIN)
            return await get_nomina_detalle_by_id(conn, detalle_id)
        return None
    except (ForeignKeyViolationError, CheckViolationError) as e:
        raise ValueError(f"Error de validación: La base de datos rechazó los datos. {e}")