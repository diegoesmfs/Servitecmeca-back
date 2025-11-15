# models/nomina_detalle.py
from datetime import datetime
from typing import Optional
import asyncpg
from decimal import Decimal

class NominaDetalle:
    """Modelo de Negocio para la entidad NominaDetalle."""
    def __init__(self, 
                 id_detalle_nomina: str, 
                 id_nomina: str, 
                 id_trabajador: int, 
                 salario_base: Decimal, 
                 total_remuneraciones: Decimal, 
                 total_deducciones: Decimal, 
                 salario_neto: Decimal, 
                 estado: int, 
                 estado_pago: int,
                 creado: datetime):
        
        self.id_detalle_nomina = id_detalle_nomina
        self.id_nomina = id_nomina
        self.id_trabajador = id_trabajador
        self.salario_base = salario_base
        self.total_remuneraciones = total_remuneraciones
        self.total_deducciones = total_deducciones
        self.salario_neto = salario_neto
        self.estado = estado
        self.estado_pago = estado_pago
        self.creado = creado

    @classmethod
    def from_record(cls, record: asyncpg.Record):
        """Convierte un asyncpg.Record en una instancia de NominaDetalle."""
        return cls(
            id_detalle_nomina=record["id_detalle_nomina"],
            id_nomina=record["id_nomina"],
            id_trabajador=record["id_trabajador"],
            salario_base=record["salario_base"],
            total_remuneraciones=record["total_remuneraciones"],
            total_deducciones=record["total_deducciones"],
            salario_neto=record["salario_neto"],
            estado=record["estado"],
            estado_pago=record["estado_pago"],
            creado=record["creado"]
        )