# controllers/concepto_nomina_controller.py
from typing import List, Optional
import asyncpg
from asyncpg.exceptions import ForeignKeyViolationError, CheckViolationError, NotNullViolationError
from app.schemas.concepto_nomina import ConceptoNominaCreate, ConceptoNominaUpdate
from app.models.concepto_nomina import ConceptoNomina
from decimal import Decimal

# --- Función Auxiliar para Actualizar Totales del Detalle ---
async def _update_detalle_totals(conn: asyncpg.Connection, id_detalle_nomina: str, monto: Decimal, tipo: int, operation: str):
    """
    Actualiza el total de remuneraciones o deducciones en nomina_detalle y recalcula el salario_neto.
    Operation: 'ADD' (para aplicar) o 'SUBTRACT' (para revertir).
    """
    if tipo == 0:  # Remuneración
        columna = "total_remuneraciones"
    elif tipo == 1:  # Deducción
        columna = "total_deducciones"
    else:
        raise ValueError("Tipo de concepto inválido. Debe ser 0 (Remuneración) o 1 (Deducción).")

    operador = "+" if operation == 'ADD' else "-"

    # Consulta SQL robusta: Actualiza la columna de total y recalcula el salario_neto
    query = f"""
    UPDATE nomina_detalle 
    SET 
        {columna} = {columna} {operador} $2,
        -- Recalcula el salario neto basado en los nuevos totales
        salario_neto = salario_base + 
                       (CASE WHEN '{columna}' = 'total_remuneraciones' THEN total_remuneraciones {operador} $2 ELSE total_remuneraciones END) -
                       (CASE WHEN '{columna}' = 'total_deducciones' THEN total_deducciones {operador} $2 ELSE total_deducciones END)
    WHERE id_detalle_nomina = $1;
    """
    await conn.execute(query, id_detalle_nomina, monto)


# --- 1. Crear Concepto Nómina ---
async def create_concepto_nomina(conn: asyncpg.Connection, concepto_in: ConceptoNominaCreate) -> Optional[ConceptoNomina]:
    query = """
    INSERT INTO concepto_nomina (
        id_detalle_nomina, razon, monto, tipo, estado
    ) VALUES ($1, $2, $3, $4, $5)
    RETURNING *;
    """
    
    values = (
        concepto_in.id_detalle_nomina, concepto_in.razon, concepto_in.monto, 
        concepto_in.tipo, concepto_in.estado
    )
    
    async with conn.transaction():
        try:
            # 1. Insertar el Concepto
            record = await conn.fetchrow(query, *values)
            
            if record:
                concepto_obj = ConceptoNomina.from_record(record)
                
                # 2. VERIFICACIÓN DE ESTADO: Solo se aplica si el estado es 1 (Activo)
                if concepto_obj.estado == 1:
                    await _update_detalle_totals(
                        conn, 
                        concepto_obj.id_detalle_nomina, 
                        concepto_obj.monto, 
                        concepto_obj.tipo, 
                        'ADD'
                    )
                return concepto_obj
        
        except ForeignKeyViolationError:
            raise ValueError("Error de clave foránea: El ID de detalle de nómina no existe.")
        except (CheckViolationError, NotNullViolationError) as e:
            raise ValueError(f"Error de validación: La base de datos rechazó los datos. {e.detail}")
    
    return None

# --- 2. Obtener un Concepto por ID ---
async def get_concepto_by_id(conn: asyncpg.Connection, concepto_id: int) -> Optional[ConceptoNomina]:
    query = "SELECT * FROM concepto_nomina WHERE id_concepto = $1;"
    record = await conn.fetchrow(query, concepto_id)
    return ConceptoNomina.from_record(record) if record else None

# --- 3. Actualizar Concepto Nómina ---
async def update_concepto_nomina(conn: asyncpg.Connection, concepto_id: int, concepto_in: ConceptoNominaUpdate) -> Optional[ConceptoNomina]:
    update_data = concepto_in.model_dump(exclude_unset=True)
    if not update_data:
        return await get_concepto_by_id(conn, concepto_id)
        
    set_clauses = []
    values = []
    param_index = 1
    
    async with conn.transaction():
        # 1. Obtener el concepto actual antes de la actualización
        old_record = await get_concepto_by_id(conn, concepto_id)
        if not old_record:
            return None
        
        # 2. Lógica de REVERSIÓN: Si el concepto estaba ACTIVO, revertir su impacto.
        if old_record.estado == 1:
            await _update_detalle_totals(
                conn, 
                old_record.id_detalle_nomina, 
                old_record.monto, 
                old_record.tipo, 
                'SUBTRACT' # Revertir el impacto previo
            )

        # 3. Construir la consulta de actualización del Concepto
        for key, value in update_data.items():
            set_clauses.append(f"{key} = ${param_index}")
            values.append(value)
            param_index += 1

        values.append(concepto_id)
        
        query = f"""
        UPDATE concepto_nomina 
        SET {', '.join(set_clauses)}
        WHERE id_concepto = ${param_index}
        RETURNING *;
        """

        try:
            new_record = await conn.fetchrow(query, *values)
            
            if new_record:
                concepto_obj = ConceptoNomina.from_record(new_record)
                
                # 4. Lógica de APLICACIÓN: Si el concepto está ACTIVO después de la actualización, aplicar el nuevo impacto.
                if concepto_obj.estado == 1:
                    await _update_detalle_totals(
                        conn, 
                        concepto_obj.id_detalle_nomina, 
                        concepto_obj.monto, 
                        concepto_obj.tipo, 
                        'ADD' # Aplicar el nuevo valor/estado
                    )
                return concepto_obj
            return None
            
        except (ForeignKeyViolationError, CheckViolationError) as e:
            raise ValueError(f"Error de validación: La base de datos rechazó los datos. {e}")

# --- 4. Listar Conceptos por Detalle de Nómina ---
async def list_conceptos_by_detalle(
    conn: asyncpg.Connection, 
    id_detalle: str
) -> List[ConceptoNomina]:
    """Lista todos los conceptos asociados a un detalle de nómina específico."""
    query = "SELECT * FROM concepto_nomina WHERE id_detalle_nomina = $1 ORDER BY tipo, razon;"
    rows = await conn.fetch(query, id_detalle)
    return [ConceptoNomina.from_record(r) for r in rows]