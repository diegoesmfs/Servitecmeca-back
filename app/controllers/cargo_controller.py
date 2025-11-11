from asyncpg import Connection, exceptions
from fastapi import HTTPException
from app.schemas.cargo import CargoCreate, CargoOut, CargoUpdate
from typing import List

# NOTA: Asumo que la función get_connection() ya existe en app/db/connection.py

# ----------------------------------------------------------------------
# C R E A T E
# ----------------------------------------------------------------------
async def create_cargo(cargo_data: CargoCreate, conn: Connection) -> CargoOut:
    # Validación manual del CHECK_RANGO_SALARIAL
    if cargo_data.salario_base > cargo_data.salario_maximo:
        raise HTTPException(
            status_code=400,
            detail="El salario máximo debe ser mayor o igual al salario base, ¡no te peles!"
        )

    query = """
    INSERT INTO public.cargos (id_cargo, titulo, descripcion, nivel, salario_base, salario_maximo, competencias)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    RETURNING *;
    """
    
    try:
        record = await conn.fetchrow(
            query, 
            cargo_data.id_cargo, 
            cargo_data.titulo, 
            cargo_data.descripcion, 
            cargo_data.nivel, 
            cargo_data.salario_base, 
            cargo_data.salario_maximo, 
            cargo_data.competencias
        )
        
        # Convertimos asyncpg.Record a dict para que pydantic lo valide correctamente
        return CargoOut.model_validate(dict(record)) if record else None
        
    except exceptions.UniqueViolationError:
        raise HTTPException(
            status_code=400,
            detail="Ese ID de cargo o el Título ya están registrados, ¡intenta con otro!"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error del servidor al crear el cargo: {e}")

# ----------------------------------------------------------------------
# R E A D (Listar todos)
# ----------------------------------------------------------------------
async def list_cargos(conn: Connection) -> List[CargoOut]:
    query = "SELECT * FROM public.cargos WHERE estado = 1 ORDER BY titulo;"
    records = await conn.fetch(query)
    
    # Convertimos cada asyncpg.Record a dict antes de validar con pydantic
    return [CargoOut.model_validate(dict(record)) for record in records]

# ----------------------------------------------------------------------
# R E A D (Por ID)
# ----------------------------------------------------------------------
async def get_cargo_by_id(cargo_id: str, conn: Connection) -> CargoOut:
    query = "SELECT * FROM public.cargos WHERE id_cargo = $1;"
    record = await conn.fetchrow(query, cargo_id)
    
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Vergación, el cargo con ID '{cargo_id}' no existe."
        )
    
    # Convertimos asyncpg.Record a dict antes de validar con pydantic
    return CargoOut.model_validate(dict(record))

# ----------------------------------------------------------------------
# U P D A T E
# ----------------------------------------------------------------------
async def update_cargo(cargo_id: str, cargo_data: CargoUpdate, conn: Connection) -> CargoOut:
    # Obtenemos el cargo actual (y verifica si existe, si no, lanza 404)
    current_cargo = await get_cargo_by_id(cargo_id, conn)
    
    # Prepara el diccionario de datos con solo los campos enviados
    update_data = cargo_data.model_dump(exclude_unset=True) 

    # Aplicamos los valores actuales si no se especificaron (para la validación)
    salario_base = update_data.get('salario_base', current_cargo.salario_base)
    salario_maximo = update_data.get('salario_maximo', current_cargo.salario_maximo)
    
    # Validación de rango salarial
    if salario_base is not None and salario_maximo is not None and salario_base > salario_maximo:
        raise HTTPException(
            status_code=400,
            detail="El salario máximo debe ser mayor o igual al salario base en la actualización."
        )
        
    # Construcción dinámica del query SQL
    fields = []
    values = []
    for key, value in update_data.items():
        fields.append(f"{key} = ${len(values) + 1}")
        values.append(value)
        
    if not fields:
        return current_cargo 

    values.append(cargo_id) # ID del cargo para la cláusula WHERE
    set_clause = ", ".join(fields)
    query = f"""
    UPDATE public.cargos 
    SET {set_clause}
    WHERE id_cargo = ${len(values)}
    RETURNING *;
    """

    try:
        updated_record = await conn.fetchrow(query, *values)
        # Convertimos asyncpg.Record a dict antes de validar con pydantic
        return CargoOut.model_validate(dict(updated_record))
        
    except exceptions.UniqueViolationError:
        raise HTTPException(
            status_code=400,
            detail="Ese Título ya lo tiene otro cargo, ¡buscáte otro!"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error del servidor al actualizar: {e}")

# ----------------------------------------------------------------------
# D E L E T E (Desactivar/Estado=0)
# ----------------------------------------------------------------------
async def delete_cargo(cargo_id: str, conn: Connection) -> dict:
    # Verificamos que exista (usa la función corregida)
    await get_cargo_by_id(cargo_id, conn)

    query = """
    UPDATE public.cargos 
    SET estado = 0 
    WHERE id_cargo = $1;
    """
    
    await conn.execute(query, cargo_id)
    
    return {"message": f"El cargo con ID '{cargo_id}' ha sido desactivado (estado=0). ¡Chao pescao!"}