# controllers/nomina_detalle_controller.py
from typing import List, Optional
import asyncpg
from asyncpg.exceptions import UniqueViolationError, ForeignKeyViolationError, CheckViolationError
from app.schemas.nomina_detalle import NominaDetalleCreate, NominaDetalleUpdate, NominaDetalleOut
from app.models.nomina_detalle import NominaDetalle
from decimal import Decimal
import uuid # Para generar un ID_DETALLE_NOMINA único

# Función de Creación Múltiple (Requerida por Nomina General)
async def create_detalles_for_nomina(
    conn: asyncpg.Connection, 
    id_nomina: str, 
    id_departamento: str
) -> List[NominaDetalle]:
    """
    Inserta registros de NominaDetalle para todos los trabajadores activos 
    del departamento especificado, usando su salario base actual.
    """
    # 1. Obtener los trabajadores activos del departamento con su salario
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
    
    # Prepara la inserción de todos los detalles en una sola transacción
    async with conn.transaction():
        for i, t in enumerate(trabajadores):
            salario_base = t["salario_base_actual"]
            
            # Cálculo del Salario Neto inicial (con Rem/Ded en 0)
            salario_neto = salario_base 

            # Generar un ID único para cada detalle (usando UUID o una combinación)
            # Usaremos una combinación sencilla ID_NOMINA + índice
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
                Decimal('0.00'), # total_remuneraciones inicia en 0
                Decimal('0.00'), # total_deducciones inicia en 0
                salario_neto, 
                1, # estado activo
                0  # estado_pago: Pendiente
            )

            try:
                record = await conn.fetchrow(query_insert, *values)
                if record:
                    detalles_creados.append(NominaDetalle.from_record(record))
            except (UniqueViolationError, ForeignKeyViolationError, CheckViolationError) as e:
                 # Manejo de error si un trabajador ya tiene un detalle para esta nómina (aunque la lógica lo evita)
                print(f"Error al crear detalle para trabajador {t['id_trabajador']}: {e}")
                raise ValueError(f"Error al crear detalles de nómina: {e}") 

    return detalles_creados


# --- CRUD Básico para Nomina Detalle ---

async def get_nomina_detalle_by_id(conn: asyncpg.Connection, detalle_id: str) -> Optional[NominaDetalle]:
    query = "SELECT * FROM nomina_detalle WHERE id_detalle_nomina = $1;"
    record = await conn.fetchrow(query, detalle_id)
    return NominaDetalle.from_record(record) if record else None

async def list_nomina_detalles_by_nomina(
    conn: asyncpg.Connection, 
    id_nomina: str
) -> List[NominaDetalle]:
    """Lista todos los detalles asociados a una nómina general específica."""
    query = "SELECT * FROM nomina_detalle WHERE id_nomina = $1 ORDER BY id_trabajador;"
    rows = await conn.fetch(query, id_nomina)
    return [NominaDetalle.from_record(r) for r in rows]

async def update_nomina_detalle(conn: asyncpg.Connection, detalle_id: str, detalle_in: NominaDetalleUpdate) -> Optional[NominaDetalle]:
    update_data = detalle_in.model_dump(exclude_unset=True)
    if not update_data:
        return await get_nomina_detalle_by_id(conn, detalle_id)
        
    set_clauses = []
    values = []
    param_index = 1
    
    # Lógica para recalcular salario_neto si se actualizan remuneraciones o deducciones
    recalculate_neto = False
    if 'total_remuneraciones' in update_data or 'total_deducciones' in update_data:
        recalculate_neto = True
        
    for key, value in update_data.items():
        set_clauses.append(f"{key} = ${param_index}")
        values.append(value)
        param_index += 1

    if recalculate_neto:
        # PostgreSQL permite usar valores de otras columnas en la sentencia SET
        # Aquí asumimos que el salario_base NO se actualiza en esta operación.
        rem = update_data.get('total_remuneraciones', 'total_remuneraciones')
        ded = update_data.get('total_deducciones', 'total_deducciones')
        
        # Si rem o ded son objetos Decimal, deben ser pasados como parámetros. 
        # Si son strings, significa que usamos la columna existente.
        
        # Simplificación: si se actualiza rem o ded, forzamos el cálculo
        # y pasamos el valor actual o el nuevo.
        # Una forma más robusta es obtener el registro primero, pero esto es más eficiente:
        
        # Solo actualizamos el salario_neto si es necesario
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
            return NominaDetalle.from_record(record)
        return None
    except (ForeignKeyViolationError, CheckViolationError) as e:
        raise ValueError(f"Error de validación: La base de datos rechazó los datos. {e}")