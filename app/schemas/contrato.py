from pydantic import BaseModel
from datetime import date, datetime

class ContratoSchema(BaseModel):
    contracto_id: int
    trabajadorid: int
    tipo_contrato: str
    fecha_inicio: date
    fecha_fin: date
    salario_base: float
    jornada_laboral: int
    estado: str
    createdat: datetime
    is_deleted: int