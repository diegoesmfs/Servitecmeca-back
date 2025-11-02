class HistorialPago:
    def __init__(self, historial_pago_id, nomina_id, fecha_pago,
                 monto_pagado, metodo_pago, estado, createdat):
        self.historial_pago_id = historial_pago_id
        self.nomina_id = nomina_id
        self.fecha_pago = fecha_pago
        self.monto_pagado = monto_pagado
        self.metodo_pago = metodo_pago
        self.estado = estado
        self.createdat = createdat