# schemas/usuario.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal
from datetime import datetime

# Opciones para el rol (basado en CHECK (rol::text = ANY (ARRAY['administrador', 'usuario'])))
RolUsuario = Literal["administrador", "usuario"]

class UsuarioCreate(BaseModel):
    nombre: str = Field(..., max_length=100)
    correo: EmailStr = Field(..., max_length=150)
    documento: str = Field(..., max_length=20)
    id_trabajador: int = Field(..., gt=0, description="Debe ser un id_trabajador existente.")
    rol: RolUsuario = Field(..., description="Rol del usuario: 'administrador' o 'usuario'")
    # Contraseña en texto plano, debe ser hasheada en el controlador
    contrasena: str = Field(..., min_length=8, max_length=255) 
    estado: Optional[int] = Field(1, ge=0, le=1) 

class UsuarioUpdate(BaseModel):
    # No se permite cambiar el id_trabajador una vez asignado
    nombre: Optional[str] = Field(None, max_length=100)
    correo: Optional[EmailStr] = Field(None, max_length=150)
    documento: Optional[str] = Field(None, max_length=20)
    rol: Optional[RolUsuario] = None
    # Permite actualizar la contraseña
    contrasena: Optional[str] = Field(None, min_length=8, max_length=255) 
    estado: Optional[int] = Field(None, ge=0, le=1) 

class UsuarioOut(BaseModel):
    id_usuario: int
    nombre: str
    correo: str
    documento: str
    id_trabajador: int
    rol: str
    estado: int
    creado: datetime
    # LA CONTRASEÑA (contrasena) NUNCA DEBE SER RETORNADA EN EL OUTPUT

    class Config:
        from_attributes = True

# Esquema para login o autenticación
class UsuarioLogin(BaseModel):
    correo: EmailStr
    contrasena: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
