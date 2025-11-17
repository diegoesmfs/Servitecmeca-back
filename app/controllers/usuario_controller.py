from typing import List, Optional
from datetime import datetime
import asyncpg
from asyncpg.exceptions import UniqueViolationError, CheckViolationError, NotNullViolationError
from app.core.security import hash_password, verify_password
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.models.usuario import Usuario

# --- 1. Crear Usuario ---
async def create_usuario(conn: asyncpg.Connection, usr_in: UsuarioCreate) -> Optional[Usuario]:
    """Crea un nuevo usuario con la contraseña hasheada."""

    hashed_pwd = hash_password(usr_in.contrasena)

    query = """
    INSERT INTO usuario (
        nombre, correo, documento, id_trabajador, rol, contrasena, estado
    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
    RETURNING *;
    """

    values = (
        usr_in.nombre, usr_in.correo, usr_in.documento, usr_in.id_trabajador,
        usr_in.rol, hashed_pwd, usr_in.estado
    )

    try:
        record = await conn.fetchrow(query, *values)
        if record:
            return Usuario.from_record(record)
    except UniqueViolationError:
        raise ValueError("Error de unicidad: El correo, documento o ID de trabajador ya están registrados.")
    except (CheckViolationError, NotNullViolationError) as e:
        raise ValueError(f"Error de validación: La base de datos rechazó los datos. {e.detail}")

    return None

# --- 2. Listar Usuarios (Paginación) ---
async def list_usuarios(
    conn: asyncpg.Connection,
    skip: int = 0,
    limit: int = 100,
    activo: Optional[bool] = None
) -> List[Usuario]:
    """Retorna la lista de usuarios, con paginación y filtro por estado."""

    where_clauses = []
    values = []
    param_index = 1

    if activo is not None:
        estado_val = 1 if activo else 0
        where_clauses.append(f"estado = ${param_index}")
        values.append(estado_val)
        param_index += 1

    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    query = f"""
    SELECT * FROM usuario 
    {where_sql} 
    ORDER BY nombre 
    LIMIT ${param_index} 
    OFFSET ${param_index + 1};
    """
    values.extend([limit, skip])

    rows = await conn.fetch(query, *values)
    return [Usuario.from_record(r) for r in rows]

# --- 3. Obtener un Usuario por ID ---
async def get_usuario_by_id(conn: asyncpg.Connection, usr_id: int) -> Optional[Usuario]:
    query = "SELECT * FROM usuario WHERE id_usuario = $1;"
    record = await conn.fetchrow(query, usr_id)
    return Usuario.from_record(record) if record else None

# --- 4. Obtener un Usuario por Correo (Útil para Login) ---
async def get_usuario_by_correo(conn: asyncpg.Connection, correo: str) -> Optional[Usuario]:
    query = "SELECT * FROM usuario WHERE correo = $1;"
    record = await conn.fetchrow(query, correo)
    return Usuario.from_record(record) if record else None

# --- 5. Actualizar Usuario ---
async def update_usuario(conn: asyncpg.Connection, usr_id: int, usr_in: UsuarioUpdate) -> Optional[Usuario]:
    """Actualiza los campos de un usuario, hasheando la nueva contraseña si se proporciona."""
    update_data = usr_in.model_dump(exclude_unset=True)
    if not update_data:
        return await get_usuario_by_id(conn, usr_id)

    # HASHEAR LA CONTRASEÑA SI ESTÁ PRESENTE
    if 'contrasena' in update_data:
        update_data['contrasena'] = hash_password(update_data['contrasena'])

    set_clauses = []
    values = []
    param_index = 1

    for key, value in update_data.items():
        # 🔎 Ahora sí permitimos actualizar id_trabajador
        set_clauses.append(f"{key} = ${param_index}")
        values.append(value)
        param_index += 1

    values.append(usr_id)

    query = f"""
    UPDATE usuario 
    SET {', '.join(set_clauses)}
    WHERE id_usuario = ${param_index}
    RETURNING *;
    """

    try:
        record = await conn.fetchrow(query, *values)
        if record:
            return Usuario.from_record(record)
        return None
    except UniqueViolationError:
        raise ValueError("Error de unicidad: El correo, documento o ID de trabajador ya están en uso.")
    except (CheckViolationError, NotNullViolationError) as e:
        raise ValueError(f"Error de validación: La base de datos rechazó los datos. {e.detail}")

# --- 6. Desactivar Usuario (Eliminación Lógica) ---
async def deactivate_usuario(conn: asyncpg.Connection, usr_id: int) -> Optional[Usuario]:
    """Realiza una eliminación lógica (establece estado a 0) de un usuario."""
    deactivate_data = UsuarioUpdate(estado=0)
    return await update_usuario(conn, usr_id, deactivate_data)