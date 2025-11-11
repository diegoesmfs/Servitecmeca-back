from pydantic import BaseModel, Field, conint
from typing import Optional, List
from datetime import datetime

# ====================
#  1. MODELO BASE (Estructura de la Data - SIN CONFIGURACIÓN)
# ====================
# Define la estructura de los campos comunes para todas las operaciones.
class CargoBase(BaseModel):
    id_cargo: str = Field(..., max_length=10, description="ID único del cargo (ej: 'GERENTE').")
    titulo: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    nivel: conint(ge=0, le=4)
    salario_base: float = Field(..., gt=0, description="Debe ser mayor a 0.")
    salario_maximo: float = Field(..., description="Debe ser mayor o igual al salario base.")
    competencias: Optional[str] = None

# ====================
#  2. ESQUEMAS DE ENTRADA (Input para la API)
# ====================

class CargoCreate(CargoBase):
    # Hereda todos los campos como requeridos para la petición POST.
    pass

class CargoUpdate(BaseModel):
    # Modelo para manejar campos opcionales en la actualización.
    titulo: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None
    nivel: Optional[conint(ge=0, le=4)] = None
    salario_base: Optional[float] = Field(None, gt=0)
    salario_maximo: Optional[float] = None
    competencias: Optional[str] = None
    estado: Optional[conint(ge=0, le=1)] = None 

# ====================
#  3. ESQUEMA DE SALIDA (Output de la DB - ¡LA ÚNICA CON MODEL_CONFIG!)
# ====================

class CargoOut(CargoBase): 
    # Campos que vienen de la DB.
    estado: conint(ge=0, le=1) = 1
    
    # <<-- CORRECCIÓN FINAL AQUÍ -->>
    # Forzamos la definición del campo de fecha/hora como requerido para el output.
    creado: datetime = Field(..., description="Fecha de creación del registro en la DB")
    
    # SOLO LA CLASE DE SALIDA LLEVA LA CONFIGURACIÓN DE MAPEADO.
    model_config = {
        "from_attributes": True  
    }