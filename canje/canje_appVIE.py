import os
import re
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from PIL import Image, ImageEnhance
# import pytesseract  <-- ELIMINADO
from passporteye import read_mrz  

# Importa tu conexión a la base de datos y modelos si los tienes
from .canje_modelos import Provincia, Municipio, Canje
from .adm_db import get_db, close_db, insertar_datos_canje
import random
import time
from datetime import datetime

# Importar las bibliotecas de Azure
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

# *** INSTRUCCIÓN IMPORTANTE: ESTE ES EL BLUEPRINT PARA LA FUNCIONALIDAD DE "CANJE" ***
canje_bp = Blueprint('canje', __name__, template_folder='../templates', static_folder='../static', url_prefix='/canje')
UPLOAD_FOLDER = os.path.join('canje', 'imagenes', 'aprocesar')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
TEMP_UPLOAD_FOLDER = 'temp_uploads'
os.makedirs(TEMP_UPLOAD_FOLDER, exist_ok=True)

# *** CONFIGURACIÓN DE LAS CREDENCIALES DE AZURE ***
# Debes configurar estas variables de entorno o directamente aquí con tus claves y endpoint
#COMPUTER_VISION_ENDPOINT = os.environ.get("COMPUTER_VISION_ENDPOINT")
COMPUTER_VISION_ENDPOINT = "https://aicanje.cognitiveservices.azure.com/"
#COMPUTER_VISION_KEY = os.environ.get("COMPUTER_VISION_KEY")
COMPUTER_VISION_KEY = "4ftcMxAJZpHI5NYoXooXcTpqCUjWp4pRMLkK0RvIQC8r28hP4eDLJQQJ99BDAC4f1cMXJ3w3AAAFACOGuO6L"
DOCUMENT_INTELLIGENCE_ENDPOINT = os.environ.get("DOCUMENT_INTELLIGENCE_ENDPOINT")
DOCUMENT_INTELLIGENCE_KEY = os.environ.get("DOCUMENT_INTELLIGENCE_KEY")
DOCUMENT_INTELLIGENCE_ENDPOINT = "https://normaia.cognitiveservices.azure.com/"
DOCUMENT_INTELLIGENCE_KEY = "GAC94o2zvuvEbEAoHWQSAVgmA9c7Hlwqy4UoT6d7k6rhzhi6ZWYwJQQJ99BDACYeBjFXJ3w3AAALACOGXJ1t"

# Inicializar los clientes de Azure
computervision_client = None
if COMPUTER_VISION_ENDPOINT and COMPUTER_VISION_KEY:
    computervision_client = ComputerVisionClient(COMPUTER_VISION_ENDPOINT, CognitiveServicesCredentials(COMPUTER_VISION_KEY))
else:
    logging.warning("No se configuraron las credenciales de Computer Vision.")
    

document_intelligence_client = None
if DOCUMENT_INTELLIGENCE_ENDPOINT and DOCUMENT_INTELLIGENCE_KEY:
    document_intelligence_client = DocumentIntelligenceClient(DOCUMENT_INTELLIGENCE_ENDPOINT, AzureKeyCredential(DOCUMENT_INTELLIGENCE_KEY))
else:
    logging.warning("No se configuraron las credenciales de Document Intelligence.")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# *** FUNCIÓN DE EXTRACCIÓN DE TEXTO CON AZURE COMPUTER VISION ***
# def extract_text_from_image_azure(image_path):
#     if not computervision_client:
#         return "Error: Computer Vision no está configurado."
#     try:
#         with open(image_path, "rb") as image_stream:
#             read_response = computervision_client.read_in_stream(image_stream, raw=True)
#         read_operation_location = read_response.headers["Operation-Location"]
#         operation_id = read_operation_location.split("/")[-1]

#         while True:
#             read_result = computervision_client.get_read_result(operation_id)
#             if read_result.status not in ["notStarted", "running"]:
#                 break
#             time.sleep(1)

#         text = ""
#         if read_result.status == OperationStatusCodes.succeeded:
#             for read_result_page in read_result.analyze_result.read_results:
#                 for line in read_result_page.lines:
#                     text += line.text + "\n"
#         return text.strip()
#     except Exception as e:
#         logging.error(f"Error al realizar OCR con Azure Computer Vision: {e}")
#         return None

