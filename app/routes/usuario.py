from fastapi import APIRouter, Depends, HTTPException, status, Query
# 🌟 Importaciones para PDF
from fastapi.responses import Response
from app.controllers import pdf_controller 
from app.controllers.pdf_controller import PDFColumn 
# -------------------------
import asyncpg
from typing import List, Optional
from app.schemas.usuario import LoginResponse, UsuarioCreate, UsuarioUpdate, UsuarioOut, UsuarioLogin, TokenResponse
from app.controllers import usuario_controller
# Asegúrate de que esta ruta sea correcta para tu proyecto:
from app.db.connection import get_connection 
from app.core.security import create_access_token

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

# 🌟🌟🌟 NUEVA RUTA: Generar PDF de Usuarios 🌟🌟🌟
@router.get("/imprimir/pdf", response_class=Response)
async def get_usuarios_pdf(
    conn: asyncpg.Connection = Depends(get_connection),
    activo: Optional[bool] = Query(None, description="Filtrar por estado.")
):
    """
    Genera y devuelve un informe PDF con la lista de usuarios, filtrada por estado.
    """
    try:
        # 1. Obtener la lista de usuarios
        usuarios = await usuario_controller.list_usuarios(
            conn, 
            skip=0, 
            limit=1000000, 
            activo=activo
        )
        
        if not usuarios:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron usuarios con esos filtros.")

        # 2. Convertir los objetos a una lista de diccionarios
        # Importante: Utilizamos el esquema UsuarioOut para serializar y obtener los campos enriquecidos (como nombre_t_trabajador)
        data_to_print = [
            UsuarioOut.model_validate(usr).model_dump(mode='json', by_alias=True) 
            for usr in usuarios
        ]
        
        # 3. Definición de las columnas para el reporte (A3 Landscape = ~400mm de ancho útil)
        columns_definition = [
            PDFColumn(key='id_usuario', header='ID', width=15, align='C'),
            PDFColumn(key='nombre', header='Nombre Usuario', width=40, align='L'),
            PDFColumn(key='documento', header='Documento', width=30, align='L'),
            PDFColumn(key='correo', header='Correo Electrónico', width=60, align='L'),
            PDFColumn(key='rol', header='Rol', width=25, align='C'),
            PDFColumn(key='nombre_t_trabajador', header='Trabajador Asignado', width=60, align='L',
                      formatter=lambda v: str(v) if v else 'N/A'),
            PDFColumn(key='creado', header='F. Creación', width=30, align='C',
                      formatter=lambda v: str(v).split('T')[0] if v else 'N/A'),
            PDFColumn(key='estado', header='Estado', width=20, align='C',
                      formatter=lambda v: "ACTIVO" if v == 1 else "INACTIVO"),
        ]
        # Suma total de anchos: 15+40+30+60+25+60+30+20 = 280 mm.
        
        estado_texto = "ACTIVOS" if activo is True else "INACTIVOS" if activo is False else "TODOS"
        report_title = f"LISTADO DE USUARIOS ({estado_texto})"

        # 4. Generar el contenido binario del PDF
        pdf_content = await pdf_controller.generate_generic_pdf(
            data=data_to_print, 
            columns=columns_definition,
            report_title=report_title
        )

        # 5. Devolver el PDF
        filename = "reporte_usuarios.pdf"
        
        return Response(
            content=pdf_content, 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error al generar el PDF: {e}"
        )


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
@router.patch("/{usr_id}", status_code=status.HTTP_204_NO_CONTENT)
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
    print(f"🔐 Login attempt for: {user_in.correo}")
    
    usuario = await usuario_controller.get_usuario_by_correo(conn, user_in.correo)
    print(f"👤 User found: {usuario is not None}")
    
    if not usuario:
        print("❌ User not found in database")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"🔑 Verifying password...")
    
    # Usa la función verify_password modificada que acepta texto plano
    from app.core.security import verify_password
    password_valid = verify_password(user_in.contrasena, usuario.contrasena)
    
    print(f"🔑 Password valid: {password_valid}")
    
    if not password_valid:
        print("❌ Password verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print("✅ Login successful")
    
    # Generar token JWT y devolverlo
    from app.core.security import create_access_token
    token_data = {
    "sub": usuario.correo,  
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