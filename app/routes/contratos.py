from fastapi import APIRouter, HTTPException, status
from app.schemas.contrato import ContratoSchema, ContratoCreate
from app.database import get_connection
import psycopg2

router = APIRouter()

# 🧩 Listar todos los contratos
@router.get("/contratos", response_model=list[ContratoSchema])
def obtener_contratos():
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM contratos WHERE is_deleted = 0")
        columnas = [desc[0] for desc in cursor.description]
        resultados = cursor.fetchall()
        if not resultados:
            raise HTTPException(status_code=404, detail="No se encontraron contratos")
        return [ContratoSchema(**dict(zip(columnas, fila))) for fila in resultados]
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener contratos: {e}")
    finally:
        cursor.close()
        conn.close()

# 🔍 Obtener contrato por ID
@router.get("/contratos/{contract_id}", response_model=ContratoSchema)
def obtener_contrato_por_id(contract_id: int):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM contratos WHERE contract_id = %s AND is_deleted = 0", (contract_id,))
        fila = cursor.fetchone()
        if not fila:
            raise HTTPException(status_code=404, detail="Contrato no encontrado")
        columnas = [desc[0] for desc in cursor.description]
        return ContratoSchema(**dict(zip(columnas, fila)))
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener contrato: {e}")
    finally:
        cursor.close()
        conn.close()

# ✨ Crear nuevo contrato
@router.post("/contratos", response_model=ContratoSchema, status_code=status.HTTP_201_CREATED)
def crear_contrato(contrato: ContratoCreate):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()

    # Validación previa: ¿existe el trabajador?
    cursor.execute("SELECT 1 FROM trabajadores WHERE worker_id = %s AND is_deleted = 0", (contrato.workerid,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="El trabajador indicado no existe o fue eliminado")

    query = """
        INSERT INTO contratos (
            workerid, tipo_contrato, fecha_inicio, fecha_fin,
            salario_base, jornada_laboral, estado,
            createdat, is_deleted
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), 0)
        RETURNING *
    """
    try:
        cursor.execute(query, (
            contrato.workerid,
            contrato.tipo_contrato,
            contrato.fecha_inicio,
            contrato.fecha_fin,
            contrato.salario_base,
            contrato.jornada_laboral,
            contrato.estado
        ))
        nuevo = cursor.fetchone()
        columnas = [desc[0] for desc in cursor.description]
        conn.commit()
        return ContratoSchema(**dict(zip(columnas, nuevo)))
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear contrato: {e}")
    finally:
        cursor.close()
        conn.close()

# 🛠️ Actualizar contrato existente
@router.put("/contratos/{contract_id}", response_model=ContratoSchema)
def actualizar_contrato(contract_id: int, contrato: ContratoCreate):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    query = """
        UPDATE contratos
        SET workerid = %s, tipo_contrato = %s, fecha_inicio = %s, fecha_fin = %s,
            salario_base = %s, jornada_laboral = %s, estado = %s
        WHERE contract_id = %s AND is_deleted = 0
        RETURNING *
    """
    try:
        cursor.execute(query, (
            contrato.workerid,
            contrato.tipo_contrato,
            contrato.fecha_inicio,
            contrato.fecha_fin,
            contrato.salario_base,
            contrato.jornada_laboral,
            contrato.estado,
            contract_id
        ))
        actualizado = cursor.fetchone()
        if not actualizado:
            raise HTTPException(status_code=404, detail="Contrato no encontrado para actualizar")
        columnas = [desc[0] for desc in cursor.description]
        conn.commit()
        return ContratoSchema(**dict(zip(columnas, actualizado)))
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar contrato: {e}")
    finally:
        cursor.close()
        conn.close()

# 🗑️ Eliminación lógica de contrato
@router.delete("/contratos/{contract_id}", status_code=status.HTTP_200_OK)
def eliminar_contrato(contract_id: int):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    query = "UPDATE contratos SET is_deleted = 1 WHERE contract_id = %s"
    try:
        cursor.execute(query, (contract_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Contrato no encontrado para eliminar")
        conn.commit()
        return {"detail": "Contrato eliminado correctamente"}
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar contrato: {e}")
    finally:
        cursor.close()
        conn.close()