def extract_text_from_image_azure(image_bytes):
    ocr_result = {"status": "failed", "analyze_result": None, "error_message": None}
    if computervision_client is None:
        ocr_result["error_message"] = "Cliente de Azure Computer Vision no inicializado."
        return ocr_result
    try:
        logging.debug(f"Tipo de 'document' antes de analyze: {type(image_bytes)}")
        read_response = computervision_client.read(image_bytes, raw=True)
        operation_location = read_response.headers["Operation-Location"]
        operation_id = operation_location.split("/")[-1]
        read_result = computervision_client.get_read_result(operation_id)
        ocr_result["status"] = "succeeded"
        ocr_result["analyze_result"] = read_result.as_dict()
    except Exception as e:
        logging.error(f"Error al realizar OCR con Azure: {e}")
        ocr_result["error_message"] = str(e)
    return ocr_result

# *** FUNCIÓN DE EXTRACCIÓN DE DATOS DEL DNI CON AZURE DOCUMENT INTELLIGENCE ***
def extract_dni_data_azure(image_bytes):
    if not document_intelligence_client:
        return None, None, None
    try:
        logging.debug(f"Tipo de 'document' antes de analyze: {type(image_bytes)}")
        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-idDocument",
            document=image_bytes
        )
        result = poller.result()

        nombre = None
        apellidos = None
        numero_documento = None

        for doc in result.documents:
            for name, field in doc.fields.items():
                if name == "firstName":
                    nombre = field.value
                elif name == "lastName":
                    apellidos = field.value
                elif name == "documentNumber":
                    numero_documento = field.value

        return nombre, apellidos, numero_documento
    except Exception as e:
        logging.error(f"Error al analizar el DNI con Azure Document Intelligence: {e}")
        return None, None, None

def extract_mrz_data(image_path):
    try:
        results = read_mrz(image_path)
        if results:
            mrz_data = results[0] # Suponiendo que solo hay un MRZ en la imagen
            return mrz_data.to_dict()
        else:
            return None
    except Exception as e:
        print(f"Error al leer el MRZ: {e}")
        return None

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
        filepath = os.path.join(TEMP_UPLOAD_FOLDER, filename)
        document.save(filepath)

        try:
            with open(filepath, "rb") as f:
                image_bytes = f.read()
            ocr_result = extract_text_from_image_azure(image_bytes)
            return jsonify({
                'filename': filename,
                'document_type': document_type,
                'ocr_result': ocr_result
            })
        finally:
            os.remove(filepath) # Asegurarse de eliminar el archivo temporal siempre

    return jsonify({'error': 'Error al cargar el documento'}), 500


    
@canje_bp.route('/upload_camara', methods=['POST'])
def upload_document_camara():
    if 'document' not in request.files:
        return jsonify({'error': 'No se proporcionó ninguna imagen'}), 400

    document = request.files['document']
    document_type = request.form.get('document_type')

    if document.filename == '':
        return jsonify({'error': 'No se seleccionó ninguna imagen'}), 400

    if document:
        filename = f"camara_{document_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png" # Nombre más descriptivo
        filepath = os.path.join(TEMP_UPLOAD_FOLDER, filename)
        document.save(filepath)

        try:
            if document_type == 'dorso_dni':
                nombre, apellidos, numero_documento = extract_dni_data_azure(filepath)
                if nombre and apellidos and numero_documento:
                    return jsonify({
                        'filename': filename,
                        'document_type': document_type,
                        'nombre': nombre,
                        'apellidos': apellidos,
                        'numero_documento': numero_documento
                    })
                else:
                    return jsonify({
                        'filename': filename,
                        'document_type': document_type,
                        'error': 'No se pudieron leer los datos del dorso del DNI (Azure).'
                    }), 400
            else:
                ocr_text = extract_text_from_image_azure(filepath)
                return jsonify({'filename': filename, 'document_type': document_type, 'ocr_text': ocr_text})
        finally:
            os.remove(filepath) # Asegurarse de eliminar el archivo temporal siempre

    return jsonify({'error': 'Error al cargar la imagen de la cámara'}), 500

@canje_bp.route('/', methods=['GET'])
def canje_form():
    return render_template('canje.html')

@canje_bp.route('/capture_canje', methods=['GET'])
def capture_canje_form():
    return render_template('capture_canje.html')

@canje_bp.route('/ver_datos_canje', methods=['GET'])
def capture_ver_datos_canje():
    return render_template('ver_canjes_db.html')




