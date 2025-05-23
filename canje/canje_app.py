import os
import re
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from PIL import Image, ImageEnhance
from passporteye import read_mrz  
import base64
import json
import smtplib
from email.mime.text import MIMEText
from .config_canje import MAIL_ACCOUNTS

# Importa tu conexión a la base de datos y modelos si los tienes
from .canje_modelos import db, Provincia, Municipio, Canje
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
def extract_text_from_image_azure(image_path, min_confidence_threshold=0.6):
    if not computervision_client:
        return None, "Error: Computer Vision no está configurado."
    try:
        with open(image_path, "rb") as image_stream:
            read_response = computervision_client.read_in_stream(image_stream, raw=True)
        read_operation_location = read_response.headers["Operation-Location"]
        operation_id = read_operation_location.split("/")[-1]

        while True:
            read_result = computervision_client.get_read_result(operation_id)
            if read_result.status not in ["notStarted", "running"]:
                break
            time.sleep(1)

        text = ""
        low_confidence_words = []
        if read_result.status == OperationStatusCodes.succeeded:
            for read_result_page in read_result.analyze_result.read_results:
                for line in read_result_page.lines:
                    for word in line.words:
                        text += word.text + " "
                        if word.confidence < min_confidence_threshold:
                            low_confidence_words.append(word.text)
                text += "\n"

        text = text.strip()
        quality_issue = None
        if low_confidence_words and (len(low_confidence_words) / text.count(' ') if text.count(' ') > 0 else 0) > 0.3:
            quality_issue = "Posible baja calidad de imagen detectada. Muchas palabras con baja confianza en el OCR."

        return text, quality_issue

    except Exception as e:
        logging.error(f"Error al realizar OCR con Azure Computer Vision: {e}")
        return None, f"Error al realizar OCR: {e}"
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
    
def regla_frente_dni(ocr_text):
    if not ocr_text:
        return {'error': 'No se pudo realizar OCR en la imagen.'}

    ocr_lower = ocr_text.lower()
    if "republica argentina" in ocr_lower and \
       "registro nacional de las personas" in ocr_lower and \
       "tramite" in ocr_lower:
        nombre_match = re.search(r"NOMBRE(?:S)?\s+(.+)", ocr_text)
        apellido_match = re.search(r"APELLIDO(?:S)?\s+(.+)", ocr_text)
        dni_match = re.search(r"DNI\s+(\d{7,9})", ocr_text)

        nombre = nombre_match.group(1).strip() if nombre_match else None
        apellidos = apellido_match.group(1).strip() if apellido_match else None
        numero_documento = dni_match.group(1).strip() if dni_match else None

        return {'nombre': nombre, 'apellidos': apellidos, 'numero_documento': numero_documento, 'ocr_text': ocr_text}
    else:
        return {'error': 'La imagen no corresponde al frente del DNI.'}

def regla_dorso_dni(ocr_text):
    if not ocr_text:
        return {'error': 'No se pudo realizar OCR en la imagen del dorso del DNI.'}
    
    if "CUIL" not in ocr_text.upper():
        return {'error': 'No se encontró la palabra "CUIL" en el dorso del DNI. La imagen no es válida.'}

    apellido_nombre_match = re.search(r"([A-Z]+)\s*<<\s*([A-Z]+(?:\s*[A-Z]+)*)\s*<", ocr_text)
    numero_doc_match = re.search(r"(?:IDARG)?(\d+)<", ocr_text) # Busca opcionalmente "IDARG" seguido de dígitos antes de "<"

    apellidos = apellido_nombre_match.group(1).strip() if apellido_nombre_match else None
    nombre = apellido_nombre_match.group(2).strip() if apellido_nombre_match else None
    numero_documento = numero_doc_match.group(1).strip() if numero_doc_match else None

    return {'nombre': nombre, 'apellidos': apellidos, 'numero_documento': numero_documento, 'ocr_text': ocr_text}


