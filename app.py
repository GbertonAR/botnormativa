from flask import Flask, request, jsonify, render_template, Blueprint, send_file
import sqlite3
import re
import os
import google.generativeai as genai
from fpdf import FPDF
import io

# *** INSTRUCCIÓN IMPORTANTE: IMPORTA EL BLUEPRINT DE "CANJE" ***
from canje.app_canje import canje_bp


app = Flask(__name__)

# *** INSTRUCCIÓN IMPORTANTE: REGISTRA EL BLUEPRINT DE "CANJE" EN LA APLICACIÓN PRINCIPAL ***
app.register_blueprint(canje_bp)


# Configurar API Key de Gemini
genai.configure(api_key="AIzaSyALSGwm8GtQNIyiofZJ0fBZf2jvAbpz_vo")

# 📂 Ruta de la base de datos
#DB_PATH = "/home/gberton/gberton2025/BOTNormativa/docu1/normativas.db"
#DB_PATH = ("/home/gberton/gberton2025/BOTNormativa/docu1/normativas.db")
#DB_PATH = os.environ.get("DB_PATH_NORMATIVAS")
#DB_PATH =("/home/site/wwwroot/normativas.db")
DB_PATH =("normativas.db")
#DB_PATH =("wwwroot/normativas.db")
#DB_PATH =("site/wwwroot/normativas.db")
print(f"Este es el valor de DB", DB_PATH)

# Importa el Blueprint
#from .pdf_generation import pdf_bp

# Registra el Blueprint en la aplicación
#app.register_blueprint(pdf_bp)


# 🔍 Función para extraer número de normativa desde la pregunta
def extraer_numero_normativa(pregunta):
    match = re.search(r'\b\d{3,4}\b', pregunta)  # Busca un número de 3 o 4 dígitos
    return int(match.group()) if match else None

# 🔍 Función para obtener normativa desde la base de datos
def obtener_normativa(numero=None, consulta=None):
    try:
        print(f"Ver valores de la cariable DB", DB_PATH)
        try:
            conn = sqlite3.connect(DB_PATH)
            print(f"Conexión a la base de datos exitosa: {DB_PATH}")
        except sqlite3.Error as e:
            print(f"Error al conectar a la base de datos: {e}")
            return None, f"Error al conectar a la base de datos: {e}"
        cursor = conn.cursor()
    except sqlite3.Error as e:
        print(f"Error al conectar a la base de datos '{DB_PATH}':")
        print(f"  Código de error: {e.sqlite_errorcode}")
        print(f"  Mensaje de error: {e}")
        conn = None  # Asegurar que conn sea None en caso de error
    

    if numero and consulta:
        # Buscar normativa por número y filtrar por contenido
        numero_norma_int = int(numero)
        #print(f"Estos son los valores de numero y consulta", {numero}, {consulta}, {numero_norma_int})
        cursor.execute("SELECT tipo, fecha, numero, contenido FROM normativas WHERE numero = ? OR contenido LIKE ?", 
                       (numero_norma_int, f"%{consulta}%"))
        resultado = cursor.fetchall()
    elif numero:
        # Buscar normativa solo por número
        cursor.execute("SELECT tipo, fecha, numero, contenido FROM normativas WHERE numero = ?", (numero,))
        resultado = cursor.fetchall()
    elif consulta:
        # Buscar normativa solo por consulta en el contenido
        cursor.execute("SELECT tipo, fecha, numero, contenido FROM normativas WHERE contenido LIKE ?", (f"%{consulta}%",))
        resultado = cursor.fetchall()
    else:
        return None
    
    conn.close()
    #print(f"Este es el RESULTADO DEL SELECT%%%%%%%%, {resultado[0]}, {resultado[1]}")
    if resultado:
        #return [row[0] for row in resultado]
        return resultado
    else:
        print("No se encontraron resultados.")
        return None
        
    #return None

    # resultados_formateados = []
    # for row in resultado:
    #     normativa = {
    #         "tipo": row[0],
    #         "numero": row[1],
    #         "fecha": row[2],
    #         "contenido": row[3]
    #     }
    #     resultados_formateados.append(normativa)
        
    # print(f"Antes de volver veamos como quedan los datos....")
    
    # # for item in (resultados_formateados - 1):
    # #     print(item)

    # return resultados_formateados


