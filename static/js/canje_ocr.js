// Este archivo contiene el código JavaScript para manejar la carga y validación de documentos en el proceso de canje de licencia de conducir.
// Se utiliza para cargar documentos como el Psicofísico y el Dorso del DNI, y validar los datos extraídos de ellos.
// Se utiliza el API Fetch para enviar los documentos al servidor y recibir respuestas.
// Se utiliza FileReader para previsualizar las imágenes cargadas antes de enviarlas al servidor.
// Se utiliza FormData para enviar archivos y datos al servidor.
const datosDocumentos = {}; // Objeto para almacenar datos de los documentos

function triggerUpload(documentType) {
    document.getElementById('document_type').value = documentType;
    document.getElementById('document_upload').click();
}

document.getElementById('document_upload').addEventListener('change', function() {
    const file = this.files[0];
    const documentType = document.getElementById('document_type').value;
    const previewElementId = 'preview_' + documentType;
    const previewElement = document.getElementById(previewElementId);
    const buttonElement = document.getElementById(documentType + '_button');

    console.log('documentType:', documentType);

    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            if (previewElement) {
                previewElement.innerHTML = `<img src="${e.target.result}" style="max-width: 100%; max-height: 100%;">`;
                buttonElement.className = 'scan-button verde';

                const formData = new FormData();
                formData.append('document', file);
                formData.append('document_type', documentType);

                fetch('/canje/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Respuesta del servidor:', data);
                    datosDocumentos[documentType] = data; // Almacenar la respuesta completa
                    console.log('Datos almacenados en datosDocumentos[', documentType, ']:', datosDocumentos[documentType]);
                    console.log('Estado actual de datosDocumentos:', datosDocumentos);
        
                    // 1. Frente DNI
                    if (documentType === 'frente_dni' && data.nombre && data.apellidos && data.numero_documento) {
                        const nombreSpan = document.getElementById('nombre_leido');
                        const apellidosSpan = document.getElementById('apellidos_leido');
                        const numeroSpan = document.getElementById('numero_documento_leido');
                        nombreSpan.textContent = data.nombre || nombreSpan.textContent;
                        apellidosSpan.textContent = data.apellidos || apellidosSpan.textContent;
                        numeroSpan.textContent = data.numero_documento || numeroSpan.textContent;
                        document.getElementById('dorso_dni_info').style.display = 'block';
                    }
                    // 2. Dorso DNI
                    else if (documentType === 'dorso_dni' && data.nombre && data.apellidos && data.numero_documento) {
                        const nombreSpan = document.getElementById('nombre_leido');
                        const apellidosSpan = document.getElementById('apellidos_leido');
                        const numeroSpan = document.getElementById('numero_documento_leido');
                        nombreSpan.textContent = data.nombre;
                        apellidosSpan.textContent = data.apellidos;
                        numeroSpan.textContent = data.numero_documento;
                        document.getElementById('dorso_dni_info').style.display = 'block';
                    } else if (documentType === 'dorso_dni' && data.error) {
                        document.getElementById('dorso_dni_info').style.display = 'none';
                        alert(data.error);
                        buttonElement.className = 'scan-button rojo';
                        previewElement.innerHTML = '';
                        delete datosDocumentos['dorso_dni'];
                    }
                    // 3. Frente Licencia
                    else if (documentType === 'licencia_frente' && data.ocr_text) {
                        datosDocumentos['licencia_frente'].ocr_text = data.ocr_text;
                        console.log('OCR Frente Licencia almacenado:', datosDocumentos['licencia_frente']);
                    }
                    // 4. Dorso Licencia
                    else if (documentType === 'licencia_dorso' && data.ocr_text) {
                        datosDocumentos['licencia_dorso'].ocr_text = data.ocr_text;
                        console.log('OCR Dorso Licencia almacenado:', datosDocumentos['licencia_dorso']);
                    }
                    // 5. Psicotécnico (asumimos 'psicofisico' es el documentType)
                    else if (documentType === 'psicofisico' && data.ocr_text) {
                        const ocrPsicofisico = data.ocr_text;
                        const lines = ocrPsicofisico.split('\n');
                        datosDocumentos['psicofisico'].apellido = data.ocr_text.apellido
                        datosDocumentos['psicofisico'].nombre = data.ocr_text.nombre
                        datosDocumentos['psicofisico'].dni = data.ocr_text.dni
                        datosDocumentos['psicofisico'].f_examen = data.ocr_text.fecha_examen
                        datosDocumentos['psicofisico'].f_dictamen = data.ocr_text.fecha_dictamen
                        datosDocumentos['psicofisico'].categoria = data.ocr_text.categoria
                        datosDocumentos['psicofisico'].imagen = data.ocr_text
                        console.log('Datos Psicofisico procesados y almacenados:', datosDocumentos['psicofisico']);
                    }
                    // 6. Certificado Curso
                    else if (documentType === 'certificado_curso' && data.ocr_text) {
                        const ocrCurso = data.ocr_text;
                        const lines = ocrCurso.split('\n');
                        datosDocumentos['certificado_curso'].nombre = data.ocr_text.nombre
                        datosDocumentos['certificado_curso'].apellido = data.ocr_text.apellido
                        datosDocumentos['certificado_curso'].dni = data.ocr_text.dni
                        datosDocumentos['certificado_curso'].imagen = data.ocr_text
                        
                        console.log('Datos Certificado Curso procesados y almacenados:', datosDocumentos['certificado_curso']);
                    }
                    // 7. Licencia LINTI
                    else if (documentType === 'licencia_linti' && data.ocr_text) {
                        const ocrLinti = data.ocr_text;
                        const lines = ocrLinti.split('\n');
                        datosDocumentos['licencia_linti'].nombre = data.ocr_text.nombre
                        datosDocumentos['licencia_linti'].apellido = data.ocr_text.apellido
                        datosDocumentos['licencia_linti'].dni = data.ocr_text.dni
                        datosDocumentos['licencia_linti'].f_vto = data.ocr_text.fecha_vto
                        datosDocumentos['licencia_linti'].categoria = data.ocr_text.categoria
                        datosDocumentos['licencia_linti'].imagen = data.ocr_text
                        console.log('Datos LINTI procesados y almacenados:', datosDocumentos['licencia_linti']);
                    }
                    // 8. Certificado Legalidad
                    else if (documentType === 'certificado_legalidad' && data.ocr_text) {
                        const ocrLegalidad = data.ocr_text;
                        const lines = ocrLegalidad.split('\n');
                        datosDocumentos['certificado_legalidad'].nombre = data.ocr_text.nombre
                        datosDocumentos['certificado_legalidad'].apellido = data.ocr_text.apellido
                        datosDocumentos['certificado_legalidad'].dni = data.ocr_text.dni
                        datosDocumentos['certificado_legalidad'].imagen = data.ocr_text
                        console.log('Datos Certificado Legalidad procesados y almacenados:', datosDocumentos['certificado_legalidad']);
                    }
                    // Manejo para otros documentTypes o casos inesperados
                    else {
                        console.log(`Datos para ${documentType}:`, data);
                    }
                    document.getElementById('document_upload').value = ''; // Resetear input
                })
                .catch(error => {
                    console.error('Error al subir el archivo:', error);
                    alert('Error al subir el archivo.');
                    const infoDiv = document.getElementById('dorso_dni_info');
                    infoDiv.style.display = 'none';
                    document.getElementById('document_upload').value = ''; // Resetear input en caso de error
                    buttonElement.className = 'scan-button rojo';
                    previewElement.innerHTML = '';
                    delete datosDocumentos[documentType];
                });
            } else {
                console.error(`No se encontró el elemento de vista previa con ID: preview_${documentType}`);
            }
        };
        reader.readAsDataURL(file);
    } else {
        if (previewElement) {
            previewElement.innerHTML = '';
        }
        buttonElement.className = 'scan-button rojo';
        if (documentType === 'dorso_dni') {
            document.getElementById('dorso_dni_info').style.display = 'none';
        }
        delete datosDocumentos[documentType]; // Eliminar datos si se cancela la selección
    }
});