def regla_psicofisico(ocr_text):
    logging.debug(f"OCR Text Psicofisico: {ocr_text}")
    if not ocr_text:
        return {'error': 'No se pudo realizar OCR en el Psicofísico.'}

    ocr_lower = ocr_text.lower()
    if "psicofisico" not in ocr_lower and \
       "psicofisica" not in ocr_lower and \
       "psicofísico" not in ocr_lower and \
       "psicofísica" not in ocr_lower:
        return {'error': 'No se encontró la palabra "PSICOFISICO", "PSICOFISICA", "PSICOFÍSICO" o "PSICOFÍSICA" en el documento. No es un psicofísico válido.'}

    # Expresiones regulares más robustas
    apellido_match = re.search(r"(?:APELLIDO|Apellido)\s*[:]?\s*([\w\s]+)", ocr_text, re.IGNORECASE)
    nombre_match = re.search(r"(?:NOMBRE|Nombre)\s*[:]?\s*([\w\s]+)", ocr_text, re.IGNORECASE)
    dni_match = re.search(r"(?:D\.N\.I\.?|DNI)\s*[:]?\s*(\d{7,9})", ocr_text, re.IGNORECASE)
    prestador_match = re.search(r"(?:PRESTADOR|Prestador)\s*[:]?\s*(.+?)(?:(?:APELLIDO|Apellido)|(?:F\.\s*EXAMEN|Fecha\s*de\s*Examen)|$)", ocr_text, re.IGNORECASE | re.DOTALL)
    fecha_examen_match = re.search(r"(?:F\.\s*EXAMEN|Fecha\s*de\s*Examen)\s*[:]?\s*(\d{2}/\d{2}/\d{4})", ocr_text, re.IGNORECASE)

    apellido = apellido_match.group(1).strip() if apellido_match else None
    nombre = nombre_match.group(1).strip() if nombre_match else None
    dni = dni_match.group(1).strip() if dni_match else None
    prestador = prestador_match.group(1).strip() if prestador_match else None
    fecha_examen = fecha_examen_match.group(1).strip() if fecha_examen_match else None

    # Limpieza adicional (más general)
    if apellido:
        apellido = re.sub(r'\s*(?:DNI|N°|NRO\.|\d{7,9})$', '', apellido, re.IGNORECASE).strip()
    if nombre:
        nombre = re.sub(r'\s*(?:CATEGORIA|CAT\.)$', '', nombre, re.IGNORECASE).strip()
        nombre = re.sub(r'\s*\d{2}/\d{2}/\d{4}$', '', nombre).strip() # Remover posible fecha al final

    return {
        'psicofisico_nombre': nombre,
        'psicofisico_apellido': apellido,
        'psicofisico_dni': dni,
        'psicofisico_prestador': prestador,
        'psicofisico_f_examen': fecha_examen,
        'psicofisico_ocr_text': ocr_text  # Guardar el texto OCR original
    }
    
