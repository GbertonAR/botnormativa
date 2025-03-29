import logging
import sqlite3
from flask import Flask, request, jsonify
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
import spacy
from sklearn.metrics.pairwise import cosine_similarity

# Configuración de logs
logging.basicConfig(filename='consultas.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Configurar Azure Cognitive Services (Text Analytics)
endpoint = "https://proyectobasew.cognitiveservices.azure.com/"
api_key = "Vtd7dMgdj4ELmBv5BBD9LhM5mrlusHAgXG7TiwQA6CcWk7OSlig4JQQJ99BCACYeBjFXJ3w3AAAEACOGFOja"

# Crear cliente de Text Analytics
client = TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))

# Inicializar Flask
app = Flask(__name__)

# Función para obtener el análisis de la pregunta con Azure
def obtener_analisis_azure(pregunta):
    try:
        response = client.analyze_sentiment([pregunta])
        sentiment = response[0].sentiment  # Ejemplo de análisis de sentimiento
        entities = client.recognize_entities([pregunta])[0].entities  # Detectar entidades en la pregunta
        return "sentimiento", ["entidad1", "entidad2"]
    except Exception as e:
        print(f"Error al analizar con Azure: {e}")
        return None, None

# Función para procesar la pregunta y buscar en la base de datos
def buscar_respuesta(pregunta):
    conn = sqlite3.connect('./docu/normativas.db')
    cursor = conn.cursor()

    # Usar Azure para obtener análisis (mantener si es necesario)
    sentiment, entities = obtener_analisis_azure(pregunta)
    #print(f"luego de azure deberia estar esto", pregunta, "#######", sentiment, ".......", entities)

    # Procesar la pregunta con spaCy para obtener el embedding
    nlp = spacy.load('es_core_news_md')
    pregunta_doc = nlp(pregunta)
    pregunta_vec = pregunta_doc.vector

    # Obtener todos los artículos desde la BD (usando JOIN)
    # cursor.execute("""
    #     SELECT normativas.tipo, normativas.numero, normativas.fecha, articulos.contenido
    #     FROM articulos
    #     JOIN normativas ON articulos.normativa_id = normativas.id
    # """)
    #print(f"Estos son los datos antes de buscar en la DB...", pregunta)
    # cursor.execute("""
    #         SELECT normativas.tipo, normativas.numero, normativas.fecha, articulos.contenido
    #         FROM articulos
    #         JOIN normativas ON  normativas.id = articulos.normativa_id 
    #         WHERE articulos.contenido LIKE BINARY '%pregunta%'
    # """)    
    cursor.execute(f"""
    SELECT normativas.tipo, normativas.numero, normativas.fecha, articulos.contenido
    FROM articulos
    JOIN normativas ON normativas.id = articulos.normativa_id
    WHERE articulos.contenido LIKE '%{pregunta}%'
    """)
    articulos = cursor.fetchall()
    print(f" esto son los datos en crudo de la DB$$$$$$$", articulos)

    # Convertir cada artículo a su embedding para compararlo con la pregunta
    articulos_vec = []
    for articulo in articulos:
        articulo_doc = nlp(articulo[3])  # columna 'contenido' del artículo
        articulo_vec = articulo_doc.vector
        articulos_vec.append((articulo, articulo_vec))

    # Calcular similitudes usando coseno
    respuestas = []
    for articulo, articulo_vec in articulos_vec:
        sim = cosine_similarity([pregunta_vec], [articulo_vec])[0][0]
        respuestas.append((articulo, sim))

    # Ordenar por similitud de mayor a menor
    respuestas.sort(key=lambda x: x[1], reverse=True)
    print (f"Esto es antes de elegir respuesta relevante......", respuestas, type(respuestas))
    print("#############")
    print("#############")
    # Elegir la respuesta más relevante
    mejor_respuesta = respuestas[0][0] if respuestas else None

    conn.close()  # Asegúrate de cerrar la conexión

    # Devolver respuesta formateada
    #print (f"mejor respuesta:-----", mejor_respuesta, type(mejor_respuesta))
    if mejor_respuesta:
            mejor_respuesta_dict = {
                "tipo": mejor_respuesta[0],
                "fecha": mejor_respuesta[1],
                "numero": mejor_respuesta[2],
                "contenido": mejor_respuesta[3]
            }
            return mejor_respuesta_dict
        #return {
        #    mejor_respuesta
            # "tipo": mejor_respuesta[0],
            # "numero": mejor_respuesta[1],
            # "fecha": mejor_respuesta[2],
            # "contenido": mejor_respuesta[3]  # Devolver el contenido completo
            #"tipo": mejor_respuesta["tipo"],
            #"numero": mejor_respuesta["numero"],
            #"fecha": mejor_respuesta["fecha"],
            #"contenido": mejor_respuesta["contenido"]
        #}
    else:
        return None

# Función para registrar logs
def registrar_log(pregunta, respuesta):
    logging.info(f"Pregunta: {pregunta}")
    logging.info(f"Respuesta: {respuesta}")

@app.route('/consultar', methods=['POST'])
def consultar():
    pregunta = request.args.get('pregunta')  # Recibir la pregunta como parámetro de la URL
    #print(pregunta)
    if not pregunta:
        return jsonify({"mensaje": "No se recibió una pregunta."}), 400

    #print(f"Aqui esta la pregunta realizada??????######", pregunta)
    respuesta = buscar_respuesta(pregunta)

    #print(f"Esto esta en respuesta ##########", respuesta)
    if respuesta:
        respuesta_texto = {
            "tipo": respuesta[1],
            "numero": respuesta[2],
            "fecha": respuesta[3],
            "contenido": respuesta[4]
        }
    else:
        respuesta_texto = {"mensaje": "No se encontró una respuesta relevante."}

    # Registrar la pregunta y la respuesta
    registrar_log(pregunta, respuesta_texto)

    return jsonify(respuesta_texto)

# Ejecutar la API en el servidor
if __name__ == '__main__':
    #app.run(debug=True)
    app.run(debug=True, port=5000)