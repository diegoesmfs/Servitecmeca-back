from pydantic import BaseModel
from datetime import datetime, date

class TrabajadorSchema(BaseModel):
    trabajador_id: int
    nombre: str
    correo: str
    documento: str  
    fecha_nacimiento: date
    estado_civil: str
    direccion: str
    telefono: str
    cuenta_bancaria: str
    position_id: int
    is_active: bool
    createdat: datetime
    is_deleted: int

class TrabajadorCreate(BaseModel):
    nombre: str
    correo: str
    documento: str  
    fecha_nacimiento: date
    estado_civil: str
    direccion: str
    telefono: str
    cuenta_bancaria: str
    position_id: int
    estado: int  