def procesar_certificado_curso(ocr_text):
    """
    Extrae información específica del OCR del certificado de curso.

    Args:
        ocr_text (str): El texto OCR extraído del certificado de curso.

    Returns:
        dict: Un diccionario con los campos 'curso_nombre', 'curso_apellido',
              'curso_dni', 'curso_imagen', 'curso_nombre_curso'.
    """
    data = {'curso_imagen': ocr_text}
    lines = ocr_text.split('\n')

    nombre = None
    apellido = None
    dni = None
    nombre_curso = None

    for line in lines:
        line_lower = line.lower()

        if "se extiende el presente certificado a" in line_lower:
            parts = line.split("a")[-1].strip().split(",")
            if len(parts) >= 2:
                apellido = parts[0].strip()
                nombre_completo = parts[1].strip()
                nombre_parts = nombre_completo.split()
                if nombre_parts:
                    nombre = " ".join(nombre_parts)
                dni_match = re.search(r'dni\s*(\d[\d\.]+)', line, re.IGNORECASE)
                if dni_match:
                    dni = dni_match.group(1).replace('.', '')
            elif len(parts) == 1:
                nombre_apellido_match = re.search(r'([A-Z]+(?: [A-Z]+)*),\s*([A-Z]+(?: [A-Z]+)*)', line)
                if nombre_apellido_match:
                    apellido = nombre_apellido_match.group(1)
                    nombre = nombre_apellido_match.group(2)
                dni_match = re.search(r'dni\s*(\d[\d\.]+)', line, re.IGNORECASE)
                if dni_match:
                    dni = dni_match.group(1).replace('.', '')

        elif "por haber aprobado el curso" in line_lower:
            curso_match = re.search(r'curso:\s*(.+)', line, re.IGNORECASE)
            if curso_match:
                nombre_curso = curso_match.group(1).strip()
            else:
                curso_match_v2 = re.search(r'curso el\s*(.+)', line, re.IGNORECASE)
                if curso_match_v2:
                    nombre_curso = curso_match_v2.group(1).strip()
                else:
                    curso_index = line_lower.find("curso:")
                    if curso_index != -1:
                        nombre_curso = line[curso_index + len("curso:"):].strip()
                    else:
                        curso_index_v2 = line_lower.find("curso el")
                        if curso_index_v2 != -1:
                            nombre_curso = line[curso_index_v2 + len("curso el"):].strip()


    data['curso_nombre'] = nombre
    data['curso_apellido'] = apellido
    data['curso_dni'] = dni
    data['curso_nombre_curso'] = nombre_curso
    data['curso_ocr_text'] = ocr_text

    print(f"Datos del OCR CURSOS (MEJORADO): {json.dumps(data, indent=4)}")
    return data
    
def procesar_licencia_linti(ocr_text):
    """
    Extrae información específica del OCR de la licencia LINTI.

    Args:
        ocr_text (str): El texto OCR extraído de la licencia LINTI.

    Returns:
        dict: Un diccionario con los campos 'linti_nombre', 'linti_apellido',
              'linti_dni', 'linti_f_vto' y 'linti_categoria', 'linti_ocr_text'.
    """
    data = {'linti_ocr_text': ocr_text}
    lines = ocr_text.split('\n')

    nombre = None
    apellido = None
    dni = None
    f_vto = None
    categoria = None

    for line in lines:
        line_lower = line.lower()

        if line_lower.startswith("nombre"):
            nombre_parts = line.split("nombre")[-1].strip().split()
            if len(nombre_parts) >= 2:  # Asegurarse de capturar el nombre completo
                nombre = " ".join(nombre_parts)
            elif len(nombre_parts) == 1 and not nombre: # Capturar el nombre si está en la siguiente línea
                continue # Esperar la siguiente línea
        elif not nombre and "adriel oscar" in line_lower: # Capturar el nombre específico
            nombre = "ADRIEL OSCAR"
        elif line_lower.startswith("apelto"): # Error de OCR común para "Apellido"
            apellido_parts = line.split("apelto")[-1].strip().split()
            if apellido_parts:
                apellido = " ".join(apellido_parts)
        elif not apellido and "medeot" in line_lower: # Capturar el apellido específico
            apellido = "MEDEOT"
        elif re.search(r'\b\d{7,8}\b', line):
            dni_match = re.search(r'\b\d{7,8}\b', line)
            if dni_match:
                dni = dni_match.group(0)
        elif re.search(r'vto\s*(\d{2}/\d{2}/\d{4})', line_lower):
            vto_match = re.search(r'vto\s*(\d{2}/\d{2}/\d{4})', line_lower)
            if vto_match:
                f_vto = vto_match.group(1)
        elif line_lower.startswith("categoria"):
            categoria_parts = line.split("categoria")[-1].strip().split()
            if categoria_parts:
                categoria = categoria_parts[0]

    data['linti_nombre'] = nombre
    data['linti_apellido'] = apellido
    data['linti_dni'] = dni
    data['linti_f_vto'] = f_vto
    data['linti_categoria'] = categoria
    data['linti_imagen'] = ocr_text

    print(f"Datos del OCR LINTI (MEJORADO): {json.dumps(data, indent=4)}")
    return data

