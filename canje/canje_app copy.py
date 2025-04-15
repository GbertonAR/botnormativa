import os
import re
from flask import Blueprint, render_template, request, jsonify
from PIL import Image
import pytesseract
from passporteye import read_mrz
# Importa tu conexión a la base de datos y modelos si los tienes
from .canje_modelos import Provincia, Municipio, Canje
from .adm_db import get_db, close_db, insertar_datos_canje
import random
import time
#from .canje_app import canje_bp
#from pymrz import MRZ
#from pymrz.mrz import MRZ  # Intenta esta importación

canje_bp = Blueprint('canje', __name__, template_folder='../templates', static_folder='../static', url_prefix='/canje')

# Asegúrate de que la ruta a tesseract esté configurada correctamente
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Ajusta según tu sistema
pytesseract.tessdata_dir = '/usr/share/tesseract-ocr/5/tessdata'  # Reemplaza con la ruta real a tu tessdata


def extract_text_from_image(image_path):
    try:
        img = Image.open(image_path)
        #text = pytesseract.image_to_string(img, lang='spa')
        text = pytesseract.image_to_string(img, lang='eng')
        return text
    except Exception as e:
        print(f"Error al realizar OCR: {e}")
        return None

def extract_dni_data(image_path):
    """
    Intenta leer la información del MRZ del dorso del DNI utilizando la biblioteca passporteye.
    """
    try:
        img = Image.open(image_path)
        mrz_data = read_mrz(image_path)

        print(f"Datos MRZ brutos (passporteye): {mrz_data}")
        print(f"¿MRZ Válido? (passporteye): {mrz_data.valid}")
        print(f"Campos MRZ (passporteye): {mrz_data.__dict__}")

        if mrz_data:
            nombre = mrz_data.names
            apellidos = mrz_data.surname
            numero_documento = mrz_data.number.rstrip('<')  # Eliminar caracteres '<' al final
            print(f"Nombre extraído: {nombre}")
            print(f"Apellidos extraídos: {apellidos}")
            print(f"Número de Documento extraído: {numero_documento}")
            return nombre, apellidos, numero_documento
        else:
            print("passporteye no detectó ningún MRZ.")
            return None, None, None

    except Exception as e:
        print(f"Error al leer el MRZ con passporteye: {e}")
        return None, None, None

@canje_bp.route('/', methods=['GET'])
def canje_form():
    return render_template('canje.html')

@canje_bp.route('/capture_canje', methods=['GET'])
def capture_canje_form():
    return render_template('capture_canje.html')

@canje_bp.route('/upload', methods=['POST'])
def upload_document():
    if 'document' not in request.files:
        return jsonify({'error': 'No se proporcionó ningún documento'}), 400

    document = request.files['document']
    document_type = request.form.get('document_type')

    if document.filename == '':
        return jsonify({'error': 'No se seleccionó ningún documento'}), 400

    if document:
        filename = f"{document_type}_{document.filename}"
        filepath = os.path.join('temp_uploads', filename)  # Guardar temporalmente
        os.makedirs('temp_uploads', exist_ok=True)
        document.save(filepath)

        if document_type == 'dorso_dni':
            nombre, apellidos, numero_documento = extract_dni_data(filepath)
            os.remove(filepath)  # Eliminar archivo temporal
            return jsonify({'filename': filename, 'document_type': document_type, 'nombre': nombre,
                            'apellidos': apellidos, 'numero_documento': numero_documento})
        else:
            text = extract_text_from_image(filepath)
            os.remove(filepath)  # Eliminar archivo temporal
            return jsonify({'filename': filename, 'document_type': document_type, 'ocr_text': text})

    return jsonify({'error': 'Error al cargar el documento'}), 500

@canje_bp.route('/procesar', methods=['POST'])
def procesar_documentos():
    # Aquí recibirás los datos de los documentos (por ahora solo el último cargado)
    # La lógica para procesar los 8 documentos y realizar el OCR se implementará aquí
    if 'documents' not in request.files:
        return jsonify({'error': 'No se proporcionaron documentos para procesar'}), 400

    document = request.files['documents']
    filename = document.filename
    filepath = os.path.join('temp_uploads', filename)
    os.makedirs('temp_uploads', exist_ok=True)
    document.save(filepath)

    ocr_text = extract_text_from_image(filepath)
    os.remove(filepath)

    return jsonify({'message': 'Documentos recibidos para procesamiento', 'filename': filename, 'ocr_text': ocr_text})

@canje_bp.route('/results', methods=['GET'])
def show_results():
    nombre = request.args.get('nombre')
    apellidos = request.args.get('apellidos')
    numero_documento = request.args.get('numero_documento')
    ocr_text = request.args.get('ocr_text')
    return render_template('results.html', nombre=nombre, apellidos=apellidos, numero_documento=numero_documento, ocr_text=ocr_text)

@canje_bp.route('/provincias', methods=['GET'])
def get_provincias():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT ID, Nombre FROM Provincias ORDER BY Nombre")
    provincias = [{'id': row[0], 'nombre': row[1]} for row in cursor.fetchall()]
    close_db(conn)
    return jsonify(provincias)

@canje_bp.route('/municipios/<int:provincia_id>', methods=['GET'])
def get_municipios(provincia_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT ID, Nombre FROM Municipios WHERE Id_Provincia = ? ORDER BY Nombre", (provincia_id,))
    municipios = [{'id': row[0], 'nombre': row[1]} for row in cursor.fetchall()]
    close_db(conn)
    return jsonify(municipios)

@canje_bp.route('/guardar_datos', methods=['POST'])
def guardar_datos():
    data = request.json
    # Aquí iría la lógica para guardar todos los datos en la base de datos
    # (datos extraídos y los seleccionados por el usuario)
    print("Datos a guardar:", data)
    return jsonify({'success': True, 'message': 'Datos guardados'}), 200

# --- Rutas para cargar provincias y municipios (usando SQLAlchemy) ---
@canje_bp.route('/canje/provincias')
def get_provincias_sqlalchemy():
    provincias = Provincia.query.all()
    provincias_lista = [{'id': p.id, 'nombre': p.nombre} for p in provincias]
    return jsonify(provincias_lista)

@canje_bp.route('/canje/municipios/<int:provincia_id>')
def get_municipios_sqlalchemy(provincia_id):
    """
    Obtiene la lista de municipios para una provincia específica.

    Args:
        provincia_id (int): El ID de la provincia para la cual se desean obtener los municipios.

    Returns:
        jsonify: Una respuesta JSON que contiene una lista de diccionarios,
                 donde cada diccionario representa un municipio con su ID y nombre.
                 Si no se encuentran municipios para la provincia, devuelve una lista vacía.
    """
    municipios = Municipio.query.filter_by(provincia_id=provincia_id).all()
    municipios_lista = [{'id': m.id, 'nombre': m.nombre} for m in municipios]
    return jsonify(municipios_lista)