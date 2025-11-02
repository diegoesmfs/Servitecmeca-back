from fastapi import APIRouter, HTTPException, status
from app.schemas.cargo import CargoSchema, CargoCreate
from app.database import get_connection
import psycopg2

router = APIRouter()

# 🧩 Listar todos los cargos
@router.get("/cargos", response_model=list[CargoSchema])
def obtener_cargos():
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM cargos WHERE is_deleted = 0")
        resultados = cursor.fetchall()
        if not resultados:
            raise HTTPException(status_code=404, detail="No se encontraron cargos")
        return [CargoSchema(**fila) for fila in resultados]
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener cargos: {e}")
    finally:
        cursor.close()
        conn.close()

# 🔍 Obtener un cargo por ID
@router.get("/cargos/{position_id}", response_model=CargoSchema)
def obtener_cargo_por_id(position_id: int):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM cargos WHERE position_id = %s AND is_deleted = 0", (position_id,))
        fila = cursor.fetchone()
        if not fila:
            raise HTTPException(status_code=404, detail="Cargo no encontrado")
        return CargoSchema(**fila)
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener cargo: {e}")
    finally:
        cursor.close()
        conn.close()

# ✨ Crear un nuevo cargo
@router.post("/cargos", response_model=CargoSchema, status_code=status.HTTP_201_CREATED)
def crear_cargo(cargo: CargoCreate):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    query = """
        INSERT INTO cargos (nombre, descripcion, sueldo_base, departmento_id, createdat, is_deleted)
        VALUES (%s, %s, %s, %s, NOW(), 0)
        RETURNING *
    """
    try:
        cursor.execute(query, (
            cargo.nombre,
            cargo.descripcion,
            cargo.sueldo_base,
            cargo.departmento_id
        ))
        nuevo = cursor.fetchone()
        conn.commit()
        return CargoSchema(**nuevo)
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear cargo: {e}")
    finally:
        cursor.close()
        conn.close()

# 🛠️ Actualizar un cargo existente
@router.put("/cargos/{position_id}", response_model=CargoSchema)
def actualizar_cargo(position_id: int, cargo: CargoCreate):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    query = """
        UPDATE cargos
        SET nombre = %s, descripcion = %s, sueldo_base = %s, departmento_id = %s
        WHERE position_id = %s AND is_deleted = 0
        RETURNING *
    """
    try:
        cursor.execute(query, (
            cargo.nombre,
            cargo.descripcion,
            cargo.sueldo_base,
            cargo.departmento_id,
            position_id
        ))
        actualizado = cursor.fetchone()
        if not actualizado:
            raise HTTPException(status_code=404, detail="Cargo no encontrado para actualizar")
        conn.commit()
        return CargoSchema(**actualizado)
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar cargo: {e}")
    finally:
        cursor.close()
        conn.close()

# 🗑️ Eliminación lógica de un cargo
@router.delete("/cargos/{position_id}", status_code=status.HTTP_200_OK)
def eliminar_cargo(position_id: int):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    query = "UPDATE cargos SET is_deleted = 1 WHERE position_id = %s"
    try:
        cursor.execute(query, (position_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Cargo no encontrado para eliminar")
        conn.commit()
        return {"detail": "Cargo eliminado correctamente"}
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar cargo: {e}")
    finally:
        cursor.close()
        conn.close()
