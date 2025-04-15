import sqlite3
from datetime import date
import qrcode
from io import BytesIO
import base64

DATABASE = 'canje/canje_db.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Para acceder a las columnas por nombre
    return conn

def close_db(conn):
    if conn:
        conn.close()

# def insertar_datos_canje(data):
#     print("Datos recibidos para insertar en la DB:", data)
#     conn = get_db()
#     cursor = conn.cursor()
#     hoy = date.today().isoformat()
#     try:
#         cursor.execute("""
#             INSERT INTO DatosDeCanje (
#                 fecha_ingreso, estado, dni, apellido, nombre,
#                 psicofisico_apellido, psicofisico_nombre, psicofisico_categoria,
#                 psicofisico_f_examen, psicofisico_f_dictamen, psicofisico_dni, psicofisico_imagen,
#                 curso_nombre, curso_apellido, curso_dni, curso_imagen,
#                 legalidad_nombre, legalidad_apellido, legalidad_dni, legalidad_imagen,
#                 provincia, municipio, ciudadano_presencial,
#                 frente_dni_imagen, dorso_dni_imagen, licencia_frente_imagen,
#                 licencia_dorso_imagen, linti_imagen, curso_certificado_imagen,
#                 psicofisico_certificado_imagen, legalidad_certificado_imagen,
#                 numero_de_tramite, imagen_qr
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """, (
#             hoy, 'Ingresado', data.get('dni'), data.get('apellido'), data.get('nombre'),
#             data.get('psicofisico_apellido'), data.get('psicofisico_nombre'), data.get('psicofisico_categoria'),
#             data.get('psicofisico_f_examen'), data.get('psicofisico_f_dictamen'), data.get('psicofisico_dni'), data.get('psicofisico_imagen'),
#             data.get('curso_nombre'), data.get('curso_apellido'), data.get('curso_dni'), data.get('curso_imagen'),
#             data.get('legalidad_nombre'), data.get('legalidad_apellido'), data.get('legalidad_dni'), data.get('legalidad_imagen'),
#             data.get('provincia'), data.get('municipio'), data.get('ciudadano_presencial'),
#             data.get('frente_dni_imagen'), data.get('dorso_dni_imagen'), data.get('licencia_frente_imagen'),
#             data.get('licencia_dorso_imagen'), data.get('linti_imagen'), data.get('curso_certificado_imagen'),
#             data.get('psicofisico_certificado_imagen'), data.get('legalidad_certificado_imagen'),
#             data.get('numero_de_tramite'),  # Agrega el data.get para numero_de_tramite
#             data.get('imagen_qr')         # Agrega el data.get para imagen_qr
#         ))
#         conn.commit()
#         return True, cursor.lastrowid
#     except sqlite3.Error as e:
#         conn.rollback()
#         return False, str(e)
#     finally:
#         close_db(conn)

def insertar_datos_canje(data):
    print("Datos recibidos para insertar en la DB:", data)
    conn = get_db()
    cursor = conn.cursor()
    hoy = date.today().isoformat()
    provincia_id = data.get('provincia_id')
    municipio_id = data.get('municipio_id')
    nombre = data.get('nombre', '').upper().split()
    apellido = data.get('apellido', '').upper().split()
    iniciales = ""
    if nombre:
        iniciales += nombre[0][0]
    if apellido:
        iniciales += apellido[0][0]

    numero_de_tramite = 1 # Esto se sobrescribe más adelante

    print(f"Valor de fecha_ingreso: {hoy}")
    print(f"Valor de estado: {'Ingresado'}")
    print(f"Valor de numero_de_tramite: {numero_de_tramite}")
    print(f"Valor de frente_dni_imagen: {data.get('frente_dni_imagen')}")

    try:
        print(f"Valor de provincia_id antes de la consulta: {provincia_id}")
        print(f"Valor de municipio_id antes de la consulta: {municipio_id}")

        cursor.execute("""
            SELECT MAX(SUBSTR(numero_de_tramite, 7))
            FROM DatosDeCanje
            WHERE SUBSTR(numero_de_tramite, 1, 2) = ?
              AND SUBSTR(numero_de_tramite, 3, 3) = ?
        """, (f"{int(provincia_id):02d}", f"{int(municipio_id):03d}"))
        resultado = cursor.fetchone()[0]
        secuencial = 1
        if resultado and resultado.isdigit():
            secuencial = int(resultado) + 1

        numero_de_tramite = f"{int(provincia_id):02d}{int(municipio_id):03d}{iniciales}{secuencial:04d}"
        qr_data = numero_de_tramite # Usamos directamente numero_de_tramite para el QR por ahora

        print(f"Valor de secuencial: {secuencial}")
        print(f"Valor de numero_de_tramite después de la consulta: {numero_de_tramite}")
        datos_qr = numero_de_tramite
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        imagen_qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        datos_qr = imagen_qr_base64

        print(datos_qr)

        sql_insert = """
            INSERT INTO DatosDeCanje (
                fecha_ingreso, estado, dni, apellido, nombre,
                psicofisico_apellido, psicofisico_nombre, psicofisico_categoria,
                psicofisico_f_examen, psicofisico_f_dictamen, psicofisico_dni, psicofisico_imagen,
                curso_nombre, curso_apellido, curso_dni, curso_imagen,
                legalidad_nombre, legalidad_apellido, legalidad_dni, legalidad_imagen,
                provincia_id, municipio_id, ciudadano_presencial,
                frente_dni_imagen, dorso_dni_imagen, licencia_frente_imagen,
                licencia_dorso_imagen, linti_imagen, curso_certificado_imagen,
                psicofisico_certificado_imagen, legalidad_certificado_imagen,
                numero_de_tramite, imagen_qr
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        data_tuple = (
            hoy, 'Ingresado', data.get('dni'), data.get('apellido'), data.get('nombre'),
            data.get('psicofisico_apellido'), data.get('psicofisico_nombre'), data.get('psicofisico_categoria'),
            data.get('psicofisico_f_examen'), data.get('psicofisico_f_dictamen'), data.get('psicofisico_dni'), data.get('psicofisico_imagen'),
            data.get('curso_nombre'), data.get('curso_apellido'), data.get('curso_dni'), data.get('curso_imagen'),
            data.get('legalidad_nombre'), data.get('legalidad_apellido'), data.get('legalidad_dni'), data.get('legalidad_imagen'),
            int(data.get('provincia_id')), int(data.get('municipio_id')), data.get('ciudadano_presente'),
            data.get('frente_dni_imagen'), data.get('dorso_dni_imagen'), data.get('licencia_frente_imagen'),
            data.get('licencia_dorso_imagen'), data.get('linti_imagen'), data.get('curso_certificado_imagen'),
            data.get('psicofisico_certificado_imagen'), data.get('legalidad_certificado_imagen'),
            numero_de_tramite, datos_qr
        )

        cursor.execute(sql_insert, data_tuple)
        conn.commit()
        return True, numero_de_tramite

    except conn.Error as e:
        if conn:
            conn.rollback()
        return False, str(e)
    finally:
        if conn:
            conn.close()

### Esto es para analizar         
        # cursor.execute("""
        #     INSERT INTO DatosDeCanje (
        #         fecha_ingreso, estado, dni, apellido, nombre,
        #         psicofisico_apellido, psicofisico_nombre, psicofisico_categoria,
        #         psicofisico_f_examen, psicofisico_f_dictamen, psicofisico_dni, psicofisico_imagen,
        #         curso_nombre, curso_apellido, curso_dni, curso_imagen,
        #         legalidad_nombre, legalidad_apellido, legalidad_dni, legalidad_imagen,
        #         provincia_id, municipio_id, ciudadano_presencial,
        #         frente_dni_imagen, dorso_dni_imagen, licencia_frente_imagen,
        #         licencia_dorso_imagen, linti_imagen, curso_certificado_imagen,
        #         psicofisico_certificado_imagen, legalidad_certificado_imagen,
        #         numero_de_tramite, imagen_qr
        #     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        # """, (
        #     hoy, 'Ingresado', data.get('dni'), data.get('apellido'), data.get('nombre'),
        #     data.get('psicofisico_apellido'), data.get('psicofisico_nombre'), data.get('psicofisico_categoria'),
        #     data.get('psicofisico_f_examen'), data.get('psicofisico_f_dictamen'), data.get('psicofisico_dni'), data.get('psicofisico_imagen'),
        #     data.get('curso_nombre'), data.get('curso_apellido'), data.get('curso_dni'), data.get('curso_imagen'),
        #     data.get('legalidad_nombre'), data.get('legalidad_apellido'), data.get('legalidad_dni'), data.get('legalidad_imagen'),
        #     int(data.get('provincia_id')), int(data.get('municipio_id')), data.get('ciudadano_presencial'),
        #     data.get('frente_dni_imagen'), data.get('dorso_dni_imagen'), data.get('licencia_frente_imagen'),
        #     data.get('licencia_dorso_imagen'), data.get('linti_imagen'), data.get('curso_certificado_imagen'),
        #     data.get('psicofisico_certificado_imagen'), data.get('legalidad_certificado_imagen'),
        #     numero_de_tramite,
        #     datos_qr
        # ))
        
#### Fin de análisis
    #     cursor.execute("""
    #     INSERT INTO DatosDeCanje (
    #         fecha_ingreso, estado, dni, apellido, nombre,
    #         psicofisico_apellido, psicofisico_nombre, psicofisico_categoria,
    #         psicofisico_f_examen, psicofisico_f_dictamen, psicofisico_dni, psicofisico_imagen,
    #         curso_nombre, curso_apellido, curso_dni, curso_imagen,
    #         legalidad_nombre, legalidad_apellido, legalidad_dni, legalidad_imagen,
    #         provincia_id, municipio_id, ciudadano_presencial,
    #         frente_dni_imagen, dorso_dni_imagen, licencia_frente_imagen,
    #         licencia_dorso_imagen, linti_imagen, curso_certificado_imagen,
    #         psicofisico_certificado_imagen, legalidad_certificado_imagen,
    #         numero_de_tramite, imagen_qr
    #     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    #     """, (
    #     hoy, 'Ingresado', data.get('dni'), None, None,  # apellido y nombre en blanco
    #     None, None, None, None, None, None, None, None,
    #     None, None, None, None, None, None, None, None,
    #     None, None, None, None, None, None, None, None,
    #     " ", datos_qr, " ", " "
    # ))

    #     conn.commit()
    #     return True, cursor.lastrowid
    # except sqlite3.Error as e:
    #     conn.rollback()
    #     print(str(e))
    #     return False, str(e)
    # finally:
    #     close_db(conn)

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
