# models/nomina_general.py (COMPLETO Y CORREGIDO)
from datetime import date, datetime
from typing import Optional
import asyncpg
from decimal import Decimal

class NominaGeneral:
    """Modelo de Negocio para la entidad NominaGeneral, extendido con el nombre de departamento."""
    def __init__(self, 
                 id_nomina: str, 
                 periodo: date, 
                 id_departamento: str, 
                 fecha_pago: date, 
                 presupuesto_utilizado: Decimal, 
                 impuesto_renta_total: Decimal, 
                 seguro_social_total: Decimal, 
                 estado: int, 
                 estado_pago: int,
                 observaciones: Optional[str],
                 creado: datetime,
                 # 🌟 CAMPO AÑADIDO POR EL JOIN 🌟
                 nombre_departamento: str):
        
        self.id_nomina = id_nomina
        self.periodo = periodo
        self.id_departamento = id_departamento
        self.fecha_pago = fecha_pago
        self.presupuesto_utilizado = presupuesto_utilizado
        self.impuesto_renta_total = impuesto_renta_total
        self.seguro_social_total = seguro_social_total
        self.estado = estado
        self.estado_pago = estado_pago
        self.observaciones = observaciones
        self.creado = creado
        # Asignación del nuevo atributo
        self.nombre_departamento = nombre_departamento

    @classmethod
    def from_record(cls, record: asyncpg.Record):
        """Convierte un asyncpg.Record en una instancia de NominaGeneral."""
        return cls(
            id_nomina=record["id_nomina"],
            periodo=record["periodo"],
            id_departamento=record["id_departamento"],
            fecha_pago=record["fecha_pago"],
            presupuesto_utilizado=record["presupuesto_utilizado"],
            impuesto_renta_total=record["impuesto_renta_total"],
            seguro_social_total=record["seguro_social_total"],
            estado=record["estado"],
            estado_pago=record["estado_pago"],
            observaciones=record["observaciones"],
            creado=record["creado"],
            # Mapeo del nuevo campo
            nombre_departamento=record["nombre_departamento"]
        )