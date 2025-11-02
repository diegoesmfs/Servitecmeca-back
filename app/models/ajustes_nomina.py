class AjusteNomina:
    def __init__(self, ajuste_id, nomina_id, tipo_ajuste, descripcion,
                 monto, createdat, is_deleted):
        self.ajuste_id = ajuste_id
        self.nomina_id = nomina_id
        self.tipo_ajuste = tipo_ajuste
        self.descripcion = descripcion
        self.monto = monto
        self.createdat = createdat
        self.is_deleted = is_deleted