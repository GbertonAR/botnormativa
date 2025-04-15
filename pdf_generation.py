# pdf_generation.py
from flask import Blueprint, request, send_file
from fpdf import FPDF
import io

pdf_bp = Blueprint('pdf_generation', __name__, url_prefix='/pdf')

@pdf_bp.route('/generar', methods=['POST'])
def generar_pdf():
    respuesta = request.form.get('respuesta')
    if not respuesta:
        return "Error: No se proporcionó la respuesta.", 400

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=respuesta)

    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)

    return send_file(buffer, download_name='respuesta_normativa.pdf', as_attachment=True)