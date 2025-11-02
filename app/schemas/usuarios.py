from pydantic import BaseModel
from datetime import datetime
from pydantic import BaseModel, Field
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
    contrasena: str  # ✅ actualizado


