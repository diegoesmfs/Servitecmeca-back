from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
# conint ya no es necesario

# ====================
# 1. MODELO BASE (Estructura de la Data - SIN CONFIGURACIÓN)
# ====================
class CargoBase(BaseModel):
    id_cargo: str = Field(..., max_length=10, description="ID único del cargo (ej: 'GERENTE').")
    titulo: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    
    # CORRECCIÓN: Usamos 'int' con Field(..., ge=0, le=4)
    nivel: int = Field(..., ge=0, le=4, description="Nivel jerárquico de 0 a 4.")
    
    # CORRECCIÓN: Usamos 'float' con Field(..., gt=0)
    salario_base: float = Field(..., gt=0, description="Debe ser mayor a 0.")
    salario_maximo: float = Field(..., description="Debe ser mayor o igual al salario base.")
    competencias: Optional[str] = None

# ====================
# 2. ESQUEMAS DE ENTRADA (Input para la API)
# ====================

class CargoCreate(CargoBase):
    # Hereda todos los campos como requeridos para la petición POST.
    pass

class CargoUpdate(BaseModel):
    # Modelo para manejar campos opcionales en la actualización.
    titulo: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None
    
    # CORRECCIÓN: Usamos 'int' con Field(None, ge=0, le=4)
    nivel: Optional[int] = Field(None, ge=0, le=4)
    
    # CORRECCIÓN: Usamos 'float' con Field(None, gt=0)
    salario_base: Optional[float] = Field(None, gt=0)
    salario_maximo: Optional[float] = None
    competencias: Optional[str] = None
    
    # CORRECCIÓN: Usamos 'int' con Field(None, ge=0, le=1)
    estado: Optional[int] = Field(None, ge=0, le=1) 

# ====================
# 3. ESQUEMA DE SALIDA (Output de la DB - ¡LA ÚNICA CON MODEL_CONFIG!)
# ====================

class CargoOut(CargoBase): 
    # Campo estado que viene de la DB.
    # CORRECCIÓN: Usamos 'int' con Field(..., ge=0, le=1)
    estado: int = Field(1, ge=0, le=1)
    
    # Forzamos la definición del campo de fecha/hora como requerido para el output.
    creado: datetime = Field(..., description="Fecha de creación del registro en la DB")
    
    # SOLO LA CLASE DE SALIDA LLEVA LA CONFIGURACIÓN DE MAPEADO.
    model_config = {
        "from_attributes": True  
    }