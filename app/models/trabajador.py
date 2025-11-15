# models/trabajador.py
from datetime import date
from typing import Optional
import asyncpg
from decimal import Decimal

class Trabajador:
    """Modelo de Negocio para la entidad Trabajador."""
    
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
                 estado: int):
        
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
            # asyncpg usa Decimal para numeric(10,2)
            salario=record["salario"], 
            tipo_contrato=record["tipo_contrato"],
            creado=record["creado"], # Tipo date en DB
            habilidades_competencias=record["habilidades_competencias"],
            estado=record["estado"]
        )