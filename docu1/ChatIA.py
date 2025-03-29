import google.generativeai as genai
import os
import sqlite3
import logging

# Configurar API Key de Gemini
genai.configure(api_key="AIzaSyALSGwm8GtQNIyiofZJ0fBZf2jvAbpz_vo")
# 📂 Ruta de los archivos y base de datos
CARPETA_DOCS = r"C:\GBerton2025\Desarrollos\IA_Normativa\doc1"
DB_PATH = os.path.join(CARPETA_DOCS, "normativas.db")

# 🔍 Función para consultar normativas en SQLite
def obtener_normativa(numero):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT contenido FROM normativas WHERE numero = ?", (numero,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else "No se encontró la normativa."

# 🔄 Consulta a Gemini con contexto de la base de datos
def consulta_gemini(numero, pregunta):
    texto_normativa = obtener_normativa(numero)
    
    if texto_normativa == "No se encontró la normativa.":
        return texto_normativa

    #model = genai.GenerativeModel("gemini-pro")
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = f"{texto_normativa}\n\nPregunta: {pregunta}"
    response = model.generate_content(prompt)
    return response.text

# 🏁 Ejemplo de uso
pregunta_usuario = "¿Qué cambios introduce el Decreto 196/2025?"
respuesta = consulta_gemini(196, pregunta_usuario)
print(respuesta)
