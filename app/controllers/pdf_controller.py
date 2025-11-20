from typing import List, Dict, Any, Optional
# Importación estándar de fpdf2 (aunque se usa FPDF)
from fpdf import FPDF, XPos, YPos
from datetime import datetime

# --- Clase FPDF personalizada ---
class PDF(FPDF):
    """Clase personalizada para añadir encabezado y pie de página al PDF."""
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'REPORTE DEL SISTEMA', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, f"Fecha de Generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, 'R')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', 0, 0, 'C')

# --- Estructura de Columna requerida para la función reutilizable ---
class PDFColumn:
    """Define la estructura y formato de una columna en el reporte."""
    def __init__(self, key: str, header: str, width: int, align: str = 'L', formatter=None):
        self.key = key
        self.header = header
        self.width = width
        self.align = align
        # Función para dar formato al valor (si no se proporciona, usa conversión simple a str)
        self.formatter = formatter if formatter is not None else lambda v: str(v) if v is not None else 'N/A'

# --- Función Generadora de PDF Reutilizable (Máxima Robustez) ---
async def generate_generic_pdf(
    data: List[Dict[str, Any]], 
    columns: List[PDFColumn],
    report_title: str
) -> bytes:
    """
    Genera un PDF de una tabla a partir de una lista de diccionarios. 
    Retorna el contenido BINARIO del PDF (bytes).
    """
    # Usamos A3 en modo horizontal (Landscape)
    pdf = PDF('L', 'mm', 'A3') # 'L' = Landscape (horizontal), 'A3' = Tamaño de página
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Sobrescribir el título genérico con el título del reporte
    pdf.set_y(15) 
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, report_title, 0, 1, 'L')
    pdf.ln(2)

    # Encabezados de la tabla
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font('Arial', 'B', 8)
    
    # 1. Imprimir los encabezados definidos (con borde completo '1')
    for col in columns:
        pdf.cell(col.width, 7, col.header, 1, 0, 'C', 1)
    pdf.ln()

    # Contenido de la tabla
    pdf.set_font('Arial', '', 8) # Restauramos fuente a 8 para A3
    cell_height = 6 # Altura de celda restaurada a 6
    
    for row in data:
        # Verifica si hay suficiente espacio para la fila completa antes de dibujarla
        if pdf.get_y() + cell_height > pdf.page_break_trigger:
            pdf.add_page()
            # Vuelve a imprimir los encabezados después del salto de página
            pdf.set_fill_color(200, 220, 255)
            pdf.set_font('Arial', 'B', 8)
            for col in columns:
                pdf.cell(col.width, 7, col.header, 1, 0, 'C', 1)
            pdf.ln()
            pdf.set_font('Arial', '', 8)

        for i, col in enumerate(columns):
            value = row.get(col.key)
            formatted_value = col.formatter(value)
            
            # El borde inferior 'B' añade la línea divisoria entre filas.
            # 'LB' (Izquierda, Abajo) para la mayoría, 'LRB' para la última celda de la fila.
            border_style = 'LRB' if i == len(columns) - 1 else 'LB'
            
            # Imprime la celda del dato
            pdf.cell(col.width, cell_height, formatted_value, border_style, 0, col.align)
        
        pdf.ln() # Salto de línea después de la fila

    # CORRECCIÓN DEFINITIVA: 
    # dest='B' (Devuelve el PDF como bytes o bytearray)
    # bytes(...) (Asegura que el retorno final sea del tipo 'bytes' para FastAPI)
    return bytes(pdf.output(dest='B'))


