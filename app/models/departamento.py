# models/departamento.py

from datetime import datetime
from typing import Optional
import asyncpg

class Departamento:
    """Modelo de Negocio para la entidad Departamento."""
    def __init__(self, 
                 id_departamento: str, 
                 nombre: str, 
                 descripcion: Optional[str], 
                 jefe_departamento: Optional[int], 
                 # 🌟 NUEVO PARÁMETRO
                 nombre_jefe_departamento: Optional[str],
                 presupuesto_anual: float, 
                 telefono: Optional[str], 
                 email: Optional[str], 
                 ubicacion: Optional[str], 
                 capacidad_empleados: int, 
                 creado: datetime, 
                 estado: int):
        
        self.id_departamento = id_departamento
        self.nombre = nombre
        self.descripcion = descripcion
        self.jefe_departamento = jefe_departamento
        # 🌟 NUEVO ATRIBUTO
        self.nombre_jefe_departamento = nombre_jefe_departamento
        self.presupuesto_anual = presupuesto_anual
        self.telefono = telefono
        self.email = email
        self.ubicacion = ubicacion
        self.capacidad_empleados = capacidad_empleados
        self.creado = creado
        self.estado = estado

    @classmethod
    def from_record(cls, record: asyncpg.Record):
        """Convierte un asyncpg.Record en una instancia de Departamento."""
        # Se asume que el nombre del jefe viene como 'nombre_jefe' o None.
        nombre_jefe = record.get("nombre_jefe")
        if nombre_jefe and record.get("apellido_jefe"):
            nombre_completo = f"{record['nombre_jefe']} {record['apellido_jefe']}"
        else:
            nombre_completo = None

        return cls(
            id_departamento=record["id_departamento"],
            nombre=record["nombre"],
            descripcion=record["descripcion"],
            jefe_departamento=record["jefe_departamento"],
            # 🌟 SE ASIGNA EL NOMBRE DEL JEFE
            nombre_jefe_departamento=nombre_completo,
            presupuesto_anual=float(record["presupuesto_anual"]),
            telefono=record["telefono"],
            email=record["email"],
            ubicacion=record["ubicacion"],
            capacidad_empleados=record["capacidad_empleados"],
            creado=record["creado"],
            estado=record["estado"]
        )