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


# --- Función de Prueba Rápida (para diagnóstico) ---
async def generate_test_pdf() -> bytes:
    """Genera un PDF de prueba simple para verificar la librería."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Documento de Prueba Funciona Correctamente!", ln=1, align="C")
    return bytes(pdf.output(dest='B'))