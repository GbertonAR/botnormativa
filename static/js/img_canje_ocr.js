// static/js/img_canje_ocr.js

// --- Obtener referencias a elementos del DOM ---
const datosDocumentos = {}; // Objeto para almacenar datos de los documentos
const documentUploadInput = document.getElementById('document_upload');
const documentTypeHiddenInput = document.getElementById('document_type');
const ocrResultadoDiv = document.getElementById('ocr_resultado_div');
const ocrTextoLeidoSpan = document.getElementById('ocr_texto_leido');

// --- Funciones para los botones de escaneo ---
function triggerUpload(documentType) {
    documentTypeHiddenInput.value = documentType;
    documentUploadInput.click();
}

// --- Evento al cambiar el archivo seleccionado en el input file ---
documentUploadInput.addEventListener('change', function() {
    const file = this.files[0];
    const documentType = documentTypeHiddenInput.value;
    const previewElementId = 'preview_' + documentType;
    const previewElement = document.getElementById(previewElementId);
    const buttonElement = document.getElementById(documentType + '_button');

    console.log('documentType:', documentType);

    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            if (previewElement) {
                // Mostrar la imagen previsualizada
                previewElement.innerHTML = `<img src="${e.target.result}" style="max-width: 100%; max-height: 100%;">`;
                // Cambiar el color del botón a verde (indicando carga)
                buttonElement.className = 'scan-button verde';

                // Crear FormData para enviar el archivo al servidor
                const formData = new FormData();
                formData.append('document', file);
                formData.append('document_type', documentType);

                // Realizar la petición POST al servidor
                fetch('/canje/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Respuesta del servidor:', data);
                    datosDocumentos[documentType] = data; // Almacenar la respuesta del servidor

                    // Mostrar el resultado del OCR si es exitoso
                    if (data.ocr_result && data.ocr_result.status === 'succeeded' && data.ocr_result.analyze_result && data.ocr_result.analyze_result.read_results) {
                        let fullText = '';
                        data.ocr_result.analyze_result.read_results.forEach(result => {
                            result.lines.forEach(line => {
                                fullText += line.text + '\n';
                            });
                        });
                        ocrTextoLeidoSpan.textContent = fullText;
                        ocrResultadoDiv.style.display = 'block';
                    } else {
                        ocrTextoLeidoSpan.textContent = 'No se pudo leer texto de la imagen.';
                        ocrResultadoDiv.style.display = 'block'; // Mostrar aunque haya error
                    }
                    documentUploadInput.value = ''; // Resetear el input de archivo
                })
                .catch(error => {
                    console.error('Error al subir el archivo:', error);
                    alert('Error al subir el archivo.');
                    ocrTextoLeidoSpan.textContent = 'Error al comunicar con el servidor.';
                    ocrResultadoDiv.style.display = 'block';
                    documentUploadInput.value = ''; // Resetear el input de archivo en caso de error
                    buttonElement.className = 'scan-button rojo';
                    previewElement.innerHTML = '';
                    delete datosDocumentos[documentType]; // Eliminar datos si hubo error
                });
            } else {
                console.error(`No se encontró el elemento de vista previa con ID: preview_${documentType}`);
            }
        };
        reader.readAsDataURL(file);
    } else {
        // Si no se selecciona archivo, limpiar la previsualización y ocultar el OCR
        if (previewElement) {
            previewElement.innerHTML = '';
        }
        buttonElement.className = 'scan-button rojo';
        ocrResultadoDiv.style.display = 'none';
        delete datosDocumentos[documentType]; // Eliminar datos si se cancela la selección
    }
});

// --- Función para cambiar el color del botón (puede que no sea necesaria ahora) ---
function cambiarColorBoton(documentType, color) {
    const button = document.getElementById(documentType + '_button');
    if (button) {
        button.className = `scan-button ${color}`;
    }
}

// --- Función para procesar los documentos (aún sin lógica específica) ---
function procesarDocumentos() {
    console.log('Datos de los documentos:', datosDocumentos);
    alert('Datos de los documentos listos para ser procesados (principalmente texto OCR).');
}

// --- Función para enviar los datos adicionales (aún sin lógica específica) ---
function enviarDatos() {
    alert('Función para enviar datos (información adicional y datos de documentos).');
}