# controllers/nomina_general_controller.py
from typing import List, Optional
import asyncpg
from asyncpg.exceptions import UniqueViolationError, ForeignKeyViolationError, CheckViolationError, NotNullViolationError
from app.schemas.nomina_general import NominaGeneralCreate, NominaGeneralUpdate
from app.models.nomina_general import NominaGeneral
# Asegúrate de que esta importación sea correcta en tu proyecto
from app.controllers import nomina_detalle_controller 

# --- 1. Crear Nómina General (CON DETALLES AUTOMÁTICOS) ---
async def create_nomina_general(conn: asyncpg.Connection, nomina_in: NominaGeneralCreate) -> Optional[NominaGeneral]:
    query = """
    INSERT INTO nomina_general (
        id_nomina, periodo, id_departamento, fecha_pago, presupuesto_utilizado, 
        impuesto_renta_total, seguro_social_total, estado, estado_pago, observaciones
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    RETURNING *;
    """
    
    values = (
        nomina_in.id_nomina, nomina_in.periodo, nomina_in.id_departamento, nomina_in.fecha_pago, 
        nomina_in.presupuesto_utilizado, nomina_in.impuesto_renta_total, nomina_in.seguro_social_total, 
        nomina_in.estado, nomina_in.estado_pago, nomina_in.observaciones
    )
    
    # Se usa una transacción para garantizar la atomicidad: si falla el detalle, falla la general.
    async with conn.transaction():
        try:
            # 1. Insertar la Nómina General
            record = await conn.fetchrow(query, *values)
            
            if record:
                nomina_general_obj = NominaGeneral.from_record(record)
                
                # 2. LLAMAR A LA FUNCIÓN DE CREACIÓN DE DETALLES (ubicada en nomina_detalle_controller)
                detalles = await nomina_detalle_controller.create_detalles_for_nomina(
                    conn, 
                    nomina_general_obj.id_nomina, 
                    nomina_general_obj.id_departamento
                )
                
                if not detalles:
                     # Opcional: Levantar una excepción si no hay trabajadores para evitar una nómina vacía
                     print(f"Advertencia: Nomina {nomina_general_obj.id_nomina} creada, pero sin detalles (0 trabajadores activos).")
                
                return nomina_general_obj

        except UniqueViolationError:
            raise ValueError("Error de unicidad: El ID de nómina ya existe.")
        except ForeignKeyViolationError:
            raise ValueError("Error de clave foránea: El ID de departamento no existe.")
        except (CheckViolationError, NotNullViolationError) as e:
            # Esta excepción capturará errores de la base de datos (Ej: CheckValido)
            raise ValueError(f"Error de validación: La base de datos rechazó los datos. {e.detail}")
    
    return None


# --- 2. Listar Nóminas Generales (con Paginación y Filtrado) ---
async def list_nominas_generales(
    conn: asyncpg.Connection, 
    skip: int = 0, 
    limit: int = 100,
    id_departamento: Optional[str] = None,
    estado_pago: Optional[int] = None
) -> List[NominaGeneral]:
    """Retorna la lista de nóminas generales, con paginación y filtros."""
    
    where_clauses = []
    values = []
    param_index = 1
    
    if id_departamento:
        where_clauses.append(f"id_departamento = ${param_index}")
        values.append(id_departamento)
        param_index += 1

    if estado_pago is not None:
        where_clauses.append(f"estado_pago = ${param_index}")
        values.append(estado_pago)
        param_index += 1

    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    query = f"""
    SELECT * FROM nomina_general 
    {where_sql} 
    ORDER BY periodo DESC, fecha_pago DESC
    LIMIT ${param_index} 
    OFFSET ${param_index + 1};
    """
    values.extend([limit, skip])

    rows = await conn.fetch(query, *values)
    return [NominaGeneral.from_record(r) for r in rows]

# --- 3. Obtener una Nómina General por ID ---
async def get_nomina_general_by_id(conn: asyncpg.Connection, nomina_id: str) -> Optional[NominaGeneral]:
    query = "SELECT * FROM nomina_general WHERE id_nomina = $1;"
    record = await conn.fetchrow(query, nomina_id)
    return NominaGeneral.from_record(record) if record else None

# --- 4. Actualizar Nómina General ---
async def update_nomina_general(conn: asyncpg.Connection, nomina_id: str, nomina_in: NominaGeneralUpdate) -> Optional[NominaGeneral]:
    update_data = nomina_in.model_dump(exclude_unset=True)
    if not update_data:
        return await get_nomina_general_by_id(conn, nomina_id)
        
    set_clauses = []
    values = []
    param_index = 1
    
    for key, value in update_data.items():
        set_clauses.append(f"{key} = ${param_index}")
        values.append(value)
        param_index += 1

    values.append(nomina_id)
    
    query = f"""
    UPDATE nomina_general 
    SET {', '.join(set_clauses)}
    WHERE id_nomina = ${param_index}
    RETURNING *;
    """

    try:
        record = await conn.fetchrow(query, *values)
        if record:
            return NominaGeneral.from_record(record)
        return None
    except ForeignKeyViolationError:
        raise ValueError("Error de clave foránea: El ID de departamento no existe.")
    except (CheckViolationError, NotNullViolationError) as e:
        raise ValueError(f"Error de validación: La base de datos rechazó los datos. {e.detail}")