from pydantic import BaseModel
from datetime import datetime

class DepartamentoSchema(BaseModel):
    departmento_id: int
    nombre: str
    descripcion: str
    createdat: datetime
    is_deleted: int

class DepartamentoCreate(BaseModel):
    nombre: str
    descripcion: str