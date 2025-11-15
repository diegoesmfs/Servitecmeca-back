# schemas/trabajador.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal
from datetime import date
from decimal import Decimal

# Opciones para el tipo_contrato (basado en CHECK (tipo_contrato = ANY (ARRAY[0, 1, 2, 3])))
TipoContrato = Literal[0, 1, 2, 3]

class TrabajadorCreate(BaseModel):
    documento: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=50)
    apellido: str = Field(..., max_length=50)
    correo: EmailStr = Field(..., max_length=150)
    telefono: Optional[str] = Field(None, max_length=15)
    direccion: Optional[str] = Field(None, max_length=255)
    id_departamento: str = Field(..., max_length=10)
    id_cargo: str = Field(..., max_length=10)
    # Usamos Decimal para mapear a numeric(10,2) de PostgreSQL
    salario: Decimal = Field(..., decimal_places=2, ge=Decimal(0))
    tipo_contrato: TipoContrato = Field(..., description="0, 1, 2 o 3.")
    # La fecha de creación la maneja el controlador/DB, pero si se envía, debe ser válida
    # No la incluiremos aquí para que sea la DB la que ponga el valor inicial (si usas DEFAULT)
    # o el controlador el que la fije. La tabla la marca como NOT NULL.
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
    
    # La fecha 'creado' no se actualiza

class TrabajadorOut(BaseModel):
    id_trabajador: int
    documento: str
    nombre: str
    apellido: str
    correo: str
    telefono: Optional[str]
    direccion: Optional[str]
    id_departamento: str
    id_cargo: str
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