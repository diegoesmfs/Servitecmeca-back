# models/cargo.py
from typing import Optional
import asyncpg
from decimal import Decimal
from datetime import datetime

class Cargo:
    """Modelo de Negocio para la entidad Cargos, extendido con nombre de departamento."""
    
    def __init__(self,
                 id_cargo: str,
                 id_departamento: str,
                 titulo: str,
                 descripcion: Optional[str],
                 nivel: int,
                 salario_base: Decimal,
                 salario_maximo: Decimal,
                 competencias: Optional[str],
                 estado: int,
                 creado: datetime,
                 # Campo para el JOIN
                 nombre_departamento: str): 
        
        self.id_cargo = id_cargo
        self.id_departamento = id_departamento
        self.titulo = titulo
        self.descripcion = descripcion
        self.nivel = nivel
        self.salario_base = salario_base
        self.salario_maximo = salario_maximo
        self.competencias = competencias
        self.estado = estado
        self.creado = creado
        self.nombre_departamento = nombre_departamento # 👈 Nuevo atributo

    @classmethod
    def from_record(cls, record: asyncpg.Record):
        """Convierte un asyncpg.Record en una instancia de Cargo."""
        return cls(
            id_cargo=record["id_cargo"],
            id_departamento=record["id_departamento"],
            titulo=record["titulo"],
            descripcion=record["descripcion"],
            nivel=record["nivel"],
            salario_base=record["salario_base"],
            salario_maximo=record["salario_maximo"],
            competencias=record["competencias"],
            estado=record["estado"],
            creado=record["creado"],
            # Mapeo del nuevo campo
            nombre_departamento=record["nombre_departamento"]
        )