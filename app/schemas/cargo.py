from pydantic import BaseModel
from datetime import datetime

class CargoSchema(BaseModel):
    posicion_id: int
    nombre: str
    descripcion: str
    sueldo_base: float
    departmento_id: int
    createdat: datetime
    is_deleted: int

class CargoCreate(BaseModel):
    nombre: str
    descripcion: str
    sueldo_base: float
    departmento_id: int