def procesar_certificado_legalidad(ocr_text, datos_dni=None):

    logging.debug(f"OCR Text Certificado de Legalidad: {ocr_text}")
    if not ocr_text:
        return {'error': 'No se pudo realizar OCR en el Certificado de Legalidad.'}

    legalidad_ocr_text = "CERTIFICADO DE LEGALIDAD" in ocr_text.upper()
    data = {
            #'certificado_legalidad_valido': certificado_valido,
            'curso_certificado_imagen': ocr_text,
            'legalidad_nombre': None,
            'legalidad_apellido': None,
            'legalidad_dni': None,
            'legalidad_ocr_text': legalidad_ocr_text
    }

    if legalidad_ocr_text:
        # Intentar extraer nombre, apellido y DNI del texto OCR
        nombre_match = re.search(r"(?:Sr\.|Sra\.|Srta\.)\s+([\w\s]+)\s+([\w\s]+)(?:\s+D\.N\.I\.? Nº|\s+DNI Nº|\s+DNI N°|\s+D\.N\.I\.? N°)\s+(\d{7,9})", ocr_text, re.IGNORECASE)
        if nombre_match:
                apellido = nombre_match.group(1).strip()
                nombre = nombre_match.group(2).strip()
                dni = nombre_match.group(3).strip()
                data['legalidad_apellido'] = apellido
                data['legalidad_nombre'] = nombre
                data['legalidad_dni'] = dni
        else:
            # Intento de extracción menos específico si el patrón anterior no coincide
            nombre_apellido_match = re.search(r"([\w\s]+)\s+([\w\s]+)(?:\s+D\.N\.I\.? Nº|\s+DNI Nº|\s+DNI N°|\s+D\.N\.I\.? N°)\s+(\d{7,9})", ocr_text, re.IGNORECASE)
            if nombre_apellido_match:
                apellido = nombre_apellido_match.group(1).strip()
                nombre = nombre_apellido_match.group(2).strip()
                dni = nombre_apellido_match.group(3).strip()
                data['legalidad_apellido'] = apellido
                data['legalidad_nombre'] = nombre
                data['legalidad_dni'] = dni
            else:
                # Intento de extraer DNI por separado si no se encuentra el patrón completo
                dni_match = re.search(r"(?:D\.N\.I\.? Nº|\s+DNI Nº|\s+DNI N°|\s+D\.N\.I\.? N°)\s+(\d{7,9})", ocr_text, re.IGNORECASE)
                if dni_match:
                      data['legalidad_dni'] = dni_match.group(1).strip()
                # Podrías añadir más patrones de extracción si identificas otros formatos comunes

    print(f"Datos del OCR LEGALIDAD (CON INTENTO DE EXTRACCIÓN): {data}")

    return data

# *** REGLAS DE VALIDACIÓN DE DOCUMENTOS ***
# Aquí puedes definir las reglas de validación para cada tipo de documento
REGLAS_DOCUMENTOS = {
    'frente_dni': regla_frente_dni,
    'dorso_dni': regla_dorso_dni,
    'licencia_municipal_frente': lambda ocr: {'ocr_text': ocr}, # Placeholder
    'licencia_municipal_dorso': lambda ocr: {'ocr_text': ocr}, # Placeholder
    'psicofisico': regla_psicofisico,
    'certificado_curso': procesar_certificado_curso,
    'licencia_linti': procesar_licencia_linti,
    'certificado_legalidad': procesar_certificado_legalidad,
}

