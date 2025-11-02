
class Cargo:
    def __init__(self, posicion_id, nombre, descripcion, sueldo_base,
                 departmento_id, createdat, is_deleted):
        self.posicion_id = posicion_id
        self.nombre = nombre
        self.descripcion = descripcion
        self.sueldo_base = sueldo_base
        self.departmento_id = departmento_id
        self.createdat = createdat
        self.is_deleted = is_deleted
