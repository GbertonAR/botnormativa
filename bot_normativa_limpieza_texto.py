import sqlite3
import re
import spacy
import nltk
from nltk.corpus import stopwords
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cargar modelos de spaCy y NLTK
nlp = spacy.load("es_core_news_md")
nltk.download('stopwords', quiet=True)
stop_words = set(stopwords.words('spanish'))

def limpiar_texto(texto):
    """Limpia y normaliza el texto."""
    texto = re.sub(r'[^\w\s.,()\-]', '', texto)  # Eliminar caracteres especiales
    texto = re.sub(r'\s+', ' ', texto)  # Eliminar múltiples espacios
    texto = texto.strip()  # Eliminar espacios al inicio y final
    return texto.lower()  # Convertir a minúsculas

def normalizar_texto(texto):
    """Normaliza el texto eliminando palabras vacías."""
    palabras = texto.split()
    palabras_filtradas = [palabra for palabra in palabras if palabra not in stop_words]
    return ' '.join(palabras_filtradas)

def limpiar_y_normalizar_articulos(nombre_db="./docu/normativas.db"):
    """Limpia y normaliza el contenido de la tabla 'articulos'."""
    try:
        conn = sqlite3.connect(nombre_db)
        cursor = conn.cursor()

        # Leer artículos
        cursor.execute("SELECT id, contenido FROM articulos")
        articulos = cursor.fetchall()

        for id_articulo, contenido in articulos:
            # Limpiar y normalizar el contenido
            contenido_limpio = limpiar_texto(contenido)
            contenido_normalizado = normalizar_texto(contenido_limpio)

            # Actualizar la base de datos
            cursor.execute("UPDATE articulos SET contenido = ? WHERE id = ?", (contenido_normalizado, id_articulo))
            logging.info(f"Artículo {id_articulo} limpiado y normalizado.")

        conn.commit()
        conn.close()
        logging.info("Proceso de limpieza y normalización de artículos completado.")

    except sqlite3.Error as e:
        logging.error(f"Error al limpiar y normalizar artículos: {e}")

if __name__ == "__main__":
    limpiar_y_normalizar_articulos()