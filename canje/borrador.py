def insertar_datos_canje(data):
    # print("Datos recibidos para insertar en la DB:", data)
    # conn = get_db()
    # cursor = conn.cursor()
    # hoy = date.today().isoformat()
    # provincia_id = data.get('provincia')
    # municipio_id = data.get('municipio')
    # nombre = data.get('nombre', '').upper().split()
    # apellido = data.get('apellido', '').upper().split()
    # iniciales = ""
    # if nombre:
    #     iniciales += nombre[0][0]
    # if apellido:
    #     iniciales += apellido[0][0]

    # numero_de_tramite = None
    
    numero_de_tramite = None
    qr_data = None
    
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

    numero_de_tramite = 1

    print(f"Valor de fecha_ingreso: {hoy}")
    print(f"Valor de estado: {'Ingresado'}")
    print(f"Valor de numero_de_tramite: {numero_de_tramite}")
    #print(f"Valor de datos_qr: {datos_qr}")
    # Imprime también algunos de los data.get() para los campos de imagen
    print(f"Valor de frente_dni_imagen: {data.get('frente_dni_imagen')}")
    
    try:
                # *** AGREGAR ESTOS PRINTS ***
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
        #datos_qr = f"Nro. Trámite: {numero_de_tramite}"
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
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Guardar la imagen en un buffer de memoria
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Codificar la imagen en base64 para poderla almacenar como texto o enviar al frontend
        imagen_qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        datos_qr = imagen_qr_base64 # Ahora datos_qr contiene la imagen codificada en base64        
        
        print(datos_qr)
        
    #try:
        # Obtener el último número secuencial para este municipio
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
        datos_qr = f"Nro. Trámite: {numero_de_tramite}"
        datos_qr = " "
        print(f"Nuevo número de trámite generado: {numero_de_tramite}")
        print(f"Datos para QR: {datos_qr}")



                
                tr.insertCell().textContent = row[6];  // Psicofísico Apellido
                tr.insertCell().textContent = row[7];  // Psicofísico Nombre
                tr.insertCell().textContent = row[8];  // Psicofísico Categoría
                tr.insertCell().textContent = row[9];  // Psicofísico F. Examen
                tr.insertCell().textContent = row[10]; // Psicofísico F. Dictamen
                tr.insertCell().textContent = row[11]; // Psicofísico DNI
                tr.insertCell().textContent = row[12]; // Psicofísico Imagen
                tr.insertCell().textContent = row[13]; // Curso Nombre
                tr.insertCell().textContent = row[14]; // Curso Apellido
                tr.insertCell().textContent = row[15]; // Curso DNI
                tr.insertCell().textContent = row[16]; // Curso Imagen
                tr.insertCell().textContent = row[17]; // Legalidad Nombre
                tr.insertCell().textContent = row[18]; // Legalidad Apellido
                tr.insertCell().textContent = row[19]; // Legalidad DNI
                tr.insertCell().textContent = row[20]; // Legalidad Imagen
                tr.insertCell().textContent = row[21]; // Provincia
                tr.insertCell().textContent = row[22]; // Municipio
                tr.insertCell().textContent = row[23]; // Ciudadano Presencial
                tr.insertCell().textContent = row[24]; // Frente DNI Imagen
                tr.insertCell().textContent = row[25]; // Dorso DNI Imagen
                tr.insertCell().textContent = row[26]; // Licencia Frente Imagen
                tr.insertCell().textContent = row[27]; // Licencia Dorso Imagen
                tr.insertCell().textContent = row[28]; // LINTI Imagen
                tr.insertCell().textContent = row[29]; // Curso Certificado Imagen
                tr.insertCell().textContent = row[30]; // Psicofísico Certificado Imagen
                tr.insertCell().textContent = row[31]; // Legalidad Certificado Imagen
