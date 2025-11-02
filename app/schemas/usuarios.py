from pydantic import BaseModel
from datetime import datetime

class UsuarioSchema(BaseModel):
    user_id: int
    nombre: str
    correo: str
    direccion: str
    telefono: str
    tipo_usuario: int
    estado: int
    createdat: datetime
    is_deleted: int

class UsuarioCreate(BaseModel):
    nombre: str
    correo: str
    direccion: str
    telefono: str
    tipo_usuario: int
    estado: int

