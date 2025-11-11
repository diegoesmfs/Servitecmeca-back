# schemas/departamento.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class DepartamentoCreate(BaseModel):
    id_departamento: str = Field(..., max_length=10)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    jefe_departamento: Optional[int] = None
    presupuesto_anual: float = Field(0.00, ge=0)
    telefono: Optional[str] = Field(None, max_length=15)
    email: Optional[EmailStr] = Field(None, max_length=150)
    ubicacion: Optional[str] = Field(None, max_length=100)
    capacidad_empleados: int = Field(..., gt=0)
    estado: Optional[int] = Field(1, ge=0, le=1) 

class DepartamentoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None
    jefe_departamento: Optional[int] = None
    presupuesto_anual: Optional[float] = Field(None, ge=0)
    telefono: Optional[str] = Field(None, max_length=15)
    email: Optional[EmailStr] = Field(None, max_length=150)
    ubicacion: Optional[str] = Field(None, max_length=100)
    capacidad_empleados: Optional[int] = Field(None, gt=0)
    estado: Optional[int] = Field(None, ge=0, le=1) 

class DepartamentoOut(BaseModel):
    id_departamento: str
    nombre: str
    descripcion: Optional[str]
    jefe_departamento: Optional[int]
    presupuesto_anual: float
    telefono: Optional[str]
    email: Optional[str]
    ubicacion: Optional[str]
    capacidad_empleados: int
    creado: datetime
    estado: int

    class Config:
        from_attributes = True