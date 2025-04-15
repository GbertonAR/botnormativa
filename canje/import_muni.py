import csv
import sqlite3
import os

# Define la ruta al archivo CSV de municipios
csv_municipios_path = 'Muni.csv'  # Ajusta la ruta si es diferente

# Define la ruta a la base de datos SQLite
db_file_path = 'canje_db.db'

def cargar_municipios_desde_csv(csv_path, db_path):
    """
    Lee datos de un archivo CSV (separado por punto y coma) y los carga en la tabla Municipios de la base de datos,
    relacionándolos con la tabla Provincias. Se espera que la primera fila del CSV sea el encabezado.
    """
    try:
        if not os.path.exists(csv_path):
            print(f"Error: El archivo CSV de municipios '{csv_path}' no se encontró.")
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Crear un diccionario para mapear el nombre de la provincia a su ID
        cursor.execute("SELECT ID, Nombre FROM Provincias")
        provincias_dict = {row[1]: row[0] for row in cursor.fetchall()}

        with open(csv_path, 'r', encoding='latin-1') as csvfile:
            lector_csv = csv.reader(csvfile, delimiter=';')
            encabezado = next(lector_csv)  # Leer el encabezado

            try:
                nombre_municipio_col_index = encabezado.index('Municipios')
                id_provincia_tabla_col_index = encabezado.index('ID_Provincia_tabla')
                mail_institucional_col_index = encabezado.index('Mail_Institucional')
            except ValueError as e:
                print(f"Error: El archivo CSV de municipios no tiene las columnas esperadas: {e}")
                conn.close()
                return

            for fila in lector_csv:
                if len(fila) >= 3:
                    nombre_municipio = fila[nombre_municipio_col_index].strip()
                    id_provincia_tabla_str = fila[id_provincia_tabla_col_index].strip()
                    mail_institucional = fila[mail_institucional_col_index].strip() if len(fila) > mail_institucional_col_index else None

                    # Intentar convertir el ID de provincia del CSV a un entero
                    try:
                        id_provincia_tabla = int(id_provincia_tabla_str)
                    except ValueError:
                        print(f"Advertencia: No se pudo convertir a entero el ID de provincia '{id_provincia_tabla_str}' para el municipio '{nombre_municipio}'. Se omitirá.")
                        continue

                    # Buscar el ID de la provincia en nuestra tabla de Provincias
                    # No necesitamos buscar por nombre, ya que el CSV tiene el ID directamente
                    provincia_id_db = id_provincia_tabla

                    try:
                        cursor.execute(
                            "INSERT INTO Municipios (Nombre, Id_Provincia, Mail_Institucional) VALUES (?, ?, ?)",
                            (nombre_municipio, provincia_id_db, mail_institucional),
                        )
                    except sqlite3.ForeignKeyError:
                        print(f"Advertencia: No existe la provincia con ID '{provincia_id_db}' para el municipio '{nombre_municipio}'. Se omitirá.")
                    except sqlite3.IntegrityError:
                        print(f"Advertencia: El municipio '{nombre_municipio}' ya existe para la provincia con ID '{provincia_id_db}'.")
                    except sqlite3.Error as e:
                        print(f"Error al insertar el municipio '{nombre_municipio}': {e}")

            conn.commit()
            print("Datos de municipios cargados exitosamente en la tabla Municipios.")

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
    cargar_municipios_desde_csv(csv_municipios_path, db_file_path)