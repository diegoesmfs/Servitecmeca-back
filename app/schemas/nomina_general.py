# schemas/nomina_general.py (COMPLETO Y CORREGIDO)
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal

class NominaGeneralCreate(BaseModel):
    id_nomina: str = Field(..., max_length=20, description="Identificador único de la nómina general (Ej: '2025-05-DEP1').")
    periodo: date
    id_departamento: str = Field(..., max_length=10)
    fecha_pago: date
    presupuesto_utilizado: Optional[Decimal] = Field(0.00, ge=0)
    impuesto_renta_total: Optional[Decimal] = Field(0.00, ge=0)
    seguro_social_total: Optional[Decimal] = Field(0.00, ge=0)
    estado: Optional[int] = Field(1, ge=0, le=1, description="1=Activa, 0=Inactiva/Anulada") 
    estado_pago: Optional[int] = Field(0, ge=0, le=3, description="0=Pendiente, 1=Parcial, 2=Completo, 3=Cancelado")
    observaciones: Optional[str] = None

class NominaGeneralUpdate(BaseModel):
    periodo: Optional[date] = None
    id_departamento: Optional[str] = Field(None, max_length=10)
    fecha_pago: Optional[date] = None
    presupuesto_utilizado: Optional[Decimal] = Field(None, ge=0)
    impuesto_renta_total: Optional[Decimal] = Field(None, ge=0)
    seguro_social_total: Optional[Decimal] = Field(None, ge=0)
    estado: Optional[int] = Field(None, ge=0, le=1) 
    estado_pago: Optional[int] = Field(None, ge=0, le=3)
    observaciones: Optional[str] = None

class NominaGeneralOut(BaseModel):
    id_nomina: str
    periodo: date
    id_departamento: str
    nombre_departamento: str  # 🌟 NUEVO CAMPO AÑADIDO
    fecha_pago: date
    presupuesto_utilizado: Decimal
    impuesto_renta_total: Decimal
    seguro_social_total: Decimal
    estado: int
    estado_pago: int
    observaciones: Optional[str]
    creado: datetime

    class Config:
        from_attributes = True