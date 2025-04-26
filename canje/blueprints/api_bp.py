from flask import Blueprint, request, jsonify
import os
import base64
from .image_processing_utils import extract_text_from_image_azure, REGLAS_DOCUMENTOS, extract_dni_data_azure  # Mover lógica aquí
from datetime import datetime

image_processing_api_bp = Blueprint('image_processing_api', __name__, url_prefix='/api/v1')
TEMP_API_UPLOAD_FOLDER = 'temp_api_uploads'
os.makedirs(TEMP_API_UPLOAD_FOLDER, exist_ok=True)

@image_processing_api_bp.route('/process_document', methods=['POST'])
def process_document():
    if 'document' not in request.files and 'imageData' not in request.json:
        return jsonify({'error': 'No se proporcionó la imagen'}), 400

    document_type = request.form.get('document_type') if 'document' in request.files else request.json.get('document_type')
    if not document_type:
        return jsonify({'error': 'Se debe especificar el tipo de documento'}), 400

    image_path = None
    try:
        if 'document' in request.files:
            document = request.files['document']
            filename = f"api_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{document.filename.rsplit('.', 1)[1].lower() if '.' in document.filename else 'png'}"
            image_path = os.path.join(TEMP_API_UPLOAD_FOLDER, filename)
            document.save(image_path)
        elif 'imageData' in request.json:
            image_data = request.json['imageData'].split(',')[1]
            image_bytes = base64.b64decode(image_data)
            filename = f"api_camera_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            image_path = os.path.join(TEMP_API_UPLOAD_FOLDER, filename)
            with open(image_path, 'wb') as f:
                f.write(image_bytes)
        else:
            return jsonify({'error': 'Error al recibir la imagen'}), 400

        ocr_text = extract_text_from_image_azure(image_path)

        if document_type == 'dorso_dni':
            nombre, apellidos, numero_documento = extract_dni_data_azure(image_path)
            return jsonify({'nombre': nombre, 'apellidos': apellidos, 'numero_documento': numero_documento, 'ocr_text': ocr_text})
        elif document_type in REGLAS_DOCUMENTOS:
            funcion_regla = REGLAS_DOCUMENTOS[document_type]
            resultado_validacion = funcion_regla(ocr_text)
            return jsonify(resultado_validacion)
        elif ocr_text:
            return jsonify({'document_type': document_type, 'ocr_text': ocr_text})
        else:
            return jsonify({'error': f'No se pudo extraer texto del {document_type}'}), 400

    except Exception as e:
        return jsonify({'error': f'Error al procesar la imagen: {str(e)}'}), 500
    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

# En tu app.py o donde inicializas la aplicación Flask:
# from .api import image_processing_api_bp
# app.register_blueprint(image_processing_api_bp)

# Y tus rutas originales de /upload y /upload_camara se modificarían para llamar a este endpoint.