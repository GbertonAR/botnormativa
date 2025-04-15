import os
import re
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from PIL import Image
import pytesseract
from passporteye import read_mrz
#from passporteye.mrz.mrz import MRZ
#from passporteye.mrz.td import MRZ  # 'td' podría referirse a 'travel document'
# Importa tu conexión a la base de datos y modelos si los tienes
from .canje_modelos import Provincia, Municipio, Canje
from .adm_db import get_db, close_db, insertar_datos_canje
import random
import time
#from .canje_app import canje_bp
#from pymrz import MRZ
#from pymrz.mrz import MRZ  # Intenta esta importación
from datetime import datetime



# *** INSTRUCCIÓN IMPORTANTE: ESTE ES EL BLUEPRINT PARA LA FUNCIONALIDAD DE "CANJE" ***
canje_bp = Blueprint('canje', __name__, template_folder='../templates', static_folder='../static', url_prefix='/canje')
UPLOAD_FOLDER = os.path.join('canje', 'imagenes', 'aprocesar')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Asegúrate de que la ruta a tesseract esté configurada correctamente
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Ajusta según tu sistema
pytesseract.tessdata_dir = '/usr/share/tesseract-ocr/5/tessdata'  # Reemplaza con la ruta real a tu tessdata

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

# @canje_bp.route('/', methods=['GET'])
# def index():
#     return render_template('canje.html')

@canje_bp.route('/capture_canje', methods=['GET'])
def capture_canje_form():
    return render_template('capture_canje.html')

@canje_bp.route('/ver_datos_canje', methods=['GET'])
def capture_ver_datos_canje():
    return render_template('ver_canjes_db.html')

# @canje_bp.route('/upload', methods=['POST'])
# def upload_file():
#     if 'frente_dni' not in request.files:
#         return jsonify({'error': 'No se proporcionó el archivo del frente del DNI'}), 400
#     # ... (similar checks para otros archivos) ...

#     frente_dni = request.files['frente_dni']
#     dorso_dni = request.files.get('dorso_dni')
#     licencia_frente = request.files.get('licencia_frente')
#     licencia_dorso = request.files.get('licencia_dorso')
#     linti = request.files.get('linti')
#     curso_certificado = request.files.get('curso_certificado')
#     psicofisico_certificado = request.files.get('psicofisico_certificado')
#     legalidad_certificado = request.files.get('legalidad_certificado')

#     if frente_dni and allowed_file(frente_dni.filename):
#         filename_frente = f"frente_dni_{datetime.now().strftime('%Y%m%d%H%M%S')}.{frente_dni.filename.rsplit('.', 1)[1].lower()}"
#         frente_dni.save(os.path.join(UPLOAD_FOLDER, filename_frente))
#     else:
#         filename_frente = None

#     filename_dorso = None
#     if dorso_dni and allowed_file(dorso_dni.filename):
#         filename_dorso = f"dorso_dni_{datetime.now().strftime('%Y%m%d%H%M%S')}.{dorso_dni.filename.rsplit('.', 1)[1].lower()}"
#         dorso_dni.save(os.path.join(UPLOAD_FOLDER, filename_dorso))

#     filename_licencia_frente = None
#     if licencia_frente and allowed_file(licencia_frente.filename):
#         filename_licencia_frente = f"licencia_frente_{datetime.now().strftime('%Y%m%d%H%M%S')}.{licencia_frente.filename.rsplit('.', 1)[1].lower()}"
#         licencia_frente.save(os.path.join(UPLOAD_FOLDER, filename_licencia_frente))

#     filename_licencia_dorso = None
#     if licencia_dorso and allowed_file(licencia_dorso.filename):
#         filename_licencia_dorso = f"licencia_dorso_{datetime.now().strftime('%Y%m%d%H%M%S')}.{licencia_dorso.filename.rsplit('.', 1)[1].lower()}"
#         licencia_dorso.save(os.path.join(UPLOAD_FOLDER, filename_licencia_dorso))

#     filename_linti = None
#     if linti and allowed_file(linti.filename):
#         filename_linti = f"linti_{datetime.now().strftime('%Y%m%d%H%M%S')}.{linti.filename.rsplit('.', 1)[1].lower()}"
#         linti.save(os.path.join(UPLOAD_FOLDER, filename_linti))

#     filename_curso_certificado = None
#     if curso_certificado and allowed_file(curso_certificado.filename):
#         filename_curso_certificado = f"curso_certificado_{datetime.now().strftime('%Y%m%d%H%M%S')}.{curso_certificado.filename.rsplit('.', 1)[1].lower()}"
#         curso_certificado.save(os.path.join(UPLOAD_FOLDER, filename_curso_certificado))

#     filename_psicofisico_certificado = None
#     if psicofisico_certificado and allowed_file(psicofisico_certificado.filename):
#         filename_psicofisico_certificado = f"psicofisico_certificado_{datetime.now().strftime('%Y%m%d%H%M%S')}.{psicofisico_certificado.filename.rsplit('.', 1)[1].lower()}"
#         psicofisico_certificado.save(os.path.join(UPLOAD_FOLDER, filename_psicofisico_certificado))

