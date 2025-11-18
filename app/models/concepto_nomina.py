# models/concepto_nomina.py
from datetime import datetime
from typing import Optional
import asyncpg
from decimal import Decimal

class ConceptoNomina:
    """Modelo de Negocio para la entidad ConceptoNomina."""
    def __init__(self, 
                 id_concepto: int, 
                 id_detalle_nomina: str, 
                 razon: str, 
                 monto: Decimal, 
                 tipo: int, # 0: Remuneración (Suma), 1: Deducción (Resta)
                 estado: int, 
                 creado: datetime):
        
        self.id_concepto = id_concepto
        self.id_detalle_nomina = id_detalle_nomina
        self.razon = razon
        self.monto = monto
        self.tipo = tipo
        self.estado = estado
        self.creado = creado

    @classmethod
    def from_record(cls, record: asyncpg.Record):
        """Convierte un asyncpg.Record en una instancia de ConceptoNomina."""
        return cls(
            id_concepto=record["id_concepto"],
            id_detalle_nomina=record["id_detalle_nomina"],
            razon=record["razon"],
            monto=record["monto"],
            tipo=record["tipo"],
            estado=record["estado"],
            creado=record["creado"]
        )