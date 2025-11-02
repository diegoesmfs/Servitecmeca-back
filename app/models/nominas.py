class Nomina:
    def __init__(self, nomina_id, trabajador_id, periodo, tipo_nomina,
                 estado_pago, total_bruto, total_neto, createdat, is_deleted):
        self.nomina_id = nomina_id
        self.trabajador_id = trabajador_id
        self.periodo = periodo
        self.tipo_nomina = tipo_nomina
        self.estado_pago = estado_pago
        self.total_bruto = total_bruto
        self.total_neto = total_neto
        self.createdat = createdat
        self.is_deleted = is_deleted