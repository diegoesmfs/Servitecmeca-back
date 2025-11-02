class Contrato:
    def __init__(self, contracto_id, trabajadorid, tipo_contrato, fecha_inicio,
                 fecha_fin, salario_base, jornada_laboral, estado, createdat, is_deleted):
        self.contracto_id = contracto_id
        self.trabajadorid = trabajadorid
        self.tipo_contrato = tipo_contrato
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.salario_base = salario_base
        self.jornada_laboral = jornada_laboral
        self.estado = estado
        self.createdat = createdat
        self.is_deleted = is_deleted