# controllers/trabajador_controller.py
from typing import List, Optional
import asyncpg
from asyncpg.exceptions import UniqueViolationError, CheckViolationError, NotNullViolationError
from datetime import date

from app.schemas.trabajador import TrabajadorCreate, TrabajadorUpdate
from app.models.trabajador import Trabajador

# --- 1. Crear Trabajador ---
async def create_trabajador(conn: asyncpg.Connection, trb_in: TrabajadorCreate) -> Optional[Trabajador]:
    """Crea un nuevo trabajador en la base de datos."""
    
    # Nota: 'creado' se establece a la fecha actual antes de la inserción.
    query = """
    INSERT INTO trabajador (
        documento, nombre, apellido, correo, telefono, direccion, 
        id_departamento, id_cargo, salario, tipo_contrato, creado, 
        habilidades_competencias, estado
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
    RETURNING *;
    """
    
    values = (
        trb_in.documento, trb_in.nombre, trb_in.apellido, trb_in.correo, trb_in.telefono, trb_in.direccion, 
        trb_in.id_departamento, trb_in.id_cargo, trb_in.salario, trb_in.tipo_contrato, date.today(), 
        trb_in.habilidades_competencias, trb_in.estado
    )
    
    try:
        record = await conn.fetchrow(query, *values)
        if record:
            return Trabajador.from_record(record)
    except UniqueViolationError:
        raise ValueError("Error de unicidad: El documento o correo ya existe.")
    except (CheckViolationError, NotNullViolationError) as e:
        # Los errores de foreign key (fk_cargo) también pueden ser manejados aquí si se necesita más detalle
        raise ValueError(f"Error de validación: La base de datos rechazó los datos. {e.detail}")
    
    return None

# --- 2. Listar Trabajadores (con Paginación y Filtrado) ---
async def list_trabajadores(
    conn: asyncpg.Connection, 
    skip: int = 0, 
    limit: int = 100,
    activo: Optional[bool] = None, # Filtra por estado
    id_departamento: Optional[str] = None # Filtra por departamento
) -> List[Trabajador]:
    """Retorna la lista de trabajadores con paginación y filtros."""
    
    where_clauses = []
    values = []
    param_index = 1
    
    # Filtro por Estado
    if activo is not None:
        estado_val = 1 if activo else 0
        where_clauses.append(f"estado = ${param_index}")
        values.append(estado_val)
        param_index += 1
        
    # Filtro por Departamento
    if id_departamento:
        where_clauses.append(f"id_departamento = ${param_index}")
        values.append(id_departamento)
        param_index += 1

    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # Paginación (LIMIT y OFFSET)
    query = f"""
    SELECT * FROM trabajador 
    {where_sql} 
    ORDER BY apellido, nombre
    LIMIT ${param_index} 
    OFFSET ${param_index + 1};
    """
    values.extend([limit, skip])

    rows = await conn.fetch(query, *values)
    return [Trabajador.from_record(r) for r in rows]

# --- 3. Obtener un Trabajador por ID ---
async def get_trabajador_by_id(conn: asyncpg.Connection, trb_id: int) -> Optional[Trabajador]:
    query = "SELECT * FROM trabajador WHERE id_trabajador = $1;"
    record = await conn.fetchrow(query, trb_id)
    return Trabajador.from_record(record) if record else None

# --- 4. Actualizar Trabajador ---
async def update_trabajador(conn: asyncpg.Connection, trb_id: int, trb_in: TrabajadorUpdate) -> Optional[Trabajador]:
    """Actualiza los campos de un trabajador y retorna el objeto actualizado."""
    update_data = trb_in.model_dump(exclude_unset=True)
    if not update_data:
        return await get_trabajador_by_id(conn, trb_id)
        
    set_clauses = []
    values = []
    param_index = 1
    
    for key, value in update_data.items():
        set_clauses.append(f"{key} = ${param_index}")
        values.append(value)
        param_index += 1

    values.append(trb_id)
    
    query = f"""
    UPDATE trabajador 
    SET {', '.join(set_clauses)}
    WHERE id_trabajador = ${param_index}
    RETURNING *;
    """

    try:
        record = await conn.fetchrow(query, *values)
        if record:
            return Trabajador.from_record(record)
        return None
    except UniqueViolationError:
        raise ValueError("Error de unicidad: El documento o correo ya están en uso.")
    except (CheckViolationError, NotNullViolationError) as e:
        raise ValueError(f"Error de validación: La base de datos rechazó los datos. {e.detail}")

# --- 5. Eliminar Trabajador (Lógica) ---
async def deactivate_trabajador(conn: asyncpg.Connection, trb_id: int) -> Optional[Trabajador]:
    """Realiza una eliminación lógica (establece estado a 0) de un trabajador."""
    deactivate_data = TrabajadorUpdate(estado=0)
    return await update_trabajador(conn, trb_id, deactivate_data)