#     filename_legalidad_certificado = None
#     if legalidad_certificado and allowed_file(legalidad_certificado.filename):
#         filename_legalidad_certificado = f"legalidad_certificado_{datetime.now().strftime('%Y%m%d%H%M%S')}.{legalidad_certificado.filename.rsplit('.', 1)[1].lower()}"
#         legalidad_certificado.save(os.path.join(UPLOAD_FOLDER, filename_legalidad_certificado))

#     mrz_data = None
#     frente_dni_path = os.path.join(UPLOAD_FOLDER, filename_frente) if filename_frente else None
#     if frente_dni_path:
#         try:
#             mrz_regions = read_mrz(frente_dni_path)
#             if mrz_regions:
#                 mrz_data = mrz_regions[0].to_dict()
#                 print("Datos MRZ brutos (passporteye):", mrz_regions[0])
#                 print("¿MRZ Válido? (passporteye):", mrz_regions[0].valid)
#                 print("Campos MRZ (passporteye):", mrz_data)
#         except Exception as e:
#             print(f"Error al leer MRZ: {e}")

#     extracted_data = {}
#     if mrz_data and mrz_data.get('valid'):
#         extracted_data['nombre'] = mrz_data.get('names', '').replace('<', ' ').strip().upper()
#         extracted_data['apellido'] = mrz_data.get('surname', '').replace('<', ' ').strip().upper()
#         extracted_data['dni'] = mrz_data.get('number', '').replace('<', '').strip()
#         print(f"Nombre extraído: {extracted_data.get('nombre')}")
#         print(f"Apellidos extraídos: {extracted_data.get('apellido')}")
#         print(f"Número de Documento extraído: {extracted_data.get('dni')}")

#     return jsonify({
#         'filenames': {
#             'frente_dni_imagen': filename_frente,
#             'dorso_dni_imagen': filename_dorso,
#             'licencia_frente_imagen': filename_licencia_frente,
#             'licencia_dorso_imagen': filename_licencia_dorso,
#             'linti_imagen': filename_linti,
#             'curso_certificado_imagen': filename_curso_certificado,
#             'psicofisico_certificado_imagen': filename_psicofisico_certificado,
#             'legalidad_certificado_imagen': filename_legalidad_certificado
#         },
#         'extracted_data': extracted_data
#     })
    
    
##### Por mi cuenta #####
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
    success, message = insertar_datos_canje(data)                                                                                                                     
    return jsonify({'success': True, 'message': 'Datos guardados'}), 200

    
# TESTEO LUNES 14/4 
# @canje_bp.route('/guardar_datos', methods=['POST'])
# def guardar_datos():
#     data = request.json
#     # Llama a la función insertar_datos_canje en adm_db.py para guardar los datos en la base de datos
#     success, message = insertar_datos_canje(data)
#     if success:
#         return jsonify({'message': 'Datos de canje guardados exitosamente', 'id': message}), 201
#     else:
#         return jsonify({'error': f'Error al guardar los datos: {message}'}), 500
    
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

    close_db(conn)  # <--- Cierra la conexión DESPUÉS de ambas consultas

    return jsonify({'registros': resultados, 'totales': dict(totales)})

# NUEVA RUTA PARA VER EL DETALLE DEL REGISTRO
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
        return render_template('detalle_canje.html', registro=dict(registro)) # CREA ESTE NUEVO TEMPLATE
    else:
        return "Registro no encontrado", 404
# def obtener_datos_canje():
#     conn = get_db()
#     cursor = conn.cursor()
#     estado_filtro = request.args.get('estado')
#     query = "SELECT * FROM DatosDeCanje"
#     params = ()
#     order_by_clause = """
#         ORDER BY CASE ciudadano_presencial
#             WHEN 'SI' THEN 0
#             WHEN 'NO' THEN 1
#             ELSE 2
#         END
#     """
#     # if estado_filtro:
#     #     query += " WHERE estado = ? ORDER BY ciudadano_presencial"
#     #     params = (estado_filtro,)
#     if estado_filtro:
#         query += " WHERE estado = ?"
#         params = (estado_filtro,)
#         query += " " + order_by_clause
#     else:
#         query += " " + order_by_clause
        
#     cursor.execute(query, params)
#     datos = cursor.fetchall()
#     close_db(conn)
#     # Formatear los datos como una lista de listas (o lista de diccionarios si prefieres)
#     resultados = [list(row) for row in datos]
#     return jsonify(resultados)    

# # --- Rutas para cargar provincias y municipios ---
# @canje_bp.route('/canje/provincias')
# def get_provincias_sqlalchemy():
#     provincias = Provincia.query.all()
#     provincias_lista = [{'id': p.id, 'nombre': p.nombre} for p in provincias]
#     return jsonify(provincias_lista)

# @canje_bp.route('/canje/municipios/<int:provincia_id>')
# def get_municipios_sqlalchemy(provincia_id):
#     municipios = Municipio.query.filter_by(provincia_id=provincia_id).all()
#     municipios_lista = [{'id': m.id, 'nombre': m.nombre} for m in municipios]
#     return jsonify(municipios_lista)

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
        return redirect(url_for('ver_registro.html', tramite_id=tramite_id))
    return render_template('buscar_registro.html')


# *** IMPORTANTE: NO DEBES TENER app = Flask(__name__) NI app.run() AQUÍ ***