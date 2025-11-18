# schemas/cargo.py
from pydantic import BaseModel, Field
from typing import Optional, Literal
from decimal import Decimal
from datetime import datetime

# Opciones para el nivel (0 a 4)
Nivel = Literal[0, 1, 2, 3, 4]

# --- Clases CREATE y UPDATE (Para entrada de datos) ---

class CargoCreate(BaseModel):
    id_cargo: str = Field(..., max_length=10)
    id_departamento: str = Field(..., max_length=10)
    titulo: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    nivel: Nivel
    salario_base: Decimal = Field(..., decimal_places=2, gt=Decimal(0))
    salario_maximo: Decimal = Field(..., decimal_places=2)
    competencias: Optional[str] = None
    estado: Optional[int] = Field(1, ge=0, le=1)
    
class CargoUpdate(BaseModel):
    id_departamento: Optional[str] = Field(None, max_length=10)
    titulo: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None
    nivel: Optional[Nivel] = None
    salario_base: Optional[Decimal] = Field(None, decimal_places=2, gt=Decimal(0))
    salario_maximo: Optional[Decimal] = Field(None, decimal_places=2)
    competencias: Optional[str] = None
    estado: Optional[int] = Field(None, ge=0, le=1)

# --- Clase de Salida (CargoOut) MODIFICADA ---
class CargoOut(BaseModel):
    id_cargo: str
    id_departamento: str
    titulo: str
    descripcion: Optional[str]
    nivel: int
    salario_base: Decimal
    salario_maximo: Decimal
    competencias: Optional[str]
    estado: int
    creado: datetime
    
    # 🌟 Nuevo campo enriquecido
    nombre_departamento: str 

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v),
        }