function cambiarColorBoton(documentType, color) {
    const button = document.getElementById(documentType + '_button');
    if (button) {
        button.className = `scan-button ${color}`;
    }
}

function procesarDocumentos() {
    console.log('Datos de los documentos:', datosDocumentos);
    const errores = {};

    // Función auxiliar para agregar errores
    function agregarError(documentType, mensaje) {
        if (!errores[documentType]) {
            errores[documentType] = [];
        }
        errores[documentType].push(mensaje);
        cambiarColorBoton(documentType, 'rojo');
    }

    // Validación del Psicofísico
    if (datosDocumentos['psicofisico'] && datosDocumentos['psicofisico'].ocr_text && datosDocumentos['dorso_dni']) {
        const ocrPsicofisico = datosDocumentos['psicofisico'].ocr_text.toLowerCase();
        const apellidoDNI = datosDocumentos['dorso_dni'].apellidos.toLowerCase();
        const dniDNI = datosDocumentos['dorso_dni'].numero_documento;

        if (!ocrPsicofisico.includes(apellidoDNI)) {
            agregarError('psicofisico', `El apellido "${apellidoDNI}" del DNI no se encuentra en el Psicofísico.`);
        }
        if (!ocrPsicofisico.includes(dniDNI)) {
            agregarError('psicofisico', `El número de DNI "${dniDNI}" no se encuentra en el Psicofisico.`);
        }
        if (!errores['psicofisico']) {
            cambiarColorBoton('psicofisico', 'verde');
        }
    } else if (datosDocumentos['psicofisico'] && !datosDocumentos['dorso_dni']) {
        alert('Advertencia: No se ha cargado el Dorso del DNI, no se pueden verificar los datos del Psicofísico.');
    } else if (!datosDocumentos['psicofisico']) {
        alert('Advertencia: No se ha cargado el Psicofísico, no se pudieron verificar los datos.');
    } else if (datosDocumentos['psicofisico'] && !datosDocumentos['psicofisico'].ocr_text) {
        alert('Advertencia: No se pudo extraer texto del Psicofísico para la validación de apellido y DNI.');
    }

    // Aquí podrías agregar más validaciones para otros documentos

    if (Object.keys(errores).length > 0) {
        let mensajeErrorGeneral = 'Se encontraron los siguientes errores en la validación:\n';
        for (const docType in errores) {
            mensajeErrorGeneral += `\nErrores en ${docType}:\n- ${errores[docType].join('\n- ')}`;
        }
        alert(mensajeErrorGeneral);
        return;
    } else {
        alert('Las validaciones se completaron sin errores. Procediendo al procesamiento con Azure...');
        // Enviar los datos de los documentos al backend para su procesamiento con Azure
        fetch('/canje/procesar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(datosDocumentos)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Respuesta del procesamiento:', data);
            // Aquí puedes manejar la respuesta del backend, mostrando los resultados del procesamiento con Azure
            if (data.processed_data) {
                // Actualizar la interfaz de usuario con los datos procesados
                if (data.processed_data['dorso_dni']) {
                    const dniData = data.processed_data['dorso_dni'];
                    document.getElementById('nombre_leido').textContent = dniData.nombre || '';
                    document.getElementById('apellidos_leido').textContent = dniData.apellidos || '';
                    document.getElementById('numero_documento_leido').textContent = dniData.numero_documento || '';
                    if (dniData.nombre || dniData.apellidos || dniData.numero_documento) {
                        document.getElementById('dorso_dni_info').style.display = 'block';
                    } else {
                        document.getElementById('dorso_dni_info').style.display = 'none';
                    }
                }
                // Puedes mostrar los resultados de otros documentos si es necesario
                alert('Documentos procesados exitosamente con Azure.');
            } else if (data.error) {
                alert(`Error en el procesamiento: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error al enviar los documentos para procesamiento:', error);
            alert('Error al enviar los documentos para procesamiento.');
        });
    }
}
