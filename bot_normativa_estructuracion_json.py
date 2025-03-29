import sqlite3
import json
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def estructurar_articulos_json(nombre_db="./docu/normativas.db"):
    """Estructura los artículos en formato JSON y los almacena en la tabla 'articulos'."""
    try:
        conn = sqlite3.connect(nombre_db)
        cursor = conn.cursor()

        # Leer artículos
        cursor.execute("SELECT id, numero, contenido FROM articulos")
        articulos = cursor.fetchall()

        for id_articulo, numero, contenido in articulos:
            # Estructurar el artículo en formato JSON
            articulo_json = json.dumps({"numero": numero, "contenido": contenido}, ensure_ascii=False)

            # Actualizar la base de datos
            cursor.execute("UPDATE articulos SET contenido_json = ? WHERE id = ?", (articulo_json, id_articulo))
            logging.info(f"Artículo {id_articulo} estructurado en formato JSON.")

        conn.commit()
        conn.close()
        logging.info("Proceso de estructuración de artículos en JSON completado.")

    except sqlite3.Error as e:
        logging.error(f"Error al estructurar artículos en JSON: {e}")

if __name__ == "__main__":
    estructurar_articulos_json()