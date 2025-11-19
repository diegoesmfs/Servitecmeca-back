# models/nomina_detalle.py (COMPLETO Y CORREGIDO)
from datetime import datetime
from typing import Optional
import asyncpg
from decimal import Decimal

class NominaDetalle:
    """Modelo de Negocio para la entidad NominaDetalle, extendido con nombre del trabajador."""
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
                 creado: datetime,
                 # 🌟 CAMPOS AÑADIDOS POR EL JOIN 🌟
                 nombre_trabajador: Optional[str] = None, 
                 apellido_trabajador: Optional[str] = None): 
        
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
        # Asignación de los nuevos atributos
        self.nombre_trabajador = nombre_trabajador
        self.apellido_trabajador = apellido_trabajador

    @classmethod
    def from_record(cls, record: asyncpg.Record):
        """Convierte un asyncpg.Record en una instancia de NominaDetalle."""
        
        # Obtenemos los campos del JOIN. Usamos .get() para evitar errores si el record 
        # viene de una inserción simple (sin JOIN).
        nombre = record.get("nombre_trabajador")
        apellido = record.get("apellido_trabajador")
        
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
            creado=record["creado"],
            # Mapeo condicional de los nuevos campos
            nombre_trabajador=nombre,
            apellido_trabajador=apellido
        )