# routes/usuario.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
import asyncpg
from typing import List, Optional
from app.schemas.usuario import LoginResponse, UsuarioCreate, UsuarioUpdate, UsuarioOut, UsuarioLogin, TokenResponse
from app.controllers import usuario_controller
# Asegúrate de que esta ruta sea correcta para tu proyecto:
from app.db.connection import get_connection 

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

# --- Endpoints CRUD Básicos ---

# POST /usuarios
@router.post("/", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
async def create_new_usuario(usr_in: UsuarioCreate, conn: asyncpg.Connection = Depends(get_connection)):
    """Crea un nuevo usuario (La contraseña se hashea en el controlador)."""
    try:
        usuario = await usuario_controller.create_usuario(conn, usr_in)
        # Se retorna el UsuarioOut que no incluye la contraseña
        return usuario
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {e}")

# GET /usuarios
@router.get("/", response_model=List[UsuarioOut])
async def list_all_usuarios(
    conn: asyncpg.Connection = Depends(get_connection),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, gt=0, le=500),
    activo: Optional[bool] = Query(None, description="Filtrar por estado.")
):
    """Obtiene la lista de usuarios con opciones de paginación y filtro por estado."""
    return await usuario_controller.list_usuarios(conn, skip=skip, limit=limit, activo=activo)

# GET /usuarios/{id}
@router.get("/{usr_id}", response_model=UsuarioOut)
async def get_single_usuario(usr_id: int, conn: asyncpg.Connection = Depends(get_connection)):
    """Obtiene los detalles de un usuario por su ID."""
    usuario = await usuario_controller.get_usuario_by_id(conn, usr_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    # Retorna UsuarioOut que excluye la contraseña
    return usuario

# PUT /usuarios/{id}
@router.put("/{usr_id}", response_model=UsuarioOut)
async def update_existing_usuario(
    usr_id: int, 
    usr_update: UsuarioUpdate, 
    conn: asyncpg.Connection = Depends(get_connection)
):
    """Actualiza campos de un usuario existente (incluida la contraseña, que se hashea)."""
    try:
        usuario = await usuario_controller.update_usuario(conn, usr_id, usr_update)
        if not usuario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        # Retorna UsuarioOut que excluye la contraseña
        return usuario
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

# DELETE /usuarios/{id} (Eliminación Lógica)
@router.delete("/{usr_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_usuario(usr_id: int, conn: asyncpg.Connection = Depends(get_connection)):
    """Deshabilita lógicamente un usuario (establece estado a 0)."""
    try:
        usuario = await usuario_controller.deactivate_usuario(conn, usr_id)
        if not usuario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al deshabilitar: {e}")

# --- Endpoint de Autenticación (Ejemplo) ---

@router.post("/login", response_model=LoginResponse)
async def login_for_access_token(user_in: UsuarioLogin, conn: asyncpg.Connection = Depends(get_connection)):
    """Verifica credenciales de usuario."""
    usuario = await usuario_controller.get_usuario_by_correo(conn, user_in.correo)
    
    if not usuario or not usuario_controller.verify_password(user_in.contrasena, usuario.contrasena):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generar token JWT y devolverlo
    from app.core.security import create_access_token
    token_data = {
    "sub": usuario.correo,  
    "contrasena": usuario.contrasena,    # usuario principal
    "id_usuario": usuario.id_usuario,
    "nombre": usuario.nombre,
    "rol": usuario.rol,
    "id_trabajador": usuario.id_trabajador,
    "estado": usuario.estado,
}

    access_token = create_access_token(token_data)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        
    }