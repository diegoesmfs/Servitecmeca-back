# models/usuario.py
from datetime import datetime
from typing import Optional
import asyncpg

class Usuario:
    """Modelo de Negocio para la entidad Usuario."""
    
    def __init__(self, 
                 id_usuario: int, 
                 nombre: str, 
                 correo: str, 
                 documento: str, 
                 id_trabajador: int, 
                 rol: str, 
                 contrasena: str, # Aquí se almacena el hash de la contraseña
                 estado: int,
                 creado: datetime):
        
        self.id_usuario = id_usuario
        self.nombre = nombre
        self.correo = correo
        self.documento = documento
        self.id_trabajador = id_trabajador
        self.rol = rol
        self.contrasena = contrasena
        self.estado = estado
        self.creado = creado

    @classmethod
    def from_record(cls, record: asyncpg.Record):
        """Convierte un asyncpg.Record en una instancia de Usuario."""
        return cls(
            id_usuario=record["id_usuario"],
            nombre=record["nombre"],
            correo=record["correo"],
            documento=record["documento"],
            id_trabajador=record["id_trabajador"],
            rol=record["rol"],
            contrasena=record["contrasena"],
            estado=record["estado"],
            creado=record["creado"]
        )