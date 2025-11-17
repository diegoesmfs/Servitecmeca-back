# schemas/nomina_detalle.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class NominaDetalleCreate(BaseModel):
    id_detalle_nomina: str = Field(..., max_length=20)
    id_nomina: str = Field(..., max_length=20)
    id_trabajador: int
    salario_base: Decimal = Field(..., gt=0)
    total_remuneraciones: Optional[Decimal] = Field(0.00, ge=0)
    total_deducciones: Optional[Decimal] = Field(0.00, ge=0)
    salario_neto: Optional[Decimal] # Se puede calcular en el controlador
    estado: Optional[int] = Field(1, ge=0, le=1) 
    estado_pago: Optional[int] = Field(0, ge=0, le=1) # 0=Pendiente, 1=Pagado

class NominaDetalleUpdate(BaseModel):
    total_remuneraciones: Optional[Decimal] = Field(None, ge=0)
    total_deducciones: Optional[Decimal] = Field(None, ge=0)
    salario_neto: Optional[Decimal] = None # Se actualiza si cambian rem/ded
    estado: Optional[int] = Field(None, ge=0, le=1) 
    estado_pago: Optional[int] = Field(None, ge=0, le=1)

class NominaDetalleOut(BaseModel):
    id_detalle_nomina: str
    id_nomina: str
    id_trabajador: int
    salario_base: Decimal
    total_remuneraciones: Decimal
    total_deducciones: Decimal
    salario_neto: Decimal
    estado: int
    estado_pago: int
    creado: datetime

    class Config:
        from_attributes = True

class NominaDetalleList(BaseModel):
    """Schema para devolver una lista de detalles creados."""
    detalles: List[NominaDetalleOut]
    count: int