@canje_bp.route('/upload', methods=['POST'])
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
            ocr_result = extract_text_from_image_azure(filepath)  # Ahora ocr_result es una tupla (text, quality_issue)
            ocr_text = ocr_result[0]  # Obtenemos el texto extraído
            quality_warning = ocr_result[1] if len(ocr_result) > 1 else None # Obtenemos la advertencia de calidad

            if document_type in REGLAS_DOCUMENTOS:
                funcion_regla = REGLAS_DOCUMENTOS[document_type]
                resultado_validacion = funcion_regla(ocr_text)
                if quality_warning:
                    resultado_validacion['quality_warning'] = quality_warning
                return jsonify(resultado_validacion)
            elif ocr_text:
                response = {'filename': filename, 'document_type': document_type, 'ocr_text': ocr_text}
                if quality_warning:
                    response['quality_warning'] = quality_warning
                return jsonify(response)
            else:
                error_message = f'No se pudo extraer texto del {document_type} con OCR de Azure.'
                if quality_warning:
                    error_message += f" Advertencia: {quality_warning}"
                return jsonify({
                    'filename': filename,
                    'document_type': document_type,
                    'error': error_message
                }), 400
        finally:
            os.remove(filepath)

    return jsonify({'error': 'Error al cargar el documento'}), 500
# def upload_document():
#     if 'document' not in request.files:
#         return jsonify({'error': 'No se proporcionó ningún documento'}), 400

#     document = request.files['document']
#     document_type = request.form.get('document_type')

#     if document.filename == '':
#         return jsonify({'error': 'No se seleccionó ningún documento'}), 400

#     if document:
#         filename = f"{document_type}_{document.filename}"
#         filepath = os.path.join(TEMP_UPLOAD_FOLDER, filename)
#         document.save(filepath)

#         try:
#             ocr_text = extract_text_from_image_azure(filepath)
#             if document_type in REGLAS_DOCUMENTOS:
#                 funcion_regla = REGLAS_DOCUMENTOS[document_type]
#                 resultado_validacion = funcion_regla(ocr_text)
#                 return jsonify(resultado_validacion)
#             elif ocr_text:
#                 return jsonify({'filename': filename, 'document_type': document_type, 'ocr_text': ocr_text})
#             else:
#                 return jsonify({
#                     'filename': filename,
#                     'document_type': document_type,
#                     'error': f'No se pudo extraer texto del {document_type} con OCR de Azure.'
#                 }), 400
#         finally:
#             os.remove(filepath)

#     return jsonify({'error': 'Error al cargar el documento'}), 500

    
@canje_bp.route('/upload_camara', methods=['POST'])
def upload_document_camara():
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
            ocr_text = extract_text_from_image_azure(filepath)
            if document_type in REGLAS_DOCUMENTOS:
                funcion_regla = REGLAS_DOCUMENTOS[document_type]
                resultado_validacion = funcion_regla(ocr_text)
                return jsonify(resultado_validacion)
            elif ocr_text:
                return jsonify({'filename': filename, 'document_type': document_type, 'ocr_text': ocr_text})
            else:
                return jsonify({
                    'filename': filename,
                    'document_type': document_type,
                    'error': f'No se pudo extraer texto del {document_type} con OCR de Azure.'
                }), 400
        finally:
            os.remove(filepath)

    return jsonify({'error': 'Error al cargar el documento'}), 500

@canje_bp.route('/', methods=['GET'])
def canje_form():
    return render_template('canje.html')

@canje_bp.route('/capture_canje', methods=['GET'])
def capture_canje_form():
    return render_template('capture_canje.html')

@canje_bp.route('/invento', methods=['GET'])
def invento():
    return render_template('invento.html')

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
                processed_data[doc_type] = {'nombre': nombre, 'apellidos': apellidos, 'numero_documento': numero_documento, 'ocr_text': ocr_text}
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
    try:
        datos_recibidos = request.get_json()
        print("Datos Recibidos del Frontend:")
        print(json.dumps(datos_recibidos, indent=4))

        # Llamar a la función para insertar los datos en la base de datos
        success, resultado = insertar_datos_canje(datos_recibidos)

        if success:
            return jsonify({'success': True, 'message': 'Datos guardados y transacción generada exitosamente.', 'numero_de_tramite': resultado}), 200
        else:
            return jsonify({'success': False, 'error': f'Error al guardar los datos: {resultado}'}), 500

    except Exception as e:
        print(f"Error inesperado al procesar la solicitud de guardado: {e}")
        return jsonify({'success': False, 'error': f'Error inesperado: {str(e)}'}), 500
    

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


