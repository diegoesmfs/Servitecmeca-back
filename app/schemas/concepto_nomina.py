# schemas/concepto_nomina.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class ConceptoNominaCreate(BaseModel):
    id_detalle_nomina: str = Field(..., max_length=20, description="FK al detalle de nómina al que pertenece.")
    razon: str = Field(..., max_length=100)
    monto: Decimal = Field(..., ge=0)
    tipo: int = Field(..., ge=0, le=1, description="0=Remuneración (Suma), 1=Deducción (Resta).")
    estado: Optional[int] = Field(1, ge=0, le=1) 

class ConceptoNominaUpdate(BaseModel):
    razon: Optional[str] = Field(None, max_length=100)
    monto: Optional[Decimal] = Field(None, ge=0)
    tipo: Optional[int] = Field(None, ge=0, le=1) 
    estado: Optional[int] = Field(None, ge=0, le=1) 

class ConceptoNominaOut(BaseModel):
    id_concepto: int
    id_detalle_nomina: str
    razon: str
    monto: Decimal
    tipo: int
    estado: int
    creado: datetime

    class Config:
        from_attributes = True