# 🌟🌟🌟 NUEVA FUNCIÓN: REPORTE DETALLADO DE NÓMINA 🌟🌟🌟
async def generate_nomina_detailed_report(
    nomina_general_data: Dict[str, Any], 
    detalles_data: List[Dict[str, Any]]
) -> bytes:
    """
    Genera un PDF con el resumen de una Nómina General y la lista de todos sus detalles.
    """
    pdf = PDF('P', 'mm', 'A4') # Usamos A4 Vertical para un reporte más detallado
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- 1. Título y Encabezado de la Nómina General ---
    pdf.set_y(25) 
    pdf.set_font('Arial', 'BU', 14)
    pdf.cell(0, 10, f"NÓMINA GENERAL DETALLADA - ID: {nomina_general_data['id_nomina']}", 0, 1, 'C')
    pdf.ln(5)

    # Función auxiliar para imprimir detalles clave
    def print_key_value(key: str, value: str, is_bold: bool = False, width=90):
        font_style = 'B' if is_bold else ''
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(width * 0.4, 6, key + ":", 0, 0, 'L')
        pdf.set_font('Arial', font_style, 10)
        pdf.cell(width * 0.6, 6, value, 0, 0, 'L')

    # Datos en dos columnas
    pdf.set_fill_color(240, 240, 240)
    
    # Columna 1 (Izquierda)
    x_pos_c1 = pdf.get_x()
    print_key_value("Departamento", nomina_general_data.get('nombre_departamento', 'N/A'))
    pdf.ln()
    pdf.set_x(x_pos_c1)
    print_key_value("Período de Nómina", str(nomina_general_data.get('periodo', 'N/A')).split('T')[0])
    pdf.ln()
    pdf.set_x(x_pos_c1)
    print_key_value("Fecha de Pago", str(nomina_general_data.get('fecha_pago', 'N/A')).split('T')[0])
    pdf.ln()
    
    # Columna 2 (Derecha - Totales)
    y_before_c2 = pdf.get_y() - 18 # Retrocede 3 líneas (3*6)
    pdf.set_xy(110, y_before_c2) # Mueve a la derecha para la segunda columna
    
    # Totales de la Nómina General
    print_key_value("Presupuesto Utilizado", f"${float(nomina_general_data.get('presupuesto_utilizado', 0)):,.2f}", True)
    pdf.ln()
    pdf.set_x(110)
    print_key_value("Impuesto Renta Total", f"${float(nomina_general_data.get('impuesto_renta_total', 0)):,.2f}")
    pdf.ln()
    pdf.set_x(110)
    print_key_value("Seguro Social Total", f"${float(nomina_general_data.get('seguro_social_total', 0)):,.2f}")
    pdf.ln()
    
    # Restaura la posición de la línea para el contenido siguiente
    pdf.ln(10) 
    
    # --- 2. Título de la Tabla de Detalles ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, "Detalles de Pago Individuales (Nómina Trabajador)", 0, 1, 'L')
    pdf.ln(2)

    # --- 3. Tabla de Detalles de Nómina ---
    
    # Definición de columnas para Detalle de Nómina (Total 185mm para A4)
    detail_columns_definition = [
        PDFColumn(key='id_trabajador', header='ID Trab.', width=20, align='C'),
        PDFColumn(key='nombre_trabajador', header='Trabajador', width=45, align='L',
                  formatter=lambda v, row: f"{v} {row.get('apellido_trabajador', '')}"),
        PDFColumn(key='salario_base', header='Salario Base', width=25, align='R', 
                  formatter=lambda v: f"${float(v):,.2f}"),
        PDFColumn(key='total_remuneraciones', header='Remuneraciones', width=25, align='R', 
                  formatter=lambda v: f"${float(v):,.2f}"),
        PDFColumn(key='total_deducciones', header='Deducciones', width=25, align='R', 
                  formatter=lambda v: f"-${float(v):,.2f}"),
        PDFColumn(key='salario_neto', header='Salario Neto', width=25, align='R', 
                  formatter=lambda v: f"${float(v):,.2f}"),
        PDFColumn(key='estado_pago', header='Est. Pago', width=20, align='C',
                  formatter=lambda v: ["PENDIENTE", "PARCIAL", "PAGADO", "ANULADO"][v]), # Asumiendo 0-3
    ]
    # Suma de anchos: 20+45+25+25+25+25+20 = 185 mm. OK para A4.

    # Imprimir encabezados de la tabla de detalles
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font('Arial', 'B', 8)
    for col in detail_columns_definition:
        pdf.cell(col.width, 7, col.header, 1, 0, 'C', 1)
    pdf.ln()

    # Imprimir contenido de la tabla de detalles
    pdf.set_font('Arial', '', 8)
    cell_height = 6 
    
    for row in detalles_data:
        # Control de salto de página
        if pdf.get_y() + cell_height > pdf.page_break_trigger:
            pdf.add_page()
            # Reimprimir encabezados en la nueva página
            pdf.set_fill_color(200, 220, 255)
            pdf.set_font('Arial', 'B', 8)
            for col in detail_columns_definition:
                pdf.cell(col.width, 7, col.header, 1, 0, 'C', 1)
            pdf.ln()
            pdf.set_font('Arial', '', 8)

        for i, col in enumerate(detail_columns_definition):
            value = row.get(col.key)
            
            # Formateador especial para el nombre completo
            if col.key == 'nombre_trabajador':
                formatted_value = col.formatter(value, row)
            else:
                formatted_value = col.formatter(value)
            
            border_style = 'LRB' if i == len(detail_columns_definition) - 1 else 'LB'
            
            pdf.cell(col.width, cell_height, formatted_value, border_style, 0, col.align)
        
        pdf.ln()

    return bytes(pdf.output(dest='B'))


# --- Función de Prueba Rápida (para diagnóstico) ---
async def generate_test_pdf() -> bytes:
    """Genera un PDF de prueba simple para verificar la librería."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Documento de Prueba Funciona Correctamente!", ln=1, align="C")
    return bytes(pdf.output(dest='B'))