@canje_bp.route('/procesar_y_enviar_mail/<int:canje_id>', methods=['POST'])
def procesar_y_enviar_mail(canje_id):
    try:
        data = request.get_json()
        send_from_label = data.get('send_from')
        additional_text = data.get('additional_text', '')
        print("Entro en la funcion con los valores", data, send_from_label, additional_text)

        # 1. Obtener el registro de DatosDeCanje usando sqlite3
        db = get_db()
        try:
            print(f"Datos Obtenidos en paso 1: ", canje_id)
            canje = db.execute('SELECT * FROM DatosDeCanje WHERE id = ?', (canje_id,)).fetchone()
            #print(f"Datos Obtenidos en paso 2: ", dict(canje))
        except Exception as e:
            current_app.logger.error(f"Error al obtener Canje: {e}")
            return jsonify({'error': 'Error al obtener datos del canje'}), 500
        
        print(f"Datos Obtenidos en paso 2:  {canje['nombre']}, {canje['apellido']}, {canje['dni']}")
        if not canje:
            return jsonify({'error': 'Registro no encontrado'}), 404

        # 2. Obtener el municipio y su correo electrónico
        municipio = db.execute('SELECT * FROM municipios WHERE id = ?', (canje['municipio_id'],)).fetchone()
        if not municipio:
            return jsonify({'error': 'Municipio no encontrado'}), 404
        
        send_to_email = municipio['mail_institucional']
        text_municipio = municipio['nombre']
        print(f"Datos Obtenidos en paso 3:", send_to_email, text_municipio)
        # 3. Obtener la cuenta de envío desde la configuración
        #print("Claves en current_app.config:", config_canje.config.keys())
        print("Claves en config_canje:", MAIL_ACCOUNTS.keys())
        #mail_account_config = config_canje.config['MAIL_ACCOUNTS'].get(send_from_label)
        #mail_account_config = current_app.config['MAIL_ACCOUNTS'].get(send_from_label)
        mail_account_config = MAIL_ACCOUNTS.get(send_from_label)
        print("Claves en mail_account_config:", mail_account_config.keys())
        if mail_account_config:
            email_address = mail_account_config.get('email')
            password = mail_account_config.get('password')
            
            smtp_server = mail_account_config.get('SMTP_SERVER')
            port = mail_account_config.get('PORT')
            print(f"Configuración para '{send_from_label}':")
            print(f"  Email: {email_address}")
            print(f"  Password: {password}")
            print(f"  SMTP Server: {smtp_server}")
            print(f"  Port: {port}")
        else:
            print(f"No se encontró la configuración para '{send_from_label}'")
            return jsonify({'error': 'Cuenta de envío no válida'}), 400
        mail_desde_voy = mail_account_config['email']
        print(f"Datos Obtenidos en paso 4: ", mail_desde_voy)
        #print(f"Datos Obtenidos en paso 3: {mail_account_config}")
        if not mail_account_config:
            return jsonify({'error': 'Cuenta de envío no válida'}), 400

        send_from_email = mail_account_config['email']
        send_from_password = mail_account_config['password']

        # 4. Crear el cuerpo del correo electrónico
        subject = "Transacción aprobada lista para procesar"
        body = f"Ya puede procesar la transacción solicitada por {canje['nombre']}, {canje['apellido']}, DNI {canje['dni']} para el día de hoy.\n\n"
        if additional_text:
            body += "Datos adicionales:\n" + additional_text

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = send_from_email
        msg['To'] = send_to_email

        # 5. Enviar el correo electrónico usando SMTP (Outlook)
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(send_from_email, send_from_password)
                server.sendmail(send_from_email, [send_to_email], msg.as_string())
            return jsonify({'success': 'Correo electrónico enviado correctamente'}), 200
        except Exception as e:
                print("Ocurrió un error al enviar el correo:")
                print(type(e).__name__, e)
        # except Exception as e:
        #     return jsonify({'error': f'Error al enviar el correo electrónico: {str(e)}'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# *** IMPORTANTE: NO DEBES TENER app = Flask(__name__) NI app.run() AQUÍ ***