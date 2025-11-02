from fastapi import APIRouter, HTTPException, status
from app.schemas.trabajador import TrabajadorSchema, TrabajadorCreate
from app.database import get_connection
import psycopg2

router = APIRouter()

@router.get("/trabajadores", response_model=list[TrabajadorSchema])
def obtener_trabajadores():
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM trabajadores WHERE is_deleted = 0")
        resultados = cursor.fetchall()
        if not resultados:
            raise HTTPException(status_code=404, detail="No se encontraron trabajadores")
        return [TrabajadorSchema(**fila) for fila in resultados]
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener trabajadores: {e}")
    finally:
        cursor.close()
        conn.close()

@router.post("/trabajadores", response_model=TrabajadorSchema, status_code=status.HTTP_201_CREATED)
def crear_trabajador(trabajador: TrabajadorCreate):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    query = """
        INSERT INTO trabajadores (
            nombre, correo, documento, fecha_nacimiento, estado_civil,
            direccion, telefono, cuenta_bancaria, posicion_id, is_active,
            createdat, is_deleted
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, true, NOW(), 0)
        RETURNING *
    """
    try:
        cursor.execute(query, (
            trabajador.nombre,
            trabajador.correo,
            trabajador.documento,
            trabajador.fecha_nacimiento,
            trabajador.estado_civil,
            trabajador.direccion,
            trabajador.telefono,
            trabajador.cuenta_bancaria,
            trabajador.posicion_id
        ))
        nuevo = cursor.fetchone()
        conn.commit()
        return TrabajadorSchema(**nuevo)
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear trabajador: {e}")
    finally:
        cursor.close()
        conn.close()

@router.put("/trabajadores/{trabajador_id}", response_model=TrabajadorSchema)
def actualizar_trabajador(trabajador_id: int, trabajador: TrabajadorCreate):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    query = """
        UPDATE trabajadores
        SET nombre = %s, correo = %s, documento = %s, fecha_nacimiento = %s,
            estado_civil = %s, direccion = %s, telefono = %s,
            cuenta_bancaria = %s, posicion_id = %s
        WHERE trabajador_id = %s AND is_deleted = 0
        RETURNING *
    """
    try:
        cursor.execute(query, (
            trabajador.nombre,
            trabajador.correo,
            trabajador.documento,
            trabajador.fecha_nacimiento,
            trabajador.estado_civil,
            trabajador.direccion,
            trabajador.telefono,
            trabajador.cuenta_bancaria,
            trabajador.posicion_id,
            trabajador_id
        ))
        actualizado = cursor.fetchone()
        if not actualizado:
            raise HTTPException(status_code=404, detail="Trabajador no encontrado para actualizar")
        conn.commit()
        return TrabajadorSchema(**actualizado)
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar trabajador: {e}")
    finally:
        cursor.close()
        conn.close()

        
@router.put("/trabajadores/{trabajador_id}", response_model=TrabajadorSchema)
def actualizar_trabajador(trabajador_id: int, trabajador: TrabajadorCreate):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    query = """
        UPDATE trabajadores
        SET nombre = %s, cedula = %s, fecha_nacimiento = %s, cargo = %s,
            salario = %s, estado = %s
        WHERE trabajador_id = %s AND is_deleted = 0
        RETURNING *
    """
    try:
        cursor.execute(query, (
            trabajador.nombre,
            trabajador.cedula,
            trabajador.fecha_nacimiento,
            trabajador.cargo,
            trabajador.salario,
            trabajador.estado,
            trabajador_id
        ))
        actualizado = cursor.fetchone()
        if not actualizado:
            raise HTTPException(status_code=404, detail="Trabajador no encontrado para actualizar")
        conn.commit()
        return TrabajadorSchema(**actualizado)
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar trabajador: {e}")
    finally:
        cursor.close()
        conn.close()

@router.delete("/trabajadores/{trabajador_id}", status_code=status.HTTP_200_OK)
def eliminar_trabajador(trabajador_id: int):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    query = "UPDATE trabajadores SET is_deleted = 1 WHERE trabajador_id = %s"
    try:
        cursor.execute(query, (trabajador_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Trabajador no encontrado para eliminar")
        conn.commit()
        return {"detail": "Trabajador eliminado correctamente"}
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar trabajador: {e}")
    finally:
        cursor.close()
        conn.close()