@canje_bp.route('/procesar', methods=['POST'])
def procesar_documentos():
    # Aquí recibirás los datos de los documentos capturados desde el frontend
    data = request.json
    print("Datos de los documentos recibidos para procesar:", data)

    processed_data = {}
    for doc_type, doc_info in data.items():
        if doc_info and doc_info.get('imageData'):
            image_data = doc_info['imageData'].split(',')[1] # Remove data:image/png;base64,
            image_bytes = base64.b64decode(image_data)
            temp_filename = os.path.join(TEMP_UPLOAD_FOLDER, f"processed_{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            with open(temp_filename, 'wb') as f:
                f.write(image_bytes)

            if doc_type == 'dorso_dni':
                nombre, apellidos, numero_documento = extract_dni_data_azure(temp_filename)
                processed_data[doc_type] = {'nombre': nombre, 'apellidos': apellidos, 'numero_documento': numero_documento}
            else:
                ocr_text = extract_text_from_image_azure(temp_filename)
                processed_data[doc_type] = {'ocr_text': ocr_text}

            os.remove(temp_filename)
        else:
            processed_data[doc_type] = {'error': 'No se proporcionó imagen para este documento.'}

    return jsonify({'message': 'Documentos procesados con Azure', 'processed_data': processed_data})

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
    print("Datos a guardar:", data)
    success, message = insertar_datos_canje(data)
    return jsonify({'success': True, 'message': 'Datos guardados'}), 200

@canje_bp.route('/obtener_datos_canje', methods=['GET'])
def obtener_datos_canje():
    conn = get_db()
    cursor = conn.cursor()
    estado_filtro = request.args.get('estado')
    query = """
        SELECT
            dc.*,
            p.nombre AS nombre_provincia,
            m.nombre AS nombre_municipio
        FROM
            DatosDeCanje dc
        LEFT JOIN
            provincias p ON dc.provincia_id = p.id
        LEFT JOIN
            municipios m ON dc.municipio_id = m.id
    """
    params = ()
    order_by_clause = """
        ORDER BY CASE dc.ciudadano_presencial
            WHEN 'SI' THEN 0
            WHEN 'NO' THEN 1
            ELSE 2
        END
    """
    where_clause = ""
    if estado_filtro:
        where_clause = " WHERE dc.estado = ?"
        params = (estado_filtro,)

    full_query = query + where_clause + " " + order_by_clause
    cursor.execute(full_query, params)
    datos = cursor.fetchall()
    resultados = [dict(row) for row in datos]

    # Calcular los totales usando SQL
    totales_query = """
        SELECT
            COUNT(*) AS total_tramites,
            SUM(CASE WHEN ciudadano_presencial = 'SI' THEN 1 ELSE 0 END) AS total_presencial,
            SUM(CASE WHEN ciudadano_presencial = 'NO' THEN 1 ELSE 0 END) AS total_no_presencial,
            SUM(CASE WHEN estado = 'Finalizado' THEN 1 ELSE 0 END) AS total_terminados
        FROM
            DatosDeCanje
    """
    totales_params = ()
    if estado_filtro:
        totales_query += " WHERE estado = ?"
        totales_params = (estado_filtro,)

    cursor.execute(totales_query, totales_params)
    totales = cursor.fetchone()

    close_db(conn)

    return jsonify({'registros': resultados, 'totales': dict(totales)})

@canje_bp.route('/detalle/<int:id>')
def ver_detalle(id):
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT
            dc.*,
            p.nombre AS nombre_provincia,
            m.nombre AS nombre_municipio
        FROM
            DatosDeCanje dc
        LEFT JOIN
            provincias p ON dc.provincia_id = p.id
        LEFT JOIN
            municipios m ON dc.municipio_id = m.id
        WHERE dc.id = ?
    """
    cursor.execute(query, (id,))
    registro = cursor.fetchone()
    close_db(conn)
    if registro:
        return render_template('detalle_canje.html', registro=dict(registro))
    else:
        return "Registro no encontrado", 404

@canje_bp.route('/registro/<tramite_id>')
def ver_registro(tramite_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM DatosDeCanje WHERE numero_de_tramite = ?", (tramite_id,))
    registro = cursor.fetchone()
    close_db()

    if registro:
        column_names = [description[0] for description in cursor.description]
        registro_dict = dict(zip(column_names, registro))
        return render_template('ver_registro.html', registro=registro_dict)
    else:
        return render_template('registro_no_encontrado.html', tramite_id=tramite_id)

@canje_bp.route('/buscar_registro', methods=['GET', 'POST'])
def buscar_registro():
    if request.method == 'POST':
        tramite_id = request.form.get('tramite_id')
        return redirect(url_for('ver_registro', tramite_id=tramite_id))
    return render_template('buscar_registro.html')

# *** IMPORTANTE: NO DEBES TENER app = Flask(__name__) NI app.run() AQUÍ ***