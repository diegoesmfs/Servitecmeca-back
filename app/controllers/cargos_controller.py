# controllers/cargos_controller.py
from typing import List, Optional
import asyncpg
from asyncpg.exceptions import UniqueViolationError, CheckViolationError, NotNullViolationError
from datetime import datetime

from app.schemas.cargos import CargoCreate, CargoUpdate
from app.models.cargo import Cargo 


# --- 1. Crear Cargo ---
async def create_cargo(conn: asyncpg.Connection, cargo_in: CargoCreate) -> Optional[Cargo]:
    """Crea un nuevo cargo y, tras la inserción, recupera el objeto completo con JOIN."""
    
    query = """
    INSERT INTO cargos (
        id_cargo, id_departamento, titulo, descripcion, nivel, 
        salario_base, salario_maximo, competencias, estado
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    RETURNING id_cargo;
    """
    
    values = (
        cargo_in.id_cargo, cargo_in.id_departamento, cargo_in.titulo, cargo_in.descripcion, 
        cargo_in.nivel, cargo_in.salario_base, cargo_in.salario_maximo, 
        cargo_in.competencias, cargo_in.estado
    )
    
    try:
        record = await conn.fetchrow(query, *values)
        if record:
            return await get_cargo_by_id(conn, record['id_cargo'])
            
    except UniqueViolationError:
        raise ValueError("Error de unicidad: El ID de cargo o la combinación título/departamento ya existen.")
    except (CheckViolationError, NotNullViolationError) as e:
        raise ValueError(f"Error de validación: La base de datos rechazó los datos. {e.detail}")
    
    return None


# --- 2. Listar Cargos ---
async def list_cargos(
    conn: asyncpg.Connection, 
    skip: int = 0, 
    limit: int = 100,
    activo: Optional[bool] = None,
    id_departamento: Optional[str] = None
) -> List[Cargo]:
    """Retorna la lista de cargos con paginación y filtros, incluyendo nombre de departamento."""
    
    where_clauses = []
    values = []
    param_index = 1
    
    if activo is not None:
        estado_val = 1 if activo else 0
        where_clauses.append(f"c.estado = ${param_index}")
        values.append(estado_val)
        param_index += 1
        
    if id_departamento:
        where_clauses.append(f"c.id_departamento = ${param_index}")
        values.append(id_departamento)
        param_index += 1

    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    query = f"""
    SELECT 
        c.*, 
        d.nombre AS nombre_departamento
    FROM cargos c
    JOIN departamento d ON c.id_departamento = d.id_departamento
    {where_sql} 
    ORDER BY d.nombre, c.titulo
    LIMIT ${param_index} 
    OFFSET ${param_index + 1};
    """
    values.extend([limit, skip])

    rows = await conn.fetch(query, *values)
    return [Cargo.from_record(r) for r in rows]


# --- 3. Obtener un Cargo por ID ---
async def get_cargo_by_id(conn: asyncpg.Connection, cargo_id: str) -> Optional[Cargo]:
    """Obtiene un cargo por ID, incluyendo el nombre de departamento."""
    query = """
    SELECT 
        c.*, 
        d.nombre AS nombre_departamento
    FROM cargos c
    JOIN departamento d ON c.id_departamento = d.id_departamento
    WHERE c.id_cargo = $1;
    """
    record = await conn.fetchrow(query, cargo_id)
    return Cargo.from_record(record) if record else None


# --- 4. Actualizar Cargo ---
async def update_cargo(conn: asyncpg.Connection, cargo_id: str, cargo_in: CargoUpdate) -> Optional[Cargo]:
    """Actualiza los campos de un cargo y retorna el objeto actualizado con los datos JOIN."""
    update_data = cargo_in.model_dump(exclude_unset=True)
    if not update_data:
        return await get_cargo_by_id(conn, cargo_id)
        
    set_clauses = []
    values = []
    param_index = 1
    
    for key, value in update_data.items():
        set_clauses.append(f"{key} = ${param_index}")
        values.append(value)
        param_index += 1

    values.append(cargo_id)
    
    query = f"""
    UPDATE cargos 
    SET {', '.join(set_clauses)}
    WHERE id_cargo = ${param_index}
    RETURNING *;
    """

    try:
        record = await conn.fetchrow(query, *values)
        if record:
            return await get_cargo_by_id(conn, cargo_id) 
        return None
    except UniqueViolationError:
        raise ValueError("Error de unicidad: La combinación título/departamento ya están en uso.")
    except (CheckViolationError, NotNullViolationError) as e:
        raise ValueError(f"Error de validación: La base de datos rechazó los datos. {e.detail}")

# --- 5. Eliminar Cargo (Lógica) ---
async def deactivate_cargo(conn: asyncpg.Connection, cargo_id: str) -> Optional[Cargo]:
    """Realiza una eliminación lógica (establece estado a 0) de un cargo."""
    deactivate_data = CargoUpdate(estado=0)
    return await update_cargo(conn, cargo_id, deactivate_data)


# --- 6. Obtener Cargos por Departamento (Para listar) ---
async def get_cargos_by_departamento(
    conn: asyncpg.Connection, 
    id_departamento: str, 
    activo: Optional[bool] = None
) -> List[Cargo]:
    """
    Retorna la lista de cargos (enriquecidos con nombre_departamento) 
    dentro de un departamento específico, con filtro opcional por estado.
    """
    
    where_clauses = ["c.id_departamento = $1"]
    values = [id_departamento]
    param_index = 2
    
    if activo is not None:
        estado_val = 1 if activo else 0
        where_clauses.append(f"c.estado = ${param_index}")
        values.append(estado_val)
        param_index += 1

    where_sql = " WHERE " + " AND ".join(where_clauses)
    
    query = f"""
    SELECT 
        c.*, 
        d.nombre AS nombre_departamento
    FROM cargos c
    JOIN departamento d ON c.id_departamento = d.id_departamento
    {where_sql} 
    ORDER BY c.titulo;
    """

    rows = await conn.fetch(query, *values)
    return [Cargo.from_record(r) for r in rows]
    
# --- 7. Contar cargos por departamento ---
async def count_cargos_by_departamento(
    conn: asyncpg.Connection, id_departamento: str, activo: Optional[bool] = None
) -> int:
    """Retorna el número de cargos en un departamento."""
    values = [id_departamento]
    
    if activo is None:
        query = "SELECT COUNT(*) as total FROM cargos WHERE id_departamento = $1;"
        row = await conn.fetchrow(query, *values)
        return int(row["total"]) if row else 0

    estado_val = 1 if activo else 0
    query = "SELECT COUNT(*) as total FROM cargos WHERE id_departamento = $1 AND estado = $2;"
    row = await conn.fetchrow(query, id_departamento, estado_val)
    return int(row["total"]) if row else 0