# 🔄 Consulta a Gemini con normativa
def consulta_gemini(pregunta, normativa_texto):
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = f"{normativa_texto}\n\nPregunta: {pregunta}"
    response = model.generate_content(prompt)
    return response.text

@app.route('/', methods=['GET', 'POST'])
def home():
    respuesta = None
    if request.method == 'POST':
        consulta = request.form['consulta']
        #respuesta = api_consulta(consulta)
    return render_template('index.html', respuesta=respuesta)

@app.route('/api/consulta', methods=['POST'])
def api_consulta():
    """Recibe una consulta y devuelve la normativa correspondiente, con integración de Gemini."""
    datos = request.get_json()
    print("Estos son los datos en crudo que llegan: {datos}", type(datos))
    numero_norma = datos.get("numero_norma")
    consulta = datos.get("consulta")
    print(f"Primer dato a verificar que info llega#####", datos, numero_norma, consulta)
    if not numero_norma and not consulta:
        return jsonify({"mensaje": "Debe ingresar al menos número de normativa o consulta por texto."}), 400

    # Buscar normativa en la base de datos
    normativas = obtener_normativa(numero_norma, consulta)
    #tipo = normativas[0]
    #fecha_d = normativas[1]
    # #print (f"aca vuelve de obtener normativa######", normativas)
    # data = request.get_json()
    # print(f"PARA VER SOBRE FINALIZACION", data, type(data))
    # tipo = data.get('tipo')
    # fecha_d= data.get('fecha')
    
    if normativas:
        resultados_api = []
        for normativa_data in normativas:
                       
            #print(f"Inspeccionando normativa_data: {normativa_data}")  # Agregar esta línea
            contenido = normativa_data[3]
            respuesta = consulta_gemini(consulta, contenido)
            resultados_api.append({
                "tipo": normativa_data[0],
                "fecha": normativa_data[1],
                "numero": normativa_data[2],
                "contenido": respuesta
            })
        #print(f"Aca esta el contenido de resultados_api: {resultados_api} y este es el tipo de variable:", type(resultados_api))
        #return jsonify({"normativas": resultados_api})
        #print (resultados_api[0])
        return jsonify(resultados_api)
    else:
        return jsonify({"mensaje": "No se encontraron normativas para la consulta."}), 404
    

    # if normativas:
    #     respuestas = [consulta_gemini(consulta, texto) for texto in normativas]
    #     print(f"Aca esta el contenido de respuestas: {respuestas} y este es el tipo de variable:", type(respuestas))
    #     return jsonify({
    #         "tipo": tipo,
    #         "fecha": fecha_d,
    #         "numero": numero_norma,
    #         "contenido": respuestas
    #     })
    #     #return jsonify({"respuestas": respuestas})
    # else:
    #     return jsonify({"mensaje": "No se encontraron normativas para la consulta."}), 404
# @pdf_bp.route('/generar', methods=['POST'])
# def generar_pdf():
#     respuesta = request.form.get('respuesta')
#     if not respuesta:
#         return "Error: No se proporcionó la respuesta.", 400

#     pdf = FPDF()
#     pdf.add_page()
#     pdf.set_font("Arial", size=12)
#     pdf.multi_cell(0, 10, txt=respuesta)

#     # Guardar el PDF en un buffer de memoria
#     buffer = io.BytesIO()
#     pdf.output(buffer)
#     buffer.seek(0)

#     return send_file(buffer, download_name='respuesta_normativa.pdf', as_attachment=True)

# En tu app.py principal, registra el Blueprint:
# from .pdf_generation import pdf_bp
# app.register_blueprint(pdf_bp)

if __name__ == '__main__':
    #app.run(debug=True, port=5000)
    app.run(host="0.0.0.0", debug=True)
