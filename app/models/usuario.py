class Usuario:
    def __init__(self, user_id, nombre, correo, contrasena, direccion, telefono,
                 tipo_usuario, estado, createdat, is_deleted):
        self.user_id = user_id
        self.nombre = nombre
        self.correo = correo
        self.contrasena = contrasena
        self.direccion = direccion
        self.telefono = telefono
        self.tipo_usuario = tipo_usuario
        self.estado = estado
        self.createdat = createdat
        self.is_deleted = is_deleted