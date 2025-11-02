from pydantic import BaseModel
from datetime import datetime

class AjusteNominaSchema(BaseModel):
    ajuste_id: int
    nomina_id: int
    tipo_ajuste: str
    descripcion: str
    monto: float
    createdat: datetime
    is_deleted: int