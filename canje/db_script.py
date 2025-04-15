import sqlite3
from datetime import date

DATABASE = 'canje_db.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Para acceder a las columnas por nombre
    return conn

def close_db(conn):
    if conn:
        conn.close()

def insertar_datos_canje(data):
    conn = get_db()
    cursor = conn.cursor()
    hoy = date.today().isoformat()
    try:
        cursor.execute("""
            INSERT INTO DatosDeCanje (
                fecha_ingreso, estado, dni, apellido, nombre,
                psicofisico_apellido, psicofisico_nombre, psicofisico_categoria,
                psicofisico_f_examen, psicofisico_f_dictamen, psicofisico_dni, psicofisico_imagen,
                curso_nombre, curso_apellido, curso_dni, curso_imagen,
                legalidad_nombre, legalidad_apellido, legalidad_dni, legalidad_imagen,
                provincia, municipio, ciudadano_presencial,
                frente_dni_imagen, dorso_dni_imagen, licencia_frente_imagen,
                licencia_dorso_imagen, linti_imagen, curso_certificado_imagen,
                psicofisico_certificado_imagen, legalidad_certificado_imagen
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            hoy, 'Ingresado', data.get('dni'), data.get('apellido'), data.get('nombre'),
            data.get('psicofisico_apellido'), data.get('psicofisico_nombre'), data.get('psicofisico_categoria'),
            data.get('psicofisico_f_examen'), data.get('psicofisico_f_dictamen'), data.get('psicofisico_dni'), data.get('psicofisico_imagen'),
            data.get('curso_nombre'), data.get('curso_apellido'), data.get('curso_dni'), data.get('curso_imagen'),
            data.get('legalidad_nombre'), data.get('legalidad_apellido'), data.get('legalidad_dni'), data.get('legalidad_imagen'),
            data.get('provincia'), data.get('municipio'), data.get('ciudadano_presencial'),
            data.get('frente_dni_imagen'), data.get('dorso_dni_imagen'), data.get('licencia_frente_imagen'),
            data.get('licencia_dorso_imagen'), data.get('linti_imagen'), data.get('curso_certificado_imagen'),
            data.get('psicofisico_certificado_imagen'), data.get('legalidad_certificado_imagen')
        ))
        conn.commit()
        return True, cursor.lastrowid
    except sqlite3.Error as e:
        conn.rollback()
        return False, str(e)
    finally:
        close_db(conn)

# Ejemplo de cómo podrías usar la función en una ruta de Flask:
# from flask import request, jsonify
#
# @app.route('/guardar_canje', methods=['POST'])
# def guardar_canje():
#     data = request.json
#     success, message = insertar_datos_canje(data)
#     if success:
#         return jsonify({'message': 'Datos de canje guardados exitosamente', 'id': message}), 201
#     else:
#         return jsonify({'error': f'Error al guardar los datos: {message}'}), 500

# Funciones para insertar Provincias y Municipios (ejemplo):
def insertar_provincia(nombre):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Provincias (Nombre) VALUES (?)", (nombre,))
        conn.commit()
        return True, cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.rollback()
        return False, f"La provincia '{nombre}' ya existe."
    except sqlite3.Error as e:
        conn.rollback()
        return False, str(e)
    finally:
        close_db(conn)

def insertar_municipio(nombre, id_provincia, mail_institucional=None):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Municipios (Nombre, Id_Provincia, Mail_Institucional) VALUES (?, ?, ?)", (nombre, id_provincia, mail_institucional))
        conn.commit()
        return True, cursor.lastrowid
    except sqlite3.ForeignKeyError:
        conn.rollback()
        return False, f"No existe la provincia con ID '{id_provincia}'."
    except sqlite3.Error as e:
        conn.rollback()
        return False, str(e)
    finally:
        close_db(conn)

# Ejemplo de cómo podrías usar estas funciones:
# insertar_provincia("Buenos Aires")
# insertar_provincia("Córdoba")
# insertar_municipio("La Plata", 1, "info@laplata.gov.ar")
# insertar_municipio("Córdoba Capital", 2, "contacto@cordoba.gov.ar")