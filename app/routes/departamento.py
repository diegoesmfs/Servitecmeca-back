from fastapi import APIRouter, HTTPException, status
from app.schemas.departamento import DepartamentoSchema, DepartamentoCreate
from app.database import get_connection
import psycopg2

router = APIRouter()

# 🧩 Listar todos los departamentos
@router.get("/departamentos", response_model=list[DepartamentoSchema])
def obtener_departamentos():
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM departamentos WHERE is_deleted = 0")
        resultados = cursor.fetchall()
        if not resultados:
            raise HTTPException(status_code=404, detail="No se encontraron departamentos")
        return [DepartamentoSchema(**fila) for fila in resultados]
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener departamentos: {e}")
    finally:
        cursor.close()
        conn.close()

# 🔍 Obtener un departamento por ID
@router.get("/departamentos/{departmento_id}", response_model=DepartamentoSchema)
def obtener_departamento_por_id(departmento_id: int):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM departamentos WHERE departmento_id = %s AND is_deleted = 0", (departmento_id,))
        fila = cursor.fetchone()
        if not fila:
            raise HTTPException(status_code=404, detail="Departamento no encontrado")
        return DepartamentoSchema(**fila)
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener departamento: {e}")
    finally:
        cursor.close()
        conn.close()

# ✨ Crear un nuevo departamento
@router.post("/departamentos", response_model=DepartamentoSchema, status_code=status.HTTP_201_CREATED)
def crear_departamento(departamento: DepartamentoCreate):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    query = """
        INSERT INTO departamentos (nombre, descripcion, createdat, is_deleted)
        VALUES (%s, %s, NOW(), 0)
        RETURNING *
    """
    try:
        cursor.execute(query, (
            departamento.nombre,
            departamento.descripcion
        ))
        nuevo = cursor.fetchone()
        conn.commit()
        return DepartamentoSchema(**nuevo)
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear departamento: {e}")
    finally:
        cursor.close()
        conn.close()

# 🛠️ Actualizar un departamento existente
@router.put("/departamentos/{departmento_id}", response_model=DepartamentoSchema)
def actualizar_departamento(departmento_id: int, departamento: DepartamentoCreate):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    query = """
        UPDATE departamentos
        SET nombre = %s, descripcion = %s
        WHERE departmento_id = %s AND is_deleted = 0
        RETURNING *
    """
    try:
        cursor.execute(query, (
            departamento.nombre,
            departamento.descripcion,
            departmento_id
        ))
        actualizado = cursor.fetchone()
        if not actualizado:
            raise HTTPException(status_code=404, detail="Departamento no encontrado para actualizar")
        conn.commit()
        return DepartamentoSchema(**actualizado)
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar departamento: {e}")
    finally:
        cursor.close()
        conn.close()

# 🗑️ Eliminación lógica de un departamento
@router.delete("/departamentos/{departmento_id}", status_code=status.HTTP_200_OK)
def eliminar_departamento(departmento_id: int):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    query = "UPDATE departamentos SET is_deleted = 1 WHERE departmento_id = %s"
    try:
        cursor.execute(query, (departmento_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Departamento no encontrado para eliminar")
        conn.commit()
        return {"detail": "Departamento eliminado correctamente"}
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar departamento: {e}")
    finally:
        cursor.close()
        conn.close()
