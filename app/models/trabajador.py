# models/trabajador.py
from datetime import date
from typing import Optional
import asyncpg
from decimal import Decimal

class Trabajador:
    """Modelo de Negocio para la entidad Trabajador, extendido con datos de JOIN."""
    
    def __init__(self, 
                 id_trabajador: int, 
                 documento: str, 
                 nombre: str, 
                 apellido: str, 
                 correo: str, 
                 telefono: Optional[str], 
                 direccion: Optional[str], 
                 id_departamento: str, 
                 id_cargo: str, 
                 salario: Decimal, 
                 tipo_contrato: int, 
                 creado: date, 
                 habilidades_competencias: Optional[str], 
                 estado: int,
                 # Campos para el JOIN
                 nombre_departamento: str, 
                 titulo_cargo: str):
        
        self.id_trabajador = id_trabajador
        self.documento = documento
        self.nombre = nombre
        self.apellido = apellido
        self.correo = correo
        self.telefono = telefono
        self.direccion = direccion
        self.id_departamento = id_departamento
        self.id_cargo = id_cargo
        self.salario = salario
        self.tipo_contrato = tipo_contrato
        self.creado = creado
        self.habilidades_competencias = habilidades_competencias
        self.estado = estado
        # Asignación de los nuevos atributos
        self.nombre_departamento = nombre_departamento
        self.titulo_cargo = titulo_cargo

    @classmethod
    def from_record(cls, record: asyncpg.Record):
        """Convierte un asyncpg.Record en una instancia de Trabajador."""
        return cls(
            id_trabajador=record["id_trabajador"],
            documento=record["documento"],
            nombre=record["nombre"],
            apellido=record["apellido"],
            correo=record["correo"],
            telefono=record["telefono"],
            direccion=record["direccion"],
            id_departamento=record["id_departamento"],
            id_cargo=record["id_cargo"],
            salario=record["salario"], 
            tipo_contrato=record["tipo_contrato"],
            creado=record["creado"],
            habilidades_competencias=record["habilidades_competencias"],
            estado=record["estado"],
            # Mapeo de los nuevos campos desde el resultado del JOIN
            nombre_departamento=record["nombre_departamento"],
            titulo_cargo=record["titulo_cargo"]
        )