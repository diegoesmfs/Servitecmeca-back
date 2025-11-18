# controllers/trabajador_controller.py
from typing import List, Optional
import asyncpg
from asyncpg.exceptions import UniqueViolationError, CheckViolationError, NotNullViolationError
from datetime import date

from app.schemas.trabajador import TrabajadorCreate, TrabajadorUpdate
from app.models.trabajador import Trabajador # Asumiendo que esta clase ahora maneja los campos extra

# --- 1. Crear Trabajador (Sin cambios en la lógica) ---
async def create_trabajador(conn: asyncpg.Connection, trb_in: TrabajadorCreate) -> Optional[Trabajador]:
    """Crea un nuevo trabajador en la base de datos."""
    
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
            # NOTA: Después de la creación, se devuelve el objeto básico. Si quieres 
            # devolver el objeto completo (con nombre_departamento y titulo_cargo),
            # deberías llamar a get_trabajador_by_id(conn, record['id_trabajador']) aquí.
            return Trabajador.from_record(record)
    except UniqueViolationError:
        raise ValueError("Error de unicidad: El documento o correo ya existe.")
    except (CheckViolationError, NotNullViolationError) as e:
        # Los errores de foreign key (fk_cargo) también pueden ser manejados aquí si se necesita más detalle
        raise ValueError(f"Error de validación: La base de datos rechazó los datos. {e.detail}")
    
    return None



# --- 2. Listar Trabajadores (MODIFICADO con JOIN) ---
async def list_trabajadores(
    conn: asyncpg.Connection, 
    skip: int = 0, 
    limit: int = 100,
    activo: Optional[bool] = None, # Filtra por estado
    id_departamento: Optional[str] = None # Filtra por departamento
) -> List[Trabajador]:
    """Retorna la lista de trabajadores con paginación y filtros, incluyendo nombre de departamento y título de cargo."""
    
    where_clauses = []
    values = []
    param_index = 1
    
    # Filtro por Estado
    if activo is not None:
        estado_val = 1 if activo else 0
        where_clauses.append(f"t.estado = ${param_index}")
        values.append(estado_val)
        param_index += 1
        
    # Filtro por Departamento
    if id_departamento:
        where_clauses.append(f"t.id_departamento = ${param_index}")
        values.append(id_departamento)
        param_index += 1

    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # La consulta JOIN selecciona los campos t.* y añade los campos d.nombre y c.titulo
    query = f"""
    SELECT 
        t.*, 
        d.nombre AS nombre_departamento, 
        c.titulo AS titulo_cargo
    FROM trabajador t
    JOIN departamento d ON t.id_departamento = d.id_departamento
    JOIN cargos c ON t.id_cargo = c.id_cargo
    {where_sql} 
    ORDER BY t.apellido, t.nombre
    LIMIT ${param_index} 
    OFFSET ${param_index + 1};
    """
    values.extend([limit, skip])

    rows = await conn.fetch(query, *values)
    return [Trabajador.from_record(r) for r in rows]



# --- 3. Obtener un Trabajador por ID (MODIFICADO con JOIN) ---
async def get_trabajador_by_id(conn: asyncpg.Connection, trb_id: int) -> Optional[Trabajador]:
    """Obtiene un trabajador por ID, incluyendo nombre de departamento y título de cargo."""
    query = """
    SELECT 
        t.*, 
        d.nombre AS nombre_departamento, 
        c.titulo AS titulo_cargo
    FROM trabajador t
    JOIN departamento d ON t.id_departamento = d.id_departamento
    JOIN cargos c ON t.id_cargo = c.id_cargo
    WHERE t.id_trabajador = $1;
    """
    record = await conn.fetchrow(query, trb_id)
    return Trabajador.from_record(record) if record else None



# --- 4. Actualizar Trabajador (MODIFICADO para retornar la versión completa) ---
async def update_trabajador(conn: asyncpg.Connection, trb_id: int, trb_in: TrabajadorUpdate) -> Optional[Trabajador]:
    """Actualiza los campos de un trabajador y retorna el objeto actualizado con los datos JOIN."""
    update_data = trb_in.model_dump(exclude_unset=True)
    if not update_data:
        # Si no hay datos que actualizar, devuelve la versión completa
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
            # Una vez actualizado, se recupera el objeto COMPLETO (con JOIN) para retornar
            return await get_trabajador_by_id(conn, trb_id) 
        return None
    except UniqueViolationError:
        raise ValueError("Error de unicidad: El documento o correo ya están en uso.")
    except (CheckViolationError, NotNullViolationError) as e:
        raise ValueError(f"Error de validación: La base de datos rechazó los datos. {e.detail}")

# --- 5. Eliminar Trabajador (Lógica) (Sin cambios en la lógica) ---
async def deactivate_trabajador(conn: asyncpg.Connection, trb_id: int) -> Optional[Trabajador]:
    """Realiza una eliminación lógica (establece estado a 0) de un trabajador."""
    deactivate_data = TrabajadorUpdate(estado=0)
    # update_trabajador se encarga de retornar el objeto completo
    return await update_trabajador(conn, trb_id, deactivate_data)


# --- 6. Contar trabajadores por departamento (Sin cambios) ---
async def count_trabajadores_by_departamento(
    conn: asyncpg.Connection, id_departamento: str, activo: Optional[bool] = None
) -> int:
    """Retorna el número de trabajadores en un departamento."""
    values = [id_departamento]
    if activo is None:
        query = "SELECT COUNT(*) as total FROM trabajador WHERE id_departamento = $1;"
        row = await conn.fetchrow(query, *values)
        return int(row["total"]) if row else 0

    estado_val = 1 if activo else 0
    query = "SELECT COUNT(*) as total FROM trabajador WHERE id_departamento = $1 AND estado = $2;"
    row = await conn.fetchrow(query, id_departamento, estado_val)
    return int(row["total"]) if row else 0