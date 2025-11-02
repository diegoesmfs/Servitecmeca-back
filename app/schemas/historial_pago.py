from pydantic import BaseModel
from datetime import date, datetime

class HistorialPagoSchema(BaseModel):
    historial_pago_id: int
    nomina_id: int
    fecha_pago: date
    monto_pagado: float
    metodo_pago: str
    estado: str
    createdat: datetime