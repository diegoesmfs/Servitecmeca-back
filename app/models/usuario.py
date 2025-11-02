class Usuario:
    def __init__(self, user_id, nombre, correo, contraseña, direccion, telefono,
                 tipo_usuario, estado, createdat, is_deleted):
        self.user_id = user_id
        self.nombre = nombre
        self.correo = correo
        self.contraseña = contraseña
        self.direccion = direccion
        self.telefono = telefono
        self.tipo_usuario = tipo_usuario
        self.estado = estado
        self.createdat = createdat
        self.is_deleted = is_deleted