# controllers/departamento_controller.py (FINAL)
from typing import List, Optional
import asyncpg
from asyncpg.exceptions import UniqueViolationError, CheckViolationError, NotNullViolationError

from app.schemas.departamento import DepartamentoCreate, DepartamentoUpdate
from app.models.departamento import Departamento

# --- 1. Crear Departamento ---
async def create_departamento(conn: asyncpg.Connection, dep_in: DepartamentoCreate) -> Optional[Departamento]:
    query = """
    INSERT INTO departamento (
        id_departamento, nombre, descripcion, jefe_departamento, 
        presupuesto_anual, telefono, email, ubicacion, capacidad_empleados, estado
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    RETURNING *;
    """
    
    values = (
        dep_in.id_departamento, dep_in.nombre, dep_in.descripcion, dep_in.jefe_departamento, 
        dep_in.presupuesto_anual, dep_in.telefono, dep_in.email, dep_in.ubicacion, 
        dep_in.capacidad_empleados, dep_in.estado
    )
    
    try:
        record = await conn.fetchrow(query, *values)
        if record:
            return Departamento.from_record(record)
    except UniqueViolationError:
        raise ValueError("Error de unicidad: ID, nombre o jefe_departamento ya existe.")
    except (CheckViolationError, NotNullViolationError) as e:
        raise ValueError(f"Error de validación: La base de datos rechazó los datos. {e.detail}")
    
    return None

# --- 2. Listar Departamentos (con Paginación y Filtrado) ---
async def list_departamentos(
    conn: asyncpg.Connection, 
    skip: int = 0, 
    limit: int = 100,
    activo: Optional[bool] = None # Si es None, trae todos. True=solo activos(1), False=solo inactivos(0)
) -> List[Departamento]:
    """Retorna la lista de departamentos, con paginación y filtro por estado."""
    
    where_clauses = []
    values = []
    param_index = 1
    
    # Filtro por Estado
    if activo is not None:
        estado_val = 1 if activo else 0
        where_clauses.append(f"estado = ${param_index}")
        values.append(estado_val)
        param_index += 1

    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # Paginación (LIMIT y OFFSET)
    query = f"""
    SELECT * FROM departamento 
    {where_sql} 
    ORDER BY nombre 
    LIMIT ${param_index} 
    OFFSET ${param_index + 1};
    """
    values.extend([limit, skip])

    rows = await conn.fetch(query, *values)
    return [Departamento.from_record(r) for r in rows]

# --- 3. Obtener un Departamento por ID ---
async def get_departamento_by_id(conn: asyncpg.Connection, dep_id: str) -> Optional[Departamento]:
    query = "SELECT * FROM departamento WHERE id_departamento = $1;"
    record = await conn.fetchrow(query, dep_id)
    return Departamento.from_record(record) if record else None

# --- 4. Actualizar Departamento ---
async def update_departamento(conn: asyncpg.Connection, dep_id: str, dep_in: DepartamentoUpdate) -> Optional[Departamento]:
    update_data = dep_in.model_dump(exclude_unset=True)
    if not update_data:
        return await get_departamento_by_id(conn, dep_id)
        
    set_clauses = []
    values = []
    param_index = 1
    
    for key, value in update_data.items():
        set_clauses.append(f"{key} = ${param_index}")
        values.append(value)
        param_index += 1

    values.append(dep_id)
    
    query = f"""
    UPDATE departamento 
    SET {', '.join(set_clauses)}
    WHERE id_departamento = ${param_index}
    RETURNING *;
    """

    try:
        record = await conn.fetchrow(query, *values)
        if record:
            return Departamento.from_record(record)
        return None
    except UniqueViolationError:
        raise ValueError("Error de unicidad: El nombre o jefe_departamento ya están en uso.")
    except (CheckViolationError, NotNullViolationError) as e:
        raise ValueError(f"Error de validación: La base de datos rechazó los datos. {e.detail}")