class Trabajador:
    def __init__(self, trabajador_id, nombre, correo, documento, fecha_nacimiento,
                 estado_civil, direccion, telefono, cuenta_bancaria, posicion_id,
                 is_active, createdat, is_deleted):
        self.trabajador_id = trabajador_id
        self.nombre = nombre
        self.correo = correo
        self.documento = documento
        self.fecha_nacimiento = fecha_nacimiento
        self.estado_civil = estado_civil
        self.direccion = direccion
        self.telefono = telefono
        self.cuenta_bancaria = cuenta_bancaria
        self.posicion_id = posicion_id
        self.is_active = is_active
        self.createdat = createdat
        self.is_deleted = is_deleted