from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
from fastapi import Depends
from app.utils.security import verify_token
from app.schemas.usuarios import UsuarioSchema
from app.database import get_connection
from app.schemas.usuarios import UsuarioSchema, UsuarioCreate
import psycopg2

router = APIRouter()




@router.get("/usuarios-publicos")
def usuarios_visibles():
    return {"mensaje": "Esta ruta es pública"}

# Ruta protegida (requiere token válido)
@router.get("/usuarios-protegidos")
def usuarios_autenticados(payload: dict = Depends(verify_token)):
    return {"mensaje": f"Hola {payload['sub']}, tienes acceso autorizado"}

# Ruta solo para administradores
@router.get("/usuarios-admin")
def usuarios_admin(payload: dict = Depends(verify_token)):
    if payload["tipo_usuario"] != 1:
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores")
    return {"mensaje": f"Bienvenido administrador {payload['sub']}"}




@router.get("/usuarios", response_model=list[UsuarioSchema], status_code=status.HTTP_200_OK)
def obtener_usuarios():
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM usuarios WHERE is_deleted = 0")
        resultados = cursor.fetchall()
        if not resultados:
            raise HTTPException(status_code=404, detail="No se encontraron usuarios")
        
        # ✅ Cada fila ya es un dict gracias a RealDictCursor
        usuarios = [UsuarioSchema(**fila) for fila in resultados]
        return usuarios
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar la consulta: {e}")
    finally:
        cursor.close()
        conn.close()


@router.get("/usuarios/{user_id}", response_model=UsuarioSchema)
def obtener_usuario_por_id(user_id: int):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM usuarios WHERE user_id = %s AND is_deleted = 0", (user_id,))
        fila = cursor.fetchone()
        if not fila:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return UsuarioSchema(**fila)  # ✅ Ya es un dict
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar la consulta: {e}")
    finally:
        cursor.close()
        conn.close()


@router.post("/usuarios", response_model=UsuarioSchema, status_code=status.HTTP_201_CREATED)
def crear_usuario(usuario: UsuarioCreate):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")

    cursor = conn.cursor()

    # ✅ Hashear la contraseña antes de guardarla
    hashed_password = pwd_context.hash(usuario.contrasena[:72])



    query = """
        INSERT INTO usuarios (nombre, correo, direccion, telefono, tipo_usuario, estado, contrasena, createdat, is_deleted)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), 0)
        RETURNING *
    """
    try:
        cursor.execute(query, (
            usuario.nombre,
            usuario.correo,
            usuario.direccion,
            usuario.telefono,
            usuario.tipo_usuario,
            usuario.estado,
            hashed_password  # ✅ Aquí va la contraseña hasheada
        ))
        nuevo_usuario = cursor.fetchone()
        conn.commit()
        return UsuarioSchema(**nuevo_usuario)
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear el usuario: {e}")
    finally:
        cursor.close()
        conn.close()


@router.put("/usuarios/{user_id}", response_model=UsuarioSchema)
def actualizar_usuario(user_id: int, usuario: UsuarioCreate):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")

    cursor = conn.cursor()

    # ✅ Hashear la nueva contraseña antes de actualizar
    hashed_password = pwd_context.hash(usuario.contrasena[:72])

    query = """
        UPDATE usuarios
        SET nombre = %s, correo = %s, direccion = %s, telefono = %s,
            tipo_usuario = %s, estado = %s, contrasena = %s
        WHERE user_id = %s AND is_deleted = 0
        RETURNING *
    """
    try:
        cursor.execute(query, (
            usuario.nombre,
            usuario.correo,
            usuario.direccion,
            usuario.telefono,
            usuario.tipo_usuario,
            usuario.estado,
            hashed_password,  # ✅ contraseña actualizada
            user_id
        ))
        actualizado = cursor.fetchone()
        if not actualizado:
            raise HTTPException(status_code=404, detail="Usuario no encontrado para actualizar")
        conn.commit()
        return UsuarioSchema(**actualizado)
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar el usuario: {e}")
    finally:
        cursor.close()
        conn.close()


@router.delete("/usuarios/{user_id}", status_code=status.HTTP_200_OK)
def eliminar_usuario(user_id: int):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")

    cursor = conn.cursor()
    query = "UPDATE usuarios SET is_deleted = 1 WHERE user_id = %s"
    try:
        cursor.execute(query, (user_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado para eliminar")
        conn.commit()
        return {"detail": "Usuario eliminado correctamente"}
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar el usuario: {e}")
    finally:
        cursor.close()
        conn.close()



