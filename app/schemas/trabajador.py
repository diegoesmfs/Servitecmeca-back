# schemas/trabajador.py (Modificado)
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal
from datetime import date
from decimal import Decimal

# Opciones para el tipo_contrato (basado en CHECK (tipo_contrato = ANY (ARRAY[0, 1, 2, 3])))
TipoContrato = Literal[0, 1, 2, 3]

# --- Clases CREATE y UPDATE (Se mantienen sin cambios) ---

class TrabajadorCreate(BaseModel):
    documento: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=50)
    apellido: str = Field(..., max_length=50)
    correo: EmailStr = Field(..., max_length=150)
    telefono: Optional[str] = Field(None, max_length=15)
    direccion: Optional[str] = Field(None, max_length=255)
    id_departamento: str = Field(..., max_length=10)
    id_cargo: str = Field(..., max_length=10)
    salario: Decimal = Field(..., decimal_places=2, ge=Decimal(0))
    tipo_contrato: TipoContrato = Field(..., description="0, 1, 2 o 3.")
    habilidades_competencias: Optional[str] = None
    estado: Optional[int] = Field(1, ge=0, le=1) 

class TrabajadorUpdate(BaseModel):
    documento: Optional[str] = Field(None, max_length=20)
    nombre: Optional[str] = Field(None, max_length=50)
    apellido: Optional[str] = Field(None, max_length=50)
    correo: Optional[EmailStr] = Field(None, max_length=150)
    telefono: Optional[str] = Field(None, max_length=15)
    direccion: Optional[str] = Field(None, max_length=255)
    id_departamento: Optional[str] = Field(None, max_length=10)
    id_cargo: Optional[str] = Field(None, max_length=10)
    salario: Optional[Decimal] = Field(None, decimal_places=2, ge=Decimal(0))
    tipo_contrato: Optional[TipoContrato] = None
    habilidades_competencias: Optional[str] = None
    estado: Optional[int] = Field(None, ge=0, le=1) 

# --- Clase de Salida (TrabajadorOut) MODIFICADA ---
class TrabajadorOut(BaseModel):
    id_trabajador: int
    documento: str
    nombre: str
    apellido: str
    correo: str
    telefono: Optional[str]
    direccion: Optional[str]
    
    # FKs originales
    id_departamento: str
    id_cargo: str
    
    # 🌟 Nuevos campos enriquecidos (vienen del JOIN en el controlador)
    nombre_departamento: str  # Campo del departamento.nombre
    titulo_cargo: str         # Campo del cargos.titulo

    salario: Decimal
    tipo_contrato: int
    creado: date
    habilidades_competencias: Optional[str]
    estado: int

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v),
        }