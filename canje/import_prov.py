# Este script carga datos de provincias desde un archivo CSV a una base de datos SQLite.
# Asegúrate de que el archivo CSV tenga una columna llamada 'Nombre' para las provincias.
# El script maneja errores comunes como la falta de archivo, problemas de conexión a la base de datos y errores de integridad.
import csv
import sqlite3
import os

# Define la ruta al archivo CSV
csv_file_path = 'Provincias.csv'  # Ajusta la ruta si es diferente

# Define la ruta a la base de datos SQLite
db_file_path = 'canje_db.db'

def cargar_provincias_desde_csv(csv_path, db_path):
    """
    Lee datos de un archivo CSV y los carga en la tabla Provincias de la base de datos.
    El archivo CSV debe tener al menos una columna con el nombre de la provincia.
    Se espera que la primera fila del CSV sea el encabezado.
    """
    try:
        if not os.path.exists(csv_path):
            print(f"Error: El archivo CSV '{csv_path}' no se encontró.")
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # with open(csv_path, 'r', encoding='latin-1') as csvfile:
        #     lector_csv = csv.reader(csvfile)
        #     encabezado = next(lector_csv)  # Leer la primera fila como encabezado
        with open(csv_path, 'r', encoding='latin-1') as csvfile:
            lector_csv = csv.reader(csvfile, delimiter=';')  # Especificamos el delimitador como punto y coma
            encabezado = next(lector_csv)

            # Asumimos que el nombre de la columna con el nombre de la provincia es 'Nombre'
            # Puedes ajustar esto si tu archivo CSV tiene un encabezado diferente
            try:
                nombre_columna_index = encabezado.index('Provincia')
            except ValueError:
                print(f"Error: El archivo CSV no tiene una columna con el encabezado 'Nombre'. Encabezados encontrados: {encabezado}")
                conn.close()
                return

            for fila in lector_csv:
                if len(fila) > nombre_columna_index:
                    nombre_provincia = fila[nombre_columna_index].strip()
                    try:
                        cursor.execute("INSERT INTO Provincias (Nombre) VALUES (?)", (nombre_provincia,))
                    except sqlite3.IntegrityError:
                        print(f"Advertencia: La provincia '{nombre_provincia}' ya existe en la base de datos.")
                    except sqlite3.Error as e:
                        print(f"Error al insertar '{nombre_provincia}': {e}")

            conn.commit()
            print("Datos de provincias cargados exitosamente en la tabla Provincias.")

    except sqlite3.Error as e:
        print(f"Error de SQLite: {e}")
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{csv_path}'.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == '__main__':
    cargar_provincias_desde_csv(csv_file_path, db_file_path)